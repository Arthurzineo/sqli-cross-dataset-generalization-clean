"""Prepara o SR-BH 2020 como corpus SQLi-only balanceado.

Decisoes desta versao (combinadas explicitamente):

  * SEM decodificacao. O corpus fica como veio. A decodificacao
    (`unquote_plus`-ate-estabilizar) que foi aplicada ao CSIC e ao ECML nao e
    aplicada aqui por enquanto.
  * TODAS as requisicoes com a tag `66 - SQL Injection` sao mantidas -- inclusive
    as 2.218 que tem outro rotulo CAPEC junto, e inclusive as ~8% que nao tem
    nenhum payload observavel na requisicao (o rotulo do SR-BH e por sessao de
    varredura, nao por requisicao). O que fazer com essas fica para depois; a
    coluna `tem_indicador_sqli` marca quais sao, para permitir a decisao sem
    reprocessar o arquivo de 436 MB.
  * SEM balanceamento aqui. Este script extrai TODAS as SQLi e TODAS as
    benignas. O balanceamento 50/50 acontece no fim do pipeline, em
    `deduplicar.py`.

    MOTIVO (corrigido depois de medir): balancear antes de deduplicar joga
    dados fora. As benignas do SR-BH sao 525.195 linhas mas so 90.049
    requisicoes distintas -- a requisicao `/` sozinha aparece 298.686 vezes.
    Amostrar 250.311 linhas ao acaso capturava apenas 48.418 distintas. Fazendo
    na ordem certa (extrair tudo -> decodificar -> deduplicar -> balancear)
    sobram ~89 mil por classe, quase o dobro.

    A deduplicacao precisa vir DEPOIS da decodificacao, porque duas formas
    codificadas diferentes podem decodificar para o mesmo texto.

Saida no schema comum do projeto (`classification, Method, URL, content,
attack_type`), o mesmo do CSIC e do ECML, mais duas colunas de apoio no fim.

Uso:  python preparar_srbh.py
"""
import re
import sys
import urllib.parse as up

import pandas as pd

from pathlib import Path

# Caminhos relativos a este arquivo -- o script roda de qualquer diretorio.
RAIZ = Path(__file__).resolve().parents[1]          # GENERALIZACAO/SQLI/
DATASETS_PROJETO = RAIZ.parents[1] / "datasets"     # TCC_SCRIPTS_ORGANIZADOS/datasets/

SEED = 42
ENTRADA = str(DATASETS_PROJETO / "SR_BH_2020" / "data_capec_multilabel.csv")
SAIDA = str(RAIZ / "datasets" / "originais" / "srbh_completo_sqli.csv")

COL_SQLI = "66 - SQL Injection"
COL_NORMAL = "000 - Normal"

# Heuristica de apoio, NAO usada para filtrar: marca se ha algum indicio
# lexico de SQL na requisicao. Serve so para a decisao posterior sobre as
# amostras rotuladas SQLi sem payload observavel.
#
# O padrao vem de `analisar_rotulos.py` -- definicao unica, para a coluna
# gravada aqui nunca divergir da analise que a interpreta.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analisar_rotulos import PADRAO_SQLI  # noqa: E402


def decodificar(s):
    """unquote_plus ate estabilizar -- usada so pela heuristica, nao na saida."""
    s = str(s) if pd.notna(s) else ""
    for _ in range(3):
        novo = up.unquote_plus(s)
        if novo == s:
            break
        s = novo
    return s


def main():
    cabecalho = pd.read_csv(ENTRADA, nrows=0)
    rotulos = [c for c in cabecalho.columns if c.split(" ")[0].isdigit()]

    print(f"lendo {ENTRADA} ...")
    d = pd.read_csv(
        ENTRADA,
        usecols=["request_http_method", "request_http_request", "request_body",
                 "request_host"] + rotulos,
        low_memory=False,
    )
    print(f"  {len(d)} requisicoes, {len(rotulos)} rotulos CAPEC")

    sqli = d[COL_SQLI] == 1
    normal = d[COL_NORMAL] == 1
    n_rotulos = d[rotulos].sum(axis=1)

    print(f"  com tag SQLi        : {int(sqli.sum())}")
    print(f"    destas, multirotulo: {int((sqli & (n_rotulos > 1)).sum())} (mantidas)")
    print(f"  benignas disponiveis: {int(normal.sum())}")

    idx = d.index[sqli | normal]
    sel = d.loc[idx]
    e_sqli = sel[COL_SQLI] == 1

    host = sel.request_host.fillna("srbh.local").astype(str)
    caminho = sel.request_http_request.fillna("").astype(str)

    saida = pd.DataFrame({
        "classification": e_sqli.astype(int).values,
        "Method": sel.request_http_method.values,
        "URL": ("http://" + host + caminho).values,
        "content": sel.request_body.values,
        "attack_type": e_sqli.map({True: "sqli", False: "legitimate"}).values,
        # apoio para a decisao posterior -- nao fazem parte do schema comum
        "capec_n_rotulos": n_rotulos.loc[idx].values,
        "tem_indicador_sqli": (
            (caminho + " " + sel.request_body.fillna("").astype(str))
            .map(decodificar).str.contains(PADRAO_SQLI).astype(int).values
        ),
    })

    saida.to_csv(SAIDA, index=False)

    n_s = int((saida.attack_type == "sqli").sum())
    n_b = int((saida.attack_type == "legitimate").sum())
    sem = int(((saida.attack_type == "sqli") & (saida.tem_indicador_sqli == 0)).sum())
    print(f"\n{SAIDA}")
    print(f"  {len(saida)} linhas: {n_s} SQLi + {n_b} benignas (sem balancear)")
    print(f"  SQLi sem indicador lexico: {sem} ({sem / n_s:.1%}) "
          f"-- decisao pendente, ver tem_indicador_sqli")
    print(f"  benignas COM indicador   : "
          f"{int(((saida.attack_type == 'legitimate') & (saida.tem_indicador_sqli == 1)).sum())}")


if __name__ == "__main__":
    main()
