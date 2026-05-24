#!/usr/bin/env python3
"""
Solve: falsehood (Crypto - Medium-Easy)
The challenge encrypts the flag with AES-CBC using a random 16-byte key.
The key bytes are coefficients of a degree-15 polynomial f(x).
We get 16 (X, Y) pairs where Y = abs(f(X)).
Since all coefficients are in [0,255] and X > 0, f(X) > 0, so Y = f(X).
Exact polynomial interpolation recovers the coefficients = AES key.
"""

from sympy import interpolate, Poly
from sympy.abc import x
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from binascii import unhexlify


with open('practice/2023-archive/ctfs/HCMUS/2023/Quals/crypto/falsehood/output.txt') as f:
    lines = f.read().strip().split('\n')

hint = eval(lines[0])
ct = unhexlify(lines[1].split('ct = ')[1].split(', ')[0])
iv = unhexlify(lines[1].split('iv = ')[1])

points = [(p[0], p[1]) for p in hint]
poly = interpolate(points, x)
coeffs = Poly(poly, x).all_coeffs()

# Coeffs from highest degree to lowest; key is c_0, c_1, ..., c_15
key_array = [int(c) for c in coeffs[::-1]]
key = b''.join([int(i).to_bytes(1, 'big') for i in key_array])

cipher = AES.new(key, AES.MODE_CBC, iv)
flag = unpad(cipher.decrypt(ct), 16).decode()
print(flag)
