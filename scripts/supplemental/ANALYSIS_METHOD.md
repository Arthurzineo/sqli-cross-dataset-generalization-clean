# Protocolo complementar, separado dos experimentos históricos

Metodologia: M04.03, M04.06–M04.10 e M04.12. Resultados: C05.01 e C05.03–C05.09; RQ1–RQ4. Status: protocolo implementado, não resultado da nova bateria.

## Por que e o que analisar

A coleção controlada complementa a coleção histórica com comparações pareadas: as vistas RAW e CANONICALIZED derivam das mesmas linhas, o teste é comum às condições ID e OOD, e a validação permanece fixa quando uma fonte é removida.

## Coorte, vistas e isolamento

Usar exclusivamente as cópias RAW configuradas dos sete arquivos da bateria principal. Não incluir `artificial` adicionalmente: a lista explícita está em `config.json`; não se presume independência por nome. A política de famílias existente exclui tanto o próprio alvo como a outra fonte `site_lab` ao avaliar `site_cooking` ou `site_sqli`.

IDs pareados são SHA-256 de dataset, hash do arquivo original e número da linha. As duas vistas preservam IDs, rótulos e ordem. RAW é a entrada RAW após o loader existente, não bytes intocados do CSV. CANONICALIZED é derivada diretamente dessa mesma linha: `decode_until_stable`, com `unquote_plus` recursivo até dez passagens, aplicado a text, URL e body. Isso também altera features que consultam URL/body. Não usa os arquivos decoded históricos. `casefold` e normalização de whitespace pertencem à chave canônica de isolamento; não são uma nova transformação universal das entradas. Consultar `src/data/loader.py` e `src/features/lexical.py` para os detalhes realmente executados.

As 64 features lexicais existentes são reutilizadas sem metadados como features. CatBoost, regressão logística e MLP compacta (64,32) são as mesmas famílias/implementações disponíveis em `src/models/classical.py`. A MLP é tabular; não é Transformer nem stacking. Embeddings estão fora deste complemento inicial; não alegar que o teste novo corrige o pareamento histórico dos encoders.

No LODO, purgar treino/validação contra todos os hashes canônicos do arquivo-alvo. Preservar o alvo inteiro com seus rótulos, inclusive eventuais conflitos. Remover conflitos de rótulos no desenvolvimento e deduplicar deterministicamente, ordenando por dataset/linha. Reservar uma família fonte para validação quando viável; caso contrário, usar grupos canônicos. Nenhuma estatística ajustada, seleção de modelo, early stopping ou threshold utiliza o alvo. Escolha da família é determinada pela seed e viabilidade de classes nas fontes, não pelo desempenho OOD.

Para o gap ID/OOD, reservar aproximadamente 20% dos grupos canônicos do alvo antes dos fits ID. Treinar ID no restante, com validação interna; o LODO continua treinado exclusivamente nas fontes externas. Avaliar ambos no mesmo conjunto de IDs do holdout. O LODO também salva métricas no alvo completo, separadas por nome. Esses scores full-target não substituem o score common-test ao calcular o gap. Se ID é inviável, registrar o motivo sem descartar um LODO viável. Métricas não interpretáveis em classe única são nulas; não criar exemplos sintéticos para completar classes.

## Seleção, scores e contribuição

Imputação mediana e scaler ajustados só no treino de cada fit. Hiperparâmetros pequenos e fixos; early stopping existente para CatBoost/MLP usando apenas validação. Salvar scores da validação, threshold escolhido, iterações selecionadas e scores do teste. A trajetória completa de épocas não é reconstruída. Não existe busca nested de hiperparâmetros nesta bateria.

Threshold maximiza F1 na validação, avaliando scores únicos mais 0 e 1; predição positiva se score ≥ threshold; empate favorece o menor threshold. Busca exata ordenada, sem matriz quadrática. PR-AUC usa average precision da implementação existente, não área trapezoidal. Oracle de teste é calculado só depois do modelo e decisão source estarem congelados, explicitamente diagnóstico; não altera o detector. Brier/ECE são diagnósticos das probabilidades emitidas, não prova de calibração nem ajuste de um calibrador.

Na contribuição, conservar exatamente os IDs de validação e teste do full LODO. Remover uma fonte apenas do treino; não repor duplicatas que anteriormente pertenciam a outra fonte. Só são removíveis arquivos realmente presentes no treino, não a família reservada para validação. Essa restrição é deliberada: a cobertura por fonte depende da seed e da viabilidade. Uma remoção inviável é registrada, não imputada. Early stopping e threshold podem mudar com o modelo, porém os exemplos usados para selecionar permanecem iguais. Comparação full-minus-removed não é causal em sentido populacional e inclui redução do tamanho do treino.

## Separabilidade controlada

Label do classificador é origem do dataset, nunca label do detector de ataque. Remover todas as ocorrências de hashes presentes em mais de uma origem, conflitos de rótulos e duplicatas canônicas. Três condições: ambas as classes igualmente representadas; apenas benignos; apenas ataques. Para cada condição usar o menor tamanho disponível de qualquer origem/classe, limitado explicitamente a 2.500 por origem/classe. Mesma quantidade inteira por origem/classe tanto no treino quanto no teste, mesmas linhas nas duas vistas e cinco seeds. Se uma classe necessária faltar em qualquer origem, registrar condição inviável; não excluir silenciosamente aquela origem.

Usar regressão logística multiclasse com configuração fixa. Reportar macro-F1, accuracy e confusão. Chance uniforme de accuracy = 1/K; 1/K para macro-F1 é referência assintótica sob equilíbrio, não F1 exato garantido para uma amostra finita. Agrupar seeds dentro da condição/vista; não tratar cinco seeds como cinco novos datasets.

## Recálculos sem treinamento

Shapley: filtrar `usable` e `experiment_type == contribution` na master. Agrupar por target/model/representation/feature_set/seed, usando coalizões efetivas após exclusão de família. Coalizões solicitadas diferentes mas efetivamente iguais só colapsam quando suas métricas concordam até 1e-10; discordância interrompe a análise. Exigir todas as coalizões não vazias, sem preencher lacunas. F1/MCC/AP/recall/FPR/FNR são analisados separadamente.

Definir explicitamente o valor da coalizão vazia por um preditor analítico independente de fontes: p=0,5 e threshold=0,5, portanto todos positivos. Se prevalência do alvo é π: F1=2π/(1+π), MCC=0, AP=π, recall=1, FPR=1, FNR=0 (somente quando interpretáveis). Essa referência não é um treinamento ausente registrado. Ela define um novo jogo e afeta a atribuição absoluta. Não afirmar que é o único baseline possível.

φᵢ = Σ[S⊆N\{i}] |S|!(|N|−|S|−1)!/|N|! × [v(S∪{i})−v(S)]. Verificar Σφᵢ = v(N)−v(∅). Para FPR/FNR, `benefit_shapley = -shapley`. Não agregar seeds nessa tabela. A função de utilidade histórica continua incluindo mudança de validação entre coalizões: os pesos corretos não removem esse confundimento.

Auditoria de splits: ler apenas colunas canonical_hash/split/dataset em chunks de 25.000 linhas, um manifest por vez. Comparar interseções treino/validação/teste, presença do alvo no desenvolvimento OOD e contagens com métricas salvas. Cada arquivo tem resultado atômico e hash; retomada considera caminho/tamanho/mtime. `--limit` limita novos manifests por chamada. Não alegar auditoria completa enquanto `full_audit_complete` for falso. Esse teste verifica manifests, não prova sozinho quais arrays um processo histórico usou em cada operação interna.

## Consolidação

Parear por condição, alvo, modelo, seed, configuração e contexto de código/cache. RAW/CANONICALIZED exigem mesmo split_id. Gap ID/OOD exige igualdade dos IDs de teste comuns; contribuição exige igualdade dos IDs de validação e teste. Deltas de canonicalização = CANONICALIZED − RAW; gap = ID − OOD; contribuição = full − removed (higher-is-better). Tabelas conservam IDs dos dois runs e resumos fazem média/desvio entre seeds dentro de cada condição/alvo. Sem testes inferenciais automáticos nesta consolidação; a etapa estatística futura deve usar targets, não seeds, como unidades.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| RAW/CANONICALIZED delta | analysis/raw_vs_canonicalized_pairs.parquet | analysis/SOURCE_LINEAGE.parquet | context + condition + same split | paired CAN−RAW per seed | consolidate.py |
| Common-test gap F1 | analysis/id_vs_ood_same_test.parquet | analysis/SOURCE_LINEAGE.parquet | ID/LODO + same evaluated IDs | ID−OOD per seed | consolidate.py |
| Fixed-validation contribution | analysis/fixed_validation_contribution.parquet | analysis/SOURCE_LINEAGE.parquet | full/removed + same val/test | full−removed per seed | consolidate.py |
| Origin macro-F1 | analysis/master_results.parquet | runs/SUPP_*/metrics.json; predictions.parquet | kind=separability; condition; representation | per run, no seed pooling | run.py |
| Exact declared-game Shapley | existing_analysis/exact_shapley.parquet; shapley_games.parquet | existing_analysis/SOURCE_FILES.parquet | usable contribution; complete effective coalitions | factorial weighted, per seed | existing_analysis.py |
| Hash audit | existing_analysis/split_audit/EXP_*.json | input_identity.file in each JSON | usable runs; optional limit | unique hash intersections per split | existing_analysis.py |

## Data Sources and Traceability

Supporting original code: `artigo/src/data/loader.py`, `src/data/splits.py`, `src/features/lexical.py`, `src/models/classical.py`, `src/evaluation/metrics.py`; paths relative to `artigo` unless prefixed. This document specifies a protocol, not unseen observations. Config input: one `artigo/scripts/supplemental/config.json`; source dataset files are resolved and hashed when prepare is invoked. Their actual count/paths, columns and changed-row counts are in `cache/*/READY.json`, `cohort.parquet`, `input_audit.parquet`. Sample identity includes source file hash and row number. Output base: `artigo/complementos_generalizacao_v1/`, separate full and explicit pilot directories.

Commands and stages: README.md, using `python artigo/scripts/supplemental/run.py --stage paired|separability|contribution`, then `python artigo/scripts/supplemental/consolidate.py`. Every future run saves complete config, code hashes, original source cache identity, split path/hash, software versions, hardware, seeds, hyperparameters and artifacts under `runs/SUPP_*/`. Git commit can be null outside a Git repository; code hashes remain available. `analysis/SOURCE_LINEAGE.parquet` links each experiment to original outputs; analytic rows carry row_id and experiment_ids. Formulas, seed handling, exclusions and filters are defined above. Tables generated are master_results, raw_vs_canonicalized_pairs, id_vs_ood_same_test, fixed_validation_contribution and their seed summaries. No figures generated here.

No-training commands: `python artigo/scripts/supplemental/existing_analysis.py --stage shapley` and `--stage audit-splits [--limit N]`. Shapley reads two analytical inputs: `artigo/analise_resultados_tcc/_global/master_results.parquet` and `SOURCE_LINEAGE.parquet`. `existing_analysis/EXECUTION.json` records their hashes, IDs count and command; `SOURCE_FILES.parquet` contains complete original-file mapping (relative paths rooted at GENERALIZACAO). `exact_shapley.parquet` links via game_id to `shapley_games.parquet`, including all contributing experiment_ids. Outputs also include `shapley_nonapplicable.parquet` and `SHAPLEY_AUDIT.json`. The split audit logs each original file read individually and the audited count in SUMMARY.json; it never reads model checkpoints. Synthetic test provenance and command: `artigo/complementos_generalizacao_v1/VALIDATION.json`; no scientific experiment_ids belong to those fabricated examples.
