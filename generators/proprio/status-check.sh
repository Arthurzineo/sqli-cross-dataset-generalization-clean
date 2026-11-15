#!/usr/bin/env bash
# Status combinado: ffuf-sqli particionado + sqlmap source0770post.
cd ~/TCC_SCRIPTS || exit 1
echo "=== STATUS $(date +%H:%M:%S) ==="

# --- ffuf-sqli particionado (5 partes x GET+POST = 10 jobs) ---
fp=$(pgrep -f ffuf | head -1)
done_jobs=$(ls output/ffsqli_part*/ffuf-sqli/results/*.json 2>/dev/null | wc -l)
newest=$(ls -t output/ffsqli_part*/ffuf-sqli/logs/*.log 2>/dev/null | head -1)
part=$(printf '%s' "$newest" | grep -oE 'ffsqli_part[0-9]')
echo "ffuf: pid=${fp:-NENHUM} jobs_concluidos=$done_jobs/10 parte_atual=${part:-?}"
if [ -n "$newest" ]; then
  meth=$(printf '%s' "$newest" | grep -oE '(GET|POST)')
  echo "ffuf: job=$meth $(tail -c 240 "$newest" | tr '\r' '\n' | grep -a Progress | tail -1)"
fi

# --- sqlmap source0770post ---
sp=$(pgrep -f source0770post | head -1)
sreq=$(grep -rhoE POST./etc output/source0770post/sqlmap/traffic 2>/dev/null | wc -l)
pass=$(grep ua= /tmp/source0770post.log 2>/dev/null | tail -1 | grep -oE '[0-9]+_[a-z_]+' | head -1)
echo "sqlmap: pid=${sp:-NENHUM/terminado} posts=$sreq pass=${pass:-?}"
