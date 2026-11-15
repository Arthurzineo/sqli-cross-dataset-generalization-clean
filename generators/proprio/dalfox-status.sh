#!/usr/bin/env bash
# Status do dalfox XSS particionado (5 partes x 3 jobs = 15 no total).
cd ~/TCC_SCRIPTS || exit 1
echo "=== DALFOX STATUS $(date +%H:%M:%S) ==="
dp=$(pgrep -f dalfox | head -1)
done=$(ls output/dalfox_part*/dalfox/results/*.json 2>/dev/null | wc -l)
resv=$(grep -h dalfox output/dalfox_part*/dalfox/janelas.tsv 2>/dev/null | awk -F'\t' '{s+=$14} END{print s+0}')
echo "dalfox: pid=${dp:-NENHUM/terminado} jobs_concluidos=$done/15 requests_reservados=$resv"
cur=$(grep -a '\[part ' /tmp/dalfox-run.log 2>/dev/null | tail -1)
echo "$cur"
tail -c 400 /tmp/dalfox-run.log 2>/dev/null | tr '\r' '\n' | grep -a -e '\[>\]' -e 'RESUMO' | tail -1
