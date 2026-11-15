# Documento de Implementação — Aplicação-Alvo para Dataset de SQLi

> **Escopo desta fase:** construir **apenas a aplicação** — o alvo web e a captura de log no Nginx. A geração de tráfego (legítimo e de ataque) e a consolidação do dataset **não fazem parte desta entrega**; serão feitas depois, com a app já no ar. Não implemente scripts de tráfego, ataque ou rotulagem agora.

> **Para quem vai implementar (humano ou IA):** este documento é autocontido. Implemente exatamente o que está descrito. Onde diz **REQUISITO**, é obrigatório; **NÃO FAÇA** marca erros comuns a evitar. Não adicione segurança, sanitização de entrada, WAF, rate limit ou autenticação além do descrito. Em caso de dúvida sobre um contrato, siga a assinatura literal das seções §5–§6.

---

## 1. Contexto e propósito (leia antes de codar)

Esta aplicação é **instrumentação de laboratório** para pesquisa acadêmica em detecção de SQL Injection. Ela é um alvo web que **recebe** requisições e faz com que o **Nginx registre** cada requisição num log estruturado. Mais adiante (fora desta fase), esse log será usado para compor um dataset — por isso a app precisa registrar a entrada intacta desde já.

Três princípios que governam TODA decisão de implementação:

1. **Campos atacáveis, não app explorável.** Todos os acessos ao banco usam **consultas parametrizadas** (prepared statements). A app NÃO é vulnerável. Os campos marcados **[ALVO]** apenas recebem a entrada e respondem normalmente; a entrada é registrada no log intacta. Uma eventual injeção não precisa (nem deve) funcionar.
2. **A entrada deve chegar e ser logada intacta.** **NÃO FAÇA** nenhuma sanitização, escaping de entrada, bloqueio de caracteres, WAF ou rate limit. Se qualquer camada rejeitar ou alterar a entrada, o payload some do log e o dataset futuro é corrompido. A segurança vem *só* da query parametrizada.
3. **Pega-ratão intencional.** Tokens SQL (`select`, `where`, `union`, `join`, `from`…) aparecem de propósito no conteúdo da aplicação — em slugs de URL, títulos e texto. Isso é desejado. **NÃO FAÇA** nada para "limpar" ou evitar esses tokens.

As features do detector (fase futura) sairão **apenas da requisição de entrada** (URI, headers, corpo). O comportamento da resposta é irrelevante — logo, os endpoints só precisam responder de forma plausível.

---

## 2. Stack e restrições

**REQUISITO:**
- Linguagem: **Python 3.11+**.
- Framework web: **Flask**, organizado em **MVC** (models / controllers / templates).
- Servidor de aplicação: **Gunicorn**.
- Reverse proxy e ponto de captura de log: **Nginx**.
- Banco: **SQLite** (arquivo único local).
- GraphQL: **Ariadne** (schema-first, casa com Flask) ou **Graphene**; preferir Ariadne. Resolvers usam o mesmo acesso parametrizado ao SQLite.
- Front-end: **HTML + CSS + JavaScript puro** (sem framework, sem build step).
- Orquestração local: **docker-compose** com dois serviços (`app`, `nginx`). SQLite é arquivo montado em volume.

**NÃO FAÇA:** ORM que esconda o SQL (SQLAlchemy Core para parametrizar é aceitável; ORM completo é desnecessário). Sem autenticação real. Sem HTTPS (só HTTP, simplifica a captura). Sem CORS restritivo.

---

## 3. Estrutura de diretórios (REQUISITO)

```
projeto/
  app/
    __init__.py            # cria a app Flask, registra blueprints e /graphql
    config.py              # caminho do DB, host/porta
    db.py                  # conexão SQLite + helper de query parametrizada
    models/
      __init__.py
      posts.py             # acesso a posts/comments/tags
      users.py             # acesso a users
      docs.py              # acesso a docs
    controllers/
      __init__.py
      pages.py             # rotas HTML (navegação)
      api_docs.py          # /api/docs/*
      api_forum.py         # /api/posts/*, /api/comments
      api_users.py         # /api/users/*, /api/login
      graphql.py           # /graphql (schema + resolvers)
    templates/
      base.html
      docs_list.html
      doc_page.html
      forum.html
    static/
      css/style.css
      js/app.js
      docs/                # conteúdo das páginas de doc (com SQL de propósito)
  db/
    schema.sql             # DDL (§4)
    seed.sql               # dados iniciais (§4) — conteúdo contém SQL de propósito
    lab.db                 # gerado; NÃO versionar
  nginx/
    nginx.conf             # proxy + log_format JSON (§7)
  tools/
    reset_db.sh            # recria lab.db a partir de schema.sql + seed.sql
  docker-compose.yml
  requirements.txt
  README.md                # como subir e resetar
```

> Nesta fase, `tools/` contém apenas `reset_db.sh`. Não crie scripts de geração de tráfego, ataque ou rotulagem.

---

## 4. Banco de dados

### 4.1 schema.sql (REQUISITO — DDL exata)

```sql
CREATE TABLE users (
  id            INTEGER PRIMARY KEY,
  username      TEXT NOT NULL UNIQUE,
  email         TEXT NOT NULL,
  password_hash TEXT NOT NULL,
  bio           TEXT
);

CREATE TABLE posts (
  id         INTEGER PRIMARY KEY,
  user_id    INTEGER NOT NULL REFERENCES users(id),
  title      TEXT NOT NULL,
  body       TEXT NOT NULL,
  created_at TEXT NOT NULL   -- ISO-8601
);

CREATE TABLE comments (
  id         INTEGER PRIMARY KEY,
  post_id    INTEGER NOT NULL REFERENCES posts(id),
  user_id    INTEGER NOT NULL REFERENCES users(id),
  body       TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE tags (
  id   INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE post_tags (
  post_id INTEGER NOT NULL REFERENCES posts(id),
  tag_id  INTEGER NOT NULL REFERENCES tags(id),
  PRIMARY KEY (post_id, tag_id)
);

CREATE TABLE docs (
  id      INTEGER PRIMARY KEY,
  slug    TEXT NOT NULL UNIQUE,
  title   TEXT NOT NULL,
  content TEXT NOT NULL
);
```

### 4.2 seed.sql (REQUISITO — conteúdo com SQL de propósito)

Popule no mínimo:
- **5 usuários** com bio de texto normal.
- **~30 posts** cujo `title`/`body` incluam conteúdo sobre SQL de propósito. Ex.: título "Como usar INNER JOIN com WHERE", corpo explicando `SELECT ... FROM ... WHERE ...`. Isto alimenta o pega-ratão.
- **comments** variados (texto normal e alguns citando SQL).
- **tags**: `sql`, `join`, `where`, `select`, `performance`, `sqlite`, `graphql`.
- **docs** (REQUISITO: slugs abaixo são exatos — são usados como pega-ratão no path):
  - `select-statement` — "The SELECT statement"
  - `where-clause` — "The WHERE clause"
  - `inner-join` — "INNER JOIN"
  - `union-operator` — "The UNION operator"
  - `order-by` — "ORDER BY"
  - `group-by-having` — "GROUP BY and HAVING"
  - Conteúdo de cada doc: explicação real com exemplos de SQL (tokens à vontade).

`tools/reset_db.sh`: apaga `db/lab.db`, roda `schema.sql` depois `seed.sql`. Deve ser idempotente.

---

## 5. Contratos REST (REQUISITO — assinaturas exatas)

Regras gerais:
- Toda leitura/escrita no banco é **parametrizada** (`cursor.execute(sql, params)`), nunca f-string/concatenação com entrada do usuário.
- Campos **[ALVO]** podem, no futuro, receber payloads arbitrários. O handler deve tratá-los como valor normal: usar como parâmetro na query e responder. Se o valor não casar nada (ex.: `id` não numérico), responder 200 com resultado vazio OU 404 — **nunca** 400 por "caractere inválido" (isso filtraria a entrada).
- Respostas de API: `Content-Type: application/json`.

| Método | Rota | Campos [ALVO] | Comportamento | Resposta OK |
|---|---|---|---|---|
| GET | `/docs` | — | lista docs | 200 HTML |
| GET | `/docs/<slug>` | `slug` (path) | renderiza doc; slug desconhecido → 404 | 200 HTML |
| GET | `/api/docs/search?q=` | `q` | `SELECT ... WHERE title LIKE ?` (param `%q%`) | 200 JSON lista |
| GET | `/api/posts?tag=&sort=&page=` | `tag`, `sort` | `sort` resolvido por **allowlist** → coluna; valor fora da allowlist → default `created_at` (NÃO concatenar `sort`) | 200 JSON lista |
| GET | `/api/posts/<id>` | `id` (path) | `SELECT ... WHERE id = ?`; id não-numérico → 404 | 200 JSON objeto |
| GET | `/api/posts/search?q=` | `q` | `LIKE ?` parametrizado | 200 JSON lista |
| POST | `/api/posts` | corpo JSON aninhado | insere parametrizado (§5.1) | 201 JSON objeto |
| POST | `/api/comments` | corpo form | insere parametrizado | 201 JSON objeto |
| POST | `/api/login` | `username`, `password` | `SELECT ... WHERE username = ?`; compara hash; credencial errada → 401 | 200 / 401 JSON |
| GET | `/api/users/<id>` | `id` (path) | `SELECT ... WHERE id = ?` | 200 / 404 JSON |
| GET | `/api/tags` | — | lista tags | 200 JSON lista |

### 5.1 Corpo de `POST /api/posts` (JSON aninhado — REQUISITO)

Aceitar corpo aninhado (não plano):
```json
{
  "post": {
    "title": "string",
    "body": "string",
    "meta": { "tags": ["sql", "join"], "source": "web" }
  }
}
```
- Extrair `post.title`, `post.body`, `post.meta.tags`.
- Inserir com query parametrizada.
- A entrada pode vir em `post.title`, `post.body` ou aninhada em `post.meta.*` — todos são [ALVO]. O handler percorre e usa os valores como parâmetros; não valida conteúdo.

### 5.2 Allowlist de `sort` (REQUISITO — anti-concatenação)

```python
SORT_COLUMNS = {"recent": "created_at", "title": "title", "id": "id"}
col = SORT_COLUMNS.get(request.args.get("sort", "recent"), "created_at")
# `col` interpolado é seguro porque veio da allowlist; NUNCA o valor cru do usuário
sql = f"SELECT ... ORDER BY {col} DESC LIMIT ? OFFSET ?"
```
O valor cru de `sort` (que pode conter payload order-by) é **logado** pelo Nginx mas **nunca** entra na query. Este é o padrão da app inteira: recebe a entrada, loga, não executa como SQL.

---

## 6. GraphQL — `POST /graphql` (REQUISITO)

Schema mínimo (schema-first):
```graphql
type Post { id: ID!, title: String!, body: String!, createdAt: String! }
type Doc { slug: String!, title: String!, content: String! }
type Query {
  post(id: ID!): Post
  searchPosts(q: String!): [Post!]!
  docs: [Doc!]!
}
```
Resolvers:
- `post(id)` → `SELECT ... WHERE id = ?` parametrizado. **[ALVO]** em `id` (via argumento **e** via variável).
- `searchPosts(q)` → `LIKE ?` parametrizado. **[ALVO]** em `q`.
- Habilitar **introspecção** (`__schema`).

Duas formas de entrada que DEVEM funcionar:
1. Inline: `{"query":"{ post(id:\"1\"){ title } }"}`
2. Com variáveis: `{"query":"query($id:ID!){ post(id:$id){ title } }","variables":{"id":"1"}}`

**NÃO FAÇA:** validar/filtrar o valor do argumento. O resolver recebe a string, usa como parâmetro, responde normalmente ou vazio.

---

## 7. Logging no Nginx (REQUISITO)

O Nginx é o ponto único de captura. Configurar um `log_format` **JSON, uma requisição por linha**, incluindo:

- timestamp com milissegundos (`$time_iso8601` + `$msec`)
- `$request_method`, `$request_uri` (com query string, **sem decodificar**), `$server_protocol`
- `$status`, `$body_bytes_sent`, `$request_time`
- `$http_user_agent`, `$http_referer`, `$remote_addr`
- **`$request_body`** — REQUISITO. Sem isto, os vetores em corpo JSON/form/GraphQL não são capturados.
- `$content_type`

Config necessária:
- `log_format labjson escape=json '...'` com os campos acima.
- No `location /`: `proxy_pass` para a app; garantir que o corpo seja lido para `$request_body` estar disponível (`client_body_buffer_size` grande o suficiente; NÃO usar `client_body_in_file_only`).
- Um `access_log /var/log/nginx/lab.jsonl labjson;` dedicado.

**NÃO FAÇA:** decodificar a query string no Nginx; a versão crua (com `%27`, `0x…`) é feature importante para a fase futura.

Entregar o `nginx.conf` completo e funcional com esse `log_format`.

---

## 8. Front-end (mínimo — REQUISITO)

Só o suficiente para navegação real e plausível:
- Página de listagem de docs e página de doc individual (consomem `/docs`).
- Página de fórum: lista posts, busca (`/api/posts/search`), abre post, formulário de comentário.
- JS puro fazendo `fetch` aos endpoints da §5/§6.
- **NÃO FAÇA:** validação de formulário que bloqueie caracteres (aspas, etc.). Os campos aceitam qualquer texto e enviam como está.

---

## 9. Reprodutibilidade (REQUISITO)

- `reset_db.sh` recria o banco a partir de schema+seed.
- Versionar `nginx.conf`, `schema.sql`, `seed.sql`.
- `README.md` com passos: subir com docker-compose, resetar o banco, onde fica o log (`lab.jsonl`).

---

## 10. Critérios de aceite (Definition of Done)

A aplicação está pronta quando:

- [ ] `docker-compose up` sobe `app` + `nginx`; a app responde via Nginx em HTTP.
- [ ] `reset_db.sh` cria `lab.db` a partir de schema+seed; docs com os slugs exatos da §4.2 existem.
- [ ] Todos os endpoints da §5 respondem conforme a tabela; nenhum retorna 400 por caractere "inválido" num campo [ALVO].
- [ ] `POST /api/posts` aceita e persiste JSON aninhado (§5.1).
- [ ] `/graphql` funciona nas duas formas (inline e variáveis) e com introspecção.
- [ ] Enviar `?q=' OR '1'='1` (e similares) a um campo [ALVO] retorna resposta normal/vazia (não erro de filtro) e a requisição aparece **intacta** em `lab.jsonl`.
- [ ] `lab.jsonl` contém, por linha, query string crua + `$request_body` + `$request_time` + campos da §7.
- [ ] Nenhuma sanitização/WAF/rate limit em lugar algum do caminho da requisição.

---

## 11. Resumo dos anti-padrões (revisar antes de entregar)

- **NÃO** montar SQL por concatenação/f-string com entrada do usuário (só via allowlist para nomes de coluna).
- **NÃO** sanitizar, escapar ou bloquear entrada; ela tem que chegar ao log intacta.
- **NÃO** retornar 400 por caractere inesperado num campo [ALVO].
- **NÃO** decodificar a query string no Nginx.
- **NÃO** implementar, nesta fase, scripts de geração de tráfego, ataque ou rotulagem.
