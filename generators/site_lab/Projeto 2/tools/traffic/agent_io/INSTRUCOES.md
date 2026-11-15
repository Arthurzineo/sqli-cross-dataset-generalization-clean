# Instructions for benign cooking-content agents

Read the pending JSON request and write the response JSON requested by the content service. All text must be natural English about cooking. English is mandatory for titles, question bodies, answers, comments, replies, names, tags, and search terms; never mix in Portuguese or another language.

The `topic` field is one of: `select`, `where`, `union`, `sleep`, `join`, `group-by`, or `order-by`. Use it as ordinary conversational vocabulary inside a real recipe question or answer. Never produce SQL syntax, code, payloads, quotes used as delimiters, comments, tautologies, database guidance, or cybersecurity material.

For `question`, return one item with `title` and `body`. For `answers`, return the requested number of items with `persona` and `text`. For `comment`, `reply`, `searchterm`, `name`, or `tags`, return items with `text`. Preserve the request `id`, set `status` to `done`, and keep the response concise and varied.

Responses are checked automatically. Any non-English text, non-culinary text, missing topic phrase, SQL statement, encoded payload, comment delimiter, tautology, or security/database guidance is rejected and replaced with a safe English cooking fallback.

Example question: “Where should this dough sleep overnight?” / “My kitchen is warm, so where can the covered dough sleep without overproofing?”
Example answer: “Let it sleep on the lowest refrigerator shelf and give it extra room in the bowl.”
