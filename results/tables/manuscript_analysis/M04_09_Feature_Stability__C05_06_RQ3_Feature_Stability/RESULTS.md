# Results — 5.6 / RQ3

Rankings CatBoost e estabilidade estão em `tables/feature_rankings_by_target.csv`, `stable_features.csv` e `feature_stability.csv`.

Alterações por remoção de fonte e sua coincidência com F1/MCC/recall/FPR estão em `tables/source_removal_feature_effects.csv`.

Ablações existentes são incluídas em `tables/feature_ablation_by_target.csv`. Dimensões dos embeddings não foram interpretadas como features semânticas.

CANONICALIZED: char_equals lidera por frequência Top-10 (1.000000), importância média 7.044073; `tables/stable_features.csv`, row_id 80409a145b8b015694bf. É estabilidade observada do ranking CatBoost, não invariância causal.

RAW: sql_comment_dash lidera por frequência Top-10 (1.000000), importância média 15.196501; `tables/stable_features.csv`, row_id e1bd6646c83296e33b4f. É estabilidade observada do ranking CatBoost, não invariância causal.

full_vs_removed/CANONICALIZED: média descritiva de Spearman=0.864649, Jaccard Top-10=0.722791; `tables/stability_overview.csv`, row_id b24855dae0b981e96bf0. A média de condições não é tratada como n de targets independentes.

full_vs_removed/RAW: média descritiva de Spearman=0.809984, Jaccard Top-10=0.658153; `tables/stability_overview.csv`, row_id be367e68ad162b445832. A média de condições não é tratada como n de targets independentes.

target_vs_target/CANONICALIZED: média descritiva de Spearman=0.820234, Jaccard Top-10=0.662290; `tables/stability_overview.csv`, row_id 72291a41fbaad64d9259. A média de condições não é tratada como n de targets independentes.

target_vs_target/RAW: média descritiva de Spearman=0.792028, Jaccard Top-10=0.582311; `tables/stability_overview.csv`, row_id 051f1be03d30922f24c1. A média de condições não é tratada como n de targets independentes.

Não foi detectada associação ajustada entre instabilidade e OOD F1, gap ou negative transfer nos estratos avaliados. Fonte: M04.11/statistics/cross_rq_relationships.csv, filtro relationship.startswith(feature_instability); p_Holm≥0.05. Não significa que as relações sejam inexistentes.

Ablações CANONICALIZED: maior melhora observada vs lex64 = 0.132225 (ecml/logistic/no_special_chars); maior queda = -0.247626 (csic/catboost/char_rates). `tables/ablation_effects_by_target.csv`, row_id 0c43cc829fa611b1327e e cee06f8f931fc60e666e. São extremos descritivos pós-teste, não seleção de features validada para deployment.

Ablações RAW: maior melhora observada vs lex64 = 0.166924 (ecml/logistic/no_special_chars); maior queda = -0.220080 (csic/logistic/char_rates). `tables/ablation_effects_by_target.csv`, row_id f649d0e94abc09b0dc4c e b1ceb88aac1b12dac5b9. São extremos descritivos pós-teste, não seleção de features validada para deployment.

## Interpretation and limitations

Somente importâncias CatBoost já existentes, lex64, LODO C e coalizões full/leave-one-source. Spearman/Kendall entre ranks médios, empates com average rank. Top-10 desempata por nome; Jaccard=interseção/união. Importância é model-specific e não causal; estável não implica invariância universal. RAW vs CANONICALIZED depende do pareamento auditado na fase RQ4.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Positive, Negative and Null Results

Todas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| derived/selected_feature_importances.parquet | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/derived/selected_feature_importances.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/feature_rankings_by_target.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_rankings_by_target.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, representation, feature); importance, rank summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/stable_features.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stable_features.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(representation, feature); importance, rank summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| derived/rank_pairs.parquet | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/derived/rank_pairs.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/feature_stability.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_stability.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(comparison, target_dataset, other_target, removed_source, representation); spearman, kendall, jaccard_topk, instability, delta_f1 summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/feature_rank_correlations.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_rank_correlations.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(comparison, target_dataset, other_target, removed_source, representation); spearman, kendall, jaccard_topk, instability, delta_f1 summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/jaccard_topk.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/jaccard_topk.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(comparison, target_dataset, other_target, removed_source, representation); spearman, kendall, jaccard_topk, instability, delta_f1 summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| derived/source_removal_feature_pairs.parquet | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/derived/source_removal_feature_pairs.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/source_removal_feature_effects.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/source_removal_feature_effects.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, removed_source, representation, feature); delta_importance, delta_rank, delta_f1, delta_mcc, delta_recall, delta_fpr, delta_threshold summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/feature_ablation_by_target.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_ablation_by_target.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, model, representation, feature_set); precision, recall, f1, mcc, pr_auc, roc_auc, balanced_accuracy, specificity, fpr, fnr, brier, ece_10 summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/stability_overview.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stability_overview.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | seeds within target-pair/source-removal condition first; descriptive average over these conditions | `artigo/scripts/analysis/final_analysis.py` |
| derived/ablation_pairs.parquet | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/derived/ablation_pairs.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/ablation_effects_by_target.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/ablation_effects_by_target.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, model, representation, feature_set); delta_f1, delta_mcc summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/raw_vs_canonicalized_stability_eligibility.csv | `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/raw_vs_canonicalized_stability_eligibility.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/SOURCE_FILES.parquet`. This mapping contains 1820 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 6037. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/TRACEABILITY.csv` lists all 16 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
