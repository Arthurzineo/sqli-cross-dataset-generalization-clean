"""Small live content service for the benign traffic generator PoC."""

from __future__ import annotations

import json
import logging
import os
import random
import re
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


LOG = logging.getLogger("traffic-content")
PORT = int(os.environ.get("TRAFFIC_CONTENT_PORT", "8877"))
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
    "comment": "That explanation makes this cooking choice much clearer.",
    "reply": "I would test one small batch first and adjust the seasoning after tasting it.",
    "searchterm": "{topic}",
    "name": "Kitchen Neighbor",
    "tags": "cooking, {topic}, recipes",
}

TOPIC_PHRASES = {
    "select": "select the right ingredient",
    "where": "decide where the ingredient belongs",
    "union": "create a union of both flavors",
    "sleep": "let the dough sleep",
    "join": "join the components smoothly",
    "group-by": "group by texture",
    "order-by": "order by cooking time",
}

CURATED_QUESTIONS = {
    "select": [
        ("How should I select apples for pie?", "I need to select apples that stay firm after baking. Which varieties give a balanced sweet and tart pie?"),
        ("Can you help me select herbs for tomato soup?", "I want to select one fresh herb for a sweet tomato soup. Would basil, thyme, or parsley work best?"),
        ("How do you select flour for fresh pasta?", "When you select flour for fresh pasta, what texture tells you that the protein level is suitable?"),
    ],
    "where": [
        ("Where should fresh herbs go in this sauce?", "Where should I add delicate herbs so the sauce keeps their fresh flavor without turning bitter?"),
        ("Where can this dough rest safely?", "My kitchen is warm, so where can covered bread dough rest without fermenting too quickly?"),
        ("Where should I store a baked fruit pie?", "Where should a fruit pie cool and stay overnight so the crust remains crisp and the filling stays safe?"),
    ],
    "union": [
        ("Would a union of these two sauces taste balanced?", "I want a union of roasted pepper sauce and a mild cream sauce. How can I keep both flavors clear?"),
        ("Can a union of grains improve this salad?", "Would a union of barley and quinoa give this salad a pleasant texture, or would the grains compete?"),
        ("How can I make a union of citrus and herbs?", "I am planning a union of lemon, orange, mint, and parsley for fish. Which proportion would taste fresh rather than sharp?"),
    ],
    "sleep": [
        ("Can enriched dough sleep in the refrigerator?", "I need this buttery dough to sleep overnight. How should I cover it so it rises slowly without drying out?"),
        ("How long should cookie dough sleep before baking?", "Should chocolate cookie dough sleep for one hour or overnight if I want a deeper caramel flavor?"),
        ("Where should sourdough sleep tonight?", "My sourdough needs to sleep until morning. Would a cold refrigerator shelf prevent it from overproofing?"),
    ],
    "join": [
        ("When should I join pasta and sauce?", "Should I join the pasta and sauce in the pan before adding cheese so the final dish turns glossy?"),
        ("How do I join soup with fresh bread?", "I want to join a creamy vegetable soup with bread that adds texture without making the meal too heavy."),
        ("Can I join roasted vegetables with this dressing?", "When should I join warm roasted vegetables with a lemon dressing so they absorb flavor but stay crisp?"),
    ],
    "group-by": [
        ("How should I group by texture for a dinner menu?", "I want to group by texture while planning dinner so each course has something crisp, creamy, and tender."),
        ("Can I group by cooking method for meal prep?", "Would it save time to group by cooking method and roast several vegetables while one pot of grains simmers?"),
        ("How do you group by temperature for a picnic?", "I need to group by chilled and room-temperature dishes so the picnic food remains pleasant and safe."),
    ],
    "order-by": [
        ("How should I order by cooking time for dinner?", "I want to order by cooking time so the roast, vegetables, and sauce reach the table together. What starts first?"),
        ("Can I order by heat level in this curry?", "Should I order by heat level and add mild spices before the hotter peppers so I can taste as I cook?"),
        ("How do I order by freshness for a salad?", "I want to order by freshness when preparing a salad. Which ingredients can be cut early and which should wait?"),
    ],
}

NAMES = ["Maya Baker", "Oliver Cook", "Nora Fields", "Theo Green", "Clara Stone", "Sam Rivers"]
SEARCH_TERMS = {
    "select": ["apple pie", "fresh herbs", "pasta flour"],
    "where": ["store herbs", "rest dough", "cool fruit pie"],
    "union": ["fusion sauce", "mixed grain salad", "citrus herbs"],
    "sleep": ["overnight dough", "rest cookie dough", "cold proof"],
    "join": ["pasta sauce", "bread pairing", "roasted vegetables"],
    "group-by": ["meal prep", "menu texture", "picnic dishes"],
    "order-by": ["cooking time", "dinner timing", "salad preparation"],
}

ALLOWED_KINDS = {"question", "answers", "comment", "reply", "searchterm", "name", "tags"}
ALLOWED_TOPICS = set(TOPIC_PHRASES)
TOPIC_WORDS = {"group-by": "group by", "order-by": "order by"}
COOKING_WORDS = {
    "bake", "bread", "cook", "cooking", "dinner", "dough", "flavor", "food",
    "ingredient", "kitchen", "meal", "pasta", "recipe", "sauce", "seasoning",
    "soup", "taste", "texture", "oven", "dish", "batch", "herb", "pie",
}
ENGLISH_MARKERS = {
    "a", "an", "and", "are", "can", "for", "how", "i", "in", "is", "it",
    "my", "of", "should", "that", "the", "this", "to", "what", "where", "with", "would",
}
PORTUGUESE_MARKERS = {
    "como", "com", "cozinha", "de", "devo", "em", "esta", "ingrediente", "meu",
    "minha", "não", "para", "pergunta", "posso", "que", "receita", "uma",
}
ATTACK_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\bunion\s+(?:all\s+)?select\b",
    r"\bselect\b.{0,80}\bfrom\b",
    r"\b(?:or|and)\s+\d+\s*=\s*\d+\b",
    r"(?:--|/\*|\*/|;\s*(?:drop|select|insert|update|delete)\b)",
    r"%(?:27|22|3b|2d%2d)",
))


def _fallback(kind: str, topic: str, count: int = 1) -> Any:
    """Return a small topic-aware value when the configured agent is unavailable."""
    phrase = TOPIC_PHRASES.get(topic, f"work with {topic}")
    if kind == "comment":
        return random.choice([
            f"That explanation helps me {phrase} while keeping the recipe balanced.",
            f"I tried to {phrase} in a small batch, and tasting between steps made the cooking choice clearer.",
            f"This is a practical way to {phrase}; I would also note the texture before changing the seasoning.",
        ])
    if kind == "reply":
        return random.choice([
            f"I would {phrase}, taste one small batch, and adjust the seasoning gradually.",
            f"To {phrase}, keep the first cooking test small and compare the flavor after it rests.",
            f"You can {phrase}, but watch the texture and give each ingredient enough cooking time.",
        ])
    if kind == "question":
        title, body = random.choice(CURATED_QUESTIONS[topic])
        return {"title": title, "body": body}
    if kind == "answers":
        samples = [
            {"persona": "sourdough_sam", "text": f"To {phrase}, try one small batch and note the texture before changing the recipe."},
            {"persona": "sauce_claire", "text": f"I would {phrase}, taste, and add the stronger flavor gradually."},
            {"persona": "student_ana", "text": f"My approach is to {phrase} so every component is ready together."},
        ]
        return samples[: max(1, count)]
    if kind == "name":
        return random.choice(NAMES)
    if kind == "searchterm":
        return random.choice(SEARCH_TERMS[topic])
    if kind == "tags":
        return f"cooking, recipes, {topic}"
    return FALLBACKS.get(kind, "A short cooking note about {topic}.").format(topic=topic)


def _orca_json(args: list[str]) -> dict[str, Any]:
    """Run one Orca CLI command and decode its JSON response."""
    completed = subprocess.run(
        [ORCA_CMD, *args],
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
    return (f"Generate BENIGN ENGLISH COOKING content only. Process request {request_id}: "
            f"read tools/traffic/agent_io/requests/{request_id}.json, "
            f"follow tools/traffic/agent_io/INSTRUCOES.md, write tools/traffic/agent_io/responses/{request_id}.json, "
            f"then reply only SAVED {request_id}.")


def _valid_text(value: object, *, kind: str, topic: str) -> bool:
    text = str(value or "").strip()
    if not text or any(pattern.search(text) for pattern in ATTACK_PATTERNS):
        return False
    if any(ord(char) > 127 for char in text):
        return False
    words = set(re.findall(r"[a-z]+", text.casefold()))
    if words & PORTUGUESE_MARKERS:
        return False
    if kind not in {"name", "tags", "searchterm"}:
        required = TOPIC_WORDS.get(topic, topic)
        if required not in text.casefold() or not (words & COOKING_WORDS):
            return False
        if len(words & ENGLISH_MARKERS) < 2:
            return False
    return True


def _validate_agent_items(kind: str, topic: str, items: object) -> list[dict[str, Any]]:
    if kind not in ALLOWED_KINDS or topic not in ALLOWED_TOPICS:
        raise RuntimeError("unsupported content request")
    if not isinstance(items, list) or not items or not all(isinstance(item, dict) for item in items):
        raise RuntimeError("agent response must contain object items")
    for item in items:
        fields = ("title", "body") if kind == "question" else ("text",)
        if not all(_valid_text(item.get(field), kind=kind, topic=topic) for field in fields):
            raise RuntimeError("agent response violated English cooking-content policy")
    return items


def generate(kind: str, topic: str, count: int = 1) -> tuple[Any, bool]:
    """Invoke the configured agent once and return (content, used_fallback)."""
    request_id = ""
    request_path: Path | None = None
    try:
        request_id = uuid.uuid4().hex[:12]
        REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
        RESPONSES_DIR.mkdir(parents=True, exist_ok=True)
        request_path = REQUESTS_DIR / f"{request_id}.json"
        request_path.write_text(json.dumps({"id": request_id, "type": kind, "topic": topic, "count": count, "status": "pending"}), encoding="utf-8")
        handle, lock = _acquire_agent()
        try:
            items = _validate_agent_items(kind, topic, _live_orca(_prompt(request_id), request_id, handle))
            LOG.info("request=%s served_by=%s", request_id, handle)
        finally:
            lock.release()
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
    finally:
        if request_path is not None:
            request_path.unlink(missing_ok=True)
        if request_id:
            (RESPONSES_DIR / f"{request_id}.json").unlink(missing_ok=True)


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
