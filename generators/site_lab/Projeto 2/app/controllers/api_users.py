"""JSON API routes for login checks and public user records."""

import hashlib

from flask import Blueprint, jsonify, request

from app.models.users import get_user_by_id, get_user_by_username


bp = Blueprint("api_users", __name__)
_PASSWORD_SALT = "lab-sqli-salt:"


def _credential_value(name: str) -> str:
    """Read a login field from JSON when present, otherwise from form data."""
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload.get(name, "")
    return request.form.get(name, "")


@bp.post("/api/login")
def login():
    """Check supplied credentials without establishing any authentication state."""
    username = _credential_value("username")
    password = _credential_value("password")
    user = get_user_by_username(username)
    password_hash = hashlib.sha256((_PASSWORD_SALT + password).encode("utf-8")).hexdigest()

    if user is None or user["password_hash"] != password_hash:
        return jsonify({"error": "invalid credentials"}), 401

    return jsonify({"id": user["id"], "username": user["username"]})


@bp.get("/api/users/<user_id>")
def user_detail(user_id: str):
    """Return a public user representation or 404 when no ID matches."""
    user = get_user_by_id(user_id)
    if user is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(
        {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "bio": user["bio"],
        }
    )
