# Memeory Investigation Notes

Date: 2026-05-24

Challenge:
- Name: `Memeory`
- Category: `forensics`
- Hint/description: `When was the last time you touch volatility? 4-part flag`

Local assets:
- `problems/meomory/Memeory-dist.zip`

Working interpretation so far:
- `Memeory` is almost certainly an intentional misspelling of `memory`.
- The hint explicitly points at memory forensics and Volatility.
- `4-part flag` strongly suggests the final flag is assembled from four independent pieces, likely recovered from different user artifacts inside memory.

## Browser/API Metadata

I did not use web search for public writeups.

Using the logged-in browser session, challenge metadata was pulled directly from the site API with the bearer token stored in browser local storage:

```js
await fetch("/api/v1/challs", {
  headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
}).then(r => r.json())
```

Relevant result:
- name: `Memeory`
- category: `forensics`
- description: `When was the last time you touch volatility? 4-part flag`
- files: Google Drive download link

## Extraction And Workspace

Archive structure:
- `sha256sum.txt`
- `challenge.tar.gz`

Main extracted artifact:
- `/tmp/memeory_chal/DESKTOP-1LI6VC6-20260522-105906.raw`

Raw image size:
- `5368709120 bytes` = `5 GiB`

Because the box has enough RAM, I copied the raw image to tmpfs for faster searching:
- `/dev/shm/memeory.raw`

Observed memory availability at the time:
- total RAM: about `31 GiB`
- available RAM: about `14 GiB`
- `/dev/shm`: `16 GiB`

## Volatility Attempts

`volatility3` is available through `uv tool run --from volatility3 vol`.

Useful plugins that worked:
- `windows.info`
- `windows.pslist`
- `windows.cmdline`
- `windows.filescan`
- `windows.dumpfiles`
- `windows.vadinfo`
- `windows.vadregexscan`
- `windows.memmap`

Unavailable or missing plugins in this environment:
- `windows.screenshot`
- `windows.clipboard`
- `windows.vadyarascan`

Follow-up on the missing clipboard path:
- `windows.clipboard` is not present in Volatility 3
- the official Volatility 3 issue tracker also lists `clipboard` as still missing from Volatility 2 parity
- I therefore built an official Volatility 2.6.1 environment in Docker to test the legacy `clipboard` plugin directly

Conclusion:
- Volatility is the intended workflow for this challenge.
- Direct raw searching and carving were still useful for cross-checking and for extracting secondary artifacts.

## Volatility 2 Clipboard Check

Because the challenge hint explicitly points at old-school Volatility workflow, I tested the official Volatility 2 GUI plugins against the image.

Environment:
- official `volatilityfoundation/volatility` source, version `2.6.1`
- Python 2.7 in Docker
- Windows profile:
  - `Win10x64_19041`

The Volatility 2 GUI path works on this image:
- `sessions` enumerates both Session `0` and Session `1`
- `wndscan` successfully recovers `WinSta0` and its desktops:
  - `Default`
  - `Disconnect`
  - `Winlogon`

Most important result from `wndscan` on the interactive station:

```text
WindowStation: WinSta0
SessionId: 1
cNumClipFormats: 0
pClipBase: 0x0
Formats:
```

The direct `clipboard` plugin run also returned only the table header and no recovered entries.

Conclusion:
- the official clipboard path was checked
- there is no populated clipboard content at capture time
- clipboard is not currently a productive lead for the missing flag part

## Confirmed Volatility Recoveries

Important process list entries:
- `explorer.exe` PID `5632`
- `KeePass.exe` PID `2964`
- `mstsc.exe` PID `6136`
- `mspaint.exe` PID `7472`
- `DumpIt.exe` PID `4036`

Command-line evidence:
- `mspaint.exe` opened `C:\Users\obiwan\Documents\flag2.png`
- `KeePass.exe` opened `C:\Users\obiwan\Documents\darkest_secrets.kdbx`

Recovered file objects from `windows.filescan.FileScan`:
- `0xe2825df7f840` -> `\Users\obiwan\Documents\flag2.png`
- `0xe2825df807e0` -> `\Users\obiwan\Desktop\flag1.txt`
- `0xe2825ee48a00` -> `\Users\obiwan\Documents\darkest_secrets.kdbx`

Successful file dumps:
- `flag1.txt`:
  - `/tmp/vol_dump_flag1/file.0xe2825df807e0.0xe2825dfc3960.DataSectionObject.flag1.txt.dat`
- `flag2.png`:
  - `/tmp/vol_dump_flag2/file.0xe2825df7f840.0xe2825dfd7ca0.DataSectionObject.flag2.png.dat`

Unsuccessful file dump:
- `darkest_secrets.kdbx` via `dumpfiles --virtaddr 0xe2825ee48a00` returned `Error dumping file`

## High-Signal Raw Findings

### Direct flag fragment

Searching the raw image for the flag prefix recovered the same fragment multiple times:

- `HCMUS-CTF{d0nt_m1nd_me_j`

Offsets for `HCMUS-CTF{`:
- `308416448`
- `736881992`
- `1043644416`
- `4938936240`

Offsets for `d0nt_m1nd_me_j`:
- `308416458`
- `736882002`
- `1043644426`
- `4938936250`

Bytes at offset `308416448` confirm the literal string:

```text
48 43 4d 55 53 2d 43 54 46 7b 64 30 6e 74 5f 6d
31 6e 64 5f 6d 65 5f 6a
```

Which decodes to:

```text
HCMUS-CTF{d0nt_m1nd_me_j
```

This looks like only the beginning of the final flag, not the full answer. The dumped `flag1.txt` recovered by Volatility matches this exact prefix and then ends in null padding.

### User file/activity artifacts

The following paths appear in memory and look challenge-relevant:
- `C:\Users\obiwan\Desktop\flag1.txt`
- `C:\Users\obiwan\Documents\flag2.png`
- `C:\Users\obiwan\Documents\darkest_secrets.kdbx`

Related application traces suggest:
- KeePass was used
- Paint was used
- Shell activity/jumplist/recent-file style data references those filenames

Example `flag1.txt` offsets:
- `345294940`
- `345295117`
- `345295412`

Example `flag2.png` offsets:
- `271454100`
- `271454172`
- `314806596`
- `366293303`

Example `darkest_secrets.kdbx` offsets:
- `271452319`
- `271452403`
- `314806812`

## KeePass Lead

This is the strongest lead so far.

### KDBX headers in memory

Searching the raw image for the KDBX signature `03 d9 a2 9a 67 fb 4b b5` found candidate database copies at:
- `815274904`
- `985398576`
- `2694176768`
- `2853727152`

The first 12 bytes at a candidate header decode as:
- `sig1 = 0x9aa2d903`
- `sig2 = 0xb54bfb67`
- `ver = 0x30001`

This is consistent with KeePass KDBX 3.x.

The surrounding header bytes look like a normal KDBX3 header containing:
- cipher UUID
- compression flags
- master seed
- transform seed
- transform rounds
- encryption IV
- protected stream key
- stream start bytes
- inner random stream ID
- end marker

Observed tail of the parsed header includes:

```text
0a 04 00 02 00 00 00 00 04 00 0d 0a 0d 0a
```

That suggests inner random stream ID `2`, which likely means Salsa20 for protected fields.

### Decrypted XML exists in memory

Memory also contains plaintext KeePass XML with protected fields still encoded as protected blobs.

Offsets for key XML markers:
- `<Key>Password</Key>` at `871151228`, `871152562`, `4710936764`, `4710937998`
- `<Key>Title</Key>` at `871151338`, `871152668`, `4710936906`, `4710938148`, `4710939420`
- `<Value Protected="True">` at `871151255`, `871152589`, `4710936790`, `4710938026`

#### Sample database entries

At offset region around `871150900`, the XML contains stock KeePass sample entries:

- Title: `Sample Entry`
- Password blob: `nkUmw14yPgc=`
- URL: `https://keepass.info/`
- UserName: `User Name`

- Title: `Sample Entry #2`
- Password blob: `mmCY0tA=`
- URL: `https://keepass.info/help/kb/testform.html`
- UserName: `Michael321`

These are useful because they can help validate any protected-string decryption attempt.

#### Challenge-relevant entries

At offset region around `4710936400`, the XML contains a custom entry:

- Title: `CTF`
- UserName: `part4`
- Current protected password blob:
  - `4srUzbb793+HGBpaP6WuCm3nyRmlKy7DPH3j9A==`
- History protected password blob:
  - `56/i3V8RuHjhGY8lVBUuwQNAprHWKW/lgIcQad3yAqvqaA==`

There is also another entry nearby:
- Title: `kho ga free`
- UserName field appears to contain a partial YouTube URL:
  - `https://www.youtube.com/watch?...a7X1o`

Interpretation:
- The `CTF` entry is probably one flag component source.
- `UserName = part4` is too explicit to ignore.
- Since the XML is already decrypted but protected fields remain wrapped, the next step is to recover the protected-stream key and decode the protected values directly.

## KeePass Protected-Value Result

Using the recovered KDBX3 protected-stream parameters and validating against nearby sample entries, the `CTF` history protected password blob:

```text
56/i3V8RuHjhGY8lVBUuwQNAprHWKW/lgIcQad3yAqvqaA==
```

decrypts to:

```text
d_call_it_a_challenge_to_meet_kpi}
```

This is almost certainly the final flag tail and matches the `part4` username label.

Important refinement:
- the protected-stream setup was validated against the nearby KeePass sample entries
- sample blob `nkUmw14yPgc=` decrypts to `Password`
- sample blob `mmCY0tA=` decrypts to `12345`

The current `CTF` protected password blob in memory is not clean plaintext material. The raw bytes in the XML region are visibly corrupted in-place:

```text
4srUzbb793<05><d5>V<95>o<0c><00><80>+HGBpaP6WuCm3nyRmlKy7DPH3j9A==
```

Even with that corruption, the surviving suffix still decrypts consistently with the same `part4` tail. That means the current blob is not a new independent flag part; it is most likely another damaged copy or revision of the same `part4` entry.

Plaintext KeePass XML recovered so far only exposes three `UserName` values:
- `User Name`
- `Michael321`
- `part4`

No plaintext `part2` or `part3` KeePass entry has been recovered yet.

## PNG / `flag2.png` Work

The original `flag2.png` was successfully recovered with Volatility:
- `/tmp/vol_dump_flag2/file.0xe2825df7f840.0xe2825dfd7ca0.DataSectionObject.flag2.png.dat`

Recovered file type:
- PNG image data
- `1980 x 1080`
- 8-bit/color RGB

Visible content:
- a hand-drawn jar or container with a red lid
- orange shredded-looking contents
- black outline and face details
- small green marks

Static inspection results:
- chunk layout is normal: `IHDR`, `sRGB`, `gAMA`, `pHYs`, two `IDAT`, `IEND`
- there are `2551` bytes after `IEND`, but they are only zero bytes
- no interesting embedded metadata

Stego-oriented checks already attempted:
- OCR on the full image and targeted crops
- per-channel and bitplane inspection
- color-isolated masks for the main drawing colors
- simple LSB extraction and printable-string scans
- `zsteg -a`

Current conclusion:
- the saved PNG looks clean and intact
- no conventional PNG steganography has been identified so far
- because `mspaint.exe` had the file open, the stronger lead is Paint process memory, which may contain unsaved image content not present in the saved PNG

## Paint Memory Result

This is now a confirmed source of one middle fragment.

`mspaint.exe` PID `7472` contains three large private image-sized VADs of the same size:
- `0x22b103b0000 - 0x22b10bd8fff`
- `0x22b11420000 - 0x22b11c48fff`
- `0x22b124c0000 - 0x22b12ce8fff`

Each buffer matches:
- `1980 * 1080 * 4 + 2944 = 0x829000`

Reconstructing them as vertically flipped `BGRA` surfaces produced valid Paint canvas states. The saved `flag2.png` only contains the jar drawing, but the in-memory canvas contains extra black handwriting and arrows that were not saved back into the PNG.

Direct visual result from the reconstructed canvas:

```text
ust_doing_rando
```

This fragment is visible by inspection in the reconstructed Paint buffers, not just OCR. It appears below the jar and is present in multiple canvas states.

Useful generated images:
- `/tmp/mspaint_reconstructed.png`
- `/tmp/mspaint_comparison_sheet.png`
- `/tmp/mspaint_text_wide_sheet.png`
- `/tmp/buf2_reconstructed.png`
- `/tmp/buf3_reconstructed.png`

Interpretation:
- the Paint artifact is very likely one independent flag part
- when combined with the prefix from `flag1.txt`, it strongly suggests the phrase starts as `..._j` + `ust_doing_rando`
- however, no additional confirmed text for the next part has been recovered from the Paint buffers yet

## MSTSC / RDP Lead

`mstsc.exe` is now the main unresolved lead for the missing segment, and this lead has produced a real remote-screen decode rather than only strings.

Known facts:
- `mstsc.exe` PID `6136` was running at capture time
- its command line is just:

```text
"C:\Windows\system32\mstsc.exe"
```

- its handle table includes a named object:

```text
MSTSC_C_Users_obiwan_AppData_Local_Microsoft_TerminalServerClient_Cache_
```

That is strong evidence that the local RDP bitmap cache was active.

Volatility 3 work completed on this lead:
- dumped the full process memory map with:
  - `windows.memmap --pid 6136 --dump`
- exported machine-readable VAD and memmap tables:
  - `/tmp/mstsc_vadinfo_6136.json`
  - `/tmp/mstsc_memmap_6136.json`
- resulting process dump:
  - `/tmp/mstsc_memmap/pid.6136.dmp`
- dump size:
  - about `683 MiB`

Important network and registry context:
- `windows.netscan.NetScan` shows:
  - `10.1.1.99:49726 -> 10.1.1.142:3389 ESTABLISHED PID 6136 mstsc.exe`
- Terminal Server Client MRU registry data points at:
  - `MRU0 = 10.1.1.142`

Important configuration strings recovered from memory:
- `screen mode id:i:1`
- `desktopwidth:i:1643`
- `desktopheight:i:938`
- `bitmapcachepersistenable:i:1`
- `full address:s:10.1.1.142`

This establishes the actual RDP desktop geometry and confirms that persistent bitmap caching was enabled.

### Recovered live RDP surface

Multiple large anonymous `PAGE_READWRITE` VADs in `mstsc.exe` were rendered as image surfaces. Most candidates were black or noise, but one VAD decodes into a real remote screen when rendered with the recovered desktop geometry.

Most important candidate:
- base VAD: `0x29ad7870000`
- size: `6156288 bytes`

Rendering this surface with widths near the real desktop width produced a valid screen image:
- `/tmp/mstsc_surface_probe/real_dims/1641x938_crop.png`

Direct visual confirmation from that decoded surface:
- remote login screen is visible
- username shown on screen: `guy`
- timestamp visible in the upper-right area:
  - `Friday May 22 06:38`

Interpretation:
- the `mstsc.exe` graphics path is confirmed valid
- this is not random stripe noise or an incorrect decode model
- the missing flag part may still be present in another RDP surface, cache tile, or neighboring render buffer

### Better-covered `mstsc.exe` surfaces and recovered `flag3`

The first successful login-screen decode came from a low-residency buffer, so I rescored the `mstsc.exe` anonymous RW VADs and carved additional surfaces directly from the Volatility memmap dump.

Two important higher-coverage candidates:
- `0x29ad8310000`
  - size: `6193152`
  - page coverage in the memmap dump: about `94.9%`
- `0x29ad9a50000`
  - size: `6164480`
  - page coverage in the memmap dump: about `97.3%`

The first of those candidates produced a much more useful render:
- `/tmp/mstsc_surface_probe/new_candidates/0x29ad8310000_1641x938_crop.png`

This recovered remote screen is not a login page. It shows a browser window open to Canva on the remote machine with a handwritten red note labeled `flag3`.

Direct visual reading of the note:

```text
flag3
m_stuff_on_
window_4n
```

The heading `flag3` is just a label. The flag fragment itself is the two lower lines combined:

```text
m_stuff_on_window_4n
```

This fills the missing bridge between the Paint fragment and the KeePass tail:
- Paint gave:
  - `ust_doing_rando`
- `mstsc.exe` now gives:
  - `m_stuff_on_window_4n`
- KeePass gave:
  - `d_call_it_a_challenge_to_meet_kpi}`

Those parts concatenate cleanly into:

```text
...just_doing_random_stuff_on_window_4nd_call_it_a_challenge_to_meet_kpi}
```

This explains why the part boundary cuts through the leetspeak `4nd`.

### Persistent bitmap-cache evidence

Direct wide-string hits inside the dumped `mstsc.exe` memory include:
- `C:\\Users\\obiwan\\AppData\\Local\\Microsoft\\Terminal Server Client\\Cache\\bcache24.bmc`
- `bcache_lock.bmc`
- `BitmapPersistCache16Size`
- `BitmapPersistCache24Size`
- `BitmapPersistCache32Size`

These strings appear near client-rendering telemetry such as:
- `RDV::RDP::ClientRendering::FrameStart`
- `RDV::RDP::ClientRendering::FrameEnd`
- `RDV::RDP::ClientRendering::CacheGlyphCount`

This does not yet prove that the full `bcache24.bmc` payload was recovered intact, but it is strong evidence that the persistent bitmap cache path is active inside the same process memory that already yielded a valid remote screen.

Important refinement from the RDP client event log:
- dumping and parsing `Microsoft-Windows-TerminalServices-RDPClient%4Operational.evtx` shows:
  - server `10.1.1.142`
  - repeated client sessions on `2026-05-22`
  - `AvcEnabled = 1`

Interpretation:
- the modern RDP graphics pipeline was active
- that helps explain why classic persistent bitmap-cache carving was less productive than direct surface recovery from `mstsc.exe`

Direct string hits inside the dump include:
- copied `flag1` content such as `HCMUS-CTF{d0nt_m1nd_me_j`
- the persistent-cache path and related rendering strings above
- many unrelated noisy matches for words like `challenge`, `rando`, and `kpi`

Negative findings so far:
- no clean `part3` plaintext recovered from `mstsc.exe`
- other same-sized `mstsc.exe` surface candidates rendered as mostly black
- sparse candidate VADs rendered only as fragmentary stripes, not readable text
- no file object or live handle for `bcache24.bmc` was recovered through `windows.filescan` or `windows.handles`

## DWM Follow-Up

I also tested the Desktop Window Manager path to make sure the rendered `mstsc.exe` surface was not missing an easier compositor copy.

Volatility 3 work:
- `dwm.exe` PID `392`
- exported:
  - `/tmp/dwm_vadinfo_392.json`
  - `/tmp/dwm_memmap_392.json`
- rebuilt a process dump from mapped physical pages:
  - `/tmp/dwm_pid392.dmp`

Candidate surfaces rendered from the fully covered large RW VADs:
- `0x26a82910000` size `5955584`
- `0x26a824a0000` size `4194304`

Generated sheet:
- `/tmp/dwm_surface_probe/contact_sheet.png`

Result:
- both decoded surfaces are effectively black
- no useful desktop screenshot or text fragment has been recovered from `dwm.exe`

Conclusion:
- `dwm.exe` is currently a dead end
- `mstsc.exe` remains the highest-value unresolved lead

## Current Hypothesis

Most likely challenge structure:
- part 1 from `flag1.txt`
- one middle part from Paint memory
- one remaining unresolved part from another user-facing artifact
- part 4 from KeePass

Current assembled pieces:
- part 1 / prefix: `HCMUS-CTF{d0nt_m1nd_me_j`
- Paint fragment: `ust_doing_rando`
- `mstsc.exe` fragment: `m_stuff_on_window_4n`
- part 4 / tail: `d_call_it_a_challenge_to_meet_kpi}`

Recovered full assembly:

```text
HCMUS-CTF{d0nt_m1nd_me_just_doing_random_stuff_on_window_4nd_call_it_a_challenge_to_meet_kpi}
```

## Next Steps

1. Submit the assembled flag and verify it against the challenge service.
2. Preserve the generated `mstsc.exe` render that shows the `flag3` note.
3. Keep the `AvcEnabled` / graphics-pipeline note in the final writeup because it explains the successful path and the dead ends.

## Notes

No external public writeups were used.

The challenge name typo and the hint both still point to the same core idea:
- memory forensics
- user artifact recovery
- Volatility-era workflow, even if raw scanning is currently faster than full Volatility automation
