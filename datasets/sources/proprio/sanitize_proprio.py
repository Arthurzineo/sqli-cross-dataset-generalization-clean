#!/usr/bin/env python3
"""Cria cópias conservadoras e não reversíveis da base ``proprio``.

Os arquivos originais nunca são alterados. A sanitização troca valores
potencialmente pessoais, operacionais ou confidenciais por marcadores sintéticos
consistentes entre as vistas RAW e CANONICALIZED. Nenhum mapa que relacione o
valor original ao marcador é persistido.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qsl, unquote_plus, urlencode


ROOT = Path(__file__).resolve().parents[3]
INPUTS = {
    "raw": ROOT / "datasets/restricted/proprio/raw/proprio.tsv",
    "canonicalized": ROOT / "datasets/restricted/proprio/canonicalized/proprio.tsv",
}
OUTPUTS = {
    "raw": ROOT / "datasets/processed/historical/raw/proprio.tsv",
    "canonicalized": ROOT / "datasets/processed/historical/canonicalized/proprio.tsv",
}

EXPECTED_COLUMNS = ["timestamp", "method", "url", "body", "malicioso", "xss", "sqli"]

EMAIL_RE = re.compile(
    r"(?i)(?<![\w.+-])[\w.+-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+"
)
IPV4_RE = re.compile(
    r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)"
)
ORCID_RE = re.compile(r"(?i)\b\d{4}-\d{4}-\d{4}-[\dX]{4}\b")
CPF_RE = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
CNPJ_RE = re.compile(r"(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)")
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?55\s*)?(?:\(?\d{2}\)?[\s.-]*)?9?\d{4}[\s.-]?\d{4}(?!\d)"
)
ABSOLUTE_HOST_RE = re.compile(r"(?i)https?://[^/\s]+")
DOMAIN_RE = re.compile(
    r"(?i)(?<![@\w-])(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|org|net|edu|gov|br|io|dev|info)(?![\w-])"
)
DOI_RE = re.compile(r"(?i)\b10\.\d{4,9}/[-._;()/:a-z0-9]+")
UUID_RE = re.compile(
    r"(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)
PATH_FILE_RE = re.compile(
    r"(?i)(?<![\w.-])([^/\s&=?]+)\.(pdf|docx?|odt|rtf|xls[xm]?|zip|jpg|jpeg|png)\b"
)
SITE_IMAGE_OWNER_RE = re.compile(r"(?i)(/public/site/images/)([^/?#\s]+)")
JOURNAL_DIRECTORY_RE = re.compile(r"(?i)(/public/journals/)(\d+)(/)")
JOURNAL_RE = re.compile(r"(?i)(/index\.php/)([^/?#\s]+)")
SENSITIVE_PATH_ID_RE = re.compile(
    r"(?i)(/(?:users?|reviewers?|authors?|submissions?|reviews?|queries?|"
    r"discussions?|participants?|assignments?|editors?|files?)/)(\d+)"
)
RESUMPTION_RE = re.compile(r"(?i)(resumptionToken\s*[=:]\s*)([^&\s<>]+)")

PLACEHOLDERS = {
    "email": "usuario_{:06d}@example.invalid",
    "name": "Jane Doe",
    "profile": "PERFIL_REMOVIDO_{:06d}",
    "credential": "removida",
    "token": "removido",
    "free_text": "TEXTO_CONFIDENCIAL_REMOVIDO_{:06d}",
    "search_query": "CONSULTAREMOVIDA{:06d}",
    "journal": "REVISTA_{:04d}",
    "identifier": "900{:07d}",
    "filename": "ARQUIVO_{:06d}.dat",
    "phone": "TELEFONE_REMOVIDO_{:06d}",
    "document": "DOCUMENTO_REMOVIDO_{:06d}",
    "orcid": "ORCID_REMOVIDO_{:06d}",
    "data_text": "registro sintetico de teste {:06d}",
    "disable_reason": "desativado para teste editorial {:06d}",
    "new_note": "nota editorial sintetica {:06d}",
    "search_text": "consulta editorial sintetica {:06d}",
    "term_text": "termo academico sintetico {:06d}",
    "source_text": "referencia editorial sintetica {:06d}",
    "interest_text": "interesse academico sintetico {:06d}",
    "tracking": "rastreador sintetico {:06d}",
    "uuid": "00000000-0000-4000-8000-{:012d}",
    "path_owner": "usuario-exemplo-{:06d}",
    "journal_directory": "{:04d}",
}

NAME_KEYS = {
    "name",
    "givenname",
    "familyname",
    "middlename",
    "firstname",
    "lastname",
    "surname",
    "displayname",
    "preferredpublicname",
    "supportname",
}
EMAIL_KEYS = {"email", "e-mail", "mail", "supportemail", "contactemail", "useremail"}
USERNAME_KEYS = {"user", "username", "login", "screenname"}
PASSWORD_KEYS = {"pass", "passwd", "password", "password2", "pwd", "senha"}
TOKEN_KEYS = {
    "token",
    "csrftoken",
    "csrf",
    "csrf_token",
    "accesstoken",
    "access_token",
    "session",
    "sessionid",
    "session_id",
    "cookie",
    "auth",
    "authorization",
    "resumptiontoken",
}
PROFILE_KEYS = {
    "affiliation",
    "institution",
    "organization",
    "mailingaddress",
    "address",
    "address1",
    "address2",
    "city",
    "state",
    "province",
    "postalcode",
    "zipcode",
    "country",
    "phone",
    "telephone",
    "orcid",
    "userurl",
    "biography",
    "signature",
    "emailsignature",
    "supportphone",
    "interests",
}
FILE_KEYS = {"filename", "uploadname", "libraryfilename", "originalfilename"}
TEXT_KEYS = {
    "title",
    "subtitle",
    "abstract",
    "keywords",
    "subject",
    "subjects",
    "comment",
    "comments",
    "commentsprivate",
    "commentstoeditor",
    "personalmessage",
    "message",
    "body",
    "content",
    "coverletter",
    "declinereviewmessage",
    "reviewformresponses",
    "reviewerguidelines",
    "reviewercompetinginterests",
    "notificationreviewercomment",
    "discussion",
}
SEARCH_QUERY_KEYS = {"query", "searchphrase"}

SYNTHETIC_TEXT_KEYS = {
    "data": "data_text",
    "disablereason": "disable_reason",
    "newnote": "new_note",
    "search": "search_text",
    "term": "term_text",
    "source": "source_text",
}
TRACKING_KEYS = {"fbclid", "gclid", "dclid", "msclkid", "_gl", "_ga"}

PLACEHOLDER_LITERALS = {
    "",
    "null",
    "none",
    "false",
    "true",
    "undefined",
    "n/a",
    "na",
    "0",
    "1",
}


def decode_until_stable(value: str, passes: int = 10) -> str:
    current = value
    for _ in range(passes):
        decoded = unquote_plus(current)
        if decoded == current:
            break
        current = decoded
    return current


def base_key(key: str) -> str:
    decoded = decode_until_stable(key).casefold().strip()
    return re.sub(r"\[[^]]*\]", "", decoded)


def key_category(key: str) -> str | None:
    normalized = base_key(key)
    if normalized in NAME_KEYS:
        return "name"
    if normalized in EMAIL_KEYS:
        return "email"
    if normalized in USERNAME_KEYS or normalized in PASSWORD_KEYS:
        return "credential"
    if normalized in TOKEN_KEYS:
        return "token"
    if normalized in SEARCH_QUERY_KEYS:
        return "search_query"
    if normalized in FILE_KEYS or "filename" in normalized:
        return "filename"
    if normalized in PROFILE_KEYS:
        if normalized == "orcid":
            return "orcid"
        if normalized in {"phone", "telephone", "supportphone"}:
            return "phone"
        return "profile"
    if normalized in TEXT_KEYS or re.search(
        r"(?:message|comment|notification|response|discussion|abstract|title|"
        r"biograph|signature|guideline|competinginterest)",
        normalized,
    ):
        return "free_text"
    if re.search(
        r"(?:user|reviewer|author|participant|assignment|submission|editor|"
        r"review|query|discussion|context|file).*id$",
        normalized,
    ):
        return "identifier"
    return None


def form_pairs(url: str, body: str) -> list[tuple[str, str]]:
    query = url.split("?", 1)[1] if "?" in url else ""
    query = re.split(r"\s+HTTP/1\.[01]\s*$", query)[0]
    pairs = parse_qsl(query, keep_blank_values=True, encoding="latin-1", errors="replace")
    pairs.extend(
        parse_qsl(body or "", keep_blank_values=True, encoding="latin-1", errors="replace")
    )
    return [(decode_until_stable(key), decode_until_stable(value)) for key, value in pairs]


class Pseudonymizer:
    def __init__(self) -> None:
        self.maps: dict[str, dict[str, str]] = defaultdict(dict)
        self.occurrences: Counter[str] = Counter()

    def replace(self, category: str, value: str) -> str:
        normalized = decode_until_stable(value).strip().casefold()
        if normalized in PLACEHOLDER_LITERALS and category not in {
            "identifier",
            "journal_directory",
            "tracking",
        }:
            return value
        self.occurrences[category] += 1
        mapping = self.maps[category]
        if normalized not in mapping:
            index = len(mapping) + 1
            if category == "ip":
                octet = ((index - 1) % 254) + 1
                mapping[normalized] = f"192.0.2.{octet}"
            elif category == "doi":
                numeric = int(hashlib.sha256(normalized.encode()).hexdigest()[:15], 16)
                mapping[normalized] = f"10.5555/{numeric % 1_000_000_000_000:012d}"
            elif category == "path_filename":
                mapping[normalized] = f"documento-sintetico-{index:06d}"
            else:
                mapping[normalized] = PLACEHOLDERS[category].format(index)
        return mapping[normalized]


def collect_exact_sensitive_values(paths: dict[str, Path]) -> dict[str, set[str]]:
    collected: dict[str, set[str]] = defaultdict(set)
    for path in paths.values():
        with path.open("r", encoding="latin-1", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            for row in reader:
                for key, value in form_pairs(row["url"], row["body"]):
                    category = key_category(key)
                    decoded = decode_until_stable(value).strip()
                    if (
                        category in {"name", "email", "profile", "credential", "token", "orcid", "phone"}
                        and decoded.casefold() not in PLACEHOLDER_LITERALS
                        and len(decoded) >= 3
                    ):
                        collected[category].add(decoded)
    return collected


def compile_exact_patterns(values: dict[str, set[str]]) -> dict[str, re.Pattern[str]]:
    patterns: dict[str, re.Pattern[str]] = {}
    for category, members in values.items():
        safe = sorted((value for value in members if len(value) >= 4), key=len, reverse=True)
        if safe:
            patterns[category] = re.compile("|".join(re.escape(value) for value in safe), re.I)
    return patterns


def sanitize_inline(
    value: str,
    pseudonyms: Pseudonymizer,
    exact_patterns: dict[str, re.Pattern[str]],
) -> str:
    result = value
    for category, pattern in exact_patterns.items():
        result = pattern.sub(lambda match, cat=category: pseudonyms.replace(cat, match.group(0)), result)
    result = EMAIL_RE.sub(lambda match: pseudonyms.replace("email", match.group(0)), result)
    result = ORCID_RE.sub(lambda match: pseudonyms.replace("orcid", match.group(0)), result)
    result = IPV4_RE.sub(lambda match: pseudonyms.replace("ip", match.group(0)), result)
    result = CNPJ_RE.sub(lambda match: pseudonyms.replace("document", match.group(0)), result)
    result = CPF_RE.sub(lambda match: pseudonyms.replace("document", match.group(0)), result)
    result = PHONE_RE.sub(lambda match: pseudonyms.replace("phone", match.group(0)), result)
    result = DOI_RE.sub(lambda match: pseudonyms.replace("doi", match.group(0)), result)
    result = UUID_RE.sub(lambda match: pseudonyms.replace("uuid", match.group(0)), result)
    result = ABSOLUTE_HOST_RE.sub("https://ojs.example.org", result)
    result = re.sub(r"(?i)\b(?:[a-z0-9-]+\.)*ucs\.br\b", "ojs.example.org", result)
    result = DOMAIN_RE.sub(
        lambda match: (
            match.group(0)
            if match.group(0).casefold() in {"ojs.example.org", "example.invalid", "teste.com.br"}
            else "teste.com.br"
        ),
        result,
    )
    result = JOURNAL_RE.sub(
        lambda match: match.group(1) + pseudonyms.replace("journal", match.group(2)), result
    )
    result = RESUMPTION_RE.sub(
        lambda match: match.group(1) + pseudonyms.replace("token", match.group(2)), result
    )
    result = re.sub(r"(?i)/etc/revistas\b", "/srv/ojs", result)
    result = SITE_IMAGE_OWNER_RE.sub(
        lambda match: match.group(1) + pseudonyms.replace("path_owner", match.group(2)),
        result,
    )
    result = JOURNAL_DIRECTORY_RE.sub(
        lambda match: (
            match.group(1)
            + pseudonyms.replace("journal_directory", match.group(2))
            + match.group(3)
        ),
        result,
    )
    result = PATH_FILE_RE.sub(
        lambda match: (
            pseudonyms.replace("path_filename", match.group(1) + "." + match.group(2))
            + "."
            + match.group(2).casefold()
        ),
        result,
    )
    return result


def sanitize_pair(
    key: str,
    value: str,
    pseudonyms: Pseudonymizer,
    exact_patterns: dict[str, re.Pattern[str]],
    label: int | None = None,
) -> tuple[str, str]:
    normalized_key = base_key(key)
    if normalized_key in {"author", "authors"}:
        return key, pseudonyms.replace("name", decode_until_stable(value))
    if normalized_key == "interests":
        return key, pseudonyms.replace("interest_text", decode_until_stable(value))
    if normalized_key in SYNTHETIC_TEXT_KEYS and not (
        normalized_key == "source" and label == 1
    ):
        return key, pseudonyms.replace(
            SYNTHETIC_TEXT_KEYS[normalized_key], decode_until_stable(value)
        )
    if normalized_key in TRACKING_KEYS:
        return key, pseudonyms.replace("tracking", decode_until_stable(value))
    if label == 0 and re.search(r"(?:id|ids)$", normalized_key):
        return key, pseudonyms.replace("identifier", decode_until_stable(value))
    category = key_category(key)
    decoded = decode_until_stable(value)
    if category:
        return key, pseudonyms.replace(category, decoded)
    if len(decoded) > 160:
        return key, pseudonyms.replace("free_text", decoded)
    return key, sanitize_inline(decoded, pseudonyms, exact_patterns)


def sanitize_path(
    path: str,
    pseudonyms: Pseudonymizer,
    exact_patterns: dict[str, re.Pattern[str]],
) -> str:
    result = sanitize_inline(path, pseudonyms, exact_patterns)
    result = SENSITIVE_PATH_ID_RE.sub(
        lambda match: match.group(1) + pseudonyms.replace("identifier", match.group(2)), result
    )
    return result


def sanitize_url(
    value: str,
    pseudonyms: Pseudonymizer,
    exact_patterns: dict[str, re.Pattern[str]],
    label: int,
) -> str:
    suffix_match = re.search(r"(\s+HTTP/1\.[01]\s*)$", value)
    suffix = suffix_match.group(1) if suffix_match else ""
    core = value[: suffix_match.start()] if suffix_match else value
    if "?" not in core:
        return sanitize_path(core, pseudonyms, exact_patterns) + suffix
    path, query = core.split("?", 1)
    pairs = parse_qsl(query, keep_blank_values=True, encoding="latin-1", errors="replace")
    sanitized = [sanitize_pair(k, v, pseudonyms, exact_patterns, label) for k, v in pairs]
    encoded = urlencode(sanitized, doseq=True, encoding="latin-1", errors="replace")
    return sanitize_path(path, pseudonyms, exact_patterns) + "?" + encoded + suffix


def sanitize_json(
    value: object,
    pseudonyms: Pseudonymizer,
    exact_patterns: dict[str, re.Pattern[str]],
    key: str = "",
    label: int | None = None,
) -> object:
    if isinstance(value, dict):
        return {
            item_key: sanitize_json(
                item_value, pseudonyms, exact_patterns, str(item_key), label
            )
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [sanitize_json(item, pseudonyms, exact_patterns, key, label) for item in value]
    text = "" if value is None else str(value)
    _, sanitized = sanitize_pair(key, text, pseudonyms, exact_patterns, label)
    return sanitized


def sanitize_body(
    value: str,
    label: int,
    pseudonyms: Pseudonymizer,
    exact_patterns: dict[str, re.Pattern[str]],
) -> str:
    if not value:
        return value
    stripped = value.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            parsed = json.loads(value)
            return json.dumps(
                sanitize_json(parsed, pseudonyms, exact_patterns, label=label),
                ensure_ascii=False,
                separators=(",", ":"),
            )
        except json.JSONDecodeError:
            pass

    raw_keys = [decode_until_stable(match) for match in re.findall(r"(?:^|&)([^=&]{1,200})=", value)]
    if label == 0 and (
        len(decode_until_stable(value)) > 160
        or any(key_category(key) == "free_text" for key in raw_keys)
    ):
        return "conteudo=" + pseudonyms.replace("free_text", decode_until_stable(value))

    if "=" in value:
        pairs = parse_qsl(value, keep_blank_values=True, encoding="latin-1", errors="replace")
        sanitized = [sanitize_pair(k, v, pseudonyms, exact_patterns, label) for k, v in pairs]
        return urlencode(sanitized, doseq=True, encoding="latin-1", errors="replace")

    decoded = decode_until_stable(value)
    if label == 0 and re.search(
        r"(?i)(atenciosamente|cordialmente|best regards|meu nome [ée]|prezad[oa]|dear\s)",
        decoded,
    ):
        return pseudonyms.replace("free_text", decoded)
    return sanitize_inline(decoded, pseudonyms, exact_patterns)


def synthetic_timestamp(row_number: int) -> str:
    instant = datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=row_number - 1)
    return instant.strftime("%d/%b/%Y:%H:%M:%S %z")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sanitize_file(
    source: Path,
    destination: Path,
    pseudonyms: Pseudonymizer,
    exact_patterns: dict[str, re.Pattern[str]],
) -> dict[str, object]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    labels: Counter[int] = Counter()
    row_count = 0
    with source.open("r", encoding="latin-1", newline="") as src, destination.open(
        "w", encoding="latin-1", newline=""
    ) as dst:
        reader = csv.DictReader(src, delimiter="\t")
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"Colunas inesperadas em {source}: {reader.fieldnames}")
        writer = csv.DictWriter(
            dst, fieldnames=reader.fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        for row_count, row in enumerate(reader, 1):
            label = int(row["sqli"])
            labels[label] += 1
            row["timestamp"] = synthetic_timestamp(row_count)
            row["url"] = sanitize_url(row["url"], pseudonyms, exact_patterns, label)
            row["body"] = sanitize_body(row["body"], label, pseudonyms, exact_patterns)
            writer.writerow(row)
    return {
        "source": str(source.relative_to(ROOT)),
        "output": str(destination.relative_to(ROOT)),
        "rows": row_count,
        "labels": {str(key): value for key, value in sorted(labels.items())},
        "bytes": destination.stat().st_size,
        "sha256": sha256(destination),
    }


def original_sensitive_strings(paths: dict[str, Path]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for path in paths.values():
        with path.open("r", encoding="latin-1", newline="") as stream:
            for row in csv.DictReader(stream, delimiter="\t"):
                result["timestamp"].add(row["timestamp"])
                decoded = decode_until_stable(row["url"] + " " + row["body"])
                result["email"].update(EMAIL_RE.findall(decoded))
                result["ip"].update(IPV4_RE.findall(decoded))
                result["orcid"].update(ORCID_RE.findall(decoded))
                journal = JOURNAL_RE.search(decoded)
                if journal:
                    result["journal"].add(journal.group(2))
    return result


def verify(
    originals: dict[str, Path],
    outputs: dict[str, Path],
    exact_values: dict[str, set[str]],
    exact_patterns: dict[str, re.Pattern[str]],
) -> dict[str, object]:
    forbidden = original_sensitive_strings(originals)
    failures: list[str] = []
    checks: dict[str, object] = {}

    for representation, path in outputs.items():
        text = path.read_text(encoding="latin-1")
        lowered = text.casefold()
        original_path = originals[representation]

        with original_path.open("r", encoding="latin-1", newline="") as stream:
            original_rows = list(csv.DictReader(stream, delimiter="\t"))
        with path.open("r", encoding="latin-1", newline="") as stream:
            sanitized_rows = list(csv.DictReader(stream, delimiter="\t"))

        original_labels = Counter(row["sqli"] for row in original_rows)
        sanitized_labels = Counter(row["sqli"] for row in sanitized_rows)
        if len(original_rows) != len(sanitized_rows):
            failures.append(f"{representation}: contagem de linhas mudou")
        if original_labels != sanitized_labels:
            failures.append(f"{representation}: distribuição de rótulos mudou")

        leaked_emails = [
            value
            for value in EMAIL_RE.findall(text)
            if not value.casefold().endswith("@example.invalid")
        ]
        if leaked_emails:
            failures.append(f"{representation}: e-mail fora de example.invalid")

        for category, pattern in exact_patterns.items():
            if pattern.search(text):
                failures.append(f"{representation}: valor original remanescente ({category})")

        sanitized_timestamps = {row["timestamp"].casefold() for row in sanitized_rows}
        if sanitized_timestamps & {value.casefold() for value in forbidden["timestamp"]}:
            failures.append(f"{representation}: timestamp original remanescente")

        observed_indicators = {
            "email": {value.casefold() for value in EMAIL_RE.findall(text)},
            "ip": {value.casefold() for value in IPV4_RE.findall(text)},
            "orcid": {value.casefold() for value in ORCID_RE.findall(text)},
        }
        for category, observed in observed_indicators.items():
            original = {value.casefold() for value in forbidden[category]}
            if observed & original:
                failures.append(f"{representation}: indicador original remanescente ({category})")

        original_journals = {value.casefold() for value in forbidden["journal"]}
        leaked_journal_paths = 0
        for row in sanitized_rows:
            match = JOURNAL_RE.search(decode_until_stable(row["url"]))
            if match and match.group(2).casefold() in original_journals:
                leaked_journal_paths += 1
        if leaked_journal_paths:
            failures.append(f"{representation}: identificador de periódico remanescente no caminho")

        if "ucs.br" in lowered:
            failures.append(f"{representation}: domínio institucional remanescente")
        checks[representation] = {
            "rows_original": len(original_rows),
            "rows_sanitized": len(sanitized_rows),
            "labels_original": dict(original_labels),
            "labels_sanitized": dict(sanitized_labels),
            "non_example_email_matches": len(leaked_emails),
            "original_journal_paths": leaked_journal_paths,
        }

    checks["failures"] = sorted(set(failures))
    checks["passed"] = not failures
    return checks


def main() -> None:
    exact_values = collect_exact_sensitive_values(INPUTS)
    exact_patterns = compile_exact_patterns(exact_values)
    pseudonyms = Pseudonymizer()

    manifest = {
        representation: sanitize_file(
            INPUTS[representation], OUTPUTS[representation], pseudonyms, exact_patterns
        )
        for representation in ("raw", "canonicalized")
    }
    verification = verify(INPUTS, OUTPUTS, exact_values, exact_patterns)

    result = {
        "files": manifest,
        "replacement_occurrences": dict(sorted(pseudonyms.occurrences.items())),
        "distinct_replacements": {
            category: len(values) for category, values in sorted(pseudonyms.maps.items())
        },
        "verification": verification,
    }
    report_path = Path(__file__).resolve().parent / "verificacao.json"
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not verification["passed"]:
        raise SystemExit("A verificação encontrou resíduos; consulte verificacao.json")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
