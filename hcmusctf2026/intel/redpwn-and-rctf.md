# Background: redpwn and rCTF

**Date:** 2026-05-21
**Purpose:** Explain who redpwn is, what rCTF is, and why HCMUS organizers
using rCTF (instead of writing their own platform) is normal, not lazy.

## redpwn the team

A US-based competitive CTF team. GitHub org founded 2019-01-08. Origin:
university students at US schools. Now an established CTF organization.

Competitive track record: top-50 globally on CTFtime across multiple years.
DEF CON CTF qualifier / finals appearances. Members have moved on to work at
Trail of Bits, Anthropic, and other security firms. Connected to the
`pwn.college` educational platform.

Domain: https://redpwn.net. Their annual competition is `redpwnCTF`.

## redpwn the toolmaker

23 public repos on `github.com/redpwn`. The relevant ones for understanding
CTF infrastructure:

| Repo | Stars | What it is |
|------|-------|-----------|
| `redpwn/jail` | 257 | nsjail-based Docker image for pwn challenges - de-facto standard CTF pwn sandbox |
| `redpwn/rctf` | (this) | scoreboard / auth / instancer software, BSD-3 |
| `redpwn/pow` | 5 | non-parallelizable proof-of-work for anti-abuse on challenge endpoints |
| `redpwn/admin-bot` | - | headless Chrome bot for client-side / XSS challenges |
| `redpwn/terraform-aws-admin-bot` | - | prod-grade Terraform to deploy admin-bot on AWS Fargate |
| `redpwn/terraform-google-admin-bot` | - | same for GCP Cloud Run |
| `redpwn/rvpn` | 12 | identity-based VPN for CTF infra |
| `redpwn/redpwnctf-2020-challenges` | 60 | open-sourced challenges from their 2020 event |
| `redpwn/redpwnctf-2021-challenges` | 32 | same, 2021 |

Take: redpwn is not a team that scraped a platform together for their own
event - they are a team that built the entire CTF-infra stack from
sandbox-up and open-sourced it. The `jail` sandbox in particular is likely
what `instancer.blackpinker.com` runs under the hood.

## What "rCTF" means

```
redpwn        the people (a CTF team)
redpwnCTF     their annual competition (the event)
rCTF          the software that runs redpwnCTF (now used by many other CTFs)
```

The "r" is for redpwn. The README opening line confirms it:

> rCTF is redpwnCTF's CTF platform. It is developed by the redpwn CTF team.

## Current maintenance status

The original `redpwn/rctf` repo carries this notice:

> This version is no longer maintained, please submit issues and feature
> requests to otter-sec/rctf.

So the active fork is now `otter-sec/rctf`. Otter Security is a US-based
smart-contract / security audit firm; they took over maintenance.

HCMUS's deployment could be running either fork - the on-wire fingerprint is
identical. If we hit a platform bug during the qualifier that looks like a
known rCTF issue, check both repos' issue trackers.

## Why HCMUS using rCTF is normal, not lazy

Rough split of CTF organizers worldwide by platform:

```
  ~70%  CTFd          (open source, US)    picoCTF, HTB, BSidesSF, many uni CTFs
  ~15%  rCTF / lactf  (open source, US)    LA CTF, redpwnCTF, HCMUS-CTF
   ~5%  custom        (built in-house)     DEF CON Finals, Google CTF
  ~10%  other / older
```

Peers who also use someone else's platform:

| Event | Run by | Platform |
|-------|--------|----------|
| LA CTF | ACM Cyber UCLA | rCTF (forked, added "lactf" templates - HCMUS reuses these) |
| picoCTF | Carnegie Mellon | CTFd-based, heavily customized |
| BSides SF CTF | Bay-area security pros | CTFd |
| ICTSC | Japan academia | CTFd |
| many Hack The Box events | HTB itself | CTFd for some events |

The only CTFs that build their own platform are:

1. **DEF CON CTF Finals** - they have crowd-sourced architecture innovation.
2. **Google CTF** - they have Google-scale engineering teams to spare.

That is the full list. Even UIT's FunSociety, the dominant Vietnamese team
that beat HCMUS 4 years running, has run their own internal events on CTFd.

## Why this matters strategically

The scoreboard, login flow, and dynamic scoring math are commodity. A CTF
organizer's actual skill shows in:

1. **Challenge authoring** - the only thing that affects difficulty.
2. **Infrastructure stability** - keeping instances up under load.
3. **Anti-cheat / team-specific flag salting**.
4. **Real-time support during the event**.

Blackpinker has been running HCMUS-CTF since 2020, and the 2023 Qualifier
earned a CTFtime weight of 9.42 (a respected score by Vietnamese standards).
The challenges themselves are where their competence lives. Writing the
scoreboard in-house would be wasted engineering against challenge quality.

Analogy: a university doesn't write its own LMS. It uses Moodle and puts
effort into the courses. HCMUS using rCTF is the same call.

## The lactf connection

The HCMUS deployment is NOT vanilla rCTF. It imports LA CTF's template
markdown shortcuts (the `[lactf div class="..."]` markers visible in the
homepage source). The blackpinker organizers either:

- Forked LA CTF's customized rCTF fork directly, or
- Cherry-picked the lactf templates onto another rCTF fork.

Either way, the homepage rules text is structurally identical to LA CTF's
event page (UCLA's 2024/2025 CTF). The "HCMUS students should use their
school email" line is the local edit on top of LA CTF's template.

Useful pointer: if a UX edge case shows up during the qualifier, look at
LA CTF's GitHub or past event sites for how their rCTF version behaves.
It is likely the same code path.

## Pointers for follow-up

- Upstream (frozen): https://github.com/redpwn/rctf
- Active fork: https://github.com/otter-sec/rctf
- redpwn site: https://redpwn.net
- LA CTF: https://lac.tf (their event)
- redpwn `jail` (the sandbox you are likely running against): https://github.com/redpwn/jail
- redpwn `admin-bot` (relevant if any Web challenge requires a bot-driven action): https://github.com/redpwn/admin-bot
