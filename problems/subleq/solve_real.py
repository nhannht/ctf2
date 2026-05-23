"""Emulator for the *real* SUBLEQ inside the hidden segment.

Layout extracted from the hidden main at vaddr 0x76c558:
  malloc size:       0x6c4d8 bytes  -> 55,451 words (one trailing word)
  initial memory:    copied from vaddr 0x700080 (file 0x1cc080)
  iteration limit:   0x3626c        =  221,804
  max address (cmp): 0xd89a         =  55,450
  length cell:       byte 0x6b968   -> word 55,405
  input base:        byte 0x6b998   -> word 55,411  (40 bytes, one per word)

SUBLEQ semantics match disasm at 0x76c711:
  for ip in steps of 3:
    a, b, c = mem[ip], mem[ip+1], mem[ip+2]
    if (a|b) negative OR a>MAX_ADDR OR b>MAX_ADDR: HALT (error)
    mem[b] -= mem[a]
    new_ip = (mem[b] <= 0) ? c : ip+3
    if --iter_count == 0: HALT (limit)
    if new_ip < 0: HALT (clean, success path)
    if new_ip+2 > MAX_ADDR: HALT (error)
    ip = new_ip

Success is whatever the host main checks afterwards. From the disasm: after
run_subleq returns, ANOTHER code path runs. We have not yet identified which
single cell encodes "ok"; we'll find it empirically by comparing final memory
states.
"""
import struct
from pathlib import Path

BIN = Path(__file__).resolve().parent / 'chall'
HIDDEN_OFF = 0x1cc080
HIDDEN_SIZE = 0x6c4d8
N_WORDS = HIDDEN_SIZE // 8
MAX_ADDR = 0xd89a  # 55450
MAX_ITERS = 0x3626c  # 221804
LEN_CELL = 55405     # 0x6b968 / 8
SUCCESS_CELL = 55407 # 0x6b978 / 8
INPUT_BASE = 55411   # 0x6b998 / 8
INPUT_LEN = 40

def load_initial():
    data = open(BIN, 'rb').read()
    return list(struct.unpack(f'<{N_WORDS}q', data[HIDDEN_OFF:HIDDEN_OFF+HIDDEN_SIZE]))

def run(password: bytes, *, capture_ips=False):
    mem = load_initial()
    mem[LEN_CELL] = len(password)
    for i in range(INPUT_LEN):
        mem[INPUT_BASE + i] = password[i] if i < len(password) else 0
    ip = 0
    iters = 0
    rc = 'limit'
    ips = [] if capture_ips else None
    while iters < MAX_ITERS:
        if ip < 0 or ip + 2 > MAX_ADDR:
            rc = 'oob_ip'; break
        a = mem[ip]; b = mem[ip+1]; c = mem[ip+2]
        if a < 0 or b < 0 or a > MAX_ADDR or b > MAX_ADDR:
            rc = 'oob_operand'; break
        if capture_ips: ips.append(ip)
        new = mem[b] - mem[a]
        mem[b] = new
        new_ip = c if new <= 0 else ip + 3
        if new_ip < 0:
            rc = 'halt'; break
        if new_ip + 2 > MAX_ADDR:
            rc = 'oob_next_ip'; break
        ip = new_ip
        iters += 1
    return rc, iters, mem, ips

if __name__ == '__main__':
    for pw in [b'', b'A', b'A'*40, b'B'*40, b'\x00'*40, b'flag{aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa}']:
        rc, it, mem, _ = run(pw)
        print(f'  len={len(pw):3d}  rc={rc:8s}  iters={it:7d}')
