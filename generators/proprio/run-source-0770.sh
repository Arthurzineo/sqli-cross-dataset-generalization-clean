#!/usr/bin/env bash
# Launcher: ataca a URL com parametro 'source' (setLocale) via POST-only,
# passes 07-70 + tampers (pula 01-06). User-Agent = Chrome fixo (defaults.env).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1
source "$ROOT/scripts/common.sh"
PROFILE=aggressive
umask 077
require_authorization

TF=config/targets-source0770.txt
TARGETS_FILE="${TARGETS_FILE:-config/targets.txt}"
[[ -r "$TARGETS_FILE" ]] || { echo "Crie $TARGETS_FILE a partir de config/targets.txt.example" >&2; exit 2; }
grep -Ev '^[[:space:]]*(#|$)' "$TARGETS_FILE" | head -n 1 > "$TF"
[[ -s "$TF" ]] || { echo "Nenhum alvo em $TARGETS_FILE" >&2; exit 2; }

export RUN_ID=source0770post
export PROFILE=aggressive
export PASS_SKIP='^0[1-6]_'
export METHOD_ONLY=POST

bash scripts/sqlmap-sweep.sh --targets "$TF" --scope config/scope.txt --profile aggressive
