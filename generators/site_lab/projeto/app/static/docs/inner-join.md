# INNER JOIN

Use `INNER JOIN` to combine matching rows:

```sql
SELECT posts.title FROM posts INNER JOIN users ON posts.user_id = users.id;
```
