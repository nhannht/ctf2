# Reverse / Hide and Seek 2 Notes

This note preserves the current reversing state and strategy so we do not lose
context.

## Current Files

- `chall`: original challenge ELF.
- `solve.py`: emulator for the visible second-stage SUBLEQ program at file
  offset `0x124040`.
- `solve_real.py`: emulator for the hidden first-stage SUBLEQ program at file
  offset `0x1cc080`.
- `solve_z3.py`: initial symbolic attempt for the hidden first-stage program.
- `/tmp/ctf2_chall_stagecopy`: temporary copy of `chall` after one wrong run.
  This copy has its hidden `LOAD` segments removed by the program itself and
  enters the normal/visible stage on next execution.
- `/tmp/ctf2_hidden_402000.bin`: extracted hidden page mapped at `0x402000`.
- `/tmp/ctf2_hidden_700000.bin`: extracted hidden `0x700000` segment.

No long-running solver process was active when this note was written.

## ELF Layout

`chall` is a static, not-stripped x86-64 ELF:

```text
ELF 64-bit LSB executable, x86-64, statically linked, not stripped
```

Important observation: it has overlapping `LOAD` segments.

Normal section view:

- `.text` starts around `0x401000`.
- `main` at `0x401e00`.
- visible `run_subleq` at `0x4021d0`.
- visible SUBLEQ memory in `.rodata` at virtual `0x524040`, file offset
  `0x124040`.

Hidden loader/runtime view:

- A later `LOAD` maps file offset `0x1cb000` over virtual `0x402000`.
- The hidden `_start` at `0x402060` calls hidden main at `0x76c558`.
- Another hidden `LOAD` maps file offset `0x1cc000` to virtual `0x700000`.
- Hidden SUBLEQ memory starts at virtual `0x700080`, file offset `0x1cc080`.

The section table disassembly is misleading until the overlapping segments are
handled.

## Hidden First Stage

Hidden main at `0x76c558` does the following:

1. Reads one line from stdin.
2. Allocates `0x6c4d8` bytes.
3. Copies hidden SUBLEQ memory from `0x700080`.
4. Stores input length at byte offset `0x6b968`, word `55405`.
5. Stores up to 40 input bytes at byte offset `0x6b998`, word `55411`.
6. Runs hidden SUBLEQ VM with:
   - max address `0xd89a` (`55450`)
   - max iterations `0x3626c` (`221804`)
7. On clean halt, checks word `0x6b978 / 8 = 55407` for value `1`.

The hidden first-stage SUBLEQ control flow was input-independent in the tested
cases, but the success word did not change with input or length in tests. This
stage appears to be a decoy gate.

Important behavior: on the failure path, hidden main rewrites its own ELF file.
It copies the original file up to offset `0x1cb000`, changes the program header
count from 10 to 8, and therefore removes the two hidden `LOAD` segments. After
that rewrite, subsequent execution enters the normal visible stage.

Command used to reproduce safely on a copy:

```bash
cp chall /tmp/ctf2_chall_stagecopy
chmod +x /tmp/ctf2_chall_stagecopy
printf 'x\n' | /tmp/ctf2_chall_stagecopy
```

After this, `/tmp/ctf2_chall_stagecopy` has 8 program headers and no longer maps
the hidden segments.

## Visible Second Stage

Visible host wrapper:

- `main`: `0x401e00`
- `load_input`: `0x402190`
- `run_subleq`: `0x4021d0`
- SUBLEQ memory file offset: `0x124040`
- SUBLEQ memory size: `0x3e458` bytes
- word count: `31883`
- max address: `0x7c8a` (`31882`)
- max iterations: `0x1f22b` (`127531`)
- input length word: `31517`
- success word: `31519`
- input byte base: `31523`

Host success condition:

```text
run_subleq returns 0 AND mem[31519] == 1
```

## SUBLEQ Semantics

Each instruction is three words `(a, b, c)` at the current instruction pointer:

```text
mem[b] -= mem[a]
if mem[b] <= 0:
    ip = c
else:
    ip += 3
if ip < 0:
    clean halt / return 0
```

Address checks reject negative operands or operands above max address.

## What the Visible Stage Does

The visible SUBLEQ program first converts 40 input bytes into 320 bit cells:

- bit cells range from word `31563` to `31882`.
- mapping is MSB-first:
  - `31563` = byte 0 bit 7
  - `31564` = byte 0 bit 6
  - ...
  - `31570` = byte 0 bit 0
  - ...
  - `31882` = byte 39 bit 0

Then it checks 16 independent chunks of 20 bits each:

```text
chunk 0:  bits 0..19
chunk 1:  bits 20..39
...
chunk 15: bits 300..319
```

The fail-increment addresses for the 16 chunk checks are:

```text
12276, 13602, 14880, 16131,
17349, 18672, 19923, 21246,
22524, 23838, 25116, 26439,
27753, 28932, 30183, 31482
```

Each fail path increments word `31518`. At the end:

- if `31518 == 0`, it sets `mem[31519] = 1`;
- otherwise success remains `0`.

So all 16 chunk checks must pass.

## Important Discovery: Non-Unique Accepted Inputs

The visible stage is not checking one exact 40-byte string. It accepts a large
family of strings.

One verified accepted printable string is:

```text
T0-UV--Jo0thjv_vhoulh_not_hj_vofsdafeA?}
```

Validation:

```bash
printf '%s\n' 'T0-UV--Jo0thjv_vhoulh_not_hj_vofsdafeA?}' \
  | /tmp/ctf2_chall_stagecopy
```

Output:

```text
ok
```

However, this is probably not the intended final CTF flag. The screenshots hint
at hidden/noisy visual data, and the checker accepts many strings. The accepted
string above reads like a noisy/corrupted phrase:

```text
... vhoulh_not_hj_vofsdafe ...
```

This resembles something like:

```text
... should_not_be_...
```

but direct guesses such as `this_should_not_be_bruteforce` failed.

## Accepted Chunk Set Sizes

For each 20-bit chunk, DFS over the SUBLEQ decision tree gave these accepted
set sizes and popcounts:

```text
chunk  0: 3003 values, popcount  6
chunk  1:   10 values, popcount 11
chunk  2:  792 values, popcount  9
chunk  3:  462 values, popcount 10
chunk  4:  792 values, popcount  9
chunk  5:   28 values, popcount 13
chunk  6:  462 values, popcount 10
chunk  7:   28 values, popcount 13
chunk  8:  252 values, popcount 11
chunk  9:   56 values, popcount 13
chunk 10:  252 values, popcount 11
chunk 11:   28 values, popcount 13
chunk 12:   56 values, popcount 13
chunk 13: 1287 values, popcount  8
chunk 14:  924 values, popcount  9
chunk 15:   70 values, popcount 13
```

The sizes are binomial-looking, for example `3003 = C(14, 6)`, `1287 = C(13, 8)`,
`924 = C(12, 6)`, `792 = C(12, 5)`, `462 = C(11, 5)`, `252 = C(10, 5)`,
`70 = C(8, 4)`, `56 = C(8, 3)`, `28 = C(8, 2)`, and `10 = C(5, 2)`.

This strongly suggests each chunk validates a fixed popcount over some effective
mask or a choose-k pattern, not exact equality. That explains why many different
printable inputs print `ok`.

## Failed / Partial Approaches

1. Initial hidden-stage Z3 model (`solve_z3.py`) assumed hidden success word
   should become 1. It was UNSAT with printable bytes because hidden stage is a
   decoy and never sets the success word for tested input classes.

2. Solving visible stage with DFS over each 20-bit decision tree found accepted
   chunk sets. Combining arbitrary printable accepted chunks produced many
   accepted strings, including the verified `T0-UV--...` string above, but not a
   clean CTF flag.

3. Broad Z3 over all printable bytes and accepted chunks returned many weird
   accepted strings. It was slow in one formulation and not useful for finding
   the intended target.

4. English direct guesses around `this_should_not_be_bruteforce` did not pass.

## Useful Reconstruction Code Idea

The most useful approach so far:

1. DFS each 20-bit decision tree.
2. For each chunk, collect accepted 20-bit values.
3. Reconstruct a 40-byte input by combining 16 chunks.
4. Add scoring or constraints to find the intended hidden readable phrase.

The chunk-to-byte boundary alternates cleanly because 20 bits is 5 nibbles:

- even chunk index starts on a byte boundary;
- odd chunk index starts at a half-byte boundary.

For a chunk value `v`:

- if bit offset is 0:
  - chunk covers byte `i`, byte `i+1`, high nibble of byte `i+2`;
- if bit offset is 4:
  - chunk covers low nibble of byte `i`, byte `i+1`, byte `i+2`.

This makes a nibble-level dynamic program better than a bit-vector SMT model.

## Current Interpretation of Screenshot Hints

Both screenshots show noisy / hidden / partially obscured media. This aligns
with:

- overlapping ELF segments hiding the real first stage;
- first stage rewriting the binary to reveal the second stage;
- second stage accepting many noisy strings instead of one exact string;
- likely need to recover a clean target message from noisy accepted space.

The challenge title is `reverse/Hide and Seek 2`; "hide in plain sight" and
noise/overlay are probably intentional.

## Next Strategy

Do not stop at the first `ok` string. Continue by finding the intended readable
flag/message.

Recommended next steps:

1. Derive the exact combinatorial rule for each 20-bit chunk.
   - Each chunk seems to check fixed popcount constraints.
   - Need identify which bit positions are free/fixed/effective.
   - This may reveal a center/template string.

2. Build a better decoder over accepted chunk values.
   - Use the 16 accepted chunk sets.
   - Search printable strings with stronger language/flag-shape scoring.
   - Prefer plausible CTF flag alphabets: lowercase, digits, `_`, `{`, `}`.
   - But do not force a standard prefix until known; previous prefix tests for
     `flag{`, `ctf{`, `HTB{`, `KCSC{`, etc. gave no results.

3. Inspect the decision tree generation pattern.
   - The code around `11196..31482` is structured.
   - Trees may encode a hidden target via the ordering of branches, not just the
     accepted sets.
   - The path chosen by a clean intended phrase may correspond to a meaningful
     path index per chunk.

4. Search for hidden strings/assets in the original binary after accounting for
   the hidden segments.
   - Plain `strings` is mostly useless because messages are XOR-built on stack.
   - Still worth checking byte-level patterns in SUBLEQ memory or branch tables.

5. Validate candidates only on `/tmp/ctf2_chall_stagecopy` or a fresh copy of
   `chall`, not by modifying the original `chall`.

## Known Good Validation Command

```bash
printf '%s\n' 'T0-UV--Jo0thjv_vhoulh_not_hj_vofsdafeA?}' \
  | /tmp/ctf2_chall_stagecopy
```

Expected output:

```text
ok
```

Again: this proves the visible checker is understood enough to generate accepted
inputs, but it may not be the final intended flag.
