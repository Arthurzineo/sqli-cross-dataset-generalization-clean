"""Remove do SR-BH as requisicoes rotuladas benignas que contem payload de ataque.

O problema e o espelho do que motivou os cortes na classe SQLi: a rotulagem do
SR-BH e por SESSAO de varredura, entao o trafego de ataque que caiu fora da
janela de uma sessao ficou marcado como `000 - Normal`. Medido no corpus:

    29,2% das benignas (21.257 de 72.803) contem payload de ataque real

Por familia, todas verificadas por amostragem antes do corte:

    path traversal / LFI   17.131   `../../../../etc/passwd`, `boot.ini`
    SSI injection           2.426   `<!--#EXEC cmd="ls /"-->`
    XSS                     1.237   `'"<script>alert(1);</script>`
    SQL keyword               322   `%');SELECT SLEEP(5)#`
    command injection         121   `/blog;sleep 15;/index.php/...`
    code injection             13   `${@die(sha1(xyzt))}`
    SQL booleano                7   `comment= AND 1=1 -- `

POR QUE IMPORTA MAIS QUE O PROBLEMA ANTERIOR: como ALVO de validacao, benigna
mal rotulada infla o FPR com ACERTOS. Um modelo que sinaliza corretamente
`/../../../etc/passwd` e contado como falso positivo. A metrica passa a punir o
detector por funcionar.

CONTROLE: o mesmo padrao aplicado aos outros cinco corpora marca 0 benignas em
CSIC, ECML e nos dois artificiais. No corpus proprio marca 8, e essas foram
inspecionadas uma a uma: sao FALSOS POSITIVOS -- trafego legitimo do OJS cujo
resumo em prosa casa por acaso (`...or X = Y...`). Por isso o corte roda so no
SR-BH, que nao tem corpo em prosa.

Descartadas, nao reetiquetadas como ataque: nao da para saber a classe (a maior
familia e path traversal, que nao e SQLi), e a fase e binaria SQLi-vs-benigno.

Reversivel: `datasets/decodificados/` e `datasets/originais/` ficam intactos.

Uso:  python remover_benignas_com_payload.py
"""
import re
from pathlib import Path

import pandas as pd

SEED = 42
RAIZ = Path(__file__).resolve().parents[1]
ALVO = RAIZ / "datasets" / "deduplicados_decodificados" / "srbh_completo_decodificado_sqli.csv"

FAMILIAS = [
    ("path_traversal", r"(?i)\.\./\.\.|/etc/passwd|boot\.ini|win\.ini|/etc/vmware"),
    ("sql_keyword", r"(?i)\b(?:union\s+(?:all\s+)?select|information_schema|"
                    r"order\s+by\s+\d|group\s+by\s+\d|sleep\s*\(?\s*\d|"
                    r"benchmark\s*\(|waitfor\s+delay)\b"),
    ("sql_booleano", r"(?i)\b(?:or|and)\b\s*(?:not\s*)?[\w.'\"()%]{1,20}\s*"
                     r"(?:=|<>|!=|[<>]=?)\s*[\w.'\"()%]{1,20}"),
    ("command_injection", r"(?i)[;&|]\s*(?:sleep|cat|ls|id|whoami|ping)\s"),
    ("code_injection", r"(?i)\$\{|print\s*\(\s*chr\s*\(|die\s*\(\s*sha1"),
    ("ssi", r"(?i)<!--\s*\#\s*(?:exec|include)"),
    ("xss", r"(?i)<script|onerror\s*=|onmouseover\s*=|javascript:|alert\s*\("),
]


def main():
    d = pd.read_csv(ALVO, low_memory=False)
    n0 = len(d)
    txt = d.URL.fillna("").astype(str) + " " + d.content.fillna("").astype(str)
    benigna = d.attack_type == "legitimate"

    fora = pd.Series(False, index=d.index)
    print(f"entrada: {n0} ({int((~benigna).sum())} SQLi + {int(benigna.sum())} benignas)")
    for nome, pat in FAMILIAS:
        m = benigna & ~fora & txt.str.contains(pat, regex=True)
        print(f"  - {nome:<20}{int(m.sum()):>7}")
        fora |= m
    print(f"  total removido        {int(fora.sum()):>7} "
          f"({100 * fora.sum() / benigna.sum():.1f}% das benignas)")

    d = d[~fora]
    i_s = d.index[d.attack_type == "sqli"]
    i_b = d.index[d.attack_type == "legitimate"]
    alvo = min(len(i_s), len(i_b))
    for i in (i_s, i_b):
        pass
    if len(i_s) > alvo:
        i_s = pd.Series(i_s).sample(n=alvo, random_state=SEED).values
    if len(i_b) > alvo:
        i_b = pd.Series(i_b).sample(n=alvo, random_state=SEED).values
    d = d.loc[pd.Index(i_s).union(pd.Index(i_b)).sort_values()]
    d.to_csv(ALVO, index=False)
    print(f"saida  : {len(d)} ({alvo} SQLi + {alvo} benignas)")
    print(f"mantido: {100 * len(d) / n0:.1f}%")


if __name__ == "__main__":
    main()
