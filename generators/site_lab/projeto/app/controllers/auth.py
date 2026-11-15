"""Simulated JWT authentication endpoints for laboratory traffic."""

from datetime import datetime, timedelta, timezone
import secrets

import jwt
from flask import Blueprint, current_app, jsonify, request

from app.db import execute, query_one


bp = Blueprint("auth", __name__)

TOKEN_LIFETIME_SECONDS = 900


def _ensure_sessions_table() -> None:
    """Make the persistent session store available for pre-auth lab databases."""
    execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
          id TEXT PRIMARY KEY,
          username TEXT NOT NULL,
          created_at TEXT NOT NULL,
          expires_at TEXT NOT NULL
        )
        """
    )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _username_from_request() -> str:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return str(payload.get("username", ""))
    return request.form.get("username", "")


def _token_from_request() -> str | None:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict) and payload.get("token") is not None:
        return str(payload["token"])

    form_token = request.form.get("token")
    if form_token:
        return form_token

    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization.removeprefix("Bearer ")
    return request.cookies.get("auth_token")


def _create_session(username: str) -> tuple[str, str]:
    _ensure_sessions_table()
    created_at = _now()
    expires_at = created_at + timedelta(seconds=TOKEN_LIFETIME_SECONDS)
    session_id = secrets.token_urlsafe(24)
    execute(
        "INSERT INTO sessions (id, username, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (session_id, username, _timestamp(created_at), _timestamp(expires_at)),
    )
    token = jwt.encode(
        {"sub": username, "sid": session_id, "exp": expires_at},
        current_app.config["JWT_SECRET"],
        algorithm="HS256",
    )
    return session_id, token


def _claims(token: str | None) -> dict | None:
    if not token:
        return None
    try:
        return jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def _session_username(session_id: str | None) -> str | None:
    if not session_id:
        return None
    _ensure_sessions_table()
    session = query_one(
        "SELECT username FROM sessions WHERE id = ? AND expires_at > ?",
        (session_id, _timestamp(_now())),
    )
    return session["username"] if session is not None else None


def _auth_response(username: str, session_id: str, token: str):
    response = jsonify(
        {
            "token": token,
            "token_type": "Bearer",
            "expires_in": TOKEN_LIFETIME_SECONDS,
            "user": {"username": username},
        }
    )
    response.set_cookie(
        "session",
        session_id,
        max_age=TOKEN_LIFETIME_SECONDS,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    response.set_cookie(
        "auth_token",
        token,
        max_age=TOKEN_LIFETIME_SECONDS,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


@bp.post("/api/auth/login")
def login():
    """Create a lab session and signed JWT for any supplied username."""
    username = _username_from_request()
    session_id, token = _create_session(username)
    return _auth_response(username, session_id, token)


@bp.post("/api/auth/refresh")
def refresh():
    """Issue a fresh session and JWT using a token, cookie, or guest fallback."""
    claims = _claims(_token_from_request())
    username = claims.get("sub") if claims else _session_username(request.cookies.get("session"))
    session_id, token = _create_session(str(username or "guest"))
    return _auth_response(str(username or "guest"), session_id, token)


@bp.get("/api/auth/me")
def me():
    """Return the JWT or cookie user, or a guest without rejecting the request."""
    claims = _claims(_token_from_request())
    username = claims.get("sub") if claims else _session_username(request.cookies.get("session"))
    if username is None:
        return jsonify({"user": {"username": "guest"}, "authenticated": False})
    return jsonify({"user": {"username": username}, "authenticated": True})
