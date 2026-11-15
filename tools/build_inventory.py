#!/usr/bin/env python3
"""Build SHA-256 checksums for files tracked by Git."""

from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def repository_inventory() -> None:
    output = ROOT / "provenance/artifact-checksums/repository_files.csv"
    rows = []
    tracked = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    for raw_path in sorted(value for value in tracked if value):
        relative = Path(raw_path.decode("utf-8", errors="surrogateescape"))
        path = ROOT / relative
        if path == output or not path.is_file():
            continue
        rows.append((relative.as_posix(), path.stat().st_size, digest(path)))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["path", "size_bytes", "sha256"])
        writer.writerows(rows)
if __name__ == "__main__":
    repository_inventory()
