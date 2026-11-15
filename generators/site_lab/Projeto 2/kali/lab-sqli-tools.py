#!/usr/bin/env python3
"""Plan or run the phase-22 SQLi tools inside the isolated Kali container.

Planning is the default and never sends a request. Execution has two deliberate gates:
``--execute`` and ``LAB_ATTACK_CONFIRM=project2-phase26``. The Docker network is the final boundary;
this program additionally refuses every target except the Compose service ``https://nginx``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from urllib.parse import urlsplit


DEFAULT_WORDLIST = Path("/payloads/wordlists/sqli-ALL-merged-dedup.txt")
DEFAULT_RESULTS = Path("/workspace/runs")
VECTORS = {
    "get-search": {
        "method": "GET",
        "path": "/api/posts/search?q=FUZZ",
        "data": None,
        "content_type": None,
    },
    "get-wiki": {
        "method": "GET",
        "path": "/api/wiki/search?q=FUZZ",
        "data": None,
        "content_type": None,
    },
    "post-login-json": {
        "method": "POST",
        "path": "/api/auth/login",
        "data": '{"username":"FUZZ","password":"project2-phase26"}',
        "content_type": "application/json",
    },
    "post-graphql-json": {
        "method": "POST",
        "path": "/graphql",
        "data": json.dumps(
            {
                "query": "query($q:String!){searchPosts(q:$q){id title}}",
                "variables": {"q": "FUZZ"},
            },
            separators=(",", ":"),
        ),
        "content_type": "application/json",
    },
}


def target_url() -> str:
    target = os.environ.get("TARGET_URL", "")
    parsed = urlsplit(target)
    if parsed.scheme != "https" or parsed.hostname != "nginx" or parsed.port is not None:
        raise ValueError("TARGET_URL deve ser exatamente https://nginx")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username:
        raise ValueError("TARGET_URL nao pode conter path, query, credenciais ou fragmento")
    return "https://nginx"


def injection_marker(value: str) -> str:
    return value.replace("FUZZ", "*")


def output_path(root: Path, tool: str, vector: str, suffix: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return root / f"{stamp}-{tool}-{vector}.{suffix}"


def ffuf_command(args: argparse.Namespace, vector: dict, url: str, output: Path) -> list[str]:
    command = [
        "ffuf", "-noninteractive", "-k", "-w", f"{args.wordlist}:FUZZ",
        "-u", url, "-rate", str(args.rate), "-t", str(args.threads),
        "-timeout", "10", "-maxtime", str(args.max_seconds),
        "-of", "json", "-o", str(output),
    ]
    # Raw corpus entries can contain spaces and other request-line delimiters.  ffuf
    # otherwise writes them verbatim into GET URLs, which Nginx records as malformed
    # requests with an empty method/URI and therefore destroys the payload evidence.
    if vector["method"] == "GET":
        command += ["-enc", "FUZZ:urlencode"]
    if vector["method"] == "POST":
        command += ["-X", "POST", "-H", f"Content-Type: {vector['content_type']}", "-d", vector["data"]]
    return command


def wfuzz_command(args: argparse.Namespace, vector: dict, url: str, output: Path) -> list[str]:
    delay = max(0.0, args.threads / args.rate) if args.rate else 0.0
    command = [
        "wfuzz", "-z", f"file,{args.wordlist}", "-t", str(args.threads),
        "-s", f"{delay:.3f}", "--req-delay", "10", "-f", f"{output},json",
    ]
    if vector["method"] == "POST":
        command += ["-H", f"Content-Type: {vector['content_type']}", "-d", vector["data"]]
    command.append(url)
    return command


def sqlmap_command(args: argparse.Namespace, vector: dict, url: str, output: Path) -> list[str]:
    marked_url = injection_marker(url)
    command = [
        "sqlmap", "-u", marked_url, "--batch", "--disable-coloring",
        "--level=2", "--risk=1", f"--threads={min(args.threads, 4)}",
        "--timeout=10", "--retries=1", f"--delay={1 / args.rate:.3f}",
        f"--output-dir={output}",
    ]
    if vector["method"] == "POST":
        command[2] = url
        command += [f"--data={injection_marker(vector['data'])}", f"--headers=Content-Type: {vector['content_type']}"]
    if args.tamper:
        command.append(f"--tamper={args.tamper}")
    return command


def build_command(args: argparse.Namespace) -> tuple[list[str], Path]:
    target = target_url()
    vector = VECTORS[args.vector]
    url = target + vector["path"]
    suffix = "dir" if args.tool == "sqlmap" else "json"
    output = output_path(args.results_dir, args.tool, args.vector, suffix)
    builders = {"ffuf": ffuf_command, "wfuzz": wfuzz_command, "sqlmap": sqlmap_command}
    return builders[args.tool](args, vector, url, output), output


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("tool", choices=("sqlmap", "ffuf", "wfuzz"))
    result.add_argument("vector", choices=tuple(VECTORS))
    result.add_argument("--wordlist", type=Path, default=DEFAULT_WORDLIST)
    result.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    result.add_argument("--rate", type=int, default=20)
    result.add_argument("--threads", type=int, default=2)
    result.add_argument("--max-seconds", type=int, default=900)
    result.add_argument("--tamper", choices=("space2comment", "randomcase", "space2comment,randomcase"))
    result.add_argument("--execute", action="store_true")
    return result


def validate_args(args: argparse.Namespace) -> None:
    if not 1 <= args.rate <= 100:
        raise ValueError("--rate deve estar entre 1 e 100 req/s")
    if not 1 <= args.threads <= 8:
        raise ValueError("--threads deve estar entre 1 e 8")
    if not 10 <= args.max_seconds <= 7200:
        raise ValueError("--max-seconds deve estar entre 10 e 7200")
    if args.tool != "sqlmap" and args.tamper:
        raise ValueError("--tamper pertence somente ao sqlmap")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        validate_args(args)
        command, output = build_command(args)
    except ValueError as exc:
        parser().error(str(exc))

    plan = {
        "mode": "execute" if args.execute else "plan",
        "tool": args.tool,
        "vector": args.vector,
        "target": "https://nginx",
        "output": str(output),
        "command": command,
        "shell_preview": shlex.join(command),
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not args.execute:
        return 0
    if os.environ.get("LAB_ATTACK_CONFIRM") != "project2-phase26":
        print("execucao recusada: defina LAB_ATTACK_CONFIRM=project2-phase26", file=sys.stderr)
        return 3
    if args.tool in {"ffuf", "wfuzz"} and not args.wordlist.is_file():
        print(f"wordlist inexistente: {args.wordlist}", file=sys.stderr)
        return 4

    args.results_dir.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(command, check=False, timeout=args.max_seconds + 15)
        return_code = completed.returncode
    except subprocess.TimeoutExpired:
        return_code = 124
    manifest = {**plan, "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(), "return_code": return_code}
    manifest_path = args.results_dir / (output.stem + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
