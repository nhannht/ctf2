# xv6

Category: `pwn`  
Status: `solved`  
Flag: `HCMUS-CTF{36_hours_is_not_enough_for_a_*real*_linux_kernel_CVE}`

## Summary

This challenge looked like a kernel-local-privilege-escalation problem inside
xv6. For this deployment, that was the decoy. The real break was outside the
guest kernel: the service exposed a QEMU monitor escape on the same stdio
channel used for challenge interaction.

Once we switched from the guest console into the QEMU monitor, we could inspect
guest physical memory directly. The service mapped `flag.txt` at a fixed
physical address, so the solve reduced to dumping that page and decoding ASCII.

## Artifacts

- Remote service: `nc xv6.blackpinker.com 1337`
- Challenge wrapper: `problems/xv6/public/chall.sh`
- Solver: `problems/xv6/solve_monitor.py`
- Player bundle: `problems/xv6/xv6-player.zip`

## Key Observation

The critical line was not in the xv6 kernel patch. It was in the QEMU launch
configuration.

The wrapper boots QEMU with:

```bash
-nographic
-device loader,file=flag.txt,addr=0x87fff000,force-raw=on
```

`-nographic` leaves the serial console and monitor multiplexed on stdio.
Sending `Ctrl-A c` switches from the guest console into QEMU monitor mode, and
the monitor can read physical memory with `xp`.

## Early Wrong Model

The obvious branch was to stay inside the guest and hunt a real xv6
kernel-local-privilege-escalation bug. That was the wrong layer for this
deployment. The wrapper already exposed something much weaker than a kernel bug:
QEMU monitor access on stdio plus a fixed physical mapping for `flag.txt`.

Once that was clear, guest exploitation stopped being necessary. We only needed
to keep the VM alive long enough to escape to monitor mode and dump memory.

## Solve Path

### 1. Read the challenge wrapper, not just the kernel diff

`chall.sh` uploads a player-controlled `_init`, rebuilds the filesystem image,
and boots QEMU for a short time window. More importantly, it loads `flag.txt`
at `0x87fff000`.

That already suggests a cleaner path than chasing a deep xv6 kernel bug.

### 2. Keep the guest alive briefly

Any valid `_init` that stays alive long enough is good enough. I used a tiny
looping init payload and waited for a visible boot marker before escaping to
monitor mode.

### 3. Switch into QEMU monitor mode

The stdio multiplexer is QEMU’s default `Ctrl-A` prefix. Sending `Ctrl-A c`
switches to monitor mode, where this command works immediately:

```text
xp /128bx 0x87fff000
```

That dumps the page containing `flag.txt`.

### 4. Parse ASCII out of the dump

The solver only needs to extract the `HCMUS-CTF{...}` pattern from the returned
bytes. The shipped extractor does exactly that:

```python
io.send(b"\x01c")
io.sendline(f"xp /{args.dump_len}bx {hex(args.addr)}".encode())
...
flag = extract_flag(data)
```

## Proof

The decisive proof artifact is the combination of:

- challenge-side mapping:

```bash
-device loader,file=flag.txt,addr=0x87fff000,force-raw=on
```

- monitor-side read:

```text
xp /128bx 0x87fff000
```

- solver output:

```text
FLAG: HCMUS-CTF{36_hours_is_not_enough_for_a_*real*_linux_kernel_CVE}
```

## Reproduction

Build a minimal looping init:

```bash
cd problems/xv6/upstream-xv6
make TOOLPREFIX=riscv64-elf- user/_loop
```

Run the extractor:

```bash
uv run python problems/xv6/solve_monitor.py \
  --host xv6.blackpinker.com \
  --port 1337 \
  --payload problems/xv6/upstream-xv6/user/_loop \
  --addr 0x87fff000 \
  --dump-len 128
```

The exact monitor command the solver prints to QEMU is:

```text
xp /128bx 0x87fff000
```

## Files

- `problems/xv6/solve_monitor.py`
- `problems/xv6/public/chall.sh`
- `problems/xv6/public/kernel.diff`
