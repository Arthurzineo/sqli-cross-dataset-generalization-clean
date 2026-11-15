#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1
TARGETS_FILE="${TARGETS_FILE:-config/targets.txt}"
[[ -r "$TARGETS_FILE" ]] || { echo "Crie $TARGETS_FILE a partir de config/targets.txt.example" >&2; exit 2; }
grep -Ev '^[[:space:]]*(#|$)' "$TARGETS_FILE" | head -n 1 > /tmp/one-url.txt
[[ -s /tmp/one-url.txt ]] || { echo "Nenhum alvo em $TARGETS_FILE" >&2; exit 2; }

echo "=== via ffuf-sqli-sweep (exec) ==="
DRY_RUN=1 RUN_ID=tt1 PROFILE=safe bash scripts/ffuf-sqli-sweep.sh --targets /tmp/one-url.txt --scope config/scope.txt --profile safe > /tmp/tt1.log 2>&1
echo "ocorrencias_do_alvo=$(grep -Fcf /tmp/one-url.txt /tmp/tt1.log)"

echo "=== via ffuf-sweep direto (RUN_FFUF_SQLI=1) ==="
DRY_RUN=1 RUN_ID=tt2 PROFILE=safe RUN_FFUF_SQLI=1 RUN_FFUF_PATHS=0 bash scripts/ffuf-sweep.sh --targets /tmp/one-url.txt --scope config/scope.txt --profile safe > /tmp/tt2.log 2>&1
echo "ocorrencias_do_alvo=$(grep -Fcf /tmp/one-url.txt /tmp/tt2.log)"
