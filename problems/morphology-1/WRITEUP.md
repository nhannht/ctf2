# Funny Helicopter Morphology - 1

## Files

- `dist.zip` contains `server_new.cpp` and a `Makefile`.
- The live service is `nc chall.blackpinker.com 20114`.

## Challenge structure

The server builds two related secrets:

1. An auxiliary ring secret `T` of dimension 8.
2. A main-ring secret `S` of dimension 16 built by concatenating the first-tower
   coefficient vectors of two auxiliary samples:

   - `S0 = B0 * T + K0`
   - `S1 = B1 * T + K1`

`PARAMS` returns a flag ciphertext produced by XORing the flag body with bytes
derived from `GetPolyCoefficientsSigned(T)`.

`CHALLENGE` uses `S` as the secret in a separate BFV-like encryption oracle.

## Immediate bug

`EVALSUM` leaks both auxiliary samples:

- `B0`, `B1`
- `S0`, `S1`

The important implementation detail is that `S` is not some hidden transform of
those values. It is literally rebuilt from:

```cpp
auto coeffs = GetPolyCoefficients(s_samp);
s_combined.insert(s_combined.end(), coeffs.begin(), coeffs.end());
```

So `EVALSUM` fully reveals the 16 coefficients of the secret `S` later used by
`CHALLENGE`.

## The modulus detail that mattered

The printed main-ring `q0` from `PARAMS` is:

`1152921504606845473`

That is **not** the modulus used by the leaked auxiliary coefficients.

The auxiliary `B` output prints `-1` as:

`1329227995784914399470124172730259968`

So the auxiliary composite modulus is:

`1329227995784914399470124172730259969`

Factoring that gave:

- `1152921504606846097`
- `1152921504606846577`

The first auxiliary CRT tower is the one that matches the leaked `S0`, `S1`
coefficients:

`q0_aux = 1152921504606846097`

Using the main-ring `q0` in the recovery model makes the equations inconsistent.

## Why the signed view of `T` is awkward

`T` is sampled with coefficients in:

- `T_MIN = 2^59`
- `T_MAX = 2^60`

But the flag key is built from:

```cpp
GetPolyCoefficientsSigned(T)
```

on the first auxiliary tower.

Since `q0_aux` is just below `2^60`, the signed view of a coefficient is usually
`coeff - q0_aux`, i.e. a large negative `int64_t`, not the original sampled
positive integer.

That signed first-tower view is the byte stream used for the XOR mask.

## Useful interaction order

For one connection:

1. `EVALSUM`
2. `PARAMS`
3. `CHALLENGE 1 0`

That keeps the same `T`/`S` for all outputs and also leaks:

- `E[0]`
- `E[1]`

which are the first two signed coefficients of `K0`.

## Recovery model

After mapping the huge `B` values back to ternary `{-1, 0, 1}`, each leaked row
becomes:

`A * v + e = s + k * q0_aux`

where:

- `v` is the first-tower coefficient vector of `T`
- `e` is the small auxiliary error vector from `K0`, `K1`
- `k` is a small integer wrap vector

Constraints that worked:

- `v[i]` sorted
- `2^59 <= v[i] <= q0_aux - 1`
- `e[0]`, `e[1]` fixed from `CHALLENGE`
- remaining `e[i]` bounded in a moderate window

Using `z3` with those constraints recovered a **unique** wrap vector `k` for a
sample instance.

After fixing `k`, ordinary least squares on the linear system was enough to
recover an approximate `v`, and that approximate `v` was already good enough to
decrypt most of the flag body into readable text.

## What the approximate decrypt looked like

A typical recovered body looked like:

```text
?4tt1ce-?r-d1d-y?8-brute?-How-Lo?g-To-m4?H-1t-t4?3?...
```

Across several fresh instances, the stable parts were:

```text
?4tt1ce-?r-d1d-y?u-brute?-How-Long-To-m4?H-1t-t4?3?
```

The strongest candidate reconstructed from the consensus was:

```text
l4tt1ce-0r-d1d-y0u-brute?-How-Long-To-m4tH-1t-t4k3?
```

and the submitted flag candidate was:

```text
HCMUS-CTF{l4tt1ce-0r-d1d-y0u-brute?-How-Long-To-m4tH-1t-t4k3?}
```

That submission returned:

```json
{"kind":"badFlag","message":"The flag was incorrect.","data":null}
```

So the analysis is close, but not finished. The remaining errors are likely in
the early ambiguous block around:

- `0r` / `z3` / similar
- `y0u` / nearby leetspeak variant
- `m4tH` / `m4th`
- `t4k3?` tail before the random hex padding

## Current status

What is confirmed:

- `EVALSUM` completely leaks the `S` used by `CHALLENGE`.
- The auxiliary first-tower modulus is `1152921504606846097`.
- The flag key comes from the signed first-tower coefficients of `T`.
- The wrap vector `k` is uniquely recoverable per instance.
- Least-squares recovery is enough to expose most of the plaintext body.

What remains:

- Turn the approximate plaintext recovery into an exact solve.
- The clean next step is to combine the known plaintext structure with the exact
  linear equations and search the remaining ambiguous bytes directly, instead of
  relying on unconstrained least squares.
