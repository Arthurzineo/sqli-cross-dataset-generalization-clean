# Generalização

Methodology section: 4.6

TCC Results section: 5.3

Research Question: RQ1

Purpose: Generalização


Main generated artifacts:

- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/ID/tables/id_results.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/pairwise_results.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/source_average.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/target_average.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/transfer_asymmetry.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_f1.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_mcc.pdf`

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/SOURCE_FILES.parquet`. This mapping contains 2220 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 6843. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/TRACEABILITY.csv` lists all 43 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
