# HCMUS-CTF 2026 - Deep Research Dossier

Prepared 2026-05-19. Team `viecz`, Bảng Triển Vọng. Qualifier 23-24/05/2026.

## 1. What this competition is

HCMUS-CTF is run by the **Computer Security Club (CSC / CompSec Club)** of the
Faculty of Information Technology (FIT), University of Science, VNU-HCM. On
CTFtime the organizing team is **blackpinker** (team ID 155048) - "The Computer
Security Club's team of fit@hcmus", ~33 members, Vietnam rank ~7-20.

Running since at least 2020 (a "Warm-up Stage" that year). Editions: 2020, 2021,
2023, 2024, 2025, now 2026. The **2023 Qualifications carried a CTFtime weight of
9.42** - a serious, well-rated event by Vietnamese standards.

## 2. The 2026 event

| Round | Date | Mode | Who |
|-------|------|------|-----|
| Qualifier | 23-24/05/2026 | Online, Jeopardy | open to all registered |
| Final | 14/06/2026 | Onsite | top teams from qualifier |

| Bracket | Eligibility | Slots to final |
|---------|-------------|----------------|
| Bảng Triển Vọng | all 4 members HCMUS students | max 10 teams (top 10 score) |
| Bảng Tài Năng | >=1 non-HCMUS, or past champion (HCMUS-only may opt in) | max 15 (12 by score + 3 reserved HCMUS) |

`viecz` is in **Bảng Triển Vọng** - the correct call. All 4 members are HCMUS
K2025 freshmen. Triển Vọng is effectively the rookie bracket, walled off from
veterans.

## 3. The competitive landscape

- **UIT's team FunSociety won HCMUS-CTF 2025** - their 4th consecutive title.
  In the 2025 qualifier they led with **6190 points**. Members are UIT InSecLab
  info-security students, each a single-category specialist (Pwn / Web / RE /
  Forensics).
- **UIT is non-HCMUS, so FunSociety competes in Bảng Tài Năng, not Triển Vọng.**
  The strongest teams (UIT, KMA, veteran HCMUS squads) are in or self-select
  into Tài Năng.
- **First prize in Bảng Triển Vọng is genuinely winnable** - opponents are
  all-HCMUS, mostly-newcomer peer teams.

## 4. Categories and past challenges

Official 2026 categories: **Pwnable, Reverse Engineering, Web Security,
Forensics, Cryptography, AI Security** (plus Misc/OSINT in practice).

### HCMUS-CTF 2023 Qualifier (19 challenges, CTFtime archive)

| Category | Challenges |
|----------|-----------|
| RE | Go Mal!, real key, Kiwi |
| Crypto | Is This Crypto?, CRY1, bootleg aes |
| Web | Safe Proxy, Cute Quote |
| Pwn | string chan, M Side |
| Misc | pickle trouble, python is safe, coin mining, japanese, grind, falsehood |
| AI/Social | Social Engineering |
| Sanity | Sneak Peek, Sanity check (free points) |

### HCMUS-CTF 2025 Qualifier (from writeups)

| Category | Challenge | Technique |
|----------|-----------|-----------|
| Forensics | TLS Challenge | SSLKEYLOGFILE + Wireshark TLS decrypt |
| Forensics | Trashbin | SMB2 traffic carving, ZIP search |
| Forensics | Disk Partition | NTFS/HFS+/ext4, unallocated space recovery |
| Forensics | File Hidden | WAV LSB steganography -> embedded ZIP |
| Web | MAL | sort-API password-hash leak + cache bug |
| Web | MALD | SSRF + path traversal + ~/.curlrc RCE |
| Web | BALD | SSRF -> Gopher -> MongoDB wire protocol -> privesc |
| Crypto | BPCasino | CBC fixed IV=0, ciphertext-collision oracle |
| AI | PixelPingu | adversarial images vs ShuffleNet/RegNet |
| Misc | Is This Bad Apple? The Sequel | YouTube metadata / OSINT |

Difficulty read: **Web is the hardest** (multi-vuln chains). Forensics and Misc
have accessible entry points. Crypto rewards textbook-attack recognition. There
is always a free **Sanity check**.

## 5. Resources

| Resource | URL | Use |
|----------|-----|-----|
| CTFtime - HCMUS CTF profile | https://ctftime.org/ctf/902/ | event history, weight |
| CTFtime - 2023 Qualifier tasks | https://ctftime.org/event/1944/tasks/ | past challenge names |
| ctf-archives (HCMUS 2023 files) | https://github.com/sajjadium/ctf-archives (ctfs/HCMUS/2023) | downloadable 2023 challenges |
| HyrniT/ctf-hcmus-challenges | https://github.com/HyrniT/ctf-hcmus-challenges | challenge source by category |
| PSDat123/HcmusCTF-writeup | https://github.com/PSDat123/HcmusCTF-writeup | solutions |
| Dat2Phit writeup (2025 qual) | https://psdat123.github.io/posts/HCMUS-CTF-2025/ | 2025 web walkthroughs |
| Forensics writeup (2025) | https://hackmd.io/@h0a9d13p/BJRc65_8ge | TLS/stego/disk forensics |
| Web writeup - UniverSea (2025) | https://hackmd.io/@Nightcore/H1IHmIYIlg | SSRF/Gopher chains |
| CyberCh1ck writeup (2025) | https://hackmd.io/@fr4nk/BJNipkq8eg | AI/crypto/pwn |
| 2026 platform (rCTF) | https://ctf.blackpinker.com | live qualifier platform |
| Challenge instancer | https://instancer.blackpinker.com | per-team Docker instance spawner |
| Challenge host | https://chall.blackpinker.com | served challenge containers |
| Organizer Facebook | https://fb.com/hcmus.compsec.club | back-channel announcements |
| Organizer Discord | https://discord.gg/t339vUWsVj | primary support channel during qualifier |

The qualifier runs on **rCTF** (github.com/redpwn/rctf, redpwn's open-source CTF
platform, BSD-3, JavaScript SPA) with **lactf** template customizations copied
from UCLA's LA CTF. Engine confirmed 2026-05-21 via the `<meta name="rctf-config">`
tag, the `{kind,message,data}` JSON error envelope, and the SPA fingerprint
(all routes return the same 9140-byte `index.html`).

Key rCTF-config values harvested from the live homepage:

| Key | Value | What it means |
|-----|-------|---------------|
| `divisions` | `prospect`, `talent` | Bảng Triển Vọng vs Bảng Tài Năng segregation |
| `userMembers` | `false` | NO per-user accounts. One shared team account per team. |
| `allowRegister` | `false` | No self-registration. All teams pre-provisioned by orgs. |
| `dockerAPI` | `https://instancer.blackpinker.com` | challenge instance spawner |
| `dockerAPIHostName` | `chall.blackpinker.com` | hostname instances are served on |
| `instanceTTL` | `3600000` ms = **1 hour** | each spawned instance auto-dies after 1h |
| `startTime` / `endTime` | epoch ms - confirms 08:00 23/05 to 20:00 24/05 ICT | competition window |
| `emailEnabled` | `true` | platform can send email (rCTF features) |

Scoring rules from the page: **dynamic scoring** (each solve REDUCES the
challenge's value for everyone), no first-blood bonus, ties broken by who
reached top score first (trivial-category solves excluded). Flag format is
`HCMUS-CTF{TEXT_HERE}` unless a challenge says otherwise. AI tools (ChatGPT,
Gemini, etc.) are explicitly allowed by the rules.

## 6. Strategy to win Bảng Triển Vọng

Draft role assignment (reassign by actual strength):

| Member | Focus |
|--------|-------|
| Nguyễn Hữu Thiện Nhân (lead) | Web + coordination / flag log |
| Trương Hoài Đức | Reverse Engineering + Pwn |
| Trần Gia Sang | Crypto + AI Security |
| Thái Kha Bảo | Forensics + Misc/OSINT |

Principles:

1. **Breadth beats depth.** Triển Vọng is won by clearing every easy/medium
   challenge across all 6 categories, not by cracking one hard Web chain.
2. **Grab the Sanity check immediately** - free points, confirms flag format.
3. **Forensics + Misc are highest-yield** for a new team - tooling and patience,
   not deep exploitation. Drill: Wireshark + SSLKEYLOGFILE, binwalk/foremost
   carving, LSB stego (zsteg, Audacity spectrogram), disk imaging
   (Autopsy/FTK), strings/exiftool.
4. **Crypto: pattern-match textbook attacks** - fixed IV, ECB, small RSA, weak
   PRNG. Work the cryptohack.org intro track.
5. **Web: target single-bug challenges** first; leave SSRF+Gopher chains for
   last. Study the 2025 MAL/MALD/BALD writeups.
6. **RE/Pwn: own the easy tier** - Ghidra/IDA static reads, simple pwntools
   buffer overflows. Skip hard heap challenges.
7. **Practice as a team before 23/05.** Pull the 2023 challenges from
   sajjadium/ctf-archives and run a timed mock qualifier this week.
8. **During the qualifier:** shared flag/notes doc, no two people on the same
   challenge unless stuck, post every solved flag immediately, sleep in shifts
   across the 2 days.

## 7. Action items (as of 2026-05-21, 2 days out)

- [x] Qualifier URL: known. `https://ctf.blackpinker.com/` (rCTF). Team token
      in `ACCESS.secret.md` (gitignored, never commit).
- [ ] Forward the Discord invite (`https://discord.gg/t339vUWsVj`) to Đức,
      Sang, Bảo. Verify all 4 are in the server before 08:00 23/05.
- [ ] Dress-rehearse the login: each teammate clicks the invite URL once from
      their own browser, confirms the page shows team `viecz`, division
      `Prospect`. If anyone hits a token-expired error, ticket the orgs via
      Discord NOW, not on qualifier morning.
- [ ] Decide the solver-browser policy: pick ONE primary browser profile that
      will live-submit flags; ops uses a second profile (or different machine)
      for scoreboard watch. Avoid concurrent submit collisions.
- [ ] Run a timed 2023 mock qualifier this week (HCTF-2 in YouTrack).
- [ ] Set up the team toolkit: Manjaro host (already on rule, see setup.sh)
      with pwntools, Ghidra/IDA, Wireshark, Autopsy, binwalk, sage/python
      crypto libs, Burp Suite. Distrobox `ctf` for untrusted binaries.
