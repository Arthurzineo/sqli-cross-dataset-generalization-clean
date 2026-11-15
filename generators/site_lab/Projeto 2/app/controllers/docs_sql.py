"""Cooking-wiki pages with meaningful, SQL-adjacent English URLs."""

import re
from html import unescape
from pathlib import Path

from flask import Blueprint, abort, jsonify, render_template, request
from werkzeug.utils import safe_join


bp = Blueprint("cooking_wiki", __name__)
CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content" / "wiki"
ROUTE_SECTIONS = {
    "select": "recipes",
    "where": "ingredients",
    "union": "flavors",
    "sleep": "dough",
    "join": "pairings",
    "group-by": "meal-prep",
    "order-by": "cooking-time",
}
_HEADING_PATTERN = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
_TAG_PATTERN = re.compile(r"<[^>]+>")
SEARCH_RESULT_LIMIT = 50


def _safe_path(relative: str = "") -> Path | None:
    candidate = safe_join(str(CONTENT_ROOT), relative)
    if candidate is None:
        return None
    resolved_root = CONTENT_ROOT.resolve()
    resolved_candidate = Path(candidate).resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError:
        return None
    return resolved_candidate


def _title_from_content(content: str, fallback: str) -> str:
    match = _HEADING_PATTERN.search(content)
    if match is None:
        return fallback.replace("-", " ").title()
    return _TAG_PATTERN.sub("", match.group(1)).strip()


def _body_text(content: str) -> str:
    return " ".join(unescape(_TAG_PATTERN.sub(" ", content)).split())


def _snippet(text: str, match_at: int, query_length: int) -> str:
    start = max(0, match_at - 72)
    end = min(len(text), match_at + query_length + 120)
    return f"{'...' if start else ''}{text[start:end]}{'...' if end < len(text) else ''}"


def _public_url(relative: str, directory: bool = False) -> str:
    clean = relative.strip("/")
    if not clean:
        return "/recipes/"
    parts = clean.split("/")
    term = parts[0]
    section = ROUTE_SECTIONS.get(term)
    if section is None:
        return "/recipes/"
    suffix = "/".join(parts[1:])
    url = f"/{term}/{section}/" + suffix
    if directory and not url.endswith("/"):
        url += "/"
    return url


def _directory_entries(directory: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    categories: list[dict[str, str]] = []
    pages: list[dict[str, str]] = []
    for child in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
        relative = child.relative_to(CONTENT_ROOT).as_posix()
        if child.is_dir() and not child.name.startswith("."):
            label = f"{child.name.replace('-', ' ').upper()} {ROUTE_SECTIONS.get(child.name, 'guides').replace('-', ' ').title()}"
            categories.append({"name": label, "path": relative, "url": _public_url(relative, True)})
        elif child.is_file() and child.suffix == ".html":
            pages.append({"name": child.stem.replace("-", " ").title(), "path": relative[:-5], "url": _public_url(relative[:-5])})
    return categories, pages


def _page_payload(relative_path: str):
    requested = _safe_path(relative_path)
    if requested is None:
        return None
    if requested.is_dir():
        categories, pages = _directory_entries(requested)
        title = "Cooking Wiki" if requested == CONTENT_ROOT.resolve() else requested.name.replace("-", " ").title()
        return {"type": "index", "path": relative_path, "title": title, "categories": categories, "pages": pages}
    document = _safe_path(f"{relative_path}.html")
    if document is None or not document.is_file():
        return None
    content = document.read_text(encoding="utf-8")
    relative = document.relative_to(CONTENT_ROOT).with_suffix("").as_posix()
    return {"type": "page", "path": relative, "url": _public_url(relative), "title": _title_from_content(content, document.stem), "html": content}


@bp.get("/api/wiki/search")
def search_wiki():
    query = request.args.get("q", "")
    needle = query.casefold()
    if not needle:
        return jsonify([])
    results = []
    for document in sorted(CONTENT_ROOT.rglob("*.html"), key=lambda item: item.as_posix()):
        relative = document.relative_to(CONTENT_ROOT).with_suffix("").as_posix()
        content = document.read_text(encoding="utf-8")
        title = _title_from_content(content, document.stem)
        text = _body_text(content)
        match_at = text.casefold().find(needle)
        if match_at < 0:
            match_at = title.casefold().find(needle)
            if match_at < 0:
                continue
            text = title
        results.append({"path": relative, "url": _public_url(relative), "title": title, "snippet": _snippet(text, match_at, len(query))})
        if len(results) >= SEARCH_RESULT_LIMIT:
            break
    return jsonify(results)


@bp.get("/api/wiki/page")
def wiki_data_page():
    payload = _page_payload(request.args.get("path", "").strip("/"))
    return jsonify(payload) if payload is not None else (jsonify({"type": "notfound"}), 404)


def cooking_wiki_page(term: str | None = None, section: str | None = None, subpath: str = ""):
    if term is None:
        relative = ""
    else:
        if ROUTE_SECTIONS.get(term) != section:
            abort(404)
        relative = "/".join(part for part in (term, subpath.strip("/")) if part)
    payload = _page_payload(relative)
    if payload is None:
        abort(404)
    if "text/html" in request.headers.get("Accept", "").lower():
        return render_template("docs_app.html", initial_path=relative)
    if payload["type"] == "index":
        return render_template("doc_sql_index.html", title=payload["title"], categories=payload["categories"], pages=payload["pages"])
    return render_template("doc_sql.html", title=payload["title"], content=payload["html"], path=payload["path"])


bp.add_url_rule("/recipes/", "wiki_index", cooking_wiki_page, defaults={"term": None, "section": None, "subpath": ""})
for _term, _section in ROUTE_SECTIONS.items():
    _endpoint = _term.replace("-", "_")
    bp.add_url_rule(f"/{_term}/{_section}/", f"{_endpoint}_index", cooking_wiki_page, defaults={"term": _term, "section": _section, "subpath": ""})
    bp.add_url_rule(f"/{_term}/{_section}/<path:subpath>", f"{_endpoint}_page", cooking_wiki_page, defaults={"term": _term, "section": _section})
