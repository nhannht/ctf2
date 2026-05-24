# Hide and Seek 2

Category: reverse. Status: solved.

Flag:

```text
HCMUS-CTF{d1d_y0u_solv3_both_ch4lls_;))}
```

## TL;DR

The binary ships two different SUBLEQ worlds:

1. a hidden first stage reached through overlapping ELF `LOAD` segments, and
2. a visible second stage that appears after the binary rewrites itself.

The visible stage is a decoy. It accepts many strings, including the tempting
`HCMUS-CTF{this_should_not_be_solvable!?}`, but that string is not the real
flag.

The real solve signal is in the hidden SUBLEQ program, but the shipped host
wrapper is also misleading:

- it writes the input bytes to the wrong cells,
- it checks `55407` as if it were a success flag,
- but `55407` is actually just one unpacked input-bit cell.

Once the hidden VM is modeled with the intended raw-byte input layout, its
constraints recover a unique readable flag:

```text
HCMUS-CTF{d1d_y0u_solv3_both_ch4lls_;))}
```

That string was accepted by the platform.

## ELF Layout

The challenge is a static x86-64 ELF with overlapping `PT_LOAD` segments.
Section-based disassembly is misleading until those mappings are accounted for.

Important mappings:

```text
visible .text / main:      around 0x401000
visible SUBLEQ memory:     file 0x124040 -> vaddr 0x524040
hidden executable page:    file 0x1cb000 -> vaddr 0x402000
hidden data/code page:     file 0x1cc000 -> vaddr 0x700000
hidden SUBLEQ memory:      file 0x1cc080 -> vaddr 0x700080
real entry point:          0x402060
```

The hidden `_start` eventually calls hidden main at `0x76c558`.

## Hidden Native Wrapper

Hidden main does this:

1. reads one line from stdin,
2. allocates `0x6c4d8` bytes,
3. copies the hidden SUBLEQ memory from `0x700080`,
4. stores the input length at word `55405`,
5. stores up to 40 input bytes at word `55411`,
6. runs the hidden SUBLEQ VM with max address `55450`,
7. after halt, checks word `55407` for value `1`.

It also decodes and prints the usual strings:

```text
"> "
"no\n"
"ok\n"
"/proc/self/exe"
```

On failure it rewrites `/proc/self/exe`, truncates the file at `0x1cb000`, and
patches the ELF program-header count from `10` to `8`. That removes the hidden
segments, so the next run lands in the visible stage.

## Why The Hidden Wrapper Lies

The key mistake is trusting the wrapper's input layout.

The hidden VM does not actually consume raw bytes from `55411..55450`. Its
first large block treats:

```text
55091..55130  = 40 raw input bytes
55131..55450  = 320 unpacked MSB-first input bits
```

The repeated pattern uses the constants:

```text
55076..55083 = 1, 2, 4, 8, 16, 32, 64, 128
```

and expands each source byte into 8 bit cells. For the first byte, for example:

```text
55091 -> 55131..55138
```

So the host writes to the wrong place:

- `55411..55450` is not a raw-byte buffer,
- it is already inside the unpacked bit workspace,
- and `55407` is not a success flag at all, just another bit cell.

That is why the early "host-faithful" hidden emulator looked input-independent:
the wrapper was smashing the VM's internal workspace instead of feeding the raw
input source.

## Visible Second Stage Is A Decoy

After the self-rewrite, the visible stage runs a different SUBLEQ program at
file offset `0x124040`.

It:

- loads 40 bytes,
- expands them to 320 MSB-first bits,
- checks 16 independent 20-bit chunks,
- increments a fail counter on each bad chunk,
- sets `mem[31519] = 1` only when all 16 chunks pass.

The important point is that this checker is underconstrained. It accepts a
large family of inputs, not one exact flag. A locally valid example is:

```text
HCMUS-CTF{this_should_not_be_solvable!?}
```

It passes the visible VM and was rejected by the platform. Nearby variants such
as `...solv4ble!?` also pass locally.

This is the intended distraction hinted by the challenge text and screenshot:
the visible checker generates plausible English-looking decoys.

## Hidden VM Structure

With the intended input model, the hidden VM becomes input-dependent again.

Two cells near the end of memory matter:

```text
55086 = hidden fail counter
55087 = hidden internal success flag
```

The terminal code at `55050..55071` is simple:

- if `55086 == 0`, set `55087 = 1` and halt,
- otherwise leave `55087 = 0` and halt.

Before that final check, the hidden VM applies two groups of constraints:

1. 40 byte-wise membership tests, one for each input byte.
2. 8 bit-plane tests, one for each bit position across all 40 bytes.

The byte blocks start at:

```text
11196, 11394, 11613, 11856, 12102, 12345, 12588, 12807,
13041, 13260, 13506, 13725, 13944, 14163, 14409, 14652,
14823, 15069, 15315, 15558, 15804, 16038, 16281, 16515,
16761, 16980, 17226, 17460, 17679, 17925, 18159, 18378,
18597, 18831, 19065, 19308, 19554, 19797, 20031, 20265
```

The bit-plane blocks start at:

```text
20511, 20757, 25800, 30738, 35592, 40530, 45501, 50115
```

Each block has a "bad" leaf that increments `55086` by subtracting `-1` from
it, exactly like the visible fail-counter pattern.

## The Important Inconsistency

Even after correcting the input layout, the shipped hidden VM still increments
the fail counter once unconditionally very early at instruction `33`.

That means the binary itself is inconsistent:

- the hidden internal success condition is impossible as shipped,
- the visible checker accepts the wrong family of strings,
- and combining the hidden intended constraints with the visible constraints is
  unsatisfiable.

So the solve is not "find a string the local binary prints `ok` for". There is
no single end-to-end string satisfying all of the shipped local logic.

The right move is to recover the intended hidden constraints and solve those.

## Solving The Hidden Constraints

I modeled the hidden checker in two layers.

### 1. Per-byte domains

For each of the 40 byte blocks, enumerate all `0..255` byte values that avoid
that block's fail increment.

This already forces the flag shape hard enough to expose the format:

```text
HCMUS-CTF{...}
```

and gives tight domains for the middle bytes.

### 2. Bit-plane constraints

Then model the 8 cross-byte plane blocks in Z3 over the same 40 symbolic bytes.

Those plane checks remove the remaining ambiguity and produce one readable
model:

```text
HCMUS-CTF{d1d_y0u_solv3_both_ch4lls_;))}
```

This string does not satisfy the visible VM, which is another confirmation that
the visible stage is a decoy rather than the real discriminator.

## Why The Flag Text Makes Sense

The recovered string points directly at the challenge structure:

```text
d1d_y0u_solv3_both_ch4lls_
```

There are effectively two sub-challenges in one file:

1. the visible noisy checker that wants you to chase `this_should_not_be_*`,
2. the hidden intended checker behind the overlapping segments.

The screenshot hint and the word "unsolvable" were warning signs that the
obvious English-looking visible output was not trustworthy.

## Verification

Submitting the recovered flag to the platform returned `goodFlag`.

Final flag:

```text
HCMUS-CTF{d1d_y0u_solv3_both_ch4lls_;))}
```

## Files

- `chall` - original static ELF with overlapping `LOAD` segments.
- `solve.py` - visible SUBLEQ emulator.
- `solve_real.py` - early hidden-stage emulator that follows the native host
  wrapper layout; useful for understanding the decoy, not for the final solve.
- `solve_z3.py` - initial symbolic prototype for the hidden stage; the final
  corrected constraint model was developed from the recovered hidden block
  structure described above.
- `REVERSING_NOTES.md` - historical notes from the false starts and partial
  models.
