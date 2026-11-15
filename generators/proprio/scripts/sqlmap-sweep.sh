#!/usr/bin/env bash
# =============================================================================
# sqlmap-sweep.sh — bateria de sqlmap por alvo (laboratório autorizado).
#
#   ./scripts/sqlmap-sweep.sh --targets ./config/targets.txt \
#                             --scope   ./config/scope.txt \
#                             --profile aggressive
#
# FORMATO DE ALVOS: uma URL por linha (ver docs/target-format.md).
#   Para cada URL o script gera automaticamente as variantes GET e POST
#   (o POST reaproveita os parâmetros da query como corpo urlencoded).
#
# CONFORMIDADE (CLAUDE.md §12):
#   - SEM --os-shell/--os-cmd/--os-pwn/--file-write/--file-dest.
#   - SEM --dump-all nem dump indiscriminado de tabelas.
#   - Enumeração de metadados (não-destrutiva) só com ALLOW_METADATA_ENUMERATION=YES.
#   - Nível/risco/técnicas/tampers vêm do perfil; agressividade é configurável.
#
# Baseado no sqlmap.sh de referência, adaptado ao common.sh e ao formato simples.
# Compatível com Bash 4.4+. Não executa ferramentas em DRY_RUN=1.
# =============================================================================
set -uo pipefail
umask 077

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
# shellcheck source=./common.sh
source "$HERE/common.sh"

TOOL_NAME="sqlmap"

# ------------------------------- ARGUMENTOS ---------------------------------
SCOPE_FILE=""; TARGETS_FILE=""; PROFILE="${PROFILE:-safe}"; CLI_DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --targets) TARGETS_FILE="$2"; shift 2 ;;
    --scope)   SCOPE_FILE="$2";   shift 2 ;;
    --profile) PROFILE="$2";      shift 2 ;;
    --dry-run) CLI_DRY_RUN=1;     shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "argumento desconhecido: $1" "$EX_USAGE" ;;
  esac
done

export PROFILE
load_configuration "$ROOT"
SCOPE_FILE="${SCOPE_FILE:-$ROOT/config/scope.txt}"
TARGETS_FILE="${TARGETS_FILE:-$ROOT/config/targets.txt}"
SQLMAP="${SQLMAP_BIN:-sqlmap}"
DRY_RUN="${DRY_RUN:-0}"
[[ "$CLI_DRY_RUN" == "1" ]] && DRY_RUN=1

# ------------------------------- CONFIG DE PERFIL ---------------------------
LEVEL="${SQLMAP_LEVEL:-1}"
RISK="${SQLMAP_RISK:-1}"
TECH="${SQLMAP_TECHNIQUE:-BEU}"
THREADS="${THREADS:-2}"
DELAY_MS="${DELAY_MS:-0}"
REQUEST_RATE="${REQUEST_RATE:-0}"
TIME_DELAY_SEC="${TIME_DELAY_SEC:-5}"
HTTP_TIMEOUT="${HTTP_TIMEOUT:-30}"
RETRIES="${RETRIES:-3}"
VERBOSE="${SQLMAP_VERBOSE:-2}"
COOLDOWN="${COOLDOWN:-0}"
TRAFFIC="${TRAFFIC:-1}"

RUN_TAMPERS="${RUN_TAMPERS:-0}"
RUN_ALL_DBMS_TAMPERS="${RUN_ALL_DBMS_TAMPERS:-0}"
RUN_CRAWL="${RUN_CRAWL:-0}"
RUN_ENUM="${RUN_ENUM:-0}"
CHECK_TAMPERS="${CHECK_TAMPERS:-1}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-60}"
PRINT_COMMANDS="${PRINT_COMMANDS:-0}"
# Filtro opcional de passes (regex ERE sobre o nome do passe, ex.: 01_full_cobertura).
# PASS_INCLUDE: só roda passes que casam. PASS_SKIP: pula passes que casam.
PASS_INCLUDE="${PASS_INCLUDE:-}"
PASS_SKIP="${PASS_SKIP:-}"
# Filtro opcional de metodo: GET ou POST. Vazio = ambas as variantes.
METHOD_ONLY="${METHOD_ONLY:-}"

MAX_REQUESTS_PER_JOB="${MAX_REQUESTS_PER_JOB:-50000}"
MAX_TOTAL_REQUESTS="${MAX_TOTAL_REQUESTS:-500000}"
MAX_JOB_SECONDS="${MAX_JOB_SECONDS:-7200}"
MAX_RUN_SECONDS="${MAX_RUN_SECONDS:-28800}"
MAX_CRAWL_URLS="${MAX_CRAWL_URLS:-10000}"

UA_MODE="${UA_MODE:-mixed}"
USER_AGENT="${USER_AGENT:-TCC-Web-Sample-Generator/0.1}"

# Segredos globais (opcionais; nunca por-alvo neste formato simples)
COOKIE="${COOKIE:-}"
PROXY="${PROXY:-}"
DBMS="${DBMS:-}"
HEADER_FILE="${HEADERS_FILE:-}"
CONTENT_TYPE="${CONTENT_TYPE:-}"

# ------------------------------- CHECKS -------------------------------------
require_authorization
require_command python3
require_command sha256sum
require_command awk
require_command grep
require_command date
require_file "$SCOPE_FILE"
require_file "$TARGETS_FILE"
if [[ "$DRY_RUN" != "1" ]]; then
  require_command timeout
  command -v "$SQLMAP" >/dev/null 2>&1 || die "sqlmap não encontrado: $SQLMAP" "$EX_UNAVAILABLE"
fi

case "$UA_MODE" in fixed|random|mixed) ;; *) die "UA_MODE inválido: $UA_MODE" "$EX_CONFIG" ;; esac
case "$PRINT_COMMANDS" in 0|1) ;; *) die "PRINT_COMMANDS inválido: $PRINT_COMMANDS" "$EX_CONFIG" ;; esac
validate_integer THREADS "$THREADS" 1 64
validate_integer DELAY_MS "$DELAY_MS" 0
validate_integer REQUEST_RATE "$REQUEST_RATE" 0
validate_integer MAX_REQUESTS_PER_JOB "$MAX_REQUESTS_PER_JOB" 1
validate_integer MAX_TOTAL_REQUESTS "$MAX_TOTAL_REQUESTS" 1
validate_integer MAX_JOB_SECONDS "$MAX_JOB_SECONDS" 1
validate_integer MAX_RUN_SECONDS "$MAX_RUN_SECONDS" 1
validate_integer MAX_CRAWL_URLS "$MAX_CRAWL_URLS" 1

# sqlmap recebe segundos e aceita frações. Nunca arredonde para baixo: com
# DELAY_MS=500 o valor anterior virava 0 e removia a limitação configurada.
EFFECTIVE_DELAY_MS="$DELAY_MS"
if (( REQUEST_RATE > 0 )); then
  RATE_DELAY_MS=$(( (1000 + REQUEST_RATE - 1) / REQUEST_RATE ))
  (( EFFECTIVE_DELAY_MS < RATE_DELAY_MS )) && EFFECTIVE_DELAY_MS="$RATE_DELAY_MS"
fi
DELAY="$(LC_NUMERIC=C printf '%d.%03d' $(( EFFECTIVE_DELAY_MS / 1000 )) $(( EFFECTIVE_DELAY_MS % 1000 )))"
if (( TIME_DELAY_SEC >= HTTP_TIMEOUT )); then
  log_warn "TIME_DELAY_SEC=$TIME_DELAY_SEC >= HTTP_TIMEOUT=$HTTP_TIMEOUT: técnicas time-based estourarão o timeout."
fi

RUN_ID="${RUN_ID:-$(new_run_id)}"
OUTDIR="${OUTDIR:-$ROOT/output/$RUN_ID/sqlmap}"
mkdir -p "$OUTDIR"/{logs,traffic,sqlmap-data,meta/commands}
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

content_type_for() {
  local data="$1" stripped
  [[ -n "$CONTENT_TYPE" ]] && { printf '%s' "$CONTENT_TYPE"; return; }
  stripped="${data#"${data%%[![:space:]]*}"}"
  if   [[ "$stripped" == \{* || "$stripped" == \[* ]]; then printf 'application/json'
  elif [[ "$stripped" == \<* ]]; then printf 'application/xml'
  else printf 'application/x-www-form-urlencoded'; fi
}

# Conta uma linha por requisição no tráfego (-t). Sem tráfego, aproxima por [PAYLOAD].
count_reqs() {
  local traffic="$1" log="$2" count=""
  if [[ -s "$traffic" ]]; then
    count="$(grep -Ec 'HTTP request \[#[0-9]+\]:' "$traffic" 2>/dev/null || true)"
    [[ "$count" =~ ^[0-9]+$ ]] || count=0
    printf '%s\texata\n' "$count"
  else
    count="$(grep -c '\[PAYLOAD\]' "$log" 2>/dev/null || true)"
    [[ "$count" =~ ^[0-9]+$ ]] || count=0
    printf '%s\taprox\n' "$count"
  fi
}

normalize_dbms() {
  local v; v="$(lower "$(trim "$1")")"
  case "$v" in
    ""|any|auto) echo any ;;
    mysql|mariadb) echo mysql ;;
    mssql|"microsoft sql server"|sqlserver|"sql server") echo mssql ;;
    postgresql|postgres|pgsql) echo postgresql ;;
    oracle) echo oracle ;;
    sqlite) echo sqlite ;;
    *) echo "$v" ;;
  esac
}

dbms_applies() {
  local selector="$1" configured; configured="$(normalize_dbms "$DBMS")"
  [[ "$selector" == "any" ]] && return 0
  [[ "$RUN_ALL_DBMS_TAMPERS" == "1" && "$configured" == "any" ]] && return 0
  [[ "$configured" == "$selector" ]]
}

is_enum_pass() { [[ "$1" == 90_* ]]; }

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
      -u|--url|--cookie|--proxy|--data|-H|--header|--headers|--csrf-token|--user-agent)
        redacted+=("$arg"); redact_next=1 ;;
      -u=*|--url=*|--cookie=*|--proxy=*|--data=*|--header=*|--headers=*|--csrf-token=*|--user-agent=*)
        redacted+=("${arg%%=*}=***REDACTED***") ;;
      *) redacted+=("$arg") ;;
    esac
  done
  printf '%q ' "${redacted[@]}"
}

mark_limit_reached() {
  [[ "$LIMIT_REACHED" == "1" ]] && return 0
  LIMIT_REACHED=1
  log_warn "limite operacional atingido: $1; não serão iniciados novos passes."
}

run_budget_exhausted() {
  local now elapsed
  now="$(date -u +%s)"; elapsed=$((now - RUN_START_EPOCH))
  if (( elapsed >= MAX_RUN_SECONDS )); then
    mark_limit_reached "MAX_RUN_SECONDS=$MAX_RUN_SECONDS"
    return 0
  fi
  if (( TOTAL_REQ >= MAX_TOTAL_REQUESTS )); then
    mark_limit_reached "MAX_TOTAL_REQUESTS=$MAX_TOTAL_REQUESTS"
    return 0
  fi
  return 1
}

TAMPER_LIST_FILE="$OUTDIR/meta/sqlmap-tampers.txt"
# ------------------------------- INVENTÁRIO SQLMAP --------------------------
if [[ "$DRY_RUN" == "1" ]]; then
  CHECK_TAMPERS=0
  log_info "DRY_RUN: inventário do sqlmap e validação de tampers desativados."
else
  timeout "$STARTUP_TIMEOUT" "$SQLMAP" --version --batch \
    > "$OUTDIR/meta/sqlmap-version.txt" 2>&1 \
    || log_warn "não foi possível registrar a versão do sqlmap (${STARTUP_TIMEOUT}s)"

  if ! timeout "$STARTUP_TIMEOUT" "$SQLMAP" --list-tampers --batch > "$TAMPER_LIST_FILE" 2>&1; then
    log_warn "--list-tampers não terminou; validação de tampers desativada."
    [[ -s "$TAMPER_LIST_FILE" ]] || CHECK_TAMPERS=0
  fi
fi

# ------------------------------- FLAGS COMUNS -------------------------------
COMMON=(
  --batch
  --answers="quit=N,crack=N,dict=N,continue=Y,follow=N,keep=N"
  --parse-errors --disable-coloring
  -v "$VERBOSE"
  --threads="$THREADS"
  --delay="$DELAY"
  --time-sec="$TIME_DELAY_SEC"
  --timeout="$HTTP_TIMEOUT"
  --retries="$RETRIES"
)
[[ -n "$COOKIE" ]] && COMMON+=(--cookie="$COOKIE")
[[ -n "$PROXY" ]]  && COMMON+=(--proxy="$PROXY")
[[ -n "$DBMS" ]]   && COMMON+=(--dbms="$DBMS")
if [[ -n "$HEADER_FILE" && -f "$HEADER_FILE" ]]; then
  while IFS= read -r header || [[ -n "$header" ]]; do
    header="${header//$'\r'/}"; th="$(trim "$header")"
    [[ -z "$th" || "$th" == \#* ]] && continue
    COMMON+=(-H "$header")
  done < "$HEADER_FILE"
fi

# ------------------------------- MATRIZ DE PASSES ---------------------------
PASS_NAMES=(); PASS_DBMS=(); PASS_FLAGS=(); PASS_TAMPERS=(); PASS_GATE=()

add_pass() { PASS_NAMES+=("$1"); PASS_DBMS+=("$2"); PASS_FLAGS+=("$3"); PASS_TAMPERS+=("$4"); PASS_GATE+=("$5"); }

BASE="--level=$LEVEL --risk=$RISK"

# Cobertura de técnicas (sempre)
add_pass "01_full_cobertura" "any" "$BASE --technique=$TECH" "" "core"
add_pass "02_boolean_error"  "any" "$BASE --technique=BE"    "" "core"
add_pass "03_union_profundo" "any" "$BASE --technique=U --union-cols=1-20 --union-char=NULL" "" "core"
add_pass "04_time_stacked"   "any" "$BASE --technique=T"     "" "core"
add_pass "05_inline_query"   "any" "$BASE --technique=Q"     "" "core"

# Descoberta / transporte
add_pass "06_forms_crawl"    "any" "$BASE --forms --crawl=$MAX_CRAWL_DEPTH --crawl-exclude=logout|sair|logoff|signout" "" "crawl"
add_pass "07_hpp"            "any" "$BASE --hpp --technique=$TECH"      "" "core"
add_pass "08_skip_waf_probe" "any" "$BASE --skip-waf --technique=$TECH" "" "core"

# Invalidação / comparação (sempre)
add_pass "10_invalid_bignum"  "any" "$BASE --invalid-bignum --technique=$TECH"  "" "core"
add_pass "11_invalid_logical" "any" "$BASE --invalid-logical --technique=$TECH" "" "core"
add_pass "12_invalid_string"  "any" "$BASE --invalid-string --technique=$TECH"  "" "core"
add_pass "13_no_cast_escape"  "any" "$BASE --no-cast --no-escape --technique=$TECH" "" "core"

# Tampers genéricos (gate: tampers)
add_pass "20_tamper_space"     "any" "$BASE --technique=$TECH" "space2comment,between,randomcase" "tampers"
add_pass "21_tamper_urlencode" "any" "$BASE --technique=$TECH" "charencode,chardoubleencode"      "tampers"
add_pass "22_tamper_quotes"    "any" "$BASE --technique=$TECH" "apostrophemask,apostrophenullencode" "tampers"
add_pass "23_tamper_keywords"  "any" "$BASE --technique=$TECH" "randomcase,unionalltounion,uppercase" "tampers"
add_pass "24_tamper_comments"  "any" "$BASE --technique=$TECH" "randomcomments,space2comment"     "tampers"

# MySQL/MariaDB (gate: tampers + dbms)
add_pass "30_mysql_versioned"  "mysql" "$BASE --technique=$TECH" "versionedkeywords,versionedmorekeywords,space2mysqlblank" "tampers"
add_pass "31_mysql_legacy"     "mysql" "$BASE --technique=$TECH" "halfversionedmorekeywords,space2mysqldash" "tampers"
add_pass "32_mysql_functions"  "mysql" "$BASE --technique=$TECH" "ifnull2ifisnull,concat2concatws" "tampers"
add_pass "33_mysql_modsec"     "mysql" "$BASE --technique=$TECH" "modsecurityversioned,modsecurityzeroversioned" "tampers"
add_pass "34_mysql_hashspace"  "mysql" "$BASE --technique=$TECH" "space2hash,space2morehash" "tampers"

# MS SQL Server / IIS
add_pass "40_mssql_iis"        "mssql" "$BASE --technique=$TECH" "charunicodeencode,percentage,space2mssqlblank" "tampers"
add_pass "41_mssql_keywords"   "mssql" "$BASE --technique=$TECH" "sp_password,randomcase,space2comment" "tampers"
add_pass "42_mssql_compare"    "mssql" "$BASE --technique=$TECH" "equaltolike,greatest" "tampers"
add_pass "43_mssql_hashspace"  "mssql" "$BASE --technique=$TECH" "space2mssqlhash,space2dash" "tampers"

# PostgreSQL / Oracle / SQLite
add_pass "50_postgresql"        "postgresql" "$BASE --technique=$TECH" "equaltolike,greatest,space2comment" "tampers"
add_pass "51_postgresql_quotes" "postgresql" "$BASE --technique=$TECH" "apostrophemask,randomcase,space2comment" "tampers"
add_pass "60_oracle"            "oracle"     "$BASE --technique=$TECH" "between,greatest,space2comment" "tampers"
add_pass "61_oracle_keywords"   "oracle"     "$BASE --technique=$TECH" "equaltolike,randomcase,space2comment" "tampers"
add_pass "70_sqlite"            "sqlite"     "$BASE --technique=$TECH" "between,randomcase,space2comment" "tampers"

# Enumeração de metadados NÃO-destrutiva (gate: enum + ALLOW_METADATA_ENUMERATION)
ENUM_FLAGS="$BASE --technique=$TECH --fingerprint --banner --current-user --current-db --is-dba --dbs --tables --exclude-sysdbs"

# ------------------------------- ALVOS (URL-only) ---------------------------
mapfile -t RAW_TARGETS < <(
  awk '{ sub(/\r$/,""); if ($0 !~ /^[[:space:]]*(#|$)/) print }' "$TARGETS_FILE"
)
[[ ${#RAW_TARGETS[@]} -gt 0 ]] || die "nenhum alvo válido em $TARGETS_FILE" "$EX_CONFIG"

URLS=()
for line in "${RAW_TARGETS[@]}"; do
  url="$(trim "$line")"
  validate_url "$url" || die "alvo inválido: $url" "$EX_CONFIG"
  is_target_in_scope "$url" "$SCOPE_FILE" || die "alvo fora do escopo: $url (host: $(extract_host "$url"))" "$EX_UNAUTHORIZED"
  URLS+=("$url")
done

# Gera as variantes GET e POST de uma URL. Emite "METHOD|url|data" por linha.
build_variants() {
  local url="$1" base query
  printf 'GET|%s|\n' "$url"
  query="${url#*\?}"
  if [[ "$query" != "$url" && -n "$query" ]]; then
    base="${url%%\?*}"
    printf 'POST|%s|%s\n' "$base" "$query"
  fi
}

# ------------------------------- LEDGER / ESTADO ----------------------------
LEDGER="$OUTDIR/janelas.tsv"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  run_id target_index method url_redacted body_sha256 pass \
  start_iso end_iso duration_s exit_code requests count_kind \
  log_bytes traffic_bytes ua_mode status > "$LEDGER"

TOTAL_REQ=0; TOTAL_LOG=0; TOTAL_TRF=0; TOTAL_PASSES=0; TOTAL_SKIPPED=0
PASS_COUNTER=0; CURRENT_PID=""; LIMIT_REACHED=0

on_interrupt() {
  log_warn "interrupção recebida"
  [[ -n "$CURRENT_PID" ]] && kill -TERM "$CURRENT_PID" 2>/dev/null || true
  exit "$EX_INTERRUPT"
}
trap on_interrupt INT TERM

tamper_chain_available() {
  local chain="$1" item; local -a items
  [[ -z "$chain" || "$CHECK_TAMPERS" != "1" ]] && return 0
  [[ -s "$TAMPER_LIST_FILE" ]] || return 0
  IFS=',' read -r -a items <<< "$chain"
  for item in "${items[@]}"; do
    grep -Eiq "(^|[^[:alnum:]_])${item}(\.py)?([^[:alnum:]_]|$)" "$TAMPER_LIST_FILE" || return 1
  done
  return 0
}

write_row() { printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >> "$LEDGER"; }

# Usa os campos pré-computados por variante (V_URLRED, V_BHASH) para evitar
# spawnar sed/sha256sum a cada passe pulado.
record_skipped() {
  local ti="$1" method="$2" name="$3" reason="$4"
  write_row "$RUN_ID" "$ti" "$method" "$V_URLRED" "$V_BHASH" "$name" \
    "" "" "0" "" "0" "skipped" "0" "0" "-" "skipped:$reason"
  TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
  log_debug "skip $name ($method): $reason"
}

ua_flags_for() { case "$1" in fixed) printf -- '--user-agent=%s' "$USER_AGENT" ;; random) printf -- '--random-agent' ;; esac; }
ua_mode_for_pass() {
  case "$UA_MODE" in
    fixed) echo fixed ;; random) echo random ;;
    mixed) (( PASS_COUNTER % 2 == 0 )) && echo fixed || echo random ;;
  esac
}

run_pass() {
  local ti="$1" method="$2" url="$3" data="$4" name="$5" tamper="$6"; shift 6
  local -a flags=("$@")
  local tag log traffic ua_mode out
  # host/slug/bhash já vêm pré-computados por variante (V_*), sem subprocessos aqui.
  # name é único por passe, então o tag dispensa hash extra.
  tag="$(printf 't%03d__%s__%s__%s' "$ti" "$V_SLUG" "$method" "$name")"
  log="$OUTDIR/logs/${tag}.log"
  traffic="$OUTDIR/traffic/${tag}.traffic"
  ua_mode="$(ua_mode_for_pass)"; PASS_COUNTER=$((PASS_COUNTER + 1))

  local -a req=()
  if is_body_method "$method"; then
    req+=(--method="$method" --data="$data" -H "Content-Type: $(content_type_for "$data")")
  fi
  local uaf; uaf="$(ua_flags_for "$ua_mode")"; [[ -n "$uaf" ]] && req+=("$uaf")
  [[ "$TRAFFIC" == "1" ]] && req+=(-t "$traffic")
  [[ -n "$tamper" ]] && req+=(--tamper="$tamper")

  out="$OUTDIR/sqlmap-data/$tag"; mkdir -p "$out"
  req+=(--output-dir="$out" --flush-session --fresh-queries)

  local -a cmd=("$SQLMAP" -u "$url" "${COMMON[@]}" "${req[@]}" "${flags[@]}")

  printf '[>] [%03d] %-6s %-22s ua=%-6s -> %s\n' "$ti" "$method" "$name" "$ua_mode" "$V_URLRED"

  if [[ "$DRY_RUN" == "1" ]]; then
    log_info "DRY_RUN: $(redacted_command_text "${cmd[@]}")"
    write_row "$RUN_ID" "$ti" "$method" "$V_URLRED" "$V_BHASH" "$name" \
      "" "" "0" "" "0" "dry-run" "0" "0" "$ua_mode" "dry-run"
    return 0
  fi

  if run_budget_exhausted; then
    return 0
  fi

  # O artefato de comando é redigido e não pode ser reexecutado diretamente.
  # O hash do comando normalizado real permite rastreabilidade sem expor dados.
  if [[ "$PRINT_COMMANDS" == "1" ]]; then
    local cfile="$OUTDIR/meta/commands/${tag}.sh" normalized_cmd
    normalized_cmd="$(printf '%q ' "${cmd[@]}")"
    {
      printf '# Valores sensíveis foram redigidos; este arquivo não é diretamente reexecutável.\n'
      redacted_command_text "${cmd[@]}"
      printf '\n'
    } > "$cfile"
    chmod 700 "$cfile"
    sha256_text "$normalized_cmd" > "${cfile}.sha256"
    chmod 600 "${cfile}.sha256"
  fi

  local s_epoch s_iso e_epoch e_iso rc dur ci reqs kind lb tb job_request_limit
  job_request_limit="$MAX_REQUESTS_PER_JOB"
  if [[ "$name" == "06_forms_crawl" && "$MAX_CRAWL_URLS" -lt "$job_request_limit" ]]; then
    # sqlmap não expõe um teto de URLs descobertas; limitar as requisições deste
    # passe oferece um limite superior conservador para a atividade de crawl.
    job_request_limit="$MAX_CRAWL_URLS"
  fi
  s_epoch="$(date -u +%s)"; s_iso="$(date -u -d "@$s_epoch" +%Y-%m-%dT%H:%M:%SZ)"

  "${cmd[@]}" > "$log" 2>&1 &
  CURRENT_PID=$!
  while kill -0 "$CURRENT_PID" 2>/dev/null; do
    local now elapsed observed_ci observed_reqs
    now="$(date -u +%s)"; elapsed=$((now - s_epoch))
    observed_ci="$(count_reqs "$traffic" "$log")"; observed_reqs="${observed_ci%%$'\t'*}"
    [[ "$observed_reqs" =~ ^[0-9]+$ ]] || observed_reqs=0
    if (( elapsed >= MAX_JOB_SECONDS )); then
      mark_limit_reached "MAX_JOB_SECONDS=$MAX_JOB_SECONDS (passe $name)"
    elif (( now - RUN_START_EPOCH >= MAX_RUN_SECONDS )); then
      mark_limit_reached "MAX_RUN_SECONDS=$MAX_RUN_SECONDS"
    elif (( observed_reqs >= job_request_limit )); then
      mark_limit_reached "MAX_REQUESTS_PER_JOB=$job_request_limit (passe $name)"
    elif (( TOTAL_REQ + observed_reqs >= MAX_TOTAL_REQUESTS )); then
      mark_limit_reached "MAX_TOTAL_REQUESTS=$MAX_TOTAL_REQUESTS"
    fi
    if [[ "$LIMIT_REACHED" == "1" ]]; then
      kill -TERM "$CURRENT_PID" 2>/dev/null || true
      break
    fi
    sleep 1
  done
  wait "$CURRENT_PID"; rc=$?; CURRENT_PID=""

  e_epoch="$(date -u +%s)"; e_iso="$(date -u -d "@$e_epoch" +%Y-%m-%dT%H:%M:%SZ)"; dur=$((e_epoch - s_epoch))
  ci="$(count_reqs "$traffic" "$log")"; reqs="${ci%%$'\t'*}"; kind="${ci#*$'\t'}"
  [[ "$reqs" =~ ^[0-9]+$ ]] || reqs=0
  lb="$(fsize "$log")"; tb="$(fsize "$traffic")"

  write_row "$RUN_ID" "$ti" "$method" "$V_URLRED" "$V_BHASH" "$name" \
    "$s_iso" "$e_iso" "$dur" "$rc" "$reqs" "$kind" "$lb" "$tb" "$ua_mode" "executed"

  TOTAL_REQ=$((TOTAL_REQ + reqs)); TOTAL_LOG=$((TOTAL_LOG + lb)); TOTAL_TRF=$((TOTAL_TRF + tb))
  TOTAL_PASSES=$((TOTAL_PASSES + 1))
  (( reqs >= job_request_limit )) && mark_limit_reached "MAX_REQUESTS_PER_JOB=$job_request_limit (passe $name)"
  (( TOTAL_REQ >= MAX_TOTAL_REQUESTS )) && mark_limit_reached "MAX_TOTAL_REQUESTS=$MAX_TOTAL_REQUESTS"
  printf '    %s req (%s) | %ss | rc=%s | acumulado=%s req\n' "$reqs" "$kind" "$dur" "$rc" "$TOTAL_REQ"
  (( COOLDOWN > 0 )) && sleep "$COOLDOWN"
  return 0
}

# ------------------------------- EXECUÇÃO -----------------------------------
log_info "run_id=$RUN_ID perfil=$PROFILE alvos=${#URLS[@]} level=$LEVEL risk=$RISK tech=$TECH dry_run=$DRY_RUN"
log_info "saída: $OUTDIR"
[[ "$(normalize_dbms "$DBMS")" == "any" && "$RUN_ALL_DBMS_TAMPERS" == "1" ]] && \
  log_info "DBMS não definido + RUN_ALL_DBMS_TAMPERS=1: tampers de todos os SGBDs (execução longa)."

target_index=0
for url in "${URLS[@]}"; do
  # Cada variante GET/POST conta como um "alvo" indexado.
  # Pré-computa (uma vez por URL) o que seria repetido a cada passe/variante.
  V_HOST="$(extract_host "$url")"
  V_SLUG="$(sanitize_identifier "$V_HOST")"
  V_URLRED="$(redact_secrets "$url")"

  while IFS='|' read -r method vurl vdata; do
    [[ "$LIMIT_REACHED" == "1" ]] && break
    [[ -z "$method" ]] && continue
    [[ -n "$METHOD_ONLY" && "$method" != "$METHOD_ONLY" ]] && continue
    target_index=$((target_index + 1))
    V_BHASH="$(sha256_text "$vdata")"   # corpo muda entre GET (vazio) e POST
    echo "============================================================================="
    printf 'ALVO [%03d]: %-6s %s\n' "$target_index" "$method" "$(redact_secrets "$vurl")"
    echo "============================================================================="

    for p in "${!PASS_NAMES[@]}"; do
      [[ "$LIMIT_REACHED" == "1" ]] && break
      name="${PASS_NAMES[$p]}"; dbms_sel="${PASS_DBMS[$p]}"
      flag_str="${PASS_FLAGS[$p]}"; tamper="${PASS_TAMPERS[$p]}"; gate="${PASS_GATE[$p]}"

      if [[ -n "$PASS_INCLUDE" && ! "$name" =~ $PASS_INCLUDE ]]; then
        record_skipped "$target_index" "$method" "$name" "fora_do_pass_include"; continue
      fi
      if [[ -n "$PASS_SKIP" && "$name" =~ $PASS_SKIP ]]; then
        record_skipped "$target_index" "$method" "$name" "pass_skip"; continue
      fi

      if [[ "$gate" == "crawl" && "$RUN_CRAWL" != "1" ]]; then
        record_skipped "$target_index" "$method" "$name" "crawl_desativado"; continue
      fi
      if [[ "$gate" == "tampers" && "$RUN_TAMPERS" != "1" ]]; then
        record_skipped "$target_index" "$method" "$name" "tampers_desativados"; continue
      fi
      if ! dbms_applies "$dbms_sel"; then
        record_skipped "$target_index" "$method" "$name" "dbms_incompativel"; continue
      fi
      if ! tamper_chain_available "$tamper"; then
        record_skipped "$target_index" "$method" "$name" "tamper_ausente:$tamper"; continue
      fi

      IFS=' ' read -r -a pass_flags <<< "$flag_str"
      run_pass "$target_index" "$method" "$vurl" "$vdata" "$name" "$tamper" "${pass_flags[@]}"
    done

    # Enumeração de metadados (não-destrutiva), sob dupla condição.
    if [[ "$LIMIT_REACHED" == "1" ]]; then
      break
    elif [[ "$RUN_ENUM" == "1" && "${ALLOW_METADATA_ENUMERATION:-NO}" == "YES" ]]; then
      IFS=' ' read -r -a enum_flags <<< "$ENUM_FLAGS"
      run_pass "$target_index" "$method" "$vurl" "$vdata" "90_enum_metadados" "" "${enum_flags[@]}"
    else
      record_skipped "$target_index" "$method" "90_enum_metadados" "enum_desativada"
    fi
  done < <(build_variants "$url")
done

# ------------------------------- RESUMO -------------------------------------
echo
echo "============================================================================="
echo "RESUMO DA EXECUÇÃO ($RUN_ID)"
echo "============================================================================="
printf 'passes executados .........: %s\n' "$TOTAL_PASSES"
printf 'passes pulados ............: %s\n' "$TOTAL_SKIPPED"
printf 'requisições enviadas ......: %s\n' "$TOTAL_REQ"
printf 'logs do sqlmap ............: %s\n' "$(human "$TOTAL_LOG")"
printf 'dump de tráfego ...........: %s\n' "$(human "$TOTAL_TRF")"
[[ "$LIMIT_REACHED" == "1" ]] && printf 'limite operacional ........: atingido\n'
echo
echo "[✓] Ledger: $LEDGER"
echo "[✓] Logs: $OUTDIR/logs   Tráfego: $OUTDIR/traffic   Comandos: $OUTDIR/meta/commands"
