# Core Issues

Category: `web`  
Status: `solved`  
Flag: `HCMUS-CTF{Tks_f0r_finding_7h3_c0r3_issu3s_4da8b6ad}`

Source bundle: `https://github.com/nhannht/ctf2/tree/master/submit/CoreIssues`

## Summary

The title was the hint. `Core Issues` meant ASP.NET Core, and the description
“top 3 core issues” was literal: this was a three-bug chain.

The solve path was:

1. use the public Flask webhook as an SSRF into the private ASP.NET Core portal
2. forge the portal cookie to upgrade a moderator session into an admin session
3. abuse the admin-only SDK preview to inject C# into generated source and run
   `/readflag`

This challenge was good because each layer looked complete on its own. The
gateway had a hostname filter, the portal had signed cookies, and the SDK
preview had an allowlist. None of those defenses survived close inspection.

## Artifacts

- Solver: `problems/CoreIssues/solve.py`
- Redirect helper: `problems/CoreIssues/redirect_server.py`
- Public gateway: `gateway/app.py`
- Internal portal: `internal-portal/Program.cs`
- SDK preview sink:
  `internal-portal/Controllers/SdkPreviewController.cs`
- Auth implementation:
  `internal-portal/Services/PortalAuth.cs`
- Final local sink: `internal-portal/readflag.c`

## Key Observation

The gateway, the auth layer, and the SDK preview were all individually flawed,
but they only became valuable when chained together. This was not a
single-endpoint bug. It was an architecture bug across three trust boundaries.

## Early Wrong Model

The wrong way to read this challenge was as a single-bug hunt. Each layer tried
to keep us there:

- the public gateway looked like “just SSRF”
- the portal looked like “just cookie forgery”
- the SDK preview looked like “just code-generation injection”

None of those branches paid off alone. The solve only worked after treating the
service as a three-stage trust chain and carrying each gain into the next one.

## Solve Path

### 1. SSRF into the internal ASP.NET Core portal

The public webhook endpoint was reachable even though the comments said it was
supposed to be internal-only.

The gateway blocklist checked the raw hostname and its percent-decoded form for
strings like `internal`, `portal`, and `localhost`. But the actual outbound
request later normalized the hostname with IDNA. That makes a fullwidth-encoded
hostname useful:

```text
http://%EF%BD%89%EF%BD%8E%EF%BD%94%EF%BD%85%EF%BD%92%EF%BD%8E%EF%BD%81%EF%BD%8C:8080
```

I used a small public `307` redirector so the gateway would preserve the `POST`
body and eventually resolve the destination as plain `internal`.

Proof that the SSRF reached the portal:

```json
{"name":"admin","role":"moderator","department":"Operations"}
```

That response already showed an important quirk: unauthenticated `/api*`
requests got a moderator-flavored session automatically.

### 2. Forge the ASP.NET Core auth cookie

The portal shipped a private `Microsoft.AspNetCore.DataProtection.dll`, and the
modified MAC validation was broken in a very direct way. The comparison buffer
was filled with `hehe` bytes, the computed hash was discarded, and the code
compared the trailer against the constant pattern instead.

So the accepted MAC was:

```text
b"hehe" * 8
```

That left a standard CBC bitflip. The moderator ticket plaintext included:

```text
name=moderator-team-01;admin=false;role=moderator
```

The working forge was:

1. obtain a real moderator cookie through SSRF
2. replace the last 32 bytes with `b"hehe" * 8`
3. flip the previous ciphertext block so `false` becomes `true;`

That produced an admin-capable portal cookie.

### 3. Turn SDK preview into code execution

The final sink was `POST /api/admin/sdk/preview`.

The cleaner code-generation bug was in enum descriptions from `x-ms-enum`.
Those descriptions reached emitted C# source without the cleanup path applied
elsewhere in Kiota. That meant a crafted description could break out of the
generated enum and inject raw C# lines.

The payload did not need a complex initializer. The preview harness constructs:

```csharp
new ApiSdk.Models.CatalogItem()
```

so injecting a partial `CatalogItem` with a field initializer was enough:

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

That executes `/readflag` during object construction. Because the input filter
blocked terms like `System`, `Process`, `flag`, and `static`, the final payload
used `\u` escapes inside identifiers to survive the policy.

### 4. Read the flag from the preview output

The webhook can SSRF the forged admin request into `/api/admin/sdk/preview`,
and the preview response includes `smokeTest.stdout`. That is where the flag
appears.

## Proof

Live success output:

```text
HCMUS-CTF{Tks_f0r_finding_7h3_c0r3_issu3s_4da8b6ad}
preview default sku:
connector SDK preview smoke test passed
```

The shipped solver automates the whole chain:

```bash
uv run python problems/CoreIssues/redirect_server.py
```

Expose that local `127.0.0.1:18080` redirector through a public tunnel, then
run:

```bash
uv run python problems/CoreIssues/solve.py \
  --redirect-url https://<your-tunnel>.lhr.life/
```

The solver prints the flag first, then the full preview JSON containing
`smokeTest.stdout`.

## Files

- `problems/CoreIssues/solve.py`
- `problems/CoreIssues/redirect_server.py`
