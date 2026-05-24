# Intel

Research dossiers and investigation notes that back up the operational docs
(STRATEGY.md, HCMUS-CTF-2026-RESEARCH.md, HCMUS-CTF-PATTERNS.md). Each file
is dated and stands alone. Strategy docs reference these; do not duplicate
content from here into them.

## Index

| File | Date | Topic |
|------|------|-------|
| [platform-discovery.md](platform-discovery.md) | 2026-05-21 | How we confirmed the qualifier platform is rCTF (not CTFd), with byte-level evidence. |
| [redpwn-and-rctf.md](redpwn-and-rctf.md) | 2026-05-21 | Who redpwn is, what rCTF is, why blackpinker using it instead of writing their own is the norm. |
| [qualifier-opening-recon.md](qualifier-opening-recon.md) | 2026-05-23 | Opening-hours snapshot of 25 released challenges, viecz position (rank 19/26 prospect), prospect-division standings, attack-order recommendation. |

## Convention

- One topic per file. Name by topic, not by date.
- Lead each file with a TL;DR and a date.
- Capture the evidence chain, not just the conclusion - so a future reader can re-verify or extend.
- Use ASCII tables / diagrams when comparing two models. Prose buries structure.
- Do not put secrets here. Secrets go in `ACCESS.secret.md` (gitignored).
