# CSIC 2010

O corpus padrão da literatura de detecção de ataques web. Aplicação de
e-commerce sintética, tráfego gerado pelo CSIC espanhol.

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `../../scripts/filtrar_sqli.py` | `datasets/originais/csic_balanceado_sqli.csv` |
| 2 | (decodificado a montante por `datasets/decodificar_csic.py`) | `datasets/decodificados/csic_balanceado_decodificado_sqli.csv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/csic_balanceado_decodificado_sqli.csv` |

## Números

| etapa | n | SQLi | benignas |
|---|---|---|---|
| origem (SQLi + XSS) | 7.216 | 2.104 | 3.608 |
| após filtro SQLi | 4.208 | 2.104 | 2.104 |
| **final (deduplicado)** | **2.354** | **1.177** | **1.177** |

Mantido: **55,9 %** — a maior perda proporcional depois do SR-BH.

## Decisões

**1.504 amostras de XSS descartadas.**

**1.547 duplicatas exatas removidas (36,8 % do corpus filtrado).** Isso não é
defeito da nossa preparação: o CSIC tem só **28 caminhos distintos em 7.216
requisições**, então requisições repetidas são inerentes ao corpus. A auditoria
anterior já havia medido 47,1 % de duplicatas no espaço de features.

**Zero conflitos de rótulo.** Nenhuma requisição idêntica aparece como benigna e
como ataque — a rotulagem do CSIC é por requisição, ao contrário da do SR-BH.

## Ressalvas

- **Aplicação única, 28 caminhos distintos, 99,6 % de reuso de path.** Após a
  deduplicação sobram 2.354 amostras — é agora o menor corpus da fase, e isso
  deve ser considerado ao usá-lo como alvo (intervalos de confiança largos).
- No original, **100 % dos ataques** e 42 % das benignas tinham `%XX`. O
  `enc_pct` era um oráculo quase perfeito aqui e apontava para o lado oposto do
  corpus próprio. Resolvido pela decodificação.
