#!/usr/bin/env bash
# =============================================================================
# scripts/common.sh — biblioteca compartilhada (sourced, não executável).
#
#   Uso nos scripts:
#     source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
#
# Contém logging, validação de escopo/URL, parser de alvos, identificação de
# execução, mascaramento de segredos, locks e utilidades. Não executa nenhuma
# ferramenta ofensiva nem faz chamadas de rede.
#
# Baseado nos helpers verificados do sqlmap.sh de referência.
# Compatível com Bash 4.4+.
# =============================================================================

# Evita ser sourced duas vezes.
[[ -n "${__COMMON_SH_LOADED:-}" ]] && return 0
__COMMON_SH_LOADED=1

# ------------------------------- CÓDIGOS DE SAÍDA ---------------------------
readonly EX_OK=0
readonly EX_USAGE=64          # erro de uso / argumento inválido
readonly EX_UNAUTHORIZED=77   # autorização/escopo negados
readonly EX_UNAVAILABLE=69    # dependência ausente
readonly EX_CONFIG=78         # configuração inválida
readonly EX_INTERRUPT=130     # SIGINT

# ------------------------------- LOGGING ------------------------------------
# Níveis: DEBUG < INFO < WARN < ERROR
LOG_LEVEL="${LOG_LEVEL:-INFO}"
LOG_FORMAT="${LOG_FORMAT:-text}"

__log_level_num() {
  case "$1" in
    DEBUG) echo 10 ;; INFO) echo 20 ;; WARN) echo 30 ;; ERROR) echo 40 ;;
    *) echo 20 ;;
  esac
}

__log() {
  local level="$1"; shift
  local msg="$*"
  (( $(__log_level_num "$level") < $(__log_level_num "$LOG_LEVEL") )) && return 0

  local ts run="${RUN_ID:-}" tool="${TOOL_NAME:-}" target="${TARGET_ID:-}"
  ts="$(date +%Y-%m-%dT%H:%M:%S%z)"
  msg="$(redact_secrets "$msg")"

  if [[ "$LOG_FORMAT" == "jsonl" ]]; then
    printf '{"ts":"%s","level":"%s","run_id":"%s","tool":"%s","target_id":"%s","message":%s}\n' \
      "$ts" "$level" "$run" "$tool" "$target" "$(json_escape "$msg")" >&2
  else
    printf '%s %-5s run=%s tool=%s target=%s %s\n' \
      "$ts" "$level" "${run:-–}" "${tool:-–}" "${target:-–}" "$msg" >&2
  fi
}

log_debug() { __log DEBUG "$@"; }
log_info()  { __log INFO  "$@"; }
log_warn()  { __log WARN  "$@"; }
log_error() { __log ERROR "$@"; }
die()       { log_error "$@"; exit "${2:-1}"; }

# ------------------------------- REQUISITOS ---------------------------------
require_command() {
  command -v "$1" >/dev/null 2>&1 || die "comando obrigatório não encontrado: $1" "$EX_UNAVAILABLE"
}

require_file() {
  [[ -f "$1" ]] || die "arquivo obrigatório não existe: $1" "$EX_CONFIG"
}

# Exige AUTHORIZED_SECURITY_TESTING=YES (exato). Perfil aggressive exige também
# DANGEROUS_ACK=YES. Chame no início de cada script antes de qualquer ação.
require_authorization() {
  [[ "${AUTHORIZED_SECURITY_TESTING:-}" == "YES" ]] || die \
    "execução bloqueada: defina AUTHORIZED_SECURITY_TESTING=YES apenas em ambiente autorizado." \
    "$EX_UNAUTHORIZED"

  if [[ "${PROFILE:-}" == "aggressive" && "${DANGEROUS_ACK:-}" != "YES" ]]; then
    die "perfil aggressive exige DANGEROUS_ACK=YES (laboratório isolado e descartável)." "$EX_UNAUTHORIZED"
  fi
}

# ------------------------------- STRINGS ------------------------------------
trim() {
  local v="$1"
  v="${v#"${v%%[![:space:]]*}"}"
  v="${v%"${v##*[![:space:]]}"}"
  printf '%s' "$v"
}

lower() { tr '[:upper:]' '[:lower:]' <<<"$1"; }
upper() { tr '[:lower:]' '[:upper:]' <<<"$1"; }

json_escape() {
  # Escapa uma string para valor JSON (com aspas). Usa python3 se disponível.
  if command -v python3 >/dev/null 2>&1; then
    python3 -c 'import json,sys; print(json.dumps(sys.argv[1]))' "$1"
  else
    local s="$1"
    s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; s="${s//$'\n'/\\n}"; s="${s//$'\t'/\\t}"
    printf '"%s"' "$s"
  fi
}

# ------------------------------- HASH / IDs ---------------------------------
hash_string() { printf '%s' "$1" | sha256sum | awk '{print $1}'; }

sanitize_identifier() {
  # Mantém apenas [A-Za-z0-9._-]; troca o resto por "_"; remove _ nas pontas.
  local id
  id="$(tr -cs '[:alnum:]._-' '_' <<<"$1")"
  id="${id#_}"; id="${id%_}"
  printf '%s' "$id"
}

# YYYYMMDD-HHMMSS-<random6>
new_run_id() {
  printf '%s-%s' "$(date +%Y%m%d-%H%M%S)" "$(hash_string "$RANDOM$$$(date +%s%N)" | cut -c1-6)"
}

# ------------------------------- VALIDAÇÃO ----------------------------------
validate_integer() {
  local name="$1" value="$2" min="${3:-}" max="${4:-}"
  [[ "$value" =~ ^[0-9]+$ ]] || die "$name deve ser inteiro não-negativo: '$value'" "$EX_USAGE"
  [[ -n "$min" && "$value" -lt "$min" ]] && die "$name < mínimo ($min): $value" "$EX_USAGE"
  [[ -n "$max" && "$value" -gt "$max" ]] && die "$name > máximo ($max): $value" "$EX_USAGE"
  return 0
}

validate_method() {
  case "$(upper "$(trim "$1")")" in
    GET|POST|PUT|PATCH|DELETE) return 0 ;;
    *) return 1 ;;
  esac
}

is_body_method() {
  case "$(upper "$1")" in
    POST|PUT|PATCH|DELETE) return 0 ;;
    *) return 1 ;;
  esac
}

# Valida esquema http/https, presença de host, ausência de fragmento e de
# caracteres de controle. Usa python3 (urllib) para parsing robusto.
validate_url() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import urlsplit
url = sys.argv[1]
try:
    p = urlsplit(url)
except ValueError as e:
    print(f"URL inválida: {e}", file=sys.stderr); raise SystemExit(1)
if p.scheme.lower() not in {"http", "https"}:
    print("a URL deve usar http:// ou https://", file=sys.stderr); raise SystemExit(1)
if not p.hostname:
    print("a URL não possui hostname", file=sys.stderr); raise SystemExit(1)
if p.fragment:
    print("fragmentos #... não são enviados ao servidor", file=sys.stderr); raise SystemExit(1)
if any(c in url for c in "\r\n\t"):
    print("a URL contém caractere de controle", file=sys.stderr); raise SystemExit(1)
PY
}

extract_host() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import urlsplit
p = urlsplit(sys.argv[1])
if p.scheme.lower() not in {"http", "https"} or not p.hostname:
    raise SystemExit(2)
print(p.hostname.rstrip(".").lower())
PY
}

extract_port() {
  python3 - "$1" <<'PY'
import sys
from urllib.parse import urlsplit
p = urlsplit(sys.argv[1])
port = p.port
if port is None:
    port = 443 if p.scheme.lower() == "https" else 80
print(port)
PY
}

# ------------------------------- ESCOPO -------------------------------------
# Rejeita curingas amplos (*, *.com, 0.0.0.0/0, TLDs inteiros). Aceita:
#   host exato | host:porta | IPv4 | CIDR IPv4 | *.sub.dominio (intencional).
# Retorna 0 se o alvo estiver no escopo; 1 caso contrário.
is_target_in_scope() {
  local url="$1" scope="${2:-$SCOPE_FILE}"
  local host entry suffix
  host="$(extract_host "$url")" || return 1

  [[ -f "$scope" ]] || return 1
  [[ -s "$scope" ]] || return 1

  while IFS= read -r entry || [[ -n "$entry" ]]; do
    entry="${entry%%#*}"
    entry="$(trim "${entry//$'\r'/}")"
    [[ -z "$entry" ]] && continue
    entry="$(lower "${entry%.}")"

    # Rejeição de curingas perigosos
    case "$entry" in
      '*'|'*.'*'.'* ) : ;;   # *.sub.dominio é ok; tratamos abaixo
    esac
    [[ "$entry" == '*' ]] && { log_warn "escopo: curinga '*' ignorado"; continue; }
    [[ "$entry" == '0.0.0.0/0' ]] && { log_warn "escopo: '0.0.0.0/0' ignorado"; continue; }

    if [[ "$entry" == \*.* ]]; then
      suffix="${entry#*.}"
      # Rejeita wildcard sobre TLD inteiro (ex.: *.com) — precisa de >=2 rótulos.
      if [[ "$suffix" != *.* ]]; then
        log_warn "escopo: wildcard amplo demais ignorado: $entry"
        continue
      fi
      [[ "$host" == "$suffix" || "$host" == *".$suffix" ]] && return 0
    else
      # remove porta da entrada para comparar só o host
      [[ "$host" == "${entry%%:*}" ]] && return 0
    fi
  done < "$scope"

  return 1
}

# ------------------------------- SEGREDOS -----------------------------------
# Mascara valores sensíveis em uma string (para logs/manifesto/dry-run).
# Headers cujo valor pode conter espaços (Authorization/Cookie/Set-Cookie) são
# mascarados até o fim da linha — over-masking é o lado seguro do erro. Pares
# chave=valor (password/token/apikey/secret/csrf) mascaram o token do valor.
redact_secrets() {
  local s="$1"
  s="$(sed -E \
      -e 's/([Aa]uthorization:[[:space:]]*).*/\1***REDACTED***/g' \
      -e 's/([Cc]ookie:[[:space:]]*).*/\1***REDACTED***/g' \
      -e 's/([Ss]et-[Cc]ookie:[[:space:]]*).*/\1***REDACTED***/g' \
      -e 's/(([Pp]assword|[Tt]oken|[Aa]pi[_-]?key|[Ss]ecret|[Cc]srf[_-]?token)[=:][[:space:]]*)[^&[:space:]]+/\1***REDACTED***/g' \
      <<<"$s")"
  printf '%s' "$s"
}

# ------------------------------- FS / RUN -----------------------------------
create_run_directory() {
  local base="$1" run="$2"
  local dir="$base/$run"
  mkdir -p "$dir"/{sqlmap,ffuf,ffuf-sqli,dalfox,xsstrike}
  printf '%s' "$dir"
}

check_disk_space() {
  local path="$1" min_gb="${2:-$MIN_FREE_DISK_GB}"
  local free_kb free_gb
  free_kb="$(df -Pk "$path" 2>/dev/null | awk 'NR==2 {print $4}')"
  [[ -z "$free_kb" ]] && { log_warn "não foi possível checar espaço em disco de $path"; return 0; }
  free_gb=$(( free_kb / 1024 / 1024 ))
  (( free_gb < min_gb )) && die "espaço em disco insuficiente: ${free_gb}GB < ${min_gb}GB" "$EX_CONFIG"
  return 0
}

check_output_permissions() {
  local dir="$1"
  [[ -d "$dir" ]] || mkdir -p "$dir"
  [[ -w "$dir" ]] || die "sem permissão de escrita em: $dir" "$EX_CONFIG"
}

# ------------------------------- LOCKS --------------------------------------
acquire_lock() {
  # Lock por diretório (atômico e portável). $1 = caminho base do lock.
  local lockdir="${1}.lock"
  if mkdir "$lockdir" 2>/dev/null; then
    printf '%s\n' "$$" > "$lockdir/pid"
    __ACTIVE_LOCK="$lockdir"
    return 0
  fi
  return 1
}

release_lock() {
  local lockdir="${1:-$__ACTIVE_LOCK}"
  [[ -n "$lockdir" && -d "$lockdir" ]] && rm -rf "$lockdir"
  __ACTIVE_LOCK=""
}

# ------------------------------- ENV / CONFIG -------------------------------
# Carrega um arquivo .env simples (KEY=VALUE), ignorando comentários/vazios.
# Não usa `source` para evitar execução de código arbitrário no arquivo.
load_env_file() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  local line key value
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%$'\r'}"
    line="$(trim "$line")"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" != *=* ]] && continue
    key="$(trim "${line%%=*}")"
    value="${line#*=}"
    value="$(trim "$value")"
    # remove aspas externas, ou comentário inline ( # precedido de espaço) em
    # valores não-citados — preservando # dentro de valores entre aspas.
    if [[ "$value" == \"*\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' ]]; then
      value="${value:1:${#value}-2}"
    else
      value="${value%%[[:space:]]#*}"
      value="$(trim "$value")"
    fi
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    export "$key=$value"
  done < "$file"
}

# Carrega defaults -> profile -> .env. Variáveis exportadas pelo ambiente têm
# precedência sobre os arquivos, conforme documentado em config/defaults.env.
load_configuration() {
  local root="${1:-.}" profile="${PROFILE:-safe}" file line key
  local -a files=(
    "$root/config/defaults.env"
    "$root/config/profiles/${profile}.env"
    "$root/.env"
  )
  local -A environment_values=()

  # Registra somente valores que vieram do ambiente, não defaults de helpers
  # já carregados neste shell. Assim, os arquivos ainda podem definir defaults
  # e o ambiente permanece a última camada da configuração.
  for file in "${files[@]}"; do
    [[ -f "$file" ]] || continue
    while IFS= read -r line || [[ -n "$line" ]]; do
      line="${line%%$'\r'}"
      line="$(trim "$line")"
      [[ -z "$line" || "$line" == \#* || "$line" != *=* ]] && continue
      key="$(trim "${line%%=*}")"
      [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
      [[ -n "${environment_values[$key]+present}" ]] && continue
      [[ "$(declare -p "$key" 2>/dev/null)" == declare\ -x* ]] || continue
      environment_values["$key"]="${!key}"
    done < "$file"
  done

  load_env_file "$root/config/defaults.env"
  if [[ "$profile" == "custom" ]]; then
    load_env_file "$root/config/profiles/custom.env"
  else
    load_env_file "$root/config/profiles/${profile}.env"
  fi
  load_env_file "$root/.env"

  for key in "${!environment_values[@]}"; do
    export "$key=${environment_values[$key]}"
  done
}

# ------------------------------- SO -----------------------------------------
detect_os() {
  case "$(uname -s 2>/dev/null)" in
    Linux*)  echo linux ;;
    Darwin*) echo macos ;;
    MINGW*|MSYS*|CYGWIN*) echo windows ;;
    *) echo unknown ;;
  esac
}

# ------------------------------- FIM ----------------------------------------
return 0 2>/dev/null || true
