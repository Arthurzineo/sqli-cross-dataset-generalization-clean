# Registro de decisões por corpus

Uma pasta por corpus. Cada `README.md` traz a procedência, o pipeline com os
scripts na ordem, os números de cada etapa, as decisões tomadas (com o porquê) e
as ressalvas a declarar no artigo.

| corpus | pasta | papel | n final |
|---|---|---|---|
| SR-BH 2020 | [`srbh/`](srbh/README.md) | alvo / treino | 103.092 |
| site-sqli | [`site_sqli/`](site_sqli/README.md) | alvo / treino | 9.122 |
| site-cooking | [`site_cooking/`](site_cooking/README.md) | alvo / treino | 7.332 |
| Próprio | [`proprio/`](proprio/README.md) | alvo / treino | 37.212 |
| ECML/PKDD 2007 | [`ecml/`](ecml/README.md) | alvo / treino | 3.300 |
| CSIC 2010 | [`csic/`](csic/README.md) | alvo / treino | 2.136 |
| Artificial SQLi+ | [`artificial_sqli_melhorado/`](artificial_sqli_melhorado/README.md) | aditivo de treino | 5.000 |
| Artificial | [`artificial/`](artificial/README.md) | aditivo de treino | 4.626 |

Os dois artificiais são versões do mesmo corpus (lado benigno idêntico) —
escolher uma, nunca as duas.

## Convenção

Toda decisão que altera dados é tomada por um **script persistido** na raiz de
`../` (nunca por comando solto), e registrada no `README.md` do corpus afetado
com os números de antes e depois. Correções de decisões anteriores ficam no
registro, marcadas — não são reescritas silenciosamente.

Scripts em uso:

| script | o que faz |
|---|---|
| `../scripts/importar_site_lab.py` | converte os quatro JSONL dos dois sites ao schema local |
| `../scripts/filtrar_sqli.py` | filtra SQLi + balanceia os corpora existentes |
| `../scripts/preparar_srbh.py` | extrai o SR-BH do CSV multi-rótulo de 436 MB |
| `../scripts/decodificar.py` | `unquote_plus` até estabilizar (idempotente) |
| `../scripts/deduplicar.py` | conflitos + duplicatas + descontaminação dos sites + balanceamento |
| `../scripts/deduplicar_codificados.py` | mesma limpeza nos oito corpora, preservando URL-encoding |
| `../scripts/preparar_ecml_codificado.py` | reconstrói do XML a versão ECML anterior à decodificação |
| `../scripts/verificar.py` | confere integridade e contaminação entre corpora |

Os scripts ficam em `../scripts/`, **não** dentro de cada pasta de corpus: cada
um trata vários corpora ao mesmo tempo (`deduplicar.py` cobre os 8), então uma
cópia por pasta seriam 6 cópias divergindo. A pasta do corpus registra *quais*
scripts o tocaram e em que ordem; o código mora num lugar só.

Todos usam caminhos relativos ao próprio arquivo, então rodam de qualquer
diretório:

    python GENERALIZACAO/SQLI/scripts/verificar.py
