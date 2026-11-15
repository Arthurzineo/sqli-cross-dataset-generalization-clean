"""Parameterized data access for documentation records."""

import sqlite3

from app.db import query, query_one


def list_docs() -> list[sqlite3.Row]:
    """Return every documentation record in stable ID order."""
    return query("SELECT id, slug, title, content FROM docs ORDER BY id")


def get_doc_by_slug(slug: str) -> sqlite3.Row | None:
    """Return one documentation record by parameterized slug, or ``None``."""
    return query_one(
        "SELECT id, slug, title, content FROM docs WHERE slug = ?",
        (slug,),
    )


def search_docs(q: str) -> list[sqlite3.Row]:
    """Return documentation records whose titles match a parameterized pattern."""
    return query(
        "SELECT id, slug, title, content FROM docs WHERE title LIKE ? ORDER BY id",
        (f"%{q}%",),
    )
