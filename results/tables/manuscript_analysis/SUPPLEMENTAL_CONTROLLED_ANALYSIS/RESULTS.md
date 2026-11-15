# Análise científica complementar — controles pareados

Escopo: novos experimentos lexicais controlados, separados do histórico. Nenhum treinamento foi executado por esta análise.

## 5.1 Cobertura e integridade

Foram analisados 1434 runs não piloto: contribution_fixed_validation=984, id=210, lodo=210, separability=30. Fonte: `tables/coverage.csv` e `SOURCE_FILES.parquet`.
A auditoria histórica terminou para todos os manifests previstos, sem inconsistências nos controles de hash, origem do alvo e contagens. Isso não prova o comportamento de cada operação interna histórica. Fonte original: `../../complementos_generalizacao_v1/existing_analysis/split_audit/SUMMARY.json` (caminho absoluto em `FILES_READ.csv`).

## 5.2 Representações e modelos

As duas vistas vêm das mesmas linhas RAW, não dos arquivos decoded históricos. A canonicalização atua também em URL/body e pode alterar enc_pct/path_depth. Esta é uma nova condição experimental; não juntar suas médias às antigas. CatBoost, logística e MLP tabular usam 64 features lexicais; não há embeddings nesta bateria. Fontes: `tables/paired_dataset_characterization.csv`, `SOURCE_FILES.parquet` e protocolo `artigo/scripts/supplemental/ANALYSIS_METHOD.md`.

## 5.3 RQ1 — generalização para alvos não vistos

O resultado principal por alvo/modelo/vista está em `tables/lodo_by_target.csv` (todas as seeds em `tables/lodo_per_run.csv`). O gap usa somente o teste comum ID/OOD, não mistura o holdout ID com o alvo inteiro. Fonte: `tables/id_ood_same_test.csv`.

| Modelo | Vista | Gap F1 médio entre alvos (ID−OOD) |
|---|---|---:|
| catboost | CANONICALIZED | 0.1008 |
| catboost | RAW | 0.2073 |
| logistic | CANONICALIZED | 0.1467 |
| logistic | RAW | 0.2469 |
| mlp | CANONICALIZED | 0.1264 |
| mlp | RAW | 0.1776 |

Esses gaps são médias não ponderadas de alvos, após resumir seeds; fonte: `tables/generalization_gap_macro.csv`. A tabela por alvo preserva as falhas locais. PR-AUC significa average precision. Desempenho OOD não estabelece transferência universal nem independência de fontes.

## 5.4 RQ2 — contribuição e transferência negativa

Há 111 condições alvo/fonte/modelo/vista com contribuição média negativa e 129 positiva; não são 111 alvos independentes. Zero usa tolerância 1e-9. Fontes: `tables/negative_transfer.csv`, `tables/positive_transfer.csv`, `tables/source_contribution_by_target.csv`.
Um caso extremo é target=srbh, source=proprio, model=logistic, view=RAW: full−removed F1=-0.1671, em 5 seeds elegíveis. Fonte: `tables/negative_transfer.csv`, row_id `ffc4fb749bef5a4bddc6bd02`.
Mais fontes não ajudam sempre. Validação e teste ficam fixos, mas tamanho do treino, early stopping e threshold resultante podem variar. A fonte reservada para validação não é removível; n_seeds varia por fonte. Médias por fonte dão peso igual aos alvos elegíveis, não às seeds disponíveis. Fonte: `tables/source_summary.csv`.

## 5.5 RQ3 — scores e thresholds

Separar discriminação (AP/ROC-AUC), decisão operacional (F1/FPR/FNR) e diagnóstico oracle. `tables/decision_by_target.csv` contém drift, oracle gap, Brier/ECE e métricas source. Um oracle alto não autoriza usar o alvo para escolher threshold.
Casos de análise de erro foram selecionados automaticamente por extremos/média representativa: `selected_runs/cases.csv`. Scores só foram abertos para esses IDs. `tables/error_examples.csv` e `tables/error_transitions.csv` preservam sample_id, caminho e critério. Não se inferem causas sem olhar o conteúdo das entradas.

Exemplo diagnóstico: proprio/catboost/RAW tem AP=0.8964, F1 source=0.7215 e F1 oracle=0.9341. Isso sugere margem de recuperação por threshold nesta condição, não garante que ela possa ser escolhida sem acesso ao alvo. Fonte: `tables/decision_by_target.csv`, row_id `eebb8b765ebe47c86aabaec2`.

## 5.6 RQ3 — estabilidade de features

As importâncias são nativas do CatBoost, normalizadas em percentual; não são SHAP nem prova causal. `tables/stable_features.csv` resume primeiro seeds e depois alvos. `derived/feature_rank_pairs.csv` preserva Spearman/Kendall/Jaccard por comparação, incluindo empates. Não são dimensões de embeddings.

RAW: maiores importâncias médias: sql_comment_dash (15.32%), char_rparen (12.82%), char_plus (10.54%), enc_pct (6.99%), ratio_nonalnum (6.98%). Fonte: `tables/stable_features.csv`, filtro representation=RAW.
CANONICALIZED: maiores importâncias médias: char_space (14.05%), char_rparen (11.52%), sql_comment_dash (9.29%), ratio_nonalnum (8.24%), sql_select (7.93%). Fonte: `tables/stable_features.csv`, filtro representation=CANONICALIZED.
Estabilidade cross_target: Spearman médio RAW=0.7800, CANONICALIZED=0.8289. Fonte: `tables/feature_stability.csv`. São comparações dependentes e descritivas; pares site_cooking/site_sqli podem compartilhar pools efetivos, não são origens independentes.
Estabilidade source_removal: Spearman médio RAW=0.8114, CANONICALIZED=0.8628. Fonte: `tables/feature_stability.csv`. São comparações dependentes e descritivas; pares site_cooking/site_sqli podem compartilhar pools efetivos, não são origens independentes.

Alterações full/removed estão em `tables/source_removal_feature_effects.csv`. Dependência de composição é uma interpretação possível, não equivalência entre importância e capacidade transferível.

## 5.7 RQ4 — canonicalização e separabilidade

| Modelo | Alvos com ganho | Empate | Piora |
|---|---:|---:|---:|
| catboost | 7 | 0 | 0 |
| logistic | 7 | 0 | 0 |
| mlp | 6 | 0 | 1 |

Fonte: `tables/canonicalization_win_tie_loss.csv`; sinal do delta médio das seeds de cada alvo, tolerância 1e-9.
Maior ganho médio: proprio/catboost, ΔF1=+0.2586; menor efeito: proprio/mlp, ΔF1=-0.0146. Fonte: `tables/canonicalization_by_target.csv`, row_ids `d9611cb7a3c35c7380d45ba8` e `99b0854429713f3e2eda1232`.

| Condição origem | RAW macro-F1 | CANONICALIZED macro-F1 |
|---|---:|---:|
| all | 0.8504 | 0.8255 |
| benign | 0.8493 | 0.8439 |
| malicious | 0.8797 | 0.8542 |

Fonte: `tables/separability.csv`; médias de seeds. Menor separabilidade não significa invariância: a origem permanece previsível. `tables/separability_controls.csv` registra tamanhos iguais, composição e purge. Não usar seeds de reamostragens sobrepostas como novos domínios independentes. Relações com OOD estão em `tables/separability_vs_generalization.csv` e são apenas exploratórias.

## 5.8 Síntese estatística

Unidade das comparações: alvo após agregação das seeds. Wilcoxon para duas condições, Friedman para modelos, Spearman para associações; Holm dentro das famílias indicadas. Fontes: `statistics/tests_holm.csv`. Com sete alvos e fontes compartilhadas entre as composições, os testes têm poder limitado; site_cooking e site_sqli pertencem à mesma família. Não interpretar p>0,05 como equivalência.

Comparação CAN-RAW catboost: p bruto=0.015625, p Holm=0.046875, 7 alvos. Resultado exploratório sensível à dependência e ao pequeno conjunto de fontes; não confirmação populacional. Fonte: `statistics/tests_holm.csv`, row_id `03f5993f18290420774b3296`.
Comparação CAN-RAW logistic: p bruto=0.015625, p Holm=0.046875, 7 alvos. Resultado exploratório sensível à dependência e ao pequeno conjunto de fontes; não confirmação populacional. Fonte: `statistics/tests_holm.csv`, row_id `58197d4c9338a9466a047cfb`.
Comparação CAN-RAW mlp: p bruto=0.046875, p Holm=0.046875, 7 alvos. Resultado exploratório sensível à dependência e ao pequeno conjunto de fontes; não confirmação populacional. Fonte: `statistics/tests_holm.csv`, row_id `17bdb2b440e00672a6f133b7`.
Comparações entre modelos após omnibus significativo estão em `statistics/model_posthoc.csv`; não interpretar Friedman sozinho como vitória de um modelo específico.

Sensibilidade agrupando arquivos de alvos relacionados pela família de origem: catboost, 6 famílias, p Holm=0.09375. Fonte: `statistics/canonicalization_family_sensitivity.csv`, row_id `e58a25e048f31b73a7217f55`. Essa análise não altera os testes por arquivo e mostra a sensibilidade da inferência à unidade considerada independente.
Sensibilidade agrupando arquivos de alvos relacionados pela família de origem: logistic, 6 famílias, p Holm=0.09375. Fonte: `statistics/canonicalization_family_sensitivity.csv`, row_id `1779a9a3df6a7d10f4f93adc`. Essa análise não altera os testes por arquivo e mostra a sensibilidade da inferência à unidade considerada independente.
Sensibilidade agrupando arquivos de alvos relacionados pela família de origem: mlp, 6 famílias, p Holm=0.09375. Fonte: `statistics/canonicalization_family_sensitivity.csv`, row_id `7b7c3b6114f1375c2f167772`. Essa análise não altera os testes por arquivo e mostra a sensibilidade da inferência à unidade considerada independente.
## Negative and Null Findings

A piora de canonicalização e todos os casos de transferência negativa estão preservados nas tabelas. Testes sem diferença detectável constam com p_holm e razão em `statistics/tests_holm.csv`; teste não aplicável por poucos alvos não é resultado nulo. Não executar teste de significância da separabilidade usando suas seeds como datasets independentes.

Família source_contribution: 42 de 42 testes aplicáveis não passaram o limiar exploratório de 0,05 após Holm; 0 não aplicáveis. Fonte: `statistics/tests_holm.csv`, filtro family=source_contribution. Isso não apaga os efeitos descritivos nem demonstra ausência de efeito.
Família cross_rq_associations: 22 de 22 testes aplicáveis não passaram o limiar exploratório de 0,05 após Holm; 0 não aplicáveis. Fonte: `statistics/tests_holm.csv`, filtro family=cross_rq_associations. Isso não apaga os efeitos descritivos nem demonstra ausência de efeito.
Família id_ood_gap: 6 de 6 testes aplicáveis não passaram o limiar exploratório de 0,05 após Holm; 0 não aplicáveis. Fonte: `statistics/tests_holm.csv`, filtro family=id_ood_gap. Isso não apaga os efeitos descritivos nem demonstra ausência de efeito.
OracleGap contém −F1_source por definição; sua associação com F1 pode ter acoplamento matemático. Correlações entre esses valores não são mecanismo causal.

## 5.9 Reprodutibilidade

Células aleatórias das tabelas finais foram reconstruídas diretamente de métricas originais; runs selecionados também foram recalculados das predictions. Fonte: `tables/reproducibility_audit.csv`. Recursos por fit: `tables/runtime_summary.csv`; tempo somado dos workers não é tempo de parede. Todas as tabelas têm row_id e experiment_ids. Figuras têm arquivo-fonte em `TRACEABILITY.csv`.

## Limitações e conclusões que não são justificadas

Não concluir generalização universal, ausência de quase-duplicatas semânticas, causalidade, melhoria garantida ao decodificar, equivalência entre origens ou validade dos encoders a partir desta bateria lexical. Não usar o novo Shapley como se a referência vazia fosse recuperada de um treinamento ausente. O recálculo Shapley está separado em `artigo/complementos_generalizacao_v1/existing_analysis/` e depende da referência declarada; não mede o mesmo protocolo de validação fixa desta análise. Não misturar resultados pairwise/ID/LODO ou antigos decoded/novos CANONICALIZED.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| LODO F1/MCC/AP | tables/lodo_by_target.csv | SOURCE_FILES.parquet | kind=lodo, pilot=0 | seeds inside target/model/view | analyze_supplemental_results.py |
| ID/OOD gap | tables/id_ood_same_test.csv | SOURCE_FILES.parquet | identical common-test IDs | ID−OOD per seed then seed summary | analyze_supplemental_results.py |
| Source contribution | tables/source_contribution_by_target.csv | SOURCE_FILES.parquet | frozen validation/test | full−removed then eligible seeds | analyze_supplemental_results.py |
| Canonicalization | tables/canonicalization_by_target.csv | SOURCE_FILES.parquet | identical RAW/CAN splits | CAN−RAW then seeds | analyze_supplemental_results.py |
| Separability | tables/separability.csv | SOURCE_FILES.parquet | balanced origins/classes | seed descriptive summaries | analyze_supplemental_results.py |
| Features | tables/stable_features.csv | SOURCE_FILES.parquet, feature_file | lexical CatBoost LODO | seeds then equally weighted targets | analyze_supplemental_results.py |
| Threshold/score behavior | tables/decision_by_target.csv; selected_runs/cases.csv | SOURCE_FILES.parquet | source-threshold LODO; oracle diagnostic | seeds inside target | analyze_supplemental_results.py |
| Statistical tests | statistics/tests_holm.csv | SOURCE_FILES.parquet | target-level seed means | two-sided, Holm per family | analyze_supplemental_results.py |
| Reproducibility | tables/reproducibility_audit.csv | original_source_files / source_prediction_file in table | seed2026 selected cells and diagnostic runs | reconstruct originals, tolerance1e-12 | analyze_supplemental_results.py |

## Data Sources and Traceability

Original-file mapping: `SOURCE_FILES.parquet`, one row per supplemental experiment_id; all eligible IDs are included. Primary analytical inputs: `<PROJECT_ROOT>/artigo/complementos_generalizacao_v1/full/analysis/master_results.parquet`, `SOURCE_LINEAGE.parquet`, `raw_vs_canonicalized_pairs.parquet`, `id_vs_ood_same_test.parquet`, `fixed_validation_contribution.parquet`. Globs for underlying artifacts: `<PROJECT_ROOT>/artigo/complementos_generalizacao_v1/full/runs/SUPP_*/metrics.json`, `feature_importance.parquet`, `predictions.parquet`; these are not all opened indiscriminately. Selected prediction IDs/criteria: `selected_runs/cases.csv`. Exact unique files read, counts by extension, projected columns, hashes and sizes: `FILES_READ.csv`, `ANALYSIS_AUDIT.json`. No checkpoint contents read, no training, no raw payload reads. Historical audit uses only `<PROJECT_ROOT>/artigo/complementos_generalizacao_v1/existing_analysis/split_audit/SUMMARY.json`; individual historical results remain separate.

Filters: completed consolidated runs, pilot_cap=0, one execution context, unique IDs; specific kind/target/model/view/source filters and formulas in `TRACEABILITY.csv` and `ANALYSIS_METHOD.md`. All scientific table rows contain row_id and experiment_ids. Seeds are summarized inside target/condition, never independent targets; absent comparisons remain absent. `TRACEABILITY.csv` records source columns, grouping/formula, command, figure source table, and each derived artifact. Original arrays for controlled cohorts remain in cache paths referenced by metrics.json; `tables/paired_dataset_characterization.csv` links dataset hashes. All tables: `tables/`, per-seed intermediates: `derived/`, statistics: `statistics/`, figures PNG/PDF: `figures/`. Figure/table relationships are explicit in TRACEABILITY.csv.

Script: `<PROJECT_ROOT>/artigo/scripts/analyze_supplemental_results.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analyze_supplemental_results.py`. Code hash, run counts, actual file counts, generation timestamp, runtime, peak RAM and reproducibility checks: `ANALYSIS_AUDIT.json`. Complete cell-to-source reconstruction example: table row → experiment_ids → SOURCE_FILES.parquet metric_file → original metrics.json. Random reconstructed values are in `tables/reproducibility_audit.csv`. This report keeps the historical protocol and new RAW-derived paired protocol separate.
