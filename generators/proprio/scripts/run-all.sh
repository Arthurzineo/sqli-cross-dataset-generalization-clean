#!/usr/bin/env bash
# =============================================================================
# run-all.sh — orquestrador. Valida ambiente, cria RUN_ID e dispara cada
# ferramenta em job separado respeitando MAX_PARALLEL_JOBS.
#
#   ./scripts/run-all.sh --profile aggressive \
#     --targets ./config/targets.txt --scope ./config/scope.txt \
#     --tools ffuf,ffuf-sqli,sqlmap
#
# XSS e opt-in: inclua dalfox,xsstrike em --tools para rodar apos SQLi. Para
# usar a wordlist SQLi local por ffuf, inclua ffuf-sqli na fase SQLi. Para uma
# janela posterior, reutilize os endpoints com:
#   --resume --run-id <mesmo-run-id> --tools dalfox,xsstrike
#
# Também: --only <tool> | --exclude <tool> | --target-id <id> |
#         --dry-run | --print-commands | --resume | --run-id <id>
# =============================================================================
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

TOOL_NAME="orchestrator"
PROFILE="${PROFILE:-safe}"
TOOLS="ffuf,sqlmap"
SCOPE_FILE=""; TARGETS_FILE=""; ONLY=""; EXCLUDE=""; TARGET_ID=""; RESUME=0
RUN_ID_PROVIDED=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)        PROFILE="$2";        shift 2 ;;
    --targets)        TARGETS_FILE="$2";   shift 2 ;;
    --scope)          SCOPE_FILE="$2";     shift 2 ;;
    --tools)          TOOLS="$2";          shift 2 ;;
    --only)           ONLY="$2";           shift 2 ;;
    --exclude)        EXCLUDE="$2";        shift 2 ;;
    --target-id)      TARGET_ID="$2";      shift 2 ;;
    --run-id)         RUN_ID="$2"; RUN_ID_PROVIDED=1; shift 2 ;;
    --dry-run)        DRY_RUN=1;           shift ;;
    --print-commands) PRINT_COMMANDS=1;    shift ;;
    --resume)         RESUME=1;            shift ;;
    -h|--help)        grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "argumento desconhecido: $1" "$EX_USAGE" ;;
  esac
done

export PROFILE
load_configuration "$ROOT"
SCOPE_FILE="${SCOPE_FILE:-$ROOT/config/scope.txt}"
TARGETS_FILE="${TARGETS_FILE:-$ROOT/config/targets.txt}"

require_authorization
require_file "$SCOPE_FILE"
require_file "$TARGETS_FILE"
validate_integer MAX_PARALLEL_JOBS "${MAX_PARALLEL_JOBS:-4}" 1 64

RUN_ID="${RUN_ID:-$(new_run_id)}"
OUTDIR="$(create_run_directory "$ROOT/output" "$RUN_ID")"
LOGDIR="$ROOT/logs/$RUN_ID"; mkdir -p "$LOGDIR"
check_disk_space "$OUTDIR"

if [[ "$RESUME" == "1" && "$RUN_ID_PROVIDED" != "1" ]]; then
  die "--resume exige --run-id para reutilizar um run existente." "$EX_USAGE"
fi

log_info "run-all iniciado: RUN_ID=$RUN_ID profile=$PROFILE tools=$TOOLS dry_run=${DRY_RUN:-0}"
"$HERE/collect-metadata.sh" --run-id "$RUN_ID" --profile "$PROFILE" || log_warn "metadata falhou"

# Seleção de ferramentas (--only/--exclude aplicados sobre --tools)
declare -a SELECTED=()
IFS=',' read -r -a requested <<< "${ONLY:-$TOOLS}"
for t in "${requested[@]}"; do
  [[ -n "$EXCLUDE" && ",$EXCLUDE," == *",$t,"* ]] && continue
  case "$t" in
    ffuf|ffuf-sqli|sqlmap|dalfox|xsstrike) ;;
    *) die "ferramenta desconhecida: $t" "$EX_USAGE" ;;
  esac
  SELECTED+=("$t")
done

child_pids=()
cleanup() {
  log_warn "encerrando: propagando sinal aos jobs filhos"
  for pid in "${child_pids[@]:-}"; do kill -TERM "$pid" 2>/dev/null || true; done
  wait 2>/dev/null || true
  exit "$EX_INTERRUPT"
}
trap cleanup INT TERM

# Executa um sweep em foreground; devolve o exit code do script.
run_tool() {
  local tool="$1" targets="$2" script="$HERE/${1}-sweep.sh"
  [[ -f "$script" ]] || { log_warn "script ausente para $tool"; return 0; }
  local args=(--targets "$targets" --scope "$SCOPE_FILE" --profile "$PROFILE")
  [[ "${DRY_RUN:-0}" == "1" ]] && args+=(--dry-run)
  log_info "dispatch: $tool (targets=$targets)"
  RUN_ID="$RUN_ID" PRINT_COMMANDS="${PRINT_COMMANDS:-0}" \
    bash "$script" "${args[@]}" > "$LOGDIR/${tool}.log" 2>&1
}

# ffuf é DESCOBERTA: roda primeiro e seus endpoints alimentam os demais tools.
declare -a DISCOVERY=() SQLI=() XSS=()
for t in "${SELECTED[@]}"; do
  case "$t" in
    ffuf) DISCOVERY+=("$t") ;;
    ffuf-sqli|sqlmap) SQLI+=("$t") ;;
    dalfox|xsstrike) XSS+=("$t") ;;
  esac
done

EFFECTIVE_TARGETS="$TARGETS_FILE"
combined="$OUTDIR/combined-targets.txt"

# 1) Fase de descoberta (ffuf), sequencial e antes de tudo.
if [[ "$RESUME" == "1" ]]; then
  (( ${#DISCOVERY[@]} == 0 )) || die "--resume nao aceita ffuf; use o combined-targets existente." "$EX_USAGE"
  require_file "$combined"
  EFFECTIVE_TARGETS="$combined"
  log_info "resume: reutilizando alvos descobertos em $combined"
elif (( ${#DISCOVERY[@]} > 0 )); then
  run_tool ffuf "$TARGETS_FILE" || log_warn "ffuf terminou com erro (veja $LOGDIR/ffuf.log)"
  discovered="$OUTDIR/ffuf/discovered-endpoints.txt"
  # Alvos combinados = originais (sem comentários) + endpoints descobertos, dedup.
  {
    grep -vE '^[[:space:]]*(#|$)' "$TARGETS_FILE" 2>/dev/null || true
    [[ -f "$discovered" ]] && cat "$discovered"
  } | awk 'NF' | sort -u > "$combined"
  chmod 600 "$combined"
  n_disc=0; [[ -f "$discovered" ]] && n_disc="$(wc -l < "$discovered")"
  n_comb="$(wc -l < "$combined")"
  log_info "descoberta: $n_disc endpoints; alvos combinados para ataque: $n_comb"
  EFFECTIVE_TARGETS="$combined"
fi

# 2) SQLi termina antes de iniciar qualquer fase XSS selecionada.
for tool in "${SQLI[@]}"; do
  log_info "fase SQLi: $tool"
  run_tool "$tool" "$EFFECTIVE_TARGETS" || log_warn "$tool terminou com erro (veja $LOGDIR/${tool}.log)"
done

# 3) XSS e opt-in. Dalfox e XSStrike podem executar em paralelo entre si,
# somente depois de SQLi, ou em uma janela posterior com --resume.
child_pids=(); running=0
for tool in "${XSS[@]}"; do
  log_info "fase XSS: $tool"
  run_tool "$tool" "$EFFECTIVE_TARGETS" &
  child_pids+=($!)
  running=$((running + 1))
  if (( running >= ${MAX_PARALLEL_JOBS:-4} )); then
    wait -n 2>/dev/null || true
    running=$((running - 1))
  fi
done

wait || true
log_info "run-all concluído: RUN_ID=$RUN_ID (veja $LOGDIR e $OUTDIR)"
