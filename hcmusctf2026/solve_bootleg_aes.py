#!/usr/bin/env python3
"""
Solve: bootleg_aes (Crypto - Easy)
The encryption script logged the AES key via `echo $x`.
Key is in log.txt: c9a391c6f65bbb38582044fd78143fe72310e96bf67401039b3b6478455a1622
IV was random and not logged, but the 256-byte pad = 16 AES blocks.
Flag starts at block 17. In CBC mode, block i (i > 1) decrypts as:
  P[i] = Decrypt(K, C[i]) XOR C[i-1]
So blocks 17+ can be decrypted without knowing IV.
"""

from Crypto.Cipher import AES

KEY = bytes.fromhex('c9a391c6f65bbb38582044fd78143fe72310e96bf67401039b3b6478455a1622')

with open('practice/2023-archive/ctfs/HCMUS/2023/Quals/crypto/bootleg_aes/ciphertext.bin', 'rb') as f:
    ct = f.read()

# Decrypt blocks 2..N without IV (block 1 is pad, blocks 17+ contain flag)
cipher = AES.new(KEY, AES.MODE_ECB)
blocks = [ct[i:i+16] for i in range(0, len(ct), 16)]

pt = b''
for i in range(1, len(blocks)):
    decrypted = cipher.decrypt(blocks[i])
    pt += bytes(a ^ b for a, b in zip(decrypted, blocks[i-1]))

# Flag is somewhere in the decrypted data - search for it
idx = pt.find(b'HCMUS-CTF')
flag = pt[idx:].split(b'\n')[0].decode()
print(flag)
