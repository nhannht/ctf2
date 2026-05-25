#!/usr/bin/env sage

import ast
import random
import sys
import zipfile
from collections import deque
from hashlib import md5
from math import isqrt
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from fpylll import IntegerMatrix, LLL


OUTPUT_MEMBER = "public/output.txt"
RELATION_DELTA = 0.99
ROW_TRIES = 3000
RANK_PRIME = 1000003


def resolve_archive():
    candidates = [
        Path.cwd() / "crypto101.zip",
        Path.cwd() / "problems" / "crypto101" / "crypto101.zip",
    ]
    if sys.argv:
        candidates.append(Path(sys.argv[0]).resolve().with_name("crypto101.zip"))

    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            return resolved

    raise RuntimeError("could not locate crypto101.zip; run from the repo root or problems/crypto101/")


def load_output():
    with zipfile.ZipFile(resolve_archive()) as handle:
        lines = handle.read(OUTPUT_MEMBER).decode().splitlines()
    points = [(Integer(x), Integer(y)) for x, y in ast.literal_eval(lines[1])]
    ciphertext = bytes.fromhex(lines[2].strip())
    return points, ciphertext


def recover_modulus_power(points):
    modulus_power = Integer(0)
    limit = min(len(points), 28)
    for i in range(limit - 2):
        x1, y1 = points[i]
        f1 = y1**2 - x1**3
        for j in range(i + 1, limit - 1):
            x2, y2 = points[j]
            f2 = y2**2 - x2**3
            for k in range(j + 1, limit):
                x3, y3 = points[k]
                f3 = y3**2 - x3**3
                expr = (f1 - f2) * (x2 - x3) - (f2 - f3) * (x1 - x2)
                modulus_power = gcd(modulus_power, abs(expr))
    if modulus_power == 0:
        raise RuntimeError("failed to recover p^4")
    prime = Integer(isqrt(isqrt(int(modulus_power))))
    if prime**4 != modulus_power:
        raise RuntimeError("recovered modulus is not a fourth power")
    return modulus_power, prime


def recover_curve_parameters(points, modulus_power):
    for i, (x1, y1) in enumerate(points):
        f1 = (y1**2 - x1**3) % modulus_power
        for j in range(i + 1, len(points)):
            x2, y2 = points[j]
            f2 = (y2**2 - x2**3) % modulus_power
            delta = (x1 - x2) % modulus_power
            if gcd(delta, modulus_power) != 1:
                continue
            a_value = ((f1 - f2) * inverse_mod(delta, modulus_power)) % modulus_power
            b_value = (f1 - a_value * x1) % modulus_power
            return Integer(a_value), Integer(b_value)
    raise RuntimeError("failed to recover curve parameters")


def recover_curve_order(prime, a_value, b_value):
    curve_fp = EllipticCurve(GF(prime), [Integer(a_value % prime), Integer(b_value % prime)])
    return Integer(curve_fp.order())


def recover_z_values(points, modulus_power, prime, curve_order, a_value, b_value):
    curve = EllipticCurve(Zmod(modulus_power), [a_value, b_value])
    curve_points = [curve(x, y) for x, y in points]
    z_values = []
    for point in curve_points:
        kernel_point = curve_order * point
        X, Y, Z = [Integer(coord) for coord in kernel_point]
        t_value = (-X * inverse_mod(Y, modulus_power)) % modulus_power
        if t_value % prime != 0:
            raise RuntimeError("formal parameter did not land in p * Z/(p^4)")
        z_values.append(Integer(t_value // prime) % (prime**3))
    return curve, curve_points, z_values


def recover_relations(z_values, prime):
    modulus = int(prime**3)
    count = len(z_values)
    matrix_lll = IntegerMatrix(count + 1, count + 1)
    for index, value in enumerate(z_values):
        matrix_lll[index, index] = 1
        matrix_lll[index, count] = int(value)
    matrix_lll[count, count] = modulus
    LLL.reduction(matrix_lll, delta=RELATION_DELTA)

    relations = []
    for row_index in range(count + 1):
        if int(matrix_lll[row_index, count]) != 0:
            continue
        row = [int(matrix_lll[row_index, col]) for col in range(count)]
        if any(row):
            relations.append(row)
    if len(relations) != count - 24:
        raise RuntimeError(f"expected {count - 24} relations, got {len(relations)}")
    return relations


def recover_kernel_basis(relations):
    relation_matrix = matrix(ZZ, relations)
    if relation_matrix.rank() != len(relations):
        raise RuntimeError("relation matrix did not have full expected rank")
    basis = relation_matrix.right_kernel().basis_matrix().LLL()
    if basis.nrows() != 24:
        raise RuntimeError(f"expected 24 kernel rows, got {basis.nrows()}")
    return [tuple(int(value) for value in basis.row(index)) for index in range(basis.nrows())]


def add_rank_mod_prime(vector_value, basis_rows, pivot_columns):
    row = [value % RANK_PRIME for value in vector_value]
    for pivot, basis_row in zip(pivot_columns, basis_rows):
        coefficient = row[pivot]
        if coefficient:
            row = [(entry - coefficient * basis_entry) % RANK_PRIME for entry, basis_entry in zip(row, basis_row)]
    for column, value in enumerate(row):
        if value:
            inverse = pow(value, -1, RANK_PRIME)
            row = [(entry * inverse) % RANK_PRIME for entry in row]
            pivot_columns.append(column)
            basis_rows.append(row)
            return True
    return False


def recover_columns(kernel_basis):
    base = tuple(-value for value in kernel_basis[-1])
    if not all(0 <= value <= 255 for value in base):
        raise RuntimeError("expected the last reduced basis row to negate into a byte column")

    steps = kernel_basis[:-1]
    seen = {base}
    queue = deque([base])
    rank_basis = []
    pivot_columns = []
    columns = []

    if add_rank_mod_prime(base, rank_basis, pivot_columns):
        columns.append(base)

    while queue and len(columns) < 24:
        current = queue.popleft()
        for step in steps:
            for sign in (1, -1):
                candidate = tuple(current[index] + sign * step[index] for index in range(len(current)))
                if candidate in seen or not all(0 <= value <= 255 for value in candidate):
                    continue
                seen.add(candidate)
                queue.append(candidate)
                if add_rank_mod_prime(candidate, rank_basis, pivot_columns):
                    columns.append(candidate)
                    if len(columns) == 24:
                        break
            if len(columns) == 24:
                break

    if len(columns) != 24:
        raise RuntimeError(f"expected 24 independent byte columns, got {len(columns)}")
    return columns


def recover_sum_point(columns, curve_points, curve_order, prime, ciphertext, curve):
    modulus = Integer(curve_order) * prime**3
    ring = Zmod(modulus)
    one_vector = vector(ring, [1] * 24)
    row_indices = list(range(len(curve_points)))

    tries = [tuple(range(24))]
    rng = random.Random(int(1))
    for _ in range(int(ROW_TRIES)):
        tries.append(tuple(rng.sample(row_indices, 24)))

    for subset in tries:
        matrix_rows = Matrix(ring, [[columns[column][row] for column in range(24)] for row in subset])
        try:
            coefficients = matrix_rows.transpose().solve_right(one_vector)
        except Exception:
            continue

        sum_point = curve(0)
        for coefficient, row in zip(coefficients, subset):
            sum_point += Integer(coefficient) * curve_points[row]

        key = md5(str(sum_point).encode()).digest()
        plaintext = AES.new(key, AES.MODE_ECB).decrypt(ciphertext)
        try:
            message = unpad(plaintext, 16)
        except ValueError:
            continue
        if b"HCMUS" in message or b"CTF" in message:
            return subset, sum_point, message

    raise RuntimeError("failed to recover sum(Q) from the recovered columns")


def main():
    points, ciphertext = load_output()

    modulus_power, prime = recover_modulus_power(points)
    a_value, b_value = recover_curve_parameters(points, modulus_power)
    curve_order = recover_curve_order(prime, a_value, b_value)

    curve, curve_points, z_values = recover_z_values(
        points,
        modulus_power,
        prime,
        curve_order,
        a_value,
        b_value,
    )
    relations = recover_relations(z_values, prime)
    kernel_basis = recover_kernel_basis(relations)
    columns = recover_columns(kernel_basis)
    subset, sum_point, message = recover_sum_point(
        columns,
        curve_points,
        curve_order,
        prime,
        ciphertext,
        curve,
    )

    print(f"p = {prime}")
    print(f"a = {a_value}")
    print(f"b = {b_value}")
    print(f"#E(F_p) = {curve_order}")
    print(f"relations = {len(relations)}")
    print(f"columns = {len(columns)}")
    print(f"subset = {subset}")
    print(f"S = {sum_point}")
    print(message.decode())


main()
