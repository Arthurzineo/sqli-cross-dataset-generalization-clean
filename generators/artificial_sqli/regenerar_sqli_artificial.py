#!/usr/bin/env python
# Regenera SO as linhas SQLi do dataset artificial, usando o gerador de
# payloads melhorado (sqli_payloads.py). Mantem as linhas benignas e as de
# XSS BYTE A BYTE identicas ao dataset_artificial_ia.tsv original, para que o
# experimento isole exatamente o efeito da mudanca nas tecnicas de SQLi.
#
# Reaproveita os CONTEXTOS de injecao do gerador original (login, busca,
# produto_id, ordenar, api_json, path, comentario, cupom) - muda apenas o
# PAYLOAD que vai dentro deles. Assim o "onde o ataque acontece" continua o
# mesmo; muda so o "como o ataque e escrito".
#
# Saida: dataset_artificial_ia_sqli_melhorado.tsv (mesmo schema/ordem de
# colunas do original).

import random

import pandas as pd

import gerar_dataset_artificial as base
from sqli_payloads import gerar_payload_sqli

ENTRADA = "dataset_artificial_ia.tsv"
SAIDA = "dataset_artificial_ia_sqli_melhorado.tsv"
SEED = 42


def gerar_sqli_melhorado():
    """Igual a base.gerar_sqli(), mas com o payload vindo do gerador novo."""
    dom = random.choice(base.DOMINIOS)
    payload = gerar_payload_sqli()
    if random.random() < 0.15:
        payload = base.enc(payload)   # variante url-encoded (mantido do original)
    contexto = random.choice(base.SQLI_CONTEXTOS)
    method, path, qs, body_params, tipo_body = contexto(dom, payload)
    method, url, body = base.montar_linha(method, path, qs, body_params, tipo_body, dom)
    return base.rand_timestamp(), method, url, body, 1, 0, 1


def main():
    print(f"Lendo {ENTRADA}...")
    df = pd.read_csv(ENTRADA, sep="\t", encoding="latin-1")
    print(f"  {len(df)} linhas | benignas={int((df.malicioso==0).sum())} "
          f"sqli={int((df.sqli==1).sum())} xss={int((df.xss==1).sum())}")

    n_sqli = int((df.sqli == 1).sum())

    # gera n_sqli linhas SQLi novas, unicas por (url, body), com o mesmo
    # mecanismo de deduplicacao do gerador original
    random.seed(SEED)
    vistos = set()
    novas = base.gerar_unicas(gerar_sqli_melhorado, n_sqli, vistos)
    novas_df = pd.DataFrame(novas, columns=list(df.columns))

    # substitui em ordem: mantem benignas e xss no lugar, troca so as SQLi
    resultado = df.copy()
    idx_sqli = df.index[df.sqli == 1].tolist()
    for col in df.columns:
        resultado.loc[idx_sqli, col] = novas_df[col].values

    # sanidade: nada mudou fora das linhas SQLi
    nao_sqli = df.sqli != 1
    assert resultado.loc[nao_sqli].equals(df.loc[nao_sqli]), "linhas nao-SQLi foram alteradas!"

    resultado.to_csv(SAIDA, sep="\t", index=False, encoding="utf-8")
    print(f"[ok] {SAIDA}: {len(resultado)} linhas ({n_sqli} SQLi regeneradas, "
          f"benignas+XSS intactas)")


if __name__ == "__main__":
    main()
