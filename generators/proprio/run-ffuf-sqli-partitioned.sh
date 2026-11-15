#!/usr/bin/env bash
# Particiona o dataset SQLi (wordlists/custom/sqli.txt) em 5 fatias de ~3000 e
# roda ffuf-sqli (GET+POST) com uma fatia por URL, em 5 endpoints distintos.
# User-Agent = Chrome fixo (defaults.env). DRY_RUN=1 valida sem enviar rede.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1
source "$ROOT/scripts/common.sh"
PROFILE=aggressive
umask 077
require_authorization

SQLI=wordlists/custom/sqli.txt
PARTDIR=wordlists/generated/sqli-parts
mkdir -p "$PARTDIR"
rm -f "$PARTDIR"/part_*

# 5 fatias por numero de linhas (~3000 cada), sem quebrar linhas.
split -n l/5 -d "$SQLI" "$PARTDIR/part_"

mapfile -t PARTS < <(ls "$PARTDIR"/part_* | sort)

# Os alvos reais ficam fora do repositório.
TARGETS_FILE="${TARGETS_FILE:-config/targets.txt}"
[[ -r "$TARGETS_FILE" ]] || { echo "Crie $TARGETS_FILE a partir de config/targets.txt.example" >&2; exit 2; }
mapfile -t URLS < <(grep -Ev '^[[:space:]]*(#|$)' "$TARGETS_FILE")
(( ${#URLS[@]} >= 5 )) || { echo "$TARGETS_FILE precisa conter ao menos 5 URLs" >&2; exit 2; }

echo "== Particoes =="
wc -l "$PARTDIR"/part_*
echo "== Execucao =="

for i in 0 1 2 3 4; do
  url="${URLS[$i]}"
  part="${PARTS[$i]}"
  tf="config/targets-ffsqli-$i.txt"
  echo "$url" > "$tf"
  echo "[part $i] url=$url wordlist=$part"
  RUN_ID="ffsqli_part$i" \
  PROFILE=aggressive \
  FFUF_SQLI_RAW_WORDLIST="$part" \
  bash scripts/ffuf-sqli-sweep.sh --targets "$tf" --scope config/scope.txt --profile aggressive
done

echo "== Concluido: 5 URLs x ~3000 payloads (GET+POST) =="
