"""Z3-based symbolic solver for the real SUBLEQ flag check.

Strategy:
- Control flow is input-independent (verified empirically). The same sequence
  of (a, b, c) operand triples executes for every input we have tried.
- Each SUBLEQ step is `mem[b] -= mem[a]`. With control flow fixed, every cell
  value at every time step is an *affine* function of the 40 input bytes.
- We record the concrete trace once (with input = 0..0), reading each step's
  (a, b, c) and the sign of mem[b] after the subtraction.
- We replay symbolically with input as 40 Z3 Int variables, asserting that
  the sign of mem[b] after each subtraction matches the concrete sign. That
  pins us to the same execution path.
- Finally we assert mem[SUCCESS_CELL] == 1 and ask Z3 to solve.
"""
import struct
import time
from pathlib import Path
from z3 import Int, IntVal, Solver, sat, And, If, Or, Sum

BIN = Path(__file__).resolve().parent / 'chall'
HIDDEN_OFF = 0x1cc080
HIDDEN_SIZE = 0x6c4d8
N_WORDS = HIDDEN_SIZE // 8         # 55,451
MAX_ADDR = 0xd89a                  # 55,450
MAX_ITERS = 0x3626c                # 221,804
LEN_CELL = 55405
SUCCESS_CELL = 55407
INPUT_BASE = 55411
INPUT_LEN = 40

def load_initial():
    data = open(BIN, 'rb').read()
    return list(struct.unpack(f'<{N_WORDS}q', data[HIDDEN_OFF:HIDDEN_OFF+HIDDEN_SIZE]))

def concrete_trace(password: bytes):
    """Run concretely, return list of (ip, a, b, c, new_b_sign) per step."""
    mem = load_initial()
    mem[LEN_CELL] = len(password)
    for i in range(INPUT_LEN):
        mem[INPUT_BASE + i] = password[i] if i < len(password) else 0
    ip = 0
    iters = 0
    trace = []
    rc = 'limit'
    while iters < MAX_ITERS:
        if ip < 0 or ip + 2 > MAX_ADDR: rc='oob_ip'; break
        a = mem[ip]; b = mem[ip+1]; c = mem[ip+2]
        if a < 0 or b < 0 or a > MAX_ADDR or b > MAX_ADDR: rc='oob'; break
        new = mem[b] - mem[a]
        mem[b] = new
        sign = -1 if new <= 0 else 1
        trace.append((ip, a, b, c, sign))
        new_ip = c if new <= 0 else ip + 3
        if new_ip < 0: rc='halt'; break
        if new_ip + 2 > MAX_ADDR: rc='oob_next'; break
        ip = new_ip; iters += 1
    return rc, trace, mem


def main():
    t0 = time.time()
    # 1. Record the concrete trace using ALL-ZERO input (a safe choice).
    rc, trace, _ = concrete_trace(b'\x00' * INPUT_LEN)
    print(f'Concrete trace recorded: rc={rc}, {len(trace)} steps  ({time.time()-t0:.2f}s)')

    # 2. Build symbolic memory.
    # Use Z3 Int for unbounded integer arithmetic. SUBLEQ stays small here.
    s = Solver()
    input_vars = [Int(f'b{i}') for i in range(INPUT_LEN)]
    for v in input_vars:
        s.add(v >= 0, v <= 0xff)
        # Constrain to printable for sanity (flags are usually printable). We
        # can drop this if Z3 returns UNSAT.
        s.add(Or(v == 0, And(v >= 0x20, v <= 0x7e)))

    # Initialize symbolic memory: every cell is concrete (IntVal) except the
    # input cells which are the symbolic variables and the length cell which
    # is 40 (matching INPUT_LEN, what the host installs).
    initial_mem = load_initial()
    initial_mem[LEN_CELL] = INPUT_LEN
    mem = [IntVal(v) for v in initial_mem]
    for i in range(INPUT_LEN):
        mem[INPUT_BASE + i] = input_vars[i]

    # 3. Replay trace symbolically.
    for step, (ip, a, b, c, sign) in enumerate(trace):
        new_val = mem[b] - mem[a]
        mem[b] = new_val
        # Sign constraint to pin to the concrete path.
        if sign == -1:
            s.add(new_val <= 0)
        else:
            s.add(new_val > 0)
        if step % 500 == 0:
            print(f'  step {step}/{len(trace)}  ({time.time()-t0:.2f}s)')

    # 4. Success assertion.
    s.add(mem[SUCCESS_CELL] == 1)
    print(f'\nModel built, calling Z3 solver...  ({time.time()-t0:.2f}s)')

    result = s.check()
    print(f'  z3: {result}  ({time.time()-t0:.2f}s)')
    if result == sat:
        m = s.model()
        flag_bytes = bytes(m[v].as_long() for v in input_vars)
        print(f'\nFLAG bytes: {flag_bytes}')
        print(f'as ascii: {flag_bytes.decode("ascii", "replace")!r}')
    else:
        print('UNSAT - try dropping the printable-byte constraint.')


if __name__ == '__main__':
    main()
