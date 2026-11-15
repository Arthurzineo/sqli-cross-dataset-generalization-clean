# Experiment Inventory

               category     n
         total_previsto 16710
       total_encontrado 16715
 total_concluido_status 16652
       total_utilizavel 16650
       total_incompleto     0
            total_falho     3
         total_excluido    65
contribution_utilizavel 13170

Source: M04.01/tables/run_counts.csv; counts are registry/status reconciled, not number of files indiscriminately. Registry duplicate IDs: `_global/duplicate_registry_ids.csv`. Missing planned combinations: M04.01/tables/missing_runs.csv. Exclusion reasons: M04.01/tables/excluded_runs.csv.

## Data Sources and Traceability

Original inputs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`, `artigo/docs/experiment_registry/experiments.csv`, original dataset metadata/configuration, and selected predictions/features/splits only. Full paths and IDs: `_global/SOURCE_LINEAGE.parquet` and `_global/SOURCE_FILES.parquet`. Actual unique files read and byte counts: `_global/FILES_READ.parquet`, `_global/file_read_summary.csv`. No checkpoint content read.

Master table: `_global/master_results.parquet`; registry: `_global/run_registry.parquet`. Columns, exact row filters, groupings, artifacts/tables/figures and formulas are documented per section in TRACEABILITY.csv, ANALYSIS_METHOD.md and Metric Provenance. Seeds are averaged within condition; targets are the statistical units. Each reported value is linked to a table row_id with experiment_ids. Missing conditions are not imputed. Complete generated artifact catalog: `_global/ARTIFACT_CATALOG.csv`.

Script: `artigo/scripts/analysis/final_analysis.py`. Config: `artigo/scripts/analysis/config.json`. Command: `<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json`. Derived outputs are all within `artigo/analise_resultados_tcc/`. Follow each section's SOURCE_FILES.parquet for original metrics, predictions, scores, thresholds, features and manifests. Use trace_value.py for a specific cell.
