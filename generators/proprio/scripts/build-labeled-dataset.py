#!/usr/bin/env python3
"""Monta datasets rotulados juntando ataque (SQLi/XSS) e trafego benigno.

Colunas de saida: timestamp, method, url, body, malicioso, xss, sqli

Dois modos:
  --mode proporcional  mantem a proporcao natural entre SQLi e XSS
  --mode balanceado    mesma quantidade de SQLi e XSS

Em ambos, a quantidade de benignas iguala a de ataques (1:1).
Amostragem estratificada por (tecnica x ofuscacao x ponto de injecao) para
cobrir o maximo de variacoes, e deterministica com seed fixa.
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


def read_rows(path):
    rows = []
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) == 4:
                rows.append(p)
    return rows


def dedup(rows):
    seen = set()
    out = []
    for r in rows:
        k = (r[1], r[2], r[3])
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def template_key(row):
    _, method, url, body = row
    payload = (url.split("?", 1)[1] if "?" in url else "") + " " + (body if body != "-" else "")
    return method, bal.skeleton(payload or url)


def stratified_pick(rows, quota, techs, seed):
    """Um representante por template, depois rodizio entre estratos.

    Se a cota exceder o numero de templates, completa com as repeticoes
    restantes - tambem em rodizio, para nao concentrar em um so template.
    """
    by_template = {}
    for r in rows:
        by_template.setdefault(template_key(r), []).append(r)

    strata = collections.defaultdict(list)
    extras = []
    for tpl, group in by_template.items():
        head, tail = group[0], group[1:]
        _, method, url, body = head
        tech, obf, point = bal.features(url, body, techs)
        strata[(tech, obf, point)].append(head)
        extras.extend(tail)

    rng = random.Random(seed)
    for key in strata:
        strata[key].sort()
        rng.shuffle(strata[key])
    order = sorted(strata, key=lambda k: (len(strata[k]), str(k)))

    chosen = []
    idx = collections.Counter()
    while len(chosen) < quota:
        moved = False
        for key in order:
            if len(chosen) >= quota:
                break
            if idx[key] < len(strata[key]):
                chosen.append(strata[key][idx[key]])
                idx[key] += 1
                moved = True
        if not moved:
            break

    if len(chosen) < quota:
        extras.sort()
        rng.shuffle(extras)
        chosen.extend(extras[: quota - len(chosen)])
    return chosen


def label(row, primary):
    """Rotulo ancorado na campanha de origem (verdade de terreno), com a flag da
    outra classe ligada quando o payload realmente carrega a assinatura dela."""
    _, _, url, body = row
    _, reasons = clf.classify(url, body)
    xss = 1 if primary == "xss" else int(any(r.startswith(("xss", "html-encoded")) for r in reasons))
    sqli = 1 if primary == "sqli" else int("sqli" in reasons)
    return 1, xss, sqli


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqli", required=True)
    ap.add_argument("--xss", required=True)
    ap.add_argument("--benign", required=True)
    ap.add_argument("--mode", choices=["proporcional", "balanceado"], required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--seed", type=int, default=20260803)
    a = ap.parse_args()

    sqli_rows = dedup(read_rows(a.sqli))
    xss_rows = dedup(read_rows(a.xss))
    benign_rows = dedup(read_rows(a.benign))

    n_benign = len(benign_rows)
    total_attack = n_benign  # 1:1

    if a.mode == "proporcional":
        pool = len(sqli_rows) + len(xss_rows)
        n_sqli = round(total_attack * len(sqli_rows) / pool)
        n_xss = total_attack - n_sqli
    else:
        n_sqli = total_attack // 2
        n_xss = total_attack - n_sqli

    n_sqli = min(n_sqli, len(sqli_rows))
    n_xss = min(n_xss, len(xss_rows))

    picked_sqli = stratified_pick(sqli_rows, n_sqli, bal.SQLI_TECH, a.seed)
    picked_xss = stratified_pick(xss_rows, n_xss, bal.XSS_TECH, a.seed)

    out = []
    for r in picked_sqli:
        out.append(r + list(map(str, label(r, "sqli"))))
    for r in picked_xss:
        out.append(r + list(map(str, label(r, "xss"))))
    for r in benign_rows:
        out.append(r + ["0", "0", "0"])

    out.sort(key=lambda r: (r[0], r[1], r[2]))

    with open(a.output, "w", encoding="utf-8", errors="surrogateescape", newline="") as fo:
        fo.write("timestamp\tmethod\turl\tbody\tmalicioso\txss\tsqli\n")
        for r in out:
            fo.write("\t".join(r) + "\n")

    counts = collections.Counter((r[4], r[5], r[6]) for r in out)
    methods = collections.Counter((r[4], r[1]) for r in out)
    dual = sum(v for k, v in counts.items() if k == ("1", "1", "1"))

    with open(a.report, "w", encoding="utf-8", newline="") as fr:
        fr.write(f"# Dataset rotulado — modo {a.mode}\n\n")
        fr.write(f"- Seed: {a.seed}\n- Total: {len(out)}\n")
        fr.write(f"- Ataques: {len(picked_sqli) + len(picked_xss)} "
                 f"(SQLi {len(picked_sqli)}, XSS {len(picked_xss)})\n")
        fr.write(f"- Benignas: {len(benign_rows)}\n")
        fr.write(f"- Amostras com as duas assinaturas (xss=1 e sqli=1): {dual}\n\n")
        fr.write("## Rotulos\n\n| malicioso | xss | sqli | amostras |\n|---|---|---|---|\n")
        for k, v in sorted(counts.items()):
            fr.write(f"| {k[0]} | {k[1]} | {k[2]} | {v} |\n")
        fr.write("\n## Metodo por classe\n\n| classe | metodo | amostras |\n|---|---|---|\n")
        for (mal, m), v in sorted(methods.items()):
            fr.write(f"| {'ataque' if mal == '1' else 'benigno'} | {m} | {v} |\n")

    print(f"  total={len(out)} sqli={len(picked_sqli)} xss={len(picked_xss)} "
          f"benignas={len(benign_rows)} dual={dual}")


if __name__ == "__main__":
    sys.exit(main())
