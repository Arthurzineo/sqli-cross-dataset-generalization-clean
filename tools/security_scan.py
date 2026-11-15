#!/usr/bin/env python3
"""Conservative pre-push scan that reports locations without printing values."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", "__pycache__", ".venv"}
SECRET_PATTERNS = {
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    "github_token": re.compile(r"(?:ghp|github_pat)_[0-9A-Za-z_]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
SENSITIVE_ASSIGNMENT = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASS|PWD))\s*=\s*(.+?)\s*$",
    re.IGNORECASE,
)
PLACEHOLDERS = {"", "changeme", "replace_me", "example", "placeholder", "none", "null"}


def text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP for part in path.parts):
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def main() -> None:
    exact = []
    assignments = []
    for path, content in text_files():
        relative = path.relative_to(ROOT).as_posix()
        for name, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(content):
                exact.append((name, relative, content.count("\n", 0, match.start()) + 1))
        if path.name == ".env" or path.suffix in {".env", ".example"}:
            for number, line in enumerate(content.splitlines(), 1):
                match = SENSITIVE_ASSIGNMENT.match(line)
                if not match:
                    continue
                value = match.group(2).strip().strip("'\"").lower()
                if value not in PLACEHOLDERS and not value.startswith("${"):
                    assignments.append((match.group(1), relative, number))

    large = [
        (path.relative_to(ROOT).as_posix(), path.stat().st_size)
        for path in ROOT.rglob("*")
        if path.is_file() and path.stat().st_size > 100_000_000
    ]
    restricted_files = [
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "datasets/restricted/proprio").rglob("*")
        if path.is_file() and path.name != "README.md"
    ]
    lines = [
        "# Varredura de segurança da Fase 2\n\n",
        f"- `gitleaks` disponível: **{bool(shutil.which('gitleaks'))}**.\n",
        f"- `trufflehog` disponível: **{bool(shutil.which('trufflehog'))}**.\n",
        f"- Correspondências de formatos fortes de segredo: **{len(exact)}**.\n",
        f"- Atribuições sensíveis não vazias em arquivos `.env`/exemplo: **{len(assignments)}**.\n",
        f"- Arquivos acima de 100 MB: **{len(large)}**.\n",
        f"- Arquivos de dados em `datasets/restricted/proprio/`: **{len(restricted_files)}**.\n",
    ]
    if exact:
        lines.append("\n## Formatos fortes encontrados\n")
        lines.extend(f"- {kind}: `{path}:{line}`\n" for kind, path, line in exact)
    if assignments:
        lines.append("\n## Atribuições sensíveis encontradas\n")
        lines.extend(f"- {name}: `{path}:{line}`\n" for name, path, line in assignments)
    if large:
        lines.append("\n## Arquivos acima de 100 MB\n")
        lines.extend(f"- `{path}` ({size} bytes)\n" for path, size in large)
    lines.append(
        "\nA busca genérica por palavras como `token` e `password` produz falsos "
        "positivos em código, documentação e payloads; por isso, este relatório "
        "separa formatos fortes e atribuições de ambiente não vazias. Uma nova "
        "varredura deve ser executada imediatamente antes do envio.\n"
    )
    (ROOT / "docs/SECURITY_SCAN_PHASE2.md").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

