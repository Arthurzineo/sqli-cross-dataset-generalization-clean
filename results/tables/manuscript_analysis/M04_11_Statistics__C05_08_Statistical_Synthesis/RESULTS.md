# Results — 5.8 / All

As unidades estatísticas são targets após resumo das seeds (`statistics/descriptive_summary.csv`). Intervalos bootstrap são exploratórios para este conjunto de fontes.

Wilcoxon, Friedman e correção Holm estão em `statistics/wilcoxon_results.csv`, `friedman_results.csv` e `holm_adjusted.csv`.

Associações previstas aparecem em `statistics/cross_rq_relationships.csv`; correlações entre número de fontes e F1 dentro de cada target são descritivas em `source_count_within_target.csv`.

Entre 132 testes com p ajustado disponível, 0 têm p_Holm<0.05, nas famílias pré-especificadas no arquivo. `statistics/holm_adjusted.csv`, filtro p_holm.notna(); isso não converte ausência de detecção nos demais testes em prova de equivalência.

Nenhum ranking de modelos é confirmado pelos testes Friedman corrigidos quando p_Holm≥0.05; 6 de 6 omnibus nessa situação (`statistics/holm_adjusted.csv`, filtro test=friedman). Post-hoc só seria realizado após omnibus ajustado significativo.

Relação brier_vs_ood_f1: 2 de 6 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=brier_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação calibration_degradation_vs_ood_f1: 1 de 6 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=calibration_degradation_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação feature_instability_vs_generalization_gap: 0 de 2 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=feature_instability_vs_generalization_gap. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação feature_instability_vs_negative_transfer: 0 de 2 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=feature_instability_vs_negative_transfer. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação feature_instability_vs_ood_f1: 0 de 2 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=feature_instability_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação oracle_gap_vs_ood_f1: 0 de 6 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=oracle_gap_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação source_contribution_vs_ood_f1: 0 de 6 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=source_contribution_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação threshold_drift_vs_generalization_gap: 0 de 6 estratos com p_Holm<0.05; tabela `statistics/cross_rq_relationships.csv`, filtro relationship=threshold_drift_vs_generalization_gap. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

## Interpretation and limitations

Seeds não são unidades independentes. Wilcoxon bilateral sobre diferenças entre targets; mínimo cinco targets; Holm por família registrada. Friedman por representação/métrica para três modelos (aproximação qui-quadrado, n pequeno); post-hoc somente se omnibus p_Holm<.05. Spearman cross-RQ com permutação bilateral exata até oito targets, uma observação por target; sem inferência quando constante ou n<5. Não usar resultados estatísticos legados com pseudo-replicação. Brier combina calibração/discriminação e compartilha predições com F1; correlação não isola mecanismos.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Negative and Null Findings

Os testes com p_Holm≥0.05 estão preservados em `statistics/holm_adjusted.csv`; devem ser descritos como ausência de diferença detectável, nunca equivalência. Pares insuficientes/constantes constam de `wilcoxon_results.csv` e `cross_rq_relationships.csv`. Ausência de pareamento LODO impede estimar seu efeito isolado de canonicalização. Separabilidade controlada por classe não foi executada; isso é falta de evidência, não efeito nulo. Negative transfer observado está em M04.07/tables/negative_transfer.csv.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| statistics/descriptive_summary.csv | `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/descriptive_summary.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| statistics/wilcoxon_results.csv | `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/wilcoxon_results.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| statistics/friedman_results.csv | `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/friedman_results.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| statistics/holm_adjusted.csv | `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/holm_adjusted.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| statistics/source_count_within_target.csv | `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/source_count_within_target.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | descriptive Spearman across effective pools within target; no pseudo-independent p-values across coalitions | `artigo/scripts/analysis/final_analysis.py` |
| statistics/cross_rq_relationships.csv | `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| statistics/pairwise_vs_lodo.csv | `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/pairwise_vs_lodo.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/SOURCE_FILES.parquet`. This mapping contains 14790 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 45141. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_11_Statistics__C05_08_Statistical_Synthesis/TRACEABILITY.csv` lists all 7 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
