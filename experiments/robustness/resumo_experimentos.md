# Experimentos de revisão 3.1, 3.2 e 3.3

Data de execução: 2026-11-02. Todos os artefatos novos estão abaixo de
`analises_revisao_v2/experimentos/`; nenhum arquivo de entrada foi alterado.

## Protocolo comum

- Os índices de treino, validação e teste vieram dos `split_file` da coleção
  controlada, obtidos a partir de
  `artigo/complementos_generalizacao_v1/full/analysis/master_results.parquet`
  (`run_experimentos.py:88-110`).
- Foram usadas as sementes 42, 123, 2026, 1337 e 9001 e as famílias de
  validação já congeladas (`run_experimentos.py:45-52`).
- Imputação, padronização, ajuste, seleção do limiar na validação e cálculo de
  métricas reutilizam o código da coleção controlada
  (`run_experimentos.py:141-180`).
- Os resumos seguem o artigo: média entre sementes dentro do alvo e, depois,
  média não ponderada entre alvos.
- O manifesto consolidado contém 829 ajustes em
  `manifesto_execucoes.csv`: 199 de 3.1, 30 de 3.2(a), 180 de 3.2(b) e 420 de
  3.3. Ele inclui o `split_id` original.

## 3.1 — Contribuição com tamanho controlado

Implementação: `run_experimentos.py:191-276`. Em cada alvo/semente, calculou-se
o menor número disponível entre todas as combinações fonte × classe do treino;
cada combinação foi subamostrada para esse número com uma semente SHA-256
derivada de análise, alvo, fonte, semente experimental e classe
(`run_experimentos.py:83-85,203-218`). O manifesto exato das linhas é
`3_1_tamanho_controlado/manifesto_linhas_selecionadas.csv`. A mesma seleção foi
usada no conjunto completo e nas remoções.

### Tamanho usado por fonte e classe

| alvo | 42 | 123 | 2026 | 1337 | 9001 |
|---|---:|---:|---:|---:|---:|
| artificial_sqli | 1.650 | 1.177 | 1.177 | 1.177 | 1.177 |
| csic | 1.650 | 1.650 | 1.650 | 1.650 | 1.650 |
| ecml | 2.322 | 1.177 | 1.177 | 1.177 | 1.177 |
| proprio | 1.650 | 1.177 | 1.177 | 1.177 | 1.177 |
| site_cooking | 1.650 | 1.177 | 1.177 | 1.177 | 1.177 |
| site_sqli | 1.650 | 1.177 | 1.177 | 1.177 | 1.177 |
| srbh | 1.650 | 1.177 | 1.177 | 1.650 | 1.177 |

Fonte: `3_1_tamanho_controlado/tamanho_por_classe_alvo_semente.csv`.

### Resultado

- Foram comparados 164 pares por semente e 40 pares alvo × fonte após a média
  entre sementes. A cobertura é a mesma das remoções elegíveis originais; uma
  fonte retida para validação não entra na remoção daquela semente.
- No nível alvo × fonte, **14/40 pares mudaram de sinal**. No nível da semente,
  foram **74/164**.
- Spearman entre contribuição original e controlada: **rho = 0,4767**
  (`p = 0,00187`) nas 40 médias alvo × fonte; **rho = 0,2401**
  (`p = 0,00196`) nos 164 pares por semente.
- No subconjunto comparável CatBoost CANONICALIZED, remover a fonte aumentou o
  F1 em **11/40** médias alvo × fonte e o reduziu em **29/40**, tanto no
  original quanto no tamanho controlado. Essa igualdade de totais esconde as
  14 trocas de sinal entre pares específicos.
- Por semente, o original teve 62 remoções que aumentaram e 102 que reduziram o
  F1; com tamanho controlado foram 70 e 94, respectivamente.

Resultados completos: `3_1_tamanho_controlado/contribuicoes_por_semente.csv`,
`contribuicoes_media_alvo_fonte.csv`, `resultados_por_semente.csv` e
`resumo_numerico.json`.

## 3.2 — Viés dos filtros do SR-BH

### Construção auditada da variante

A preparação está em `run_experimentos.py:292-395`, partindo de
`SQLI/datasets/originais/srbh_completo_sqli.csv`.

| etapa | benignos | maliciosos | total |
|---|---:|---:|---:|
| seleção original | 525.195 | 250.311 | 775.506 |
| após conflitos | 501.524 | 244.403 | 745.927 |
| após deduplicação exata | 89.292 | 184.112 | 273.404 |
| balanceado, sem filtros | **89.292** | **89.292** | **178.584** |
| final filtrado reconstruído | 53.290 | 53.290 | 106.580 |

A reconstrução do conjunto filtrado coincidiu exatamente com a cópia RAW
existente. Os três cortes identificaram 7.043 SQLi sem indicador, 7.398 SQLi
fora do padrão estrito e 21.561 benignos com padrão de ataque. Cada corte foi
seguido por rebalanceamento, que retirou o mesmo número da classe oposta. A
vista CANONICALIZED foi derivada das mesmas 178.584 linhas da RAW.

Artefatos: `3_2_srbh_sem_filtros/variant/contagens_preparacao.csv`,
`manifesto_linhas_srbh_sem_filtros.csv`, `cohort.parquet` e `READY.json`.

### (a) SR-BH sem filtros como alvo

| modelo | vista | F1 filtrado | F1 sem filtros | delta F1 | delta PR-AUC | delta recall | delta FPR |
|---|---|---:|---:|---:|---:|---:|---:|
| CatBoost | CAN | 0,7900 | 0,7245 | -0,0655 | -0,0458 | -0,0842 | +0,0252 |
| CatBoost | RAW | 0,7024 | 0,6264 | -0,0760 | -0,1071 | -0,0793 | +0,0444 |
| Logística | CAN | 0,6977 | 0,6344 | -0,0633 | -0,0784 | -0,0581 | +0,0497 |
| Logística | RAW | 0,5747 | 0,5375 | -0,0373 | -0,0341 | -0,0448 | -0,0019 |
| MLP | CAN | 0,7274 | 0,6661 | -0,0613 | -0,0939 | -0,0592 | +0,0478 |
| MLP | RAW | 0,6704 | 0,6194 | -0,0510 | -0,0579 | -0,0660 | +0,0108 |

Nos registros retirados pelos filtros:

| modelo/vista | SQLi sem indicador: F1 / recall (n=7.043) | SQLi fora do padrão: F1 / recall (n=7.398) | benignos com padrão: FPR (n=21.561) |
|---|---:|---:|---:|
| CatBoost CAN | 0,2090 / 0,1190 | 0,5187 / 0,3523 | 0,2393 |
| CatBoost RAW | 0,2030 / 0,1167 | 0,3133 / 0,1906 | 0,2868 |
| Logística CAN | 0,2657 / 0,1763 | 0,5288 / 0,3984 | 0,3359 |
| Logística RAW | 0,3370 / 0,2119 | 0,4338 / 0,2914 | 0,2607 |
| MLP CAN | 0,3397 / 0,2512 | 0,5702 / 0,4652 | 0,4055 |
| MLP RAW | 0,3395 / 0,2199 | 0,4471 / 0,3074 | 0,3252 |

FPR não se aplica aos grupos somente maliciosos; F1 de ataque e recall não se
aplicam ao grupo somente benigno. Resultados por semente e todos os valores:
`3_2_srbh_sem_filtros/como_alvo/resultados_por_semente.csv` e
`metricas_grupos_removidos_por_semente.csv`.

### (b) SR-BH sem filtros como fonte

Após deduplicação canônica interna, a fonte SR-BH efetiva passou de 104.324
para 175.307 linhas em cada split. Foram removidas 3.277 duplicatas canônicas
internas; não houve sobreposição adicional com os alvos nem com as outras
fontes. O SR-BH permaneceu na mesma partição (treino ou validação) de cada
semente (`run_experimentos.py:469-517`).

Delta F1 (sem filtros como fonte menos artigo), por alvo:

| alvo | CB CAN | CB RAW | Log CAN | Log RAW | MLP CAN | MLP RAW |
|---|---:|---:|---:|---:|---:|---:|
| artificial_sqli | -0,054 | +0,043 | -0,029 | -0,054 | -0,010 | -0,029 |
| csic | +0,043 | -0,035 | +0,051 | +0,011 | -0,029 | -0,011 |
| ecml | -0,031 | +0,001 | -0,056 | +0,000 | -0,021 | +0,033 |
| proprio | -0,016 | +0,066 | -0,005 | +0,045 | +0,051 | -0,003 |
| site_cooking | +0,003 | -0,001 | +0,024 | -0,064 | -0,017 | -0,085 |
| site_sqli | +0,005 | -0,005 | +0,012 | -0,079 | -0,019 | -0,097 |

Macro entre os seis alvos:

| modelo/vista | F1 artigo | F1 com SR-BH sem filtros | delta |
|---|---:|---:|---:|
| CatBoost CAN | 0,9109 | 0,9027 | -0,0082 |
| CatBoost RAW | 0,7975 | 0,8092 | +0,0117 |
| Logística CAN | 0,8685 | 0,8681 | -0,0004 |
| Logística RAW | 0,7594 | 0,7357 | -0,0237 |
| MLP CAN | 0,8902 | 0,8828 | -0,0075 |
| MLP RAW | 0,8330 | 0,8011 | -0,0319 |

Detalhes: `3_2_srbh_sem_filtros/como_fonte/comparacao_por_alvo.csv`,
`comparacao_macro.csv`, `resultados_por_semente.csv` e
`auditoria_substituicao.csv`.

## 3.3 — Sensibilidade de hiperparâmetros

As seis configurações alternativas estão declaradas em
`run_experimentos.py:533-540`; a agregação está em `run_experimentos.py:543-601`.

| configuração | F1 RAW | F1 CAN | CAN - RAW | alvos com melhora CAN |
|---|---:|---:|---:|---:|
| Logística C=0,1 | 0,7434 | 0,8563 | +0,1129 | 7/7 |
| Logística C=10 | 0,7280 | 0,8556 | +0,1276 | 7/7 |
| CatBoost 100 / profundidade 4 | 0,7957 | 0,8801 | +0,0844 | 7/7 |
| CatBoost 400 / profundidade 6 | 0,7785 | 0,8899 | +0,1114 | 7/7 |
| MLP (32,) | 0,8285 | 0,8895 | +0,0611 | 6/7 |
| MLP (128,64) | 0,7901 | 0,8621 | +0,0720 | 7/7 |

Para referência, as configurações do artigo produziram: Logística 0,7330 RAW /
0,8441 CAN; CatBoost 0,7839 / 0,8936; MLP 0,8097 / 0,8670.

- Em RAW, a ordem permaneceu **MLP > CatBoost > Logística** no baseline e nos
  dois cenários alternativos.
- Em CAN, o baseline e o cenário de maior capacidade mantiveram
  **CatBoost > MLP > Logística**. No cenário de menor capacidade, houve mudança
  para **MLP (32,) > CatBoost (100/d4) > Logística (C=0,1)**, com F1 0,8895
  versus 0,8801.
- Não foi escolhida uma configuração “melhor” a partir do alvo.
- A lacuna ID–OOD não foi recalculada: uma comparação válida exigiria mais 420
  ajustes ID, além dos 420 LODO solicitados, e por isso não foi considerada
  barata. A decisão está registrada em `tempo_parede.json`.

Resultados: `3_3_sensibilidade_hiperparametros/resultados_por_semente.csv`,
`resultados_por_alvo.csv`, `f1_macro.csv`, `efeito_canonicalizacao.csv` e
`ordem_modelos.csv`.

## Pergunta extra — coincidências de esqueletos

Implementação e ressalva: `run_experimentos.py:604-698`. A análise compara
tokens estruturados canonicalizados (query, formulário, JSON e caminho), com
dígitos convertidos em zero, contra as fontes elegíveis do split LODO da
semente 42. Trata-se de igualdade de tokens estruturais, não de similaridade
semântica.

| alvo | fonte | requisições com algum token coincidente | fração |
|---|---|---:|---:|
| proprio | artificial_sqli | 29.989 / 37.232 | 80,546% |
| proprio | srbh | 29.990 / 37.232 | 80,549% |
| proprio | csic / ecml | 0 | 0% |
| proprio | site_cooking | 23 | 0,062% |
| proprio | site_sqli | 25 | 0,067% |
| artificial_sqli | proprio | 2.462 / 5.000 | 49,240% |
| artificial_sqli | srbh | 2.462 / 5.000 | 49,240% |
| artificial_sqli | csic / ecml | 0 | 0% |
| artificial_sqli | site_cooking | 3 | 0,060% |
| artificial_sqli | site_sqli | 4 | 0,080% |

O token dominante nos dois alvos foi `body:-=`: 29.989 requisições de
`proprio` e 2.462 de `artificial_sqli`, coincidente com `artificial_sqli`/SR-BH
e `proprio`/SR-BH, respectivamente. Ele é um marcador estrutural vazio
(placeholder/boilerplate), não um payload SQLi. Em `artificial_sqli`, os tokens
seguintes foram `query:offset=000` (22) e `query:offset=00` (6), também
boilerplate de paginação; os payloads (`admin'`, `pg_sleep`, `sleep`) ocorreram
somente uma ou duas vezes. Em `proprio`, os demais tokens do Top-10 têm no
máximo dez ocorrências e são majoritariamente formas vazias/de pontuação; o
único nome explícito adicional foi `body:comment=` (uma ocorrência).

Conclusão: os percentuais altos entre `proprio`, `artificial_sqli` e SR-BH são
dominados por placeholder estrutural, não por compartilhamento frequente de
payloads SQLi. Arquivos: `extra_esqueletos/coincidencias_por_fonte.csv`,
`tokens_coincidentes_todos.csv` e `top10_tokens_unicos_por_alvo.csv`. Para
`artificial_sqli` só existiram sete tokens únicos coincidentes; portanto não se
inventaram três itens para completar dez.

## Tempos de parede

| análise | segundos | minutos |
|---|---:|---:|
| 3.1 | 73,21 | 1,22 |
| 3.2 — preparação | 18,61 | 0,31 |
| 3.2(a) — como alvo | 42,10 | 0,70 |
| 3.2(b) — como fonte | 538,09 | 8,97 |
| **3.2 total** | **598,79** | **9,98** |
| 3.3 | 832,55 | 13,88 |
| pergunta extra | 12,51 | 0,21 |

Tempo total das três análises e da pergunta extra: aproximadamente 1.517,06 s
(25,28 min), sem contar as verificações finais e a consolidação dos CSVs.
Fonte: `tempos_parede.csv`.
