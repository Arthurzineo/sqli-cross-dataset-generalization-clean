"""Remove do CSIC as amostras cujo payload e o placeholder `'INJECTED_PARAM`.

O CSIC 2010 marca alguns ataques substituindo o valor do parametro pelo literal
`'INJECTED_PARAM` -- e convencao de rotulagem do corpus, nao payload real:

    .../autenticar.jsp?modo=entrar&login='INJECTED_PARAM&pwd=70staje...
    .../caracteristicas.jsp?id=1'INJECTED_PARAM

Nao ha ataque para o extrator enxergar: sobra uma aspa e uma palavra em
maiusculas. Mante-las ensina o modelo a detectar a string `INJECTED_PARAM`, que
so existe neste corpus -- artefato de coleta puro, exatamente o que esta fase
investiga.

Sao descartadas, nao convertidas em benignas (mesma regra do XSS), e a classe
benigna e reduzida para manter o 50/50.

Reversivel: `datasets/decodificados/` e `datasets/originais/` ficam intactos.

Uso:  python remover_csic_injected_param.py
"""
from pathlib import Path

import pandas as pd

SEED = 42
RAIZ = Path(__file__).resolve().parents[1]
ALVO = RAIZ / "datasets" / "deduplicados_decodificados" / "csic_balanceado_decodificado_sqli.csv"
MARCA = "INJECTED_PARAM"


def main():
    d = pd.read_csv(ALVO)
    n0 = len(d)
    txt = d.URL.fillna("").astype(str) + " " + d.content.fillna("").astype(str)
    fora = (d.attack_type == "sqli") & txt.str.contains(MARCA, regex=False)
    print(f"entrada: {n0} ({int((d.attack_type=='sqli').sum())} SQLi + "
          f"{int((d.attack_type=='legitimate').sum())} benignas)")
    print(f"  - com '{MARCA}': {int(fora.sum())}")

    d = d[~fora]
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
    print(f"mantido: {100 * len(d) / n0:.1f}%")


if __name__ == "__main__":
    main()
