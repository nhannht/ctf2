# Crypto101 Write-up

## Challenge Summary

The challenge gives `challenge.sage` and `output.txt`. The server creates an
elliptic curve over `Zmod(p^4)`, chooses one hidden point `P`, derives 24 hidden
multiples `Q_i`, and publishes 120 random byte combinations:

```python
R = [sum([x * y for x, y in zip(ci, Q)]) for ci in c]
key = md5(str(sum(Q)).encode()).digest()
```

The goal is to recover `sum(Q)` and decrypt the AES-ECB ciphertext.

## Artifacts

- Challenge archive: `crypto101.zip`
- Reconstructed one-shot solver: `solve.sage`

## Recovering the Curve

For each public point `(x, y)`, the curve equation gives:

```text
y^2 - x^3 - a*x - b == 0 mod p^4
```

Taking differences between points eliminates `b`. GCDs of the resulting
relations reveal `p^4`, and therefore `p`.

Recovered prime:

```text
p = 98157186733344025409544268114685952947062826455672779162056866933696329360077
```

Once `p^4` is known, solve two curve equations to recover `a` and `b` modulo
`p^4`, then rebuild the curve in Sage.

## Formal Log Leak

Let `N = #E(F_p)`. Multiplying each public `R_i` by `N` sends it into the formal
group kernel modulo `p`.

For a projective point on a short Weierstrass curve, use the formal parameter:

```text
t = -X / Y mod p^4
```

Here `t` is divisible by `p`, and the formal logarithm satisfies
`log(t) = t mod p^4`. So:

```text
z_i = (t_i / p) mod p^3
```

Each `z_i` is the same byte combination of the hidden scalar logs of `Q_i`.
This converts the elliptic-curve problem into a linear hidden-byte problem over
`Z/(p^3)`.

## Lattice Reduction

Build the relation lattice for the 120 values `z_i`:

```text
v_1*z_1 + ... + v_120*z_120 == 0 mod p^3
```

LLL returns 96 short relations, matching `120 - 24`. The right kernel of those
relations is 24-dimensional and contains the byte coefficient columns used to
build the public `R_i`.

Do not use exact CVP here. It is slow and memory-heavy. After LLL, the intended
shortcut is that bounded byte columns are already exposed by small translations
of the reduced kernel basis. One basis vector had all entries in `[-255, 0]`;
negating it gave a valid byte column, and adding/subtracting nearby reduced
basis vectors recovered 24 independent byte-valued columns in `[0, 255]`.

## Recovering the Key

With the recovered byte matrix `C`, solve for coefficients `d_i` such that:

```text
C^T d = (1, 1, ..., 1)
```

Then combine the public points:

```python
S = sum(d_i * R_i)
key = md5(str(S).encode()).digest()
```

Decrypting the ciphertext with AES-ECB and PKCS#7 unpadding gives the flag.

## Flag

```text
HCMUS-CTF{tH3_L4tT1cE_w4$_r3dUc3D_bY_LLL_th3n_BKZ_b3t4_40_$H0rT_v3cT0r$_p4D1c_f0Rm4L_Gr0Up_L0G$_h3n$3L_L1fT$_m0d_p4_t0_p3_t0_p$_r3c0v3r_th3_k3y_fr0m_bYt3_c0mb0$_n0_m0r3_h0m3Br3W_CrYpT0$}
```

## Reproduction

Run the retained solver:

```bash
env HOME=/tmp sage problems/crypto101/solve.sage
```
