"""SQLite access helpers for the laboratory application.

All values received from callers must be passed through ``params``. Never
interpolate user-controlled values into ``sql``; column names are the sole
exception when they come from an explicit allowlist.
"""

import sqlite3
from collections.abc import Sequence

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """Return the SQLite connection associated with the current request."""
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DB_PATH"])
        connection.row_factory = sqlite3.Row
        g.db = connection
    return g.db


def close_db(_error: BaseException | None = None) -> None:
    """Close the current request's SQLite connection, when one was opened."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def query(sql: str, params: Sequence[object] = ()) -> list[sqlite3.Row]:
    """Run a parameterized query and return every matching row."""
    cursor = get_db().execute(sql, params)
    try:
        return cursor.fetchall()
    finally:
        cursor.close()


def query_one(sql: str, params: Sequence[object] = ()) -> sqlite3.Row | None:
    """Run a parameterized query and return its first row, if any."""
    cursor = get_db().execute(sql, params)
    try:
        return cursor.fetchone()
    finally:
        cursor.close()


def execute(sql: str, params: Sequence[object] = ()) -> int:
    """Run a parameterized write, commit it, and return its ``lastrowid``."""
    connection = get_db()
    cursor = connection.execute(sql, params)
    try:
        connection.commit()
        return cursor.lastrowid
    finally:
        cursor.close()


def init_app(app) -> None:
    """Register request-lifecycle handling for SQLite connections."""
    app.teardown_appcontext(close_db)
