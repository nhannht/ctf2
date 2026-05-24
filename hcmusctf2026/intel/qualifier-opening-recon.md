# Qualifier Opening Recon: Challenge Set + Standings

**Date:** 2026-05-23 (qualifier day 1, opening hours)
**Source:** Logged-in browser session at https://ctf.blackpinker.com/challs via
chrome-devtools MCP, plus authenticated `/api/v1/*` probes.
**Goal:** Snapshot the released challenge set, our team position, and the
prospect-division landscape at the moment of opening so later sessions have a
baseline to diff against.

## TL;DR

- Platform served 25 challenges across 6 categories at opening.
- Team `viecz` opened with 2 solves for 208 pts, sitting at division rank
  19 / 26 (prospect, "Triển Vọng") and global rank 70 / 82.
- 4 of 6 categories still have 0 solves for us (forensics, pwn, reverse, web).
  Per `STRATEGY.md` "breadth beats depth", these are the next-move priority.
- 5-way tie at 208 pts in prospect means one more solve jumps us +4 ranks.
- rCTF is using dynamic scoring: the "solves count" column is the truer
  difficulty signal than the displayed point value.

## Team identity snapshot

```
team:      viecz
division:  prospect (Triển Vọng)
score:     208
solved:    2 / 25
div rank:  19 / 26   (5-way tie at 208 with Số Páo Danh, ZingH3, YoungMan, Rrawrrrrrrrrrrr)
global:    70 / 82
```

Solves at snapshot time:

| Category | Name         | Points | Solves at submit |
|----------|--------------|--------|------------------|
| crypto   | EasyCurve    | 108    | 67               |
| misc     | sanity check | 100    | 75               |

## Prospect division standings (all 26 teams)

```
Rank  Team                              Score
  1   dacuhuki                          2335
  2   HackCompetitiveProgramming        1817
  3   LongTimeNoCTF                     1244
  4   TopFrag                           1184
  5   2Lazy2Carry                        938
  6   BAND                               598
  7   N3tw0rkGhosts                      585
  8   Kernel Panic                       558
  9   HCMUS-Lazarus                      558
 10   FOURDOGS                           548
 11   SoPaoDanh                          541
 12   CannotSolveCTF                     513
 13   Lastdance                          382
 14   GFUS                               339
 15   404N0tF0und                        239
 16   DLMQ                               231
 17   Số Páo Danh                        208   (tied)
 18   ZingH3                             208   (tied)
 19   viecz                              208   <- us
 20   YoungMan                           208   (tied)
 21   Rrawrrrrrrrrrrr                    208   (tied)
 22   4:00 am                            131
 23   Bonbon                             131
 24   Skibidi                            108
 25   ktbeo                              100
 26   NO FLAG NO LIFE                    100
```

Reference numbers for the bracket leader gap (informational only - we do not
compete with the talent bracket): talent leader is UIT-TraTac at 7648 pts.

## Released challenge set (25)

By category:

```
Category    Count   Our solves
crypto       5       1
forensics    3       0
misc         4       1
pwn          4       0
reverse      4       0
web          5       0
```

Sorted by solves descending (easier challenges first - dynamic scoring means
high solves = low remaining points):

| Solves | Category   | Name                          | Pts | Artifact                       |
|-------:|------------|-------------------------------|----:|--------------------------------|
| 75     | misc       | sanity check                  | 100 | (solved)                       |
| 67     | crypto     | EasyCurve                     | 108 | (solved)                       |
| 55     | forensics  | Streamer                      | 131 | stream.pcapng                  |
| 44     | reverse    | meowmeowmeow                  | 174 | meow.sb3 (Scratch project)     |
| 38     | reverse    | Model Inversion               | 209 | model.pt + run.py              |
| 37     | reverse    | 100goilays                    | 216 | 100goilays.zip                 |
| 21     | crypto     | Crypto101                     | 350 | crypto101.zip                  |
| 18     | web        | Pink Black Vault Heist        | 377 | dist zip + Spawn Instance      |
| 15     | web        | TARget                        | 394 | dist zip + Spawn Instance      |
| 14     | reverse    | Hide and Seek 2               | 402 | chall (ELF)                    |
| 12     | forensics  | Intro2Pcap                    | 417 | acme_crm_ir_capture.pcap       |
| 10     | misc       | トロール                       | 432 | https://troll.blackpinker.com/ |
|  7     | pwn        | dead pixel                    | 452 | dead_pixel.zip + spawn         |
|  7     | pwn        | xv6                           | 452 | xv6-player.zip + nc            |
|  5     | crypto     | Funny Helicopter Morphology 1 | 465 | dist.zip + spawn               |
|  4     | crypto     | Rust In Peace                 | 471 | rust-in-peace.zip + spawn      |
|  4     | pwn        | simple file manager           | 471 | simple_file_manager.zip        |
|  3     | web        | The Real TARget               | 477 | The-Real-TARget-dist.zip       |
|  3     | misc       | Nyanko Daisensou              | 477 | nyanko.blackpinker.com         |
|  3     | web        | Core Issues                   | 477 | CoreIssues.zip                 |
|  1     | forensics  | Memeory                       | 488 | Google Drive download          |
|  1     | pwn        | notebook                      | 488 | to_player.7z                   |
|  0     | misc       | Bad Apple 3                   | 500 | (YouTube link, iykyk)          |
|  0     | web        | Fun PHP                       | 500 | FunPHP.zip                     |
|  0     | crypto     | Funny Helicopter Morphology 2 | 500 | (uses spawn from part 1)       |

Note: solve counts and point values are live - rCTF rescales as new solves
come in. The table above is a snapshot, not a fixed reference. Re-query
`/api/v1/challs` for current values.

## Recommended attack order (matches STRATEGY.md breadth doctrine)

```
1. forensics / Streamer       (pcapng)     - covers forensics category
2. reverse  / meowmeowmeow    (.sb3)       - covers reverse, Scratch is zipped JSON
3. reverse  / Model Inversion (.pt)        - keeps reverse going, ML inversion
4. pwn      / dead pixel      (binary)     - covers pwn category
5. web      / Pink Black Vault Heist       - covers web category
```

After step 5 we have at least one solve in every category, which is the
defining win condition for Triển Vọng. Then go after the 0-solve crypto and
the higher-point web/reverse chains.

## Platform API recon

Confirmed live endpoints (all need `Authorization: Bearer <token>`):

| Endpoint                                              | What it returns                                       |
|-------------------------------------------------------|-------------------------------------------------------|
| GET /api/v1/users/me                                  | Team profile incl. score, division, **teamToken**     |
| GET /api/v1/challs                                    | Full challenge list with category, points, solves     |
| GET /api/v1/leaderboard/now                           | Global leaderboard (limit, offset)                    |
| GET /api/v1/leaderboard/now?division=prospect         | Filter by division (prospect or talent)               |
| GET /api/v1/users/me/solves                           | 404 - this endpoint does not exist on rCTF            |

Auth token storage in the browser: `localStorage.token` (raw string, NOT
JSON-wrapped - calling `JSON.parse` on it will throw).

### Security note

`GET /api/v1/users/me` returns the team's `teamToken` field in plaintext to
any authenticated session. That token grants full login to the team account.
Already known to be sensitive - it lives in `ACCESS.secret.md` (gitignored)
and `REGISTRATION.md` "Platform access". Recon only re-confirms this is the
active login secret and that the platform exposes it via the profile API.

Implication: a logged-in session is equivalent to possession of the team
token. Do not leave logged-in sessions on shared machines. Do not paste
console output containing the `teamToken` field anywhere outside the team.

## How to re-run this recon

1. Open https://ctf.blackpinker.com/challs in a logged-in Chrome tab.
2. Select the tab in chrome-devtools MCP, then run:

```javascript
async () => {
  let tok = localStorage.getItem('token');
  const headers = { 'Authorization': 'Bearer ' + tok };
  const j = async u => (await (await fetch(u, { headers })).json());
  return {
    me: await j('/api/v1/users/me'),
    challs: await j('/api/v1/challs'),
    prospect: await j('/api/v1/leaderboard/now?limit=30&offset=0&division=prospect'),
  };
}
```

3. Diff the new snapshot against this file (look for: new challenges
   released, our solves count moving, division rank shift).
