# Platform Discovery: Confirming the 2026 Qualifier Engine

**Date:** 2026-05-21 (2 days before qualifier)
**Trigger:** Organizer email arrived with a team token + one invite URL for all
4 teammates. Repo docs assumed the platform was CTFd, where one-link-per-team
is unusual. Investigation goal: verify the platform identity and the security
posture before sharing access with the team.

## TL;DR

- Platform is **rCTF** (redpwn's open-source CTF platform), with **lactf**
  template customizations copied from UCLA's LA CTF.
- NOT malicious. Site is legit, TLS valid, behind Cloudflare, CSP hardened.
- The "one link to all teammates" is correct for rCTF: it uses a single
  shared team account, NOT per-user accounts.
- The two-different-tokens (email vs Profile page) is rCTF's normal post-auth
  token rotation behaviour.

## Method

Three independent classes of evidence, any one of which would have been
conclusive on its own:

1. HTML / DOM markers in the served page.
2. API error envelopes from `/api/v1/*` probes.
3. SPA routing fingerprint (same body bytes for any non-API route).

Cross-referenced against rCTF upstream (`github.com/redpwn/rctf`) and a known
rCTF instance (LA CTF) for ground truth.

## Evidence

### 1. The `rctf-config` meta tag

The site embeds:

```
<meta name="rctf-config" content="{...}">
```

with a JSON payload containing rCTF-specific config keys. CTFd does not emit
this tag. Parsed payload:

| Key | Value | Implication |
|-----|-------|-------------|
| `ctfName` | HCMUS-CTF 2026 Qualification | identity |
| `divisions` | `{ prospect, talent }` | matches Bảng Triển Vọng + Bảng Tài Năng |
| `origin` | https://ctf.blackpinker.com | self-confirms domain |
| `dockerAPI` | https://instancer.blackpinker.com | Docker challenge spawner |
| `dockerAPIHostName` | chall.blackpinker.com | hostname instances serve on |
| `instanceTTL` | 3600000 ms (= 1 hour) | per-instance lifetime |
| `userMembers` | false | NO per-user accounts; one shared team account |
| `allowRegister` | false | self-registration disabled, pre-provisioned teams |
| `emailEnabled` | true | platform can send email |
| `startTime` | epoch ms = 08:00 23/05/2026 ICT | confirms email |
| `endTime` | epoch ms = 20:00 24/05/2026 ICT | confirms email |

### 2. JSON error envelope

```
$ curl -s https://ctf.blackpinker.com/api/v1/leaderboard/now
{"kind":"badBody","message":"The request body does not meet requirements.","data":null}
```

The `{kind, message, data}` shape is rCTF's signature error envelope. CTFd
uses `{success, errors, data}`. The literal string `"kind":"badBody"` lives
in the rCTF source.

API surface probe (all non-HTML, all JSON):

| Path | Status | Content-Type |
|------|--------|--------------|
| `/api/v1/leaderboard/now` | 400 | application/json |
| `/api/v1/integrations/ctftime/standings` | 404 | application/json |
| `/api/v1/users/me` | 401 | application/json |
| `/api/v1/challs` | 401 | application/json |

The 401s mean authenticated routes exist and reject anonymous calls. The 400
on `/leaderboard/now` (instead of 200) is because the endpoint expects query
params we didn't send; the JSON-vs-HTML response shape is what proves it's an
API-first SPA backend.

### 3. SPA routing fingerprint

Probed five distinct routes; recorded body size and HTML title:

```
/            size=9140  <title>HCMUS-CTF 2026 Qualification</title>
/admin       size=9140  <title>HCMUS-CTF 2026 Qualification</title>
/setup       size=9140  <title>HCMUS-CTF 2026 Qualification</title>
/teams/new   size=9140  <title>HCMUS-CTF 2026 Qualification</title>
/login       size=9140  <title>HCMUS-CTF 2026 Qualification</title>
```

All five return identical 9140-byte bodies. This is impossible for CTFd
(Flask, server-rendered: `/admin` would 302 to login, `/setup` would be the
install wizard, etc.). It is the signature behaviour of a single-page React
app where the server returns `index.html` for any non-API path and the JS
client routes internally.

### 4. lactf template markers

Inside the page's markdown homepage content:

```
[lactf div class="lactf-hero"]
[lactf div class="lactf-sponsors card"]
[lactf div class="lactf-rules card"]
```

`lactf` = LA CTF, ACM Cyber UCLA. These are custom markdown shortcuts they
added on top of vanilla rCTF for their own layout. HCMUS's instance has
imported LA CTF's template style. The deployment is "rCTF + lactf
customizations", not vanilla rCTF.

### 5. Upstream identity confirmation

`https://api.github.com/repos/redpwn/rctf`:

```
name:        rctf
full_name:   redpwn/rctf
description: redpwn's CTF platform
owner:       redpwn
language:    JavaScript
license:     BSD 3-Clause
```

README opening line:

> rCTF is redpwnCTF's CTF platform. It is developed by the redpwn CTF team.

Notable: the README also says "This version is no longer maintained, please
submit issues and feature requests to otter-sec/rctf." The active maintenance
fork is now `otter-sec/rctf`. HCMUS could be running either; on-wire
fingerprints are identical, so we cannot tell from outside.

## Security posture (clean)

| Check | Result |
|------|--------|
| DNS | 104.21.67.79, 172.67.218.112 - Cloudflare anycast |
| TLS issuer | Google Trust Services WE1 |
| TLS subject | CN=blackpinker.com, SAN *.blackpinker.com |
| TLS validity | 2026-03-27 to 2026-06-25 |
| HSTS | max-age=15552000; includeSubDomains |
| CSP | tight - no inline script, only self + Google reCAPTCHA + Google Analytics + instancer.blackpinker.com |
| X-Frame-Options | SAMEORIGIN |
| X-Content-Type-Options | nosniff |

Nothing in headers, certs, or DNS suggests phishing or hostile takeover. This
is the real qualifier platform.

## The "two different tokens" question

Email's invite URL token:

```
GuGcL5ho7Hyupcrx/hWnn5K1caB1UTKWbGp4eGjwJHuADGJ/5Xe5G6VQkRLlUlWo99/YBNuBJAjdHFd+0/gyDRUe5rsUQoageskL5zAQmcM1uMOcDWAWPyeHhhOy
```

Token visible in Profile -> Team Invite panel after first auth:

```
XafLW1tmU14lmR2ofEf2Nh6DXfEwxl2Zq5vsFkwJvtbm78wazRGfgleavr3TMdPOUW9FTr6u1kgATnyxphDid6uqpESv%2FWiDzOM7tGAnoE8y01R6RruwLhHyFLhm
```

Different bytes. In rCTF this is normal: the team has a `loginToken` that the
platform can rotate. The post-auth Profile panel surfaces the current valid
login token, which may differ from the bootstrap token in the organizer
email. Both tokens point at the same team account.

Operational implication: if the token is rotated mid-event, retrieve the new
one from the Profile panel and update `ACCESS.secret.md`. Do NOT trust the
email's token after rotation.

## The "shared account" surprise

CTFd model (what the repo assumed):

```
team viecz
  +- captain account (Nhân)         pw: xxx
  +- member account (Đức)           pw: xxx
  +- member account (Sang)          pw: xxx
  +- member account (Bảo)           pw: xxx
invite URL = link to add a NEW USER
```

rCTF model (what is actually running):

```
team viecz = ONE shared account
  +- one team token = the password
  +- everyone logs in by clicking the SAME invite URL
  +- no captain, no members, just "team viecz" logged in
invite URL = link that auto-logs the holder into the shared account
```

This explains why the organizer email sent the same URL to all 4 of us: that
IS the team's login. The wording on the Profile page ("Send this team invite
URL to your teammates so they can login") is generic rCTF UI, unaware that
the orgs already mailed the link directly.

## Where these findings landed

- `STRATEGY.md` gained a "Login policy" section and a "Challenge instance
  lifecycle" section.
- `HCMUS-CTF-PATTERNS.md` gained section 1b on platform impact.
- `HCMUS-CTF-2026-RESEARCH.md` section 5 was rewritten with the rCTF-config
  harvest table.
- `CLAUDE.md` Constraints entry now identifies the platform as rCTF.
- `ACCESS.secret.md` (gitignored) holds the team token + invite URL.
- YouTrack `HCTF-3` rewritten for the new login dress-rehearsal flow.
- YouTrack `HCTF-4` rewritten as "build rCTF API helper scripts".
