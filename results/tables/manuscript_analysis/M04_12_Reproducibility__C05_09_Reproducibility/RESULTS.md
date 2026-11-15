# Results — 5.9 / All

Custo reconstruído por soma dos tempos registrados em `tables/runtime_summary.csv`; não representa tempo de calendário, nem todos os custos de extração do encoder.

Arquivos e espaço constam em `tables/storage_summary.csv`; completude de metadados em `tables/artifact_completeness.csv`.

Valores de tabelas foram escolhidos com seed fixa e recalculados dos JSON originais (`tables/reproducibility_audit.csv`).

Foram reconstruídos 15 valores finais diretamente dos JSON originais; 15 conferiram à tolerância 1e-12. Fonte: `tables/reproducibility_audit.csv`, coluna match.

## Interpretation and limitations

Somente stat dos artefatos grandes; checkpoints não são lidos. Runtime somado apenas para runs utilizáveis, falhas sem duração não imputadas. RSS é pico cumulativo do processo, não memória incremental por fold. Configuração atual tem hash, porém histórico imutável não existe. Auditoria numérica seleciona linhas de tabelas ID/LODO/threshold e reabre os JSON de métricas para média independente.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Positive, Negative and Null Results

Todas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| tables/runtime_summary.csv | `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/runtime_summary.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/storage_summary.csv | `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/storage_summary.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/artifact_completeness.csv | `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/artifact_completeness.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/reproducibility_audit.csv | `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/reproducibility_audit.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/selected_prediction_metric_audit.csv | `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/selected_prediction_metric_audit.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/SOURCE_FILES.parquet`. This mapping contains 16715 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 50793. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/TRACEABILITY.csv` lists all 5 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
