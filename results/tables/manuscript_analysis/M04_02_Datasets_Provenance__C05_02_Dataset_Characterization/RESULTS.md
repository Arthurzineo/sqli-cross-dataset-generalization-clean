# Results — 5.2 / All

Distribuições de classes, tamanho e diversidade estão em `tables/dataset_characterization.csv`; diferenças lexicais são estratificadas por classe em `tables/dataset_textual_characteristics.csv`.

RAW e CANONICALIZED são arquivos distintos, com tamanhos diferentes em parte das fontes. artificial é documentado, mas artificial_sqli é a variante da grade principal.

As 14 versões das fontes primárias têm prevalência positiva 0.500000 a 0.500000 (`tables/dataset_characterization.csv`, filtro primary=True). Isso controla a prevalência global entre arquivos, mas não torna os conteúdos equivalentes nem garante balanço após remoções no desenvolvimento.

## Interpretation and limitations

Arquivos originais processados um dataset por vez; sem treino. Caracterização lexical existente reutilizada com sua procedência. n_unique refere-se ao texto realmente carregado; prevalência é ataques/n. DOI, ano e método de geração permanecem ausentes quando não registrados.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Positive, Negative and Null Results

Todas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| tables/dataset_characterization.csv | `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_characterization.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/dataset_class_distribution.csv | `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_class_distribution.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/dataset_textual_characteristics.csv | `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_textual_characteristics.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/dataset_provenance.csv | `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_provenance.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| derived/normalization_audit.parquet | `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/derived/normalization_audit.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| derived/canonicalization_effects.parquet | `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/derived/canonicalization_effects.parquet` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| tables/selected_class_controlled_lexical_differences.csv | `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/selected_class_controlled_lexical_differences.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/SOURCE_FILES.parquet`. This mapping contains 0 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 18. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/TRACEABILITY.csv` lists all 11 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
