import re, glob, os
import pathlib
ROOT = str(pathlib.Path(__file__).resolve().parent.parent)

# Arquivos que vieram com uma PAGINA HTML embutida (CSS reset, JS de UI "spoiler",
# barras de progresso, tutorial, bloqueio Kaspersky). Nesses, so mantemos linhas
# que tenham indicador de ATAQUE real; o resto (page markup/JS/CSS) e descartado.
POISON = {
    os.path.normpath(f"{ROOT}/wordlists/payload-box/sqli/sqlite-payloads.txt"),
    os.path.normpath(f"{ROOT}/wordlists/seclists/xss/XSS-OFJAAAH.txt"),
}

# ---- filtros conservadores (para arquivos NAO-poison) ----
RE_SEL = re.compile(rb'^\s*[.#:*]?[\w:().,\[\]="\'\-+~>* ]+\{\s*[^<]*\}?\s*$')
RE_DECL = re.compile(rb'^\s*[-A-Za-z]{1,30}\s*:\s*.+;\s*$')
RE_BARETAG = re.compile(rb'^\s*</?[a-zA-Z][a-zA-Z0-9]{0,10}\s*/?>\s*$')
RE_HTMLTAG = re.compile(rb'</?[a-zA-Z]')
RE_SINK = re.compile(
    rb'on[a-z]{3,}\s*=|javascript:|<script|<svg|<img|<iframe|<embed|<object|<video|'
    rb'<audio|<body|<details|<marquee|<math|<meta|<style|<a[ />]|<form|<input|<select|'
    rb'<textarea|<base|<link|<keygen|<frame|<isindex|<image|srcdoc|formaction|data:|'
    rb'expression\(|&#|%3c|\\u00|\\x|alert|prompt|confirm|eval|document|window|location|'
    rb'settimeout|setinterval|fetch\(|xlink|href|src\s*=|url\(|=&|&\{', re.I)
DECL_ATTACK = [b'javascript', b'alert', b'prompt(', b'confirm(', b'expression', b'onerror',
               b'onload', b'onmouse', b'onfocus', b'onclick', b'ontoggle', b'&#', b'char(',
               b'concat', b'union', b'select', b'sleep', b'benchmark', b'waitfor', b'--',
               b'/*', b'||', b'&&', b'0x', b'eval', b'document']

# Tokens EXCLUSIVOS da pagina embutida (nunca aparecem em payload real).
# Drop global e seguro, mesmo com tag/quote/etc.
PAGE_TOK = [b'spoiler', b'setupclipboard', b'flex-table', b'copyable_url', b'url-section',
            b'showtutorial', b'falsepositive', b'kaspersky', b'securelist', b'testid',
            b'githubusercontent', b'data-testid', b'::-webkit', b'::-moz', b'::-ms',
            b'-webkit-progress', b'-moz-progress',
            # identificadores do JS de pagina (copy-to-clipboard / text-width)
            b'getcssstyle', b'gettextwidth', b'copiedtextstub', b'copiedtext',
            b'nodeschild', b'textnodetype', b'elementnodetype', b'getcontext("2d"',
            b'createelement("textarea"', b'victimsite.com',
            b'iconwidth', b'columnoffset', b'secondcolumnwidth', b'firstcolumnwidth',
            b'traversenodes', b'measuretext', b'elementtitle', b'.childnodes',
            b'geticon', b'geturltext']

# "pwd" isolado (com breakouts/comentarios) = command injection, nao SQLi.
RE_PWD = re.compile(rb'^[\s()\'"`]*p[wW][dD][\s()#;/*\-]*$')

def is_page_junk(l):
    low = l.lower()
    if any(t in low for t in PAGE_TOK): return True
    if b'<' not in l and b':root' in low and b'{' in l: return True  # CSS :root{
    if b'<' not in l and (b'.nodevalue' in low or b'nodes[' in low): return True  # DOM JS
    if RE_PWD.match(l): return True                                  # comando pwd
    s = low.lstrip()
    if s.startswith(b'perl ') or s.startswith(b'perl-e') or s.startswith(b'redirect '):
        return True                                                  # comando/fixture
    return False

def junk_conservador(l):
    low = l.lower()
    if is_page_junk(l): return True
    if RE_BARETAG.match(l): return True
    if RE_HTMLTAG.search(l):
        return not RE_SINK.search(l)
    if b'<' in l: return False
    if len(l) > 5000: return True
    if b'data:font/' in low or b'data:application/font' in low: return True
    if b'data:image/' in low and b'base64' in low: return True
    if any(x in low for x in (b'@font-face', b'@media', b'@keyframes', b'@charset', b'@supports')): return True
    if l.strip() in (b'{', b'}', b'});', b')', b'('): return True
    if RE_SEL.match(l): return True
    if RE_DECL.match(l) and not any(a in low for a in DECL_ATTACK): return True
    return False

# ---- para arquivos POISON: manter SO se tiver indicador de ataque ----
SQLI_ATK = [b"'", b'"', b'--', b'#', b'/*', b';', b'=', b'<', b'>', b'select', b'union',
            b' or ', b' and ', b'||', b'&&', b'sleep', b'benchmark', b'waitfor', b'char(',
            b'concat', b'0x', b'having', b'order by', b'insert', b'update', b'delete',
            b'drop', b'exec', b'extractvalue', b'updatexml', b'like', b'sqlite', b'pg_',
            b'dbms_', b'load_file', b'outfile', b'%', b'admin', b'password', b'user']

def keep_poison(l, kind):
    low = l.lower()
    if kind == "sqli":
        return any(t in low for t in SQLI_ATK) and not junk_conservador(l)
    else:  # xss: precisa de sink/tag de ataque
        if junk_conservador(l): return False
        return bool(RE_SINK.search(l)) or bool(RE_HTMLTAG.search(l))

# Politica "so payload completo": exige SINAL de ataque real. Remove SIDs
# (VENOM, ORA8171T), nomes de evento soltos (onBlur) e fragmentos sem sinal.
SQLI_KEEP = re.compile(
    rb"""['"`]|--|\#|/\*|\*/|;|=|<|>|\|\||&&|0x|@@|"""
    rb"""\b(select|union|or|and|sleep|benchmark|waitfor|char|concat|having|order|"""
    rb"""insert|update|delete|drop|exec|extractvalue|updatexml|like|null|from|where|"""
    rb"""load_file|outfile|utl_|dbms_|pg_sleep|substr|ascii|hex|md5|version|cast|convert)\b""",
    re.I)

RE_JSVAR = re.compile(rb'^\s*(var|const|let)\s', re.I)   # declaracao JS (page code)

def has_signal(l, kind):
    if kind == "sqli":
        if b'<' not in l and RE_JSVAR.match(l): return False   # JS de pagina, nao SQL
        return bool(SQLI_KEEP.search(l))
    else:  # xss: tag ou sink de ataque
        return (b'<' in l) or bool(RE_SINK.search(l))

def consolidate(globs, kind, out):
    files = []
    for g in globs:
        files += sorted(glob.glob(os.path.join(ROOT, g)))
    seen = set(); res = []; dropped = {}
    for path in files:
        npath = os.path.normpath(path)
        poison = npath in POISON
        with open(path, "rb") as fh:
            data = fh.read()
        if data.startswith(b"\xef\xbb\xbf"): data = data[3:]
        d = 0
        for l in data.split(b"\n"):
            if not l: continue
            drop = (not keep_poison(l, kind)) if poison else junk_conservador(l)
            if not drop and not has_signal(l, kind):   # exige sinal de ataque
                drop = True
            if drop:
                d += 1; continue
            if l in seen: continue
            seen.add(l); res.append(l)
        if d:
            dropped[os.path.basename(path)] = d
    with open(out, "wb") as fh:
        fh.write(b"\n".join(res) + b"\n")
    return len(res), dropped

for kind, globs in (
    ("sqli", ["wordlists/payloadsallthethings/sqli/*.txt", "wordlists/seclists/sqli/*.txt",
              "wordlists/fuzzdb/sqli/*/*.txt", "wordlists/payload-box/sqli/*.txt"]),
    ("xss",  ["wordlists/payloadsallthethings/xss/*.txt", "wordlists/seclists/xss/*.txt"]),
):
    n, dropped = consolidate(globs, kind, f"{ROOT}/wordlists/base/{kind}-web.txt")
    print(f"[{kind}] base LIMPO = {n}")
    for f, d in sorted(dropped.items(), key=lambda x: -x[1])[:6]:
        print(f"     dropou {d} de {f}")
