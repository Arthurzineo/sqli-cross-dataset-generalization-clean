# Results — 5.1 / All

Duplicatas e conflitos estão quantificados em `tables/duplicate_audit.csv` e `tables/label_conflicts.csv`; remoções por fold em `tables/before_after_audit.csv`.

Pairwise permite pares da mesma família e precisa identificá-los. LODO e contribuição aplicam controle de família. Oracle usa o target somente como diagnóstico (`tables/leakage_checks.csv`).

srbh/CANONICALIZED tem 68 chaves canônicas com rótulos conflitantes (`tables/label_conflicts.csv`, row_id 4195c512d8ad927b7091). O teste preserva essas entradas; esse ruído limita o desempenho interpretável.

## Interpretation and limitations

Lowercase e whitespace auditados separadamente nesta análise; chave canônica combina URL decode recursivo, casefold e normalização whitespace. Overlaps inter-dataset reutilizados da auditoria salva. Alvo preservado; remoções de conflitos e overlap ocorrem no desenvolvimento. Validação reserva uma família inteira quando ambas as partições têm duas classes; fallback GroupShuffleSplit. Não houve busca source-aware de hiperparâmetros.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Positive, Negative and Null Results

Todas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| tables/duplicate_audit.csv | `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/duplicate_audit.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/cross_dataset_overlap.csv | `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/cross_dataset_overlap.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/label_conflicts.csv | `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/label_conflicts.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/before_after_audit.csv | `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/before_after_audit.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/leakage_checks.csv | `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/leakage_checks.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/selected_split_hash_audit.csv | `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/selected_split_hash_audit.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | exact set intersections of canonical hashes; targeted selection, not exhaustive all-run row audit | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/SOURCE_FILES.parquet`. This mapping contains 16650 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 50738. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/TRACEABILITY.csv` lists all 8 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
