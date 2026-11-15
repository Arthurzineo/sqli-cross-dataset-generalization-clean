#!/usr/bin/env python
# Prepara o ECML/PKDD 2007 como SEGUNDO CORPUS ALVO, no mesmo formato e com o
# mesmo schema do CSIC decodificado - para servir de validacao cross-dataset
# independente, com procedencia de coleta totalmente diferente (Gemius SA,
# 4 semanas de trafego na Europa Central/Oriental, 2007).
#
# ORIGEM: learning_dataset.xml do ECML/PKDD 2007 Discovery Challenge
#   (50.116 amostras, 7 tipos de ataque + Valid).
#
# TRES DECISOES DE ADAPTACAO, todas por comparabilidade com o CSIC:
#
# 1) SO SQLi E XSS. O desafio original tem 7 tipos (LdapInjection, OsCommanding,
#    PathTransversal, SSI, XPathInjection alem desses dois). Ficam so os dois
#    que este trabalho detecta; o resto e descartado - nao vira "benigno",
#    porque rotular ataque como benigno envenenaria a validacao.
#
# 2) SO AMOSTRAS DE ROTULO UNICO. 2.180 amostras tem dois <type> ao mesmo tempo
#    (ex.: SqlInjection + OsCommanding). Elas sao descartadas: como o alvo aqui
#    e binario e as ablacoes sao por tipo, uma amostra que e SQLi *e* outra
#    coisa nao pertence limpo a nenhum dos dois lados.
#
# 3) SO ATAQUES VISIVEIS AO PIPELINE. O campo <attackIntervall> diz ONDE esta
#    o payload. Em parte das amostras ele esta nos CABECALHOS HTTP
#    (Accept-Language, User-Agent...), e o extrator deste projeto - montar_texto
#    = URL + body - nao le cabecalho nenhum. Manter essas amostras injetaria
#    falsos negativos garantidos, que mediriam a limitacao do extrator e nao a
#    do modelo. Sao descartadas:
#        SQLi: 1.408 query + 242 body = 1.650 mantidos, 365 em header descartados
#        XSS : 1.206 query + 207 body + 100 uri = 1.513 mantidos, 312 descartados
#    (Se algum dia o pipeline passar a ler cabecalhos, basta rodar com
#     --incluir-headers para recuperar as 677.)
#
# BALANCEAMENTO: benignos amostrados aleatoriamente (seed 42) ate igualar o
# total de ataques, mesma convencao do csic_sqli_xss_balanceado. A proporcao
# interna SQLi:XSS fica a natural do corpus; --balancear-tipos iguala tambem
# os dois tipos entre si.
#
# DECODIFICACAO: aplica o mesmo unquote_plus-ate-estabilizar de
# decodificar_csic.py, para o ECML entrar na mesma convencao do dataset grande
# e do CSIC decodificado (senao enc_pct volta a ser artefato).
#
# As features lexicas sao extraidas importando as funcoes de decodificar_csic.py,
# nao copiando - assim o schema sai identico por construcao.
#
# Uso:
#     python preparar_ecml.py --xml <caminho>/learning_dataset.xml
#     python preparar_ecml.py --xml ... --codebert     # tambem gera embeddings

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd

from decodificar_csic import decodificar, limpar_url, extrair_lexicas

NS = "{http://www.example.org/ECMLPKDD}"
SEED = 42

MAPA_TIPO = {"SqlInjection": "sqli", "XSS": "xss", "Valid": "legitimate"}
LOCAIS_VISIVEIS = {"uri", "query", "body"}

SAIDA_FONTE = "ecml_sqli_xss_balanceado_decodificado.csv"
SAIDA_LEXICO = "ecml_dataset_lexicas_decodificado.csv"
SAIDA_CODEBERT = "ecml_dataset_codebert_decodificado.csv"


def texto(el):
    return (el.text or "") if el is not None else ""


def host_de(headers):
    for linha in headers.splitlines():
        if linha.lower().startswith("host:"):
            return linha.split(":", 1)[1].strip()
    return ""


def parsear(caminho, incluir_headers):
    """Le o XML em streaming e devolve as amostras aproveitaveis."""
    linhas = []
    descartes = {"multi_rotulo": 0, "tipo_fora_do_escopo": 0, "ataque_em_header": 0}

    for _, el in ET.iterparse(str(caminho), events=("end",)):
        if el.tag != NS + "sample":
            continue

        cl = el.find(NS + "class")
        tipos = [t.text for t in cl.findall(NS + "type")]

        if len(tipos) != 1:
            descartes["multi_rotulo"] += 1
            el.clear(); continue
        tipo = tipos[0]
        if tipo not in MAPA_TIPO:
            descartes["tipo_fora_do_escopo"] += 1
            el.clear(); continue

        if tipo != "Valid" and not incluir_headers:
            ivs = [i.text or "" for i in cl.findall(NS + "attackIntervall")]
            locais = {s.split(":")[0] for s in ivs if s}
            if locais and not (locais & LOCAIS_VISIVEIS):
                descartes["ataque_em_header"] += 1
                el.clear(); continue

        req = el.find(NS + "request")
        metodo = texto(req.find(NS + "method")).strip() or "GET"
        uri = texto(req.find(NS + "uri"))
        query = texto(req.find(NS + "query"))
        corpo = texto(req.find(NS + "body"))
        headers = texto(req.find(NS + "headers"))

        host = host_de(headers)
        url = f"http://{host}{uri}" if host else uri
        if query:
            url += "?" + query
        url += " HTTP/1.1"                      # mesmo sufixo do CSIC

        linhas.append({"classification": 0 if tipo == "Valid" else 1,
                       "Method": metodo, "URL": url, "content": corpo,
                       "attack_type": MAPA_TIPO[tipo]})
        el.clear()

    return pd.DataFrame(linhas), descartes


def balancear(df, balancear_tipos):
    ataques = df[df.classification == 1]
    benignos = df[df.classification == 0]

    if balancear_tipos:
        n = ataques.attack_type.value_counts().min()
        ataques = (ataques.groupby("attack_type", group_keys=False)
                   .apply(lambda g: g.sample(n, random_state=SEED)))

    n_atq = len(ataques)
    if len(benignos) < n_atq:
        raise SystemExit(f"benignos insuficientes: {len(benignos)} < {n_atq}")
    benignos = benignos.sample(n_atq, random_state=SEED)

    out = pd.concat([benignos, ataques]).sample(frac=1, random_state=SEED)
    return out.reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml", required=True, help="caminho do learning_dataset.xml")
    ap.add_argument("--incluir-headers", action="store_true",
                    help="mantem ataques cujo payload esta so nos cabecalhos")
    ap.add_argument("--balancear-tipos", action="store_true",
                    help="iguala tambem SQLi e XSS entre si")
    ap.add_argument("--codebert", action="store_true")
    args = ap.parse_args()

    print(f"Lendo {args.xml} ...")
    df, descartes = parsear(Path(args.xml), args.incluir_headers)
    print(f"  aproveitaveis: {len(df)}")
    print("  descartados:")
    for k, v in descartes.items():
        print(f"    {k:<22}{v}")
    print("\n  antes do balanceamento:")
    print(df.attack_type.value_counts().to_string())

    df = balancear(df, args.balancear_tipos)
    print(f"\n  depois do balanceamento: {len(df)} amostras")
    print(df.attack_type.value_counts().to_string())
    print(f"  benigno/malicioso: {(df.classification == 0).sum()}/"
          f"{(df.classification == 1).sum()}")

    # mesma decodificacao aplicada ao CSIC, para a mesma convencao de enc_pct
    cru = (df.URL.fillna("").astype(str) + " " + df.content.fillna("").astype(str))
    tem_enc = cru.str.contains(r"%[0-9a-fA-F]{2}", regex=True)
    print(f"\n  com %XX antes de decodificar: benignos "
          f"{tem_enc[df.classification == 0].mean():.1%} | ataques "
          f"{tem_enc[df.classification == 1].mean():.1%}")
    for c in ["URL", "content"]:
        df[c] = df[c].map(decodificar)
    cru = (df.URL.fillna("").astype(str) + " " + df.content.fillna("").astype(str))
    tem_enc = cru.str.contains(r"%[0-9a-fA-F]{2}", regex=True)
    print(f"  depois: benignos {tem_enc[df.classification == 0].mean():.1%} | "
          f"ataques {tem_enc[df.classification == 1].mean():.1%}")

    df.to_csv(SAIDA_FONTE, index=False)
    print(f"\n[ok] {SAIDA_FONTE}")

    # ordem das colunas identica a do csic_dataset_*_decodificado.csv:
    # classification, attack_type, <features...>
    def com_rotulos(feats):
        feats = feats.copy()
        feats.insert(0, "attack_type", df.attack_type.values)
        feats.insert(0, "classification", df.classification.values)
        return feats

    url_limpa = df.URL.map(limpar_url)
    lex = com_rotulos(extrair_lexicas(url_limpa, df.content))
    lex.to_csv(SAIDA_LEXICO, index=False)
    print(f"[ok] {SAIDA_LEXICO}  ({lex.shape[1] - 2} features)")

    if args.codebert:
        from decodificar_csic import extrair_codebert
        emb = com_rotulos(extrair_codebert(url_limpa, df.content))
        emb.to_csv(SAIDA_CODEBERT, index=False)
        print(f"[ok] {SAIDA_CODEBERT}")


if __name__ == "__main__":
    main()
