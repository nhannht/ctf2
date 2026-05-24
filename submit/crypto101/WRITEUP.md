# Crypto101

Category: `crypto`  
Status: `solved`  
Flag: `HCMUS-CTF{tH3_L4tT1cE_w4$_r3dUc3D_bY_LLL_th3n_BKZ_b3t4_40_$H0rT_v3cT0r$_p4D1c_f0Rm4L_Gr0Up_L0G$_h3n$3L_L1fT$_m0d_p4_t0_p3_t0_p$_r3c0v3r_th3_k3y_fr0m_bYt3_c0mb0$_n0_m0r3_h0m3Br3W_CrYpT0$}`

Source bundle: `https://github.com/nhannht/ctf2/tree/master/submit/crypto101`

## Summary

This challenge bundled an elliptic-curve construction over `Z/(p^4)` with a
homemade “random linear combination” layer and an AES-ECB ciphertext. The
important step was to stop treating the public points as a generic EC discrete
log problem and move them into the formal group, where the arithmetic becomes
linear modulo `p^3`.

Once the public points were linearized, the remaining task was a bounded hidden
byte-combination problem. Lattice reduction exposed the byte columns, and the
same public combinations then recovered the AES key material.

## Artifacts

- Challenge archive: `problems/crypto101/crypto101.zip`
- Included files inside the archive:
  - `challenge.sage`
  - `output.txt`

## Key Observation

The challenge publishes 120 random byte combinations of 24 hidden points:

```python
R = [sum([x * y for x, y in zip(ci, Q)]) for ci in c]
key = md5(str(sum(Q)).encode()).digest()
```

The key insight is that multiplying each public point by `N = #E(F_p)` pushes
it into the formal-group kernel modulo `p`. In that region, the formal
logarithm turns the elliptic-curve combinations into ordinary linear
combinations over `Z/(p^3)`.

## Early Wrong Model

The first temptation was to treat the public points as a generic elliptic-curve
discrete-log instance and then force the byte layer with exact CVP. That was
the wrong abstraction twice over:

- the hard-looking curve arithmetic becomes linear after pushing into the
  formal-group kernel
- the byte-combination layer does not need an exact closest-vector solve once
  LLL exposes the short column structure

The challenge only becomes tractable after simplifying the algebra first and
using lattice reduction as a structure-recovery step rather than as a
last-resort optimizer.

## Solve Path

### 1. Recover the curve modulus and parameters

For each public point `(x, y)`, the short-Weierstrass equation gives:

```text
y^2 - x^3 - a*x - b == 0 mod p^4
```

Taking pairwise differences eliminates `b`. A GCD over those relations recovers
`p^4`, and therefore `p`.

Recovered prime:

```text
p = 98157186733344025409544268114685952947062826455672779162056866933696329360077
```

Once `p^4` is known, two point equations are enough to solve for `a` and `b`
modulo `p^4`.

### 2. Move the public points into the formal group

After multiplying each public `R_i` by `N = #E(F_p)`, use the standard formal
parameter:

```text
t = -X / Y mod p^4
```

In the kernel, `t` is divisible by `p`, and the formal logarithm collapses to:

```text
log(t) = t mod p^4
```

So we get:

```text
z_i = (t_i / p) mod p^3
```

Each `z_i` is now the same hidden byte combination, but in a linear ring.

### 3. Use lattice reduction to recover the byte columns

The 120 public `z_i` values satisfy linear relations:

```text
v_1*z_1 + ... + v_120*z_120 == 0 mod p^3
```

LLL returns `96` short relations, which matches the expected nullity
`120 - 24`. The right kernel of those relations contains the byte coefficient
columns used to build the public combinations.

The practical shortcut is important here. Exact CVP was the wrong path. After
LLL, the bounded byte columns were already exposed by short translations of the
reduced basis. One basis vector landed entirely in `[-255, 0]`; negating it
gave a valid byte column, and nearby basis combinations recovered the other 23.

### 4. Recombine the public points and derive the AES key

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

## Proof

Decisive intermediate artifact:

```text
p = 98157186733344025409544268114685952947062826455672779162056866933696329360077
```

Decisive final derivation:

```python
S = sum(d_i * R_i)
key = md5(str(S).encode()).digest()
```

## Reproduction

We did not preserve a final one-shot repo-local solver script for this
challenge. The solve was completed interactively from the shipped
`challenge.sage` logic and `output.txt`, and the exact values we printed and
used were the ones above:

- recovered modulus prime `p`
- recovered linear combination `S`
- derived AES key `md5(str(S).encode()).digest()`

So this page records the exact algebra and code fragments that produced the
flag rather than pretending there was a cleaner retained command history.

## Files

- `problems/crypto101/crypto101.zip`
