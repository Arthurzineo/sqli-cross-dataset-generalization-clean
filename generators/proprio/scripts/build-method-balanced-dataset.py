#!/usr/bin/env python3
"""Monta um dataset rotulado balanceado POR METODO.

Diferente do build-labeled-dataset.py (que equilibra benigno vs ataque no TOTAL),
aqui cada metodo HTTP fica com benigno == ataque, para eliminar o vies
"POST => ataque" / "GET => benigno". As cotas por metodo sao passadas na linha
de comando (tipicamente = ao estoque de benigno de cada metodo).

Colunas de saida: timestamp, method, url, body, malicioso, xss, sqli
Deterministico: mesma entrada + mesma seed => saida identica.
"""
import argparse
import collections
import importlib.util
import random
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


bal = load_module("bal", HERE / "build-balanced-dataset.py")
clf = load_module("clf", HERE / "classify-attack-lines.py")
lab = load_module("lab", HERE / "build-labeled-dataset.py")


def by_method(rows):
    d = collections.defaultdict(list)
    for r in rows:
        d[r[1]].append(r)
    return d


def pick_benign(rows, quota, seed):
    """Amostra benigna deterministica. Se a cota == estoque, leva tudo;
    caso contrario, embaralha por template de endpoint para manter diversidade."""
    if quota >= len(rows):
        return list(rows)
    by_tpl = collections.defaultdict(list)
    for r in rows:
        by_tpl[lab.template_key(r)].append(r)
    rng = random.Random(seed)
    for k in by_tpl:
        by_tpl[k].sort()
        rng.shuffle(by_tpl[k])
    order = sorted(by_tpl, key=lambda k: (len(by_tpl[k]), str(k)))
    chosen, idx = [], collections.Counter()
    while len(chosen) < quota:
        moved = False
        for k in order:
            if len(chosen) >= quota:
                break
            if idx[k] < len(by_tpl[k]):
                chosen.append(by_tpl[k][idx[k]])
                idx[k] += 1
                moved = True
        if not moved:
            break
    return chosen


def split_counts(target, n_sqli_avail, n_xss_avail, mode):
    if mode == "proporcional":
        pool = n_sqli_avail + n_xss_avail
        n_sqli = round(target * n_sqli_avail / pool) if pool else 0
    else:  # balanceado
        n_sqli = target // 2
    n_xss = target - n_sqli
    # clampa a disponibilidade, realocando o resto para a outra classe
    n_sqli = min(n_sqli, n_sqli_avail)
    n_xss = min(n_xss, n_xss_avail)
    falta = target - (n_sqli + n_xss)
    if falta > 0:
        add_sqli = min(falta, n_sqli_avail - n_sqli)
        n_sqli += add_sqli
        falta -= add_sqli
        n_xss += min(falta, n_xss_avail - n_xss)
    return n_sqli, n_xss


def main():
    ap = argparse.ArgumentParser(description="Dataset rotulado balanceado por metodo.")
    ap.add_argument("--sqli", required=True)
    ap.add_argument("--xss", required=True)
    ap.add_argument("--benign", required=True)
    ap.add_argument("--get", type=int, required=True, help="alvo por classe no metodo GET (benigno=ataque)")
    ap.add_argument("--post", type=int, required=True, help="alvo por classe no metodo POST (benigno=ataque)")
    ap.add_argument("--split", choices=["balanceado", "proporcional"], default="balanceado")
    ap.add_argument("--output", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--seed", type=int, default=20260803)
    a = ap.parse_args()

    sqli = by_method(lab.dedup(lab.read_rows(a.sqli)))
    xss = by_method(lab.dedup(lab.read_rows(a.xss)))
    benign = by_method(lab.dedup(lab.read_rows(a.benign)))

    targets = {"GET": a.get, "POST": a.post}
    out = []
    plan = {}
    for m in ("GET", "POST"):
        tgt = targets[m]
        # benigno: cota == alvo (limitado ao estoque)
        b_tgt = min(tgt, len(benign.get(m, [])))
        picked_b = pick_benign(benign.get(m, []), b_tgt, a.seed)

        # ataque: mesmo alvo do benigno para equilibrar o metodo
        a_tgt = b_tgt
        n_sqli, n_xss = split_counts(a_tgt, len(sqli.get(m, [])), len(xss.get(m, [])), a.split)
        picked_sqli = lab.stratified_pick(sqli.get(m, []), n_sqli, bal.SQLI_TECH, a.seed)
        picked_xss = lab.stratified_pick(xss.get(m, []), n_xss, bal.XSS_TECH, a.seed)

        for r in picked_sqli:
            out.append(r + list(map(str, lab.label(r, "sqli"))))
        for r in picked_xss:
            out.append(r + list(map(str, lab.label(r, "xss"))))
        for r in picked_b:
            out.append(r + ["0", "0", "0"])

        plan[m] = {
            "benigno": len(picked_b),
            "ataque": len(picked_sqli) + len(picked_xss),
            "sqli": len(picked_sqli),
            "xss": len(picked_xss),
            "benigno_disp": len(benign.get(m, [])),
            "sqli_disp": len(sqli.get(m, [])),
            "xss_disp": len(xss.get(m, [])),
        }

    out.sort(key=lambda r: (r[0], r[1], r[2]))
    with open(a.output, "w", encoding="utf-8", errors="surrogateescape", newline="") as fo:
        fo.write("timestamp\tmethod\turl\tbody\tmalicioso\txss\tsqli\n")
        for r in out:
            fo.write("\t".join(r) + "\n")

    labels = collections.Counter((r[4], r[5], r[6]) for r in out)
    meth_cls = collections.Counter((r[1], r[4]) for r in out)
    dual = labels.get(("1", "1", "1"), 0)

    with open(a.report, "w", encoding="utf-8", newline="") as fr:
        fr.write(f"# Dataset rotulado — balanceado por metodo (split {a.split})\n\n")
        fr.write(f"- Seed: {a.seed}\n- Total: {len(out)}\n")
        fr.write(f"- Amostras com as duas assinaturas (xss=1 e sqli=1): {dual}\n\n")
        fr.write("## Balanceamento por metodo\n\n")
        fr.write("| Metodo | Benigno | Ataque | (SQLi | XSS) | Estoque benigno |\n|---|---|---|---|---|---|\n")
        for m in ("GET", "POST"):
            s = plan[m]
            fr.write(f"| {m} | {s['benigno']} | {s['ataque']} | {s['sqli']} | {s['xss']} | {s['benigno_disp']} |\n")
        fr.write("\n## Rotulos\n\n| malicioso | xss | sqli | amostras |\n|---|---|---|---|\n")
        for k, v in sorted(labels.items()):
            fr.write(f"| {k[0]} | {k[1]} | {k[2]} | {v} |\n")
        fr.write("\n## Metodo x classe\n\n| metodo | classe | amostras |\n|---|---|---|\n")
        for (m, mal), v in sorted(meth_cls.items()):
            fr.write(f"| {m} | {'ataque' if mal == '1' else 'benigno'} | {v} |\n")

    for m in ("GET", "POST"):
        s = plan[m]
        print(f"  {m:5} benigno={s['benigno']:6} ataque={s['ataque']:6} "
              f"(sqli={s['sqli']} xss={s['xss']})")
    print(f"  total={len(out)} dual={dual}")


if __name__ == "__main__":
    sys.exit(main())
