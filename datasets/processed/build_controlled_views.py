#!/usr/bin/env python3
"""Deriva as duas vistas pareadas usadas pela coleção controlada.

A vista RAW é uma cópia byte a byte da entrada histórica RAW. A vista
CANONICALIZED preserva as mesmas linhas e aplica ``unquote_plus`` até a
convergência (máximo de dez passagens) somente às colunas de URL e corpo,
como no protocolo controlado.
"""

from __future__ import annotations

import csv
import hashlib
import shutil
from pathlib import Path
from urllib.parse import unquote_plus


DATASETS = {
    "artificial.tsv": ("\t", "latin-1", ("url", "body")),
    "artificial_sqli.tsv": ("\t", "latin-1", ("url", "body")),
    "csic.csv": (",", "utf-8", ("URL", "content")),
    "ecml.csv": (",", "utf-8", ("URL", "content")),
    "site_sqli.csv": (",", "utf-8", ("url", "body")),
    "site_cooking.csv": (",", "utf-8", ("url", "body")),
    "srbh.csv": (",", "utf-8", ("URL", "content")),
}


def canonicalize(value: str, passes: int = 10) -> str:
    current = value
    for _ in range(passes):
        decoded = unquote_plus(current)
        if decoded == current:
            break
        current = decoded
    return current


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path, delimiter: str, encoding: str) -> int:
    with path.open("r", encoding=encoding, newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle, delimiter=delimiter))


def write_manifest(root: Path) -> None:
    manifest = root / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ["collection", "representation", "dataset", "file", "rows", "bytes", "sha256"]
        )
        for collection in ("historical", "controlled"):
            for representation in ("raw", "canonicalized"):
                for filename, (delimiter, encoding, _) in DATASETS.items():
                    path = root / collection / representation / filename
                    if not path.is_file():
                        raise FileNotFoundError(path)
                    writer.writerow(
                        [
                            collection,
                            representation,
                            path.stem,
                            path.relative_to(root),
                            row_count(path, delimiter, encoding),
                            path.stat().st_size,
                            sha256(path),
                        ]
                    )


def build(root: Path) -> None:
    historical_raw = root / "historical" / "raw"
    controlled_raw = root / "controlled" / "raw"
    controlled_can = root / "controlled" / "canonicalized"
    controlled_raw.mkdir(parents=True, exist_ok=True)
    controlled_can.mkdir(parents=True, exist_ok=True)

    for filename, (delimiter, encoding, text_columns) in DATASETS.items():
        source = historical_raw / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, controlled_raw / filename)

        destination = controlled_can / filename
        with source.open("r", encoding=encoding, newline="") as src:
            reader = csv.DictReader(src, delimiter=delimiter)
            if reader.fieldnames is None:
                raise ValueError(f"Cabeçalho ausente: {source}")
            missing = set(text_columns) - set(reader.fieldnames)
            if missing:
                raise ValueError(f"Colunas ausentes em {source}: {sorted(missing)}")
            with destination.open("w", encoding=encoding, newline="") as dst:
                writer = csv.DictWriter(
                    dst,
                    fieldnames=reader.fieldnames,
                    delimiter=delimiter,
                    lineterminator="\n",
                )
                writer.writeheader()
                for row in reader:
                    for column in text_columns:
                        row[column] = canonicalize(row[column])
                    writer.writerow(row)

    write_manifest(root)


if __name__ == "__main__":
    build(Path(__file__).resolve().parent)
