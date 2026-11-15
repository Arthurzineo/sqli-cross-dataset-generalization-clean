#!/usr/bin/env python3
"""Monta datasets balanceados e maximamente diversos a partir dos TSV de ataque.

Estrategia, em ordem:

1. Descarta probes de reconhecimento (requisicoes sem tecnica de ataque
   identificada) - sao varreduras de reflexao, nao exploracao.
2. Reduz cada payload ao seu *template*, substituindo numeros aleatorios,
   tokens de ferramenta e literais hex por marcadores. Assim
   "AND 1849=1849" e "AND 7177=7177" contam como o mesmo ataque.
3. Mantem UMA amostra por template (a mais antiga, para reprodutibilidade).
4. Estratifica os templates por (tecnicas x ofuscacoes x ponto de injecao) e
   preenche a cota em rodizio entre os estratos, para que tecnicas raras nao
   sejam engolidas pelas dominantes.

Deterministico: mesma entrada e mesma seed produzem saida byte a byte identica.
"""
import argparse
import base64
import binascii
import collections
import random
import re
import sys

SQLI_TECH = [
    ("union", re.compile(r"\bunion\b", re.I)),
    ("error_based", re.compile(r"\b(extractvalue|updatexml|exp\s*\(|gtid_subset|json_keys|convert\s*\(|cast\s*\(|floor\s*\(rand)", re.I)),
    ("time_based", re.compile(r"\b(sleep\s*\(|waitfor\s+delay|pg_sleep|benchmark\s*\(|generate_series)", re.I)),
    ("boolean_based", re.compile(r"\b(and|or)\b[^=]{0,40}?\d+\s*=\s*\d+", re.I)),
    ("stacked", re.compile(r";\s*(select|insert|update|delete|drop|create|exec)", re.I)),
    ("inline_subquery", re.compile(r"\(\s*select\b", re.I)),
    ("comment_terminated", re.compile(r"(--|#|/\*)")),
]

XSS_TECH = [
    ("script_tag", re.compile(r"<\s*script", re.I)),
    ("event_handler", re.compile(r"\bon[a-z]{3,15}\s*=", re.I)),
    ("svg_vector", re.compile(r"<\s*svg", re.I)),
    ("img_vector", re.compile(r"<\s*img", re.I)),
    ("iframe_vector", re.compile(r"<\s*iframe", re.I)),
    ("other_tag", re.compile(r"<\s*(details|body|input|select|marquee|video|audio|object|embed|form|math|style|title|textarea|noscript)", re.I)),
    ("javascript_uri", re.compile(r"java\s*script\s*:", re.I)),
    ("data_uri", re.compile(r"data:\s*text/html", re.I)),
    ("dom_property", re.compile(r"\b(document\.|window\.|top\[|self\[|eval\(|settimeout|setinterval|reflect\.apply)", re.I)),
    ("sink_call", re.compile(r"\b(alert|confirm|prompt)\s*[\(`]", re.I)),
]

OBFUS = [
    ("html_entity", re.compile(r"&#x?[0-9a-f]{1,6};", re.I)),
    ("fullwidth", re.compile(r"[＀-￯]")),
    ("sql_char_fn", re.compile(r"\b(char|chr)\s*\(\s*\d", re.I)),
    ("sql_hex_literal", re.compile(r"0x[0-9a-f]{4,}", re.I)),
    ("inline_comment", re.compile(r"/\*[^*]*\*/")),
    ("mysql_versioned", re.compile(r"/\*!\d*")),
    ("unicode_escape", re.compile(r"(?:\\+|/+)u[0-9a-f]{4}", re.I)),
    ("hex_escape", re.compile(r"(?:\\+|/+)x[0-9a-f]{2}", re.I)),
    ("backtick_call", re.compile(r"(alert|confirm|prompt)\s*`", re.I)),
    ("ctrl_break", re.compile(r"\\n|\\t|\\r")),
]

B64TOK = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
DIGITS = re.compile(r"\d+")
HEXLIT = re.compile(r"0x[0-9a-f]+", re.I)
DLX = re.compile(r"dlx[0-9a-f]+(?:dlxmid[0-9a-f]+)?(?:xld[0-9a-f]+)?", re.I)
WORD = re.compile(r"\b[a-zA-Z]{4,8}\d*\b")

KEYWORDS = set("""select union from where and or not null like exp cast convert char chr sleep
waitfor delay benchmark extractvalue updatexml concat case when then else end order group by
having limit offset into outfile dual information_schema table_name column_name version user
database schema script svg img iframe body input alert confirm prompt onerror onload onfocus
onmouseover javascript data html text base href src srcdoc document window top self eval
settimeout setinterval reflect apply autofocus tabindex class id style title form details
marquee video audio object embed math noscript textarea generate_series pg_sleep json_keys
gtid_subset floor rand sysmaster syspaghdr elt make_set rlike regexp""".split())


def has_base64(text):
    for tok in B64TOK.findall(text):
        t = tok[: len(tok) - len(tok) % 4]
        if len(t) < 16:
            continue
        try:
            raw = base64.b64decode(t, validate=True)
        except (binascii.Error, ValueError):
            continue
        if raw and sum(1 for b in raw if 32 <= b < 127) / len(raw) >= 0.9:
            return True
    return False


def skeleton(text):
    s = DLX.sub("@DLX@", text)
    s = HEXLIT.sub("0xH", s)
    s = DIGITS.sub("#", s)
    s = WORD.sub(lambda m: m.group() if m.group().lower() in KEYWORDS else "@T@", s)
    return re.sub(r"\s+", " ", s).strip().lower()[:400]


def injection_point(url, body):
    pts = []
    path = url.split("?", 1)[0]
    if re.search(r"[<'\"();]|select|script|union|alert|dlx[0-9a-f]|\.\./", path, re.I):
        pts.append("path")
    if "?" in url:
        pts.append("query")
    if body and body != "-":
        pts.append("body")
    return "+".join(pts) if pts else "none"


def features(url, body, techs):
    blob = url + " " + (body if body != "-" else "")
    t = tuple(sorted(n for n, rx in techs if rx.search(blob)))
    o = [n for n, rx in OBFUS if rx.search(blob)]
    if has_base64(blob):
        o.append("base64")
    return t, tuple(sorted(o)), injection_point(url, body)


def load(path, techs):
    """Retorna {skeleton: (linha, estrato)} guardando so o 1o de cada template."""
    templates = {}
    total = probes = 0
    with open(path, encoding="utf-8", errors="surrogateescape") as fh:
        header = fh.readline().rstrip("\n")
        for line in fh:
            row = line.rstrip("\n")
            p = row.split("\t")
            if len(p) != 4:
                continue
            total += 1
            _, method, url, body = p
            tech, obf, point = features(url, body, techs)
            if not tech:
                probes += 1
                continue
            payload = (url.split("?", 1)[1] if "?" in url else "") + " " + (body if body != "-" else "")
            sk = (method, skeleton(payload or url))
            if sk not in templates:
                templates[sk] = (row, (method, tech, obf, point))
    return header, templates, total, probes


def pick(templates, method, quota, seed):
    """Rodizio entre estratos para cobrir o maximo de combinacoes."""
    strata = collections.defaultdict(list)
    for (m, _sk), (row, stratum) in templates.items():
        if m != method:
            continue
        strata[stratum[1:]].append(row)
    rng = random.Random(seed)
    for key in strata:
        strata[key].sort()
        rng.shuffle(strata[key])
    order = sorted(strata, key=lambda k: (len(strata[k]), k))
    chosen = []
    idx = collections.Counter()
    while len(chosen) < quota:
        progressed = False
        for key in order:
            if len(chosen) >= quota:
                break
            i = idx[key]
            if i < len(strata[key]):
                chosen.append(strata[key][i])
                idx[key] += 1
                progressed = True
        if not progressed:
            break
    return chosen, len(strata), sum(1 for k in order if idx[k] > 0)


def main():
    ap = argparse.ArgumentParser(description="Monta dataset balanceado e diverso.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--kind", required=True, choices=["sqli", "xss"])
    ap.add_argument("--get", type=int, required=True, help="cota de GET (0 = todos os templates)")
    ap.add_argument("--post", type=int, required=True, help="cota de POST (0 = todos os templates)")
    ap.add_argument("--output", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--seed", type=int, default=20260803)
    a = ap.parse_args()

    techs = SQLI_TECH if a.kind == "sqli" else XSS_TECH
    header, templates, total, probes = load(a.input, techs)

    avail = collections.Counter(m for m, _ in templates)
    quotas = {"GET": a.get or avail["GET"], "POST": a.post or avail["POST"]}

    out_rows = []
    stats = {}
    for method in ("GET", "POST"):
        rows, n_strata, n_used = pick(templates, method, quotas[method], a.seed)
        out_rows.extend(rows)
        stats[method] = {
            "pedido": quotas[method],
            "entregue": len(rows),
            "templates_disponiveis": avail[method],
            "estratos": n_strata,
            "estratos_cobertos": n_used,
        }

    out_rows.sort(key=lambda r: r.split("\t", 1)[0])
    with open(a.output, "w", encoding="utf-8", errors="surrogateescape", newline="") as fo:
        fo.write(header + "\n")
        for r in out_rows:
            fo.write(r + "\n")

    tech_c = collections.Counter()
    obf_c = collections.Counter()
    pt_c = collections.Counter()
    meth_c = collections.Counter()
    for r in out_rows:
        _, method, url, body = r.split("\t")
        t, o, pt = features(url, body, techs)
        meth_c[method] += 1
        for x in t:
            tech_c[x] += 1
        for x in (o or ("(nenhuma)",)):
            obf_c[x] += 1
        pt_c[pt] += 1

    with open(a.report, "w", encoding="utf-8", newline="") as fr:
        fr.write(f"# Relatorio de amostragem — {a.input}\n\n")
        fr.write(f"- Linhas na entrada: {total}\n")
        fr.write(f"- Probes de reconhecimento descartados: {probes}\n")
        fr.write(f"- Templates distintos de payload: {len(templates)}\n")
        fr.write(f"- Amostras na saida: {len(out_rows)} (seed {a.seed})\n\n")
        fr.write("## Cotas\n\n| Metodo | Pedido | Entregue | Templates disp. | Estratos | Cobertos |\n")
        fr.write("|---|---|---|---|---|---|\n")
        for m, s in stats.items():
            fr.write(f"| {m} | {s['pedido']} | {s['entregue']} | {s['templates_disponiveis']} "
                     f"| {s['estratos']} | {s['estratos_cobertos']} |\n")
        for title, c in (("Tecnicas", tech_c), ("Ofuscacao", obf_c), ("Ponto de injecao", pt_c)):
            fr.write(f"\n## {title}\n\n| Categoria | Amostras |\n|---|---|\n")
            for k, v in c.most_common():
                fr.write(f"| {k} | {v} |\n")

    for m, s in stats.items():
        print(f"  {m:5} pedido={s['pedido']:6} entregue={s['entregue']:6} "
              f"templates={s['templates_disponiveis']:6} estratos={s['estratos_cobertos']}/{s['estratos']}")
    print(f"  total saida={len(out_rows)} | probes descartados={probes}")


if __name__ == "__main__":
    sys.exit(main())
