#!/usr/bin/env python3
"""Small deterministic SQLi payload variations for dataset diversity.

The source wordlist already contains most SQLi techniques.  These transforms therefore
fill representation gaps instead of manufacturing a combinatorial payload explosion.
Transport encoding belongs to the request vector and is intentionally not done here.
"""

from __future__ import annotations

import random
import re


SQL_KEYWORDS = re.compile(
    r"\b(select|union|where|from|and|or|sleep|benchmark|waitfor|delay|insert|update|delete|drop)\b",
    re.IGNORECASE,
)


def _mixed_case(match: re.Match[str], rng: random.Random) -> str:
    return "".join(char.upper() if rng.random() < 0.5 else char.lower() for char in match.group(0))


def vary(payload: str, rng: random.Random) -> tuple[str, str]:
    """Return one bounded variation and its name without deleting source characters."""
    choice = rng.randrange(10)
    if choice == 0 and " " in payload and "/**/" not in payload:
        return payload.replace(" ", "/**/"), "space_comment"
    if choice == 1 and SQL_KEYWORDS.search(payload):
        return SQL_KEYWORDS.sub(lambda match: _mixed_case(match, rng), payload), "keyword_case"
    if choice == 2 and "=" in payload and " = " not in payload:
        return payload.replace("=", "/**/=/**/", 1), "operator_gap"
    return payload, "identity"


def encode_for_vector(payload: str, vector: str) -> tuple[str, str]:
    """Document the transport contract; request builders perform the actual encoding."""
    if vector.startswith("get-"):
        return payload, "urlencode-query"
    if vector.endswith("-form"):
        return payload, "urlencode-form"
    if vector.endswith("-json"):
        return payload, "json-string"
    raise ValueError(f"vetor desconhecido: {vector}")
