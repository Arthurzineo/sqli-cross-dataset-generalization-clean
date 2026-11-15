# Results — 5.7 / RQ4

A elegibilidade pareada de cada comparação está em `RAW_VS_CANONICALIZED/tables/pairing_audit.csv`; apenas execuções elegíveis alimentam `paired_results.csv`.

Separabilidade existente é exploratória: os tamanhos por origem não são iguais e duplicatas não foram controladas (`DATASET_SEPARABILITY/tables/separability_all.csv`). Os experimentos benign-only e malicious-only não existem.

Sem observações de separabilidade por target, as relações separabilidade→generalização não são estimáveis (`RELATIONSHIPS/tables/separability_vs_generalization.csv`).

Dos 8220 candidatos pareados por configuração, 15 satisfizeram igualdade de amostras por split. Protocolos elegíveis: baseline_id; targets: ecml. Fonte: `RAW_VS_CANONICALIZED/tables/pairing_audit.csv` e `paired_results.csv`. Não há estimativa pareada LODO do efeito isolado da canonicalização.

Separabilidade exploratória RAW: Macro-F1=0.854330, n=30654, seed=42; `DATASET_SEPARABILITY/tables/separability_all.csv`, row_id 942361a1b4c01196ea6d. Sem controles suficientes, isso não prova redução controlada de separabilidade.

Separabilidade exploratória CANONICALIZED: Macro-F1=0.822894, n=30436, seed=42; `DATASET_SEPARABILITY/tables/separability_all.csv`, row_id 646fce9b57d77aebf01a. Sem controles suficientes, isso não prova redução controlada de separabilidade.

## Interpretation and limitations

Parear protocolo/target/fontes/modelo/config/feature/seed/family policy. Exigir contagens iguais e multiconjuntos dataset+canonical_hash+label+split iguais. Delta=CANONICALIZED−RAW. O hash canônico permite alinhamento sem IDs dependentes de representação. Mesmo multiconjunto não prova equivalência individual de rótulos conflitantes; casos de erro serão pareados somente por chave única. Não realizar treino adicional para preencher condições ausentes.

As observações se limitam às fontes avaliadas. Não demonstram causalidade nem transferência universal. Casos selecionados apoiam interpretação e não estimam prevalência de erros.

## Positive, Negative and Null Results

Todas as condições das tabelas são preservadas, incluindo baixo desempenho e efeitos negativos/zero. Não significância e indisponibilidade são distintas; resultados inexistentes estão marcados, não substituídos por zeros. Consulte as tabelas completas e a síntese estatística antes de afirmar superioridade.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| RAW_VS_CANONICALIZED/tables/pairing_audit.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/pairing_audit.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| RAW_VS_CANONICALIZED/tables/paired_results.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/paired_results.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| RAW_VS_CANONICALIZED/tables/by_target.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/by_target.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(experiment_type, target_dataset, model, feature_set); delta_precision, delta_recall, delta_f1, delta_mcc, delta_pr_auc, delta_roc_auc, delta_balanced_accuracy, delta_specificity, delta_fpr, delta_fnr, delta_brier, delta_ece_10, delta_threshold_source, delta_threshold_drift summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| RAW_VS_CANONICALIZED/tables/by_model.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/by_model.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(experiment_type, model, feature_set); delta_f1_mean, delta_mcc_mean, delta_pr_auc_mean summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| RAW_VS_CANONICALIZED/tables/win_tie_loss.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/win_tie_loss.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | groupby(experiment_type, target_dataset, model, feature_set); delta_precision, delta_recall, delta_f1, delta_mcc, delta_pr_auc, delta_roc_auc, delta_balanced_accuracy, delta_specificity, delta_fpr, delta_fnr, delta_brier, delta_ece_10, delta_threshold_source, delta_threshold_drift summarized with mean/std(ddof=1)/median/min/max; n_seeds identifies seed repetition; input row experiment_ids unioned | `artigo/scripts/analysis/final_analysis.py` |
| DATASET_SEPARABILITY/tables/separability_all.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/DATASET_SEPARABILITY/tables/separability_all.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| DATASET_SEPARABILITY/tables/separability_benign.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/DATASET_SEPARABILITY/tables/separability_benign.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| DATASET_SEPARABILITY/tables/separability_malicious.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/DATASET_SEPARABILITY/tables/separability_malicious.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| DATASET_SEPARABILITY/tables/raw_vs_canonicalized.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/DATASET_SEPARABILITY/tables/raw_vs_canonicalized.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |
| RELATIONSHIPS/tables/separability_vs_generalization.csv | `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RELATIONSHIPS/tables/separability_vs_generalization.csv` | SOURCE_FILES.parquet / AUXILIARY_SOURCES.csv | row_id + experiment_ids + dimensions | none; one row per observation | `artigo/scripts/analysis/final_analysis.py` |

## Data Sources and Traceability

Original source-file mapping: `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/SOURCE_FILES.parquet`. This mapping contains 16440 experiment IDs and paths to metrics, manifests, predictions, scores, thresholds and feature files. Mapped artifacts are not necessarily opened.

Auxiliary inputs (including dataset provenance and original metadata): `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/AUXILIARY_SOURCES.csv`.

Original globs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`; selected-only `artigo/runs/feature_importance/EXP_*.csv`, `artigo/runs/predictions/EXP_*.csv`. Dataset globs: `artigo/datasets/metadata/*.csv`, `artigo/datasets/original_copies/{raw,decoded}/*`, `artigo/datasets/processed/embeddings/*/*.json`. No checkpoints read.

Number of mapped files actually read in the analysis session: 50093. Complete read ledger with byte sizes and mtime: `_global/FILES_READ.parquet`. For global exact unique-file counts, see `_global/file_read_summary.csv`. Files may support multiple sections; do not add section counts.

Master: `artigo/analise_resultados_tcc/_global/master_results.parquet`. Lineage: `artigo/analise_resultados_tcc/_global/SOURCE_LINEAGE.parquet`. Registry: `artigo/analise_resultados_tcc/_global/run_registry.parquet`.

Columns: every artifact's `source_columns` is recorded in `TRACEABILITY.csv`. Metrics use `metrics_source`; `metrics_oracle_diagnostic` is exclusively diagnostic. Filters: usable=True (completed, pilot=0, valid metrics) unless coverage/exclusion audit; exact per-row IDs and dimension columns define all additional selections. No seed treated as an independent target. Grouping and seed aggregation: mean/std(ddof=1)/median/min/max within target + requested composition + model + representation + feature set; macro summaries then weight targets equally. Explicit derived comparisons are paired by seed first.

Formulas: F1=2TP/(2TP+FP+FN); gap=ID−OOD; ratio=OOD/ID; contribution=full−removed for higher-is-better, reversed for error rates; threshold drift=abs(source−oracle); oracle gap=F1_oracle−F1_source; canonicalization delta=CANONICALIZED−RAW only for eligible pairs. PR-AUC is average precision. Non-applicable metrics are null, not zero.

Script: `artigo/scripts/analysis/final_analysis.py`. Configuration: `artigo/scripts/analysis/config.json`.

Command (from project root):
```bash
<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json
```

Derived files, tables and figures: `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/TRACEABILITY.csv` lists all 10 registered artifacts, their source tables, columns, filters, aggregation and generation command. Each table has `row_id`, `experiment_ids` and `source_file`; figure provenance points to its exact plotting table. Follow row_id → experiment_ids → SOURCE_FILES → original JSON/prediction/split. Use `scripts/analysis/trace_value.py --table <table> --row-id <row_id> --column <column>` to print the chain.
