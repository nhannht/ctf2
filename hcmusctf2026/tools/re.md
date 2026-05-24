# RE - Toolchain

Research-backed (2026-05-23, revised after crypto teammate critique) by
cross-referencing five tool roundups (devopsschool, picoCTF Solutions,
hackmag's Ghidra deep-dive, CUJO AI Go-binary series, Practical CTF book)
plus the angr documentation, frida docs, FLARE floss, and the HCMUS
practice archive at `practice/2023-archive/` and `practice/hyrnit-source/`.
The Crypto+RE bridge section (PRNG in binary, encrypted strings, Feistel
recognition, math-heavy hard tier) is shaped by the cross-area critique from
`tools/crypto.md` author and aligned with the randcrack workflow there.

The 2023 HCMUS RE folder ships two binaries: `Go_Mal/server` (Go x86-64, not
stripped, debug_info) and `Is_This_Crypto/main` (C x86-64 PIE, not stripped).
The J4F `babyroid` writeup solved an Android APK with jadx + manual algebra.
The 2025 forecast (HCMUS-CTF-PATTERNS.md section 4b) calls out an easy
flag-check binary, a medium Android/.NET/LCG reverser, and a hard
math-heavy challenge (Finesse 2025 used PDF parsing + linear algebra).
The toolchain below targets exactly those three shapes.

## Tier 1 - must have, install before the qualifier

| Tool | Why it's the consensus pick | Install |
|------|------------------------------|---------|
| **Ghidra** (>= 11.3) | Free, NSA-backed, multi-arch decompiler. Best free decompiler output; "the common entry point for malware triage or CTF reverse engineering". Less memory than IDA, supports 50+ architectures including embedded and legacy. The flagship workhorse for stripped native binaries. | `pacman -S ghidra` or download from ghidra-sre.org. Needs JDK 21. |
| **jadx** (jadx-gui) | One-step APK -> Java decompilation. The J4F `babyroid` solve used jadx alone. Has string search, find-usage, and direct APK loading. Strict default for any `.apk` triage. | `pacman -S jadx` or download release from GitHub. |
| **radare2 / rizin** | Instant launch, no JVM, fully scriptable via `r2pipe`. Best companion to Ghidra for quick triage, embedded firmware, and writing Python solvers against the binary. Use rizin (the community fork) if your distro packages it; otherwise upstream r2. | `pacman -S radare2` or `pacman -S rizin` |
| **gdb + pwndbg or GEF** | The default Linux dynamic debugger. Required for runtime watchpoints, comparing what the binary sees vs what you guessed statically, and resolving anti-debug. pwndbg/GEF skins make heap and register state readable; pwn folks already have one installed. | `pacman -S gdb` then `git clone https://github.com/pwndbg/pwndbg` or GEF, source from `~/.gdbinit` |

Minimum viable RE kit during the qualifier:
**Ghidra + jadx + radare2 + gdb (pwndbg).**

That kit covers: native ELF/PE/Mach-O (Ghidra), Android APK (jadx), quick
triage and scripting (r2), and runtime verification (gdb). Nothing else is
strictly required for Triển Vọng easy + medium tier.

## Tier 2 - load on demand when the archetype matches

| Tool | Trigger archetype | Notes |
|------|-------------------|-------|
| **IDA Free 9.x** | When Ghidra's decompiler garbles a specific function and you want a second opinion. | IDA Free now ships Hex-Rays decompile for x86/x64/ARM/ARM64 (since 9.0). Slightly more accurate on complex control flow (~92% vs Ghidra's ~88% in roundup tests). Limited vs IDA Pro but free. |
| **Binary Ninja Cloud** | Browser-only sanity check on small binaries (< 5 MB). | https://cloud.binary.ninja/ - free, no install. Useful as a third decompiler view on `Is_This_Crypto/main`-sized binaries when both Ghidra and IDA Free disagree. |
| **Cutter** | Want a GUI on top of radare2/rizin instead of CLI. | Rizin-based fork is the maintained one. Same engine as r2, friendlier for navigation. Skip if you're already fluent in r2 prompt. |
| **dnSpy / ILSpy / dotPeek** | `.NET` binary (`.exe`/`.dll`, PE32 + CLR header). | dnSpy decompiles AND debugs and edits IL inline; ILSpy is read-only but maintained. Both expose String Heap / UserString Heap (CTF flag candidates) and `{}` icons mark methods with code. |
| **frida** | Android dynamic hook (root-detection bypass, runtime decryption, hooking opaque native JNI). | `pip install frida-tools`. Push `frida-server` to the device (or emulator), then `frida -U -n com.example.app -l hook.js`. JS hooks like `RootBeer.isRooted.overload().implementation = function() { return false; }`. |
| **apktool** | Need decoded resources, smali, AndroidManifest XML (jadx hides some res/ assets, Chaquopy Python payloads, multi-DEX edge cases). | Run alongside jadx, not as a replacement. `apktool d app.apk` -> inspect `assets/`, `res/`, `AndroidManifest.xml`. |
| **dex2jar** + a Java decompiler | Legacy fallback if jadx mis-handles a DEX. | `d2j-dex2jar app.apk` -> open the JAR in JD-GUI or CFR. Rare in 2025+ but still in the cheat sheets. |
| **angr** | Pure flag-check binary where every byte runs through a fixed transformation, no I/O magic, no anti-debug. | `pip install angr`. Set entry state, mark target/avoid addresses, solve. Real-world hit rate is lower than memes claim - works best on classroom-style "if (transform(input) == const) print flag" binaries. |
| **qemu-user** + cross-debuggers | Non-x86 architectures (ARM, MIPS, RISC-V) on an x86 box. | `pacman -S qemu-user qemu-user-static` then `qemu-arm -L /usr/arm-linux-gnueabi ./chall` or `qemu-aarch64 -g 1234 ./chall` to attach gdb-multiarch. |
| **GolangAnalyzerExtension** (Ghidra plugin) | Stripped Go binary, especially if the 2023 Go_Mal pattern repeats. | https://github.com/mooncat-greenpy/Ghidra_GolangAnalyzerExtension - recovers Go function names, file paths, and type info for go1.6 - go1.26. Drop into Ghidra `Extensions/` dir. Also `redress` and `go-re.tk` as standalone CLI alternates. |
| **strings + binwalk + file + xxd** | First-touch triage on EVERY binary. Cost-free. Always run. | Already on the host. `file chall && strings -n 8 chall \| grep -i 'flag\|hcmus\|key' && binwalk -e chall`. Catches sanity tier and obvious leaks in under 20 seconds. |
| **FLARE floss** | Encrypted / XOR-obfuscated strings hidden from plain `strings`. Uses emulation + angr to recover stack-built and decrypted strings. | `pip install flare-floss`. Flaky on stripped Go and heavily-templated C++ - keep the manual fallback (Ghidra script + gdb post-init `.data` dump) for when it whiffs. See the "Encrypted strings" archetype row. |
| **Z3 / claripy** | Algebraic inversion of small-state PRNGs (xorshift, xoroshiro), and constraint solving when the transform is bit-level but reversible. | `pip install z3-solver`. Faster than angr when you can encode the transform symbolically by hand. |
| **numpy + objcopy** | Math-heavy hard tier: extract `.rodata` constants, then closed-form matrix exponentiation in Python (`A^n = P D^n P^-1` via eigendecomposition) without dragging in Sage. | `pacman -S python-numpy binutils`. `objcopy --dump-section .rodata=rodata.bin ./chall` -> `numpy.fromfile('rodata.bin', dtype=...)`. |
| **ChatGPT / Gemini / Claude** (rules-allowed) | Archetype recognition on unfamiliar decompiler output, especially math-heavy hard tier. | Rules-allowed by HCMUS-CTF 2026. Paste pseudo-C + ask "what algorithm is this". Faster than searching Wikipedia for an unfamiliar transform. |

## Mapping back to HCMUS-CTF archetypes

Cross-referenced with `HCMUS-CTF-PATTERNS.md` section 4b RE block:

| Archetype | Example | Primary tool | Backup / next step |
|-----------|---------|--------------|--------------------|
| Easy native flag-check (C/C++ x86-64) | `Is_This_Crypto/main` (2023), Hide and Seek (2025) | Ghidra decompile, find `main`, invert the transform | r2 + python solver; angr if the transform is mechanical |
| Easy native flag-check (Go) | `Go_Mal/server` (2023) | Ghidra + GolangAnalyzerExtension; recover symbols then read decompile | `redress` or `go-re.tk` if symbols are stripped |
| Medium Android APK | `babyroid` (J4F) | jadx-gui on the APK, grep for `checkFlag`/`flag`/`HCMUS-CTF{`, read decompiled Java | apktool for resources; frida hook if the check uses JNI or runtime decryption |
| Medium .NET binary | (not in HCMUS history, but on the standard archetype list) | dnSpy decompile + inline debug; ILSpy as second opinion | de4dot if obfuscated (ConfuserEx etc.) |
| Medium LCG reversal (glibc `rand()` / MSVC `rand()` / textbook LCG in source) | Hide and Seek (2025) | Ghidra decompile, dump the seed at the `srand` call via gdb breakpoint, replay the stream in Python (`x = x*1103515245 + 12345 & 0x7fffffff` for glibc-style; `ctypes.CDLL("libc.so.6").rand` for byte-exact replay) | re-implement the exact LCG constants the decompile shows |
| Medium MT19937 reversal in a C/C++ binary (`std::mt19937` or `mt19937_64`) | Crypto+RE cross-cat archetype (see `tools/crypto.md` randcrack row) | Ghidra confirms MT19937 (recognize the 624 x 32-bit state and the temper/untemper steps); set a gdb breakpoint on the rand call, dump 624 consecutive outputs to a file, feed to `randcrack` for state recovery | manual untemper if randcrack version mismatch |
| Medium xorshift / xorshift64* / xoroshiro / xoshiro256++ | Go runtime PRNG, Rust stdlib PRNG, modern CTF binaries | Z3 / claripy to invert algebraically once you read the shift+xor constants from the decompile | hand-coded 5-line inverse if the shifts are simple (xorshift64 inverse is closed-form) |
| Medium XOR / RC4 reversal | recurring | Ghidra decompile, read the key schedule, write the inverse XOR or RC4 loop in Python | xortool if it's repeating-XOR with unknown key length |
| Medium custom block cipher in C (Is_This_Crypto archetype) | `Is_This_Crypto/main` (2023) | Read the round function. Two XOR-linked halves alternating across N rounds = Feistel - invert by running rounds in reverse order with the same key schedule. Lai-Massey if the two halves are combined via subtraction modulo p instead of XOR. | If the round function is invertible standalone (SPN), invert each round inline |
| Encrypted strings (XOR-obfuscated rodata, runtime-decrypted format strings) | recurring CTF anti-strings trick | `floss --no-decoded-strings ./chall` first; if it whiffs, set a gdb breakpoint just after the binary's init / `_init_array` decryptor, `dump memory data.bin <.data start> <.data end>`, run `strings` on the dump | Ghidra script that walks xrefs from `memcpy(rodata + N, ...)` to find the decrypt loop |
| Hard math-heavy (linear algebra, matrix exp, polynomial systems) | Finesse (2025) | RE-side solve by default (one-solver constraint): `objcopy --dump-section .rodata=rodata.bin ./chall`, parse constants with `numpy.fromfile`, then closed-form matrix exponentiation `A^n = P D^n P^-1` via `numpy.linalg.eig`. Use Sage when the operation is over an integer ring or finite field that numpy cannot model. | Hand off to crypto/Sang only if it is provably a pure-math wall and time is critical - per STRATEGY.md "Solve-order priority" hard tier is bonus anyway |
| Anti-debug / packed | rare in HCMUS but show up in mock CTFs | radare2 + `file`/`binwalk` to detect packer (UPX is most common); `upx -d`; then Ghidra | If custom packer: dynamic dump via gdb + `dump memory`, or frida on the unpacker stub |
| Cross-arch (ARM/MIPS/RISC-V) | not seen in HCMUS 2023-2025, low probability | qemu-user + Ghidra (multi-arch out of the box) | gdb-multiarch attached to qemu-user `-g <port>` for runtime |

## Workflow

The 45-minute time-box from STRATEGY.md drives this workflow. Triage in
minutes, static analysis in tens of minutes, dynamic only if static is
not enough. Bail at 45 minutes and return in the mop-up window.

### Step 1 - Triage (target: 2-5 minutes)

Always run, in this exact order, before opening any decompiler.

```
file chall                       # what architecture and format?
strings -n 8 chall | less        # any plaintext leaks (HCMUS-CTF{, base64, urls)?
strings -n 8 -e l chall          # UTF-16 strings (.NET, Windows binaries)
xxd chall | head                 # magic bytes - is it ELF, PE, APK, ZIP, .NET PE?
binwalk chall                    # embedded archives, packed payloads
sha256sum chall                  # for comparing to writeups / pasting into AI
```

Decision tree after triage:

```
ELF x86-64 not stripped       -> Ghidra, look at main / DAT_ table
ELF x86-64 Go binary          -> Ghidra + GolangAnalyzerExtension
ELF stripped                  -> radare2 `aaa` then `afl`, then Ghidra
PE32+ with CLR header (.NET)  -> dnSpy
Android .apk                  -> jadx-gui, then apktool if assets/ matters
ARM / MIPS / RISC-V           -> qemu-user + Ghidra
UPX magic ("UPX!" in strings) -> `upx -d chall`, retry triage on the dump
ZIP / disk image              -> NOT REVERSE - hand to forensics teammate
```

Decide skip vs commit at this point. If the binary's archetype does not match
anything in the table above and nothing leaks from strings, mark it and move
on. Triển Vọng is won by clearing easy and medium, not by burning 4 hours on
a custom packer.

### Step 2 - Static analysis (target: 15-25 minutes)

For native binaries (Ghidra path):

1. Open in Ghidra, run auto-analysis with defaults plus GolangAnalyzerExtension
   if Go was detected.
2. Locate `main`, `_start`, or whatever the entry/`@main.main` symbol becomes.
3. Read the decompile. Rename variables as you understand them - the goal is
   to make the function readable enough to invert in your head or in Python.
4. Identify the flag-check shape: equality comparison against a constant
   string? loop over input applying a transform then `memcmp`? lookup table?
5. Extract every constant: key bytes, S-boxes, IV, magic numbers. Copy them
   into a `solve.py` next to the binary.
6. Write the inverse transform in Python. Run it. Validate against the binary
   with `gdb` if the answer doesn't print `HCMUS-CTF{...}` immediately.

For Android APK (jadx path):

1. `jadx-gui app.apk`. Wait for the decompile.
2. Open `AndroidManifest.xml` (top of the tree). Find the launcher activity
   name (`android:name=".MainActivity"` or similar). Note any exported
   components.
3. Jump to that activity. Look for `checkFlag`, `validate`, `onClick`,
   `verify` - jadx has Ctrl+F string search and Ctrl+Shift+F symbol search.
4. Read the check logic. The J4F `babyroid` writeup is the model: a chain of
   length, prefix, charAt, regex constraints that each pin one position of
   the flag. Solve as algebra.
5. If the check is in native code (`System.loadLibrary` + `native` Java
   method), pull the matching `.so` from `lib/<arch>/` and switch to the
   Ghidra path on that `.so`.
6. If a runtime call obscures the constant (Chaquopy Python, asset
   decryption, dynamic class loading), switch to frida.

For .NET (dnSpy path):

1. Open the `.exe` or `.dll` in dnSpy. The decompile is C# directly.
2. Skim the namespace tree. Methods marked with `{}` contain code; classes
   without `{}` are pure data/enums.
3. Check the Metadata > String Heap and UserString Heap for hardcoded flags
   and keys.
4. Read the validation method, write the inverter or set a breakpoint and run.

#### Crypto+RE bridge (PRNG in binary, encrypted strings, custom cipher)

When the binary leans on randomness or hidden constants - common across HCMUS
editions and the place RE and Crypto overlap - branch on what you see:

1. **PRNG recognition cheat sheet**
   - 624 x 32-bit state array + temper steps with `0x9d2c5680` / `0xefc60000`
     -> `std::mt19937`. Dump 624 outputs via gdb breakpoint on the rand call,
     feed to `randcrack` (see `tools/crypto.md`).
   - `state = state * 1103515245 + 12345 & 0x7fffffff` -> glibc-style LCG.
     `ctypes.CDLL('libc.so.6').rand` for byte-exact replay once you have the seed.
   - `state = state * 214013 + 2531011 & 0x7fffffff` -> MSVC `rand()`.
   - State of 64-128 bits with `x ^= x << a; x ^= x >> b; x ^= x << c` -> xorshift
     family. Z3 invert or hand-code the closed-form inverse for xorshift64.
   - `xoshiro256++` / `xoroshiro128**` -> Go runtime / Rust stdlib PRNG. Z3.
2. **Seed source matters**: if `srand(time(0))` or `srand(getpid())`, brute the
   seed range over a small window (`time(0) +/- 30 seconds`) instead of cracking
   the algorithm. Always check the seed call before the RNG itself.
3. **Encrypted strings**: when `strings` shows garbage but the binary clearly
   uses long messages, run `floss ./chall` first. If floss times out or returns
   garbage (stripped Go, templated C++), set a gdb breakpoint at the entry of
   `main` (or after `_init_array`), then `dump memory data.bin <.data start>
   <.data end>` and re-run `strings` on the dump.
4. **Custom block cipher**: if the decompile shows N rounds with two XOR-linked
   halves alternating, it is a Feistel - the inverse runs the same rounds in
   reverse order with the same key schedule, no inverse round-function needed.
   If the halves are combined modulo a prime instead of XOR, it is Lai-Massey;
   same trick. Implement in `pycryptodome` style.

### Step 3 - Dynamic analysis (only if static was not enough)

Trigger conditions: the check uses runtime-decrypted constants; the
transform is too obfuscated to read; you want to confirm a guess fast.

Pick the matching path. Don't run both.

```
Native Linux ELF:
  gdb ./chall
  pwndbg> break *flag_check_addr      (or `break main`)
  pwndbg> run
  pwndbg> x/16gx $rdi                  (inspect args, regs)
  pwndbg> ni / si                      (step)
  pwndbg> dump memory out.bin $a $b    (dump decrypted regions)

Native Windows PE on Linux host:
  Run via wine + gdb-mingw or x64dbg under wine. For CTF, often easier to
  just use Ghidra's emulator or angr.

Android APK:
  Push frida-server, start app, `frida -U -n <pkg> -l hook.js`. Sample hook:
    Java.perform(function() {
      var FV = Java.use('com.example.FlagValidator');
      FV.checkFlag.implementation = function(ctx, s) {
        console.log('checkFlag called with', s);
        var r = this.checkFlag(ctx, s);
        console.log(' -> returned', r);
        return r;
      };
    });
  Or hook RootBeer / SafetyNet / SSL pinning to bypass guards.

Symbolic (angr) - last resort for native flag-check binaries:
  import angr
  p = angr.Project('./chall', auto_load_libs=False)
  st = p.factory.entry_state(args=['./chall', angr.PointerWrapper(b'A'*32)])
  sm = p.factory.simulation_manager(st)
  sm.explore(find=ADDR_WIN, avoid=ADDR_LOSE)
  print(sm.found[0].posix.dumps(0))    # if input via stdin
  print(sm.found[0].solver.eval(sym_input, cast_to=bytes))

Cross-arch:
  qemu-aarch64 -g 1234 ./chall &
  gdb-multiarch -ex 'target remote :1234' ./chall
```

### Step 4 - Validate

Always validate the candidate flag before submitting:

1. Run the binary with the candidate input. Confirm it prints the flag or the
   "correct!" branch.
2. Confirm the format is `HCMUS-CTF{...}` (per rCTF platform fact). If the
   transform produced something else, you reversed half of it.
3. If submission fails: re-check casing, leading/trailing characters, and
   whether the binary expected stdin vs argv.
4. Save the working `solve.py` into the writeup folder so the workflow is
   replayable per STRATEGY.md "Treat the instance as ephemeral".

## Pre-qualifier rehearsal targets

Run each of these inside the `ctf` distrobox container before 23/05. They
mirror the three RE archetypes the forecast predicts.

| Practice target | Expected archetype | Tools to rehearse |
|-----------------|--------------------|--------------------|
| `practice/2023-archive/ctfs/HCMUS/2023/Quals/rev/Is_This_Crypto/main` | Native flag-check + custom crypto | Ghidra decompile + Python solver |
| `practice/2023-archive/ctfs/HCMUS/2023/Quals/rev/Go_Mal/server` | Go binary (not stripped, debug info present) | Ghidra + GolangAnalyzerExtension symbol recovery |
| `practice/hyrnit-source/RE/Go Mal!/` | Same Go binary, second copy | Confirm GolangAnalyzerExtension installed and active |
| `writeups/babyroid/src/babydroid.apk` | Android APK with algebraic flag check | jadx-gui static decompile; the J4F writeup is the reference |

If all four solve cleanly inside 45 minutes each, the Tier 1 kit is ready.
If Ghidra fails on Go_Mal because GolangAnalyzerExtension isn't installed -
fix that before 23/05. If jadx can't load babydroid.apk - reinstall before
23/05.

## Constraints from the wider strategy

- Never run an untrusted challenge binary on the host. Use the `ctf`
  distrobox container per `CLAUDE.md` "Toolkit setup".
- 45-minute time-box per challenge (STRATEGY.md "Discipline rules").
  RE rabbit holes are the classic violator - one obscure transform can eat
  4 hours. Bail at 45.
- The hard tier (Finesse-style math-heavy) is bonus. Do not commit time
  there until easy + medium across all categories are mopped up
  (STRATEGY.md "Solve-order priority" 1-3).
- The 1-hour instancer TTL does not normally apply to RE (challenge files
  are usually static downloads, not live containers) - but if a challenge
  ships an instanced RE service (rare), the exploit script must be
  replayable in one shot per STRATEGY.md "Challenge instance lifecycle".

## Sources

- [Top 10 Reverse Engineering Tools in 2026 - devopsschool](https://www.devopsschool.com/blog/top-10-reverse-engineering-tools-in-2025-features-pros-cons-comparison/)
- [Ghidra vs IDA Pro - hackmag deep dive](https://hackmag.com/security/nsa-ghidra-2)
- [Ghidra vs IDA Pro in 2026 - secybers](https://secybers.com/blog-details/ghidra-vs-ida-pro-in-2026-a-comprehensive-reverse-engineering-tool-comparison)
- [How to Use Ghidra for Reverse Engineering CTF Challenges - picoCTF Solutions](https://picoctfsolutions.com/posts/ghidra-reverse-engineering)
- [radare2 vs Ghidra (2026) - appsecsanta](https://appsecsanta.com/mobile-security-tools/radare2-vs-ghidra)
- [Reverse Engineering Go Binaries with Ghidra - CUJO AI](https://cujo.com/blog/reverse-engineering-go-binaries-with-ghidra/)
- [Reverse Engineering Go Binaries with Ghidra Part 2 - CUJO AI](https://cujo.com/blog/reverse-engineering-go-binaries-with-ghidra-part-2-type-extraction-windows-pe-files-and-golang-versions/)
- [Ghidra_GolangAnalyzerExtension - mooncat-greenpy](https://github.com/mooncat-greenpy/Ghidra_GolangAnalyzerExtension)
- [Reversing Golang Binaries with Ghidra - FIRST 2022 paper](https://www.first.org/resources/papers/conf2022/Palotay_53.pdf)
- [From APK to Source - Complete Android Reverse Engineering Workflow](https://www.marginaldeer.com/blog/apk-reverse-engineering-workflow/)
- [Android | CTF Support reverse-engineering guide](https://ctf.support/reverse-engineering/android/)
- [Reverse engineering Android apps (CTF challenge) - Prathunan](https://medium.com/@prathunan777/reverse-engineering-android-apps-ctf-challenge-baa3a9cbe7d5)
- [Android App Reverse Engineering Part 4 - Dynamic Analysis with Frida - Huli](https://blog.huli.tw/2023/04/27/en/android-apk-decompile-intro-4/)
- [Frida Android docs](https://frida.re/docs/examples/android/)
- [Frida Method Hooking for Android App Analysis - marginaldeer](https://www.marginaldeer.com/blog/frida-method-hooking-android/)
- [angr CTF Challenge Examples - official docs](https://docs.angr.io/en/latest/appendix/more-examples.html)
- [angr for CTF - Automating Reversing a Binary - Shivsarthak](https://shivsarthak.medium.com/angr-for-ctf-automating-reversing-a-binary-d5ca574d1d0b)
- [angr CTF Challenge Solvers - DeepWiki](https://deepwiki.com/angr/angr-examples/4-ctf-challenge-solvers)
- [Reversing C# - .NET / Unity - Practical CTF (Jorian Woltjer)](https://book.jorianwoltjer.com/reverse-engineering/reversing-c-.net-unity)
- [dnSpy on GitHub](https://github.com/dnSpy/dnSpy)
- [Reversing .NET Applications - CCCamp19 CTF CampRE](https://bananamafia.dev/post/dotnet-re-cccamp19/)
- [FLARE floss - automated string deobfuscation](https://github.com/mandiant/flare-floss)
- [randcrack - Python MT19937 state recovery (cross-link from tools/crypto.md)](https://github.com/tna0y/Python-random-module-cracker)
- [Z3 theorem prover - Python bindings](https://github.com/Z3Prover/z3)
- [glibc rand() / drand48() implementation notes](https://www.mscs.dal.ca/~selinger/random/)
- [Cracking xoshiro / xorshift PRNGs with Z3 (Robert Heaton)](https://robertheaton.com/2018/12/02/programming-projects-for-advanced-beginners-ascii-art/)
