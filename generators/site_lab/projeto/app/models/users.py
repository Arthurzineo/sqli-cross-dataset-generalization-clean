"""Parameterized data access for user records."""

import sqlite3

from app.db import query_one


def get_user_by_id(user_id: object) -> sqlite3.Row | None:
    """Return one user selected by a parameterized ID, or ``None``."""
    return query_one(
        "SELECT id, username, email, password_hash, bio FROM users WHERE id = ?",
        (user_id,),
    )


def get_user_by_username(username: str) -> sqlite3.Row | None:
    """Return one user selected by a parameterized username, or ``None``."""
    return query_one(
        "SELECT id, username, email, password_hash, bio FROM users WHERE username = ?",
        (username,),
    )
