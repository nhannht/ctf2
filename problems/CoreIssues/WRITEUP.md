# Core Issues

Flag: `HCMUS-CTF{Tks_f0r_finding_7h3_c0r3_issu3s_4da8b6ad}`

## Hint Reading

The title and description were direct hints:

- `Core Issues` means `ASP.NET Core`, not just “important issues”.
- `Can you list top 3 core issues?` points at a three-bug chain, not one bug.

That matched the shipped source exactly:

1. public Flask gateway
2. private ASP.NET Core portal
3. admin-only SDK preview that generates and runs C#

The intended solve was:

1. reach the internal Core service from the public gateway
2. escalate from moderator to admin
3. turn the SDK preview into code execution and call `/readflag`

## Architecture

The public distribution contains:

- `gateway/app.py`
- `internal-portal/Program.cs`
- `internal-portal/Controllers/SdkPreviewController.cs`
- `internal-portal/Services/PortalAuth.cs`
- `internal-portal/readflag.c`

`docker-compose.yml` wires the public gateway to a private service alias `internal`.

Important facts from source:

- `POST /api/webhooks/test` is exposed publicly even though comments say it should be internal-only.
- The gateway validates the raw hostname before canonicalization, then later applies `unquote(...).encode("idna").decode("ascii")` before connecting.
- The internal portal auto-creates a moderator session for any unauthenticated `/api*` request.
- The admin-only SDK preview accepts attacker-controlled OpenAPI, generates C# with Kiota, then runs `dotnet run`.
- The portal container ships a setuid `/readflag`.

## Bug 1: SSRF Into Internal Portal

The gateway blocklist checks the raw hostname and its percent-decoded form for:

- `internal`
- `portal`
- `localhost`
- `metadata`

But the actual outbound request uses the IDNA-normalized hostname.

So the bypass is:

- send the gateway to a public redirector
- make the redirector return `Location: http://%EF%BD%89...:8080/...`
- let the gateway validate the percent-encoded fullwidth hostname
- let `idna` normalize it to plain `internal`

Working internal host:

- `http://%EF%BD%89%EF%BD%8E%EF%BD%94%EF%BD%85%EF%BD%92%EF%BD%8E%EF%BD%81%EF%BD%8C:8080`

I used a tiny redirect helper that returns a `307` so `POST` bodies survive the redirect.

Live SSRF confirmed access to the portal:

- `/api/me` returned `{"name":"admin","role":"moderator","department":"Operations"}`
- `/api/admin/settings` only returned moderator-visible settings

## Bug 2: DataProtection Cookie Forgery

The portal ships a private `Microsoft.AspNetCore.DataProtection.dll` and actually loads it.

Local decompilation of `ManagedAuthenticatedEncryptor.CalculateAndValidateMac` showed the authentication bug:

- it fills the comparison buffer with `hehehehe...`
- computes a hash over the attacker-controlled trailing bytes
- discards the computed hash
- compares the payload trailer against the constant `hehe` pattern

For the portal’s `AES_256_CBC` + `HMACSHA256` setup, the accepted MAC is:

- `b"hehe" * 8`

That leaves CBC malleability as the remaining step. The session claim contains:

- `name=moderator-team-01;admin=false;role=moderator`

From the local ticket layout, the plaintext offset for `false` is:

- `167`

Payload format from the shipped DLL is:

- `4-byte magic`
- `16-byte key id`
- `16-byte key-modifier/context`
- `16-byte IV`
- `ciphertext`
- `32-byte MAC`

So the previous-block byte sequence that controls plaintext offset `167` starts at:

- `20 + 16 + 167`

The working forge is:

1. start from a real moderator cookie
2. replace the last 32 bytes with `b"hehe" * 8`
3. CBC-bitflip `false` into `true;`

Locally, the forged cookie unlocked full admin settings. The same byte math worked on the live moderator cookie fetched through SSRF.

## Bug 3: Kiota C# Source Injection

The final sink is `POST /api/admin/sdk/preview`.

My first lead was request-builder path injection, which is real but awkward because it lands in multiple C# contexts. The cleaner sink was in the shipped `Kiota.Builder.dll`.

Decompilation showed that almost every description path goes through `CleanupDescription()`, except one:

- enum value descriptions from `x-ms-enum`

`KiotaBuilder.SetEnumOptions()` copies `enumDescription?.Description` directly into `CodeDocumentation.DescriptionTemplate`, and the C# writer later emits it with one `WriteLine(...)`.

That means embedded newlines spill raw C# lines into `Models/<Enum>.cs`.

The generated harness constructs:

- `new ApiSdk.Models.CatalogItem()`

So the easiest execution target is not a module initializer. It is a namespace-scope injected partial class:

```csharp
public partial class CatalogItem {
    public object? P =
        global::System.Diagnostics.Process.Start(
            global::System.Text.Encoding.UTF8.GetString(
                new byte[]{47,114,101,97,100,102,108,97,103}
            )
        );
}
```

That runs during object construction, so the harness itself triggers `/readflag`.

The input policy blocks terms like `System`, `Process`, `flag`, and `static`, so the payload uses `\u` escapes inside identifiers:

- `Syst\u0065m`
- `Di\u0061gnostics`
- `Pro\u0063ess`

To keep the generated enum file compiling, I used three enum values:

1. a normal first enum member
2. an injected description that closes the original enum, adds the partial `CatalogItem`, then opens `#if false`
3. an injected description that emits `#endif` and opens a dummy enum so the remaining generated member and closing brace stay valid

## Live Exploit

Full chain:

1. use webhook SSRF to hit `/api/me`
2. extract the live `.AspNetCore.Portal` moderator cookie from `Set-Cookie`
3. forge it into admin with the `hehe` MAC and CBC bitflip
4. use webhook SSRF again to `POST /api/admin/sdk/preview` with:
   - `Cookie: .AspNetCore.Portal=<forged>`
   - malicious OpenAPI JSON containing the `x-ms-enum` description payload
5. read the flag from `smokeTest.stdout`

Live success output included:

```text
HCMUS-CTF{Tks_f0r_finding_7h3_c0r3_issu3s_4da8b6ad}
preview default sku:
connector SDK preview smoke test passed
```

## Artifacts

- `solve.py` automates the full exploit chain through the public webhook
- `redirect_server.py` is the small helper used for the `307` redirect with the fullwidth internal host

Example:

```bash
uv run python problems/CoreIssues/solve.py \
  --redirect-url https://<your-tunnel>.lhr.life/
```

## Submission

Challenge id:

- `9297eb52-8bb0-4a54-be1f-a1ddb7be0510`

Submission result:

- `goodFlag`
- rank `35`
