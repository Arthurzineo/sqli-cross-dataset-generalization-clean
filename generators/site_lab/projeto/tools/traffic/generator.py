"""Small benign Playwright session generator for the traffic PoC."""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("TRAFFIC_BASE_URL", "https://localhost:8443").rstrip("/")
CONTENT_URL = os.environ.get("TRAFFIC_CONTENT_URL", "http://127.0.0.1:8765").rstrip("/")
RUNS_DIR = Path(__file__).resolve().parent / "runs"
PROBABILITIES = {
    "docs": 0.70, "search": 0.50, "forum": 0.80, "open_post": 0.70,
    "comment": 0.40, "reply": 0.25, "new_post": 0.18,
}
TOPICS = ["select", "where", "join", "union", "group-by", "indexes"]


def content(kind: str, topic: str) -> dict:
    """Get one field from the live content service; never hardcode session text."""
    query = urlencode({"type": kind, "topic": topic})
    with urlopen(f"{CONTENT_URL}/gen?{query}", timeout=90) as response:  # noqa: S310 - configured local service
        payload = json.load(response)
    if response.status != 200:
        raise RuntimeError(f"content service returned {response.status}")
    return payload


def pause() -> None:
    """Human-like think time, kept short for the PoC."""
    time.sleep(random.uniform(0.25, 0.8))


def short_author(value: object, fallback: str = "SQL Explorer") -> str:
    """Keep generated author fields to one to three name-like words."""
    words = re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)?", str(value or ""))[:3]
    return " ".join(words) or fallback


def choose_actions() -> dict[str, bool | int]:
    actions = {name: random.random() < weight for name, weight in PROBABILITIES.items()}
    actions["docs_pages"] = random.randint(1, 3)
    actions["posts"] = random.randint(0, 2) if actions["open_post"] else 0
    if not actions["forum"]:
        actions["open_post"] = actions["comment"] = actions["reply"] = actions["new_post"] = False
    if not actions["open_post"]:
        actions["comment"] = actions["reply"] = False
    if not actions["comment"]:
        actions["reply"] = False
    return actions


def plan_sessions(sessions: int) -> dict[str, int]:
    counts = {name: 0 for name in PROBABILITIES}
    counts["read_only"] = 0
    for _ in range(sessions):
        chosen = choose_actions()
        for name in PROBABILITIES:
            counts[name] += int(bool(chosen[name]))
        if not any(chosen[name] for name in ("comment", "reply", "new_post")):
            counts["read_only"] += 1
    return counts


def run_session(browser, session_number: int, manifest: dict) -> None:
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    topic = random.choice(TOPICS)
    chosen = choose_actions()
    try:
        page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
        manifest["actions"].append({"session": session_number, "method": "GET", "url": "/"})
        pause()

        if chosen["docs"]:
            page.goto(f"{BASE_URL}/docs/SQL/postgres/", wait_until="domcontentloaded")
            page.wait_for_selector("#docs-app", timeout=15000)
            manifest["actions"].append({"session": session_number, "method": "GET", "url": "/docs/SQL/postgres/"})
            pause()
            # Follow SPA hierarchy: index -> category -> individual page.
            links = page.locator("#docs-app .docs-app-index a")
            if links.count():
                link = links.nth(random.randrange(links.count()))
                href = link.get_attribute("href") or "/docs/SQL/postgres/"
                link.click(); page.wait_for_timeout(500)
                manifest["actions"].append({"session": session_number, "method": "CLICK", "level": "category", "url": href})
                pause()
            for _ in range(int(chosen["docs_pages"])):
                links = page.locator("#docs-app .docs-app-index a")
                if not links.count():
                    break
                link = links.nth(random.randrange(links.count()))
                href = link.get_attribute("href") or "/docs/SQL/postgres/"
                link.click(); page.wait_for_timeout(500)
                manifest["actions"].append({"session": session_number, "method": "CLICK", "level": "page", "url": href})
                manifest["actions"].append({"session": session_number, "method": "POST", "url": "/graphql", "purpose": "related"})
                pause()

        if chosen["search"] and chosen["docs"]:
            search_term = content("searchterm", topic).get("text", topic)
            page.locator("#docs-app-search-input").fill(search_term)
            page.wait_for_timeout(450)
            manifest["actions"].append({"session": session_number, "method": "GET", "url": "/api/docs/sql/search?q=<generated>"})
            pause()

        if not chosen["forum"]:
            return
        page.goto(f"{BASE_URL}/forum", wait_until="domcontentloaded")
        page.wait_for_selector("#post-list", timeout=15000)
        manifest["actions"].append({"session": session_number, "method": "GET", "url": "/forum"})
        pause()

        page.locator("#post-sort").select_option("title")
        page.wait_for_timeout(350)
        manifest["actions"].append({"session": session_number, "method": "GET", "url": "/api/posts?sort=title&page=1&per_page=10"})
        tag_value = topic if topic in {"select", "where", "join", "union", "group-by"} else "sql"
        tag_button = page.locator(f"#post-tags .post-tag-filter[data-tag='{tag_value}']")
        if tag_button.count():
            tag_button.click()
            page.wait_for_timeout(350)
            manifest["actions"].append({"session": session_number, "method": "GET", "url": f"/api/posts?tag={tag_value}&sort=title&page=1&per_page=10"})

        if not chosen["open_post"] or not page.locator(".post-open").count():
            return
        page.locator(".post-open").first.click()
        page.wait_for_timeout(350)
        author = short_author(content("name", topic).get("text", "SQL Explorer"))
        if chosen["comment"]:
            comment_text = content("comment", topic).get("text", "Thanks for the explanation.")
            page.locator("#comment-author").fill(author)
            page.locator("#comment-body").fill(comment_text)
            page.locator("#comment-form button[type='submit']").click()
            page.wait_for_timeout(450)
            manifest["actions"].append({"session": session_number, "method": "POST", "url": "/api/comments"})

        # A second generated reply exercises the same benign comment flow without attack payloads.
        if chosen["reply"]:
            reply_text = content("reply", topic).get("text", "I would compare the query plan next.")
            page.locator("#comment-body").fill(reply_text)
            page.locator("#comment-form button[type='submit']").click()
            page.wait_for_timeout(350)
            manifest["actions"].append({"session": session_number, "method": "POST", "url": "/api/comments"})

        if chosen["new_post"]:
            question = content("question", topic)
            question_author = short_author(content("name", topic).get("text", author), author)
            tags = content("tags", topic).get("text", f"sql, {topic}")
            page.locator("#new-post-author").fill(question_author)
            page.locator("#new-post-title").fill(question.get("title", f"Question about {topic}"))
            page.locator("#new-post-body").fill(question.get("body", f"I am studying {topic}."))
            page.locator("#new-post-tags").fill(tags)
            page.locator("#new-post-form button[type='submit']").click()
            page.wait_for_timeout(700)
            manifest["actions"].append({"session": session_number, "method": "POST", "url": "/graphql"})
    finally:
        context.close()


def run_isolated_session(session_number: int, manifest: dict) -> None:
    """Give each worker its own sync Playwright fiber and browser instance."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            run_session(browser, session_number, manifest)
        finally:
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one or two benign browser sessions.")
    parser.add_argument("--sessions", type=int, default=int(os.environ.get("TRAFFIC_SESSIONS", "1")))
    parser.add_argument("--concurrency", type=int, default=int(os.environ.get("TRAFFIC_CONCURRENCY", "1")))
    parser.add_argument("--plan", action="store_true", help="simulate action selection without browser or content service")
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)
    if args.plan:
        sessions = max(args.sessions, 1)
        print(json.dumps({"sessions": sessions, "probabilities": PROBABILITIES, "distribution": plan_sessions(sessions)}, indent=2))
        return 0
    sessions = max(args.sessions, 1)
    started = datetime.now(timezone.utc)
    manifest = {
        "label": "benign",
        "started_at": started.isoformat(),
        "base_url": BASE_URL,
        "content_service": CONTENT_URL,
        "sessions": sessions,
        "concurrency": max(1, min(args.concurrency, sessions)),
        "actions": [],
        "errors": [],
    }
    if args.concurrency > 1:
        with ThreadPoolExecutor(max_workers=min(args.concurrency, sessions)) as pool:
            futures = {pool.submit(run_isolated_session, n, manifest): n for n in range(1, sessions + 1)}
            for future in as_completed(futures):
                try:
                    future.result()
                except (PlaywrightTimeoutError, OSError, RuntimeError) as error:
                    manifest["errors"].append({"session": futures[future], "error": str(error)})
    else:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for n in range(1, sessions + 1):
                    try:
                        run_session(browser, n, manifest)
                    except (PlaywrightTimeoutError, OSError, RuntimeError) as error:
                        manifest["errors"].append({"session": n, "error": str(error)})
            finally:
                browser.close()
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    output = RUNS_DIR / f"{started.strftime('%Y%m%dT%H%M%SZ')}.json"
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(output), "sessions": sessions, "actions": len(manifest["actions"]), "errors": manifest["errors"]}, ensure_ascii=False))
    return 0 if not manifest["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
