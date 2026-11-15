#!/usr/bin/env bash
# =============================================================================
# ffuf-sqli-sweep.sh - executa somente a wordlist SQLi bruta local via ffuf.
#
#   ./scripts/ffuf-sqli-sweep.sh --targets ./config/targets.txt \
#      --scope ./config/scope.txt --profile safe
#
# Usa FFUF_SQLI_RAW_WORDLIST, que por padrao aponta para
# wordlists/custom/sqli.txt. FFUF_VALUE_PARAM define o parametro de consulta
# que recebera os valores (padrao: ffuf_value).
#
# Este adaptador preserva as validacoes de autorizacao, escopo, limites,
# redacao e ledger de ffuf-sweep.sh. Nao executa caminhos, descoberta, XSS ou
# variantes codificadas da lista SQLi.
# Compatibilidade: Bash 4.4+.
# =============================================================================
set -Eeuo pipefail
umask 077

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      awk '
        /^# =+/ { if (seen++) exit; next }
        seen { sub(/^# ?/, ""); print }
      ' "$0"
      exit 0
      ;;
  esac
done

# Mantem os artefatos da janela SQLi separados dos artefatos de descoberta.
RUN_ID="${RUN_ID:-$(new_run_id)}"
OUTDIR="${OUTDIR:-$ROOT/output/$RUN_ID/ffuf-sqli}"
export RUN_ID OUTDIR

# Forca apenas o job SQLi raw. FFUF_SQLI_RAW_WORDLIST e propositalmente
# preservada para que .env ou o ambiente possam apontar para outra lista local.
export RUN_FFUF_PATHS=0
export RUN_FFUF_PARAMETERS=0
export RUN_FFUF_VALUES=0
export RUN_FFUF_HEADERS=0
export RUN_FFUF_COOKIES=0
export RUN_FFUF_FORM=0
export RUN_FFUF_JSON=0
export RUN_FFUF_SQLI=1
export RUN_FFUF_XSS=0
export RUN_FFUF_METHODS=0
export RUN_FFUF_CONTENT_TYPES=0
export RUN_FFUF_COMBINED=0

exec bash "$HERE/ffuf-sweep.sh" "$@"
