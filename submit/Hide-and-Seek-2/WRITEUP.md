# Hide and Seek 2

Category: `reverse`  
Status: `solved`  
Flag: `HCMUS-CTF{d1d_y0u_solv3_both_ch4lls_;))}`

## Summary

This binary really contains two different SUBLEQ problems.

The visible one is a decoy. It appears after the binary rewrites itself, it
accepts plausible flag-like strings, and it even admits the tempting
`HCMUS-CTF{this_should_not_be_solvable!?}` family. That is not the real flag.

The real solve lives in a hidden first stage reached through overlapping ELF
`LOAD` segments. On top of that, the shipped native wrapper lies about how the
input is laid out in memory. Once that wrapper mistake is corrected, the hidden
constraints recover a unique readable flag.

## Artifacts

- Original binary: `problems/subleq/chall`
- Visible-stage emulator: `problems/subleq/solve.py`
- Hidden-stage host-faithful emulator: `problems/subleq/solve_real.py`
- Constraint notes / prototypes:
  - `problems/subleq/solve_z3.py`
  - `problems/subleq/REVERSING_NOTES.md`

## Key Observation

There are two traps here:

1. the binary rewrites itself so the next run lands in a different SUBLEQ world
2. the hidden native wrapper writes the input bytes into the wrong cells

So the correct question is not “what string makes the local binary print `ok`?”
The correct question is “what were the hidden constraints supposed to be before
the wrapper corrupted the VM workspace?”

## Early Wrong Model

Two false starts were especially convincing:

- trust the visible checker because it prints plausible success and accepts
  flag-shaped strings
- trust the native wrapper's input layout and emulate that host behavior
  directly

Both produce neat-looking local results and both are wrong. The visible stage
only yields the decoy flag family, and the wrapper scribbles over the hidden
VM's unpacked bit workspace before the real constraints run.

## Solve Path

### 1. Recover the hidden stage from the overlapping ELF segments

The ELF is static x86-64 with overlapping `PT_LOAD` mappings. Section-based
disassembly alone is misleading.

The important hidden mappings are:

```text
hidden executable page:  file 0x1cb000 -> vaddr 0x402000
hidden data/code page:   file 0x1cc000 -> vaddr 0x700000
hidden SUBLEQ memory:    file 0x1cc080 -> vaddr 0x700080
real entry point:        0x402060
```

That hidden first stage allocates a fresh VM image, copies the hidden SUBLEQ
memory, and runs it before the visible stage ever matters.

### 2. Correct the wrapper’s fake input model

The shipped wrapper writes input length to word `55405` and input bytes to
`55411..`, then checks word `55407` as if it were a success flag.

That model is wrong for the hidden VM.

The VM actually expects:

```text
55091..55130  = 40 raw input bytes
55131..55450  = 320 unpacked MSB-first input bits
```

So the wrapper is scribbling over the unpacked bit workspace instead of feeding
the raw byte source. That is why the early host-faithful hidden emulator looked
nearly input-independent.

### 3. Treat the visible second stage as a decoy

After the self-rewrite, the visible SUBLEQ checker accepts a family of strings,
including:

```text
HCMUS-CTF{this_should_not_be_solvable!?}
```

That string passes the visible logic locally and is rejected by the platform.
So the visible stage is not a reliable discriminator. It is the fake
challenge hinted at by the title and the screenshot.

### 4. Solve the intended hidden constraints

Once the input model is corrected, the hidden VM applies two useful groups of
checks:

- 40 per-byte membership constraints
- 8 cross-byte bit-plane constraints

The terminal cells are:

```text
55086 = hidden fail counter
55087 = hidden internal success flag
```

The solve method was:

1. enumerate valid byte values for each of the 40 byte positions
2. recover the obvious `HCMUS-CTF{...}` shape
3. encode the remaining 8 bit-plane checks in Z3
4. solve for the unique readable model

That produces:

```text
HCMUS-CTF{d1d_y0u_solv3_both_ch4lls_;))}
```

## Proof

Two decisive proof points:

- the visible decoy string

```text
HCMUS-CTF{this_should_not_be_solvable!?}
```

passes the local visible checker and is rejected remotely

- the hidden recovered string

```text
HCMUS-CTF{d1d_y0u_solv3_both_ch4lls_;))}
```

was accepted by the platform as `goodFlag`

## Reproduction

The checked-in scripts match the three stages we actually used:

```bash
uv run python problems/subleq/solve.py
uv run python problems/subleq/solve_real.py
uv run python problems/subleq/solve_z3.py
```

- `solve.py` reproduces the visible decoy checker
- `solve_real.py` reproduces the hidden-stage host-faithful VM behavior
- `solve_z3.py` encodes the corrected hidden constraints and prints the final
  recovered flag string

## Files

- `problems/subleq/chall`
- `problems/subleq/solve.py`
- `problems/subleq/solve_real.py`
- `problems/subleq/solve_z3.py`
- `problems/subleq/REVERSING_NOTES.md`
