#!/usr/bin/env python3
"""Deriva as duas vistas pareadas usadas pela coleção controlada.

A vista RAW é uma cópia byte a byte da entrada histórica RAW. A vista
CANONICALIZED preserva as mesmas linhas e aplica ``unquote_plus`` até a
convergência (máximo de dez passagens) somente às colunas de URL e corpo,
como no protocolo controlado.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path
from urllib.parse import unquote_plus


DATASETS = {
    "artificial_sqli.tsv": ("\t", "latin-1", ("url", "body")),
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


if __name__ == "__main__":
    build(Path(__file__).resolve().parent)
