# The Curious Kitchen Wiki — Project 2

Project 2 is an isolated English-language variant of the SQLi Dataset Lab. The application is a generic cooking and recipe wiki with a community forum. It remains parameterized and non-exploitable by design while preserving request input in structured Nginx logs.

## Research purpose

Legitimate pages and conversations intentionally use ambiguous SQL-domain words such as `select`, `where`, `union`, `sleep`, `join`, `group by`, and `order by` as normal English. This creates challenging benign examples without writing SQL statements or attack payloads.

Examples:

- “Which apples would you select for pie?”
- “Where should the dough sleep overnight?”
- “Can I make a union of these two sauces?”

## Run Project 2

Project 2 has its own Compose identity, database, volumes, network, and host ports, so it can run beside Project 1.

```sh
cd "Projeto 2"
docker compose up --build -d app nginx
```

Open:

- `https://localhost:8444/`
- `https://localhost:8444/docs`
- `https://localhost:8444/recipes/`
- `https://localhost:8444/select/recipes/`
- `https://localhost:8444/forum`

Port `8081` redirects to HTTPS on `8444`.

## Content layout

The cooking SPA uses SQL-adjacent English terms only where each term has a
clear culinary meaning:

- `/select/recipes/` — choosing recipes
- `/where/ingredients/` — locating and storing ingredients
- `/union/flavors/` — combining flavors and cuisines
- `/sleep/dough/` — resting dough
- `/join/pairings/` — pairing dishes and sauces
- `/group-by/meal-prep/` — organizing meal preparation
- `/order-by/cooking-time/` — sequencing dishes by cooking time

The old artificial `/docs/SQL/...` namespace is intentionally not exposed.

All displayed articles, seeded questions, answers, user profiles, tags, and UI labels are in English and concern cooking.

## Benign content generation

Future content agents must follow `tools/traffic/CONTENT_POLICY.md` and `tools/traffic/agent_io/INSTRUCOES.md`. They create natural cooking questions and answers, use SQL-domain words only when they fit ordinary English, and must not emit SQL syntax, payloads, security instructions, or database advice.

The browser generator defaults to Project 2 at `https://localhost:8444` and visits the cooking wiki route.

Prepare and run the high-volume benign campaign locally with:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-traffic.txt
CAMPAIGN_PY="$PWD/.venv/bin/python" .venv/bin/python tools/traffic/campaign.py
```

The campaign uses the host Chrome without downloading another browser. Live agents are
optional and are intended only for small qualitative samples; all agent output is checked
for English culinary context before use. The high-volume default uses varied curated
English fallbacks so it does not depend on an interactive agent terminal.

## Logging

Nginx writes the current structured JSONL request log to `logs/lab.jsonl`. This copy starts with a clean database and clean runtime logs so future Project 2 traffic cannot be confused with the Project 1 dataset.

The completed benign campaign artifact is `log/benigno.jsonl`. After consolidation,
`logs/lab.jsonl` is reopened empty so there is only one stored copy of the campaign data.

## Isolated Kali toolbox

The optional `kali-tools` profile remains isolated in Docker and targets only Project 2's internal `https://nginx` service. No offensive tools are installed on the host.

The Project 2 attack campaign uses read-only search/authentication vectors so payloads
are captured in request URIs or JSON bodies without being saved as forum content. Its
vectors cover `/api/posts/search`, `/api/wiki/search`, `/api/auth/login`, and `/graphql`.
Execution is doubly gated by `--execute` and
`LAB_ATTACK_CONFIRM=project2-phase26`; both the wrapper and injector refuse any target
other than the exact internal URL `https://nginx`.

Plan or run the authorized local-lab campaign with:

```sh
python3 tools/attack/attack_campaign.py
python3 tools/attack/attack_campaign.py --execute
```

The completed request artifacts are kept as `log/benigno.jsonl` and
`log/malicioso.jsonl`; the live `logs/lab.jsonl` is reopened empty after consolidation.
