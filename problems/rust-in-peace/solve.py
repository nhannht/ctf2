from __future__ import annotations

import argparse
import concurrent.futures
import random
import socket
import time
from dataclasses import dataclass
from typing import Iterable

from z3 import (
    BitVec,
    BitVecSort,
    BitVecVal,
    Concat,
    Extract,
    K,
    Select,
    Solver,
    SolverFor,
    Store,
    ULE,
)


PERM = [
    5,
    44,
    34,
    62,
    13,
    29,
    9,
    59,
    47,
    23,
    43,
    39,
    18,
    35,
    51,
    21,
    2,
    48,
    45,
    7,
    54,
    46,
    30,
    10,
    3,
    12,
    42,
    1,
    11,
    37,
    19,
    0,
    55,
    60,
    32,
    38,
    27,
    49,
    20,
    58,
    15,
    36,
    53,
    56,
    31,
    52,
    6,
    40,
    14,
    28,
    26,
    24,
    63,
    61,
    16,
    33,
    41,
    4,
    17,
    25,
    22,
    8,
    50,
    57,
]

BLOCK_BYTES = 8
NIBBLES = 16

INV_PERM = [0] * 64
for src, dst in enumerate(PERM):
    INV_PERM[dst] = src


def u64_from_hex_le(hex_text: str) -> int:
    return int.from_bytes(bytes.fromhex(hex_text), "little")


def hex_le_from_u64(value: int) -> str:
    return value.to_bytes(BLOCK_BYTES, "little").hex()


def split_hex_blocks(hex_text: str) -> list[int]:
    if len(hex_text) % (2 * BLOCK_BYTES) != 0:
        raise ValueError("hex payload length is not a whole number of blocks")
    return [
        u64_from_hex_le(hex_text[offset : offset + 2 * BLOCK_BYTES])
        for offset in range(0, len(hex_text), 2 * BLOCK_BYTES)
    ]


def sboxes_from_hex_nibbles(hex_nibbles: list[int]) -> list[list[int]]:
    base: list[list[int]] = []
    for idx in range(4):
        sbox = list(range(16))
        i = 4 * idx
        while i < 4 * idx + 16:
            a = hex_nibbles[i]
            b = hex_nibbles[i + 1]
            sbox[a], sbox[b] = sbox[b], sbox[a]
            i += 2
        base.append(sbox)
    return base


def inverse_sboxes(sboxes: list[list[int]]) -> list[list[int]]:
    out: list[list[int]] = []
    for sbox in sboxes:
        inv = [0] * 16
        for idx, value in enumerate(sbox):
            inv[value] = idx
        out.append(inv)
    return out


def sbox_layer(state: int, sboxes: list[list[int]]) -> int:
    out = 0
    for i in range(NIBBLES):
        nibble = (state >> (4 * i)) & 0xF
        out |= sboxes[i % 4][nibble] << (4 * i)
    return out


def permute_bits(state: int) -> int:
    out = 0
    for src, dst in enumerate(PERM):
        out |= ((state >> src) & 1) << dst
    return out


def inverse_permute_bits(state: int) -> int:
    out = 0
    for src, dst in enumerate(PERM):
        out |= ((state >> dst) & 1) << src
    return out


def encrypt_block(block: int, rounds: int, sboxes: list[list[int]]) -> int:
    state = block
    for _ in range(rounds - 1):
        state = sbox_layer(state, sboxes)
        state = permute_bits(state)
    return sbox_layer(state, sboxes)


def decrypt_block(block: int, rounds: int, inv_sboxes: list[list[int]]) -> int:
    state = sbox_layer(block, inv_sboxes)
    for _ in range(rounds - 1):
        state = inverse_permute_bits(state)
        state = sbox_layer(state, inv_sboxes)
    return state


@dataclass(frozen=True)
class WorkerConfig:
    name: str
    solver_kind: str
    used_e: int
    used_d: int
    seed: int
    timeout_ms: int


@dataclass
class WorkerResult:
    name: str
    sat: bool
    elapsed: float
    hex_nibbles: list[int] | None


def build_solver(kind: str) -> Solver:
    if kind == "qfaufbv":
        return SolverFor("QF_AUFBV")
    return Solver()


def identity_array():
    array = K(BitVecSort(4), BitVecVal(0, 4))
    for value in range(16):
        array = Store(array, BitVecVal(value, 4), BitVecVal(value, 4))
    return array


def symbolic_base_sboxes(hex_vars: list) -> list:
    bases = []
    for idx in range(4):
        array = identity_array()
        i = 4 * idx
        while i < 4 * idx + 16:
            a = hex_vars[i]
            b = hex_vars[i + 1]
            va = Select(array, a)
            vb = Select(array, b)
            array = Store(Store(array, a, vb), b, va)
            i += 2
        bases.append(array)
    return bases


def symbolic_inverse_sboxes(bases: list) -> list:
    inv_bases = []
    for base in bases:
        inv = K(BitVecSort(4), BitVecVal(0, 4))
        for value in range(16):
            inv = Store(inv, Select(base, BitVecVal(value, 4)), BitVecVal(value, 4))
        inv_bases.append(inv)
    return inv_bases


def symbolic_encrypt_const(block: int, rounds: int, bases: list):
    state = [BitVecVal((block >> (4 * idx)) & 0xF, 4) for idx in range(NIBBLES)]
    for _ in range(rounds - 1):
        subbed = [Select(bases[idx % 4], state[idx]) for idx in range(NIBBLES)]
        next_state = []
        for dst_nibble in range(NIBBLES):
            bits = []
            for dst_bit in range(4):
                src_bit = INV_PERM[4 * dst_nibble + dst_bit]
                src_nibble, src_nibble_bit = divmod(src_bit, 4)
                bits.append(Extract(src_nibble_bit, src_nibble_bit, subbed[src_nibble]))
            next_state.append(Concat(bits[3], bits[2], bits[1], bits[0]))
        state = next_state
    subbed = [Select(bases[idx % 4], state[idx]) for idx in range(NIBBLES)]
    return Concat(*reversed(subbed))


def symbolic_decrypt_const(block: int, rounds: int, inv_bases: list):
    state = [BitVecVal((block >> (4 * idx)) & 0xF, 4) for idx in range(NIBBLES)]
    state = [Select(inv_bases[idx % 4], state[idx]) for idx in range(NIBBLES)]
    for _ in range(rounds - 1):
        next_state = []
        for dst_nibble in range(NIBBLES):
            bits = []
            for dst_bit in range(4):
                src_bit = PERM[4 * dst_nibble + dst_bit]
                src_nibble, src_nibble_bit = divmod(src_bit, 4)
                bits.append(Extract(src_nibble_bit, src_nibble_bit, state[src_nibble]))
            next_state.append(Concat(bits[3], bits[2], bits[1], bits[0]))
        state = [Select(inv_bases[idx % 4], next_state[idx]) for idx in range(NIBBLES)]
    return Concat(*reversed(state))


def solve_worker(
    config: WorkerConfig,
    rounds: int,
    enc_pairs: list[tuple[int, int]],
    dec_pairs: list[tuple[int, int]],
) -> WorkerResult:
    started = time.time()
    solver = build_solver(config.solver_kind)
    solver.set(timeout=config.timeout_ms)
    solver.set(random_seed=config.seed)

    hex_vars = [BitVec(f"{config.name}_h{idx}", 4) for idx in range(28)]
    for var in hex_vars:
        solver.add(ULE(var, BitVecVal(15, 4)))

    bases = symbolic_base_sboxes(hex_vars)
    inv_bases = symbolic_inverse_sboxes(bases)

    for pt, ct in enc_pairs[: config.used_e]:
        solver.add(symbolic_encrypt_const(pt, rounds, bases) == BitVecVal(ct, 64))
    for ct, pt in dec_pairs[: config.used_d]:
        solver.add(symbolic_decrypt_const(ct, rounds, inv_bases) == BitVecVal(pt, 64))

    result = solver.check()
    elapsed = time.time() - started
    if str(result) != "sat":
        return WorkerResult(config.name, False, elapsed, None)

    model = solver.model()
    recovered = [model.eval(var).as_long() for var in hex_vars]
    return WorkerResult(config.name, True, elapsed, recovered)


class ChallengeSession:
    def __init__(self, host: str, port: int):
        self.sock = socket.create_connection((host, port), timeout=30)
        self.sock.settimeout(30)
        self.buffer = bytearray()

    def close(self) -> None:
        self.sock.close()

    def _recv_until(self, token: bytes) -> bytes:
        while token not in self.buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise EOFError("connection closed")
            self.buffer.extend(chunk)
        index = self.buffer.index(token) + len(token)
        out = bytes(self.buffer[:index])
        del self.buffer[:index]
        return out

    def _recv_line(self) -> bytes:
        return self._recv_until(b"\n")

    def _send_line(self, text: str) -> None:
        self.sock.sendall(text.encode() + b"\n")

    def read_banner(self) -> int:
        self._recv_until(b"Working with ")
        rounds_line = self._recv_until(b" rounds.\n")
        rounds = int(rounds_line.decode().split()[0])
        self._recv_until(b"> ")
        return rounds

    def query(self, mode: str, block_hex: str) -> str:
        self._send_line(f"{mode}{block_hex}")
        line = self._recv_line().rstrip(b"\n").decode()
        self._recv_until(b"> ")
        return line

    def query_blocks(self, mode: str, blocks: list[int]) -> list[int]:
        payload = "".join(hex_le_from_u64(block) for block in blocks)
        response = self.query(mode, payload)
        return split_hex_blocks(response)

    def keepalive(self) -> None:
        self.query("E", "")

    def start_challenge(self) -> None:
        self._send_line("")

    def read_challenge(self) -> str:
        self._recv_until(b"Challenge: ")
        challenge = self._recv_line().strip().decode()
        self._recv_until(b"Response: ")
        return challenge

    def send_response(self, response_hex: str) -> None:
        self._send_line(response_hex)

    def read_remaining(self) -> str:
        self.sock.settimeout(2)
        chunks = [bytes(self.buffer)]
        self.buffer.clear()
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        except socket.timeout:
            pass
        return b"".join(chunks).decode("utf-8", "replace")


def collect_pairs(
    session: ChallengeSession,
    rng: random.Random,
    enc_count: int,
    dec_count: int,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    enc_pairs: list[tuple[int, int]] = []
    dec_pairs: list[tuple[int, int]] = []

    interesting = [
        0,
        (1 << 64) - 1,
        0x0123456789ABCDEF,
        0xFEDCBA9876543210,
    ]
    enc_inputs = interesting[:]
    while len(enc_inputs) < enc_count:
        enc_inputs.append(rng.getrandbits(64))

    dec_inputs = interesting[:]
    while len(dec_inputs) < dec_count:
        dec_inputs.append(rng.getrandbits(64))

    for pt in enc_inputs[:enc_count]:
        ct_hex = session.query("E", hex_le_from_u64(pt))
        enc_pairs.append((pt, u64_from_hex_le(ct_hex)))

    for ct in dec_inputs[:dec_count]:
        pt_hex = session.query("D", hex_le_from_u64(ct))
        dec_pairs.append((ct, u64_from_hex_le(pt_hex)))

    return enc_pairs, dec_pairs


def validate_candidate(
    hex_nibbles: list[int],
    rounds: int,
    enc_pairs: Iterable[tuple[int, int]],
    dec_pairs: Iterable[tuple[int, int]],
) -> tuple[bool, list[list[int]]]:
    sboxes = sboxes_from_hex_nibbles(hex_nibbles)
    inv_sboxes = inverse_sboxes(sboxes)

    for pt, ct in enc_pairs:
        if encrypt_block(pt, rounds, sboxes) != ct:
            return False, sboxes
    for ct, pt in dec_pairs:
        if decrypt_block(ct, rounds, inv_sboxes) != pt:
            return False, sboxes
    return True, sboxes


def recover_sboxes(
    rounds: int,
    enc_pairs: list[tuple[int, int]],
    dec_pairs: list[tuple[int, int]],
    timeout_s: int,
    keepalive,
) -> list[list[int]]:
    configs = [
        WorkerConfig("w0", "qfaufbv", 4, 0, 1, timeout_s * 1000),
        WorkerConfig("w1", "qfaufbv", 6, 0, 2, timeout_s * 1000),
        WorkerConfig("w2", "qfaufbv", 4, 2, 3, timeout_s * 1000),
        WorkerConfig("w3", "qfaufbv", 6, 2, 4, timeout_s * 1000),
    ]

    solve_enc = enc_pairs[:-2]
    solve_dec = dec_pairs[:-2]
    verify_enc = enc_pairs
    verify_dec = dec_pairs

    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(solve_worker, config, rounds, solve_enc, solve_dec): config
            for config in configs
        }

        pending = set(futures)
        while pending:
            done, pending = concurrent.futures.wait(
                pending,
                timeout=15,
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            if not done:
                keepalive()
                continue

            for future in done:
                result = future.result()
                print(f"[{result.name}] sat={result.sat} elapsed={result.elapsed:.1f}s")
                if not result.sat or result.hex_nibbles is None:
                    continue

                valid, sboxes = validate_candidate(
                    result.hex_nibbles,
                    rounds,
                    verify_enc,
                    verify_dec,
                )
                print(f"[{result.name}] verification={valid}")
                if valid:
                    for pending_future in pending:
                        pending_future.cancel()
                    return sboxes

            if pending:
                keepalive()

    raise RuntimeError("no valid model recovered")


def build_consistency_records(
    lifted_queries: dict[int, list[int]],
    image_queries: dict[int, list[int]],
) -> list[tuple[int, int, int, int, dict[tuple[int, int], int]]]:
    records: list[tuple[int, int, int, int, dict[tuple[int, int], int]]] = []
    for pos in range(NIBBLES):
        cls = pos % 4
        for input_value, lifted in enumerate(lifted_queries[pos]):
            for output_value, image in enumerate(image_queries[pos]):
                preimage = inverse_permute_bits(image)
                constraints: dict[tuple[int, int], int] = {}
                consistent = True
                for nibble_index in range(NIBBLES):
                    key = (nibble_index % 4, (lifted >> (4 * nibble_index)) & 0xF)
                    value = (preimage >> (4 * nibble_index)) & 0xF
                    previous = constraints.get(key)
                    if previous is None:
                        constraints[key] = value
                    elif previous != value:
                        consistent = False
                        break
                if consistent:
                    records.append((pos, cls, input_value, output_value, constraints))
    return records


def recover_sboxes_from_records(
    records: list[tuple[int, int, int, int, dict[tuple[int, int], int]]],
) -> list[list[int]] | None:
    domains: dict[tuple[int, int], set[int]] = {
        (cls, input_value): set()
        for cls in range(4)
        for input_value in range(16)
    }
    for _, cls, input_value, output_value, _ in records:
        domains[(cls, input_value)].add(output_value)

    while True:
        changed = False
        for cls in range(4):
            taken = {
                next(iter(domains[(cls, input_value)]))
                for input_value in range(16)
                if len(domains[(cls, input_value)]) == 1
            }
            for input_value in range(16):
                current = domains[(cls, input_value)]
                if len(current) <= 1:
                    continue
                pruned = current - taken
                if pruned and pruned != current:
                    domains[(cls, input_value)] = pruned
                    changed = True

        if any(len(values) == 0 for values in domains.values()):
            return None

        fixed = {
            key: next(iter(values))
            for key, values in domains.items()
            if len(values) == 1
        }

        filtered_records = []
        for pos, cls, input_value, output_value, constraints in records:
            if output_value not in domains[(cls, input_value)]:
                continue
            consistent = True
            for key, value in constraints.items():
                fixed_value = fixed.get(key)
                if fixed_value is not None and fixed_value != value:
                    consistent = False
                    break
                if value not in domains[key]:
                    consistent = False
                    break
            if consistent:
                filtered_records.append((pos, cls, input_value, output_value, constraints))

        if len(filtered_records) != len(records):
            records = filtered_records
            changed = True

        if not records:
            return None

        for key in domains:
            surviving = {
                output_value
                for _, cls, input_value, output_value, _ in records
                if key == (cls, input_value)
            }
            if surviving and surviving != domains[key]:
                domains[key] = surviving
                changed = True

        if any(len(values) == 0 for values in domains.values()):
            return None

        if not changed:
            break

    if any(len(values) != 1 for values in domains.values()):
        return None

    return [
        [next(iter(domains[(cls, input_value)])) for input_value in range(16)]
        for cls in range(4)
    ]


def recover_sboxes_weak_instance(
    session: ChallengeSession,
    rounds: int,
) -> list[list[int]] | None:
    zero = session.query_blocks("E", [0])[0]
    if zero != 0:
        return None

    lifted_queries: dict[int, list[int]] = {}
    image_queries: dict[int, list[int]] = {}

    for pos in range(NIBBLES):
        lifted_inputs = [input_value << (4 * pos) for input_value in range(16)]
        image_inputs = [permute_bits(input_value << (4 * pos)) for input_value in range(16)]
        lifted_queries[pos] = [
            permute_bits(value)
            for value in session.query_blocks("E", lifted_inputs)
        ]
        image_queries[pos] = [
            permute_bits(value)
            for value in session.query_blocks("E", image_inputs)
        ]

    recovered = recover_sboxes_from_records(
        build_consistency_records(lifted_queries, image_queries)
    )
    if recovered is None:
        return None

    probe_inputs = [
        0,
        (1 << 64) - 1,
        0x0123456789ABCDEF,
        0xFEDCBA9876543210,
        0x1337133713371337,
        0x4242424242424242,
    ]
    for block, oracle in zip(probe_inputs, session.query_blocks("E", probe_inputs), strict=True):
        if encrypt_block(block, rounds, recovered) != oracle:
            return None

    return recovered


def solve_instance(host: str, port: int, solver_timeout: int) -> None:
    attempt = 0
    while True:
        attempt += 1
        session = ChallengeSession(host, port)
        try:
            rounds = session.read_banner()
            print(f"[+] attempt {attempt}: connected, rounds={rounds}")

            sboxes = recover_sboxes_weak_instance(session, rounds)
            if sboxes is None:
                print(f"[-] attempt {attempt}: instance not in the weak class, reconnecting")
                continue

            print(f"[+] attempt {attempt}: recovered weak-instance sboxes")
            session.start_challenge()
            for index in range(100):
                challenge_hex = session.read_challenge()
                challenge = u64_from_hex_le(challenge_hex)
                response = encrypt_block(challenge, rounds, sboxes)
                session.send_response(hex_le_from_u64(response))
                if (index + 1) % 10 == 0:
                    print(f"[+] solved {index + 1}/100")

            print(session.read_remaining())
            return
        finally:
            session.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="chall.blackpinker.com")
    parser.add_argument("--port", default=20125, type=int)
    parser.add_argument("--solver-timeout", default=900, type=int)
    args = parser.parse_args()

    solve_instance(args.host, args.port, args.solver_timeout)


if __name__ == "__main__":
    main()
