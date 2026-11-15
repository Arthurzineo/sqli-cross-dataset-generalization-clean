#!/usr/bin/env bash
# Launcher: sqlmap contra um POST de login do OJS configurado localmente.
# Ataca os campos do formulario (username, password, source). csrfToken tratado
# como token anti-CSRF (nao injetado). User-Agent = Chrome fixo (pedido do usuario).
# Conformidade: sem --os-shell/--os-cmd/--file-*/--dump. Somente deteccao.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1
source "$ROOT/scripts/common.sh"
PROFILE=aggressive
umask 077
require_authorization

OUT=output/posttest/sqlmap
mkdir -p "$OUT/traffic" "$OUT/data"

UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
TARGETS_FILE="${TARGETS_FILE:-config/targets.txt}"
[[ -r "$TARGETS_FILE" ]] || { echo "Crie $TARGETS_FILE a partir de config/targets.txt.example" >&2; exit 2; }
URL="$(grep -Ev '^[[:space:]]*(#|$)' "$TARGETS_FILE" | head -n 1)"
[[ -n "$URL" ]] || { echo "Nenhum alvo em $TARGETS_FILE" >&2; exit 2; }
SCOPE_FILE="${SCOPE_FILE:-config/scope.txt}"
[[ -r "$SCOPE_FILE" ]] || { echo "Crie $SCOPE_FILE a partir de config/scope.txt.example" >&2; exit 2; }
is_target_in_scope "$URL" "$SCOPE_FILE" || die "alvo fora do escopo: $URL" "$EX_UNAUTHORIZED"
: "${OJS_CSRF_TOKEN:?Defina OJS_CSRF_TOKEN no ambiente}"
: "${OJS_COOKIE:?Defina OJS_COOKIE no ambiente}"
BODY="csrfToken=${OJS_CSRF_TOKEN}&source=&username=test&password=test&remember=1"
COOKIE="$OJS_COOKIE"

sqlmap -u "$URL" \
  --data="$BODY" \
  --cookie="$COOKIE" \
  --user-agent="$UA" \
  -p "username,password,source" \
  --skip="csrfToken,remember" \
  --level=5 --risk=3 --technique=BEUSTQ \
  --batch --answers="quit=N,crack=N,dict=N,continue=Y,follow=N,keep=N" \
  --threads=8 --timeout=30 --retries=2 \
  --parse-errors --disable-coloring \
  -t "$OUT/traffic/post_signIn.traffic" \
  --output-dir="$OUT/data" \
  --flush-session --fresh-queries
