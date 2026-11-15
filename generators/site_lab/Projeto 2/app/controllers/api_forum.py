"""JSON API routes for forum posts, comments, and tags."""

from flask import Blueprint, jsonify, request

from app.models.posts import (
    create_comment,
    create_post,
    get_post_by_id,
    list_comments_by_post,
    list_posts,
    list_tags,
    search_posts,
)


bp = Blueprint("api_forum", __name__)


def _page_number(value: str | None) -> int:
    """Use the first page when the supplied page cannot be represented as an int."""
    try:
        return int(value) if value is not None else 1
    except ValueError:
        return 1


def _per_page(value: str | None) -> int:
    """Parse a bounded page size without rejecting malformed input."""
    try:
        parsed = int(value) if value is not None else 10
    except (TypeError, ValueError):
        return 10
    return min(max(parsed, 1), 100)


@bp.get("/api/posts")
def posts():
    """Return a paginated JSON list of posts."""
    rows = list_posts(
        tag=request.args.get("tag") or None,
        sort=request.args.get("sort", "recent"),
        page=_page_number(request.args.get("page")),
        per_page=_per_page(request.args.get("per_page")),
    )
    return jsonify([dict(row) for row in rows])


@bp.get("/api/posts/search")
def search():
    """Return posts whose title or body matches the supplied search text."""
    q = request.args.get("q", "")
    return jsonify([dict(row) for row in search_posts(q)])


@bp.get("/api/posts/<post_id>")
def post_detail(post_id: str):
    """Return one post or 404 when its parameterized ID has no match."""
    post = get_post_by_id(post_id)
    if post is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(dict(post))


@bp.get("/api/posts/<post_id>/comments")
def post_comments(post_id: str):
    """Return a post's comments, including each resolved author."""
    return jsonify([dict(row) for row in list_comments_by_post(post_id)])


@bp.post("/api/posts")
def create_post_route():
    """Create a post from the required nested JSON structure."""
    payload = request.get_json(silent=True) or {}
    post = payload.get("post", {}) if isinstance(payload, dict) else {}
    meta = post.get("meta", {}) if isinstance(post, dict) else {}
    tags = meta.get("tags", ()) if isinstance(meta, dict) else ()
    if not isinstance(tags, (list, tuple)):
        tags = (tags,)

    created = create_post(
        title=post.get("title", "") if isinstance(post, dict) else "",
        body=post.get("body", "") if isinstance(post, dict) else "",
        tags=tags,
        author_name=post.get("author") if isinstance(post, dict) else None,
        user_id=None,
    )
    return jsonify(dict(created)), 201


@bp.post("/api/comments")
def create_comment_route():
    """Create a comment with a free-form author and return its JSON representation."""
    created = create_comment(
        post_id=request.form.get("post_id"),
        body=request.form.get("body", ""),
        author_name=request.form.get("author"),
        user_id=None,
    )
    return jsonify(dict(created)), 201


@bp.get("/api/tags")
def tags():
    """Return the complete tag list as JSON."""
    return jsonify([dict(row) for row in list_tags()])
