#!/usr/bin/env bash
# Local host -> Cooking Wiki (Docker :8444)
HOST=${LAB_HOST:-localhost}
PORT=${LAB_PORT:-8444}

echo "CHECKING CONNECTIVITY TO https://${HOST}:${PORT}/"
curl -sk -m 6 -o /dev/null -w "configured_https=%{http_code}\n" "https://${HOST}:${PORT}/" 2>/dev/null || echo "configured_https=FAIL"
curl -sk -m 6 -o /dev/null -w "loopback_https=%{http_code}\n"  "https://127.0.0.1:${PORT}/" 2>/dev/null || echo "loopback_https=FAIL"

# Ferramentas locais presentes?
echo "TOOLS:"
for t in curl python3 sqlite3 docker; do printf "  %s=%s\n" "$t" "$(command -v $t >/dev/null 2>&1 && echo yes || echo NO)"; done
echo LOCAL_CONN_DONE
