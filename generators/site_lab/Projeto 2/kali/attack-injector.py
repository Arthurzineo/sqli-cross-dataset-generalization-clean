#!/usr/bin/env python3
"""Generate a balanced, bounded SQLi request window against the local lab only."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
import http.client
import json
import os
from pathlib import Path
import random
import ssl
import threading
import time
from urllib.parse import urlencode, urlsplit

from encoder import encode_for_vector, vary


GET_VECTORS = ("get-search", "get-wiki")
# Keep attack traffic read-only with respect to forum content. Login and GraphQL search
# exercise JSON bodies without persisting payloads into posts or comments.
POST_VECTORS = ("post-login-json", "post-graphql-json")
DEFAULT_WORDLIST = Path("/payloads/wordlists/sqli-ALL-merged-dedup.txt")
_thread = threading.local()


@dataclass(frozen=True)
class RequestSpec:
    vector: str
    path: str
    body: bytes | None
    headers: dict[str, str]
    variation: str
    transport: str


def validate_target(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https" or parsed.hostname != "nginx" or parsed.port is not None
        or parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username
    ):
        raise ValueError("TARGET_URL deve ser exatamente https://nginx")
    return "nginx"


def load_payloads(path: Path) -> list[str]:
    # The merged corpus is intentionally byte-diverse and is not valid UTF-8 throughout.
    # Latin-1 provides a lossless byte-to-codepoint mapping; request transports then encode
    # that logical payload explicitly as URL/form UTF-8 or JSON UTF-8.
    payloads = [line.rstrip(b"\r").decode("latin-1") for line in path.read_bytes().split(b"\n")]
    payloads = [payload for payload in payloads if payload]
    if not payloads:
        raise ValueError("wordlist vazia")
    return payloads


def request_spec(vector: str, payload: str, rng: random.Random) -> RequestSpec:
    payload, variation = vary(payload, rng)
    payload, transport = encode_for_vector(payload, vector)
    headers = {"User-Agent": "tcc-attack-injector/1.0", "Accept": "application/json"}
    if vector == "get-search":
        return RequestSpec(vector, "/api/posts/search?" + urlencode({"q": payload}), None, headers, variation, transport)
    if vector == "get-wiki":
        return RequestSpec(vector, "/api/wiki/search?" + urlencode({"q": payload}), None, headers, variation, transport)
    if vector == "post-login-json":
        body = json.dumps({"username": payload, "password": "project2-phase26"}, ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"
        return RequestSpec(vector, "/api/auth/login", body, headers, variation, transport)
    if vector == "post-graphql-json":
        body = json.dumps(
            {
                "query": "query($q:String!){searchPosts(q:$q){id title}}",
                "variables": {"q": payload},
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()
        headers["Content-Type"] = "application/json"
        return RequestSpec(vector, "/graphql", body, headers, variation, transport)
    raise ValueError(f"vetor desconhecido: {vector}")


def connection() -> http.client.HTTPSConnection:
    current = getattr(_thread, "connection", None)
    if current is None:
        context = ssl._create_unverified_context()
        current = http.client.HTTPSConnection("nginx", 443, timeout=15, context=context)
        _thread.connection = current
    return current


def send(spec: RequestSpec) -> tuple[int | None, str | None]:
    method = "GET" if spec.body is None else "POST"
    try:
        conn = connection()
        conn.request(method, spec.path, body=spec.body, headers=spec.headers)
        response = conn.getresponse()
        response.read()
        return response.status, None
    except Exception as exc:  # one failed socket must not poison the whole resumable batch
        conn = getattr(_thread, "connection", None)
        if conn is not None:
            conn.close()
        _thread.connection = None
        return None, type(exc).__name__


def jobs(count: int, payloads: list[str], seed: int, offset: int = 0) -> list[RequestSpec]:
    rng = random.Random(seed)
    methods = ["GET"] * (count // 2) + ["POST"] * (count - count // 2)
    rng.shuffle(methods)
    result = []
    for index, method in enumerate(methods):
        vector = rng.choice(GET_VECTORS if method == "GET" else POST_VECTORS)
        payload = payloads[(offset + index) % len(payloads)]
        result.append(request_spec(vector, payload, rng))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--seed", type=int, default=22)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--rate", type=int, default=100)
    parser.add_argument("--wordlist", type=Path, default=DEFAULT_WORDLIST)
    parser.add_argument("--manifest", type=Path, default=Path("/workspace/attack-injector.manifest.json"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.count <= 100_000:
        parser.error("--count deve estar entre 1 e 100000")
    if not 1 <= args.workers <= 32:
        parser.error("--workers deve estar entre 1 e 32")
    if not 1 <= args.rate <= 500:
        parser.error("--rate deve estar entre 1 e 500")
    try:
        validate_target(os.environ.get("TARGET_URL", ""))
        payloads = load_payloads(args.wordlist)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    planned = jobs(args.count, payloads, args.seed, args.offset)
    vectors = Counter(item.vector for item in planned)
    plan = {
        "mode": "execute" if args.execute else "plan",
        "target": "https://nginx",
        "count": args.count,
        "offset": args.offset,
        "seed": args.seed,
        "workers": args.workers,
        "rate": args.rate,
        "wordlist": str(args.wordlist),
        "wordlist_size": len(payloads),
        "vectors": dict(sorted(vectors.items())),
        "methods": {
            "GET": sum(vectors[name] for name in GET_VECTORS),
            "POST": sum(vectors[name] for name in POST_VECTORS),
        },
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
    if not args.execute:
        return 0
    if os.environ.get("LAB_ATTACK_CONFIRM") != "project2-phase26":
        print("execucao recusada: defina LAB_ATTACK_CONFIRM=project2-phase26", file=os.sys.stderr)
        return 3

    started = datetime.now(timezone.utc)
    statuses: Counter[str] = Counter()
    errors: Counter[str] = Counter()
    variations: Counter[str] = Counter(item.variation for item in planned)
    transports: Counter[str] = Counter(item.transport for item in planned)
    interval = 1 / args.rate
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = []
        next_at = time.monotonic()
        for index, spec in enumerate(planned, 1):
            wait = next_at - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            pending.append(pool.submit(send, spec))
            next_at = max(next_at + interval, time.monotonic())
            if index % 1000 == 0:
                print(f"submitted={index}/{args.count}", flush=True)
        for future in pending:
            status, error = future.result()
            if status is not None:
                statuses[str(status)] += 1
            if error:
                errors[error] += 1

    manifest = {
        **plan,
        "mode": "completed",
        "started_at": started.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "statuses": dict(sorted(statuses.items())),
        "errors": dict(sorted(errors.items())),
        "variations": dict(sorted(variations.items())),
        "transports": dict(sorted(transports.items())),
        "successful_responses": sum(statuses.values()),
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
