#!/usr/bin/env bash
# =============================================================================
# test_target_parser.sh — testes SEM rede para helpers de parsing/validação.
# =============================================================================
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
source "$ROOT/scripts/common.sh"

pass=0; fail=0
ok()   { pass=$((pass+1)); printf 'ok   - %s\n' "$1"; }
bad()  { fail=$((fail+1)); printf 'FAIL - %s\n' "$1"; }

# validate_method
for m in GET POST PUT PATCH DELETE; do validate_method "$m" && ok "metodo $m" || bad "metodo $m"; done
validate_method "TRACE" && bad "TRACE deveria falhar" || ok "TRACE rejeitado"

# validate_url
validate_url "http://app.lab.local/x?y=1" 2>/dev/null && ok "url http valida" || bad "url http valida"
validate_url "ftp://app.lab.local/" 2>/dev/null && bad "ftp deveria falhar" || ok "ftp rejeitado"
validate_url "http://app.lab.local/#frag" 2>/dev/null && bad "fragmento deveria falhar" || ok "fragmento rejeitado"

# extract_host / extract_port
[[ "$(extract_host "https://API.Lab.Local:8443/a")" == "api.lab.local" ]] && ok "host minusculo" || bad "host minusculo"
[[ "$(extract_port "https://api.lab.local/a")" == "443" ]] && ok "porta https default" || bad "porta https default"

# sanitize_identifier
[[ "$(sanitize_identifier "a b/c*d")" == "a_b_c_d" ]] && ok "sanitize id" || bad "sanitize id"

# validate_integer
( validate_integer X 5 1 10 ) 2>/dev/null && ok "inteiro valido" || bad "inteiro valido"
( validate_integer X abc 1 10 ) 2>/dev/null && bad "abc deveria falhar" || ok "abc rejeitado"

# redact_secrets
out="$(redact_secrets 'Authorization: Bearer abc123 password=hunter2')"
[[ "$out" != *"hunter2"* && "$out" != *"abc123"* ]] && ok "segredos mascarados" || bad "segredos mascarados"

printf '\n%s passaram, %s falharam\n' "$pass" "$fail"
[[ "$fail" -eq 0 ]]
