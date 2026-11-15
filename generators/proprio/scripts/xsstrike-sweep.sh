#!/usr/bin/env bash
# =============================================================================
# xsstrike-sweep.sh - bateria de XSStrike por alvo (laboratorio autorizado).
#
#   ./scripts/xsstrike-sweep.sh --targets ./config/targets.txt \
#                                --scope ./config/scope.txt \
#                                --profile safe
#
# XSStrike e acionado em jobs separados para analise refletida, fuzzer,
# descoberta de parametros, variacao de encoding e corpos POST/JSON informados
# pelo operador. O crawler interno fica desligado por padrao e exige uma
# confirmacao explicita, pois a ferramenta nao expoe teto confiavel de paginas.
#
# Compatibilidade: Bash 4.4+. DRY_RUN somente compoe comandos redigidos e nao
# executa XSStrike nem faz chamadas de rede.
# =============================================================================
set -uo pipefail
umask 077

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

TOOL_NAME="xsstrike"

# ------------------------------- ARGUMENTOS ---------------------------------
SCOPE_FILE=""; TARGETS_FILE=""; PROFILE="${PROFILE:-safe}"; CLI_DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --targets) TARGETS_FILE="$2"; shift 2 ;;
    --scope)   SCOPE_FILE="$2";   shift 2 ;;
    --profile) PROFILE="$2";      shift 2 ;;
    --dry-run) CLI_DRY_RUN=1;      shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "argumento desconhecido: $1" "$EX_USAGE" ;;
  esac
done

export PROFILE
load_configuration "$ROOT"
SCOPE_FILE="${SCOPE_FILE:-$ROOT/config/scope.txt}"
TARGETS_FILE="${TARGETS_FILE:-$ROOT/config/targets.txt}"
XSSTRIKE="${XSSTRIKE_BIN:-xsstrike}"
DRY_RUN="${DRY_RUN:-0}"
[[ "$CLI_DRY_RUN" == "1" ]] && DRY_RUN=1

# ------------------------------- CONFIGURACAO -------------------------------
THREADS="${THREADS:-2}"
REQUEST_RATE="${REQUEST_RATE:-0}"
DELAY_MS="${DELAY_MS:-0}"
HTTP_TIMEOUT="${HTTP_TIMEOUT:-30}"
RETRIES="${RETRIES:-3}"
PRINT_COMMANDS="${PRINT_COMMANDS:-0}"
ENABLE_SAMPLE_HEADERS="${ENABLE_SAMPLE_HEADERS:-0}"
USER_AGENT="${USER_AGENT:-TCC-Web-Sample-Generator/0.1}"

MAX_REQUESTS_PER_JOB="${MAX_REQUESTS_PER_JOB:-50000}"
MAX_TOTAL_REQUESTS="${MAX_TOTAL_REQUESTS:-500000}"
MAX_JOB_SECONDS="${MAX_JOB_SECONDS:-7200}"
MAX_RUN_SECONDS="${MAX_RUN_SECONDS:-28800}"
MAX_CRAWL_DEPTH="${MAX_CRAWL_DEPTH:-5}"
MAX_CRAWL_URLS="${MAX_CRAWL_URLS:-10000}"

XSSTRIKE_PROXY="${XSSTRIKE_PROXY:-${PROXY:-}}"
XSSTRIKE_FORM_DATA="${XSSTRIKE_FORM_DATA:-}"
XSSTRIKE_JSON_DATA="${XSSTRIKE_JSON_DATA:-}"
XSSTRIKE_SEEDS_FILE="${XSSTRIKE_SEEDS_FILE:-}"
XSSTRIKE_CRAWL_SCOPE_ACK="${XSSTRIKE_CRAWL_SCOPE_ACK:-NO}"
XSSTRIKE_CORE_REQUEST_BUDGET="${XSSTRIKE_CORE_REQUEST_BUDGET:-100}"
XSSTRIKE_FUZZ_REQUEST_BUDGET="${XSSTRIKE_FUZZ_REQUEST_BUDGET:-500}"
XSSTRIKE_PARAM_REQUEST_BUDGET="${XSSTRIKE_PARAM_REQUEST_BUDGET:-250}"

COOKIE="${COOKIE:-}"
HEADER_FILE="${HEADERS_FILE:-}"
RUN_XSSTRIKE_REFLECTED="${RUN_XSSTRIKE_REFLECTED:-1}"
RUN_XSSTRIKE_FUZZER="${RUN_XSSTRIKE_FUZZER:-0}"
RUN_XSSTRIKE_PARAMS="${RUN_XSSTRIKE_PARAMS:-0}"
RUN_XSSTRIKE_ENCODE="${RUN_XSSTRIKE_ENCODE:-1}"
RUN_XSSTRIKE_FORM="${RUN_XSSTRIKE_FORM:-0}"
RUN_XSSTRIKE_JSON="${RUN_XSSTRIKE_JSON:-0}"
RUN_XSSTRIKE_CRAWL="${RUN_XSSTRIKE_CRAWL:-0}"

# ------------------------------- VALIDACAO ---------------------------------
require_authorization
require_command python3
require_command sha256sum
require_command awk
require_command grep
require_command date
require_file "$SCOPE_FILE"
require_file "$TARGETS_FILE"
if [[ "$DRY_RUN" != "1" ]]; then
  command -v "$XSSTRIKE" >/dev/null 2>&1 || die "xsstrike nao encontrado: $XSSTRIKE" "$EX_UNAVAILABLE"
fi

case "$PRINT_COMMANDS" in 0|1) ;; *) die "PRINT_COMMANDS invalido: $PRINT_COMMANDS" "$EX_CONFIG" ;; esac
case "$ENABLE_SAMPLE_HEADERS" in 0|1) ;; *) die "ENABLE_SAMPLE_HEADERS invalido: $ENABLE_SAMPLE_HEADERS" "$EX_CONFIG" ;; esac
case "$XSSTRIKE_CRAWL_SCOPE_ACK" in YES|NO) ;; *) die "XSSTRIKE_CRAWL_SCOPE_ACK invalido" "$EX_CONFIG" ;; esac
validate_integer THREADS "$THREADS" 1 64
validate_integer REQUEST_RATE "$REQUEST_RATE" 0
validate_integer DELAY_MS "$DELAY_MS" 0
validate_integer HTTP_TIMEOUT "$HTTP_TIMEOUT" 1
validate_integer RETRIES "$RETRIES" 0
validate_integer MAX_REQUESTS_PER_JOB "$MAX_REQUESTS_PER_JOB" 1
validate_integer MAX_TOTAL_REQUESTS "$MAX_TOTAL_REQUESTS" 1
validate_integer MAX_JOB_SECONDS "$MAX_JOB_SECONDS" 1
validate_integer MAX_RUN_SECONDS "$MAX_RUN_SECONDS" 1
validate_integer MAX_CRAWL_DEPTH "$MAX_CRAWL_DEPTH" 0
validate_integer MAX_CRAWL_URLS "$MAX_CRAWL_URLS" 1
validate_integer XSSTRIKE_CORE_REQUEST_BUDGET "$XSSTRIKE_CORE_REQUEST_BUDGET" 1 "$MAX_REQUESTS_PER_JOB"
validate_integer XSSTRIKE_FUZZ_REQUEST_BUDGET "$XSSTRIKE_FUZZ_REQUEST_BUDGET" 1 "$MAX_REQUESTS_PER_JOB"
validate_integer XSSTRIKE_PARAM_REQUEST_BUDGET "$XSSTRIKE_PARAM_REQUEST_BUDGET" 1 "$MAX_REQUESTS_PER_JOB"

if [[ "$RUN_XSSTRIKE_CRAWL" == "1" ]]; then
  [[ "$XSSTRIKE_CRAWL_SCOPE_ACK" == "YES" ]] || die \
    "RUN_XSSTRIKE_CRAWL=1 exige XSSTRIKE_CRAWL_SCOPE_ACK=YES; revise a limitacao de escopo do crawler." "$EX_CONFIG"
  (( REQUEST_RATE > 0 )) || die "crawler XSStrike exige REQUEST_RATE maior que zero para limitar volume." "$EX_CONFIG"
fi
if [[ -n "$XSSTRIKE_SEEDS_FILE" ]]; then
  require_file "$XSSTRIKE_SEEDS_FILE"
  while IFS= read -r seed || [[ -n "$seed" ]]; do
    seed="$(trim "${seed//$'\r'/}")"
    [[ -z "$seed" || "$seed" == \#* ]] && continue
    validate_url "$seed" || die "seed XSStrike invalida: $seed" "$EX_CONFIG"
    is_target_in_scope "$seed" "$SCOPE_FILE" || die "seed XSStrike fora do escopo: $seed" "$EX_UNAUTHORIZED"
  done < "$XSSTRIKE_SEEDS_FILE"
fi

EFFECTIVE_DELAY_MS="$DELAY_MS"
if (( REQUEST_RATE > 0 )); then
  RATE_DELAY_MS=$(( (1000 + REQUEST_RATE - 1) / REQUEST_RATE ))
  (( EFFECTIVE_DELAY_MS < RATE_DELAY_MS )) && EFFECTIVE_DELAY_MS="$RATE_DELAY_MS"
fi

RUN_ID="${RUN_ID:-$(new_run_id)}"
OUTDIR="${OUTDIR:-$ROOT/output/$RUN_ID/xsstrike}"
mkdir -p "$OUTDIR"/{logs,results,meta/commands,meta/headers}
check_disk_space "$OUTDIR"
RUN_START_EPOCH="$(date -u +%s)"

# ------------------------------- HELPERS LOCAIS -----------------------------
sha256_text() { printf '%s' "$1" | sha256sum | awk '{print $1}'; }
fsize() { [[ -f "$1" ]] && stat -c '%s' "$1" 2>/dev/null || printf '0\n'; }

human() {
  local bytes="$1"
  command -v numfmt >/dev/null 2>&1 && numfmt --to=iec-i --suffix=B "$bytes" 2>/dev/null && return
  printf '%sB\n' "$bytes"
}

redacted_command_text() {
  local arg redact_next=0 redact_headers=0
  local -a redacted=()
  for arg in "$@"; do
    if (( redact_headers )); then
      if [[ "$arg" == -* ]]; then
        redact_headers=0
      else
        redacted+=("***REDACTED***")
        continue
      fi
    fi
    if (( redact_next )); then
      redacted+=("***REDACTED***")
      redact_next=0
      continue
    fi
    case "$arg" in
      -u|--url|--data|--proxy|--seeds)
        redacted+=("$arg"); redact_next=1 ;;
      --headers)
        redacted+=("$arg"); redact_headers=1 ;;
      -u=*|--url=*|--data=*|--proxy=*|--seeds=*)
        redacted+=("${arg%%=*}=***REDACTED***") ;;
      *) redacted+=("$arg") ;;
    esac
  done
  printf '%q ' "${redacted[@]}"
}

mark_limit_reached() {
  [[ "$LIMIT_REACHED" == "1" ]] && return 0
  LIMIT_REACHED=1
  log_warn "limite operacional atingido: $1; nao serao iniciados novos jobs."
}

run_budget_exhausted() {
  local now elapsed
  now="$(date -u +%s)"; elapsed=$((now - RUN_START_EPOCH))
  if (( elapsed >= MAX_RUN_SECONDS )); then
    mark_limit_reached "MAX_RUN_SECONDS=$MAX_RUN_SECONDS"
    return 0
  fi
  if (( TOTAL_RESERVED >= MAX_TOTAL_REQUESTS )); then
    mark_limit_reached "MAX_TOTAL_REQUESTS=$MAX_TOTAL_REQUESTS"
    return 0
  fi
  return 1
}

BASE_HEADERS=()
if [[ -n "$HEADER_FILE" && -f "$HEADER_FILE" ]]; then
  while IFS= read -r header || [[ -n "$header" ]]; do
    header="${header//$'\r'/}"; header_trimmed="$(trim "$header")"
    [[ -z "$header_trimmed" || "$header_trimmed" == \#* ]] && continue
    BASE_HEADERS+=("$header")
  done < "$HEADER_FILE"
fi

# ------------------------------- ALVOS --------------------------------------
mapfile -t RAW_TARGETS < <(
  awk '{ sub(/\r$/,""); if ($0 !~ /^[[:space:]]*(#|$)/) print }' "$TARGETS_FILE"
)
[[ ${#RAW_TARGETS[@]} -gt 0 ]] || die "nenhum alvo valido em $TARGETS_FILE" "$EX_CONFIG"

URLS=()
for line in "${RAW_TARGETS[@]}"; do
  url="$(trim "$line")"
  validate_url "$url" || die "alvo invalido: $url" "$EX_CONFIG"
  is_target_in_scope "$url" "$SCOPE_FILE" || die "alvo fora do escopo: $url (host: $(extract_host "$url"))" "$EX_UNAUTHORIZED"
  URLS+=("$url")
done

# ------------------------------- JOBS ---------------------------------------
JOB_NAMES=(); JOB_CATEGORY=(); JOB_ENCODING=(); JOB_DATA=(); JOB_GATE=(); JOB_BUDGET=(); JOB_FLAGS=()

add_job() {
  JOB_NAMES+=("$1"); JOB_CATEGORY+=("$2"); JOB_ENCODING+=("$3")
  JOB_DATA+=("$4"); JOB_GATE+=("$5"); JOB_BUDGET+=("$6"); JOB_FLAGS+=("$7")
}

build_jobs() {
  JOB_NAMES=(); JOB_CATEGORY=(); JOB_ENCODING=(); JOB_DATA=(); JOB_GATE=(); JOB_BUDGET=(); JOB_FLAGS=()
  add_job "01_reflected" "reflected" "builtin" "" "reflected" "$XSSTRIKE_CORE_REQUEST_BUDGET" ""
  add_job "02_fuzzer" "fuzzer" "builtin" "" "fuzzer" "$XSSTRIKE_FUZZ_REQUEST_BUDGET" "--fuzzer"
  add_job "03_parameters" "parameter-discovery" "builtin" "" "params" "$XSSTRIKE_PARAM_REQUEST_BUDGET" "--params"
  add_job "04_encoded" "encoding" "builtin" "" "encode" "$XSSTRIKE_CORE_REQUEST_BUDGET" "--encode"
  add_job "10_form" "form" "raw" "$XSSTRIKE_FORM_DATA" "form" "$XSSTRIKE_FUZZ_REQUEST_BUDGET" ""
  add_job "11_json" "json" "raw" "$XSSTRIKE_JSON_DATA" "json" "$XSSTRIKE_FUZZ_REQUEST_BUDGET" ""
  add_job "20_crawl" "crawler" "builtin" "" "crawl" "$MAX_CRAWL_URLS" "--crawl"
}

gate_enabled() {
  case "$1" in
    reflected) [[ "$RUN_XSSTRIKE_REFLECTED" == "1" ]] ;;
    fuzzer) [[ "$RUN_XSSTRIKE_FUZZER" == "1" ]] ;;
    params) [[ "$RUN_XSSTRIKE_PARAMS" == "1" ]] ;;
    encode) [[ "$RUN_XSSTRIKE_ENCODE" == "1" ]] ;;
    form) [[ "$RUN_XSSTRIKE_FORM" == "1" && -n "$XSSTRIKE_FORM_DATA" ]] ;;
    json) [[ "$RUN_XSSTRIKE_JSON" == "1" && -n "$XSSTRIKE_JSON_DATA" ]] ;;
    crawl) [[ "$RUN_XSSTRIKE_CRAWL" == "1" ]] ;;
    *) return 1 ;;
  esac
}

# ------------------------------- LEDGER / ESTADO ----------------------------
LEDGER="$OUTDIR/janelas.tsv"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  run_id sample_id target_index method url_redacted category encoding wordlist_source \
  command_hash start_iso end_iso duration_s exit_code requests_reserved log_bytes status > "$LEDGER"

TOTAL_RESERVED=0; TOTAL_LOG=0; TOTAL_JOBS=0; TOTAL_SKIPPED=0
CURRENT_PID=""; LIMIT_REACHED=0; JOB_SEQUENCE=0

write_row() { printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >> "$LEDGER"; }

record_skipped() {
  local ti="$1" category="$2" encoding="$3" reason="$4"
  write_row "$RUN_ID" "" "$ti" "GET" "$V_URLRED" "$category" "$encoding" "builtin" \
    "" "" "" "0" "" "0" "0" "skipped:$reason"
  TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
  log_debug "skip $category/$encoding: $reason"
}

on_interrupt() {
  log_warn "interrupcao recebida"
  [[ -n "$CURRENT_PID" ]] && kill -TERM "$CURRENT_PID" 2>/dev/null || true
  exit "$EX_INTERRUPT"
}
trap on_interrupt INT TERM

# ------------------------------- EXECUCAO -----------------------------------
run_job() {
  local ti="$1" name="$2" category="$3" encoding="$4" data="$5" gate="$6" base_budget="$7" flag_string="$8"
  local attempts reservation sample_id tag log job_dir command_normalized command_hash
  local now s_epoch s_iso e_epoch e_iso duration rc log_bytes attempt job_deadline
  local -a cmd=() flags=() job_headers=()

  if ! gate_enabled "$gate"; then
    record_skipped "$ti" "$category" "$encoding" "modo_desativado_ou_sem_corpo"
    return 0
  fi
  if run_budget_exhausted; then
    return 0
  fi

  attempts=$((RETRIES + 1))
  if (( base_budget > MAX_REQUESTS_PER_JOB / attempts )); then
    record_skipped "$ti" "$category" "$encoding" "estimativa_acima_do_limite_por_job"
    return 0
  fi
  reservation=$((base_budget * attempts))
  if (( TOTAL_RESERVED + reservation > MAX_TOTAL_REQUESTS )); then
    mark_limit_reached "MAX_TOTAL_REQUESTS=$MAX_TOTAL_REQUESTS"
    return 0
  fi

  JOB_SEQUENCE=$((JOB_SEQUENCE + 1))
  SAMPLE_ID="xsstrike-t$(printf '%03d' "$ti")-${category}-${encoding}-$(printf '%06d' "$JOB_SEQUENCE")"
  tag="$(printf 't%03d__%s__%s__%s' "$ti" "$V_SLUG" "$category" "$encoding")"
  log="$OUTDIR/logs/${tag}.log"
  job_dir="$OUTDIR/results/$tag"
  mkdir -p "$job_dir"

  job_headers=("${BASE_HEADERS[@]}" "User-Agent: $USER_AGENT")
  [[ -n "$COOKIE" ]] && job_headers+=("Cookie: $COOKIE")
  if [[ "$ENABLE_SAMPLE_HEADERS" == "1" ]]; then
    job_headers+=("X-Research-Sample-ID: $SAMPLE_ID" "X-Research-Run-ID: $RUN_ID")
  fi
  case "$gate" in
    form) job_headers+=("Content-Type: application/x-www-form-urlencoded") ;;
    json) job_headers+=("Content-Type: application/json") ;;
  esac

  cmd=("$XSSTRIKE" -u "$CURRENT_URL" --timeout "$HTTP_TIMEOUT" --threads "$THREADS" --json)
  [[ -n "$data" ]] && cmd+=(--data "$data")
  [[ -n "$XSSTRIKE_PROXY" ]] && cmd+=(--proxy "$XSSTRIKE_PROXY")
  (( ${#job_headers[@]} > 0 )) && cmd+=(--headers "${job_headers[@]}")
  [[ -n "$XSSTRIKE_SEEDS_FILE" && "$gate" == "crawl" ]] && cmd+=(--seeds "$XSSTRIKE_SEEDS_FILE")
  [[ "$EFFECTIVE_DELAY_MS" != "0" ]] && cmd+=(--delay "$EFFECTIVE_DELAY_MS")
  [[ -n "$flag_string" ]] && IFS=' ' read -r -a flags <<< "$flag_string"
  cmd+=("${flags[@]}")

  command_normalized="$(printf '%q ' "${cmd[@]}")"
  command_hash="$(sha256_text "$command_normalized")"
  printf '[>] [%03d] %-20s %-16s -> %s\n' "$ti" "$category" "$encoding" "$V_URLRED"

  if [[ "$DRY_RUN" == "1" ]]; then
    log_info "DRY_RUN: $(redacted_command_text "${cmd[@]}")"
    write_row "$RUN_ID" "$SAMPLE_ID" "$ti" "GET" "$V_URLRED" "$category" "$encoding" "builtin" \
      "$command_hash" "" "" "0" "" "$reservation" "0" "dry-run"
    return 0
  fi

  if [[ "$PRINT_COMMANDS" == "1" ]]; then
    local cfile="$OUTDIR/meta/commands/${tag}.sh"
    {
      printf '# Valores sensiveis foram redigidos; este arquivo nao e diretamente reexecutavel.\n'
      redacted_command_text "${cmd[@]}"
      printf '\n'
    } > "$cfile"
    chmod 700 "$cfile"
    printf '%s\n' "$command_hash" > "${cfile}.sha256"
    chmod 600 "${cfile}.sha256"
  fi

  s_epoch="$(date -u +%s)"; s_iso="$(date -u -d "@$s_epoch" +%Y-%m-%dT%H:%M:%SZ)"
  job_deadline=$((s_epoch + MAX_JOB_SECONDS))
  TOTAL_RESERVED=$((TOTAL_RESERVED + reservation))
  rc=1
  for ((attempt=1; attempt<=attempts; attempt++)); do
    now="$(date -u +%s)"
    (( now >= job_deadline )) && { mark_limit_reached "MAX_JOB_SECONDS=$MAX_JOB_SECONDS (job $name)"; break; }
    (cd "$job_dir" && "${cmd[@]}") > "$log" 2>&1 &
    CURRENT_PID=$!
    while kill -0 "$CURRENT_PID" 2>/dev/null; do
      now="$(date -u +%s)"
      if (( now >= job_deadline )); then
        mark_limit_reached "MAX_JOB_SECONDS=$MAX_JOB_SECONDS (job $name)"
      elif (( now - RUN_START_EPOCH >= MAX_RUN_SECONDS )); then
        mark_limit_reached "MAX_RUN_SECONDS=$MAX_RUN_SECONDS"
      fi
      if [[ "$LIMIT_REACHED" == "1" ]]; then
        kill -TERM "$CURRENT_PID" 2>/dev/null || true
        break
      fi
      sleep 1
    done
    wait "$CURRENT_PID"; rc=$?; CURRENT_PID=""
    [[ "$rc" == "0" || "$LIMIT_REACHED" == "1" ]] && break
    log_warn "job $name falhou na tentativa $attempt/$attempts (rc=$rc)"
  done

  e_epoch="$(date -u +%s)"; e_iso="$(date -u -d "@$e_epoch" +%Y-%m-%dT%H:%M:%SZ)"
  duration=$((e_epoch - s_epoch)); log_bytes="$(fsize "$log")"
  TOTAL_LOG=$((TOTAL_LOG + log_bytes)); TOTAL_JOBS=$((TOTAL_JOBS + 1))
  write_row "$RUN_ID" "$SAMPLE_ID" "$ti" "GET" "$V_URLRED" "$category" "$encoding" "builtin" \
    "$command_hash" "$s_iso" "$e_iso" "$duration" "$rc" "$reservation" "$log_bytes" "executed"
  printf '    reserva=%s req | %ss | rc=%s | acumulado=%s req\n' "$reservation" "$duration" "$rc" "$TOTAL_RESERVED"
}

log_info "run_id=$RUN_ID perfil=$PROFILE alvos=${#URLS[@]} dry_run=$DRY_RUN"
log_info "saida: $OUTDIR"

target_index=0
for CURRENT_URL in "${URLS[@]}"; do
  [[ "$LIMIT_REACHED" == "1" ]] && break
  target_index=$((target_index + 1))
  V_HOST="$(extract_host "$CURRENT_URL")"
  V_SLUG="$(sanitize_identifier "$V_HOST")"
  V_URLRED="$(redact_secrets "$CURRENT_URL")"
  build_jobs

  for JOB_INDEX in "${!JOB_NAMES[@]}"; do
    [[ "$LIMIT_REACHED" == "1" ]] && break
    run_job "$target_index" "${JOB_NAMES[$JOB_INDEX]}" "${JOB_CATEGORY[$JOB_INDEX]}" \
      "${JOB_ENCODING[$JOB_INDEX]}" "${JOB_DATA[$JOB_INDEX]}" "${JOB_GATE[$JOB_INDEX]}" \
      "${JOB_BUDGET[$JOB_INDEX]}" "${JOB_FLAGS[$JOB_INDEX]}"
  done
done

# ------------------------------- RESUMO -------------------------------------
echo
echo "============================================================================="
echo "RESUMO DA EXECUCAO ($RUN_ID)"
echo "============================================================================="
printf 'jobs executados ...........: %s\n' "$TOTAL_JOBS"
printf 'jobs pulados ..............: %s\n' "$TOTAL_SKIPPED"
printf 'requisicoes reservadas ....: %s\n' "$TOTAL_RESERVED"
printf 'logs do xsstrike ..........: %s\n' "$(human "$TOTAL_LOG")"
[[ "$LIMIT_REACHED" == "1" ]] && printf 'limite operacional ........: atingido\n'
echo
echo "[ok] Ledger: $LEDGER"
echo "[ok] Logs: $OUTDIR/logs   Resultados: $OUTDIR/results   Comandos: $OUTDIR/meta/commands"
