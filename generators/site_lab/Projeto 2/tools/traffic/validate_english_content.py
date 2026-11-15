#!/usr/bin/env python3
"""Validate Project 2's persistent content and optional benign JSONL artifact."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PORTUGUESE = {
    "ainda", "assim", "como", "com", "cozinha", "devo", "esta", "está",
    "ingrediente", "ingredientes", "meu", "minha", "não", "onde", "para",
    "pergunta", "posso", "que", "receita", "resposta", "uma", "você",
}
ATTACK_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\bunion\s+(?:all\s+)?select\b",
    r"\b(?:or|and)\s+\d+\s*=\s*\d+\b",
    r"(?:--|/\*|\*/|;\s*(?:drop|select|insert|update|delete)\b)",
    r"%(?:27|22|3b|2d%2d)",
))
TAG = re.compile(r"<[^>]+>")


def validate_text(source: str, value: object, failures: list[str]) -> None:
    text = " ".join(unescape(TAG.sub(" ", str(value or ""))).split())
    words = set(re.findall(r"[a-zà-ÿ]+", text.casefold()))
    found = sorted(words & PORTUGUESE)
    if found:
        failures.append(f"{source}: Portuguese markers {found}")
    if any(pattern.search(text) for pattern in ATTACK_PATTERNS):
        failures.append(f"{source}: attack-like syntax")


def validate_database(db: Path, failures: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    with sqlite3.connect(db) as connection:
        for table, columns in {
            "posts": ("title", "body"),
            "comments": ("body",),
            "docs": ("title", "content"),
        }.items():
            rows = connection.execute(f"SELECT id, {', '.join(columns)} FROM {table}").fetchall()
            counts[table] = len(rows)
            for row in rows:
                for column, value in zip(columns, row[1:]):
                    validate_text(f"{table}[{row[0]}].{column}", value, failures)
    return counts


def validate_pages(failures: list[str]) -> int:
    pages = sorted((ROOT / "app" / "content" / "wiki").rglob("*.html"))
    for page in pages:
        validate_text(str(page.relative_to(ROOT)), page.read_text(encoding="utf-8"), failures)
    return len(pages)


def validate_log(path: Path, failures: list[str]) -> int:
    count = 0
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                failures.append(f"{path}:{line_number}: invalid JSON ({error})")
                continue
            count += 1
            if record.get("label") not in (None, "benign", 0, "0"):
                failures.append(f"{path}:{line_number}: non-benign label")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "db" / "lab.db")
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    failures: list[str] = []
    report: dict[str, object] = {
        "pages": validate_pages(failures),
        "database": validate_database(args.db, failures),
    }
    if args.log:
        report["log_lines"] = validate_log(args.log, failures)
    report["failures"] = failures[:100]
    report["valid"] = not failures
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
