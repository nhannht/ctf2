# Rust In Peace

Category: `crypto`  
Status: `solved`  
Flag: `HCMUS-CTF{TH3_0rAcl3_5P0K3_1N_R0Und5_ANd_tH3_tHR35H0LD_an5w3R3D_1N_P3rMuTaT10N2}`

## Summary

The hint was accurate: this challenge was not meant to be solved by grinding a
large SMT model. The service generates a fresh random key per connection, so we
do not need a universal solver. We only need to wait for a weak instance.

The useful weak class is when `E(0) = 0`. In that case the round structure
collapses enough that single-active-nibble states become informative again, and
the four repeating base S-boxes can be recovered from oracle queries.

## Artifacts

- Live service used during the solve: `chall.blackpinker.com:20702`
- Challenge source: `problems/rust-in-peace/rust-in-peace/chall.rs`
- Solver: `problems/rust-in-peace/solve.py`

## Key Observation

The cipher is a 64-bit SPN with:

- 16 nibbles
- 12 rounds
- a fixed public bit permutation
- four base S-boxes repeated every four nibble positions
- no round keys

If we define the one-round function as `G = P ∘ S`, then public encryption is:

```text
E = P^-1 ∘ G^12
```

So the real target is not the full key schedule. It is the one-round map `G`.
On weak instances where every base S-box maps `0 -> 0`, the all-zero state is a
fixed point and the one-round behavior becomes recoverable from structured
queries.

## Early Wrong Model

The hint was right to warn against heavy solving. The first branch was to force
the full structure directly:

- full SMT over overlapping SHA-256 nibble windows stalled
- brute consistency over all S-box candidates was too slow
- hill climbing on the effective key space was unstable

That failure was useful because it narrowed the real problem down to oracle
selection. Since the service generates a fresh random instance per connection,
the right move was to discard hard instances and wait for a weak one.

## Solve Path

### 1. Stop forcing the heavy model

The early Z3 route was logically valid but practically wrong:

- full SMT over the overlapping SHA-256 nibble windows stalled
- direct S-box recovery by brute consistency was too slow
- hill climbing on the effective key space was unreliable

This is exactly what the hint warned against.

### 2. Reconnect until the instance is weak

Each new connection generates a fresh random set of S-boxes, so the solver
first queries `E(0)`.

If `E(0) != 0`, the instance is discarded immediately.

If `E(0) = 0`, then the instance is in the weak class we want.

### 3. Recover the repeated base S-boxes

For a nibble position `i`, define:

- `A_i(v)`: only nibble `i` is `v`
- `B_i(u)`: the permuted image of a single active nibble

On a weak instance:

```text
G(A_i(v)) = B_i(S_class(i)(v))
```

The solver queries the lifted oracle:

```text
H(x) = P(E(x)) = G^12(x)
```

and uses candidate pairs `(A_i(v), B_i(u))` to derive consistency constraints
of the form:

```text
S_c(a) = b
```

across the four base S-box classes. Because each `S_c` must be a permutation on
`0..15`, the constraint system collapses quickly on weak instances.

### 4. Answer the 100 challenge blocks locally

Once the four base S-boxes are known, local encryption is straightforward.
The solver verifies the recovered round function on extra probes, then switches
into challenge mode and answers all 100 blocks.

## Proof

The live solve hit a weak instance on attempt `18`.

Final service output:

```text
Congratulations! Here is the flag: HCMUS-CTF{TH3_0rAcl3_5P0K3_1N_R0Und5_ANd_tH3_tHR35H0LD_an5w3R3D_1N_P3rMuTaT10N2}
```

## Reproduction

The checked-in solver is the same entry point we used for the final solve. The
exact run shape is:

```bash
uv run python problems/rust-in-peace/solve.py \
  --host chall.blackpinker.com \
  --port 20702
```

If the live instance is not weak, the solver reconnects until it finds one with
`E(0) = 0`, recovers the four repeated base S-boxes, and then answers the 100
challenge blocks.

## Files

- `problems/rust-in-peace/solve.py`
- `problems/rust-in-peace/rust-in-peace/chall.rs`
