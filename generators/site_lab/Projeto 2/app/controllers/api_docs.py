"""JSON API routes for documentation search."""

from flask import Blueprint, jsonify, request

from app.models.docs import search_docs


bp = Blueprint("api_docs", __name__)


@bp.get("/api/docs/search")
def search():
    """Return documentation records matching the supplied title text."""
    q = request.args.get("q", "")
    return jsonify([dict(doc) for doc in search_docs(q)])
