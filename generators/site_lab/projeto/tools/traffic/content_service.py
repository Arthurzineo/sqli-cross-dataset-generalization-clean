"""Small live content service for the benign traffic generator PoC."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


LOG = logging.getLogger("traffic-content")
PORT = int(os.environ.get("TRAFFIC_CONTENT_PORT", "8765"))
AGENT = os.environ.get("TRAFFIC_AGENT", "codex").lower()
AGENT_HANDLE = os.environ.get("TRAFFIC_AGENT_HANDLE", "")
ORCA_CMD = os.environ.get("ORCA_CMD", "orca")
TIMEOUT_SECONDS = float(os.environ.get("TRAFFIC_AGENT_TIMEOUT", "30"))
PROJECT_ROOT = Path(__file__).resolve().parents[2]
AGENT_IO_ROOT = Path(os.environ.get("TRAFFIC_AGENT_IO_ROOT", str(PROJECT_ROOT / "tools" / "traffic" / "agent_io")))
REQUESTS_DIR = AGENT_IO_ROOT / "requests"
RESPONSES_DIR = AGENT_IO_ROOT / "responses"


def _parse_agents() -> list[tuple[str, str]]:
    raw = os.environ.get("TRAFFIC_AGENTS", "")
    parsed = []
    for entry in raw.split(","):
        if ":" in entry:
            kind, handle = entry.split(":", 1)
            if handle.strip():
                parsed.append((kind.strip().lower() or "agent", handle.strip()))
    if parsed:
        return parsed
    return [(AGENT, AGENT_HANDLE)] if AGENT_HANDLE else []


AGENT_POOL = _parse_agents()
AGENT_LOCKS = {handle: threading.Lock() for _, handle in AGENT_POOL}
POOL_MUTEX = threading.Lock()
POOL_INDEX = 0

FALLBACKS = {
    "comment": "I found the explanation of {topic} useful, especially the note about checking intermediate results.",
    "reply": "For {topic}, I would first isolate the smallest reproducible query and compare its plan with the expected behavior.",
    "searchterm": "{topic}",
    "name": "SQL Explorer",
    "tags": "sql, {topic}, database",
}


def _fallback(kind: str, topic: str, count: int = 1) -> Any:
    """Return a small topic-aware value when the configured agent is unavailable."""
    if kind == "question":
        return {
            "title": f"How should I reason about {topic}?",
            "body": f"I am studying {topic} and would appreciate a concise explanation of the main behavior and common pitfalls.",
        }
    if kind == "answers":
        samples = [
            {"persona": "dba_veteran", "text": f"For {topic}, start with a small reproducible query and inspect its behavior."},
            {"persona": "query_tuner", "text": f"Compare the execution plan for {topic} before and after each change."},
            {"persona": "student", "text": f"I would verify the expected rows for {topic} with a focused test."},
        ]
        return samples[: max(1, count)]
    return FALLBACKS.get(kind, "A short note about {topic}.").format(topic=topic)


def _orca_json(args: list[str]) -> dict[str, Any]:
    """Run one Orca CLI command and decode its JSON response."""
    completed = subprocess.run(
        ["cmd.exe", "/d", "/s", "/c", ORCA_CMD, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "orca command failed")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"invalid Orca JSON: {completed.stdout[:160]}") from error


def _live_orca(prompt: str, request_id: str, handle: str) -> list[dict[str, Any]]:
    """Touch the configured agent and wait for the matching JSON response file."""
    # Clear any text left in the interactive composer before typing a new prompt.
    _orca_json([
        "terminal", "send", "--terminal", handle,
        "--text", ("\b" * 256) + "\x15", "--json",
    ])
    _orca_json([
        "terminal", "send", "--terminal", handle,
        "--text", prompt, "--enter", "--json",
    ])

    response_path = RESPONSES_DIR / f"{request_id}.json"
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(0.5)
        if response_path.exists():
            payload = json.loads(response_path.read_text(encoding="utf-8"))
            if payload.get("id") != request_id or payload.get("status") != "done":
                continue
            items = payload.get("items")
            if isinstance(items, list) and items:
                return items
    raise TimeoutError("agent delimiters not received before timeout")


def _acquire_agent() -> tuple[str, threading.Lock]:
    if not AGENT_POOL:
        raise RuntimeError("TRAFFIC_AGENT_HANDLE is not configured")
    deadline = time.monotonic() + TIMEOUT_SECONDS
    global POOL_INDEX
    while time.monotonic() < deadline:
        with POOL_MUTEX:
            start = POOL_INDEX
            POOL_INDEX = (POOL_INDEX + 1) % len(AGENT_POOL)
            ordered = AGENT_POOL[start:] + AGENT_POOL[:start]
        for kind, handle in ordered:
            lock = AGENT_LOCKS[handle]
            if lock.acquire(blocking=False):
                LOG.info("selected agent=%s handle=%s", kind, handle)
                return handle, lock
        time.sleep(0.05)
    raise TimeoutError("all traffic agents are busy")


def _prompt(request_id: str) -> str:
    return (f"Process request {request_id}: read tools/traffic/agent_io/requests/{request_id}.json, "
            f"follow tools/traffic/agent_io/INSTRUCOES.md, write tools/traffic/agent_io/responses/{request_id}.json, "
            f"then reply only SAVED {request_id}.")


def generate(kind: str, topic: str, count: int = 1) -> tuple[Any, bool]:
    """Invoke the configured agent once and return (content, used_fallback)."""
    try:
        request_id = uuid.uuid4().hex[:12]
        REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
        RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
        request_path = REQUESTS_DIR / f"{request_id}.json"
        request_path.write_text(json.dumps({"id": request_id, "type": kind, "topic": topic, "count": count, "status": "pending"}), encoding="utf-8")
        handle, lock = _acquire_agent()
        try:
            items = _live_orca(_prompt(request_id), request_id, handle)
            LOG.info("request=%s served_by=%s", request_id, handle)
        finally:
            lock.release()
            request_path.unlink(missing_ok=True)
            (RESPONSES_DIR / f"{request_id}.json").unlink(missing_ok=True)
        if kind == "answers":
            return items, False
        item = items[0] if isinstance(items[0], dict) else {"text": str(items[0])}
        if kind == "question":
            if not item.get("title") or not item.get("body"):
                raise RuntimeError("question response missing title/body")
            return {"title": item["title"], "body": item["body"]}, False
        text = str(item.get("text", "")).strip()
        if not text or text.casefold() == "and":
            raise RuntimeError("invalid agent text")
        return text, False
    except (OSError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as error:
        LOG.warning("agent generation failed; using fallback: %s", error)
        return _fallback(kind, topic), True


class ContentHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/gen":
            self._send(404, {"error": "not found"})
            return
        params = parse_qs(parsed.query, keep_blank_values=True)
        kind = params.get("type", ["comment"])[0]
        topic = params.get("topic", [""])[0]
        count = int(params.get("count", ["3" if kind == "answers" else "1"])[0] or 1)
        content, used_fallback = generate(kind, topic, count)
        payload: dict[str, Any] = {"type": kind, "topic": topic}
        if kind == "question":
            payload.update(content if isinstance(content, dict) else {"title": "", "body": content})
        elif kind == "answers":
            payload["items"] = content
        else:
            payload["text"] = content
        if used_fallback:
            payload["fallback"] = True
        self._send(200, payload)

    def _send(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format: str, *args: object) -> None:
        LOG.info("%s - %s", self.address_string(), format % args)


def serve() -> None:
    logging.basicConfig(level=os.environ.get("TRAFFIC_LOG_LEVEL", "INFO"))
    server = ThreadingHTTPServer((os.environ.get("TRAFFIC_CONTENT_HOST", "127.0.0.1"), PORT), ContentHandler)
    LOG.info("content service listening on http://%s:%s (agent=%s)", *server.server_address, AGENT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
