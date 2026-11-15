-- Forum Q&A personas and SQL discussion threads.
-- Password hashes are SHA-256("lab-sqli-salt:<username>123").

INSERT INTO users (id, username, email, password_hash, bio) VALUES
  (6, 'dba_veteran', 'dba_veteran@example.test', '4f97ae05767896a81158584fcf8235ea2a2a35a934c13d1e44b38fa0a59ea433', 'Database administrator focused on reliable PostgreSQL operations.'),
  (7, 'junior_dev', 'junior_dev@example.test', '67449cc26cc36345c38202e1f350b0f1f7490ff29e80214395df3dd00d5fea8f', 'Early-career developer learning SQL by building applications.'),
  (8, 'backend_carla', 'backend_carla@example.test', 'e27bed3291f0416fa83fbf14f58cb4c69ea26521368f7777cf57e8e81f54de77', 'Backend engineer who works with APIs and relational databases.'),
  (9, 'data_analyst_theo', 'data_analyst_theo@example.test', '82a2c07314a65c63d6bc103dbb67ea9f8d5855c2cdc41146f85c739495a943e5', 'Data analyst interested in clear queries and query plans.'),
  (10, 'prof_okonkwo', 'prof_okonkwo@example.test', 'f1a9de4fb516807f99b367c638f20019bf1885a8d5b0c57dc3120f6e4c26d9a1', 'Professor explaining database concepts with small examples.'),
  (11, 'skeptic_sam', 'skeptic_sam@example.test', '583e888fafebd6d66084bc9ae794c64b8086e738698fa245020d6fe6dd800560', 'Engineer who asks for evidence before accepting tuning advice.'),
  (12, 'concise_kim', 'concise_kim@example.test', 'cdd523c4fd6e4c4fc8837221b5995f9e2de6faf6fde93776bc351bcb5d9eb9db', 'Developer who prefers direct, practical answers.'),
  (13, 'verbose_victor', 'verbose_victor@example.test', 'a505b2c632eb91306ce13718ff5959890e554079fd85e9a1fedefefd318e98eb', 'Consultant who documents the trade-offs behind SQL choices.'),
  (14, 'ops_maria', 'ops_maria@example.test', 'ff8bdbf1cb22098576ab74b414010c046282483f35393ed802e1f5ffc4416a90', 'Operations engineer concerned with production query behavior.'),
  (15, 'consultant_raj', 'consultant_raj@example.test', 'b2abd39fd431126b4c8028009a8f97a4d89b8f2bdfdddd6d1af56e40717a59b8', 'Database consultant focused on maintainable schemas and indexes.'),
  (16, 'student_lee', 'student_lee@example.test', 'c4535d1f4676ab4757584cc76a00cf8cd9c1d5c57e3b8877631a07e7185a83af', 'Student practicing PostgreSQL fundamentals.'),
  (17, 'night_owl_nadia', 'night_owl_nadia@example.test', '036f44425b99767425fc97925df5d05258cc9224c2da8f7e5ef281b58e86b028', 'Developer investigating late-night production incidents.');

INSERT INTO posts (id, user_id, title, body, created_at) VALUES
  (31, 16, 'Why does `WHERE col = NULL` return no rows?', 'I have `SELECT * FROM orders WHERE shipped_at = NULL` and it returns nothing even though there are rows with a NULL `shipped_at`. What am I doing wrong?', '2026-09-01 09:00:00'),
  (32, 7, 'INNER JOIN vs LEFT JOIN — what''s the practical difference?', 'When I switch `INNER JOIN` to `LEFT JOIN` between `customers` and `orders`, my row count changes. Can someone explain with a small example when I should use each?', '2026-09-01 09:01:00'),
  (33, 8, 'Efficient pagination with LIMIT and OFFSET', 'My query `SELECT ... ORDER BY created_at DESC LIMIT 20 OFFSET 100000` gets slow on big tables. Is OFFSET the problem, and what''s a better approach (keyset pagination)?', '2026-09-01 09:02:00'),
  (34, 9, 'GROUP BY with HAVING vs filtering in WHERE', 'I want only groups whose `COUNT(*) > 5`. Why can''t I put that in `WHERE`, and when do I use `HAVING` instead?', '2026-09-01 09:03:00'),
  (35, 7, '"each UNION query must have the same number of columns"', 'My `SELECT a, b FROM t1 UNION SELECT a FROM t2` throws an error. What''s the rule for UNION column lists and types?', '2026-09-01 09:04:00'),
  (36, 8, 'UPDATE a table using values from another table', 'How do I update `products.price` based on a matching row in `price_updates`? Is `UPDATE ... FROM` the right approach in PostgreSQL?', '2026-09-01 09:05:00'),
  (37, 16, 'Duplicate rows after a JOIN — how to collapse them?', 'After joining `posts` to `post_tags` I get the same post multiple times. Should I use `DISTINCT`, `GROUP BY`, or restructure the query?', '2026-09-01 09:06:00'),
  (38, 14, 'How does ORDER BY handle NULL values?', 'Some NULLs show up first, some last, depending on ASC/DESC. How do `NULLS FIRST` and `NULLS LAST` work?', '2026-09-01 09:07:00'),
  (39, 13, 'When should I use a CTE (WITH) instead of a subquery?', 'Is `WITH recent AS (...) SELECT ... FROM recent` just a readability thing, or are there real differences vs an inline subquery?', '2026-09-01 09:08:00'),
  (40, 16, 'Case-insensitive search: LIKE vs ILIKE', 'I want `name LIKE ''%ann%''` to match "Ann" and "ANN". Should I use `ILIKE`, `LOWER()`, or something else? Any index implications?', '2026-09-01 09:09:00'),
  (41, 7, 'UPSERT in PostgreSQL — INSERT ... ON CONFLICT', 'I want to insert a row, but if the key already exists, update it instead. How does `ON CONFLICT (id) DO UPDATE` work, and what''s `EXCLUDED`?', '2026-09-01 09:10:00'),
  (42, 9, 'Why isn''t my composite index on (a, b) used when I filter only on b?', 'I created `CREATE INDEX ON t (a, b)` but a query with only `WHERE b = ?` does a seq scan. Is that expected because of the leftmost-prefix rule?', '2026-09-01 09:11:00');

INSERT INTO comments (id, post_id, user_id, body, created_at) VALUES
  (101, 31, 6, '`NULL` is not a value that compares equal to anything, including itself. Use `WHERE shipped_at IS NULL`; use `IS NOT NULL` for the opposite test.', '2026-09-01 10:00:00'),
  (102, 31, 12, 'Use `IS NULL`, not `= NULL`.', '2026-09-01 10:01:00'),
  (103, 32, 8, 'An INNER JOIN keeps only customers with a matching order. A LEFT JOIN keeps every customer and fills order columns with NULL when no order exists.', '2026-09-01 10:02:00'),
  (104, 32, 10, 'Think of the left table as mandatory in a LEFT JOIN. Start from `customers LEFT JOIN orders` when customers without orders must remain visible.', '2026-09-01 10:03:00'),
  (105, 33, 9, 'OFFSET makes the database walk past the skipped rows. Keyset pagination remembers the last `(created_at, id)` and asks for rows before that key.', '2026-09-01 10:04:00'),
  (106, 33, 14, 'In production, pair the keyset predicate with an index such as `(created_at DESC, id DESC)` and use a stable ordering.', '2026-09-01 10:05:00'),
  (107, 34, 10, 'WHERE filters input rows before grouping. HAVING filters the groups after `COUNT(*)` has been calculated.', '2026-09-01 10:06:00'),
  (108, 34, 7, 'So this is the pattern: `GROUP BY customer_id HAVING COUNT(*) > 5`.', '2026-09-01 10:07:00'),
  (109, 35, 6, 'Each SELECT in a UNION needs the same number of output columns in matching positions, and the types in each position must be compatible.', '2026-09-01 10:08:00'),
  (110, 35, 12, 'Add a matching second column to the second SELECT, perhaps `SELECT a, NULL::text FROM t2` when that type is appropriate.', '2026-09-01 10:09:00'),
  (111, 36, 8, 'Yes. In PostgreSQL, `UPDATE products p SET price = u.price FROM price_updates u WHERE u.product_id = p.id` is the common form.', '2026-09-01 10:10:00'),
  (112, 36, 11, 'Make sure `price_updates` has at most one matching row per product. Multiple matches make the chosen source row unpredictable.', '2026-09-01 10:11:00'),
  (113, 37, 9, 'The duplicates reflect one row per matching tag. Use `EXISTS` when you only need to filter posts by a tag, rather than returning tag rows.', '2026-09-01 10:12:00'),
  (114, 37, 15, 'DISTINCT can be correct for presentation, but first decide the result grain. Restructure the join or aggregate tags when one post per row is the contract.', '2026-09-01 10:13:00'),
  (115, 38, 6, 'PostgreSQL defaults are NULLS LAST for ASC and NULLS FIRST for DESC. State the desired behavior explicitly when it matters: `ORDER BY due_at ASC NULLS LAST`.', '2026-09-01 10:14:00'),
  (116, 38, 17, 'Explicit NULL placement also makes reviews easier because readers do not have to remember the default.', '2026-09-01 10:15:00'),
  (117, 39, 13, 'A CTE often improves readability and can be referenced more than once. Modern PostgreSQL may inline a simple CTE, so inspect the plan instead of assuming a performance penalty.', '2026-09-01 10:16:00'),
  (118, 39, 8, 'Use a subquery for a small local expression; use a named CTE when it clarifies a multi-step query. `MATERIALIZED` and `NOT MATERIALIZED` let you influence that choice when needed.', '2026-09-01 10:17:00'),
  (119, 40, 8, '`ILIKE` is PostgreSQL''s case-insensitive LIKE. For frequent wildcard searches, consider the `pg_trgm` extension and a trigram index.', '2026-09-01 10:18:00'),
  (120, 40, 11, '`LOWER(name) LIKE LOWER(...)` can work too, but benchmark with your collation and pattern shape before choosing an index.', '2026-09-01 10:19:00'),
  (121, 41, 6, '`EXCLUDED` is the row you tried to insert. For example: `ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name`.', '2026-09-01 10:20:00'),
  (122, 41, 7, 'The conflict target must match a unique constraint or unique index, right?', '2026-09-01 10:21:00'),
  (123, 42, 9, 'That is the usual behavior for a B-tree composite index: predicates on the leading column `a` are the most useful. An index on `b` may be warranted for that workload.', '2026-09-01 10:22:00'),
  (124, 42, 15, 'Check `EXPLAIN (ANALYZE, BUFFERS)` with realistic data. A sequential scan can still be cheaper when the predicate returns a large share of the table.', '2026-09-01 10:23:00');

INSERT INTO posts (id, user_id, title, body, created_at) VALUES
  (43, 15, 'Relational vs document (NoSQL) databases — how to choose?', 'For a new project, how do I decide between a relational database and a document store? What kinds of workloads favor each?', '2026-09-01 11:00:00'),
  (44, 16, 'What are the ACID properties and why do they matter?', 'I keep seeing "ACID" mentioned. Can someone explain atomicity, consistency, isolation, and durability in plain terms and why an application developer should care?', '2026-09-01 11:01:00'),
  (45, 9, 'OLTP vs OLAP — what''s the real difference?', 'People say a system is "OLTP" or "OLAP". What distinguishes these workloads, and does it change how you design the schema and hardware?', '2026-09-01 11:02:00'),
  (46, 8, 'Normalization vs denormalization — when to break the rules?', 'I learned about normal forms in school, but production systems seem to denormalize a lot. When is denormalization justified?', '2026-09-01 11:03:00'),
  (47, 7, 'Primary key vs unique constraint — conceptual difference', 'Both enforce uniqueness. Conceptually, what''s the difference, and why can a table have only one primary key but many unique constraints?', '2026-09-01 11:04:00'),
  (48, 14, 'Transaction isolation levels and the anomalies they prevent', 'What do READ COMMITTED, REPEATABLE READ, and SERIALIZABLE actually protect against (dirty reads, non-repeatable reads, phantoms)? A conceptual explanation, please.', '2026-09-01 11:05:00'),
  (49, 16, 'What is a deadlock and how do databases handle it?', 'Two transactions get stuck waiting on each other. How does a database detect this, and what happens to the transactions?', '2026-09-01 11:06:00'),
  (50, 15, 'PostgreSQL vs MySQL — how do teams decide?', 'Setting aside fanboyism, what are the real, practical factors that make a team pick PostgreSQL over MySQL or the other way around?', '2026-09-01 11:07:00'),
  (51, 13, 'Sharding vs replication — what problems does each solve?', 'I hear both terms for "scaling the database". Conceptually, how are sharding and replication different, and what do they each buy you?', '2026-09-01 11:08:00'),
  (52, 17, 'What is a write-ahead log (WAL) and why does it exist?', 'I read that databases write to a WAL before applying changes. What''s the purpose of that, and how does it relate to durability and crash recovery?', '2026-09-01 11:09:00'),
  (53, 7, 'Why do apps use connection pooling?', 'What problem does a connection pool actually solve, and what goes wrong if every request opens its own database connection?', '2026-09-01 11:10:00'),
  (54, 16, 'How do B-tree indexes work, at a high level?', 'Without going into implementation details, what is a B-tree index conceptually, and why does it make lookups and range scans fast?', '2026-09-01 11:11:00');

INSERT INTO comments (id, post_id, user_id, body, created_at) VALUES
  (125, 43, 15, 'Choose from access patterns and constraints, not labels. Relational systems fit connected data, strong integrity rules, and flexible reporting; document stores fit aggregates that are naturally retrieved and changed together.', '2026-09-01 12:00:00'),
  (126, 43, 8, 'A document store does not remove modeling work. It moves more consistency decisions into the application, which can be useful or expensive depending on the team.', '2026-09-01 12:01:00'),
  (127, 44, 10, 'Atomicity means an all-or-nothing unit of work. Consistency preserves declared rules, isolation controls interference between concurrent work, and durability keeps committed results after a crash.', '2026-09-01 12:02:00'),
  (128, 44, 12, 'ACID is why a successful payment does not become half a payment after a failure.', '2026-09-01 12:03:00'),
  (129, 45, 9, 'OLTP serves many short, concurrent operational actions and usually values fast writes. OLAP scans and aggregates large histories for analysis, so its data layout and hardware priorities differ.', '2026-09-01 12:04:00'),
  (130, 45, 14, 'Mixing heavy analytics with a busy operational database can create contention. Teams often separate reporting workloads to protect customer-facing latency.', '2026-09-01 12:05:00'),
  (131, 46, 10, 'Normalization reduces duplicated facts and update anomalies. Denormalization is justified when measured read needs, reporting needs, or distribution costs outweigh that maintenance burden.', '2026-09-01 12:06:00'),
  (132, 46, 11, 'Do not call it a performance improvement until it is measured. A duplicated value needs a clear owner and a reliable way to stay synchronized.', '2026-09-01 12:07:00'),
  (133, 47, 6, 'A primary key is the table''s chosen identity and is unique and non-null. A unique constraint enforces uniqueness for another candidate key; several of those can exist.', '2026-09-01 12:08:00'),
  (134, 47, 7, 'So an email address can be unique, while an internal id is still the primary identity?', '2026-09-01 12:09:00'),
  (135, 48, 10, 'Isolation levels define which effects of concurrent work a transaction may observe. Higher isolation prevents more anomalies, but may require retries or reduce concurrency.', '2026-09-01 12:10:00'),
  (136, 48, 14, 'Serializable is a correctness tool, not a free upgrade. Applications must be prepared to retry when the database rejects a conflicting transaction.', '2026-09-01 12:11:00'),
  (137, 49, 6, 'A deadlock is a cycle of waits. The database detects that no participant can proceed, aborts one transaction, and lets the others continue; the application should retry the aborted work.', '2026-09-01 12:12:00'),
  (138, 49, 17, 'Keeping transactions short and acquiring shared resources in a consistent order makes deadlocks much less common.', '2026-09-01 12:13:00'),
  (139, 50, 8, 'Start with required features, operational experience, managed-service options, ecosystem fit, and the team''s ability to run the chosen system. Both can be solid production choices.', '2026-09-01 12:14:00'),
  (140, 50, 15, 'Migration cost and existing expertise often matter more than a generic feature checklist. Test the workloads that are actually important to the product.', '2026-09-01 12:15:00'),
  (141, 51, 13, 'Replication copies data to improve availability, read capacity, or recovery. Sharding partitions data across independent nodes to spread storage and write load, but adds routing and cross-shard complexity.', '2026-09-01 12:16:00'),
  (142, 51, 11, 'Replication is not automatically a write-scaling solution. It depends on the replication model and where writes are accepted.', '2026-09-01 12:17:00'),
  (143, 52, 6, 'A write-ahead log records enough change information durably before data pages are updated. After a crash, recovery can replay committed work and discard incomplete work.', '2026-09-01 12:18:00'),
  (144, 52, 14, 'The log also gives operations a foundation for backup, replication, and point-in-time recovery strategies.', '2026-09-01 12:19:00'),
  (145, 53, 8, 'Creating a database connection is relatively expensive. A pool reuses a bounded set, limits pressure on the database, and avoids connection storms during traffic spikes.', '2026-09-01 12:20:00'),
  (146, 53, 11, 'A pool is not unlimited capacity. Badly chosen pool sizes can overwhelm the database or leave requests waiting, so size it with the database and deployment topology in mind.', '2026-09-01 12:21:00'),
  (147, 54, 9, 'Conceptually, a B-tree keeps sorted keys in balanced pages. The balance makes the path to a key short, and the sorted leaf pages make adjacent ranges efficient to read.', '2026-09-01 12:22:00'),
  (148, 54, 12, 'It narrows a lookup through ordered levels instead of checking every row.', '2026-09-01 12:23:00');

UPDATE posts
SET author_name = CASE id % 6
  WHEN 0 THEN 'anon_dev'
  WHEN 1 THEN 'sql_learner'
  WHEN 2 THEN 'db_guest'
  WHEN 3 THEN 'curious_coder'
  WHEN 4 THEN 'query_novice'
  WHEN 5 THEN 'data_wanderer'
END
WHERE id BETWEEN 31 AND 54;
