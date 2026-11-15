# Analysis Method — 4.1 / 5.1

Grade esperada reconstruída dos scripts de execução, cenários, seis ablações efetivamente solicitadas e cinco seeds. Métricas exigem status COMPLETED, pilot=0 e campos válidos. Falhas não são substituídas por zeros. RQs se sobrepõem; suas contagens não devem ser somadas.

O que/por quê: Cobertura experimental, para All. Foram usados os arquivos e IDs mapeados em SOURCE_FILES.parquet; pilotos/falhas/não aplicáveis em M04.01/tables/excluded_runs.csv. Não se imputam métricas ausentes. Os dados não foram usados para escolher novamente modelos ou thresholds. Artefatos por linha permitem recuperar os filtros exatos e seeds.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| tables/coverage_matrix.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/coverage_matrix.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/missing_runs.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/missing_runs.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/excluded_runs.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/excluded_runs.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/run_counts.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_counts.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | count of IDs matching category; previsto is enumeration of design coverage including SKIPPED | `artigo/scripts/analysis/final_analysis.py` |
| tables/run_coverage_by_type.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_type.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/run_coverage_by_target.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_target.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/run_coverage_by_model.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_model.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/run_coverage_by_representation.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_representation.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/run_coverage_by_source_composition.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_source_composition.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/run_coverage_by_seed.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_seed.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/seed_coverage.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/seed_coverage.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(experiment_type, target_dataset, training_datasets, model, representation, feature_set);  summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| tables/rq_counts.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/rq_counts.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/metric_consistency.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/metric_consistency.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/metric_missingness.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/metric_missingness.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/empty_files.csv | `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/empty_files.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/SOURCE_FILES.parquet`. This mapping contains 16715 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 50792. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/TRACEABILITY.csv` lists all 15 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
