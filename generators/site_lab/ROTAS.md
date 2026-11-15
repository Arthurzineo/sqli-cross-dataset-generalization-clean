# ROTAS.md — Mapa completo de rotas e fluxos do site

> Documento de referência para **outra IA (ou humano)** entender a aplicação-alvo de laboratório
> de SQLi. Cobre **todas as rotas**, os **campos de cada POST**, respostas, status, os campos
> `[ALVO]` (que recebem entrada e vão logados intactos) e os **fluxos** do site.
> Fonte da verdade do comportamento: o código em `projeto/app/`. Fonte do design: `IMPLEMENTACAO-app-alvo-sqli.md` e `fases/`.

## 0. Contexto em uma frase
App web de **laboratório** (Flask MVC + Gunicorn + Nginx + SQLite + GraphQL/Ariadne + SPA React)
que **recebe requisições e faz o Nginx logar cada uma** (`projeto/logs/lab.jsonl`) para compor um
dataset de detecção de SQL Injection.

### Princípios que valem para TODAS as rotas
- **App não explorável, campos atacáveis.** Todo acesso ao banco é **parametrizado** (`?`), nunca
  concatenação. Acesso a arquivos usa `safe_join` (sem path traversal).
- **Campos `[ALVO]`** recebem qualquer entrada (incl. payloads SQLi como `' OR '1'='1`), usam-na
  como **valor/parametro**, e respondem normal. **Nunca** retornam 400 por "caractere inválido".
- **Entrada logada intacta.** Nada é sanitizado/escapado/bloqueado no caminho da requisição. O
  Nginx grava a query string **sem decodificar** (`%27` etc.) e o corpo em `$request_body`.
- **Sem autenticação real / sem enforcement.** Existe um fluxo de auth **simulado** (gera
  JWT/cookie/sessão) que **não bloqueia** nenhuma rota — é só para gerar tráfego realista.
- **HTTP → HTTPS.** Servido em HTTPS (self-signed); HTTP redireciona.

## 1. Infra / acesso
| Item | Valor |
|------|-------|
| URL HTTPS (principal) | `https://localhost:8443/` (cert self-signed — aceitar no navegador / `curl -k`) |
| URL HTTP | `http://localhost:8080/` → **301** para HTTPS |
| Subir | `cd projeto && docker compose up --build -d` |
| Reset do banco | `docker compose exec app sh tools/reset_db.sh` (ou `sh tools/reset_db.sh` local) |
| Log (dataset) | `projeto/logs/lab.jsonl` (1 JSON por linha) |
| CORS | liberado (`Access-Control-Allow-Origin: *`, methods, headers); **preflight `OPTIONS` → 204 e é logado** |
| Upstream | Nginx (443/80) → Gunicorn `app:8000` |

### Campos gravados por linha no `lab.jsonl` (log_format `labjson`)
`timestamp`, `timestamp_msec`, `request_method`, `request_uri` (cru, **sem decodificar**),
`server_protocol`, `status`, `body_bytes_sent`, `request_time`, `user_agent`, `referer`,
`remote_addr`, **`request_body`**, `content_type`.
(Headers/cookies **não** são logados — auth via header é invisível ao dataset, por design.)

---

## 2. Páginas HTML (navegação) — blueprint `pages`
| Método | Rota | Descrição | Resposta |
|--------|------|-----------|----------|
| GET | `/` | Home; links para `/docs`, `/docs/SQL/postgres/`, `/forum` | 200 HTML |
| GET | `/docs` | Lista de docs do banco (tabela `docs`) | 200 HTML |
| GET | `/docs/<slug>` | Página de um doc; `slug` **[ALVO]**; desconhecido → **404** | 200/404 HTML |
| GET | `/forum` | Página do fórum (lista + criar dúvida + busca + abrir/comentar) | 200 HTML |

---

## 3. Documentação SQL PostgreSQL (árvore de arquivos + SPA React) — blueprint `docs_sql`
Conteúdo em `projeto/app/content/docs/SQL/postgres/<categoria>/<pagina>.html` (~93 páginas:
`syntax/`, `commands/`, `queries/`, `functions/` (inclui `sleep`=pg_sleep), `operators/`,
`datatypes/`, `indexes/`, `performance/`).

| Método | Rota | Params | Descrição | Resposta |
|--------|------|--------|-----------|----------|
| GET | `/docs/SQL/<path:subpath>` | `subpath` **[ALVO]** | Requisição HTML (`Accept: text/html`) → serve a **shell da SPA React** (`docs_app.html`). Traversal (`..`) → 404. | 200 HTML (shell) / 404 |
| GET | `/api/docs/sql/page?path=` | `path` **[ALVO]** | Dados do doc em JSON (a SPA usa a cada navegação) | 200 JSON |
| GET | `/api/docs/sql/search?q=` | `q` **[ALVO]** | Busca substring nos docs (type-ahead) | 200 JSON |

**`GET /api/docs/sql/page?path=<subpath>` → JSON:**
- Página: `{"type":"page","path":"postgres/queries/where","title":"WHERE","html":"<fragmento>"}`
- Índice/diretório: `{"type":"index","path":"postgres/queries","title":"...","categories":[{name,path}],"pages":[{name,path}]}`
- Traversal/inexistente: `{"type":"notfound"}` (status 404); nunca 400; nunca lê fora de `CONTENT_ROOT`.

**`GET /api/docs/sql/search?q=<termo>` → JSON:** `[{"path":"postgres/queries/where","title":"WHERE","snippet":"..."}]`
(substring case-insensitive; `q` vazio → `[]`; limite ~50). `q` **[ALVO]**, sem 400, path nunca vaza arquivo.

---

## 4. API do Fórum (REST) — blueprint `api_forum`
| Método | Rota | Params/Body | Resposta |
|--------|------|-------------|----------|
| GET | `/api/posts` | query: `tag` **[ALVO]**, `sort` (allowlist), `page`, `per_page` | 200 JSON lista de posts |
| GET | `/api/posts/search?q=` | `q` **[ALVO]** | 200 JSON lista |
| GET | `/api/posts/<id>` | `id` **[ALVO]** no path | 200 JSON post / **404** (id sem match, incl. não-numérico) |
| GET | `/api/posts/<id>/comments` | `id` **[ALVO]** | 200 JSON lista de comentários (com `author`) |
| POST | `/api/posts` | **JSON aninhado** (ver abaixo) | **201** JSON do post criado |
| POST | `/api/comments` | **form** (ver abaixo) | **201** JSON do comentário |
| GET | `/api/tags` | — | 200 JSON lista de tags |

- `sort` **allowlist**: `recent`→`created_at`, `title`→`title`, `id`→`id`. Valor fora da lista →
  default `created_at` (o valor cru é logado mas **nunca** entra na SQL). `page`/`per_page` inválidos → default.

### POST `/api/posts` — corpo **JSON aninhado** (`Content-Type: application/json`)
```json
{
  "post": {
    "title": "string",     // [ALVO]
    "body": "string",      // [ALVO]
    "author": "string",    // [ALVO] nome livre de quem pergunta (opcional)
    "meta": {
      "tags": ["sql", "join"],   // [ALVO] (lista; nomes de tag)
      "source": "web"
    }
  }
}
```
Extrai `post.title`, `post.body`, `post.author`, `post.meta.tags`. Insere parametrizado.
Resposta 201: `{"id","user_id":null,"title","body","created_at","author_name","author"}` (formato do model).
> Observação: a UI do fórum ("Ask a question") hoje cria post via **GraphQL `createPost`** (§7),
> mas este endpoint REST continua ativo e aceita o corpo acima.

### POST `/api/comments` — corpo **form** (`application/x-www-form-urlencoded`)
| Campo | Obrigatório | `[ALVO]` |
|-------|-------------|----------|
| `post_id` | sim | sim |
| `author` | não (nome livre; senão vira persona/anonymous) | sim |
| `body` | sim | sim |

Resposta 201: `{"id","post_id","user_id":null,"body","created_at","author_name"}`.
(Não usa mais `user_id` — o autor é texto livre `author`.)

---

## 5. Usuários / login básico — blueprint `api_users`
| Método | Rota | Body/Params | Resposta |
|--------|------|-------------|----------|
| POST | `/api/login` | `username`, `password` (JSON **ou** form) — ambos **[ALVO]** | **200** `{id,username}` / **401** credencial inválida |
| GET | `/api/users/<id>` | `id` **[ALVO]** | 200 `{id,username,email,bio}` / **404** (id sem match); **nunca** expõe `password_hash` |

- Login compara `sha256("lab-sqli-salt:" + password)` com `users.password_hash` (parametrizado por `username`).
- Credenciais de referência (seed): `alice/alice123`, `bruno/bruno123`, `carla/carla123`, `diego/diego123`, `elena/elena123`.
- `username=' OR '1'='1` → 401 normal (query parametrizada não casa), **sem 400**.
- **Não** cria sessão nem protege nada (é só uma checagem).

---

## 6. Auth simulado (JWT + cookie + sessão) — blueprint `auth`
Gera tráfego de auth **realista e logável**; **não bloqueia** nenhuma rota. O frontend (`auth.js`,
carregado em toda página) faz **auto-login no load** e **re-login periódico randomizado** (username
de um pool + sufixo; body às vezes com `device`/`locale`; intervalo com jitter 30–90s) + **refresh** a cada ~5 min.

| Método | Rota | Body | Resposta |
|--------|------|------|----------|
| POST | `/api/auth/login` | JSON (ou form): `{"username": "...", "auto": true, "device"?, "locale"?}` — `username` **[ALVO]** | 200 `{token, token_type:"Bearer", expires_in:900, user:{...}}` + **Set-Cookie** `session` e `auth_token` (HttpOnly, SameSite=Lax) |
| POST | `/api/auth/refresh` | token via body/cookie (senão guest) | 200 novo `{token,...}` |
| GET | `/api/auth/me` | token/cookie | 200 `{user:{username}, authenticated:bool}` |

- `expires_in` = 900s. JWT assinado com HMAC (`JWT_SECRET` de lab). Sessões em tabela `sessions`.
- Qualquer `username` é aceito (sem filtro). O `Authorization: Bearer <token>` enviado nas demais
  requisições **não** é logado (por design).

---

## 7. GraphQL — `POST /graphql` (Ariadne, schema-first) — introspecção habilitada
Aceita forma **inline** e **com variáveis**. Corpo: `{"query":"...","variables":{...}}`.
Usado de verdade pela SPA de docs (painel "related posts" via `searchPosts`) e pelo form
"Ask a question" (mutation `createPost`).

### Schema
```graphql
type Post    { id: ID!, title: String!, body: String!, author: String!, createdAt: String! }
type Doc     { slug: String!, title: String!, content: String! }
type Comment { id: ID!, postId: ID!, author: String!, body: String!, createdAt: String! }

type Query {
  post(id: ID!): Post              # [ALVO] em id (argumento e variável)
  searchPosts(q: String!): [Post!]!# [ALVO] em q
  docs: [Doc!]!
}

type Mutation {
  createPost(title: String!, body: String!, author: String, tags: [String!]): Post!   # todos [ALVO]
  addComment(postId: ID!, author: String, body: String!): Comment!                     # todos [ALVO]
}
```
- Todas as variáveis/argumentos são **[ALVO]**: usados como parâmetro nos models (parametrizado),
  **sem filtro**, **sem 400**; vão logados no `request_body` do `POST /graphql`.
- Resolvers mapeiam `created_at`→`createdAt`.

### Exemplos
- Query inline: `{"query":"{ post(id:\"1\"){ title author } }"}`
- Query c/ variáveis: `{"query":"query($q:String!){ searchPosts(q:$q){ id title } }","variables":{"q":"where"}}`
- Mutation createPost: `{"query":"mutation($t:String!,$b:String!,$a:String,$tags:[String!]){ createPost(title:$t, body:$b, author:$a, tags:$tags){ id title author } }","variables":{"t":"...","b":"...","a":"Eve","tags":["sql"]}}`
- Mutation addComment: `{"query":"mutation($p:ID!,$a:String,$b:String!){ addComment(postId:$p, author:$a, body:$b){ id author body } }","variables":{"p":"31","a":"Trudy","b":"..."}}`

---

## 8. Esquema do banco (SQLite) — para contexto
```
users(id, username UNIQUE, email, password_hash, bio)
posts(id, user_id NULLABLE→users, title, body, created_at, author_name)
comments(id, post_id→posts, user_id NULLABLE→users, body, created_at, author_name)
tags(id, name UNIQUE)               -- sql, join, where, select, performance, sqlite, graphql
post_tags(post_id, tag_id)          -- PK composta
docs(id, slug UNIQUE, title, content)  -- slugs: select-statement, where-clause, inner-join, union-operator, order-by, group-by-having
sessions(id, username, created_at, expires_at)   -- auth simulado
```
Seed: 5 users + 12 personas (Q&A), 54 posts (30 base + 24 perguntas Q&A, todos com `author_name`
genérico/persona), 60 comments, 7 tags, 6 docs. Reset via `tools/reset_db.sh` (schema + seed + seed_forum).

---

## 9. Fluxos principais (para uma IA reproduzir/entender)

### 9.1 Ao abrir qualquer página (auto-auth)
1. `auth.js` dispara `POST /api/auth/login` (body com `username` aleatório) → recebe JWT + cookies.
2. Re-login periódico randomizado (jitter 30–90s) + `POST /api/auth/refresh` a cada ~5 min.
3. As demais requisições levam `Authorization: Bearer` (não logado).

### 9.2 Docs SQL (SPA React)
1. Navegar para `/docs/SQL/postgres/...` → servidor entrega a **shell** React.
2. A SPA lê o path e busca `GET /api/docs/sql/page?path=<subpath>` (por navegação, sem reload).
3. Caixa de busca (índices) → `GET /api/docs/sql/search?q=` (type-ahead).
4. Cada página aberta dispara `POST /graphql searchPosts(q:<tópico>)` (painel "related posts").

### 9.3 Fórum (Q&A)
1. `GET /forum` → lista via `GET /api/posts?tag=&sort=&page=&per_page=`.
2. Controles: ordenação (`sort`), filtro por tag (`/api/tags` → `?tag=`), paginação (`?page=`),
   busca type-ahead (`GET /api/posts/search?q=`).
3. **Criar dúvida** ("Ask a question", campo *Your name*) → **`POST /graphql createPost`** (mutation).
4. **Abrir post** → `GET /api/posts/<id>` + `GET /api/posts/<id>/comments` (mostra respostas por `author`).
5. **Responder** (campo *Your name* + texto) → `POST /api/comments` (form: `post_id`, `author`, `body`).

### 9.4 Superfícies de escrita (para o dataset)
- REST: `POST /api/posts` (JSON aninhado), `POST /api/comments` (form).
- GraphQL: `mutation createPost`, `mutation addComment`.
- Auth: `POST /api/auth/login`, `POST /api/auth/refresh` (bodies variados).

---

## 10. Resumo por método (para gerar tráfego)
- **GET** — `/`, `/docs`, `/docs/<slug>`, `/forum`, `/docs/SQL/<path>`, `/api/docs/sql/page?path=`,
  `/api/docs/sql/search?q=`, `/api/docs/search?q=`, `/api/posts?...`, `/api/posts/search?q=`,
  `/api/posts/<id>`, `/api/posts/<id>/comments`, `/api/tags`, `/api/users/<id>`, `/api/auth/me`.
- **POST** — `/api/posts` (JSON), `/api/comments` (form), `/api/login` (JSON/form),
  `/api/auth/login`, `/api/auth/refresh`, `/graphql` (queries e mutations).
- **OPTIONS** — qualquer rota (preflight CORS → 204, logado).
- **301** — qualquer rota via HTTP (`8080`) → HTTPS.

### Vetores `[ALVO]` por tipo (onde injetar payloads)
- **Query string:** `?q=`, `?tag=`, `?sort=`, `?page=`, `?per_page=`, `?path=`.
- **Path param:** `/docs/<slug>`, `/docs/SQL/<path>`, `/api/posts/<id>`, `/api/users/<id>`, `/api/posts/<id>/comments`.
- **Body JSON:** `post.title/body/author/meta.tags` (`/api/posts`); `username/password` (`/api/login`); `username` (`/api/auth/login`).
- **Body form:** `post_id/author/body` (`/api/comments`).
- **Variáveis GraphQL:** `id`, `q`, `title`, `body`, `author`, `tags`, `postId`.

> Em todos, a resposta é normal (200/201/401/404 conforme o caso), **nunca 400 por caractere**, e o
> payload aparece **cru** no `lab.jsonl` (query em `request_uri`, corpo em `request_body`).
