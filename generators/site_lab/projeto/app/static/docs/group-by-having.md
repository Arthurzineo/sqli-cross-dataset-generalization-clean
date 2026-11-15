# GROUP BY and HAVING

Use `GROUP BY` and `HAVING` for aggregate reports:

```sql
SELECT user_id, COUNT(*) FROM posts GROUP BY user_id HAVING COUNT(*) > 1;
```
