# HCMUS-CTF - Cross-Edition Pattern Analysis

Compiled 2026-05-20 from CTFtime, the sajjadium/ctf-archives, and public writeups
(PSDat123, CyberCh1ck, UniverSea, h0a9d13p). Purpose: extract what repeats so the
2026 qualifier holds no surprises.

## 1. Reality check on "100% winrate"

No CTF can be guaranteed - there are live opponents and unseen challenges. But
HCMUS-CTF is one of the most pattern-stable CTFs in Vietnam: same categories,
same tools, same attack archetypes every edition. Pre-mastering the recurring
pattern removes most avoidable risk. In Bảng Triển Vọng (rookie bracket, no UIT
or KMA) that preparation is enough to place top 10.

## 1b. Platform facts confirmed 2026-05-21

Engine is **rCTF** (redpwn's open-source CTF platform) with lactf template
customizations. This shapes strategy as follows:

| Fact | Strategy impact |
|------|-----------------|
| Flag format `HCMUS-CTF{TEXT_HERE}` (unless challenge overrides) | Treat any other format as wrong-flag, not wrong-extract. Save 5 minutes of "did I get the right region?" doubt. |
| Dynamic scoring (more solves = fewer points), no first-blood bonus | Rare-solve challenges are worth proportionally more. If a low-traffic medium is in your wheelhouse, prioritize it over a high-traffic easy of nominal-equal value. |
| Per-challenge instances via `instancer.blackpinker.com`, 1-hour TTL | Build replayable exploit scripts. Do not rely on long-lived container state. |
| AI tools (ChatGPT, Gemini, etc.) explicitly allowed | Use them. Especially for unfamiliar crypto / RE archetype recognition. |
| Shared team account, no per-user attribution | Self-track who solved what in Discord for post-event learning. |

## 2. Edition data

| Edition | Teams | Duration | Categories | ~Challenges |
|---------|-------|----------|------------|-------------|
| 2023 Qualifier | 92 | 24 h | crypto, pwn, rev, web, forensics, misc | 19 |
| 2025 Qualifier | many | ~48 h | AI, crypto, forensics, misc, pwn, rev, web | 21+ |
| 2026 (ours) | TBD | 2 days (23-24/05) | Pwn, RE, Web, Forensics, Crypto, AI, Misc | expect ~24-30 |

Champions: 2023 "The Council of Sheep" (3847 pts); 2025 "FunSociety" (UIT, Bảng
Tài Năng - not our bracket).

## 3. The recurring pattern (memorize this)

| Category | The shape that keeps coming back |
|----------|----------------------------------|
| Crypto | One easy textbook bug (substitution cipher solved via boxentriq.com, fixed-IV CBC, bootleg AES, **Python `random` state recovery via `randcrack` when authors seed weakly**) + one hard lattice/Groebner. 2023: Substitution, bootleg aes, CRY1. J4F edition: OH SEED (RandCrack). 2025: BPCasino (fixed IV), Compressed (LLL), Flagtrix (Groebner). |
| Forensics | Always present: a pcap to decrypt (TLS keylog), a stego file (WAV LSB), a disk/carving task. Tool-driven, low skill ceiling. |
| Web | Easy: one isolated bug. Hard: a chain - SSRF -> Gopher -> MongoDB, or path-traversal -> ~/.curlrc -> RCE. The chains are the wall. |
| RE | One medium (LCG/XOR reversal, .NET, Android) + one hard (math-heavy: linear algebra, matrix exponentiation). |
| Pwn | One medium (buffer overflow + leak) + one hard (UAF/heap, fastbin, ROP). |
| AI | New since 2025, now permanent: prompt injection (easy) + adversarial images / model evasion (hard). |
| Misc/OSINT | Always 1-2 easy points: YouTube metadata, encoding puzzles, OSINT. |
| Sanity | One free flag. Always. |

## 4. Known past challenges

### 2023 Qualifier (19 challenges)

Go Mal! (RE), Safe Proxy (web), real key (RE), Is This Crypto? (crypto+RE),
Sneak Peek, grind (misc), pickle trouble (misc/python), CRY1 (crypto),
string chan (pwn), coin mining (misc), M Side, Kiwi, Cute Quote (web),
Social Engineering (AI/social), falsehood (misc), python is safe (misc),
japanese, bootleg aes (crypto), Sanity check.
Archive: github.com/sajjadium/ctf-archives -> ctfs/HCMUS/2023/Quals
(folders: crypto, pwn, rev, web).

### 2025 Qualifier (21+ challenges)

| Category | Challenge | Difficulty | Technique |
|----------|-----------|-----------|-----------|
| AI | Campus Tour | Easy | prompt injection, chatbot guard bypass |
| AI | gsql1 | Medium | Gemini API prompt injection, SQL UNION extraction |
| AI | PixelPingu | Hard | PyTorch adversarial images vs ShuffleNet/RegNet |
| Crypto | BPCasino | Easy | CBC fixed-IV, ciphertext-collision oracle |
| Crypto | Compressed | Hard | gmpy2, Sage, LLL lattice reduction |
| Crypto | Flagtrix | Hard | Groebner basis, polynomial systems |
| Forensics | TLS Challenge | Easy | Wireshark TLS keylog decrypt |
| Forensics | Disk Partition | Easy | string matching, CLI tools |
| Forensics | Trashbin | Medium | SMB2 pcap, ZIP carving |
| Forensics | File Hidden | Medium | WAV LSB stego -> ZIP |
| Misc | Bad Apple? Sequel | Easy | YouTube metadata |
| Misc | Bad Apple? | Medium | Infinite Storage Glitch, video, Docker |
| Pwn | CSES | Medium | buffer overflow, heap leak, pwntools |
| Pwn | DragonBalls | Hard | use-after-free, fastbin, libc leak, ROP |
| RE | Hide and Seek | Medium | LCG reversal, XOR decryption |
| RE | Finesse | Hard | PDF parsing, linear algebra |
| Web | MAL | Medium | hash leak via sort API, cache bug |
| Web | MALD | Medium/Hard | SSRF + path traversal + ~/.curlrc RCE |
| Web | BALD | Hard | SSRF -> Gopher -> MongoDB wire protocol -> privesc |
| Web | Admin Panel | Hard | password bruteforce, proxy rotation, curl override RCE |

## 4b. 2026 per-category forecast (compiled 2026-05-23)

Synthesized from a raw scan of `practice/2023-archive/`, `practice/hyrnit-source/`,
and `writeups/` (J4F edition - 9 solves, 13th place, year unmarked but pre-2025).
The forecast holds in the same priority order as STRATEGY.md solve-order.

```
CRYPTO  (~4 challenges expected: 1 sanity + 1 easy + 1 mid + 1 hard)
+-- Sanity / encoding         base64, ROT, hex chains
+-- Easy textbook bug         substitution cipher (boxentriq), fixed-IV CBC,
                              Mersenne predict via randcrack (OH SEED, J4F)
+-- Medium bootleg primitive  homebrew AES/SBOX, malformed RSA (bootleg_aes 2023)
+-- Hard math                 LLL lattice (Compressed 2025) or
                              Groebner basis (Flagtrix 2025)

FORENSICS  (~4 challenges, mostly easy/mid - the bracket-winning category)
+-- TLS pcap decrypt          Wireshark + keylog file (TLS Challenge 2025)
+-- Disk / FS carving         strings, binwalk, foremost, photorec (Disk Partition 2025)
+-- Stego                     WAV LSB, image LSB, audio spectrogram (File Hidden 2025)
+-- Protocol pcap             SMB2/HTTP/USB reassembly (Trashbin 2025)

WEB  (~3-4 challenges, easy + 2 chains)
+-- Easy isolated bug         sort API leak, IDOR, weak auth (MAL 2025, No Backend J4F)
+-- Chain 1                   SSRF -> Gopher -> internal protocol (BALD 2025)
+-- Chain 2                   path traversal -> dotfile read -> RCE (MALD 2025, ~/.curlrc)
+-- Optional                  brute + proxy rotation (Admin Panel 2025)

RE  (~3 challenges, easy + mid + hard)
+-- Easy                      flag-check function in C/Go binary (Go_Mal 2023)
+-- Medium                    Android APK via jadx (babyroid J4F), .NET, or LCG reverse
+-- Hard                      math-heavy: matrix exponentiation, linear algebra (Finesse 2025)

PWN  (~3 challenges, mid-heavy)
+-- Medium                    classic BoF + libc leak (CSES 2025, www J4F)
+-- Medium                    Python jail / pickle / unsafe deserialization (pickle_trouble 2023)
+-- Hard                      UAF / fastbin / tcache (DragonBalls 2025)

AI  (~2-3 challenges - new since 2025, now permanent)
+-- Easy                      prompt injection / chatbot guard bypass (Campus Tour 2025)
+-- Medium                    LLM + SQL extraction (gsql1 2025)
+-- Hard                      adversarial image vs PyTorch model (PixelPingu 2025)

MISC / OSINT  (~2 easy challenges, points-dense)
+-- YouTube/file metadata     exiftool, ffmpeg (Bad Apple? Sequel 2025)
+-- Encoding / OSINT          chained encodings, Google-fu (japanese 2023)

SANITY  (always exactly 1, free flag)
```

Confidence per layer:

| Layer | Confidence | Why |
|-------|------------|-----|
| Categories | 95% | 2023, 2025, J4F edition all used the same six core categories; AI added in 2025 has stuck. |
| Per-category archetypes | 80-90% | Each category has 1-2 recurring shapes; three editions matched the same molds. |
| Difficulty distribution (~10:10:7) | 80% | Holds within ~10% across editions. |
| Specific problems | 0% | Authors rotate the bug; toolchain stays the same. |
| Point values | 0% | Dynamic scoring on rCTF - per-team count determines points. |

## 4c. Toolchain required (derived from the forecast)

The forecast translates to this tool list. The "In setup.sh?" column is
unverified - run an audit before relying on it.

| Tool | Used for | In setup.sh? |
|------|----------|--------------|
| Wireshark + tshark | Forensics pcap (every edition) | unverified |
| binwalk, foremost, photorec, scalpel | Disk/file carving | unverified |
| Audacity, Sonic Visualiser | Stego audio | unverified |
| pwntools | Pwn (every edition) | unverified |
| gdb + pwndbg or gef | Pwn debugging | unverified |
| ROPgadget, one_gadget | Pwn ROP chains | unverified |
| Sage, gmpy2, sympy, fpylll | Crypto hard tier (LLL, Groebner) | unverified |
| jadx, apktool, dex2jar, frida | Android RE | unverified |
| Ghidra, radare2, IDA Free | Native RE | unverified |
| randcrack (pip), pycryptodome | Crypto easy/mid | unverified |
| PyTorch + torchvision | AI hard tier (adversarial images) | unverified |
| sqlmap, ffuf, gobuster, curl | Web | unverified |
| Burp Suite Community (or Caido/ZAP) | Web proxy | unverified |
| exiftool, ffmpeg | Misc / metadata | unverified |
| boxentriq.com (web tool, no install) | Substitution cipher one-click | n/a |
| ChatGPT / Gemini / Claude (rules-allowed) | Archetype recognition | n/a |

## 5. How many challenges, and the target

Expect ~24-30 challenges in 2026, distributed roughly:

```
  Easy / free : ~10   MUST clear all. This tier IS the bracket.
  Medium      : ~10   target 5-8. This separates top-10 from the pack.
  Hard        : ~6-8  bonus. 1-2 if time allows. Do not chase.
```

Target to win Bảng Triển Vọng: roughly 15-20 solves - not the whole board.

## 6. The winning insight

Every edition has a predictable easy tier of ~8-12 challenges that need only
tool knowledge and pattern recognition, not deep exploitation. Triển Vọng is won
by clearing that entire easy tier plus as many mediums as possible. The hard
lattice / heap / SSRF-chain challenges are NOT required to place top 10. Breadth
beats depth. Points-per-minute beats raw points.
