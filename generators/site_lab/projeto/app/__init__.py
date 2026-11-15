"""Flask application factory and controller wiring."""

from importlib import import_module

from flask import Blueprint, Flask, jsonify

from . import db


_BLUEPRINT_MODULES = (
    "app.controllers.pages",
    "app.controllers.api_docs",
    "app.controllers.api_forum",
    "app.controllers.api_users",
    "app.controllers.auth",
    "app.controllers.docs_sql",
)


def _register_controller_blueprints(app: Flask) -> set[str]:
    """Register controller ``bp`` objects that have been implemented so far."""
    registered: set[str] = set()
    for module_name in _BLUEPRINT_MODULES:
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name:
                continue
            raise

        blueprint = getattr(module, "bp", None)
        if blueprint is not None:
            app.register_blueprint(blueprint)
            registered.add(module_name)
    return registered


def _register_placeholder_routes(app: Flask, pages_registered: bool, graphql_registered: bool) -> None:
    """Provide minimal routes until controller and GraphQL phases replace them."""
    placeholder = Blueprint("foundation_placeholder", __name__)

    if not pages_registered:
        @placeholder.get("/docs")
        def docs_placeholder():
            return "<h1>Documentation is being prepared.</h1>"

        @placeholder.get("/forum")
        def forum_placeholder():
            return "<h1>Forum is being prepared.</h1>"

    if not graphql_registered:
        @placeholder.route("/graphql", methods=["GET", "POST"])
        def graphql_placeholder():
            return jsonify({"data": None, "message": "GraphQL is being prepared."})

    app.register_blueprint(placeholder)


def _register_graphql(app: Flask) -> bool:
    """Mount GraphQL when its controller exposes ``register(app)``."""
    try:
        module = import_module("app.controllers.graphql")
    except ModuleNotFoundError as error:
        if error.name == "app.controllers.graphql":
            return False
        raise

    register = getattr(module, "register", None)
    if callable(register):
        register(app)
        return True
    return False


def create_app() -> Flask:
    """Create the Flask application with available controllers and DB teardown."""
    app = Flask(__name__)
    app.config.from_object("app.config")
    db.init_app(app)

    registered_controllers = _register_controller_blueprints(app)
    graphql_registered = _register_graphql(app)
    if "app.controllers.pages" not in registered_controllers or not graphql_registered:
        # TODO: Phases 3 and 4 replace these routes with real controllers/schema.
        _register_placeholder_routes(
            app,
            pages_registered="app.controllers.pages" in registered_controllers,
            graphql_registered=graphql_registered,
        )

    return app
