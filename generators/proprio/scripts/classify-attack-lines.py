#!/usr/bin/env python3
"""Deterministically split four-column request logs into attack and benign TSVs."""

from __future__ import annotations

import argparse
import base64
import binascii
import html
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

SAMPLE_SEED = 20260803
SAMPLE_SIZE = 20

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sqli", re.compile(r"(?:\bunion\s+(?:all\s+)?select\b|(?<![-\w])select(?![-\w])|\b(?:and|or)\s+(?:not\s+)?['\"]?\d+['\"]?\s*=\s*['\"]?\d+|\b\d{3,}\s*=\s*\d{3,}|--(?:\s|&|$)|/\*|\bsleep\s*\(|\bwaitfor\s+delay\b|\bextractvalue\s*\(|\b(?:iif|elt|make_set|benchmark)\s*\(|\border\s+by\b|\bhaving\b|\b(?:boolean\s+mode|regexp_substring|dbms_pipe|randomblob|crypt_key|case\s+when)\b|information_schema|\bchar\s*\(|\bchr\s*\(|\b0x[0-9a-f]{4,}\b)", re.I)),
    # "on[a-z]+=" without \b matched "publicationId=" / "submissionId=", and the
    # bare (java|script|alert|...) alternation matched "description" and
    # "subscriptions". Both are everywhere in legitimate OJS URLs, so the
    # handler now needs a word boundary and the loose alternation is gone —
    # the specific sink/tag/uri branches already cover the real payloads.
    # Handlers go up to ~20 chars ("onanimationiteration"), and the corpus breaks
    # the "javascript" keyword three ways: an escaped TAB inside the word
    # ("javas\tcript:"), a nested duplicate that a naive strip-once filter would
    # rebuild ("javasscriptcript:"), and fullwidth chars (folded by NFKC).
    ("xss", re.compile(r"(?:<\s*(?:script|xss)\b|\bon[a-z]{2,25}\s*=|java.{0,4}script.{0,10}:|<\s*(?:svg|img|details|span|style|iframe|body|input|marquee|object|embed)\b|\b(?:alert|confirm|prompt|eval)\s*[\(`;,]|[=,;]\s*(?:alert|confirm|prompt|eval)\b|%u[0-9a-f]{4}|document\.|window\.|\\u[0-9a-f]{4}|data:text/html)", re.I)),
    ("html-encoded-xss", re.compile(r"(?:&#(?:x[0-9a-f]+|\d+);?\s*){2,}", re.I)),
    ("path-traversal-lfi", re.compile(r"(?:\.\./|/etc/passwd|\.bash_history|wp-config)", re.I)),
    ("command-injection", re.compile(r"(?:;\s*(?:id|whoami)\b|\|\s*whoami\b|`[^`]+`|\$\([^)]*\))", re.I)),
    ("tool-fingerprint", re.compile(r"(?:ffuf_value=|dalfox_waf_probe|dlx[0-9a-f]+.*?xld[0-9a-f]+)", re.I)),
)

COMMON_PARAMETER_NAMES = {
    "page", "lang", "type", "year", "file", "view", "sort", "from", "size", "term",
    "date", "item", "name", "user", "code", "path", "source", "title", "query",
    "search", "limit", "offset", "order", "filter", "issue", "journal", "locale",
}
# sqlmap injects mixed-case 4-letter names (nVGE, EPlM, xsCT). Requiring both
# cases keeps legitimate lowercase params like "verb" and "step" out.
RANDOM_PARAMETER = re.compile(r"(?:^|[?&])((?=[A-Za-z]{4})(?=[a-z]*[A-Z])(?=[A-Z]*[a-z])[A-Za-z]{4})(?:=|&|$)")
STACKED_QUERY = re.compile(r";\s*(?:select|insert|update|delete|declare|exec|drop)\b", re.I)
BASE64_TOKEN = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/])")
NUMERIC_SOURCE = re.compile(r"(?:^|[?&])source=-?\d+(?:&|$)", re.I)


def normalize(value: str) -> str:
    # NFKC folds fullwidth payloads; HTML entities are decoded only in this copy.
    folded = unicodedata.normalize("NFKC", value)
    decoded = unicodedata.normalize("NFKC", html.unescape(folded))
    # The nginx pipeline can turn a literal backslash into a slash in paths;
    # recognize both spellings without changing the original output record.
    # Consume the whole run of separators: the TSV escapes one literal backslash
    # as "\\", so matching a single one would leave a stray "\" mid-word and
    # "al\\u0065rt(1)" would normalize to "al\ert(1)" instead of "alert(1)".
    decoded = re.sub(r"(?:\\+|/+)(u[0-9a-f]{4})", lambda m: chr(int(m.group(1)[1:], 16)), decoded, flags=re.I)
    decoded = re.sub(r"(?:\\+|/+)(x[0-9a-f]{2})", lambda m: chr(int(m.group(1)[1:], 16)), decoded, flags=re.I)
    return unicodedata.normalize("NFKC", html.unescape(decoded)).lower()


def strip_escapes(text: str) -> str:
    """Text with literal \\t \\n \\r removed, for separators planted inside a
    keyword ("javas\\tcript:"). Matched IN ADDITION to the normal form, never
    instead of it: collapsing them merges tokens and breaks \\b anchors, so
    "<svg\\nonload=" would stop matching "<svg\\b"."""
    return re.sub(r"\\+[ntr]", "", text)


METACHAR = re.compile(r"['\"<>()]")


def unbalanced_parameter_quote(text: str) -> bool:
    """Metacharacter probe, not merely an odd quote.

    sqlmap maps injection points with bursts like  '(")(),,((  and  'aBcDeF<'">
    while legitimate form data trips a bare odd-quote test with a single
    apostrophe inside a word. Requiring a cluster separates the two.
    """
    query = text.split("?", 1)[1] if "?" in text else text
    for part in re.split(r"[&;]", query):
        if "=" not in part:
            continue
        value = part.split("=", 1)[1]
        odd = value.count("'") % 2 or value.count('"') % 2
        if not odd:
            continue
        meta = len(METACHAR.findall(value))
        # Density, not raw count: OJS lets editors post rich text, so a long
        # message with <p>/<br> and curly quotes is legitimate, while a probe
        # is short and almost entirely metacharacters.
        if meta >= 3 and len(value) <= 80 and meta / max(len(value), 1) >= 0.15:
            return True
    return False


def encoded_quote_probe(text: str) -> bool:
    """A percent-encoded quote or angle bracket planted in a PATH segment.

    Real navigation never carries %27/%22/%3c in the path; a scanner probing
    for injection does.
    """
    path = text.split("?", 1)[0]
    # Both spellings: the percent-encoded form as logged, and the bare character
    # once the decoding stage has run. Checking only one silently under-counts
    # depending on where in the pipeline the file sits.
    return bool(re.search(r"%(?:27|22|3c|3e|5c)", path, re.I) or re.search(r"['\"<>]", path))


def base64_indicator(text: str) -> bool:
    """Decode candidate parameter tokens, but only accept decoded attack evidence."""
    for match in BASE64_TOKEN.finditer(text):
        candidate = match.group(0)
        for _ in range(3):
            try:
                decoded = base64.b64decode(candidate + "=" * (-len(candidate) % 4), validate=True)
            except (binascii.Error, ValueError):
                break
            decoded_text = decoded.decode("utf-8", "ignore")
            if not decoded_text or not any(pattern.search(normalize(decoded_text)) for _, pattern in PATTERNS):
                candidate = decoded_text
                continue
            return True
    return False


def classify(url: str, body: str) -> tuple[bool, list[str]]:
    raw_text = url + "\n" + ("" if body == "-" else body)
    text = normalize(raw_text)
    unescaped = strip_escapes(text)
    reasons = [name for name, pattern in PATTERNS
               if pattern.search(text) or pattern.search(unescaped)]
    if base64_indicator(url + "\n" + ("" if body == "-" else body)):
        reasons.append("base64_evasion")
    if re.search(r"&#(?:x[0-9a-f]+|\d+);?", raw_text, re.I):
        if "html-encoded-xss" not in reasons:
            reasons.append("html-encoded-xss")
        # A dense run of HTML entities is the preserved encoding of payloads in
        # this corpus, including entities that contain a second URL-encoding pass.
        if "xss" not in reasons:
            reasons.append("xss")
        decoded = html.unescape(text)
        if re.search(r"<\s*(?:script|svg|img)\b|on(?:error|load)\s*=|javascript\s*:", decoded, re.I):
            if "xss" not in reasons:
                reasons.append("xss")
    if STACKED_QUERY.search(text) and "sqli" not in reasons:
        reasons.append("sqli")
    if unbalanced_parameter_quote(text):
        reasons.append("metacharacter-probe")
    # url only: raw_text appends the body, which would be read as the path
    # whenever the URL carries no query string.
    if encoded_quote_probe(url):
        reasons.append("encoded-quote-in-path")
    # raw_text, not text: normalize() lowercases, which would erase the mixed case.
    for match in RANDOM_PARAMETER.finditer(raw_text):
        if match.group(1).lower() not in COMMON_PARAMETER_NAMES:
            reasons.append("sqlmap-random-parameter")
            break
    return bool(reasons), reasons


def sample_line(samples: list[str], seen: int, line: str, rng: random.Random) -> None:
    if len(samples) < SAMPLE_SIZE:
        samples.append(line)
        return
    index = rng.randrange(seen)
    if index < SAMPLE_SIZE:
        samples[index] = line


def markdown_sample(line: str) -> str:
    # Preserve malformed source bytes in TSV output and render them safely here.
    line = line.encode("ascii", "backslashreplace").decode("ascii")
    return line.replace("|", "\\|").replace("\r", "\\r").replace("\n", "\\n")


def process(args: argparse.Namespace) -> tuple[int, int, Counter[str], list[str], list[str], list[str]]:
    total = attacks = 0
    categories: Counter[str] = Counter()
    attack_samples: list[str] = []
    benign_samples: list[str] = []
    benign_all: list[str] = []
    attack_rng = random.Random(SAMPLE_SEED)
    benign_rng = random.Random(SAMPLE_SEED)
    with Path(args.input).open("r", encoding="utf-8", errors="surrogateescape", newline="") as source, \
            Path(args.out_attack).open("w", encoding="utf-8", errors="surrogateescape", newline="") as attack, \
            Path(args.out_benign).open("w", encoding="utf-8", errors="surrogateescape", newline="") as benign:
        header = source.readline()
        if not header:
            raise ValueError("input is empty")
        if header.rstrip("\r\n").split("\t") != ["timestamp", "method", "url", "body"]:
            raise ValueError("input header must be timestamp, method, url, body")
        attack.write(header)
        benign.write(header)
        for line_number, line in enumerate(source, 2):
            raw = line.rstrip("\r\n")
            fields = raw.split("\t")
            if len(fields) != 4:
                raise ValueError(f"line {line_number} does not have exactly 4 TSV fields")
            is_attack, reasons = classify(fields[2], fields[3])
            total += 1
            if is_attack:
                attacks += 1
                attack.write(line)
                for reason in reasons:
                    categories[reason] += 1
                sample_line(attack_samples, attacks, raw, attack_rng)
            else:
                benign.write(line)
                benign_all.append(raw)
                sample_line(benign_samples, total - attacks, raw, benign_rng)
    return total, attacks, categories, attack_samples, benign_samples, benign_all


def write_report(path: str, input_path: str, total: int, attacks: int, categories: Counter[str], attack_samples: list[str], benign_samples: list[str], benign_all: list[str]) -> None:
    benign = total - attacks
    with Path(path).open("w", encoding="utf-8", newline="\n") as report:
        report.write("# Classificação de tráfego\n\n")
        report.write(f"- Entrada: `{input_path}`\n- Semente de amostragem: `{SAMPLE_SEED}`\n")
        report.write(f"- Total de linhas: **{total}**\n- Ataque: **{attacks}**\n- Benignas: **{benign}**\n\n")
        report.write("## Distribuição por indicador\n\n| Indicador | Linhas |\n|---|---:|\n")
        for name, count in sorted(categories.items()):
            report.write(f"| {name} | {count} |\n")
        report.write("\n## Amostras de ataque\n\n")
        for line in attack_samples:
            report.write(f"- `{markdown_sample(line)}`\n")
        report.write("\n## Amostras benignas\n\n")
        for line in benign_samples:
            report.write(f"- `{markdown_sample(line)}`\n")
        numeric = sum(bool(NUMERIC_SOURCE.search(line)) for line in benign_all)
        report.write("\n## Linhas benignas restantes (lista integral)\n\n")
        report.write(f"Total listado: **{len(benign_all)}**.\n\n")
        for line in benign_all:
            report.write(f"- `{markdown_sample(line)}`\n")
        report.write("\n## Caso de fronteira: probes numéricos\n\n")
        report.write(f"Foram mantidas **{numeric}** linhas benignas com `source` puramente numérico; recomenda-se revisão contextual antes de qualquer remoção.\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Split a four-column request TSV into attack and benign files.")
    parser.add_argument("--input", required=True, help="input TSV")
    parser.add_argument("--out-attack", required=True, help="attack output TSV")
    parser.add_argument("--out-benign", required=True, help="benign output TSV")
    parser.add_argument("--report", required=True, help="Markdown report")
    args = parser.parse_args()
    try:
        total, attacks, categories, attack_samples, benign_samples, benign_all = process(args)
        write_report(args.report, args.input, total, attacks, categories, attack_samples, benign_samples, benign_all)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"processed={total} attack={attacks} benign={total - attacks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
