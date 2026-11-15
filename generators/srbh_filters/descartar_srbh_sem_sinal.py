"""Descarta do SR-BH as requisicoes rotuladas SQLi que nao tem sinal de SQL.

DECISAO E JUSTIFICATIVA

As 6.949 foram lidas uma a uma (ver `corpora/srbh/README.md`). NAO sao trafego
benigno mal rotulado: sao sessoes do OWASP ZAP. O scanner injeta um payload num
segmento do caminho e repete o crawl inteiro do site com ele -- por isso o
volume com tao pouca variedade real.

Mesmo assim saem do corpus, por dois motivos:

  1. Cerca de um quinto sao sondas de SQLi legitimas (`(`, `)`, `NULL` colados
     num segmento), mas a FASE de sondagem: sem nenhuma semantica de SQL.
     Aprende-las e aprender "caractere estranho colado no caminho" -- o mesmo
     atalho estrutural que este trabalho documenta como artefato de coleta.
  2. O resto sao ataques de OUTRA classe (command injection, code injection,
     response splitting, SSRF, XXE) mais um residuo de trafego de conta sem
     payload nenhum. Numa tarefa binaria SQLi-vs-benigno, ensinar template
     injection como "SQLi" ensina a classe errada.

Nao viram benignas -- sao descartadas, mesma regra aplicada ao XSS: rotular
ataque como benigno envenenaria a validacao.

Reversivel: `datasets/decodificados/` e `datasets/originais/` ficam intactos.

Uso:  python descartar_srbh_sem_sinal.py
"""
from pathlib import Path

import pandas as pd

SEED = 42
RAIZ = Path(__file__).resolve().parents[1]
ALVO = RAIZ / "datasets" / "deduplicados_decodificados" / "srbh_completo_decodificado_sqli.csv"


def main():
    d = pd.read_csv(ALVO, low_memory=False)
    n0 = len(d)
    sqli = d.attack_type == "sqli"
    descartar = sqli & (d.tem_indicador_sqli == 0)
    print(f"entrada: {n0} ({int(sqli.sum())} SQLi + {int((~sqli).sum())} benignas)")
    print(f"descartando {int(descartar.sum())} SQLi sem sinal lexico")

    d = d[~descartar]

    # rebalanceia: a classe benigna agora sobra
    i_s = d.index[d.attack_type == "sqli"]
    i_b = d.index[d.attack_type == "legitimate"]
    alvo = min(len(i_s), len(i_b))
    if len(i_b) > alvo:
        i_b = pd.Series(i_b).sample(n=alvo, random_state=SEED).values
    if len(i_s) > alvo:
        i_s = pd.Series(i_s).sample(n=alvo, random_state=SEED).values
    d = d.loc[pd.Index(i_s).union(pd.Index(i_b)).sort_values()]

    d.to_csv(ALVO, index=False)
    print(f"saida  : {len(d)} ({alvo} SQLi + {alvo} benignas)")
    print(f"mantido: {100 * len(d) / n0:.1f}% do arquivo anterior")
    resid = int(((d.attack_type == "sqli") & (d.tem_indicador_sqli == 0)).sum())
    print(f"residuo SQLi sem sinal: {resid}")


if __name__ == "__main__":
    main()
