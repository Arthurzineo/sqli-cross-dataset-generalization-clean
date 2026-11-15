"""Deixa no SR-BH apenas as requisicoes com semantica de SQL de verdade.

CONTEXTO -- este e o SEGUNDO corte no SR-BH; `descartar_srbh_sem_sinal.py` foi
o primeiro. Os dois existem porque o primeiro criterio era inconsistente.

O primeiro corte usou `tem_indicador_sqli`, que aceita qualquer aspa ou
ponto-e-virgula mas nao aceita `(`, `)` e `NULL`. Isso separou `/blog'` de
`/blog(` por acidente da regex: as quatro sao a MESMA familia -- sonda do
scanner colando um metacaractere num segmento do caminho, para provocar erro de
sintaxe no SQL. Descartar uma e manter a outra nao tem criterio.

Este corte aplica a regra principiada: **exigir semantica de SQL**, ou seja
palavra-chave (SELECT, UNION, information_schema, sleep...), injecao booleana
(`AND 1923=7138`) ou comentario/literal SQL (`--`, `/*`, `@@`, `0x...`).

Sai:
  * 869 requisicoes de OUTRA classe sem sintaxe SQL -- XSS
    (`'"<script>alert(1);</script>`) e SSI (`"><!--#EXEC cmd="ls /"-->`) que
    passaram no filtro anterior so por conterem aspas. Numa tarefa binaria
    SQLi-vs-benigno, ensina-las como SQLi ensina a classe errada.
  * 7.304 sondas puras (`/blog'`, `/blog;`, `/blog'"`) -- sao SQLi, mas so a
    fase de sondagem. Sem semantica de SQL, so sao aprendiveis como "caractere
    estranho no caminho": o atalho estrutural que este trabalho documenta como
    artefato de coleta, o `path_depth` com outra roupa.

Fica quem tem sintaxe SQL, inclusive as 732 que trazem marca de outra classe
junto -- essas sao SQLi de verdade com ruido, nao classe errada.

Nao viram benignas -- sao descartadas, mesma regra aplicada ao XSS.
Reversivel: `datasets/decodificados/` e `datasets/originais/` ficam intactos.

Uso:  python filtrar_semantica_sql.py
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analisar_rotulos import PADRAO_SQL_ESTRITO, PADRAO_OUTRA_CLASSE  # noqa: E402

SEED = 42
ALVO = RAIZ / "datasets" / "deduplicados_decodificados" / "srbh_completo_decodificado_sqli.csv"


def main():
    d = pd.read_csv(ALVO, low_memory=False)
    n0 = len(d)
    sqli = d.attack_type == "sqli"
    txt = (d.URL.fillna("").astype(str) + " " + d.content.fillna("").astype(str))
    tem_sql = txt.str.contains(PADRAO_SQL_ESTRITO)
    tem_outra = txt.str.contains(PADRAO_OUTRA_CLASSE)

    fora_outra = sqli & ~tem_sql & tem_outra
    fora_sonda = sqli & ~tem_sql & ~tem_outra
    print(f"entrada: {n0} ({int(sqli.sum())} SQLi + {int((~sqli).sum())} benignas)")
    print(f"  - so outra classe (sem sintaxe SQL): {int(fora_outra.sum())}")
    print(f"  - so aspa/ponto-e-virgula          : {int(fora_sonda.sum())}")

    d = d[~(fora_outra | fora_sonda)]

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

    txt2 = (d.URL.fillna("").astype(str) + " " + d.content.fillna("").astype(str))
    resid = int((~txt2[d.attack_type == "sqli"].str.contains(PADRAO_SQL_ESTRITO)).sum())
    print(f"residuo SQLi sem sintaxe SQL: {resid}")


if __name__ == "__main__":
    main()
