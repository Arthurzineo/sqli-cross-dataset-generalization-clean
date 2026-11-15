#!/usr/bin/env python3
"""Build deterministic local SQLi and XSS payload wordlists.

The generator reads only local corpus files and never invokes a security tool.
It keeps every distinct source payload byte-for-byte, fills the required gap
with structural variants only, and writes labels separately from the payloads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path
from typing import Callable, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TARGET = 15_000
DEFAULT_SEED = 1337
MAX_LINE_BYTES = 1_048_576

FORBIDDEN_ENCODING = re.compile(
    rb"%[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|\\x[0-9A-Fa-f]{2}|&(lt|gt|quot|amp|#x?[0-9A-Fa-f]+);",
    re.IGNORECASE,
)
MARKER_PATTERN = re.compile(rb"/\*[a-z]{2,4}-[0-9]{2,}-[a-z0-9]{5,}\*/", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Gera wordlists locais, deterministicas e deduplicadas de SQLi e XSS."
    )
    parser.add_argument("--target", type=int, default=DEFAULT_TARGET, help="Itens unicos por tipo (padrao: 15000).")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Semente para embaralhamento e variantes (padrao: 1337).")
    parser.add_argument("--sqli-source", type=Path, default=REPOSITORY_ROOT / "wordlists/base/sqli-web.txt")
    parser.add_argument("--xss-source", type=Path, default=REPOSITORY_ROOT / "wordlists/base/xss-web.txt")
    parser.add_argument("--sqli-output", type=Path, default=REPOSITORY_ROOT / "wordlists/custom/sqli.txt")
    parser.add_argument("--xss-output", type=Path, default=REPOSITORY_ROOT / "wordlists/custom/xss.txt")
    parser.add_argument("--sqli-synthetic", type=Path, default=REPOSITORY_ROOT / "wordlists/synthetic/sqli-synthetic.txt")
    parser.add_argument("--xss-synthetic", type=Path, default=REPOSITORY_ROOT / "wordlists/synthetic/xss-synthetic.txt")
    parser.add_argument("--labels", type=Path, default=REPOSITORY_ROOT / "wordlists/synthetic/labels.tsv")
    parser.add_argument("--manifest", type=Path, default=REPOSITORY_ROOT / "wordlists/synthetic/manifest.json")
    parser.add_argument("--check", action="store_true", help="Valida somente os arquivos ja gerados.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def split_payload_lines(path: Path) -> list[bytes]:
    """Return nonempty payload records without changing source bytes."""
    if not path.is_file():
        raise ValueError(f"arquivo de origem ausente: {path}")

    result: list[bytes] = []
    for raw_line in path.read_bytes().split(b"\n"):
        if not raw_line:
            continue
        if len(raw_line) > MAX_LINE_BYTES:
            raise ValueError(f"linha maior que {MAX_LINE_BYTES} bytes em {path}")
        result.append(raw_line)
    if not result:
        raise ValueError(f"nenhum payload nao vazio em {path}")
    return result


def unique_in_order(values: Sequence[bytes]) -> list[bytes]:
    seen: set[bytes] = set()
    unique: list[bytes] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique


def write_payload_lines(path: Path, values: Sequence[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\n".join(values) + b"\n")


def write_labels(path: Path, labels: Sequence[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\n".join(labels) + (b"\n" if labels else b""))


def derived_random(seed: int, kind: str, index: int, value: bytes) -> random.Random:
    material = str(seed).encode("ascii") + b"\0" + kind.encode("ascii") + b"\0" + str(index).encode("ascii") + b"\0" + value
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def as_text(value: bytes) -> str:
    return value.decode("utf-8", errors="surrogateescape")


def as_bytes(value: str) -> bytes:
    return value.encode("utf-8", errors="surrogateescape")


def random_case(value: str, rng: random.Random) -> str:
    result: list[str] = []
    for char in value:
        if char.isalpha():
            result.append(char.upper() if rng.randrange(2) else char.lower())
        else:
            result.append(char)
    return "".join(result)


def replace_whitespace(value: str, replacement: str) -> str:
    return re.sub(r"[ \t]+", replacement, value)


def sql_variant(value: bytes, index: int, seed: int) -> tuple[bytes, str]:
    rng = derived_random(seed, "sqli", index, value)
    text = as_text(value)
    family = index % 10

    if family == 0:
        return as_bytes(random_case(text, rng)), "case"
    if family == 1:
        return as_bytes(replace_whitespace(text, "\t")), "tab-whitespace"
    if family == 2:
        return as_bytes(replace_whitespace(text, "/**/")), "comment-whitespace"
    if family == 3:
        prefix = rng.choice(("'", '"', ")", "')", '\")')) * rng.randrange(1, 4)
        return as_bytes(prefix + text), "prefix-context"
    if family == 4:
        suffix = rng.choice(("-- ", "#", "/* */", ")")) * rng.randrange(1, 4)
        return as_bytes(text + suffix), "suffix-context"
    if family == 5:
        left = "(" * rng.randrange(1, 5)
        right = ")" * rng.randrange(1, 5)
        return as_bytes(left + text + right), "parenthesis-wrapper"
    if family == 6:
        prefix = rng.choice(("'", '"', "(", "'("))
        suffix = rng.choice(("'", '"', ")", ")'"))
        return as_bytes(prefix + text + suffix), "quote-wrapper"
    if family == 7:
        spaced = re.sub(r"\s+", lambda _: rng.choice(("\t", "/**/", "  ")), text)
        return as_bytes(spaced), "separator-variation"
    if family == 8:
        left = rng.choice(("'", '"', "(", "(("))
        right = rng.choice(("-- ", "#", ")", "/* */"))
        return as_bytes(left + random_case(text, rng) + right), "case-context"
    wrapped = rng.choice(("(", "'(", '"(', "(("))
    closing = ")" * rng.randrange(1, 4)
    return as_bytes(wrapped + replace_whitespace(random_case(text, rng), "/**/") + closing), "compound-structure"


def xss_variant(value: bytes, index: int, seed: int) -> tuple[bytes, str]:
    rng = derived_random(seed, "xss", index, value)
    text = as_text(value)
    family = index % 10

    if family == 0:
        return as_bytes(random_case(text, rng)), "case"
    if family == 1:
        return as_bytes(replace_whitespace(text, "\t")), "tab-whitespace"
    if family == 2:
        prefix = rng.choice(('">', "'>", "</title>", "</textarea>", "</script>"))
        return as_bytes(prefix + text), "prefix-context"
    if family == 3:
        suffix = rng.choice(("<", ">", "\">", "'>", "/>"))
        return as_bytes(text + suffix), "suffix-context"
    if family == 4:
        left = rng.choice(('"', "'", "<", "</"))
        right = rng.choice(('"', "'", ">", "/>"))
        return as_bytes(left + text + right), "delimiter-wrapper"
    if family == 5:
        prefix = rng.choice(("<!--", "<!----", "<", "</"))
        suffix = rng.choice(("-->", ">", "/>", ""))
        return as_bytes(prefix + text + suffix), "markup-wrapper"
    if family == 6:
        spaced = re.sub(r"\s+", lambda _: rng.choice(("\t", "  ", "/**/")), text)
        return as_bytes(spaced), "separator-variation"
    if family == 7:
        prefix = rng.choice(('">', "'>", "</script>", "</textarea>"))
        suffix = rng.choice(("<", ">", "/>", "<!-- -->"))
        return as_bytes(prefix + random_case(text, rng) + suffix), "case-context"
    if family == 8:
        left = "<" * rng.randrange(1, 4)
        right = ">" * rng.randrange(1, 4)
        return as_bytes(left + text + right), "bracket-wrapper"
    prefix = rng.choice(("</title>", "</textarea>", "</script>", '\">'))
    suffix = rng.choice(("<!-- -->", ">", "/>", ""))
    return as_bytes(prefix + replace_whitespace(random_case(text, rng), "\t") + suffix), "compound-structure"


VariantFunction = Callable[[bytes, int, int], tuple[bytes, str]]


def label_row(kind: str, ordinal: int, family: str, source_index: int, source: bytes) -> bytes:
    source_hash = hashlib.sha256(source).hexdigest()
    return f"{kind}\t{ordinal}\t{family}\t{source_index}\t{source_hash}".encode("ascii")


def build_dataset(source: Sequence[bytes], target: int, seed: int, kind: str, variant: VariantFunction) -> tuple[list[bytes], list[bytes], list[bytes]]:
    if target < len(source):
        raise ValueError(f"target de {kind} ({target}) e menor que o corpus unico de origem ({len(source)})")

    result = list(source)
    synthetic: list[bytes] = []
    labels: list[bytes] = []
    seen = set(result)
    attempt = 0
    maximum_attempts = max((target - len(source)) * 80, 2_000)

    while len(result) < target and attempt < maximum_attempts:
        source_index = attempt % len(source)
        candidate, family = variant(source[source_index], attempt, seed)
        attempt += 1
        if not candidate or len(candidate) > MAX_LINE_BYTES or candidate in seen:
            continue
        if FORBIDDEN_ENCODING.search(candidate) or MARKER_PATTERN.search(candidate):
            continue
        seen.add(candidate)
        result.append(candidate)
        synthetic.append(candidate)
        labels.append(label_row(kind, len(synthetic), family, source_index, source[source_index]))

    if len(result) != target:
        raise RuntimeError(f"nao foi possivel atingir {target} payloads unicos de {kind}")
    return result, synthetic, labels


def shuffle_dataset(values: list[bytes], seed: int, kind: str) -> None:
    random.Random(f"{seed}:{kind}:custom").shuffle(values)


def dataset_details(source_path: Path, output_path: Path, synthetic_path: Path, source_all: Sequence[bytes], source_unique: Sequence[bytes], dataset: Sequence[bytes], synthetic: Sequence[bytes]) -> dict[str, object]:
    return {
        "source": str(source_path),
        "source_sha256": sha256_file(source_path),
        "source_lines": len(source_all),
        "source_unique": len(source_unique),
        "output": str(output_path),
        "output_sha256": sha256_file(output_path),
        "final_unique": len(dataset),
        "synthetic_output": str(synthetic_path),
        "synthetic_sha256": sha256_file(synthetic_path),
        "synthetic_unique": len(synthetic),
    }


def generate(args: argparse.Namespace) -> dict[str, object]:
    if args.target <= 0:
        raise ValueError("--target deve ser maior que zero")

    sqli_source_all = split_payload_lines(args.sqli_source)
    xss_source_all = split_payload_lines(args.xss_source)
    sqli_source = unique_in_order(sqli_source_all)
    xss_source = unique_in_order(xss_source_all)

    sqli_dataset, sqli_synthetic, sqli_labels = build_dataset(sqli_source, args.target, args.seed, "sqli", sql_variant)
    xss_dataset, xss_synthetic, xss_labels = build_dataset(xss_source, args.target, args.seed, "xss", xss_variant)
    shuffle_dataset(sqli_dataset, args.seed, "sqli")
    shuffle_dataset(xss_dataset, args.seed, "xss")

    write_payload_lines(args.sqli_output, sqli_dataset)
    write_payload_lines(args.xss_output, xss_dataset)
    write_payload_lines(args.sqli_synthetic, sqli_synthetic)
    write_payload_lines(args.xss_synthetic, xss_synthetic)
    write_labels(args.labels, sqli_labels + xss_labels)

    manifest = {
        "schema_version": 2,
        "generator": "scripts/generate-payloads.py",
        "seed": args.seed,
        "target_per_type": args.target,
        "labels": str(args.labels),
        "labels_sha256": sha256_file(args.labels),
        "labels_rows": len(sqli_labels) + len(xss_labels),
        "types": {
            "sqli": dataset_details(args.sqli_source, args.sqli_output, args.sqli_synthetic, sqli_source_all, sqli_source, sqli_dataset, sqli_synthetic),
            "xss": dataset_details(args.xss_source, args.xss_output, args.xss_synthetic, xss_source_all, xss_source, xss_dataset, xss_synthetic),
        },
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def validate_dataset(path: Path, target: int, label: str) -> list[bytes]:
    values = split_payload_lines(path)
    if len(values) != target:
        raise ValueError(f"{label}: esperado {target} linhas, encontrado {len(values)}")
    if len(set(values)) != target:
        raise ValueError(f"{label}: linhas duplicadas")
    return values


def validate_synthetic(path: Path, label: str) -> list[bytes]:
    values = split_payload_lines(path)
    if len(values) != len(set(values)):
        raise ValueError(f"{label}: sinteticos duplicados")
    if any(FORBIDDEN_ENCODING.search(value) for value in values):
        raise ValueError(f"{label}: encoding encontrado nos sinteticos")
    if any(MARKER_PATTERN.search(value) for value in values):
        raise ValueError(f"{label}: marcador encontrado nos sinteticos")
    return values


def check(args: argparse.Namespace) -> dict[str, object]:
    if not args.manifest.is_file():
        raise ValueError(f"manifesto ausente: {args.manifest}")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("target_per_type") != args.target or manifest.get("seed") != args.seed:
        raise ValueError("target ou seed do manifesto nao confere")

    sqli_values = validate_dataset(args.sqli_output, args.target, "SQLi")
    xss_values = validate_dataset(args.xss_output, args.target, "XSS")
    sqli_synthetic = validate_synthetic(args.sqli_synthetic, "SQLi")
    xss_synthetic = validate_synthetic(args.xss_synthetic, "XSS")
    labels = [line for line in args.labels.read_bytes().split(b"\n") if line] if args.labels.is_file() else []
    if len(labels) != len(sqli_synthetic) + len(xss_synthetic):
        raise ValueError("labels.tsv nao possui uma linha por sintetico")

    for label, path, source_path, values, synthetic in (
        ("sqli", args.sqli_output, args.sqli_source, sqli_values, sqli_synthetic),
        ("xss", args.xss_output, args.xss_source, xss_values, xss_synthetic),
    ):
        details = manifest.get("types", {}).get(label, {})
        source_all = split_payload_lines(source_path)
        if not set(source_all).issubset(set(values)):
            raise ValueError(f"{label}: corpus de origem nao foi preservado")
        if details.get("source_sha256") != sha256_file(source_path):
            raise ValueError(f"{label}: hash da origem nao confere")
        if details.get("source_lines") != len(source_all):
            raise ValueError(f"{label}: contagem fisica da origem nao confere")
        if details.get("final_unique") != len(values) or details.get("synthetic_unique") != len(synthetic):
            raise ValueError(f"{label}: contagens do manifesto nao conferem")
        if details.get("output_sha256") != sha256_file(path):
            raise ValueError(f"{label}: hash da saida nao confere")

    if manifest.get("labels_rows") != len(labels) or manifest.get("labels_sha256") != sha256_file(args.labels):
        raise ValueError("manifesto de labels nao confere")
    return manifest


def main() -> int:
    args = parse_args()
    try:
        manifest = check(args) if args.check else generate(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    sqli_count = manifest["types"]["sqli"]["final_unique"]
    xss_count = manifest["types"]["xss"]["final_unique"]
    mode = "validado" if args.check else "gerado"
    print(f"{mode}: SQLi={sqli_count} unicos, XSS={xss_count} unicos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
