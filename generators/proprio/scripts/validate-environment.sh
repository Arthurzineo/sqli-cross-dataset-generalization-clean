#!/usr/bin/env bash
# =============================================================================
# validate-environment.sh — checagens estáticas de ambiente (sem rede).
# Verifica autorização, escopo, alvos, dependências e permissões, e reporta
# a versão das ferramentas SEM executá-las contra qualquer alvo.
# =============================================================================
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

TOOL_NAME="validate-environment"

load_configuration "$ROOT"

SCOPE_FILE="${SCOPE_FILE:-$ROOT/config/scope.txt}"
TARGETS_FILE="${TARGETS_FILE:-$ROOT/config/targets.txt}"

problems=0
note()  { log_info "$*"; }
fail()  { log_error "$*"; problems=$((problems + 1)); }

note "verificando dependências básicas..."
for c in bash python3 sha256sum awk grep sed date; do
  if command -v "$c" >/dev/null 2>&1; then note "ok: $c"; else fail "faltando: $c"; fi
done

note "verificando ferramentas ofensivas (apenas presença, sem executar)..."
for varname in SQLMAP_BIN FFUF_BIN DALFOX_BIN XSSTRIKE_BIN; do
  bin="${!varname:-}"
  [[ -z "$bin" ]] && { fail "$varname não definido"; continue; }
  if command -v "$bin" >/dev/null 2>&1; then note "ok: $varname=$bin"; else log_warn "ausente: $varname=$bin (instale antes de rodar)"; fi
done

note "verificando autorização..."
if [[ "${AUTHORIZED_SECURITY_TESTING:-}" == "YES" ]]; then
  note "ok: AUTHORIZED_SECURITY_TESTING=YES"
else
  log_warn "AUTHORIZED_SECURITY_TESTING != YES (execução real ficará bloqueada)"
fi

note "verificando escopo ($SCOPE_FILE)..."
if [[ -f "$SCOPE_FILE" && -s "$SCOPE_FILE" ]]; then note "ok: escopo presente"; else fail "escopo ausente ou vazio: $SCOPE_FILE"; fi

note "verificando alvos ($TARGETS_FILE)..."
if [[ -f "$TARGETS_FILE" ]]; then note "ok: alvos presentes"; else log_warn "alvos ausentes: $TARGETS_FILE"; fi

note "verificando permissões de saída..."
check_output_permissions "$ROOT/output" && note "ok: output/ gravável"
check_output_permissions "$ROOT/logs"   && note "ok: logs/ gravável"

if (( problems > 0 )); then
  die "$problems problema(s) encontrado(s) na validação de ambiente." "$EX_CONFIG"
fi
log_info "ambiente validado sem erros."
