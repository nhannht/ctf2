#!/usr/bin/env python3
"""
Solve: CRY1 (Crypto - Easy)
The server sends: encoded = sum(key[i] * ord(flag[i])) for i in 0..25
where key = gen_key(user_id, 26) and user_id = int(time.time()).
Each connection gives a different user_id, hence a different key.
Collect 26 equations (one per connection), solve the 26x26 linear system.
"""

import random
import numpy as np


def gen_key(user_id, n):
    random.seed(user_id)
    return [random.randrange(1024) for _ in range(n)]


def solve(equations, values):
    """
    equations: list of 26 key vectors (each length 26)
    values: list of 26 encoded values
    Returns: the flag string
    """
    A = np.array(equations, dtype=np.float64)
    b = np.array(values, dtype=np.float64)
    x = np.linalg.solve(A, b)
    return ''.join(chr(int(round(v))) for v in x)


# --- For a live server, collect equations like this: ---
# from pwn import remote
# equations = []
# values = []
# for _ in range(26):
#     p = remote('host', port)
#     p.recvuntil(b'Welcome\n')
#     line = p.recvline().decode()
#     # "Here is your encoded flag: <number>\n"
#     val = int(line.split(': ')[1].strip())
#     # user_id is int(time.time()) at connect time
#     # we know our connect time, so we can reproduce the key
#     user_id = int(time.time())  # approximate, may need adjustment
#     key = gen_key(user_id, 26)
#     equations.append(key)
#     values.append(val)
#     p.close()
#     time.sleep(1)  # wait for next second
#
# flag = solve(equations, values)
# print(flag)


# --- Demo with a test flag ---
if __name__ == '__main__':
    test_flag = 'HCMUS-CTF{test_fl4g_here3}'  # exactly 26 chars
    assert len(test_flag) == 26

    equations = []
    values = []
    for uid in range(1000000000, 1000000026):
        key = gen_key(uid, 26)
        val = sum(a * ord(b) for a, b in zip(key, test_flag))
        equations.append(key)
        values.append(val)

    recovered = solve(equations, values)
    print('Test flag:', test_flag)
    print('Recovered:', recovered)
    print('Match:', recovered == test_flag)
