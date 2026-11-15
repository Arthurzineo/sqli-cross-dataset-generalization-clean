"""Mede, em cada corpus, quantos ataques nao tem sinal lexico de SQL.

Responde a pergunta: "sobrou requisicao mal classificada como SQLi?"

O SR-BH e o caso critico -- o rotulo dele e por SESSAO de varredura, nao por
requisicao: uma execucao de sqlmap emite tambem requisicoes comuns de
reconhecimento, e todas ficaram marcadas como ataque. Mas o fenomeno nao e
exclusivo dele: em qualquer corpus existem ataques cujo payload o espaco de
features nao enxerga. A auditoria anterior chamou isso de teto de
representacao, e mediu 36,4% entre os falsos negativos comuns.

Por isso o script mede TODOS os corpora com a MESMA heuristica -- so assim da
para separar "rotulagem ruim do SR-BH" de "limite do extrator", que produzem o
mesmo sintoma.

A heuristica NAO e usada para filtrar nada. Ela e um proxy: tokens de SQL e
metacaracteres sobre o texto ja decodificado. Marca de menos (payload exotico
sem token conhecido) e marca de mais (aspas em texto benigno).

Uso:
    python analisar_rotulos.py                 # datasets/deduplicados_decodificados
    python analisar_rotulos.py decodificados   # compara com antes da limpeza
"""
import glob
import os
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BASE = RAIZ / "datasets"

# CORRECAO (medida, nao suposta): a primeira versao deste padrao nao cobria
# injecao booleana cega -- `" AND "1"="1` no CSIC e `AND 1923=7138` no corpus
# proprio sao SQLi legitimos e passavam como "sem sinal". Isso inflava a
# contagem dos corpora bem rotulados e fazia o SR-BH parecer menos anomalo do
# que e. Adicionados: aspas duplas, comparacao booleana apos AND/OR/XOR,
# comentarios de bloco, ORDER/GROUP BY, literais hex e funcoes comuns.
PADRAO_SQLI = re.compile(
    r"\b(?:select|union|insert|update|delete|drop|information_schema|sleep|"
    r"benchmark|concat|updatexml|extractvalue|having|waitfor|exec|cast|"
    r"substring|sysobjects|version|database|table_name|xor)\b"
    r"|\b(?:and|or)\b\s*[\w'\"()]+\s*(?:=|<>|!=|\blike\b)"
    r"|\b(?:order|group)\s+by\b"
    r"|'|\"|--|/\*|@@|0x[0-9a-f]{4,}|;",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------- #
# Criterio ESTRITO: exige semantica de SQL de verdade, nao so um metacaractere.
#
# `PADRAO_SQLI` acima aceita qualquer aspa ou ponto-e-virgula. Isso deixa passar
# duas coisas que nao sao SQLi: payload de outra classe que por acaso tem aspa
# (XSS `'"<script>alert(1)`, SSI `"><!--#EXEC cmd="ls /"-->`), e a sonda pura do
# scanner (`/blog'`, `/blog;`) -- que e SQLi, mas so a fase de sondagem, sem
# nenhuma semantica de SQL, aprendivel apenas como "caractere estranho no
# caminho": o mesmo atalho estrutural que este trabalho documenta como artefato.
# --------------------------------------------------------------------------- #
PADRAO_SQL_ESTRITO = re.compile(
    r"""(?ix)
    # palavras-chave
      \b(?: select|union|insert|update|delete|drop|alter|shutdown|truncate
           | information_schema|sysobjects|table_name
           | sleep|benchmark|waitfor|updatexml|extractvalue|xor
           | order\s+by | group\s+by )\b
    # injecao booleana -- o identificador pode ter ponto (Rl_v.Account) e a
    # comparacao pode ser =, <>, !=, <, >, LIKE, IN(...) ou BETWEEN..AND
    # `NOT` opcional entre o operador logico e o operando (`OR NOT 9829=8460`,
    # injecao booleana cega do sqlmap), e `IN BOOLEAN MODE` (full-text do MySQL)
    | \b(?:or|and)\b \s* (?:\bnot\b\s*)? [\w.'"()%]+ \s*
      (?: [<>]=? | <> | != | = | \blike\b | \bin\b\s*\( | \bbetween\b )
    | \bin\s+boolean\s+mode\b
    | \bas\b\s+\w+\s+\bwhere\b
    # comentario / literal SQL. `--` pode vir colado no separador (`shutdown--&`)
    | -- | /\* | @@ | 0x[0-9a-f]{4,}
    # evasao por concatenacao e por remocao de espaco, usada no ECML:
    # 'UNI' 'ON' , UNIONALLSELECT , DELETEFROM , INSERTINTO
    | union\s*all\s*select | unionall | selectfrom | deletefrom | insertinto
    | \bexec\s*\(
    # arsenal do sqlmap: condicionais, funcoes de tempo e fuzz de parenteses
    | \b(?: make_set | iif | elt | if | case\s+when | rlike | regexp
           | procedure\s+analyse | call\s+\w+ | chr | char | repeat
           | dbms_pipe | utl_inaddr | pg_sleep )\s*\(
    | [,)(\"']{4,}
    """,
)

# Marcas de ataque de OUTRA classe (XSS, SSI, RCE, command injection, LFI).
PADRAO_OUTRA_CLASSE = re.compile(
    r"(?i)<script|onmouseover\s*=|onerror\s*=|onload\s*=|javascript:|"
    r"alert\s*\(|<img|<svg|<iframe"
    r"|print\s*\(\s*chr\s*\(|\$\{|passthru|phpinfo|eval\s*\("
    r"|<!--\s*#|[|&;`]\s*(?:cat|ls|id|whoami|ping|dir)\b|`"
    r"|/etc/passwd|c:[\\/]|\.\./",
)


def carregar(caminho):
    sep = "\t" if caminho.endswith(".tsv") else ","
    enc = "latin-1" if caminho.endswith(".tsv") else "utf-8"
    d = pd.read_csv(caminho, sep=sep, encoding=enc, low_memory=False)
    if "attack_type" in d.columns:
        rot, cu, cc = d.attack_type, "URL", "content"
    else:
        rot, cu, cc = d.sqli.map({1: "sqli", 0: "legitimate"}), "url", "body"
    txt = (d[cu].fillna("").astype(str) + " "
           + d[cc].fillna("").astype(str)).str.strip()
    return d, rot, txt


def analisar(pasta):
    arqs = sorted(f for f in glob.glob(f"{BASE}/{pasta}/*")
                  if f.endswith((".csv", ".tsv"))
                  and not os.path.basename(f).split(".")[0].isupper()
                  and "RELATORIO" not in f and "ROTULOS" not in f)
    print(f"=== {pasta}/ — ataques sem sinal léxico de SQL ===\n")
    print(f"{'corpus':<50}{'SQLi':>9}{'sem sinal':>11}{'%':>7}"
          f"{'benignas c/ sinal':>19}{'%':>7}")
    linhas = []
    for f in arqs:
        d, rot, txt = carregar(f)
        tem = txt.str.contains(PADRAO_SQLI)
        s = rot == "sqli"
        b = rot == "legitimate"
        sem = int((s & ~tem).sum())
        ben_com = int((b & tem).sum())
        nome = os.path.basename(f)
        print(f"{nome[:49]:<50}{int(s.sum()):>9}{sem:>11}"
              f"{100 * sem / max(int(s.sum()), 1):>6.1f}%"
              f"{ben_com:>19}{100 * ben_com / max(int(b.sum()), 1):>6.1f}%")
        linhas.append({"corpus": nome, "n_sqli": int(s.sum()),
                       "sqli_sem_sinal": sem,
                       "pct_sqli_sem_sinal": round(100 * sem / max(int(s.sum()), 1), 1),
                       "benignas_com_sinal": ben_com,
                       "pct_benignas_com_sinal": round(100 * ben_com / max(int(b.sum()), 1), 1)})
    saida = BASE / pasta / "ROTULOS.csv"
    pd.DataFrame(linhas).to_csv(saida, index=False)
    print(f"\n-> {saida}")


if __name__ == "__main__":
    analisar(sys.argv[1] if len(sys.argv) > 1 else "deduplicados_decodificados")
