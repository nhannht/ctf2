# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

CTF-preparation workspace for team `viecz` competing in HCMUS-CTF 2026 (qualifier 23-24/05/2026,
online Jeopardy, final 14/06/2026 onsite). Bracket: Bảng Triển Vọng (all-HCMUS rookie bracket).
NOT a software project - there is no build, no tests, no lint. The deliverable is solved flags
and writeups, not shipped code.

## Top-level layout

| Path | What it is | When to read it |
|------|------------|-----------------|
| HCMUS-CTF-2026-RESEARCH.md | Event facts, bracket rules, competitive landscape | Any question about who/when/where |
| HCMUS-CTF-PATTERNS.md | Cross-edition pattern table: what each category keeps reusing | Triage / picking which challenge to attack |
| STRATEGY.md | 36-hour execution plan, solver-vs-ops roles, discipline rules | During the qualifier or when planning |
| REGISTRATION.md | Team members, MSSV, emails, payment, fee record | Identity / contact questions only |
| setup.sh | Manjaro/Arch toolkit installer (pacman + AUR + pipx + gems) | Setting up a fresh machine |
| practice/2023-archive/ | sajjadium/ctf-archives clone, HCMUS 2023 Quals (crypto, pwn, rev, web) | Mock practice runs |
| practice/hyrnit-source/ | HyrniT/ctf-hcmus-challenges clone, organized by category | Browsing past challenge sources |
| writeups/ | Team J4F writeups from a past edition (9 challenges, 13th place) | Solution reference |
| tools/ | Per-area toolchain + workflow docs (Crypto, Forensics, Web, RE, Pwn, AI, Misc). See "Toolchain by area" below. | Before reaching for tooling on any challenge |
| intel/ | Research dossiers backing the operational docs (platform discovery, opponent recon, etc.) | When verifying claims in STRATEGY/RESEARCH or extending an investigation |

The two `practice/` subtrees are upstream git clones - treat them as read-only reference material;
do not edit, and do not commit changes back into them.

## Toolkit setup

```
bash setup.sh
```

Idempotent (`pacman --needed`, pipx upgrade fallback). Needs an AUR helper (yay or paru) for the
AUR section. Manual follow-ups printed at the end: wireshark group, docker enable, distrobox
isolation container for untrusted CTF binaries.

The container `ctf` (distrobox + archlinux) is the intended sandbox for running any challenge
binary. Never run an untrusted challenge binary on the host.

## Solving workflow

When the user asks to solve or analyze a challenge:

1. Read STRATEGY.md and HCMUS-CTF-PATTERNS.md once at the start of a solving session - they
   encode the time-box, points-per-minute, and pattern-match priorities the user wants applied.
2. Match the challenge against the pattern table in HCMUS-CTF-PATTERNS.md section 3 before
   reaching for tooling. Most challenges fit a known archetype.
3. Time-box: 45 minutes per challenge, then move on (STRATEGY.md "Discipline rules").
4. New writeups go under `writeups/<challenge-name>/` with `README.md` + `src/`. Match the
   existing folder shape, do not invent a new layout.

## Toolchain by area

Each area has a curated tools doc in `tools/` produced by a 7-agent Opus research team on
2026-05-23 (independent research + cross-area peer review in a 7-cycle: crypto <-> re,
re <-> pwn, pwn <-> misc, misc <-> ai, ai <-> web, web <-> forensics, forensics <-> crypto).
Each doc has the same shape: Tier 1 must-have, Tier 2 load-on-demand, archetype mapping
(cross-ref `HCMUS-CTF-PATTERNS.md` §3 / §4b), Workflow (triage -> exploit -> validate),
sources. Read the area's doc before reaching for tooling.

| Area | Doc | Tier 1 must-have |
|------|-----|------------------|
| Crypto | [tools/crypto.md](tools/crypto.md) | CyberChef, SageMath, pycryptodome, RsaCtfTool, randcrack |
| Forensics | [tools/forensics.md](tools/forensics.md) | Wireshark+tshark, binwalk, exiftool, zsteg+steghide+stegsolve, Volatility 3, Audacity+Sonic Visualiser |
| Web | [tools/web.md](tools/web.md) | Burp/Caido, ffuf, sqlmap, curl, Firefox devtools, Gopherus, jwt_tool |
| RE | [tools/re.md](tools/re.md) | Ghidra, jadx, radare2, gdb |
| Pwn | [tools/pwn.md](tools/pwn.md) | pwntools, gdb+pwndbg, ROPgadget, checksec, one_gadget |
| AI | [tools/ai.md](tools/ai.md) | ChatGPT/Gemini/Claude, PyTorch+torchvision, torchattacks, jailbreak catalog, garak |
| Misc/OSINT | [tools/misc.md](tools/misc.md) | exiftool, ffmpeg, binwalk, pickletools, unblob, CyberChef, Sherlock+theHarvester |

Cross-area note: when a challenge straddles categories (e.g. Crypto+RE like `Is_This_Crypto`
2023, or LLM-fronted Web like the 2025 chatbot widgets), check both docs. The peer-review
cycle made each doc explicitly cross-reference its neighbors at the handoff points (TLS-keylog
extraction across Crypto/Forensics, Python jail / pickle across Misc/Pwn, prompt-injection
across AI/Web, RNG-in-binaries across Crypto/RE).

## Task tracking (YouTrack)

This repo's tasks live in YouTrack project key **`HCTF`** (HCMUS-CTF 2026). Per the global
[`~/.claude/rules/task-management.md`](../../.claude/rules/task-management.md) rule, YouTrack is
the primary task manager - any tracked work for this repo goes there, not into a markdown TODO
in this directory.

Field scheme for HCTF (the default YouTrack scheme - older projects like VIECZ use a different
one, do NOT assume):

- **Type**: `Bug`, `Cosmetics`, `Exception`, `Feature`, `Task`, `Usability Problem`,
  `Performance Problem`, `Epic`
- **State**: `Submitted`, `Open`, `In Progress`, `To be discussed`, `Reopened`,
  `Can't Reproduce`, `Duplicate`, `Fixed`, `Won't fix`, `Incomplete`, `Obsolete`, `Verified`
- **Priority**: `Show-stopper`, `Critical`, `Major`, `Normal`, `Minor`

Workflow:

1. At session start, run `mcp__youtrack__get_issue_fields_schema(projectKey="HCTF")` once to
   confirm the schema (it can drift if admins edit field schemes).
2. To see what's open: `mcp__youtrack__search_issues(query="project: HCTF")`.
3. Use `create_issue` / `update_issue` for persistent work; use the built-in `TaskCreate` ONLY
   for the within-session step list (per global rule).
4. Instance URL and auth token live in the YouTrack MCP server config (`~/.claude.json`,
   untracked) - read from there, never hardcode the domain in any file under this repo.

## Constraints that are easy to miss

- All 4 team members are HCMUS K2025 freshmen. The effective solver count is 1 (lead) plus
  Sang as a partial second on Forensics/Crypto - STRATEGY.md "Operating model". Plan accordingly.
- Qualifier platform confirmed 2026-05-21: **rCTF** (redpwn's open-source CTF platform with
  lactf customizations) at https://ctf.blackpinker.com/. NOT CTFd - the team model is one
  shared account per team, not per-user accounts. See STRATEGY.md "Login policy" for the
  operating implications. Team token and invite URL live in `ACCESS.secret.md` (gitignored,
  never commit). Discord server invite also in `ACCESS.secret.md` and in `REGISTRATION.md`
  "Platform access".
- Bracket Triển Vọng is won by clearing the easy tier across all 6 categories, not by cracking
  one hard chain. Breadth beats depth - HCMUS-CTF-PATTERNS.md section 6.
