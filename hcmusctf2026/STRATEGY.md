# HCMUS-CTF 2026 - Execution Strategy (solo carry)

Team `viecz`, Bảng Triển Vọng. Qualifier 08:00 23/05 - 20:00 24/05/2026, online
Jeopardy, **36 hours** (not 48 - confirmed in BTC mail).

## Operating model

The effective technical team is one solver (carry). Sang is a partial second
solver if available. The other two members are headcount required by the
4-member rule and run operations only - no challenge-solving expected of them.

```
  +-----------------------------------------------------------+
  | SOLVER (carry)  | all solving: full board, all categories |
  +-----------------+-----------------------------------------+
  | SOLVER 2 (Sang) | optional second on Forensics + Crypto   |
  +-----------------+-----------------------------------------+
  | OPS x2          | flag submission into rCTF, scoreboard   |
  |                 | watch, food/coffee, sleep-shift timing  |
  +-----------------------------------------------------------+
```

## 36-hour timeline

```
  DAY 1 (23/05, wall clock 08:00 - 24:00, H0-H16)
  H0-2     08:00-10:00  TRIAGE SWEEP. Open every challenge. Tag
                        [free][easy][mid][hard][skip]. Solve nothing yet.
                        Build the kill list, sorted by points-per-minute.
  H2-3     10:00-11:00  Clear all [free] + sanity. Lock in flag format.
  H3-9     11:00-17:00  Strongest-category easy+mid tier, top to bottom.
  H9-13    17:00-21:00  Sweep [easy] across ALL other categories - fast
                        shallow wins. THIS IS THE BRACKET-WINNING BLOCK.
  H13-15   21:00-23:00  Continue [mid] in the strongest 1-2 categories.
  H15-16   23:00-24:00  Wrap day 1: write day-2 target list, queue sleep.

  SLEEP    00:00-06:00  H16-H22, 6 hours, NON-NEGOTIABLE. Sleep through
                        the dead hours; nothing rewards being awake at 4am.

  DAY 2 (24/05, wall clock 06:00 - 20:00, H22-H36)
  H22-23   06:00-07:00  Re-triage: scoreboard, newly-released challenges,
                        what slipped on day 1.
  H23-30   07:00-14:00  [mid] tier sweep, all categories. Bulk of the score.
  H30-31   14:00-15:00  Lunch + standings check. Decide hard vs mop-up.
  H31-34   15:00-18:00  [hard] tier ONLY if top-10 contested; otherwise
                        more [mid] mop-up. Triển Vọng is won on easy+mid.
  H34-35   18:00-19:00  Final mop-up: revisit any timed-out [easy]/[mid].
  H35-36   19:00-20:00  STOP solving. Verify every flag is submitted.
                        Lose nothing to a forgotten paste.
```

Sleep total: 6 h (one block, not two). 36 h is too short for the original
two-block plan - one consolidated overnight rest beats two fragmented naps.

## Discipline rules

- Time-box hard: 45 minutes per challenge, then move on. Mark it, return in the
  mop-up window. The classic loss is a 4-hour rabbit hole while easy flags rot.
- Triage before solving. The first 2 hours produce zero flags - correct. Knowing
  the whole board lets you always pick the best points-per-minute target.
- Points-per-minute, not points. Five 150-pt challenges at 1 h each beat one
  400-pt challenge at 5 h. Breadth wins Triển Vọng.
- Sleep is a weapon. Two blocks. The board releases early; nothing rewards being
  awake at 4am. A rested solver on day 2 out-solves a zombie.
- Forensics + Misc first when unsure. Points-dense, tool-driven, fast - they
  feed score while the brain is fresh for hard exploitation later.

## Solve-order priority

1. Sanity / free.
2. Easy tier, every category (the bracket is won here).
3. Medium tier, strongest categories first.
4. Hard tier, only with time remaining.

Target: ~15-20 solves total. See HCMUS-CTF-PATTERNS.md for the full pattern.

## Login policy (rCTF shared-team-account model)

The platform is **rCTF**, not CTFd. There is exactly **one** account for team
viecz - the team token is the password. Everyone who clicks the invite URL
logs into the same shared account.

```
  team viecz on rCTF
        |
        +-> one team token (= the password, kept in ACCESS.secret.md)
        |
        +-> shared session: each teammate clicks the invite URL,
            lands logged in as team viecz. No captain. No members.
```

Operational rules during the qualifier:

- ONE primary solver browser profile actually submits flags. Pick it before
  23/05 and stick with it. Avoids the "two teammates submit the same flag
  twice in 200ms" double-submit edge case.
- OPS read-only second login from a different browser profile (or a second
  machine). Use it to refresh the scoreboard and the challenge list - never
  to submit unless coordinated with the solver.
- NEVER paste the invite URL or token into ChatGPT, Gemini, screenshots,
  Discord, or any other public surface. Compromise of the token = full
  account takeover.
- If rCTF rotates the token mid-session (happens on first auth, may happen
  again), retrieve the new one from Profile -> Team Invite panel and update
  `ACCESS.secret.md` locally. Re-share the new URL inside the team Discord
  DM only.
- Do not log out unnecessarily. If you must, the invite URL still works -
  but rotation is silent and confusing under stress.

## Challenge instance lifecycle (rCTF dockerized challenges)

Per-team challenge instances spawn via `instancer.blackpinker.com` and are
served from `chall.blackpinker.com`. Each instance has a **1-hour TTL** -
after that, the container is killed and a fresh one starts on next request,
which means any state inside the container (uploaded files, partial RCE,
in-memory secrets, persistent shells) is GONE.

Implications for timeboxing:

- Save attack progress externally: exfil any state you need to a local
  notes file before the TTL clock runs out.
- Treat the instance as ephemeral - your exploit script must be replayable
  from scratch in one go, not "manual step 1, then 30 min later step 2".
- If you must take a break mid-challenge, do it inside the 45-min timebox
  rule anyway. The instance will still be replayable when you return; the
  state inside it might not.

## Pre-competition checklist (2 days out, 2026-05-21)

- [ ] Build the toolkit: run setup.sh on the Manjaro host.
- [ ] Create the isolation container (distrobox/podman) for untrusted binaries.
- [x] Qualifier URL known: https://ctf.blackpinker.com/ (rCTF). Team token in
      `ACCESS.secret.md`.
- [ ] Forward the Discord invite (https://discord.gg/t339vUWsVj) to all 3
      teammates. Verify everyone joined before 08:00 23/05.
- [ ] Login dress-rehearsal: every teammate clicks the invite URL, confirms
      Profile shows team `viecz` / division `Prospect`. Reports back via
      Discord. If any error, ticket orgs immediately.
- [ ] Pick the solver browser profile vs ops browser profile (see Login policy).
- [ ] Prepare the shared flag/notes doc - ops submits from it via the solver
      profile only (avoid double-submit).
- [ ] Run a timed mock with the 2023 archive challenges (HCTF-2 in YouTrack).
