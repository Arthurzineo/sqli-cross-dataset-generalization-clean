#!/usr/bin/env bash
# =============================================================================
# test_scope_validation.sh — testes SEM rede para is_target_in_scope().
# =============================================================================
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
source "$ROOT/scripts/common.sh"

pass=0; fail=0
scope="$(mktemp)"; trap 'rm -f "$scope"' EXIT
cat > "$scope" <<'EOF'
app.lab.local
api.lab.local:8443
10.10.20.15
*.sqli.lab.local
EOF

check() { # descrição | url | esperado(0=in,1=out)
  local desc="$1" url="$2" want="$3"
  if is_target_in_scope "$url" "$scope"; then got=0; else got=1; fi
  if [[ "$got" == "$want" ]]; then pass=$((pass+1)); printf 'ok   - %s\n' "$desc"
  else fail=$((fail+1)); printf 'FAIL - %s (want=%s got=%s)\n' "$desc" "$want" "$got"; fi
}

check "host exato in-scope"        "http://app.lab.local/x"        0
check "host com porta in-scope"    "https://api.lab.local:8443/y"  0
check "IPv4 exato in-scope"        "http://10.10.20.15/z"          0
check "wildcard sub in-scope"      "http://a.sqli.lab.local/"      0
check "host fora do escopo"        "http://evil.com/"              1
check "subdominio nao autorizado"  "http://x.app.lab.local/"       1

printf '\n%s passaram, %s falharam\n' "$pass" "$fail"
[[ "$fail" -eq 0 ]]
