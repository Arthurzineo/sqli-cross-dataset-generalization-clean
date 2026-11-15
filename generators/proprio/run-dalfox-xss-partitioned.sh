#!/usr/bin/env bash
# Particiona o dataset XSS (wordlists/custom/xss.txt) em 5 fatias de ~3000 e
# roda dalfox (reflected + mining + payloads, GET) com uma fatia por URL, em 5
# endpoints. User-Agent = Chrome fixo (defaults.env). DRY_RUN=1 valida sem rede.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1
source "$ROOT/scripts/common.sh"
PROFILE=aggressive
umask 077
require_authorization

XSS=wordlists/custom/xss.txt
PARTDIR=wordlists/generated/xss-parts
mkdir -p "$PARTDIR"
rm -f "$PARTDIR"/part_*
split -n l/5 -d "$XSS" "$PARTDIR/part_"
mapfile -t PARTS < <(ls "$PARTDIR"/part_* | sort)

# Os alvos reais ficam fora do repositório.
TARGETS_FILE="${TARGETS_FILE:-config/targets.txt}"
[[ -r "$TARGETS_FILE" ]] || { echo "Crie $TARGETS_FILE a partir de config/targets.txt.example" >&2; exit 2; }
mapfile -t URLS < <(grep -Ev '^[[:space:]]*(#|$)' "$TARGETS_FILE")
(( ${#URLS[@]} >= 5 )) || { echo "$TARGETS_FILE precisa conter ao menos 5 URLs" >&2; exit 2; }

echo "== Particoes XSS =="
wc -l "$PARTDIR"/part_*
echo "== Execucao =="

for i in 0 1 2 3 4; do
  url="${URLS[$i]}"
  part="${PARTS[$i]}"
  tf="config/targets-dalfox-$i.txt"
  echo "$url" > "$tf"
  echo "[part $i] url=$url wordlist=$part"
  RUN_ID="dalfox_part$i" \
  PROFILE=aggressive \
  RUN_DALFOX_MINING=1 \
  DALFOX_XSS_RAW_WORDLIST="$part" \
  bash scripts/dalfox-sweep.sh --targets "$tf" --scope config/scope.txt --profile aggressive
done

echo "== Concluido: 5 URLs x reflected+mining+payloads (~3000 XSS cada, GET) =="
