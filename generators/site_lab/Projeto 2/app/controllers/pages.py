"""HTML navigation routes for documentation and the forum."""

from flask import Blueprint, abort, render_template

from app.models.docs import get_doc_by_slug, list_docs
from app.models.posts import list_posts


bp = Blueprint("pages", __name__)


@bp.get("/")
def home():
    """Render the laboratory home page."""
    return render_template("home.html")


@bp.get("/docs")
def docs_list():
    """Render the documentation index."""
    return render_template("docs_list.html", docs=list_docs())


@bp.get("/docs/<slug>")
def doc_page(slug: str):
    """Render one documentation page or return 404 when it is not found."""
    doc = get_doc_by_slug(slug)
    if doc is None:
        abort(404)
    return render_template("doc_page.html", doc=doc)


@bp.get("/forum")
def forum():
    """Render the forum page with its initial post list."""
    return render_template("forum.html", posts=list_posts())
