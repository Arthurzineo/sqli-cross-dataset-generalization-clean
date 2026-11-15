INSERT INTO users (id, username, email, password_hash, bio) VALUES
  (1, 'alice', 'alice@example.test', 'f84466274da941bcf3512373cf13b6c0ecc7c1c25bafa1f3c1c2ca688048df28', 'Technical writer who enjoys database examples.'),
  (2, 'bruno', 'bruno@example.test', 'd175e0ed950da5dddd501883e47d021dbc8e6fe8ec545e1ab19fb8887740c8bd', 'Backend developer interested in reliable services.'),
  (3, 'carla', 'carla@example.test', '08dd225ac27ea86707809272fb7bfbcf06959bd89163e445fd4ac46674a919f6', 'Community moderator and documentation editor.'),
  (4, 'diego', 'diego@example.test', 'f1afa06267dde9af8c5c01cff8c1bf9d9386c34ca9ea84ba5dcaadd5a86bbc97', 'Data analyst who likes clear reports.'),
  (5, 'elena', 'elena@example.test', '31c3a6116c9571ca2aaa040817559218137fface507ea67061b6a49534761970', 'Student learning how relational data fits together.');

INSERT INTO tags (id, name) VALUES
  (1, 'sql'),
  (2, 'join'),
  (3, 'where'),
  (4, 'select'),
  (5, 'performance'),
  (6, 'sqlite'),
  (7, 'graphql');

INSERT INTO posts (id, user_id, title, body, created_at) VALUES
  (1, 1, 'Getting started with SELECT', 'Use SELECT id, title FROM posts to choose the columns needed by a page.', '2026-01-01T09:00:00Z'),
  (2, 2, 'Finding rows with WHERE', 'A WHERE clause narrows a SELECT result, for example WHERE user_id = 1.', '2026-01-02T09:00:00Z'),
  (3, 3, 'How INNER JOIN connects tables', 'INNER JOIN posts with users ON posts.user_id = users.id when author data is needed.', '2026-01-03T09:00:00Z'),
  (4, 4, 'ORDER BY for predictable lists', 'SELECT title FROM posts ORDER BY created_at DESC keeps recent discussions first.', '2026-01-04T09:00:00Z'),
  (5, 5, 'GROUP BY and counts', 'GROUP BY tag_id with COUNT(*) shows how frequently each tag is used.', '2026-01-05T09:00:00Z'),
  (6, 1, 'When to use a LEFT JOIN', 'A LEFT JOIN keeps every user even when a user has no matching post.', '2026-01-06T09:00:00Z'),
  (7, 2, 'SQLite text dates', 'Store ISO-8601 text and ORDER BY created_at for chronological SQLite results.', '2026-01-07T09:00:00Z'),
  (8, 3, 'Understanding UNION', 'UNION combines compatible SELECT results and removes duplicate rows by default.', '2026-01-08T09:00:00Z'),
  (9, 4, 'A simple INSERT example', 'INSERT INTO tags (name) VALUES (?) should receive values as query parameters.', '2026-01-09T09:00:00Z'),
  (10, 5, 'UPDATE with a condition', 'UPDATE posts SET title = ? WHERE id = ? changes only the selected record.', '2026-01-10T09:00:00Z'),
  (11, 1, 'DELETE needs a WHERE clause', 'DELETE FROM comments WHERE id = ? is safer than deleting every comment.', '2026-01-11T09:00:00Z'),
  (12, 2, 'Indexes and query plans', 'EXPLAIN QUERY PLAN helps inspect how SQLite evaluates a SELECT statement.', '2026-01-12T09:00:00Z'),
  (13, 3, 'Filtering with LIKE', 'SELECT title FROM docs WHERE title LIKE ? supports a search box.', '2026-01-13T09:00:00Z'),
  (14, 4, 'Parameter placeholders matter', 'Use WHERE username = ? instead of building SQL text from request input.', '2026-01-14T09:00:00Z'),
  (15, 5, 'Joining post tags', 'JOIN post_tags ON posts.id = post_tags.post_id links posts to tags.', '2026-01-15T09:00:00Z'),
  (16, 1, 'Aggregate functions', 'SELECT COUNT(*), MIN(id), MAX(id) FROM posts summarizes a table.', '2026-01-16T09:00:00Z'),
  (17, 2, 'HAVING after GROUP BY', 'Use HAVING COUNT(*) > 1 after GROUP BY to filter aggregate groups.', '2026-01-17T09:00:00Z'),
  (18, 3, 'Transactions in SQLite', 'BEGIN, INSERT, and COMMIT make a group of related writes atomic.', '2026-01-18T09:00:00Z'),
  (19, 4, 'Reading a GraphQL resolver', 'A resolver can call SELECT title FROM posts WHERE id = ? with a parameter.', '2026-01-19T09:00:00Z'),
  (20, 5, 'Pagination with LIMIT', 'SELECT id, title FROM posts ORDER BY id DESC LIMIT ? OFFSET ? supports pages.', '2026-01-20T09:00:00Z'),
  (21, 1, 'DISTINCT values', 'SELECT DISTINCT user_id FROM posts returns each author once.', '2026-01-21T09:00:00Z'),
  (22, 2, 'NULL checks', 'Use WHERE bio IS NULL instead of comparing a NULL value with equals.', '2026-01-22T09:00:00Z'),
  (23, 3, 'Foreign keys in a forum', 'REFERENCES users(id) documents the relationship between posts and users.', '2026-01-23T09:00:00Z'),
  (24, 4, 'Subqueries for comparison', 'A SELECT can use WHERE id IN (SELECT post_id FROM comments) when useful.', '2026-01-24T09:00:00Z'),
  (25, 5, 'The CASE expression', 'SELECT CASE WHEN id > 10 THEN ''new'' ELSE ''old'' END labels a row.', '2026-01-25T09:00:00Z'),
  (26, 1, 'Reading JOIN order', 'Start with FROM posts then JOIN users so each selected column has context.', '2026-01-26T09:00:00Z'),
  (27, 2, 'A WHERE clause for tags', 'SELECT posts.title FROM posts JOIN post_tags WHERE post_tags.tag_id = ? is parameterized.', '2026-01-27T09:00:00Z'),
  (28, 3, 'Column aliases', 'SELECT p.title AS post_title FROM posts AS p keeps JSON mapping clear.', '2026-01-28T09:00:00Z'),
  (29, 4, 'SQLite prepared statements', 'Prepared SELECT statements separate SQL structure from supplied values.', '2026-01-29T09:00:00Z'),
  (30, 5, 'Reviewing a query', 'Read SELECT, FROM, WHERE, GROUP BY, and ORDER BY in that logical sequence.', '2026-01-30T09:00:00Z');

INSERT INTO post_tags (post_id, tag_id) VALUES
  (1, 4), (2, 3), (3, 2), (4, 5), (5, 3), (6, 2), (7, 6), (8, 1), (9, 1), (10, 1),
  (11, 3), (12, 5), (13, 4), (14, 1), (15, 2), (16, 4), (17, 3), (18, 6), (19, 7), (20, 5),
  (21, 4), (22, 3), (23, 1), (24, 4), (25, 1), (26, 2), (27, 3), (28, 4), (29, 6), (30, 1);

INSERT INTO comments (id, post_id, user_id, body, created_at) VALUES
  (1, 1, 2, 'The SELECT example is clear for newcomers.', '2026-02-01T10:00:00Z'),
  (2, 2, 3, 'WHERE conditions become easier after practicing with small tables.', '2026-02-02T10:00:00Z'),
  (3, 3, 4, 'The INNER JOIN explanation helped me follow the foreign key.', '2026-02-03T10:00:00Z'),
  (4, 5, 1, 'COUNT with GROUP BY is useful for tag reports.', '2026-02-04T10:00:00Z'),
  (5, 7, 5, 'ISO-8601 dates make ORDER BY straightforward.', '2026-02-05T10:00:00Z'),
  (6, 9, 3, 'Using parameters with INSERT is a good habit.', '2026-02-06T10:00:00Z'),
  (7, 12, 1, 'EXPLAIN QUERY PLAN is worth checking before performance changes.', '2026-02-07T10:00:00Z'),
  (8, 14, 5, 'A placeholder keeps the SQL structure separate from a value.', '2026-02-08T10:00:00Z'),
  (9, 19, 2, 'GraphQL resolvers should use the same parameterized SELECT helpers.', '2026-02-09T10:00:00Z'),
  (10, 20, 4, 'LIMIT and OFFSET are enough for a small forum page.', '2026-02-10T10:00:00Z'),
  (11, 25, 2, 'CASE makes a result easier to read without changing stored data.', '2026-02-11T10:00:00Z'),
  (12, 30, 1, 'Reading the clauses in sequence is a useful review technique.', '2026-02-12T10:00:00Z');

INSERT INTO docs (id, slug, title, content) VALUES
  (1, 'select-statement', 'The SELECT statement', 'SELECT chooses columns from a table. Example: SELECT id, title FROM posts;'),
  (2, 'where-clause', 'The WHERE clause', 'WHERE filters rows. Example: SELECT title FROM posts WHERE user_id = 1;'),
  (3, 'inner-join', 'INNER JOIN', 'INNER JOIN returns matching rows. Example: SELECT posts.title FROM posts INNER JOIN users ON posts.user_id = users.id;'),
  (4, 'union-operator', 'The UNION operator', 'UNION combines compatible SELECT results. Example: SELECT title FROM posts UNION SELECT title FROM docs;'),
  (5, 'order-by', 'ORDER BY', 'ORDER BY sorts results. Example: SELECT title FROM posts ORDER BY created_at DESC;'),
  (6, 'group-by-having', 'GROUP BY and HAVING', 'GROUP BY creates aggregates and HAVING filters them. Example: SELECT user_id, COUNT(*) FROM posts GROUP BY user_id HAVING COUNT(*) > 1;');

UPDATE posts
SET author_name = CASE id % 6
  WHEN 0 THEN 'anon_dev'
  WHEN 1 THEN 'sql_learner'
  WHEN 2 THEN 'db_guest'
  WHEN 3 THEN 'curious_coder'
  WHEN 4 THEN 'query_novice'
  WHEN 5 THEN 'data_wanderer'
END
WHERE id BETWEEN 1 AND 30;
