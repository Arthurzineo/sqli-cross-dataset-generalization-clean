# Results — 5.5 / RQ3

Threshold drift e oracle gap estão separados em `tables/threshold_drift.csv` e `tables/oracle_gap.csv`; oracle é diagnóstico pós-teste.

Brier e ECE-10 já estavam nos arquivos de métricas e foram reutilizados (`tables/calibration_results.csv`). Não houve treinamento de calibrador.

Scores são inspecionados somente nos casos selecionados (`selected_runs/threshold_cases.csv`). Scores de validação/source não foram salvos; comparação source vs target não é reconstruída.

Maior oracle gap LODO C = 0.405255, em proprio/catboost/RAW, seed 123. F1 com threshold de origem=0.529767; F1 oracle diagnóstico=0.935021; AP=0.887015. `tables/threshold_results.csv`, row_id e8f6dbc2bdb16152927b. Isso mostra margem diagnóstica de decisão para o ranking existente; não demonstra que retuning no target seria permitido.

## Interpretation and limitations

Drift=abs(t_source−t_oracle); oracle gap=F1_oracle−F1_source. ECE usa 10 intervalos uniformes [0,1]; Brier=mean((p−y)^2). Probabilidades não são assumidas calibradas. Mudança ID/OOD inclui populações de teste diferentes. Associações usam seeds resumidas e targets como unidades.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Positive, Negative and Null Results

Todas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| tables/threshold_results.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_results.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/threshold_drift.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_drift.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(experiment_type, target_dataset, training_datasets, model, representation, feature_set); threshold_drift, threshold_source, threshold_oracle summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/oracle_gap.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/oracle_gap.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(experiment_type, target_dataset, training_datasets, model, representation, feature_set); oracle_gap, f1, f1_oracle, pr_auc summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/calibration_results.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/calibration_results.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(experiment_type, target_dataset, training_datasets, model, representation, feature_set); brier, ece_10, f1, fpr, fnr summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| selected_runs/threshold_cases.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/selected_runs/threshold_cases.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| derived/calibration_pairs.parquet | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/derived/calibration_pairs.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/calibration_id_vs_ood.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/calibration_id_vs_ood.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(target_dataset, model, representation); delta_brier, delta_ece, ood_f1 summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| derived/selected_score_distributions.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/derived/selected_score_distributions.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| derived/selected_reliability_bins.csv | `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/derived/selected_reliability_bins.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/SOURCE_FILES.parquet`. This mapping contains 16650 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 50721. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/TRACEABILITY.csv` lists all 11 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
