#!/usr/bin/env bash
# XSS via POST (dalfox job 30_form) nos endpoints de formulario do OJS.
# Injeta payloads do xss.txt nos campos do corpo. POST-only (reflected/mining/
# GET-payloads desligados). User-Agent = Chrome fixo (defaults.env).
# Teto de 15 min por job (MAX_JOB_SECONDS=900) pra endpoint lento nao travar.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT" || exit 1
source "$ROOT/scripts/common.sh"
PROFILE=aggressive
umask 077
require_authorization

XSS=wordlists/custom/xss.txt
PARTDIR=wordlists/generated/xss-post-parts
mkdir -p "$PARTDIR"; rm -f "$PARTDIR"/part_*
split -n l/3 -d "$XSS" "$PARTDIR/part_"
mapfile -t PARTS < <(ls "$PARTDIR"/part_* | sort)

# Três endpoints de formulário lidos da configuração local não versionada.
TARGETS_FILE="${TARGETS_FILE:-config/targets.txt}"
[[ -r "$TARGETS_FILE" ]] || { echo "Crie $TARGETS_FILE a partir de config/targets.txt.example" >&2; exit 2; }
mapfile -t URLS < <(grep -Ev '^[[:space:]]*(#|$)' "$TARGETS_FILE")
(( ${#URLS[@]} >= 3 )) || { echo "$TARGETS_FILE precisa conter ao menos 3 URLs" >&2; exit 2; }
BODIES=(
  'source=test'
  'username=test&password=test'
  'username=test&password=test&email=test@test.local&givenName=test&familyName=test'
)

echo "== Particoes XSS-POST =="
wc -l "$PARTDIR"/part_*
echo "== Execucao =="

for i in 0 1 2; do
  url="${URLS[$i]}"
  body="${BODIES[$i]}"
  part="${PARTS[$i]}"
  tf="config/targets-dalfoxpost-$i.txt"
  echo "$url" > "$tf"
  echo "[post $i] url=$url body=$body wordlist=$part"
  RUN_ID="dalfoxpost_part$i" \
  PROFILE=aggressive \
  MAX_JOB_SECONDS=900 \
  RUN_DALFOX_REFLECTED=0 RUN_DALFOX_MINING=0 RUN_DALFOX_PAYLOADS=0 RUN_DALFOX_FORM=1 \
  DALFOX_FORM_DATA="$body" \
  DALFOX_XSS_RAW_WORDLIST="$part" \
  bash scripts/dalfox-sweep.sh --targets "$tf" --scope config/scope.txt --profile aggressive
done

echo "== Concluido: 3 endpoints POST x XSS (form) =="
