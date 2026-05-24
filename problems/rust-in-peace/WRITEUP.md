# Rust In Peace

Status: solved

Flag:

- `HCMUS-CTF{TH3_0rAcl3_5P0K3_1N_R0Und5_ANd_tH3_tHR35H0LD_an5w3R3D_1N_P3rMuTaT10N2}`

Solved against the live instance:

- `chall.blackpinker.com:20702`

## Hint Interpretation

Title:

- `Rust In Peace`

Hint:

- `It’s truly sad if you’re burning tokens to solve such a fun little challenge.`

What mattered:

- the title was mostly flavor
- the hint was telling us not to force the challenge with a heavy SMT search
- the intended weakness was structural and instance-based

The crucial observation was that the service creates a fresh random key for every
connection. We do not have to solve every possible instance. We only have to
wait for a weak one.

## Challenge Structure

Source:

- `rust-in-peace/chall.rs`

The cipher is a 64-bit SPN:

- 16 nibbles
- 12 rounds
- nibble-wise S-box layer
- fixed public bit permutation
- no round keys at all

The S-boxes come from an 8-byte random key:

```rust
let key = random_bytes(8);
let sboxes = sboxes_from_key(&key);
```

Only four base S-boxes exist and they repeat every four nibbles.

The challenge flow is:

1. arbitrary chosen `E` and `D` oracle queries
2. empty line to start challenge mode
3. 100 random 64-bit blocks
4. answer each with the correct encryption

## What Did Not Work

The original route in `solve.py` modeled the overlapping SHA-256 nibble windows
with Z3.

That model was correct, but it was the wrong practical solve path:

- the live instance timed out repeatedly
- direct SMT over the 4 S-box tables also stalled
- hill climbing on the 28 effective hex nibbles did not converge reliably

This is exactly what the hint was warning about.

## The Real Weakness

Let:

- `S` be the full nibble-wise S-box layer
- `P` be the fixed bit permutation
- `G = P ∘ S`

Then the public encryption oracle is:

- `E = P^{-1} ∘ G^{12}`

So if we can recover the one-round function `G`, we are done.

The instance generator is random per connection, which creates a weak-key class
often enough to exploit:

- reconnect until `E(0) = 0`

Empirically, this happens often because many generated base S-box tuples satisfy
`S0(0)=S1(0)=S2(0)=S3(0)=0`.

For those instances, `0` is a fixed point of the whole round function, and
single-active-nibble states become useful again.

## Structured Recovery Attack

For a nibble position `i`, define:

- `A_i(v)` = state with nibble `i = v`, all other nibbles `0`
- `B_i(u)` = `P(u << (4*i))`

On a weak instance with `S(0)=0` in every base class:

- `G(A_i(v)) = B_i(S_class(i)(v))`

So for a fixed position `i`, the unknown correspondence between the 16 states
`A_i(v)` and the 16 states `B_i(u)` is exactly the base S-box for that nibble
class.

Now query the 12-round oracle in lifted form:

- `H(x) = P(E(x)) = G^{12}(x)`

If `y = G(x)`, then:

- `H(y) = G(H(x))`

That means every correct pair `(A_i(v), B_i(u))` gives a real one-round pair:

- `(H(A_i(v)), H(B_i(u)))`

And from a one-round pair `(z, G(z))`, the S-box table entries are readable
directly:

- compute `P^{-1}(G(z))`
- each nibble output is just `S_class(nibble)(input_nibble)`

### Practical CSP

For every:

- position `i`
- input value `v`
- candidate output value `u`

we test whether `(H(A_i(v)), H(B_i(u)))` could be a valid one-round pair.

Each valid candidate produces a bundle of constraints of the form:

- `S_c(a) = b`

across all four base classes.

Then solve the small global consistency problem:

- each `S_c` must be a permutation on `0..15`
- all constraints from every accepted candidate must agree

In the weak class, this collapses quickly and uniquely recovers the four base
S-box tables.

## Live Solve Procedure

The final solver in `solve.py` does this:

1. connect
2. query `E(0)`
3. if it is not `0`, reconnect immediately
4. on a weak instance, batch-query the `A_i(v)` and `B_i(u)` sets
5. reconstruct the four base S-boxes with the CSP
6. verify on extra oracle probes
7. start challenge mode and answer all 100 blocks locally

The live run solved on attempt 18.

## Result

Live output ended with:

```text
Congratulations! Here is the flag: HCMUS-CTF{TH3_0rAcl3_5P0K3_1N_R0Und5_ANd_tH3_tHR35H0LD_an5w3R3D_1N_P3rMuTaT10N2}
```

## Artifacts

- solver: `solve.py`
- source: `rust-in-peace/chall.rs`
