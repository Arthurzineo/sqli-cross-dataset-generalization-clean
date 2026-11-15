#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_DIR="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
COMPOSE=(docker compose --project-directory "${PROJECT_DIR}" --profile attack-tools)
SERVICE="kali-tools"

usage() {
  cat <<'EOF'
Uso: tools/kali_toolbox.sh COMANDO [ARGUMENTOS]

Comandos:
  build                 constroi somente a imagem Kali
  up                    constroi e inicia o toolbox em segundo plano
  status                mostra estado, usuario, redes e alvo interno
  versions              mostra as versoes de sqlmap, ffuf e wfuzz
  doctor                valida isolamento, ferramentas e HTTPS interno
  shell                 abre um bash interativo dentro do toolbox
  plan TOOL VETOR ...   mostra o comando SQLi sem enviar requisicoes
  run TOOL VETOR ...    executa com confirmacao explicita da fase 22
  exec FERRAMENTA ...   executa sqlmap, ffuf, wfuzz, curl, jq ou python3
  stop                  para somente o toolbox, sem apagar volumes

O container nao possui egress externo e enxerga apenas o Nginx do laboratorio.
Subir ou diagnosticar o toolbox nao inicia a campanha SQLi.
EOF
}

die() {
  printf 'erro: %s\n' "$*" >&2
  exit 2
}

require_docker() {
  command -v docker >/dev/null 2>&1 || die "Docker nao encontrado"
  docker compose version >/dev/null 2>&1 || die "Docker Compose v2 nao encontrado"
}

is_running() {
  [[ "$("${COMPOSE[@]}" ps --status running --quiet "${SERVICE}")" != "" ]]
}

require_running() {
  is_running || die "${SERVICE} nao esta em execucao; use '$0 up'"
}

container_exec() {
  "${COMPOSE[@]}" exec -T "${SERVICE}" "$@"
}

require_docker
command="${1:-help}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "${command}" in
  build)
    [[ $# -eq 0 ]] || die "build nao aceita argumentos"
    "${COMPOSE[@]}" build "${SERVICE}"
    ;;
  up)
    [[ $# -eq 0 ]] || die "up nao aceita argumentos"
    # The laboratory is managed separately.  --no-deps prevents this helper from
    # rebuilding or restarting app/nginx merely because kali-tools depends on nginx.
    "${COMPOSE[@]}" up --build --detach --no-deps "${SERVICE}"
    ;;
  status)
    [[ $# -eq 0 ]] || die "status nao aceita argumentos"
    "${COMPOSE[@]}" ps "${SERVICE}"
    if is_running; then
      container_exec sh -c 'printf "user=%s uid=%s target=%s\\n" "$(id -un)" "$(id -u)" "$TARGET_URL"'
      container_id="$("${COMPOSE[@]}" ps --quiet "${SERVICE}")"
      docker inspect --format 'readonly={{.HostConfig.ReadonlyRootfs}} privileged={{.HostConfig.Privileged}} capabilities={{json .HostConfig.CapDrop}} networks={{range $name, $_ := .NetworkSettings.Networks}}{{$name}} {{end}}' "${container_id}"
    fi
    ;;
  versions)
    [[ $# -eq 0 ]] || die "versions nao aceita argumentos"
    require_running
    container_exec sh -c 'sqlmap --version; ffuf -V; wfuzz --version'
    ;;
  doctor)
    [[ $# -eq 0 ]] || die "doctor nao aceita argumentos"
    require_running
    container_exec sh -c '
      set -eu
      test "$(id -u)" -ne 0
      test "$TARGET_URL" = "https://nginx"
      test -r /payloads/wordlists/sqli-ALL-merged-dedup.txt
      test ! -w /payloads/wordlists/sqli-ALL-merged-dedup.txt
      command -v sqlmap >/dev/null
      command -v ffuf >/dev/null
      command -v wfuzz >/dev/null
      test "$(curl -k -sS -o /dev/null -w "%{http_code}" "$TARGET_URL/")" = "200"
      printf "doctor=OK user=%s target=%s payloads=read-only\\n" "$(id -un)" "$TARGET_URL"
    '
    ;;
  shell)
    [[ $# -eq 0 ]] || die "shell nao aceita argumentos"
    require_running
    "${COMPOSE[@]}" exec "${SERVICE}" bash
    ;;
  plan)
    require_running
    [[ $# -ge 2 ]] || die "uso: plan TOOL VETOR [opcoes]"
    container_exec lab-sqli-tools "$@"
    ;;
  run)
    require_running
    [[ $# -ge 2 ]] || die "uso: run TOOL VETOR [opcoes]"
    "${COMPOSE[@]}" exec -T -e LAB_ATTACK_CONFIRM=project2-phase26 "${SERVICE}" \
      lab-sqli-tools "$@" --execute
    ;;
  exec)
    require_running
    [[ $# -gt 0 ]] || die "informe a ferramenta e seus argumentos"
    tool="$1"
    shift
    case "${tool}" in
      sqlmap|ffuf|wfuzz|curl|jq|python3) ;;
      *) die "ferramenta nao permitida: ${tool}" ;;
    esac
    container_exec "${tool}" "$@"
    ;;
  stop)
    [[ $# -eq 0 ]] || die "stop nao aceita argumentos"
    "${COMPOSE[@]}" stop "${SERVICE}"
    ;;
  help|-h|--help)
    usage
    ;;
  *)
    usage >&2
    die "comando desconhecido: ${command}"
    ;;
esac
