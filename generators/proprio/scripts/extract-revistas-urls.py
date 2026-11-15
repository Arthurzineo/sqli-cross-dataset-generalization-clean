#!/usr/bin/env python3
# Extrai todas as URLs sob /etc/revistas a partir do HTML de uma pagina OJS.
#   python3 extract-revistas-urls.py <base_url> <arquivo_saida>
# Roda no WSL (usa a rota do WSL -> homolog). Cert proprio do homolog e aceito.
import sys, re, ssl, urllib.request, urllib.parse
from pathlib import Path

if len(sys.argv) > 1:
    base = sys.argv[1]
else:
    targets = Path(__file__).resolve().parents[1] / "config" / "targets.txt"
    if not targets.is_file():
        raise SystemExit(f"Crie {targets} a partir de config/targets.txt.example")
    base = next((line.strip() for line in targets.read_text().splitlines()
                 if line.strip() and not line.lstrip().startswith("#")), "")
    if not base:
        raise SystemExit(f"Nenhum alvo em {targets}")
outfile = sys.argv[2] if len(sys.argv) > 2 else "/dev/stdout"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE  # homolog interno pode ter certificado proprio

req = urllib.request.Request(base, headers={"User-Agent": "TCC-Extract-WSL"})
html = urllib.request.urlopen(req, timeout=25, context=ctx).read().decode("utf-8", "replace")

# junta os links de href= e src= (com aspas simples ou duplas)
raw = re.findall(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", html, re.I)

root = base.rstrip("/") + "/"   # trata .../revistas/ como diretorio p/ resolver relativos
allowed_host = urllib.parse.urlsplit(base).hostname
seen, urls = set(), []
for u in raw:
    u = u.strip()
    if not u or u.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        continue
    absu = urllib.parse.urljoin(root, u)
    p = urllib.parse.urlsplit(absu)
    if p.scheme not in ("http", "https"):
        continue
    if p.hostname and p.hostname.lower() != (allowed_host or "").lower():
        continue                              # so o mesmo host
    if "/etc/revistas" not in p.path:
        continue                              # so o path revistas
    norm = urllib.parse.urlunsplit((p.scheme, p.netloc, p.path, p.query, ""))  # sem fragmento
    if norm not in seen:
        seen.add(norm); urls.append(norm)

urls.sort()
with open(outfile, "w", encoding="utf-8") as fh:
    fh.write("\n".join(urls) + ("\n" if urls else ""))

print("extraidas %d URLs sob /etc/revistas -> %s" % (len(urls), outfile))
com_param = sum(1 for u in urls if "?" in u)
print("  com parametros (?): %d" % com_param)
for u in urls[:20]:
    print("  " + u)
