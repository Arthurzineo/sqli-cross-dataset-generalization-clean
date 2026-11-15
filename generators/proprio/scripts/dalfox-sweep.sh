#!/usr/bin/env bash
# =============================================================================
# dalfox-sweep.sh - bateria de Dalfox por alvo (laboratorio autorizado).
#
#   ./scripts/dalfox-sweep.sh --targets ./config/targets.txt \
#                              --scope ./config/scope.txt \
#                              --profile safe
#
# Cada alvo e validado contra o escopo. Os jobs cobrem analise refletida,
# descoberta/mineracao de parametros, payloads XSS da wordlist local (custom/
# xss.txt) e corpos POST/JSON configurados pelo operador. Sem variacoes de
# encoding. Nao ha fluxo stored XSS automatico
# e blind XSS usa somente callback local explicitamente validado no escopo.
#
# Compatibilidade: Bash 4.4+. DRY_RUN somente compoe comandos redigidos e nao
# executa Dalfox nem faz chamadas de rede.
# =============================================================================
set -uo pipefail
umask 077

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

TOOL_NAME="dalfox"

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
DALFOX="${DALFOX_BIN:-dalfox}"
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

CUSTOM_WORDLIST_DIR="${CUSTOM_WORDLIST_DIR:-$ROOT/wordlists/custom}"
DALFOX_XSS_RAW_WORDLIST="${DALFOX_XSS_RAW_WORDLIST:-$CUSTOM_WORDLIST_DIR/xss.txt}"

DALFOX_PROXY="${DALFOX_PROXY:-${PROXY:-}}"
DALFOX_EXCLUDE_PARAMS="${DALFOX_EXCLUDE_PARAMS:-}"
DALFOX_FORMAT="${DALFOX_FORMAT:-json}"
DALFOX_FORM_DATA="${DALFOX_FORM_DATA:-}"
DALFOX_JSON_DATA="${DALFOX_JSON_DATA:-}"
DALFOX_CORE_REQUEST_BUDGET="${DALFOX_CORE_REQUEST_BUDGET:-100}"
DALFOX_MINING_REQUEST_BUDGET="${DALFOX_MINING_REQUEST_BUDGET:-500}"
DALFOX_STORED_FLOW_FILE="${DALFOX_STORED_FLOW_FILE:-}"

COOKIE="${COOKIE:-}"
HEADER_FILE="${HEADERS_FILE:-}"
ALLOW_LOCAL_BLIND_XSS="${ALLOW_LOCAL_BLIND_XSS:-NO}"
LOCAL_BLIND_XSS_CALLBACK="${LOCAL_BLIND_XSS_CALLBACK:-}"

RUN_DALFOX_REFLECTED="${RUN_DALFOX_REFLECTED:-1}"
RUN_DALFOX_MINING="${RUN_DALFOX_MINING:-0}"
RUN_DALFOX_PAYLOADS="${RUN_DALFOX_PAYLOADS:-1}"
RUN_DALFOX_FORM="${RUN_DALFOX_FORM:-0}"
RUN_DALFOX_JSON="${RUN_DALFOX_JSON:-0}"

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
  command -v "$DALFOX" >/dev/null 2>&1 || die "dalfox nao encontrado: $DALFOX" "$EX_UNAVAILABLE"
fi

case "$PRINT_COMMANDS" in 0|1) ;; *) die "PRINT_COMMANDS invalido: $PRINT_COMMANDS" "$EX_CONFIG" ;; esac
case "$ENABLE_SAMPLE_HEADERS" in 0|1) ;; *) die "ENABLE_SAMPLE_HEADERS invalido: $ENABLE_SAMPLE_HEADERS" "$EX_CONFIG" ;; esac
case "$ALLOW_LOCAL_BLIND_XSS" in YES|NO) ;; *) die "ALLOW_LOCAL_BLIND_XSS invalido: $ALLOW_LOCAL_BLIND_XSS" "$EX_CONFIG" ;; esac
case "$DALFOX_FORMAT" in json|plain) ;; *) die "DALFOX_FORMAT invalido: $DALFOX_FORMAT" "$EX_CONFIG" ;; esac
validate_integer THREADS "$THREADS" 1 64
validate_integer REQUEST_RATE "$REQUEST_RATE" 0
validate_integer DELAY_MS "$DELAY_MS" 0
validate_integer HTTP_TIMEOUT "$HTTP_TIMEOUT" 1
validate_integer RETRIES "$RETRIES" 0
validate_integer MAX_REQUESTS_PER_JOB "$MAX_REQUESTS_PER_JOB" 1
validate_integer MAX_TOTAL_REQUESTS "$MAX_TOTAL_REQUESTS" 1
validate_integer MAX_JOB_SECONDS "$MAX_JOB_SECONDS" 1
validate_integer MAX_RUN_SECONDS "$MAX_RUN_SECONDS" 1
validate_integer DALFOX_CORE_REQUEST_BUDGET "$DALFOX_CORE_REQUEST_BUDGET" 1 "$MAX_REQUESTS_PER_JOB"
validate_integer DALFOX_MINING_REQUEST_BUDGET "$DALFOX_MINING_REQUEST_BUDGET" 1 "$MAX_REQUESTS_PER_JOB"

if [[ "$ALLOW_LOCAL_BLIND_XSS" == "YES" ]]; then
  [[ -n "$LOCAL_BLIND_XSS_CALLBACK" ]] || die "ALLOW_LOCAL_BLIND_XSS=YES exige LOCAL_BLIND_XSS_CALLBACK." "$EX_CONFIG"
  validate_url "$LOCAL_BLIND_XSS_CALLBACK" || die "callback blind XSS invalido: $LOCAL_BLIND_XSS_CALLBACK" "$EX_CONFIG"
  is_target_in_scope "$LOCAL_BLIND_XSS_CALLBACK" "$SCOPE_FILE" || die "callback blind XSS fora do escopo." "$EX_UNAUTHORIZED"
fi
if [[ -n "$DALFOX_STORED_FLOW_FILE" ]]; then
  require_file "$DALFOX_STORED_FLOW_FILE"
  log_info "fluxo stored XSS informado, mas nao e automatizado por este script; referencia: $DALFOX_STORED_FLOW_FILE"
fi

EFFECTIVE_DELAY_MS="$DELAY_MS"
if (( REQUEST_RATE > 0 )); then
  RATE_DELAY_MS=$(( (1000 + REQUEST_RATE - 1) / REQUEST_RATE ))
  (( EFFECTIVE_DELAY_MS < RATE_DELAY_MS )) && EFFECTIVE_DELAY_MS="$RATE_DELAY_MS"
fi

RUN_ID="${RUN_ID:-$(new_run_id)}"
OUTDIR="${OUTDIR:-$ROOT/output/$RUN_ID/dalfox}"
mkdir -p "$OUTDIR"/{logs,results,meta/commands}
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
  local arg redact_next=0
  local -a redacted=()
  for arg in "$@"; do
    if (( redact_next )); then
      redacted+=("***REDACTED***")
      redact_next=0
      continue
    fi
    case "$arg" in
      url|-u|--url|-d|--data|-H|--header|--headers|-C|--cookie|--cookies|--proxy|--blind|--user-agent)
        redacted+=("$arg"); redact_next=1 ;;
      -u=*|--url=*|-d=*|--data=*|-H=*|--header=*|--headers=*|-C=*|--cookie=*|--cookies=*|--proxy=*|--blind=*|--user-agent=*)
        redacted+=("${arg%%=*}=***REDACTED***") ;;
      *) redacted+=("$arg") ;;
    esac
  done
  printf '%q ' "${redacted[@]}"
}

wordlist_lines() {
  local file="$1" count
  [[ -s "$file" ]] || return 1
  count="$(awk 'BEGIN { n=0 } { sub(/\r$/, ""); if ($0 !~ /^[[:space:]]*(#|$)/) n++ } END { print n }' "$file")"
  [[ "$count" =~ ^[0-9]+$ && "$count" -gt 0 ]] || return 1
  printf '%s' "$count"
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

# ------------------------------- HEADERS BASE -------------------------------
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
JOB_NAMES=(); JOB_CATEGORY=(); JOB_ENCODING=(); JOB_METHOD=(); JOB_DATA=()
JOB_PAYLOAD_FILE=(); JOB_CONTENT_TYPE=(); JOB_GATE=(); JOB_BUDGET=()

add_job() {
  JOB_NAMES+=("$1"); JOB_CATEGORY+=("$2"); JOB_ENCODING+=("$3"); JOB_METHOD+=("$4")
  JOB_DATA+=("$5"); JOB_PAYLOAD_FILE+=("$6"); JOB_CONTENT_TYPE+=("$7")
  JOB_GATE+=("$8"); JOB_BUDGET+=("$9")
}

build_jobs() {
  JOB_NAMES=(); JOB_CATEGORY=(); JOB_ENCODING=(); JOB_METHOD=(); JOB_DATA=()
  JOB_PAYLOAD_FILE=(); JOB_CONTENT_TYPE=(); JOB_GATE=(); JOB_BUDGET=()

  add_job "01_reflected" "reflected" "builtin" "GET" "" "" "" "reflected" "$DALFOX_CORE_REQUEST_BUDGET"
  add_job "02_discovery" "parameter-discovery" "builtin" "GET" "" "" "" "mining" "$DALFOX_MINING_REQUEST_BUDGET"
  add_job "10_raw" "xss" "raw" "GET" "" "$DALFOX_XSS_RAW_WORDLIST" "" "payload" "0"
  add_job "30_form" "form" "raw" "POST" "$DALFOX_FORM_DATA" "$DALFOX_XSS_RAW_WORDLIST" "application/x-www-form-urlencoded" "form" "0"
  add_job "31_json" "json" "raw" "POST" "$DALFOX_JSON_DATA" "$DALFOX_XSS_RAW_WORDLIST" "application/json" "json" "0"
}

gate_enabled() {
  case "$1" in
    reflected) [[ "$RUN_DALFOX_REFLECTED" == "1" ]] ;;
    mining) [[ "$RUN_DALFOX_MINING" == "1" ]] ;;
    payload) [[ "$RUN_DALFOX_PAYLOADS" == "1" ]] ;;
    form) [[ "$RUN_DALFOX_FORM" == "1" && -n "$DALFOX_FORM_DATA" ]] ;;
    json) [[ "$RUN_DALFOX_JSON" == "1" && -n "$DALFOX_JSON_DATA" ]] ;;
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
  local ti="$1" method="$2" category="$3" encoding="$4" source="$5" reason="$6"
  write_row "$RUN_ID" "" "$ti" "$method" "$V_URLRED" "$category" "$encoding" "$source" \
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
  local ti="$1" name="$2" category="$3" encoding="$4" method="$5" data="$6"
  local payload_file="$7" content_type="$8" gate="$9" base_budget="${10}"
  local payload_count reservation source_wordlist sample_id tag log output
  local command_normalized command_hash now s_epoch s_iso e_epoch e_iso duration rc log_bytes
  local attempt attempts job_deadline remaining
  local -a cmd=()

  if ! gate_enabled "$gate"; then
    record_skipped "$ti" "$method" "$category" "$encoding" "$payload_file" "modo_desativado_ou_sem_corpo"
    return 0
  fi
  if run_budget_exhausted; then
    return 0
  fi

  source_wordlist="$payload_file"
  if [[ -n "$payload_file" ]]; then
    payload_count="$(wordlist_lines "$payload_file")" || {
      record_skipped "$ti" "$method" "$category" "$encoding" "$payload_file" "wordlist_ausente_ou_vazia"
      return 0
    }
    base_budget="$payload_count"
  fi
  attempts=$((RETRIES + 1))
  if (( base_budget > MAX_REQUESTS_PER_JOB / attempts )); then
    record_skipped "$ti" "$method" "$category" "$encoding" "$source_wordlist" "estimativa_acima_do_limite_por_job"
    return 0
  fi
  reservation=$((base_budget * attempts))
  if (( TOTAL_RESERVED + reservation > MAX_TOTAL_REQUESTS )); then
    mark_limit_reached "MAX_TOTAL_REQUESTS=$MAX_TOTAL_REQUESTS"
    return 0
  fi

  JOB_SEQUENCE=$((JOB_SEQUENCE + 1))
  sample_id="dalfox-t$(printf '%03d' "$ti")-${category}-${encoding}-$(printf '%06d' "$JOB_SEQUENCE")"
  tag="$(printf 't%03d__%s__%s__%s' "$ti" "$V_SLUG" "$category" "$encoding")"
  log="$OUTDIR/logs/${tag}.log"
  output="$OUTDIR/results/${tag}.${DALFOX_FORMAT}"

  cmd=("$DALFOX" url --url "$CURRENT_URL" --workers "$THREADS" --timeout "$HTTP_TIMEOUT" \
    --delay "$EFFECTIVE_DELAY_MS" --format "$DALFOX_FORMAT" --output "$output" --user-agent "$USER_AGENT")
  [[ -n "$DALFOX_PROXY" ]] && cmd+=(--proxy "$DALFOX_PROXY")
  [[ -n "$COOKIE" ]] && cmd+=(--cookies "$COOKIE")
  [[ -n "$DALFOX_EXCLUDE_PARAMS" ]] && cmd+=(--ignore-param "$DALFOX_EXCLUDE_PARAMS")
  [[ "$ALLOW_LOCAL_BLIND_XSS" == "YES" ]] && cmd+=(--blind "$LOCAL_BLIND_XSS_CALLBACK")
  for header in "${BASE_HEADERS[@]}"; do cmd+=(-H "$header"); done
  if [[ "$ENABLE_SAMPLE_HEADERS" == "1" ]]; then
    cmd+=(-H "X-Research-Sample-ID: $sample_id" -H "X-Research-Run-ID: $RUN_ID")
  fi
  if [[ "$gate" == "mining" ]]; then
    # dalfox v3: mineracao (dict+dom) e ON por padrao; --only-discovery basta.
    cmd+=(--only-discovery)
  fi
  if [[ -n "$payload_file" ]]; then
    cmd+=(--only-custom-payload --custom-payload "$payload_file")
  fi
  if [[ "$method" != "GET" ]]; then
    cmd+=(--method "$method" --data "$data")
    [[ -n "$content_type" ]] && cmd+=(-H "Content-Type: $content_type")
  fi

  command_normalized="$(printf '%q ' "${cmd[@]}")"
  command_hash="$(sha256_text "$command_normalized")"
  printf '[>] [%03d] %-20s %-16s -> %s\n' "$ti" "$category" "$encoding" "$V_URLRED"

  if [[ "$DRY_RUN" == "1" ]]; then
    log_info "DRY_RUN: $(redacted_command_text "${cmd[@]}")"
    write_row "$RUN_ID" "$sample_id" "$ti" "$method" "$V_URLRED" "$category" "$encoding" "$source_wordlist" \
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
    "${cmd[@]}" > "$log" 2>&1 &
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
  write_row "$RUN_ID" "$sample_id" "$ti" "$method" "$V_URLRED" "$category" "$encoding" "$source_wordlist" \
    "$command_hash" "$s_iso" "$e_iso" "$duration" "$rc" "$reservation" "$log_bytes" "executed"
  printf '    reserva=%s req | %ss | rc=%s | acumulado=%s req\n' "$reservation" "$duration" "$rc" "$TOTAL_RESERVED"
}

log_info "run_id=$RUN_ID perfil=$PROFILE alvos=${#URLS[@]} dry_run=$DRY_RUN formato=$DALFOX_FORMAT"
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
      "${JOB_ENCODING[$JOB_INDEX]}" "${JOB_METHOD[$JOB_INDEX]}" "${JOB_DATA[$JOB_INDEX]}" \
      "${JOB_PAYLOAD_FILE[$JOB_INDEX]}" "${JOB_CONTENT_TYPE[$JOB_INDEX]}" "${JOB_GATE[$JOB_INDEX]}" \
      "${JOB_BUDGET[$JOB_INDEX]}"
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
printf 'logs do dalfox ............: %s\n' "$(human "$TOTAL_LOG")"
[[ "$LIMIT_REACHED" == "1" ]] && printf 'limite operacional ........: atingido\n'
echo
echo "[ok] Ledger: $LEDGER"
echo "[ok] Logs: $OUTDIR/logs   Resultados: $OUTDIR/results   Comandos: $OUTDIR/meta/commands"
