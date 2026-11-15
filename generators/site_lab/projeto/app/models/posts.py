"""Parameterized data access for forum posts, comments, and tags."""

from collections.abc import Sequence
from datetime import datetime, timezone
import sqlite3

from app.db import execute, query, query_one


SORT_COLUMNS = {"recent": "created_at", "title": "title", "id": "id"}
DEFAULT_PAGE_SIZE = 10


def list_posts(
    tag: str | None = None,
    sort: str = "recent",
    page: int = 1,
    per_page: int = DEFAULT_PAGE_SIZE,
) -> list[sqlite3.Row]:
    """Return a page of posts, optionally filtered by an exact tag name."""
    column = SORT_COLUMNS.get(sort, "created_at")
    page_number = max(page, 1)
    page_size = max(per_page, 1)
    offset = (page_number - 1) * page_size

    # ``column`` is safe to interpolate because it can only come from SORT_COLUMNS.
    if tag:
        sql = f"""
            SELECT p.id, p.user_id, p.title, p.body, p.created_at, p.author_name,
                   u.username,
                   COALESCE(NULLIF(p.author_name, ''), u.username, 'anonymous') AS author
            FROM posts p
            LEFT JOIN users u ON u.id = p.user_id
            JOIN post_tags ON post_tags.post_id = p.id
            JOIN tags ON tags.id = post_tags.tag_id
            WHERE tags.name = ?
            ORDER BY p.{column} DESC
            LIMIT ? OFFSET ?
        """
        return query(sql, (tag, page_size, offset))

    sql = f"""
        SELECT p.id, p.user_id, p.title, p.body, p.created_at, p.author_name,
               u.username,
               COALESCE(NULLIF(p.author_name, ''), u.username, 'anonymous') AS author
        FROM posts p
        LEFT JOIN users u ON u.id = p.user_id
        ORDER BY p.{column} DESC
        LIMIT ? OFFSET ?
    """
    return query(sql, (page_size, offset))


def get_post_by_id(post_id: object) -> sqlite3.Row | None:
    """Return one post selected by its parameterized ID, or ``None``."""
    return query_one(
        """
        SELECT p.id, p.user_id, p.title, p.body, p.created_at, p.author_name,
               u.username,
               COALESCE(NULLIF(p.author_name, ''), u.username, 'anonymous') AS author
        FROM posts p
        LEFT JOIN users u ON u.id = p.user_id
        WHERE p.id = ?
        """,
        (post_id,),
    )


def search_posts(q: str) -> list[sqlite3.Row]:
    """Search post titles and bodies with a parameterized LIKE pattern."""
    pattern = f"%{q}%"
    return query(
        """
        SELECT p.id, p.user_id, p.title, p.body, p.created_at, p.author_name,
               u.username,
               COALESCE(NULLIF(p.author_name, ''), u.username, 'anonymous') AS author
        FROM posts p
        LEFT JOIN users u ON u.id = p.user_id
        WHERE p.title LIKE ? OR p.body LIKE ?
        ORDER BY p.created_at DESC
        """,
        (pattern, pattern),
    )


def create_post(
    title: str,
    body: str,
    tags: Sequence[str] = (),
    author_name: str | None = None,
    user_id: object | None = None,
    created_at: str | None = None,
) -> sqlite3.Row | None:
    """Insert a post and associate every matching tag, then return the post."""
    timestamp = created_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    post_id = execute(
        """
        INSERT INTO posts (user_id, title, body, created_at, author_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, title, body, timestamp, author_name),
    )

    for tag_name in tags:
        tag = query_one("SELECT id FROM tags WHERE name = ?", (tag_name,))
        if tag is not None:
            execute(
                "INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)",
                (post_id, tag["id"]),
            )

    return get_post_by_id(post_id)


def create_comment(
    post_id: object,
    body: str,
    author_name: str | None = None,
    user_id: object | None = None,
) -> sqlite3.Row | None:
    """Insert a parameterized comment with an optional free-form author."""
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    comment_id = execute(
        """
        INSERT INTO comments (post_id, user_id, body, created_at, author_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (post_id, user_id, body, timestamp, author_name),
    )
    return query_one(
        """
        SELECT c.id, c.post_id, c.user_id, c.body, c.created_at, c.author_name,
               u.username,
               COALESCE(NULLIF(c.author_name, ''), u.username, 'anonymous') AS author
        FROM comments c
        LEFT JOIN users u ON u.id = c.user_id
        WHERE c.id = ?
        """,
        (comment_id,),
    )


def list_comments_by_post(post_id: object) -> list[sqlite3.Row]:
    """Return a post's comments with their authors, ordered by stable comment ID."""
    return query(
        """
        SELECT c.id, c.post_id, c.user_id, c.body, c.created_at, c.author_name,
               u.username,
               COALESCE(NULLIF(c.author_name, ''), u.username, 'anonymous') AS author
        FROM comments c
        LEFT JOIN users u ON u.id = c.user_id
        WHERE c.post_id = ?
        ORDER BY c.id
        """,
        (post_id,),
    )


def list_tags() -> list[sqlite3.Row]:
    """Return all tags ordered by their stable IDs."""
    return query("SELECT id, name FROM tags ORDER BY id")
