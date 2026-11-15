# Corpus artificial (IA)

10.000 amostras sintéticas geradas por `datasets/gerar_dataset_artificial.py`,
cobrindo **21 perfis de site** diferentes. Não é corpus alvo — existe para somar
ao treino.

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `../../scripts/filtrar_sqli.py` | `datasets/originais/dataset_artificial_ia_sqli.tsv` |
| 2 | (decodificado a montante por `datasets/decodificar_artificial.py`) | `datasets/decodificados/dataset_artificial_ia_decodificado_sqli.tsv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/dataset_artificial_ia_decodificado_sqli.tsv` |

## Números

| etapa | n | SQLi | benignas |
|---|---|---|---|
| origem | 10.000 | 2.500 | 5.000 |
| após filtro SQLi | 5.000 | 2.500 | 2.500 |
| **final (deduplicado)** | **4.626** | **2.313** | **2.313** |

Mantido: **92,5 %**.

## Decisões

**2.500 amostras de XSS descartadas.**

**187 duplicatas exatas removidas.** Esperado num corpus gerado por template — o
gerador produz colisões.

## Para que serve

A auditoria anterior mediu que o valor deste corpus era sobretudo **diluir os
artefatos estruturais**: os 21 perfis de site quebram a correlação falsa entre
`path_depth` e benignidade que existe no corpus próprio (um host só). Com as 36
features de ataque, adicioná-lo ao treino **não mudava nada** (376 → 376 erros no
CSIC) — o filtro de features e o corpus artificial resolvem o mesmo problema e
não se somam.

Isso vale como hipótese a re-testar nesta fase, agora com SQLi só e quatro alvos.

## Ressalvas

- Sintético. Não serve como corpus alvo — só como aditivo de treino.
- No original, 51,3 % das linhas tinham `%XX`, e o dataset embute o próprio viés
  de encoding (a auditoria anterior mediu `enc_pct` com AUC isolado de 0,882
  aqui). Resolvido pela decodificação.
