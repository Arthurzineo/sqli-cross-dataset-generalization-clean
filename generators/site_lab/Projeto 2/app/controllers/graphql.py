"""Schema-first GraphQL endpoint backed by parameterized models."""

from ariadne import MutationType, QueryType, gql, graphql_sync, make_executable_schema
from flask import jsonify, request

from app.models.docs import list_docs
from app.models.posts import create_comment, create_post, get_post_by_id, search_posts


type_defs = gql(
    """
    type Post {
      id: ID!
      title: String!
      body: String!
      author: String!
      createdAt: String!
    }

    type Doc {
      slug: String!
      title: String!
      content: String!
    }

    type Comment {
      id: ID!
      postId: ID!
      author: String!
      body: String!
      createdAt: String!
    }

    type Query {
      post(id: ID!): Post
      searchPosts(q: String!): [Post!]!
      docs: [Doc!]!
    }

    type Mutation {
      createPost(title: String!, body: String!, author: String, tags: [String!]): Post!
      addComment(postId: ID!, author: String, body: String!): Comment!
    }
    """
)

query_type = QueryType()
mutation_type = MutationType()


def _post_value(row):
    """Map the SQLite column name to the GraphQL field name."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "author": row["author"],
        "createdAt": row["created_at"],
    }


@query_type.field("post")
def resolve_post(_, _info, id):
    """Resolve a post with the model's parameterized ID lookup."""
    return _post_value(get_post_by_id(id))


@query_type.field("searchPosts")
def resolve_search_posts(_, _info, q):
    """Resolve a parameterized post-title/body search."""
    return [_post_value(row) for row in search_posts(q)]


@query_type.field("docs")
def resolve_docs(_, _info):
    """Resolve all documentation records."""
    return [dict(row) for row in list_docs()]


def _comment_value(row):
    """Map SQLite comment columns to the public GraphQL field names."""
    return {
        "id": row["id"],
        "postId": row["post_id"],
        "author": row["author"],
        "body": row["body"],
        "createdAt": row["created_at"],
    }


@mutation_type.field("createPost")
def resolve_create_post(_, _info, title, body, author=None, tags=None):
    """Create a post through the parameterized model contract."""
    row = create_post(title, body, tags=tags or (), author_name=author)
    return _post_value(row)


@mutation_type.field("addComment")
def resolve_add_comment(_, _info, postId, body, author=None):
    """Create a comment through the parameterized model contract."""
    row = create_comment(post_id=postId, body=body, author_name=author)
    return _comment_value(row)


schema = make_executable_schema(type_defs, query_type, mutation_type)


def graphql_view():
    """Execute one GraphQL request; Ariadne keeps introspection enabled by default."""
    success, result = graphql_sync(schema, request.get_json(silent=True) or {})
    return jsonify(result), 200 if success else 400


def register(app) -> None:
    """Mount the POST-only GraphQL endpoint in the Flask application factory."""
    app.add_url_rule("/graphql", "graphql", graphql_view, methods=["POST"])
