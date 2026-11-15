# Results — 5.4 / RQ2

A contribuição principal usa pool completo menos uma fonte com mesmo target/modelo/representação/seed (`tables/source_contribution_full.csv`).

Os casos de negative transfer estão em `tables/negative_transfer.csv`; efeitos positivos e nulos também são preservados. Fontes removidas automaticamente pelo filtro de família ficam em `tables/family_filtered_noops.csv`.

O arquivo legado dataset_shapley.csv não é utilizado como estimativa Shapley clássica.

Há 111 condições com contribuição F1 negativa, 129 positiva e 0 neutra após média das seeds (`tables/negative_transfer.csv`, `positive_transfer.csv`, `neutral_transfer.csv`; contagem de linhas). Portanto mais fontes não ajudaram sempre. Maior caso negativo: proprio→srbh, logistic/RAW: F1 full=0.577788, sem fonte=0.741797, contribuição=-0.164008; row_id 8af155769200c509eb5e de `negative_transfer.csv`.

CANONICALIZED: maior contribuição média descritiva entre modelos/targets é artificial_sqli (0.055983); menor é site_sqli (-0.010699). `tables/source_overall_summary.csv`, row_id 523c8f05df36686d5c71 e 24fb56d0a7eba51399f4. Os contadores targets_helped/harmed em `source_summary.csv` mostram exceções; média positiva não implica ajuda consistente.

RAW: maior contribuição média descritiva entre modelos/targets é srbh (0.052204); menor é proprio (-0.050563). `tables/source_overall_summary.csv`, row_id 7307a099cef5da8f3e8b e 0e82bb04c13f09477a38. Os contadores targets_helped/harmed em `source_summary.csv` mostram exceções; média positiva não implica ajuda consistente.

## Interpretation and limitations

C_i=M(full)−M(without_i); positivo indica contribuição para F1/MCC/AP/recall. Para FPR/FNR benefit=erro(without)−erro(full). Seeds pareadas primeiro; médias e desvios dentro da condição. Alteração de validação é registrada por par. Não interpretar o efeito como causalidade.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Positive, Negative and Null Results

Todas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| derived/full_vs_removed.parquet | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/derived/full_vs_removed.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/source_contribution_full.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_contribution_full.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, removed_source, model, representation, feature_set, source_removed_was_effective); delta_precision, delta_recall, delta_f1, delta_mcc, delta_pr_auc, delta_roc_auc, delta_balanced_accuracy, delta_specificity, delta_fpr, delta_fnr, delta_brier, delta_ece_10, full_f1, full_mcc, full_pr_auc, removed_f1, removed_mcc, removed_pr_auc, threshold_delta, benefit_fpr, benefit_fnr summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/source_target_matrix_f1.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_target_matrix_f1.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | seed means, then equal model/representation weights; family-filtered no-ops excluded | `artigo/scripts/analysis/final_analysis.py` |
| tables/source_target_matrix_mcc.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_target_matrix_mcc.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | seed means, then equal model/representation weights; family-filtered no-ops excluded | `artigo/scripts/analysis/final_analysis.py` |
| tables/source_summary.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_summary.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/target_summary.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/target_summary.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/negative_transfer.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/negative_transfer.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, removed_source, model, representation, feature_set, source_removed_was_effective); delta_precision, delta_recall, delta_f1, delta_mcc, delta_pr_auc, delta_roc_auc, delta_balanced_accuracy, delta_specificity, delta_fpr, delta_fnr, delta_brier, delta_ece_10, full_f1, full_mcc, full_pr_auc, removed_f1, removed_mcc, removed_pr_auc, threshold_delta, benefit_fpr, benefit_fnr summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/positive_transfer.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/positive_transfer.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, removed_source, model, representation, feature_set, source_removed_was_effective); delta_precision, delta_recall, delta_f1, delta_mcc, delta_pr_auc, delta_roc_auc, delta_balanced_accuracy, delta_specificity, delta_fpr, delta_fnr, delta_brier, delta_ece_10, full_f1, full_mcc, full_pr_auc, removed_f1, removed_mcc, removed_pr_auc, threshold_delta, benefit_fpr, benefit_fnr summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/neutral_transfer.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/neutral_transfer.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, removed_source, model, representation, feature_set, source_removed_was_effective); delta_precision, delta_recall, delta_f1, delta_mcc, delta_pr_auc, delta_roc_auc, delta_balanced_accuracy, delta_specificity, delta_fpr, delta_fnr, delta_brier, delta_ece_10, full_f1, full_mcc, full_pr_auc, removed_f1, removed_mcc, removed_pr_auc, threshold_delta, benefit_fpr, benefit_fnr summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/family_filtered_noops.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/family_filtered_noops.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, removed_source, model, representation, feature_set, source_removed_was_effective); delta_precision, delta_recall, delta_f1, delta_mcc, delta_pr_auc, delta_roc_auc, delta_balanced_accuracy, delta_specificity, delta_fpr, delta_fnr, delta_brier, delta_ece_10, full_f1, full_mcc, full_pr_auc, removed_f1, removed_mcc, removed_pr_auc, threshold_delta, benefit_fpr, benefit_fnr summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/per_effective_source_pool.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/per_effective_source_pool.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | equal seeds; duplicate requested coalitions with identical effective pools included explicitly; deterministic duplicate results checked separately | `artigo/scripts/analysis/final_analysis.py` |
| tables/source_overall_summary.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_overall_summary.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | first seeds within condition, then equal targets in each model, then equal model weighting; not independence of all coalitions | `artigo/scripts/analysis/final_analysis.py` |
| tables/effective_pool_duplicates.csv | `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/effective_pool_duplicates.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/SOURCE_FILES.parquet`. This mapping contains 13170 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 40099. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/TRACEABILITY.csv` lists all 15 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
