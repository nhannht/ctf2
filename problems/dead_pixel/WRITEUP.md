# dead pixel

Category: pwn

Flag:

```text
HCMUS-CTF{w3lc0m3_t0_th3_r34l_w0rld_n30}
```

## Summary

The challenge is not a normal stack-smash binary.  The intended bug is tied to
the "dead pixel" theme: the program installs a `SIGSEGV` handler and rewrites
the saved `RIP` after a crash.

The exploit uses a signed index bug in `corrupt_data()` to write outside
`corruption_table`.  By combining that with the crash handler, we can make an
intentional segfault dispatch to `escape_reality()`, which runs `/bin/sh`.

## Reversing Notes

Ghidra decompilation shows:

```c
void glitch_out(void) {
    cout << ">> GLITCH: Reality rejected your input." << endl;
    *(long *)0x4445414450495845 = 0;
}
```

That write always segfaults.  The binary installs this handler:

```c
void handle_pixel_death(int sig, siginfo_t *info, void *ctx) {
    if (1 < signal_count) {
        exit(0xff);
    }
    signal_count++;
    *(long *)((long)ctx + 0xa8) = *(long *)(pixel_handlers + render_stage * 8);
}
```

On x86-64 Linux, `ctx + 0xa8` is the saved `RIP` in `ucontext_t`.  So a crash
becomes:

```text
RIP = pixel_handlers[render_stage]
```

The useful target is:

```c
void escape_reality(void) {
    system("/bin/sh");
    exit(0);
}
```

## Bug

`corrupt_data()` reads a signed integer `local_24` and only checks the upper
bound:

```c
if ((local_20 < local_24) || (*(long *)(packet_log + (long)local_24 * 8) == 0)) {
    glitch_out();
}
```

There is no lower-bound check, so negative indexes are allowed if
`packet_log[index]` points to a nonzero value.

If validation passes, the same signed index is used to mutate
`corruption_table[index]`:

```c
*(ulong *)(corruption_table + (long)local_24 * 8) += rand_byte;
```

Because `packet_log` and `corruption_table` are adjacent globals, this gives
controlled relative writes to other globals.

Important addresses:

```text
packet_log       = 0x52c0
corruption_table = 0x5340
packet_index     = 0x53c0
pixel_handlers   = 0x53e0
render_stage     = 0x5008
memory_cells     = 0x5010
```

Useful indexes:

```text
index -103: validates through GOT, writes render_stage
index -102: validates through GOT, writes memory_cells
index 16:   reads corruption_table[0], writes packet_index
index 1:    writes corruption_table[1]
```

The key alias is:

```text
pixel_handlers[-19] == corruption_table[1]
```

So the goal is:

```text
corruption_table[1] = escape_reality
render_stage = -19
memory_cells < -200
trigger glitch_out()
```

When `run_game()` sees `memory_cells < -200`, it calls `glitch_out()` before
showing the next menu.  Since `render_stage` is already `-19`, the SIGSEGV
handler loads `RIP` from `corruption_table[1]`.

## Randomness

The binary seeds `rand()` from only two bytes:

```c
read(open("/dev/urandom", 0), &seed, 2);
srand(seed);
```

Only 65536 seeds are possible.  The solver observes success/failure from
`overflow_buffer()` until the 16 packet slots are full, then brute-forces the
16-bit seed and predicts all future `rand()` values.

`overflow_buffer()` stores one of several static strings into `packet_log` when:

```c
rand() % 10 == 0
```

That leaks enough of the random stream to recover the seed.

## Exploit Steps

1. Use `OVERFLOW BUFFER` until all 16 packet slots are populated.
2. Recover the 16-bit `srand()` seed from the observed ACK/no-response pattern.
3. Use `CORRUPT DATA` index `0` once so `corruption_table[0]` becomes nonzero.
4. Use index `16` to increment `packet_index` from 16 to 17.  This makes future
   `overflow_buffer()` calls write into `packet_log[16]`, which is the same
   address as `corruption_table[0]`.
5. Use `overflow_buffer()` again until an ACK writes a PIE text pointer into
   `corruption_table[1]`.
6. Predict future `rand()` byte deltas and use index `1` to adjust that pointer
   exactly to `escape_reality`.
7. Plan a bounded sequence using indexes `-102` and a harmless negative index to
   keep `memory_cells > -200` until the final operation.
8. On the final operation, use index `-103` when the predicted delta is `-20`.
   This sets `render_stage` from `1` to `-19` and drops `memory_cells` below
   `-200`.
9. `run_game()` calls `glitch_out()`, the signal handler redirects RIP through
   `pixel_handlers[-19]`, and `escape_reality()` spawns a shell.

The solver sends `cat flag` to the shell and extracts the flag.

## Verification

Local fake flag:

```bash
uv run python problems/dead_pixel/solve.py
```

Remote:

```bash
uv run python problems/dead_pixel/solve.py --host chall.blackpinker.com --port 20850
```

Successful remote output:

```text
HCMUS-CTF{w3lc0m3_t0_th3_r34l_w0rld_n30}
```

