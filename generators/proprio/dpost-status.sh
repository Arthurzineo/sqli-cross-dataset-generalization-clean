#!/usr/bin/env bash
# Status do dalfox XSS-POST (3 endpoints de formulario).
cd ~/TCC_SCRIPTS || exit 1
echo "=== DPOST STATUS $(date +%H:%M:%S) ==="
worker=$(pgrep -af dalfox | grep -v bash | tail -1 | cut -c1-95)
jsons=$(ls output/dalfoxpost_part*/dalfox/results/*.json 2>/dev/null | wc -l)
sweep=$(pgrep -f dalfox-sweep | head -1)
fim=$(grep -c Concluido /tmp/dpost-run.log 2>/dev/null)
cur=$(grep -a '\[post ' /tmp/dpost-run.log 2>/dev/null | tail -1 | cut -c1-90)
echo "worker=${worker:-NENHUM}"
echo "jsons=$jsons sweep=${sweep:-NENHUM/terminado} fim=$fim"
echo "ultimo: $cur"
