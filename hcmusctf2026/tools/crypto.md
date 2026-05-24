# Crypto - Toolchain

Research-backed 2026-05-23 by cross-referencing five independent sources: HackerDNA's 2026 CTF toolkit, the `apsdehal/awesome-ctf` curated list, neerajlovecyber's CTF cryptography cheatsheet, Jorian Woltjer's `book.jorianwoltjer.com` RSA chapter, and Robin Jadoul's 2024 lattice training notes. Cross-checked against the 2023 HCMUS-CTF qualifier (`practice/2023-archive/`) and the J4F-edition writeups (`OH SEED`, `SignMe`, `Substitution`).

## Tier 1 - must have, install before 08:00 23/05

| Tool | Why it is the consensus pick | Install |
|------|------------------------------|---------|
| **CyberChef** | Universal first-pass: encoding chains (base64/hex/ROT/morse), classical ciphers, hash ID, byte ops, AES test-vectors. Browser-only, no dependency. Cited in every cheatsheet. | https://gchq.github.io/CyberChef/ (save the page offline before the CTF in case the venue blocks it) |
| **SageMath** | The only realistic environment for lattice (LLL, BKZ), Coppersmith, Groebner basis, ECDLP, ring arithmetic at scale. No substitute exists in CTFs. `Compressed` and `Flagtrix` (2025) and `SignMe` (J4F) were unsolvable without it. | Manjaro/Arch: `pacman -S sagemath` (~2 GB). The `setup.sh` already lists it. |
| **pycryptodome** | The standard Python cryptography library for CTF: `long_to_bytes`, `bytes_to_long`, RSA key construction, AES modes, padding helpers. Import as `from Crypto.Util.number import ...`. | `pip install pycryptodome` inside a venv. Do not install the legacy `pycrypto` package. |
| **RsaCtfTool** | The "try everything" RSA hammer: Wiener, Boneh-Durfee, common-modulus, Fermat, Pollard rho, Hastad broadcast, small-d, ~30 attacks against `(n, e, c)`. Solves the easy/medium RSA bucket without thinking. | `pip install rsactftool` or `git clone https://github.com/RsaCtfTool/RsaCtfTool && pip install -r requirements.txt` |
| **randcrack** | Mersenne Twister state recovery from 624 consecutive `random.getrandbits(32)` outputs. Cracks Python `random.seed(...)` instantly once you have enough output. Solved `OH SEED` (J4F) and trivializes anything shaped like CRY1 (2023). | `pip install randcrack` |

Minimum viable kit during the qualifier:
**CyberChef (browser) + SageMath + pycryptodome + RsaCtfTool + randcrack.**

## Tier 2 - load on demand when the archetype matches

| Tool | Trigger archetype | Install / URL |
|------|-------------------|---------------|
| **hashcat** | GPU hash cracking (MD5/SHA/PBKDF2/bcrypt/NTLM). | `pacman -S hashcat` |
| **John the Ripper** | CPU hash cracking + the `*2john` adapter zoo: `pem2john`, `ssh2john`, `zip2john`, `pdf2john`, `keepass2john`. | `pacman -S john` |
| **dCode.fr** | Classical/historical ciphers (Caesar, Vigenere, Playfair, Beaufort, Bacon, Polybius). Browser-only. | https://www.dcode.fr/ |
| **quipqiup.com** | Monoalphabetic substitution and Vigenere without a key, one-click. | https://www.quipqiup.com/ |
| **boxentriq.com** | Same archetype as quipqiup, alternate front-end; J4F's `Substitution` writeup used this exact site. | https://www.boxentriq.com/code-breaking |
| **xortool** | Repeating-XOR with unknown key length. | `pip install xortool` |
| **FeatherDuster / Cryptanalib** | Automated cryptanalysis triage when the archetype is unclear (does mode-detection, simple oracles). | `pip install featherduster` |
| **padding-oracle-attacker** | CBC padding oracle (Vaudenay 2002) over HTTP. | `npm i -g padding-oracle-attacker` |
| **editcap** (Wireshark suite) | Embed a TLS keylog into a pcapng via secrets block: `editcap --inject-secrets tls,keys.log in.pcapng out.pcapng`. Replayable from a script, unlike the Wireshark GUI Preferences route. | Ships with Wireshark: `pacman -S wireshark-qt` (already required by forensics) |
| **hash_extender** | Length-extension on MD4 / MD5 / SHA-1 / SHA-256 / SHA-512. | `git clone https://github.com/iagox86/hash_extender && make` |
| **gmpy2 + sympy** | Arbitrary-precision integer math and symbolic math from Python. Use when Sage is overkill but `int` is too slow. | `pip install gmpy2 sympy` |
| **fpylll** | Low-level lattice / LLL primitives from Python when you need a custom basis Sage cannot express cleanly. Build is heavy - prefer distro packages where possible. | `pacman -S python-fpylll` or `pip install fpylll` |
| **flatter** | Fast lattice reduction for large Coppersmith bases. Outperforms `fplll` on lattices with hundreds of rows; the standard upgrade when SageMath's default LLL is too slow. | https://github.com/keeganryan/flatter (build from source) |
| **cuso** | Automatic Coppersmith small-root solver for multivariate polynomials. Wraps flatter/fpylll under the hood. Use when you have a polynomial system and do not want to hand-craft the lattice. | `pip install cuso` |
| **yafu** | Automated integer factorization (ECM + SIQS + GGNFS handoff for >95 digits). Faster than msieve. Use when RsaCtfTool gives up on a 200-300 digit `n`. | https://github.com/bbuhrow/yafu |
| **Alpertron ECM** | Browser-based ECM + SIQS factor calculator. Persists progress in localStorage, so a long factorization survives a tab reload. Good fallback when you cannot install yafu in time. | https://www.alpertron.com.ar/ECM.HTM |
| **factordb.com** | Lookup cache for already-factored integers. Always check before launching a sieve. | http://factordb.com/ |
| **CryptoHack** | Not a tool - the de facto training playground and writeup index. Paste challenge code into its search to find the matching archetype. | https://cryptohack.org/challenges/ |
| **ChatGPT / Gemini / Claude** | Archetype identifier of last resort. Rules-allowed (HCMUS-CTF-PATTERNS §1b). Paste the `server.py` source, ask "what attack does this enable". | n/a |

## Mapping back to HCMUS-CTF archetypes

Cross-referenced with `HCMUS-CTF-PATTERNS.md` §3 and §4b.

| Archetype | Where it showed up | Primary tool | Backup |
|-----------|--------------------|--------------|--------|
| Sanity / encoding chain | every edition | CyberChef | `python -c "import base64; ..."` |
| Monoalphabetic substitution | Substitution / Substitution 2 (J4F) | quipqiup.com or boxentriq.com | dCode |
| Caesar / Vigenere with unknown key | classical bucket | dCode | CyberChef "Vigenere" recipe |
| Fixed-IV CBC / ciphertext-collision oracle | BPCasino 2025 | pycryptodome (replay the encrypt path) | hand-rolled XOR |
| Bootleg AES / homebrew S-box | bootleg_aes 2023 | Read the script, identify the missing diffusion step, invert it with pycryptodome | - |
| RSA, any flavor (Wiener, common-modulus, small-e, partial-key) | M_Side 2023, recurring | RsaCtfTool first | SageMath for Coppersmith / partial-key, gmpy2 for manual modular math |
| Large `n` (>200 digits) RsaCtfTool cannot factor | rare-but-real | yafu (local) | Alpertron ECM (browser) -> factordb cache check |
| Mersenne Twister / Python `random` predict | CRY1 2023, OH SEED (J4F) | randcrack | hand-rolled state inversion |
| MT19937 state directly recoverable from a process memory dump | forensics-adjacent | Locate the 624-word state buffer inside the `_random.Random` C object (see `tools/forensics.md` for the volatility step), feed to randcrack via `setstate` - skip the 624-outputs collection step entirely | hand-rolled state inversion |
| Python `random.seed(int)` with a guessable seed (time, user id) | CRY1 2023 | brute the seed range with `random.seed(t)` in a loop | randcrack if 624 outputs are leaked instead |
| LCG with leaked outputs | crypto+RE bucket | SageMath ring solve | sympy `Mod` solve |
| TLS pcap with provided keylog | TLS Challenge 2025 | `editcap --inject-secrets tls,keys.log in.pcapng out.pcapng` then open in Wireshark | GUI: Wireshark Preferences -> Protocols -> TLS -> (Pre)-Master-Secret log filename (use only when file is plain `.pcap`, since editcap's secrets-block needs PCAPNG) |
| TLS pcap with NO provided keylog, but memdump / `/proc` snapshot present | crypto+forensics handoff | Strings-grep the dump for the six NSS keylog labels (`CLIENT_RANDOM`, `CLIENT_HANDSHAKE_TRAFFIC_SECRET`, `SERVER_HANDSHAKE_TRAFFIC_SECRET`, `CLIENT_TRAFFIC_SECRET_0`, `SERVER_TRAFFIC_SECRET_0`, `EXPORTER_SECRET`) - browsers store these as plaintext ASCII in process memory. Then `editcap --inject-secrets` as above. | volatility + `linux.proc.Maps` if strings-grep misses; check `/proc/<pid>/environ` for `SSLKEYLOGFILE` path leak |
| Hash cracking (hash in hand) | misc-adjacent | hashcat (GPU) | John (CPU + `*2john` adapter). Hash/token recovery FROM a system (journal, sqlite, history) belongs in `tools/forensics.md` |
| Padding oracle (CBC) | classic | padding-oracle-attacker | hand-rolled with pycryptodome |
| Length-extension (MD/SHA) | classic | hash_extender | - |
| LLL lattice (small unknowns, hidden number) | Compressed 2025 | SageMath | fpylll, flatter for big bases |
| Coppersmith partial-key / small-root | recurring hard | SageMath `small_roots()` | cuso (auto), flatter (fast LLL) |
| Groebner basis / polynomial systems | Flagtrix 2025 | SageMath `Ideal.groebner_basis()` | - |
| ECDLP / curve cryptography | recurring hard | SageMath | - |
| ElGamal / DSA / ECDSA nonce reuse or weak-k | SignMe (J4F) | SageMath `Matrix.solve_right` in `Zmod(p-1)` | gmpy2 manual |
| Custom in-binary crypto | Is_This_Crypto 2023 (cross-cat with RE) | Identify the primitive, lift to Python with pycryptodome | - |
| Unknown archetype | first 5 minutes of triage | Paste the server source into ChatGPT/Gemini and ask "name the attack class" | CryptoHack writeup search |

### Key material reconstruction (crypto + forensics dovetail)

A crypto challenge that ships with a companion forensics artifact (pcap + memdump, pcap + disk image, pcap + `/proc` snapshot) is almost always asking the solver to RECOVER the key material first, then decrypt. The split: forensics extracts, crypto decrypts. The handoff is one of these strings:

| What to grep for | What it gives you | Decrypt step |
|------------------|-------------------|--------------|
| `CLIENT_RANDOM <64hex> <96hex>` (and the other five NSS labels) in a memdump | TLS 1.2 keylog | `editcap --inject-secrets tls,keys.log in.pcapng out.pcapng` |
| `CLIENT_HANDSHAKE_TRAFFIC_SECRET <64hex> <64hex>` + the matching server / 0-RTT lines | TLS 1.3 keylog | same `editcap` recipe - editcap handles both versions |
| `SSLKEYLOGFILE=<path>` in `/proc/<pid>/environ` snapshot | path to a keylog file that should be elsewhere in the artifact | find the file, then `editcap` |
| 624 consecutive 32-bit words inside a `_random.Random` C object in a Python process dump | MT19937 internal state | `randcrack` with `setstate`, predict next outputs directly |
| `[A-Fa-f0-9]{32,64}` blobs in journal/history/sqlite-WAL files | hash or token to crack | hand off to `tools/forensics.md` for extraction; bring the hash back here for hashcat/john |

Tools required for the extraction step (volatility3, strings, journalctl, sqlite3) live in `tools/forensics.md`. Only the `editcap` step is on the crypto side.

## Workflow

```
                +--------------------------------------+
  challenge --> | TRIAGE (5 min hard cap)              |
                |                                      |
                | 1. Read the title + description.     |
                | 2. Open server.py / chal source.     |
                | 3. Pattern-match against §4b row.    |
                | 4. Tag [easy] [mid] [hard] [skip].   |
                +-----+-----------+--------------------+
                      |           |
        archetype     |           |   archetype unclear
        recognized    |           v
                      |   +-----------------------+
                      |   | Paste into LLM:       |
                      |   | "name the attack"     |
                      |   | + CryptoHack search   |
                      |   +-----------+-----------+
                      |               |
                      v               v
                +-----------------------------------------+
                | EXPLOIT (35 min)                        |
                |                                         |
                | Pick the cell from the archetype table. |
                | Run the canonical recipe (below).       |
                | If 35 min in and no flag: skip.         |
                +-----------+-----------------------------+
                            |
                            v
                +-----------------------------------------+
                | VALIDATE (5 min)                        |
                |                                         |
                | 1. Confirm flag matches HCMUS-CTF{...}. |
                | 2. Submit once. Ops watch scoreboard.   |
                | 3. Save script under writeups/<name>/.  |
                +-----------------------------------------+
```

Time-box: 45 min hard, per STRATEGY.md "Discipline rules". A crypto challenge that does not yield in 45 min belongs in the day-2 mop-up window, not in a 4-hour rabbit hole.

### Canonical recipes per archetype

Each recipe is "open this tool, run this command, look for this signal". No improvisation - that is the point. If a recipe runs and does not produce `HCMUS-CTF{...}` in under 5 minutes, you are in the wrong archetype: stop, re-triage.

**1. Sanity / encoding chain.** Open CyberChef. Drop blob into Input. Apply "Magic" recipe with `Intensive mode = on` and `Depth = 6`. If Magic fails, walk the chain manually:

```
input -> "From Hex" -> "From Base64" -> "ROT13" -> "Reverse"
```

Stop the moment `HCMUS-CTF{` materializes in Output. Common chains: base64-of-hex, hex-of-base64, base32+base64, rot13+base64, morse+ROT.

**2. Monoalphabetic substitution.** Paste ciphertext into `quipqiup.com` or `boxentriq.com/code-breaking/cryptogram`. Hit Solve. If output is gibberish, fix it by pinning the flag crib:

```
quipqiup -> "Clues" tab -> enter "HCMUS-CTF{" as a crib
                                 -> pin those letters to their ciphertext counterparts
                                 -> re-solve
```

Fallback for polyalphabetic: dCode "Vigenere Cipher" with Kasiski test for key length.

**3. RSA easy/medium.** Extract `(n, e, c)`. Always check `factordb.com` first - 5 seconds, free. Then:

```
echo -n "$N" > n.txt
RsaCtfTool -n $N -e $E --uncipher $C --attack all --timeout 120
```

If `n` has a hint relation like M_Side 2023 (`hint = 4*p*p + q*q`), it is NOT a factorization problem. Treat as algebra in SageMath:

```python
# Sage
R.<p,q> = ZZ[]
I = R.ideal([4*p*p + q*q - hint, p*q - n])
print(I.variety())
```

**4. RSA hard (small-root, partial-key, Coppersmith).** SageMath with the bounds visible in the challenge.

```python
# Sage - partial high bits of p known
N = ...
p_high = ...     # known high bits of p
e = 65537
PR.<x> = PolynomialRing(Zmod(N))
f = p_high + x   # unknown low bits
roots = f.monic().small_roots(X=2^unknown_bits, beta=0.4)
p = int(p_high + roots[0])
q = N // p
```

If `small_roots` times out, swap default LLL for flatter via `cuso`, or hand-build the lattice and reduce externally.

**5. Mersenne Twister state recovery (`OH SEED`-style).** Collect 624 consecutive 32-bit outputs from the oracle (rejected outputs do not count - they must be sequential outputs of the same `Random` instance).

```python
from randcrack import RandCrack
rc = RandCrack()
for chunk in observed_32bit_outputs[:624]:
    rc.submit(chunk)
next_val = rc.predict_getrandbits(32)
```

If outputs are 64-bit, split each into two 32-bit halves before feeding.

**5b. Mersenne Twister state lifted from a memdump (forensics handoff).** When the challenge ships a Python process memory dump instead of an output stream, skip the 624-collection step entirely - the state is sitting in the `_random.Random` C object as 625 consecutive 32-bit words (624 state + index). See `tools/forensics.md` for the volatility3 `linux.proc.Maps` walk; bring the 625 words back here and:

```python
import random
state = (3, tuple(words_from_dump + (index_from_dump,)), None)
r = random.Random()
r.setstate(state)
print(r.getrandbits(32))    # next output predicted
```

**6. `random.seed(timestamp)` brute (CRY1 2023).** Window the seed around the observed connection time:

```python
import random, time
import datetime
target_sum = ...     # the encoded value from the server
flag_len = 26
seen_unix = int(time.time())
for t in range(seen_unix - 120, seen_unix + 120):
    random.seed(t)
    key = [random.randrange(1024) for _ in range(flag_len)]
    # CRY1 encoding is sum(k[i] * ord(c[i])) - invert if you know flag prefix
    # Practically: brute the flag char-by-char given the linear sum
    ...
```

Seed search is cheap - 240 candidates - so the bottleneck is inverting the per-byte sum, which for `sum(a_i * c_i)` with known `a_i` and partial known `c_i` is a 1-D constraint.

**7. Fixed-IV CBC / ciphertext-collision (BPCasino 2025).** Encrypt-only oracle with a fixed IV is leaky because `Enc_k(P) == Enc_k(P')` iff `P == P'`. Build a byte-by-byte dictionary:

```python
# pseudo
table = {}
for b in range(256):
    table[encrypt(prefix + bytes([b]))] = b
# then identify the unknown byte by matching ciphertext
```

Then recover the target plaintext block one byte at a time. Hint: the oracle usually accepts arbitrary user input under the same IV - that is your dictionary builder.

**8. Bootleg AES / homebrew block cipher (bootleg_aes 2023).** Read `enc.sh` / the encryption script. Identify what is missing vs real AES: usually MixColumns is absent, or the S-box is a fixed permutation with no diffusion. Reverse the steps in Python with pycryptodome's primitives or hand-rolled XOR. Look for: single-round permutations, identity S-boxes, missing key schedule.

**9. Hash cracking.** Identify hash with `hashid`. Choose mode by `-m`:

```
hashcat -m 0   md5
hashcat -m 100 sha1
hashcat -m 1400 sha256
hashcat -m 1000 NTLM
hashcat -a 0 -m <mode> hashes.txt /usr/share/wordlists/rockyou.txt
```

GPU unavailable? `john --wordlist=rockyou.txt --format=<fmt> hashes.txt`. ZIP/PDF/SSH: use the matching `*2john` adapter first.

**10. Padding oracle (CBC).** Confirm distinguishable errors (HTTP 200 vs 500, "Invalid padding" vs "Wrong MAC"). Then:

```
padding-oracle-attacker decrypt 'http://target/api?ct=$CT' \
    --error 'invalid padding' \
    --concurrency 8 \
    --block-size 16
```

Walk away. Comes back with plaintext. Average solve under 60 seconds for one block.

**11. LLL / hidden-number / knapsack (Compressed 2025).** Build the basis matrix in Sage. The art is the basis - the reduction is a one-liner.

```python
# Sage - canonical HNP shape
M = Matrix(ZZ, [
    [q,  0,  0,  ...],
    [0,  q,  0,  ...],
    ...
    [t1, t2, t3, ..., 1, 0],
    [a1, a2, a3, ..., 0, K],
])
B = M.LLL()
# scan B.rows() for one matching the bound; recover the secret
```

If LLL output looks wrong, try `M.BKZ(block_size=20)`, then `block_size=30`. If still too slow on a tall lattice, export the matrix and reduce with flatter externally.

**12. Groebner basis / multivariate (Flagtrix 2025).** Set up the ring matching the modulus, build the ideal, reduce.

```python
# Sage
P.<x0, x1, x2, x3> = PolynomialRing(GF(p))
I = ideal([
    f1(x0, x1, x2, x3) - c1,
    f2(x0, x1, x2, x3) - c2,
    ...
])
G = I.groebner_basis()
print(G)   # flag variables appear linearly
```

If the basis does not collapse to linear, you do not have enough equations - go back to the oracle and pull more samples.

**13. DSA / ECDSA / ElGamal nonce reuse (SignMe J4F).** Two signatures with related nonces over different messages give two equations in two unknowns over `Z/(p-1)Z` (or `Z/qZ` for ECDSA).

```python
# Sage - ElGamal nonce ratio attack like SignMe
Z = Zmod(p-1)
A = matrix(Z, 2, [[s1, r1], [3*s2, r2]])   # 3 = the known k2/k1 ratio
y = vector(Z, 2, [h1, h2])
k, x = A.solve_right(y)
```

The "art" is figuring out the relation between nonces from how the challenge generates them - often a simple linear combination of user input bytes.

**14. ECDLP on a weak curve.** SageMath. If the curve order is smooth (Pohlig-Hellman), or singular, or anomalous, Sage's `.discrete_log()` handles it directly. Otherwise it is a hard problem; skip.

**15. TLS pcap decryption (keylog provided).** Inject the keylog into the pcapng once, then open in Wireshark - this beats the GUI Preferences route because the keys travel with the file:

```
editcap --inject-secrets tls,keys.log capture.pcapng decrypted.pcapng
wireshark decrypted.pcapng    # HTTP / HTTP2 / gRPC now visible under TLS frames
```

If the file is a legacy `.pcap` (not pcapng), editcap cannot embed the secrets block; fall back to Wireshark Preferences -> Protocols -> TLS -> (Pre)-Master-Secret log filename, point it at `keys.log`.

**16. TLS pcap, no keylog provided (forensics handoff).** When the challenge ships a memory dump or `/proc` snapshot alongside the pcap, the keylog is recoverable. Grep the dump for the six NSS labels:

```
strings -n 64 mem.raw | \
  grep -E '^(CLIENT_RANDOM|CLIENT_HANDSHAKE_TRAFFIC_SECRET|SERVER_HANDSHAKE_TRAFFIC_SECRET|CLIENT_TRAFFIC_SECRET_0|SERVER_TRAFFIC_SECRET_0|EXPORTER_SECRET) [0-9a-f]{64} [0-9a-f]{64,96}$' \
  > keys.log
editcap --inject-secrets tls,keys.log capture.pcapng decrypted.pcapng
```

Browsers (Firefox, Chromium) store these as plaintext ASCII in the renderer process, so a single strings pass usually catches them. If it does not, check `/proc/<pid>/environ` for an `SSLKEYLOGFILE` path leak pointing at the actual file elsewhere in the artifact, then `editcap` as above. The volatility3 walk lives in `tools/forensics.md`.

### Pre-qualifier verification (do today)

Run each Tier 1 tool against a known input before the qualifier opens. The first time `sage` complains about a missing GMP backend or RsaCtfTool fails on `gmpy2` is during the qualifier, not before.

```
sage --version
python -c "import Crypto; print(Crypto.__version__)"
python -c "import randcrack; print(randcrack)"
RsaCtfTool --help | head -5
```

Practice run: `practice/2023-archive/ctfs/HCMUS/2023/Quals/crypto/CRY1/server.py` is a `random.seed(int(time.time()))` archetype - solve it end-to-end as a dress rehearsal. Target time: 30 min.

## Sources

- [HackerDNA - CTF Tools: Essential Hacking Toolkit for Beginners (2026)](https://hackerdna.com/blog/ctf-tools)
- [apsdehal/awesome-ctf curated tool list](https://github.com/apsdehal/awesome-ctf)
- [CTF Cryptography Cheatsheet - neerajlovecyber](https://neerajlovecyber.com/ctf-cryptography-cheat-sheet)
- [Crypto Cheatsheet for CTFs - XSS3cut10n3r](https://xss3cut10n3r.me/posts/crypto-cheatsheet/)
- [Cryptography great cheat-sheet for CTFs - Rishav anand (Medium)](https://medium.com/@anandrishav2228/cryptography-great-cheat-sheet-for-ctfs-d2ada754b319)
- [RsaCtfTool on PyPI](https://pypi.org/project/rsactftool/)
- [RsaCtfTool GitHub](https://github.com/RsaCtfTool/RsaCtfTool)
- [RSA - Practical CTF (Jorian Woltjer)](https://book.jorianwoltjer.com/cryptography/asymmetric-encryption/rsa)
- [RSA Attacks for CTF Cryptography - picoCTF Solutions](https://picoctfsolutions.com/posts/rsa-attacks-ctf)
- [CryptoHack challenge archive](https://cryptohack.org/challenges/ctf-archive/)
- [Practical lattice reductions for CTF challenges - Robin Jadoul, 2024](https://ur4ndom.dev/static/files/latticetraining/practical_lattice_reductions.pdf)
- [keeganryan/flatter - Fast lattice reduction](https://github.com/keeganryan/flatter)
- [kionactf/coppersmith - Coppersmith method for CTF](https://github.com/kionactf/coppersmith)
- [Alpertron ECM Integer Factorization Calculator](https://www.alpertron.com.ar/ECM.HTM)
- [bbuhrow/yafu - Automated integer factorization](https://github.com/bbuhrow/yafu)
- [hackenproof-public/CTF-Toolkit curated list](https://github.com/hackenproof-public/CTF-Toolkit)
- [Wireshark editcap manual - `--inject-secrets` for TLS keylog injection](https://www.wireshark.org/docs/man-pages/editcap.html)
- [NSS Key Log Format - Mozilla / Firefox source documentation](https://firefox-source-docs.mozilla.org/security/nss/legacy/key_log_format/index.html)
