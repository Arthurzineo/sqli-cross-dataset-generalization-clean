"""Nested static SQL documentation routes."""

import re
from html import unescape
from pathlib import Path

from flask import Blueprint, abort, jsonify, render_template, request
from werkzeug.utils import safe_join


bp = Blueprint("docs_sql", __name__)
CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content" / "docs" / "SQL"
_HEADING_PATTERN = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)
_TAG_PATTERN = re.compile(r"<[^>]+>")
SEARCH_RESULT_LIMIT = 50


def _safe_path(*parts: str) -> Path | None:
    """Resolve a content path while keeping it inside ``CONTENT_ROOT``."""
    candidate = safe_join(str(CONTENT_ROOT), *parts)
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
    """Use the first h1 in a trusted documentation fragment as its title."""
    match = _HEADING_PATTERN.search(content)
    if match is None:
        return fallback.replace("-", " ").title()
    return _TAG_PATTERN.sub("", match.group(1)).strip()


def _body_text(content: str) -> str:
    """Return readable text from a trusted HTML fragment for literal search."""
    return " ".join(unescape(_TAG_PATTERN.sub(" ", content)).split())


def _snippet(text: str, match_at: int, query_length: int) -> str:
    """Build a compact text-only excerpt around a literal search match."""
    start = max(0, match_at - 72)
    end = min(len(text), match_at + query_length + 120)
    prefix = "..." if start else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}"


def _directory_entries(directory: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """List direct subcategories and HTML pages, excluding repository placeholders."""
    categories: list[dict[str, str]] = []
    pages: list[dict[str, str]] = []
    for child in sorted(directory.iterdir(), key=lambda item: item.name.lower()):
        relative = child.relative_to(CONTENT_ROOT).as_posix()
        if child.is_dir() and not child.name.startswith("."):
            categories.append({"name": child.name, "path": relative})
        elif child.is_file() and child.suffix == ".html":
            pages.append({"name": child.stem.replace("-", " ").title(), "path": relative[:-5]})
    return categories, pages


@bp.get("/api/docs/sql/search")
def search_sql_docs():
    """Search trusted content fragments with a literal, case-insensitive term."""
    query = request.args.get("q", "")
    needle = query.casefold()
    if not needle:
        return jsonify([])

    resolved_root = CONTENT_ROOT.resolve()
    results: list[dict[str, str]] = []
    for document in sorted(CONTENT_ROOT.rglob("*.html"), key=lambda item: item.as_posix()):
        resolved_document = document.resolve()
        try:
            relative_path = resolved_document.relative_to(resolved_root)
        except ValueError:
            continue

        content = resolved_document.read_text(encoding="utf-8")
        title = _title_from_content(content, document.stem)
        text = _body_text(content)
        match_at = text.casefold().find(needle)
        if match_at < 0:
            match_at = title.casefold().find(needle)
            if match_at < 0:
                continue
            text = title

        results.append(
            {
                "path": relative_path.with_suffix("").as_posix(),
                "title": title,
                "snippet": _snippet(text, match_at, len(query)),
            }
        )
        if len(results) >= SEARCH_RESULT_LIMIT:
            break
    return jsonify(results)


@bp.get("/api/docs/sql/page")
def docs_sql_data_page():
    """Return one trusted SQL fragment or directory index as JSON for the SPA."""
    raw_path = request.args.get("path", "")
    relative_path = raw_path.strip("/") or "postgres"
    requested = _safe_path(relative_path)
    if requested is None:
        return jsonify({"type": "notfound"}), 404

    if requested.is_dir():
        categories, pages = _directory_entries(requested)
        return jsonify(
            {
                "type": "index",
                "path": requested.relative_to(CONTENT_ROOT).as_posix(),
                "title": requested.name.replace("-", " ").title(),
                "categories": categories,
                "pages": pages,
            }
        )

    document = _safe_path(f"{relative_path}.html")
    if document is None or not document.is_file():
        return jsonify({"type": "notfound"}), 404

    content = document.read_text(encoding="utf-8")
    return jsonify(
        {
            "type": "page",
            "path": document.relative_to(CONTENT_ROOT).with_suffix("").as_posix(),
            "title": _title_from_content(content, document.stem),
            "html": content,
        }
    )


@bp.get("/docs/SQL/<path:subpath>")
def docs_sql_page(subpath: str):
    """Render a nested SQL fragment or an index for a content directory."""
    requested = _safe_path(subpath)
    if requested is None:
        abort(404)

    # HTML navigations receive the SPA shell; API/XHR callers keep the legacy renderer.
    if "text/html" in request.headers.get("Accept", "").lower():
        initial_path = subpath.strip("/") or "postgres"
        return render_template("docs_app.html", initial_path=initial_path)

    if requested.is_dir():
        categories, pages = _directory_entries(requested)
        return render_template(
            "doc_sql_index.html",
            title=requested.relative_to(CONTENT_ROOT).as_posix(),
            categories=categories,
            pages=pages,
        )

    document = _safe_path(f"{subpath}.html")
    if document is None or not document.is_file():
        abort(404)

    content = document.read_text(encoding="utf-8")
    return render_template(
        "doc_sql.html",
        title=_title_from_content(content, document.stem),
        content=content,
        path=document.relative_to(CONTENT_ROOT).with_suffix("").as_posix(),
    )
