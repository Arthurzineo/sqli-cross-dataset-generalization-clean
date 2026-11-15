#!/usr/bin/env python3
"""Validate and merge the benign/attack JSONL windows with explicit labels."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_line_set(path: Path) -> tuple[set[bytes], int]:
    lines = path.read_bytes().splitlines()
    unique = set(lines)
    return unique, len(lines) - len(unique)


def inspect_jsonl(path: Path) -> tuple[int, Counter[str], Counter[str], int]:
    count = 0
    methods: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    sqli_signals = 0
    indicators = ("%27", "%22", "select", "union", "sleep", "benchmark", "waitfor", " or ", "'", "\"")
    # Nginx preserves request bytes for the detection dataset. The source corpus contains
    # a few non-UTF-8 bytes, so surrogateescape is required to parse the surrounding JSON
    # without silently dropping or replacing evidence.
    with path.open("r", encoding="utf-8", errors="surrogateescape") as source:
        for line_number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON invalido em {path}:{line_number}: {exc}") from exc
            count += 1
            methods[str(row.get("request_method", ""))] += 1
            statuses[str(row.get("status", ""))] += 1
            raw = f"{row.get('request_uri', '')} {row.get('request_body', '')}".lower()
            if any(indicator in raw for indicator in indicators):
                sqli_signals += 1
    return count, methods, statuses, sqli_signals


def merge(benign: Path, attack: Path, output: Path) -> None:
    temporary = output.with_suffix(output.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as destination:
        for source_path, label in ((benign, 0), (attack, 1)):
            with source_path.open("r", encoding="utf-8", errors="surrogateescape") as source:
                for line in source:
                    row = json.loads(line)
                    row["label"] = label
                    # ensure_ascii serializes surrogateescaped request bytes into an
                    # unambiguous valid-UTF-8 JSON representation in the merged dataset.
                    destination.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
    temporary.replace(output)


def validate(benign: Path, attack: Path, output: Path, expected_benign: int, expected_attack: int) -> dict:
    benign_count, benign_methods, benign_statuses, _ = inspect_jsonl(benign)
    attack_count, attack_methods, attack_statuses, attack_signals = inspect_jsonl(attack)
    if benign_count != expected_benign:
        raise ValueError(f"benign esperado={expected_benign}, obtido={benign_count}")
    if attack_count != expected_attack:
        raise ValueError(f"attack esperado={expected_attack}, obtido={attack_count}")
    benign_lines, benign_duplicates = exact_line_set(benign)
    attack_lines, attack_duplicates = exact_line_set(attack)
    overlap = len(benign_lines & attack_lines)
    if benign_duplicates or attack_duplicates:
        raise ValueError(f"duplicatas exatas: benign={benign_duplicates}, attack={attack_duplicates}")
    if overlap:
        raise ValueError(f"sobreposicao exata entre classes: {overlap}")
    invalid_methods = attack_methods - Counter({"GET": attack_methods["GET"], "POST": attack_methods["POST"]})
    if invalid_methods:
        raise ValueError(f"metodos invalidos na janela de ataque: {dict(invalid_methods)}")
    if attack_methods["GET"] + attack_methods["POST"] != attack_count:
        raise ValueError("todas as linhas de ataque devem possuir metodo GET ou POST")
    ratio_get = attack_methods["GET"] / attack_count
    if not 0.47 <= ratio_get <= 0.53:
        raise ValueError(f"proporcao GET fora do limite: {ratio_get:.4f}")
    if attack_signals / attack_count < 0.70:
        raise ValueError("menos de 70% das linhas de ataque contem sinal SQLi reconhecivel")
    merge(benign, attack, output)
    merged_count, merged_methods, merged_statuses, _ = inspect_jsonl(output)
    labels = Counter()
    with output.open("r", encoding="utf-8") as source:
        for line in source:
            labels[str(json.loads(line)["label"])] += 1
    report = {
        "valid": True,
        "benign": {"count": benign_count, "sha256": sha256(benign), "exact_duplicates": benign_duplicates, "methods": dict(benign_methods), "statuses": dict(benign_statuses)},
        "attack": {
            "count": attack_count,
            "sha256": sha256(attack),
            "exact_duplicates": attack_duplicates,
            "methods": dict(attack_methods),
            "statuses": dict(attack_statuses),
            "get_ratio": ratio_get,
            "sqli_signal_ratio": attack_signals / attack_count,
        },
        "dataset": {
            "path": str(output), "count": merged_count, "sha256": sha256(output),
            "labels": dict(labels), "methods": dict(merged_methods), "statuses": dict(merged_statuses),
            "cross_class_exact_overlap": overlap,
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benign", type=Path, required=True)
    parser.add_argument("--attack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--expected-benign", type=int, default=30113)
    parser.add_argument("--expected-attack", type=int, default=30000)
    args = parser.parse_args()
    report = validate(args.benign, args.attack, args.output, args.expected_benign, args.expected_attack)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
