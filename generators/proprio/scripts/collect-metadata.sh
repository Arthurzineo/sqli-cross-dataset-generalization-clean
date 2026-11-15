#!/usr/bin/env bash
# =============================================================================
# collect-metadata.sh — gera metadata.json de uma execução (sem segredos).
#   ./scripts/collect-metadata.sh --run-id <RUN_ID> [--profile <p>]
# Não registra senhas, tokens, cookies completos, Authorization ou API keys.
# =============================================================================
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

TOOL_NAME="metadata"
RUN_ID=""; PROFILE="${PROFILE:-safe}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id)  RUN_ID="$2";  shift 2 ;;
    --profile) PROFILE="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "argumento desconhecido: $1" "$EX_USAGE" ;;
  esac
done

[[ -n "$RUN_ID" ]] || die "--run-id é obrigatório" "$EX_USAGE"
export PROFILE
load_configuration "$ROOT"

outdir="$ROOT/output/$RUN_ID"
mkdir -p "$outdir"
meta="$outdir/metadata.json"

tool_version() { command -v "$1" >/dev/null 2>&1 && printf 'present' || printf 'unknown'; }

cat > "$meta" <<JSON
{
  "run_id": "$RUN_ID",
  "started_at": "$(date +%Y-%m-%dT%H:%M:%S%z)",
  "profile": "$PROFILE",
  "targets_file": "${TARGETS_FILE:-./config/targets.txt}",
  "scope_file": "${SCOPE_FILE:-./config/scope.txt}",
  "hostname": "$(hostname 2>/dev/null || echo unknown)",
  "user": "${USER:-${USERNAME:-unknown}}",
  "git_commit": "$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo optional)",
  "tools": {
    "sqlmap": "$(tool_version "${SQLMAP_BIN:-sqlmap}")",
    "ffuf": "$(tool_version "${FFUF_BIN:-ffuf}")",
    "dalfox": "$(tool_version "${DALFOX_BIN:-dalfox}")",
    "xsstrike": "$(tool_version "${XSSTRIKE_BIN:-xsstrike}")"
  }
}
JSON

chmod 600 "$meta"
log_info "metadata gravado em $meta"
