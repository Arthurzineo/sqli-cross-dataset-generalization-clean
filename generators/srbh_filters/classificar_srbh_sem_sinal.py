"""Classifica as requisicoes do SR-BH rotuladas SQLi que nao tem sinal de SQL.

METODO (segunda versao, apos leitura manual dos 6.949 registros).

A primeira versao casava regex no texto inteiro e errava: marcava `{{ data.url }}`
como template injection (e artefato de crawl -- o ZAP segue literalmente os
templates Underscore que o WordPress publica no proprio JS) e casava o `http://`
da propria requisicao como SSRF.

A leitura mostrou a estrutura real: o trafego e do **OWASP ZAP** (assinaturas
`zap=zaproxy`, `0W45pz4p`, `8501779237819759495.owasp.org`, `first_name=ZAP`).
O ZAP pega cada URL descoberta no crawl e **injeta um payload num segmento do
caminho**, repetindo o site inteiro com aquele payload. Por isso 6.949 linhas
com pouquissima variedade real: e payload x URL-do-crawl.

Entao a classificacao nao olha a linha toda -- isola o TOKEN INJETADO,
comparando cada segmento do caminho com o vocabulario de segmentos que aparece
no trafego BENIGNO do proprio corpus (16.150 segmentos legitimos). O que nao
esta la e payload.

Uso:  python classificar_srbh_sem_sinal.py
"""
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
CORPUS = RAIZ / "datasets" / "deduplicados_decodificados" / "srbh_completo_decodificado_sqli.csv"
SAIDA = RAIZ / "datasets" / "deduplicados_decodificados" / "SRBH_SEM_SINAL.csv"

# Ordem = prioridade. Aplicada ao TOKEN injetado, nao a linha inteira.
CATEGORIAS = [
    # `(`, `)` e NULL colados num segmento legitimo sao a sonda classica de
    # SQLi: parentese desbalanceado e NULL provocam erro de sintaxe no SQL.
    # E a regra "SQL Injection" do ZAP na fase de deteccao de ponto injetavel.
    ("sonda_sqli", r"[()]|NULL"),
    ("command_injection", r"(?:^|[|&;`])\s*(?:cat|ls|id|whoami|ping|sleep|dir)\b|`"),
    ("code_injection", r"\$\{"),
    ("http_response_splitting", r"(?i)set-cookie:"),
    ("ssrf_redirect", r"(?i)owasp\.org|^\\\\|^//|^https?:"),
    ("path_traversal_lfi", r"(?i)^c:|etc|passwd|\.\."),
    ("xml_xxe", r"\]\]>"),
    ("marcador_zap", r"(?i)^any$|0W45pz4p|^@$|zaproxy"),
    ("artefato_crawl_template", r"\{\{"),
]


def vocabulario_legitimo(d):
    """Segmentos de caminho que aparecem no trafego benigno do corpus."""
    v = set()
    for u in d[d.attack_type == "legitimate"].URL.astype(str):
        v.update(s for s in urlparse(u).path.split("/") if s)
    return v


def main():
    d = pd.read_csv(CORPUS, low_memory=False)
    vocab = vocabulario_legitimo(d)
    s = d[(d.attack_type == "sqli") & (d.tem_indicador_sqli == 0)].copy()

    def token(u):
        segs = [x for x in urlparse(str(u)).path.split("/") if x]
        fora = [x for x in segs if x not in vocab]
        return " | ".join(fora) if fora else ""

    s["token_injetado"] = s.URL.map(token)
    s["categoria"] = "sem_payload_no_caminho"
    for nome, pat in CATEGORIAS:
        pend = s.categoria == "sem_payload_no_caminho"
        casa = s.token_injetado.str.contains(pat, regex=True, na=False)
        s.loc[pend & (s.token_injetado != "") & casa, "categoria"] = nome
    s.loc[(s.categoria == "sem_payload_no_caminho")
          & (s.token_injetado != ""), "categoria"] = "outro_payload"

    vc = s.categoria.value_counts()
    print(f"{len(s)} requisicoes rotuladas SQLi sem sinal lexico de SQL")
    print(f"vocabulario legitimo: {len(vocab)} segmentos\n")
    print(f"{'categoria':<28}{'n':>7}{'%':>8}")
    for c, n in vc.items():
        print(f"{c:<28}{n:>7}{100 * n / len(s):>7.1f}%")

    sqli = int((s.categoria == "sonda_sqli").sum())
    outro = int((~s.categoria.isin(["sonda_sqli", "sem_payload_no_caminho"])).sum())
    limpo = int((s.categoria == "sem_payload_no_caminho").sum())
    print(f"\nsonda de SQLi (ataque da classe certa) : {sqli} ({100*sqli/len(s):.1f}%)")
    print(f"ataque de outra classe                 : {outro} ({100*outro/len(s):.1f}%)")
    print(f"sem payload no caminho                 : {limpo} ({100*limpo/len(s):.1f}%)")

    s[["URL", "content", "Method", "token_injetado", "categoria",
       "capec_n_rotulos"]].to_csv(SAIDA, index=False)
    print(f"\n-> {SAIDA}")


if __name__ == "__main__":
    main()
