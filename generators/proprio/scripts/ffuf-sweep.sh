#!/usr/bin/env bash
# =============================================================================
# ffuf-sweep.sh - bateria de ffuf por alvo (laboratorio autorizado).
#
#   ./scripts/ffuf-sweep.sh --targets ./config/targets.txt \
#                            --scope ./config/scope.txt \
#                            --profile safe
#
# FORMATO DE ALVOS: uma URL http/https por linha. Cada alvo e validado contra
# o escopo antes de qualquer job ser composto. Nao segue redirects: o ffuf nao
# fornece uma forma segura de revalidar cada destino redirecionado.
#
# MODOS: caminhos, nomes de parametros, valores, headers, cookies, formulario,
# JSON, SQLi (raw), XSS (raw), metodos, content types e
# combinacoes com FUZZ/FUZZ2. Wordlists ausentes sao registradas como skip;
# nenhuma lista e baixada ou gerada automaticamente por este script.
#
# Compatibilidade: Bash 4.4+. DRY_RUN somente compoe comandos redigidos e nao
# executa ffuf nem faz chamadas de rede.
# =============================================================================
set -uo pipefail
umask 077

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

TOOL_NAME="ffuf"

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
FFUF="${FFUF_BIN:-ffuf}"
DRY_RUN="${DRY_RUN:-0}"
[[ "$CLI_DRY_RUN" == "1" ]] && DRY_RUN=1

# ------------------------------- CONFIGURACAO -------------------------------
THREADS="${THREADS:-2}"
REQUEST_RATE="${REQUEST_RATE:-0}"
DELAY_MS="${DELAY_MS:-0}"
HTTP_TIMEOUT="${HTTP_TIMEOUT:-30}"
PRINT_COMMANDS="${PRINT_COMMANDS:-0}"
FOLLOW_REDIRECTS="${FOLLOW_REDIRECTS:-0}"
ENABLE_SAMPLE_HEADERS="${ENABLE_SAMPLE_HEADERS:-0}"
USER_AGENT="${USER_AGENT:-TCC-Web-Sample-Generator/0.1}"

MAX_REQUESTS_PER_JOB="${MAX_REQUESTS_PER_JOB:-50000}"
MAX_TOTAL_REQUESTS="${MAX_TOTAL_REQUESTS:-500000}"
MAX_JOB_SECONDS="${MAX_JOB_SECONDS:-7200}"
MAX_RUN_SECONDS="${MAX_RUN_SECONDS:-28800}"
MAX_CRAWL_DEPTH="${MAX_CRAWL_DEPTH:-5}"
MAX_CRAWL_URLS="${MAX_CRAWL_URLS:-10000}"

CUSTOM_WORDLIST_DIR="${CUSTOM_WORDLIST_DIR:-$ROOT/wordlists/custom}"
FFUF_PATH_WORDLIST="${FFUF_PATH_WORDLIST:-$CUSTOM_WORDLIST_DIR/paths.txt}"
FFUF_PARAMETER_WORDLIST="${FFUF_PARAMETER_WORDLIST:-$CUSTOM_WORDLIST_DIR/parameters.txt}"
FFUF_VALUE_WORDLIST="${FFUF_VALUE_WORDLIST:-$CUSTOM_WORDLIST_DIR/parameters.txt}"
FFUF_HEADER_WORDLIST="${FFUF_HEADER_WORDLIST:-$CUSTOM_WORDLIST_DIR/parameters.txt}"
FFUF_COOKIE_WORDLIST="${FFUF_COOKIE_WORDLIST:-$CUSTOM_WORDLIST_DIR/parameters.txt}"
FFUF_SQLI_RAW_WORDLIST="${FFUF_SQLI_RAW_WORDLIST:-$CUSTOM_WORDLIST_DIR/sqli.txt}"
FFUF_XSS_RAW_WORDLIST="${FFUF_XSS_RAW_WORDLIST:-$CUSTOM_WORDLIST_DIR/xss.txt}"
FFUF_METHOD_WORDLIST="${FFUF_METHOD_WORDLIST:-$CUSTOM_WORDLIST_DIR/methods.txt}"
FFUF_CONTENT_TYPE_WORDLIST="${FFUF_CONTENT_TYPE_WORDLIST:-$CUSTOM_WORDLIST_DIR/content-types.txt}"

FFUF_OUTPUT_FORMAT="${FFUF_OUTPUT_FORMAT:-json}"
FFUF_MATCH_CODES="${FFUF_MATCH_CODES:-all}"
FFUF_FILTER_SIZE="${FFUF_FILTER_SIZE:-}"
FFUF_FILTER_WORDS="${FFUF_FILTER_WORDS:-}"
FFUF_FILTER_LINES="${FFUF_FILTER_LINES:-}"
FFUF_EXTENSIONS="${FFUF_EXTENSIONS:-}"
FFUF_AUTOCALIBRATE="${FFUF_AUTOCALIBRATE:-1}"
FFUF_RECURSION="${FFUF_RECURSION:-0}"
FFUF_RECURSION_DEPTH="${FFUF_RECURSION_DEPTH:-$MAX_CRAWL_DEPTH}"
FFUF_REPLAY_PROXY="${FFUF_REPLAY_PROXY:-}"
FFUF_PROXY="${FFUF_PROXY:-${PROXY:-}}"
FFUF_HEADER_NAME="${FFUF_HEADER_NAME:-X-Forwarded-For}"
FFUF_COOKIE_NAME="${FFUF_COOKIE_NAME:-ffuf_probe}"
FFUF_VALUE_PARAM="${FFUF_VALUE_PARAM:-ffuf_value}"

COOKIE="${COOKIE:-}"
HEADER_FILE="${HEADERS_FILE:-}"

RUN_FFUF_PATHS="${RUN_FFUF_PATHS:-1}"
RUN_FFUF_PARAMETERS="${RUN_FFUF_PARAMETERS:-1}"
RUN_FFUF_VALUES="${RUN_FFUF_VALUES:-1}"
RUN_FFUF_HEADERS="${RUN_FFUF_HEADERS:-1}"
RUN_FFUF_COOKIES="${RUN_FFUF_COOKIES:-1}"
RUN_FFUF_FORM="${RUN_FFUF_FORM:-1}"
RUN_FFUF_JSON="${RUN_FFUF_JSON:-1}"
RUN_FFUF_SQLI="${RUN_FFUF_SQLI:-1}"
RUN_FFUF_XSS="${RUN_FFUF_XSS:-1}"
RUN_FFUF_METHODS="${RUN_FFUF_METHODS:-0}"
RUN_FFUF_CONTENT_TYPES="${RUN_FFUF_CONTENT_TYPES:-0}"
RUN_FFUF_COMBINED="${RUN_FFUF_COMBINED:-0}"

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
  command -v "$FFUF" >/dev/null 2>&1 || die "ffuf nao encontrado: $FFUF" "$EX_UNAVAILABLE"
fi

case "$PRINT_COMMANDS" in 0|1) ;; *) die "PRINT_COMMANDS invalido: $PRINT_COMMANDS" "$EX_CONFIG" ;; esac
case "$ENABLE_SAMPLE_HEADERS" in 0|1) ;; *) die "ENABLE_SAMPLE_HEADERS invalido: $ENABLE_SAMPLE_HEADERS" "$EX_CONFIG" ;; esac
case "$FFUF_AUTOCALIBRATE" in 0|1) ;; *) die "FFUF_AUTOCALIBRATE invalido: $FFUF_AUTOCALIBRATE" "$EX_CONFIG" ;; esac
case "$FFUF_RECURSION" in 0|1) ;; *) die "FFUF_RECURSION invalido: $FFUF_RECURSION" "$EX_CONFIG" ;; esac
case "$FOLLOW_REDIRECTS" in
  0) ;;
  1) die "FOLLOW_REDIRECTS=1 nao e suportado: ffuf nao revalida o escopo de cada redirect." "$EX_CONFIG" ;;
  *) die "FOLLOW_REDIRECTS invalido: $FOLLOW_REDIRECTS" "$EX_CONFIG" ;;
esac
case "$FFUF_OUTPUT_FORMAT" in json|csv|html) ;; *) die "FFUF_OUTPUT_FORMAT invalido: $FFUF_OUTPUT_FORMAT" "$EX_CONFIG" ;; esac

validate_integer THREADS "$THREADS" 1 64
validate_integer REQUEST_RATE "$REQUEST_RATE" 0
validate_integer DELAY_MS "$DELAY_MS" 0
validate_integer HTTP_TIMEOUT "$HTTP_TIMEOUT" 1
validate_integer MAX_REQUESTS_PER_JOB "$MAX_REQUESTS_PER_JOB" 1
validate_integer MAX_TOTAL_REQUESTS "$MAX_TOTAL_REQUESTS" 1
validate_integer MAX_JOB_SECONDS "$MAX_JOB_SECONDS" 1
validate_integer MAX_RUN_SECONDS "$MAX_RUN_SECONDS" 1
validate_integer MAX_CRAWL_DEPTH "$MAX_CRAWL_DEPTH" 0
validate_integer MAX_CRAWL_URLS "$MAX_CRAWL_URLS" 1
validate_integer FFUF_RECURSION_DEPTH "$FFUF_RECURSION_DEPTH" 0

if [[ "$FFUF_RECURSION" == "1" && "$REQUEST_RATE" == "0" ]]; then
  die "FFUF_RECURSION=1 exige REQUEST_RATE maior que zero para limitar o volume." "$EX_CONFIG"
fi

EFFECTIVE_DELAY_MS="$DELAY_MS"
if (( REQUEST_RATE > 0 )); then
  RATE_DELAY_MS=$(( (1000 + REQUEST_RATE - 1) / REQUEST_RATE ))
  (( EFFECTIVE_DELAY_MS < RATE_DELAY_MS )) && EFFECTIVE_DELAY_MS="$RATE_DELAY_MS"
fi
DELAY="$(LC_NUMERIC=C printf '%d.%03d' $(( EFFECTIVE_DELAY_MS / 1000 )) $(( EFFECTIVE_DELAY_MS % 1000 )))"

RUN_ID="${RUN_ID:-$(new_run_id)}"
OUTDIR="${OUTDIR:-$ROOT/output/$RUN_ID/ffuf}"
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
      -u|--url|-b|--cookie|-d|--data|-H|--header|--headers|-x|--proxy|-replay-proxy|--replay-proxy)
        redacted+=("$arg"); redact_next=1 ;;
      -u=*|--url=*|-b=*|--cookie=*|-d=*|--data=*|-H=*|--header=*|--headers=*|-x=*|--proxy=*|-replay-proxy=*|--replay-proxy=*)
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

estimate_requests() {
  local specs="$1" spec file lines estimate=1
  local -a entries
  IFS=',' read -r -a entries <<< "$specs"
  for spec in "${entries[@]}"; do
    file="${spec%:*}"
    lines="$(wordlist_lines "$file")" || return 1
    if (( estimate > MAX_REQUESTS_PER_JOB / lines )); then
      printf '%s' "$((MAX_REQUESTS_PER_JOB + 1))"
      return 0
    fi
    estimate=$((estimate * lines))
  done
  printf '%s' "$estimate"
}

job_seconds_limit() {
  local request_limit="$1" limit="$MAX_JOB_SECONDS" rate_limit
  if (( REQUEST_RATE > 0 )); then
    rate_limit=$(( request_limit / REQUEST_RATE ))
    (( rate_limit < 1 )) && rate_limit=1
    (( rate_limit < limit )) && limit="$rate_limit"
  fi
  printf '%s' "$limit"
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
JOB_NAMES=(); JOB_CATEGORY=(); JOB_ENCODING=(); JOB_METHOD=(); JOB_URL=()
JOB_DATA=(); JOB_WORDLISTS=(); JOB_HEADERS=(); JOB_COOKIE=(); JOB_GATE=()

add_job() {
  JOB_NAMES+=("$1"); JOB_CATEGORY+=("$2"); JOB_ENCODING+=("$3")
  JOB_METHOD+=("$4"); JOB_URL+=("$5"); JOB_DATA+=("$6")
  JOB_WORDLISTS+=("$7"); JOB_HEADERS+=("$8"); JOB_COOKIE+=("$9"); JOB_GATE+=("${10}")
}

build_jobs() {
  local target="$1" base separator
  base="${target%%\?*}"
  base="${base%/}"                    # remove barra final -> evita .../revistas//FUZZ
  separator="?"; [[ "$target" == *\?* ]] && separator="&"

  JOB_NAMES=(); JOB_CATEGORY=(); JOB_ENCODING=(); JOB_METHOD=(); JOB_URL=()
  JOB_DATA=(); JOB_WORDLISTS=(); JOB_HEADERS=(); JOB_COOKIE=(); JOB_GATE=()

  add_job "01_paths" "paths" "raw" "GET" "${base}/FUZZ" "" \
    "${FFUF_PATH_WORDLIST}:FUZZ" "" "" "paths"
  add_job "02_parameters" "parameters" "raw" "GET" "${target}${separator}FUZZ=1" "" \
    "${FFUF_PARAMETER_WORDLIST}:FUZZ" "" "" "parameters"
  add_job "03_values" "values" "raw" "GET" "${target}${separator}${FFUF_VALUE_PARAM}=FUZZ" "" \
    "${FFUF_VALUE_WORDLIST}:FUZZ" "" "" "values"
  add_job "04_headers" "headers" "raw" "GET" "$target" "" \
    "${FFUF_HEADER_WORDLIST}:FUZZ" "${FFUF_HEADER_NAME}: FUZZ" "" "headers"
  add_job "05_cookies" "cookies" "raw" "GET" "$target" "" \
    "${FFUF_COOKIE_WORDLIST}:FUZZ" "" "${FFUF_COOKIE_NAME}=FUZZ" "cookies"
  add_job "06_form" "form" "raw" "POST" "$base" "${FFUF_VALUE_PARAM}=FUZZ" \
    "${FFUF_VALUE_WORDLIST}:FUZZ" "Content-Type: application/x-www-form-urlencoded" "" "form"
  add_job "07_json" "json" "raw" "POST" "$base" "{\"${FFUF_VALUE_PARAM}\":\"FUZZ\"}" \
    "${FFUF_VALUE_WORDLIST}:FUZZ" "Content-Type: application/json" "" "json"
  add_job "20_sqli_raw" "sqli" "raw" "GET" "${target}${separator}${FFUF_VALUE_PARAM}=FUZZ" "" \
    "${FFUF_SQLI_RAW_WORDLIST}:FUZZ" "" "" "sqli"
  add_job "21_sqli_raw_post" "sqli" "raw" "POST" "$base" "${FFUF_VALUE_PARAM}=FUZZ" \
    "${FFUF_SQLI_RAW_WORDLIST}:FUZZ" "Content-Type: application/x-www-form-urlencoded" "" "sqli"
  add_job "30_xss_raw" "xss" "raw" "GET" "${target}${separator}${FFUF_VALUE_PARAM}=FUZZ" "" \
    "${FFUF_XSS_RAW_WORDLIST}:FUZZ" "" "" "xss"
  add_job "31_xss_raw_post" "xss" "raw" "POST" "$base" "${FFUF_VALUE_PARAM}=FUZZ" \
    "${FFUF_XSS_RAW_WORDLIST}:FUZZ" "Content-Type: application/x-www-form-urlencoded" "" "xss"
  add_job "40_methods" "methods" "raw" "FUZZ" "$target" "" \
    "${FFUF_METHOD_WORDLIST}:FUZZ" "" "" "methods"
  add_job "41_content_types" "content-types" "raw" "POST" "$base" "${FFUF_VALUE_PARAM}=sample" \
    "${FFUF_CONTENT_TYPE_WORDLIST}:FUZZ" "Content-Type: FUZZ" "" "content-types"
  add_job "50_combined" "combined" "raw" "GET" "${target}${separator}FUZZ=FUZZ2" "" \
    "${FFUF_PARAMETER_WORDLIST}:FUZZ,${FFUF_VALUE_WORDLIST}:FUZZ2" "" "" "combined"
}

gate_enabled() {
  case "$1" in
    paths) [[ "$RUN_FFUF_PATHS" == "1" ]] ;;
    parameters) [[ "$RUN_FFUF_PARAMETERS" == "1" ]] ;;
    values) [[ "$RUN_FFUF_VALUES" == "1" ]] ;;
    headers) [[ "$RUN_FFUF_HEADERS" == "1" ]] ;;
    cookies) [[ "$RUN_FFUF_COOKIES" == "1" ]] ;;
    form) [[ "$RUN_FFUF_FORM" == "1" ]] ;;
    json) [[ "$RUN_FFUF_JSON" == "1" ]] ;;
    sqli) [[ "$RUN_FFUF_SQLI" == "1" ]] ;;
    xss) [[ "$RUN_FFUF_XSS" == "1" ]] ;;
    methods) [[ "$RUN_FFUF_METHODS" == "1" ]] ;;
    content-types) [[ "$RUN_FFUF_CONTENT_TYPES" == "1" ]] ;;
    combined) [[ "$RUN_FFUF_COMBINED" == "1" ]] ;;
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
  local ti="$1" method="$2" category="$3" encoding="$4" wordlists="$5" reason="$6"
  write_row "$RUN_ID" "" "$ti" "$method" "$V_URLRED" "$category" "$encoding" "$wordlists" \
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
  local ti="$1" name="$2" category="$3" encoding="$4" method="$5" url="$6" data="$7"
  local wordlists="$8" job_headers="$9" job_cookie="${10}"
  local estimate reservation job_request_limit remaining job_seconds sample_id tag log output source_wordlist
  local command_normalized command_hash
  local now s_epoch s_iso e_epoch e_iso duration rc log_bytes spec header ext
  local -a cmd=() list_specs ext_values

  if ! gate_enabled "${JOB_GATE[$JOB_INDEX]}"; then
    record_skipped "$ti" "$method" "$category" "$encoding" "$wordlists" "modo_desativado"
    return 0
  fi
  if run_budget_exhausted; then
    return 0
  fi
  if ! estimate="$(estimate_requests "$wordlists")"; then
    record_skipped "$ti" "$method" "$category" "$encoding" "$wordlists" "wordlist_ausente_ou_vazia"
    return 0
  fi
  job_request_limit="$MAX_REQUESTS_PER_JOB"
  if [[ "$FFUF_RECURSION" == "1" && "$category" == "paths" && "$MAX_CRAWL_URLS" -lt "$job_request_limit" ]]; then
    job_request_limit="$MAX_CRAWL_URLS"
  fi
  if (( estimate > job_request_limit )); then
    record_skipped "$ti" "$method" "$category" "$encoding" "$wordlists" "estimativa_acima_do_limite_por_job"
    return 0
  fi
  reservation="$estimate"
  # A recursao pode encontrar mais caminhos que a wordlist inicial; reserve o
  # teto do crawl para nao ultrapassar o orcamento global por estimativa baixa.
  [[ "$FFUF_RECURSION" == "1" && "$category" == "paths" ]] && reservation="$job_request_limit"
  if (( TOTAL_RESERVED + reservation > MAX_TOTAL_REQUESTS )); then
    mark_limit_reached "MAX_TOTAL_REQUESTS=$MAX_TOTAL_REQUESTS"
    return 0
  fi

  JOB_SEQUENCE=$((JOB_SEQUENCE + 1))
  sample_id="ffuf-t$(printf '%03d' "$ti")-${category}-${encoding}-$(printf '%06d' "$JOB_SEQUENCE")"
  tag="$(printf 't%03d__%s__%s__%s__%s' "$ti" "$V_SLUG" "$method" "$category" "$encoding")"
  log="$OUTDIR/logs/${tag}.log"
  output="$OUTDIR/results/${tag}.${FFUF_OUTPUT_FORMAT}"
  source_wordlist="${wordlists%%,*}"
  source_wordlist="${source_wordlist%:*}"

  now="$(date -u +%s)"
  remaining=$((MAX_RUN_SECONDS - (now - RUN_START_EPOCH)))
  (( remaining < 1 )) && { mark_limit_reached "MAX_RUN_SECONDS=$MAX_RUN_SECONDS"; return 0; }
  job_seconds="$(job_seconds_limit "$job_request_limit")"
  (( remaining < job_seconds )) && job_seconds="$remaining"

  cmd=("$FFUF" -u "$url" -X "$method" -t "$THREADS" -timeout "$HTTP_TIMEOUT" \
    -maxtime-job "$job_seconds" -maxtime "$remaining" -o "$output" -of "$FFUF_OUTPUT_FORMAT" -mc "$FFUF_MATCH_CODES")
  (( REQUEST_RATE > 0 )) && cmd+=(-rate "$REQUEST_RATE")
  (( EFFECTIVE_DELAY_MS > 0 )) && cmd+=(-p "$DELAY")
  [[ -n "$FFUF_FILTER_SIZE" ]] && cmd+=(-fs "$FFUF_FILTER_SIZE")
  [[ -n "$FFUF_FILTER_WORDS" ]] && cmd+=(-fw "$FFUF_FILTER_WORDS")
  [[ -n "$FFUF_FILTER_LINES" ]] && cmd+=(-fl "$FFUF_FILTER_LINES")
  [[ "$FFUF_AUTOCALIBRATE" == "1" ]] && cmd+=(-ac)
  [[ -n "$FFUF_PROXY" ]] && cmd+=(-x "$FFUF_PROXY")
  [[ -n "$FFUF_REPLAY_PROXY" ]] && cmd+=(-replay-proxy "$FFUF_REPLAY_PROXY")

  if [[ "$FFUF_RECURSION" == "1" && "$category" == "paths" ]]; then
    cmd+=(-recursion -recursion-depth "$FFUF_RECURSION_DEPTH")
  fi
  if [[ "$category" == "paths" && -n "$FFUF_EXTENSIONS" ]]; then
    # ffuf aceita UM -e com lista separada por virgula (varios -e: so o ultimo vale)
    cmd+=(-e "$FFUF_EXTENSIONS")
  fi

  cmd+=(-H "User-Agent: $USER_AGENT")
  for header in "${BASE_HEADERS[@]}"; do cmd+=(-H "$header"); done
  [[ -n "$job_headers" ]] && cmd+=(-H "$job_headers")
  if [[ "$ENABLE_SAMPLE_HEADERS" == "1" ]]; then
    cmd+=(-H "X-Research-Sample-ID: $sample_id" -H "X-Research-Run-ID: $RUN_ID")
  fi
  if [[ -n "$data" ]]; then cmd+=(-d "$data"); fi
  if [[ -n "$COOKIE" || -n "$job_cookie" ]]; then
    [[ -n "$COOKIE" && -n "$job_cookie" ]] && job_cookie="$COOKIE; $job_cookie"
    [[ -n "$COOKIE" && -z "$job_cookie" ]] && job_cookie="$COOKIE"
    cmd+=(-b "$job_cookie")
  fi
  IFS=',' read -r -a list_specs <<< "$wordlists"
  for spec in "${list_specs[@]}"; do cmd+=(-w "$spec"); done
  command_normalized="$(printf '%q ' "${cmd[@]}")"
  command_hash="$(sha256_text "$command_normalized")"

  printf '[>] [%03d] %-16s %-14s -> %s\n' "$ti" "$category" "$encoding" "$V_URLRED"
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
  TOTAL_RESERVED=$((TOTAL_RESERVED + reservation))
  "${cmd[@]}" > "$log" 2>&1 &
  CURRENT_PID=$!
  while kill -0 "$CURRENT_PID" 2>/dev/null; do
    now="$(date -u +%s)"
    if (( now - s_epoch >= job_seconds )); then
      mark_limit_reached "MAX_JOB_SECONDS=$job_seconds (job $name)"
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

  e_epoch="$(date -u +%s)"; e_iso="$(date -u -d "@$e_epoch" +%Y-%m-%dT%H:%M:%SZ)"
  duration=$((e_epoch - s_epoch)); log_bytes="$(fsize "$log")"
  TOTAL_LOG=$((TOTAL_LOG + log_bytes)); TOTAL_JOBS=$((TOTAL_JOBS + 1))
  write_row "$RUN_ID" "$sample_id" "$ti" "$method" "$V_URLRED" "$category" "$encoding" "$source_wordlist" \
    "$command_hash" "$s_iso" "$e_iso" "$duration" "$rc" "$reservation" "$log_bytes" "executed"
  printf '    reserva=%s req | %ss | rc=%s | acumulado=%s req\n' "$reservation" "$duration" "$rc" "$TOTAL_RESERVED"
}

log_info "run_id=$RUN_ID perfil=$PROFILE alvos=${#URLS[@]} dry_run=$DRY_RUN formato=$FFUF_OUTPUT_FORMAT"
log_info "saida: $OUTDIR"

target_index=0
for url in "${URLS[@]}"; do
  [[ "$LIMIT_REACHED" == "1" ]] && break
  target_index=$((target_index + 1))
  V_HOST="$(extract_host "$url")"
  V_SLUG="$(sanitize_identifier "$V_HOST")"
  V_URLRED="$(redact_secrets "$url")"
  build_jobs "$url"

  for JOB_INDEX in "${!JOB_NAMES[@]}"; do
    [[ "$LIMIT_REACHED" == "1" ]] && break
    run_job "$target_index" "${JOB_NAMES[$JOB_INDEX]}" "${JOB_CATEGORY[$JOB_INDEX]}" \
      "${JOB_ENCODING[$JOB_INDEX]}" "${JOB_METHOD[$JOB_INDEX]}" "${JOB_URL[$JOB_INDEX]}" \
      "${JOB_DATA[$JOB_INDEX]}" "${JOB_WORDLISTS[$JOB_INDEX]}" "${JOB_HEADERS[$JOB_INDEX]}" \
      "${JOB_COOKIE[$JOB_INDEX]}"
  done
done

# --------------------- CONSOLIDACAO DE ENDPOINTS DESCOBERTOS -----------------
# Entregavel do pipeline: reune os achados dos JSON do ffuf numa lista
# URL-por-linha (esquema+host+path, sem query), no escopo e deduplicada, no
# MESMO formato de config/targets.txt, para alimentar sqlmap/dalfox/xsstrike.
DISCOVERED_FILE="$OUTDIR/discovered-endpoints.txt"
TOTAL_DISCOVERED=0

consolidate_endpoints() {
  : > "$DISCOVERED_FILE"; chmod 600 "$DISCOVERED_FILE"
  if [[ "$FFUF_OUTPUT_FORMAT" != "json" ]]; then
    log_warn "consolidacao requer FFUF_OUTPUT_FORMAT=json; discovered-endpoints.txt ficara vazio."
    return 0
  fi
  local -a result_files=()
  local f
  for f in "$OUTDIR"/results/*.json; do [[ -e "$f" ]] && result_files+=("$f"); done
  [[ ${#result_files[@]} -eq 0 ]] && { log_info "sem resultados json para consolidar."; return 0; }

  local tmp; tmp="$(mktemp)"
  # Normaliza cada .results[].url para esquema+host+path (sem query/fragmento).
  python3 - "${result_files[@]}" > "$tmp" <<'PY'
import json, sys
from urllib.parse import urlsplit, urlunsplit
seen = set()
for path in sys.argv[1:]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        continue
    for res in (data.get("results") or []):
        u = res.get("url") or ""
        if not u:
            continue
        try:
            p = urlsplit(u)
        except ValueError:
            continue
        if p.scheme.lower() not in ("http", "https") or not p.hostname:
            continue
        norm = urlunsplit((p.scheme, p.netloc, p.path or "/", "", ""))
        if norm not in seen:
            seen.add(norm)
            print(norm)
PY

  local url
  while IFS= read -r url || [[ -n "$url" ]]; do
    [[ -z "$url" ]] && continue
    # Revalida cada endpoint contra o escopo antes de gravar.
    if is_target_in_scope "$url" "$SCOPE_FILE"; then
      printf '%s\n' "$url" >> "$DISCOVERED_FILE"
      TOTAL_DISCOVERED=$((TOTAL_DISCOVERED + 1))
    fi
  done < <(sort -u "$tmp")
  rm -f "$tmp"
  log_info "endpoints descobertos (no escopo): $TOTAL_DISCOVERED -> $DISCOVERED_FILE"
}

if [[ "$DRY_RUN" == "1" ]]; then
  : > "$DISCOVERED_FILE"; chmod 600 "$DISCOVERED_FILE"
  log_info "DRY_RUN: discovered-endpoints.txt criado vazio (ffuf nao executado)."
else
  consolidate_endpoints
fi

# ------------------------------- RESUMO -------------------------------------
echo
echo "============================================================================="
echo "RESUMO DA EXECUCAO ($RUN_ID)"
echo "============================================================================="
printf 'jobs executados ...........: %s\n' "$TOTAL_JOBS"
printf 'jobs pulados ..............: %s\n' "$TOTAL_SKIPPED"
printf 'requisicoes reservadas ....: %s\n' "$TOTAL_RESERVED"
printf 'logs do ffuf ..............: %s\n' "$(human "$TOTAL_LOG")"
printf 'endpoints descobertos .....: %s\n' "$TOTAL_DISCOVERED"
[[ "$LIMIT_REACHED" == "1" ]] && printf 'limite operacional ........: atingido\n'
echo
echo "[ok] Ledger: $LEDGER"
echo "[ok] Endpoints: $DISCOVERED_FILE"
echo "[ok] Logs: $OUTDIR/logs   Resultados: $OUTDIR/results   Comandos: $OUTDIR/meta/commands"
