# Forensics - Toolchain

Research-backed (2026-05-23, revised post-team-review) by cross-referencing five
independent CTF forensics resources: Trail of Bits CTF Field Guide, HackTricks
file-carving chapter, CTF Support steganography pages, the Volatility Foundation
cheatsheets, and the DominicBreuker stego-toolkit. Consensus across the five
sources is consistent. The 2023 archive has no forensics material (sajjadium
captured only crypto/pwn/rev/web), so the archetype mapping below is anchored on
the four 2025 problems in `HCMUS-CTF-PATTERNS.md` §4b: TLS pcap decrypt, disk/FS
carving, WAV LSB stego, and SMB2 pcap reassembly. The 2.A-Web sub-section was
added after a cross-area critique from the web teammate covering HTTP/2,
WebSocket, chunked-body reassembly, and compressed-response unwrap. The 2.I
system-artifact sub-section was added to dovetail with tools/crypto.md hash
cracking (forensics recovers, crypto cracks).

## Tier 1 - must have, install before the qualifier

| Tool | Why it's the consensus pick | Install |
|------|----------------------------|---------|
| **Wireshark + tshark** | Every HCMUS edition ships a pcap. Wireshark for interactive inspection; tshark for scripted `--export-objects http,smb,imf,tftp` reassembly and `-Y` display-filter dumps. TLS decrypt via `Edit -> Preferences -> Protocols -> TLS -> (Pre)-Master-Secret log filename`. | `pacman -S wireshark-qt` (Manjaro/Arch). Add user to `wireshark` group for non-root capture. |
| **binwalk** | First reflex on any unknown blob: signature scan, embedded file detection, entropy plot, recursive extract. `binwalk -e file` writes carved children to `_file.extracted/`. The "is there a ZIP appended to this PNG" hammer. | `pacman -S binwalk` or `pip install binwalk` (Python 3 fork). |
| **exiftool** | Metadata is a free flag surface every edition: GPS, software fingerprint, embedded thumbnail, custom XMP fields stuffed by the author. `exiftool -a -G1 -s file` dumps every tag with group prefix. | `pacman -S perl-image-exiftool`. |
| **zsteg + steghide + stegsolve** | The three LSB hammers. `zsteg -a img.png` brute-forces every channel/bit/endianness combo on PNG/BMP. `steghide extract -sf img.jpg` handles JPEG DCT embedding (use **stegseek** for passphrase brute). Stegsolve is the Java GUI that flips bit planes interactively - irreplaceable when zsteg misses a non-standard plane. | `gem install zsteg`; `pacman -S steghide`; download `Stegsolve.jar` (no package). `pacman -S stegseek` for the cracker. |
| **Volatility 3** | The de-facto memory-dump framework. Plugin-based, supports Windows/Linux/macOS dumps. `vol -f mem.raw windows.pslist`, `windows.cmdline`, `windows.netscan`, `windows.malfind`. Vol2 is legacy but still needed for some pre-Win10 profiles. | `pipx install volatility3` (and keep a `vol.py` from Vol2 around for old profiles). |
| **Audacity + Sonic Visualiser** | Audio stego inspection. Audacity for waveform/spectrogram views and channel arithmetic (Left minus Right cancels noise to reveal hidden audio). Sonic Visualiser's spectrogram has finer FFT controls - the right tool when flag text is drawn into the frequency domain. | `pacman -S audacity sonic-visualiser`. |

Minimum viable forensics kit during the qualifier:
**Wireshark + binwalk + exiftool + zsteg + Audacity + Volatility 3.**

## Tier 2 - load on demand when the archetype matches

| Tool | Trigger archetype |
|------|-------------------|
| **foremost** | File-signature carver driven by `/etc/foremost.conf`. Use when binwalk extraction is too noisy or misses a signature. `foremost -t all -i blob -o out/`. |
| **photorec** | Recovers 480+ file types from raw images and corrupted filesystems. Use when foremost is too narrow or the input is a full disk image with no partition table. Part of the testdisk package. |
| **scalpel** | Foremost's faster sibling; same config-file model, but maintained separately. Useful as a tiebreaker carver. |
| **testdisk** | Partition-table repair and recovery. Recovers deleted FAT/NTFS/ext partitions and rebuilds boot sectors. Reach for it when the challenge file looks truncated or `fdisk -l` shows no partitions. |
| **Sleuth Kit + Autopsy** | Filesystem-level forensics on disk images: `fls`, `icat`, `mmls`, `tsk_recover`. Autopsy is the web UI. Use when the challenge is "find the deleted file in this dd image" rather than raw bytes. |
| **stegseek** | Brute-forces steghide passphrases (~millions/sec against rockyou.txt). The fast path when `steghide extract` fails with "wrong passphrase". |
| **DeepSound** | Specific stego tool that hides files inside WAV/FLAC with optional AES. If the challenge mentions DeepSound or you see `.dsf`-like containers, this is the only extractor that works. Windows-only - run under Wine or in a VM. |
| **wavsteg / stegolsb (LSB Steganography toolkit)** | CLI LSB extractor for WAV samples - the scripted alternative to clicking through Sonic Visualiser. `stegolsb wavsteg -r -i in.wav -o out.bin -n 2 -b 1000000`. |
| **NetworkMiner** | Pcap object reassembly with a graphical timeline (Linux: NetworkMinerCLI under mono). Easier than tshark when you want to eyeball every file/credential/session quickly. For web-crossover challenges, prefer `tshark --export-objects http,out/` plus Burp Repeater raw-paste (see Phase 2.A-Web) - it gives a replayable request, not just a list. |
| **PolarProxy + mitmproxy** | Replay/inspect TLS streams when the challenge provides a recorded session plus the key material - especially handy if the keylog format is non-standard. |
| **strings + xxd + hexdump -C + 010 Editor / ImHex** | Raw inspection. `strings -e l` for UTF-16 (Windows artifacts), `strings -n 8 file | grep -i flag` as the first one-liner on any binary blob. ImHex/010 Editor for templated parsing (PNG, PCAP, ELF) and bit-level edits. |
| **bulk_extractor** | Mass-extract emails, URLs, credit-card numbers, base64 chunks, and EXIF from any blob. Useful on memory dumps too big to load into Volatility quickly. |
| **PCAPNG + editcap inject keylog** | `editcap --inject-secrets tls,keys.log in.pcapng out.pcapng` embeds TLS keys directly into the pcap so other tools (Wireshark/tshark/PolarProxy) decrypt without per-tool configuration. |
| **CyberChef** | Same browser tool the crypto doc uses, but the "Magic" recipe is invaluable for unknown encodings extracted from a pcap payload or a memory dump. Offline-cache the page before the CTF. |
| **AperiSolve** (`aperisolve.com`) | One-shot online image analyser: zsteg + steghide + binwalk + EXIF + bit planes on one page. Useful as a second pair of eyes when your local toolchain returns nothing. Personal-experience claim: the site has been alive and stable through 2025. |

## Mapping back to HCMUS-CTF archetypes

The 2025 forensics block had exactly four challenges - TLS Challenge, Disk
Partition, Trashbin (SMB2 pcap), File Hidden (WAV LSB). Treat that as the 2026
template until proven otherwise.

| Archetype (2025 example) | Primary tool | Backup |
|--------------------------|--------------|--------|
| TLS pcap decrypt (TLS Challenge) | Wireshark with keylog file at TLS protocol prefs | `editcap --inject-secrets tls,keys.log in.pcapng out.pcapng` (PCAPNG only - DSB block needs PCAPNG format; convert .pcap with `editcap in.pcap in.pcapng` first) |
| TLS keys recovered from companion artifact | `strings -n 64 mem.raw \| grep -E '^(CLIENT_RANDOM\|CLIENT_HANDSHAKE_TRAFFIC_SECRET\|SERVER_HANDSHAKE_TRAFFIC_SECRET\|CLIENT_TRAFFIC_SECRET_0\|SERVER_TRAFFIC_SECRET_0\|EXPORTER_SECRET) [0-9a-f]{64}'` | `vol -f mem.raw windows.memmap --pid <browser> --dump`, then re-grep the dumped regions; check `/proc/<pid>/environ` for `SSLKEYLOGFILE=` path |
| Disk / FS carving (Disk Partition) | `binwalk -e` + `strings -n 8 \| grep -iE 'flag\|HCMUS'` | photorec on raw image, then Autopsy for filesystem-aware inspection |
| WAV LSB stego (File Hidden) | `zsteg -a` for PNG/BMP; for WAV: `stegolsb wavsteg` or Audacity "Analyze -> Plot Spectrum" | Sonic Visualiser spectrogram, DeepSound when the container hints it |
| SMB2 / HTTP / USB pcap reassembly (Trashbin) | `tshark -r cap.pcap --export-objects "smb,out/"` (also `http`, `imf`, `tftp`) | Wireshark GUI `File -> Export Objects -> SMB`; NetworkMiner for visual extraction |
| HTTP(S) replay from pcap (web crossover) | `tshark -Y 'http.request' -T json` then reconstruct as curl; paste raw stream into Burp Repeater - see Phase 2.A-Web | NetworkMiner credentials tab for quick sweep |
| Memory dump | `vol -f mem.raw windows.pslist / cmdline / netscan / malfind` then `windows.dumpfiles` | `strings -e l mem.raw \| grep -i flag` as a brute fallback while Volatility profiles load |
| Hash / token / secret recovery from system artifacts | `journalctl --no-pager --output=cat \| grep -iE 'authorization\|bearer\|token\|password'`; `sqlite3 history.sqlite "SELECT * FROM history"` for browser/shell history; `cat .bash_history .zsh_history` | `bulk_extractor` for mass extraction of base64/JWT/PEM-like blocks. Crack the recovered hashes with hashcat / John per tools/crypto.md |
| Image with metadata or appended data | `exiftool -a -G1 -s img` + `binwalk -e img` | AperiSolve as a sanity check |
| Image LSB / bit-plane | `zsteg -a img.png` | Stegsolve bit-plane scrubber |
| JPEG passphrase stego | `steghide extract -sf img.jpg -p ''` then `stegseek img.jpg rockyou.txt` | - |
| Unknown blob | `file blob`, then `binwalk blob`, then `strings -n 8 blob \| head -50` | `bulk_extractor -o out blob` |
| LLM as archetype identifier | ChatGPT / Gemini / Claude (rules-allowed) | - |

## Workflow

Forensics challenges decompose into three phases. Run them in order. Do not
skip triage - guessing the archetype wastes the 45-minute timebox from
STRATEGY.md "Discipline rules".

### Phase 1: Triage (target: under 5 minutes)

The goal is to identify what the file actually is. The provided extension lies
half the time - magic bytes do not.

```
file blob                        # filetype by magic bytes
xxd blob | head -2               # confirm magic visually
exiftool -a -G1 -s blob          # all metadata, every group
binwalk blob                     # signature scan (no extract yet)
strings -n 8 blob | head -40     # cheap content peek
strings -e l blob | head -40     # UTF-16 if Windows artifacts suspected
```

Decision tree after triage:

```
+-- magic = PCAP / PCAPNG       -> Phase 2.A (pcap)
+-- magic = PNG/JPG/GIF/BMP/WebP-> Phase 2.B (image)
+-- magic = WAV/FLAC/MP3/OGG    -> Phase 2.C (audio)
+-- magic = ZIP/7z/RAR/TAR/GZ   -> Phase 2.D (archive)
+-- magic = ELF / PE / Mach-O   -> Phase 2.E (binary) - tell RE teammate, may be misclassified
+-- magic = disk/FS (MBR/GPT/FAT/NTFS/ext) -> Phase 2.F (disk image)
+-- magic unknown / "data"      -> Phase 2.G (raw blob) - binwalk + strings + bulk_extractor
+-- binwalk shows embedded files -> carve first with `binwalk -e`, then re-triage each child
```

### Phase 2: Exploit (canonical recipes)

**2.A - pcap (TLS / SMB2 / HTTP / USB / DNS / ICMP)**

```
# 0. CHEAPEST WIN FIRST: look for a sibling keylog before doing anything else.
#    Authors who want you to decrypt TLS usually ship the keys alongside.
ls -la "$(dirname cap.pcap)"
ls "$(dirname cap.pcap)" | grep -iE 'keys?\.log|keylog|sslkey|secret|tlskeys?'

# 1. If there is a keylog file, embed it directly into the pcap.
#    editcap --inject-secrets requires PCAPNG (DSB block format).
#    If the input is .pcap, convert first:  editcap cap.pcap cap.pcapng
editcap --inject-secrets tls,keys.log cap.pcapng cap-decrypted.pcapng

# 2. Pull objects out without manually clicking through Wireshark.
tshark -r cap-decrypted.pcapng --export-objects "http,out_http/"
tshark -r cap-decrypted.pcapng --export-objects "smb,out_smb/"
tshark -r cap-decrypted.pcapng --export-objects "imf,out_mail/"
tshark -r cap-decrypted.pcapng --export-objects "tftp,out_tftp/"

# 3. Grep the carved blobs and the raw pcap for the flag prefix.
grep -rai 'HCMUS-CTF{' out_*/
strings cap-decrypted.pcapng | grep -i 'HCMUS-CTF{'

# 4. If USB pcap: extract HID keystrokes
tshark -r usb.pcap -Y 'usb.transfer_type == 0x01 && usb.src == "1.4.1"' \
       -T fields -e usbhid.data

# 5. No keylog file? Look for one in any companion memory dump or /proc snapshot.
#    The TLS master secrets live in browser process memory as plaintext ASCII
#    NSS keylog lines. The six labels and their hex shapes are well-known.
strings -n 64 mem.raw | grep -E \
  '^(CLIENT_RANDOM|CLIENT_HANDSHAKE_TRAFFIC_SECRET|SERVER_HANDSHAKE_TRAFFIC_SECRET|CLIENT_TRAFFIC_SECRET_0|SERVER_TRAFFIC_SECRET_0|EXPORTER_SECRET) [0-9a-f]{64}' \
  > recovered_keys.log
# Then loop back to step 1 with recovered_keys.log.
```

**2.A-Web - HTTP / HTTP/2 / WebSocket pcap (web crossover)**

When the pcap contains web traffic and the goal is to UNDERSTAND or REPLAY a
request, not just carve files. Six recipes ordered by likelihood:

```
# i. Reconstruct an interesting request as raw HTTP, then paste into Burp
#    Repeater (Burp Community works - "Send to Repeater" via raw paste).
#    Find the stream first:
tshark -r cap.pcap -Y 'http.request' \
       -T fields -e tcp.stream -e http.host -e http.request.method -e http.request.uri \
       | sort -u
# Then dump the full HTTP request bytes for one stream:
tshark -r cap.pcap -q -z "follow,tcp,raw,7"        # stream 7 example
# Paste the raw request into Burp Repeater - see tools/web.md §A.2
# (protected-path bypass recipe is the canonical Repeater muscle memory).

# ii. Chunked transfer-encoded bodies are sometimes shown raw (1f\r\n...0\r\n).
#     Enable "Reassemble chunked transfer-encoded bodies" in
#     Edit -> Preferences -> Protocols -> HTTP, or post-process:
python3 -c "import sys, io, http.client; \
  print(http.client.HTTPResponse(io.BufferedReader(io.BytesIO(sys.stdin.buffer.read()))).read())" \
  < raw_response.bin

# iii. HTTP/2 over TLS (Cloudflare/Nginx, gRPC). Requires the keylog from 2.A.0.
tshark -r cap.pcap -o "tls.keylog_file:keys.log" -Y http2 \
       -T fields -e http2.header.name -e http2.header.value -e http2.data.data
# gRPC challenges: same dissector, payloads are length-prefixed protobuf.

# iv. Compressed response bodies. Carved files from --export-objects http
#     come out still gzipped/brotli/zstd when Content-Encoding is set.
for f in out_http/*; do
  enc=$(file "$f")
  case "$enc" in
    *gzip*)   mv "$f" "$f.gz" && gunzip "$f.gz" ;;
    *Brotli*) brotli -d "$f" -o "${f}.br_out" ;;
    *Zstd*)   zstd -d "$f" -o "${f}.zst_out" ;;
  esac
done

# v. Cookies, bearer tokens, JWTs - the most common "replay the admin" wins.
tshark -r cap.pcap -Y 'http.cookie or http.set_cookie' \
       -T fields -e http.host -e ip.dst -e http.cookie -e http.set_cookie
tshark -r cap.pcap -Y 'http.authorization' \
       -T fields -e http.host -e http.authorization
# Hunt JWTs in carved bodies:
grep -aroE 'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+' out_http/
# Forge / inspect with jwt_tool - see tools/web.md §B7 for the full
# alg=none / weak-HMAC / kid-traversal / jku-SSRF / RS256->HS256 ladder.
# To replay a lifted admin cookie against /admin: see tools/web.md §A.2
# (set Cookie header in Repeater, hit the protected endpoint).

# vi. WebSocket frames (ws:// or wss://). rCTF/lactf-style live chat/game
#     challenges often use this surface.
tshark -r cap.pcap -Y 'websocket' \
       -T fields -e websocket.payload -e websocket.opcode -e websocket.fin
# GUI alternative: right-click any ws frame -> Follow -> WebSocket Stream.
# Binary frames: pipe payload through xxd and reassemble per protocol.
# To replay carved frames live: wsrepl / wsdler - see tools/web.md Tier 2.
```

**2.B - image**

```
exiftool -a -G1 -s img                            # may already contain the flag
strings -n 8 img | grep -i 'HCMUS-CTF{'           # plain or trailing
binwalk -e img                                    # appended ZIP/PNG is common
zsteg -a img.png                                  # PNG/BMP LSB brute
steghide extract -sf img.jpg -p ''                # JPEG empty passphrase
stegseek img.jpg /usr/share/wordlists/rockyou.txt # passphrase brute
# If everything above is empty, open in Stegsolve and step through every bit plane.
```

**2.C - audio (WAV / FLAC / MP3 / OGG)**

```
exiftool -a -G1 -s audio.wav
binwalk -e audio.wav                              # appended payload
stegolsb wavsteg -r -i audio.wav -o out.bin -n 2 -b 1000000   # LSB extract
# Visual checks:
audacity audio.wav    # waveform + Analyze -> Plot Spectrum
sonic-visualiser audio.wav  # spectrogram (Layer -> Add Spectrogram)
# Channel arithmetic for hidden-in-difference tricks:
ffmpeg -i audio.wav -filter_complex \
  '[0:a]channelsplit=channel_layout=stereo[L][R];[L][R]amerge,pan=mono|c0=c0-c1[out]' \
  -map '[out]' diff.wav
```

**2.D - archive (ZIP / 7z / RAR)**

```
unzip -l archive.zip          # inventory, look at sizes and timestamps
# Encrypted ZIP: classical John attack
zip2john archive.zip > zip.hash
john --wordlist=/usr/share/wordlists/rockyou.txt zip.hash
# Known-plaintext on ZipCrypto (not AES):
bkcrack -C archive.zip -c known.bin -p plain.bin
```

**2.E - binary (ELF / PE / Mach-O)**

Send to the RE teammate after recording basic metadata:

```
file bin && checksec --file=bin && exiftool bin
strings -n 8 bin | grep -i 'HCMUS-CTF{'
```

**2.F - disk image**

```
mmls disk.img                       # partition layout
fsstat -o <offset> disk.img         # filesystem metadata per partition
fls -r -o <offset> disk.img         # full file tree, deleted included
icat -o <offset> disk.img <inode>   # extract one file
tsk_recover -e -o <offset> disk.img out/   # extract all (incl. unallocated)
# If the partition table is broken:
testdisk disk.img                   # interactive recovery
# For convenience GUI: autopsy -> add data source -> disk.img
```

**2.G - raw blob / unknown**

```
binwalk -e blob                   # carve everything binwalk recognises
foremost -t all -i blob -o fore/  # second-opinion carve
photorec blob                     # broadest carve, expect noise
bulk_extractor -o bulk blob       # emails, URLs, credit cards, EXIF, base64
strings -n 8 blob | grep -aE 'HCMUS-CTF\{|flag\{|FLAG\{'
```

**2.H - memory dump**

```
vol -f mem.raw windows.info                 # OS profile sanity
vol -f mem.raw windows.pslist               # process list
vol -f mem.raw windows.cmdline              # command lines (often leaks the flag)
vol -f mem.raw windows.netscan              # network sockets
vol -f mem.raw windows.malfind              # injected code regions
vol -f mem.raw windows.dumpfiles --pid <P>  # dump files mapped by PID
# Linux dumps swap windows.* -> linux.*; same plugin names.
strings -e l mem.raw | grep -aE 'HCMUS-CTF\{' &  # background brute while Vol loads
```

**2.I - system artifact (mounted filesystem / extracted home / live snapshot)**

When the challenge gives a filesystem snapshot and the goal is "find the secret
the user typed". Hash/token recovery feeds into tools/crypto.md hashcat/John for
cracking - this section is recovery only, not cracking.

```
# Shell history (often holds typed passwords, API tokens, curl auth headers).
cat ~/.bash_history ~/.zsh_history ~/.local/share/fish/fish_history 2>/dev/null

# systemd journal: typed sudo prompts, auth events, leaked env vars.
journalctl --no-pager --output=cat \
  | grep -iE 'authorization|bearer|token|password|api[_-]?key|secret'

# Browser history / cookies / session storage (SQLite).
sqlite3 ~/.mozilla/firefox/*.default*/places.sqlite "SELECT url FROM moz_places ORDER BY last_visit_date DESC LIMIT 50"
sqlite3 ~/.mozilla/firefox/*.default*/cookies.sqlite "SELECT host,name,value FROM moz_cookies"
sqlite3 "~/.config/google-chrome/Default/History" "SELECT url FROM urls ORDER BY last_visit_time DESC LIMIT 50"

# SQLite write-ahead logs sometimes hold rows already deleted from the main DB.
strings places.sqlite-wal | grep -iE 'flag|HCMUS-CTF|token'

# /etc/shadow style hashes (hand off to tools/crypto.md for cracking).
grep -E '\$[0-9a-z]+\$' /mnt/snapshot/etc/shadow

# SSH agent forwarding leaks (running agent in the snapshot).
find /tmp -name 'ssh-*' -type d 2>/dev/null
```

### Phase 3: Validate

```
# Flag format check (rCTF rejects malformed flags).
echo "$FLAG" | grep -E '^HCMUS-CTF\{[^}]+\}$'

# Sanity: the inner text should be UTF-8 printable, no stray null bytes.
echo -n "$FLAG" | xxd | head -2
```

If the candidate matches but the platform rejects it: re-extract with a
different tool (different LSB endianness, different bit plane, different
encoding chain through CyberChef). Do NOT mutate the flag manually - the
extracted bytes are authoritative; if it does not validate, your extraction is
wrong, not the flag text.

## Sources

- [Forensics - CTF Field Guide (Trail of Bits)](https://trailofbits.github.io/ctf/forensics/)
- [HackTricks - File/Data Carving and Recovery Tools](https://book.hacktricks.wiki/en/generic-methodologies-and-resources/basic-forensic-methodology/partitions-file-systems-carving/file-data-carving-recovery-tools.html)
- [CTF Support - Audio Steganography](https://ctf.support/steganography/audio-steganography/)
- [CTF Support - Image Steganography](https://ctf.support/steganography/image-steganography/)
- [CTF Support - Memory Forensics](https://ctf.support/forensics/memory-forensics/)
- [DominicBreuker/stego-toolkit](https://github.com/DominicBreuker/stego-toolkit)
- [0xRick - Steganography tools and resources](https://0xrick.github.io/lists/stego/)
- [Wireshark Wiki - TLS](https://wiki.wireshark.org/TLS)
- [Wireshark Tutorial: Decrypting HTTPS Traffic (Unit 42)](https://unit42.paloaltonetworks.com/wireshark-tutorial-decrypting-https-traffic/)
- [Wireshark Tutorial: Exporting Objects From a Pcap (Unit 42)](https://unit42.paloaltonetworks.com/using-wireshark-exporting-objects-from-a-pcap/)
- [tshark.dev - Export objects](https://tshark.dev/export/)
- [Volatility 3 Cheatsheet - neerajlovecyber](https://neerajlovecyber.com/memory-forensics-volatility-cheatsheet-guide)
- [The Volatility Foundation Blog](https://volatilityfoundation.org/volatility-blog/)
- [Practical Memory Forensics with Volatility 2 and 3 (0x0Aleem)](https://medium.com/@0x0Aleem/practical-memory-forensics-with-volatility-2-3-windows-and-linux-cheat-sheet-ef5eee325863)
- [Mason Competitive Cyber - Intro To CTF Forensics](https://competitivecyber.club/past-talks/MasonCC-S22-Intro-to-CTF-Forensics.pdf)
- [The Sleuth Kit - File and Volume System Analysis](https://www.sleuthkit.org/sleuthkit/desc.php)
- [CTF tools - Snyk](https://snyk.io/articles/ctf/ctf-tools/)
- [Img2Sound - Audio Steganography Cheatsheet](https://img2sound.com/articles/audio-steganography-cheatsheet/)
