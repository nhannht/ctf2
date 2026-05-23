"""SUBLEQ emulator matching the host wrapper in chall.

Memory: 31883 words (signed 64-bit). Loaded from SUBLEQ_INITIAL_MEM at file offset 0x124040.
Input loaded by load_input():
  mem[31613] = input length (clamped non-negative)
  mem[31619 + i] = input byte i, for i in 0..39 (zero if i >= length)
Success condition: run_subleq returns 0 AND mem[31615] == 1.

SUBLEQ semantics (matching run_subleq disasm):
  Each instruction at ip is triple (a, b, c) where ip, ip+1, ip+2 are mem addresses (so ip moves in steps of 3).
  Constraints checked at each step: ip+2 <= 0x7c8a (31882), a >= 0, b >= 0, a <= 31882, b <= 31882.
  Execute: mem[b] -= mem[a]. If result <= 0: new_ip = c. Else new_ip = ip + 3.
  After update, if new_ip < 0: HALT (success-style). If new_ip > 0x7c8a: also halt with error.
  Max iterations: 0x1f22b = 127531. Hitting the cap returns -3 (failure).
"""
import struct
from pathlib import Path

BIN = Path(__file__).resolve().parent / 'chall'
SUBLEQ_OFF = 0x124040
SUBLEQ_SIZE = 0x3e458  # bytes
N_WORDS = SUBLEQ_SIZE // 8  # 31883
MAX_ADDR = 0x7c8a  # 31882
MAX_ITERS = 0x1f22b  # 127531
INPUT_LEN_ADDR = 31517  # 0x3d8e8 / 8
SUCCESS_ADDR = 31519    # 0x3d8f8 / 8
INPUT_BASE = 31523      # 0x3d918 / 8

def load_initial():
    data = open(BIN, 'rb').read()
    return list(struct.unpack('<' + 'q' * N_WORDS, data[SUBLEQ_OFF:SUBLEQ_OFF + SUBLEQ_SIZE]))

def run(password: bytes, trace_writes_to=None, trace=False):
    """Run the VM. Returns (rc, mem). rc==0 on clean halt (neg jump), nonzero on error."""
    mem = load_initial()
    # load_input
    mem[INPUT_LEN_ADDR] = len(password)
    for i in range(40):
        mem[INPUT_BASE + i] = password[i] if i < len(password) else 0
    ip = 0
    iters = 0
    rc = -3  # iteration limit
    while iters < MAX_ITERS:
        if ip + 2 > MAX_ADDR:
            rc = -1
            break
        a = mem[ip]
        b = mem[ip + 1]
        c = mem[ip + 2]
        if a < 0 or b < 0 or a > MAX_ADDR or b > MAX_ADDR:
            rc = -2
            break
        new = mem[b] - mem[a]
        mem[b] = new
        if trace_writes_to is not None and b == trace_writes_to:
            print(f'iter {iters:6d} ip={ip:5d} a={a:5d} b={b:5d} c={c:5d}  mem[a]={mem[a]} mem[b]<-{new}')
        if new <= 0:
            new_ip = c
        else:
            new_ip = ip + 3
        if trace:
            print(f'{iters:6d} ip={ip:5d} a={a:5d} b={b:5d} c={c:5d}  mem[b]<-{new}  -> ip={new_ip}')
        if new_ip < 0:
            rc = 0  # clean halt
            break
        if new_ip > MAX_ADDR:
            rc = -4
            break
        ip = new_ip
        iters += 1
    return rc, mem

if __name__ == '__main__':
    # Sanity check: run with empty input
    rc, mem = run(b'')
    print(f'empty input: rc={rc}, mem[success]={mem[SUCCESS_ADDR]}, mem[len]={mem[INPUT_LEN_ADDR]}')

    # Run with all-A 40-byte input
    rc, mem = run(b'A' * 40)
    print(f'AAAA..: rc={rc}, mem[success]={mem[SUCCESS_ADDR]}')

    # Run with all-zero 40-byte input
    rc, mem = run(b'\x00' * 40)
    print(f'NULx40: rc={rc}, mem[success]={mem[SUCCESS_ADDR]}')

    # Run with printable test
    rc, mem = run(b'flag{test_test_test_test_test_test_test_}')
    print(f'flag{{test..}}: rc={rc}, mem[success]={mem[SUCCESS_ADDR]}, len={len(b"flag{test_test_test_test_test_test_test_}")}')
