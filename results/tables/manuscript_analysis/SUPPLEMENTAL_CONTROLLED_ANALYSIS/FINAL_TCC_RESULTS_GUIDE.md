# Chapter 5 — Controlled supplemental results guide

Este é um complemento, não uma substituição das contagens e populações históricas. Consulte RESULTS.md para os valores e ressalvas.

## 5.1 Experimental Coverage and Integrity

Main result and safe interpretation: A auditoria dos manifests agora é completa; não prova cada operação interna nem quase-duplicatas semânticas.

Tables to include: tables/coverage.csv

Figures to include: none

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.2 Dataset, Representation, and Model Characterization

Main result and safe interpretation: Explicar que CAN deriva das mesmas linhas RAW e inclui URL/body; 64 features, sem embeddings.

Tables to include: tables/paired_dataset_characterization.csv

Figures to include: none

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.3 Cross-Dataset Generalization — RQ1

Main result and safe interpretation: Resultado principal: F1 por alvo e gap em teste idêntico; média global somente secundária.

Tables to include: tables/lodo_by_target.csv; tables/id_ood_same_test.csv

Figures to include: figures/lodo_by_target.pdf; figures/id_ood_common_test_gap.pdf

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.4 Source-Dataset Contribution — RQ2

Main result and safe interpretation: Resultado principal: efeitos com validação fixa; número de seeds elegíveis varia. Não é comparação size-matched nem causal.

Tables to include: tables/source_contribution_by_target.csv; tables/negative_transfer.csv

Figures to include: figures/source_contribution.pdf

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.5 Decision Behavior — RQ3

Main result and safe interpretation: Oracle só diagnóstico; separar ranking de scores e threshold. Casos extremos não estimam população.

Tables to include: tables/decision_by_target.csv

Figures to include: figures/selected_score_shift.pdf

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.6 Feature Stability — RQ3

Main result and safe interpretation: Importância nativa CatBoost; não invariância causal, não dimensões de embedding.

Tables to include: tables/stable_features.csv; tables/source_removal_feature_effects.csv

Figures to include: none

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.7 Canonicalization and Dataset Separability — RQ4

Main result and safe interpretation: Resultado principal: efeito pareado e origem ainda discriminável. Não omitir perdas; não inferir causa por correlação.

Tables to include: tables/canonicalization_by_target.csv; tables/separability.csv

Figures to include: figures/canonicalization_effect.pdf; figures/controlled_separability.pdf

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.8 Statistical Synthesis

Main result and safe interpretation: Seeds agregadas dentro do alvo; Holm por família; conservar não significativos e não aplicáveis separadamente.

Tables to include: statistics/tests_holm.csv

Figures to include: none

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.

## 5.9 Reproducibility

Main result and safe interpretation: Reconstrução dos originais; não confundir runtime somado e parede; não juntar novos IDs aos antigos sem rótulo de protocolo.

Tables to include: tables/reproducibility_audit.csv; tables/runtime_summary.csv

Figures to include: none

Source analysis folder: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/`; detailed findings: `RESULTS.md`.

Supplementary: tabelas por seed, métricas adicionais, casos selecionados, ranks completos e manifests. Negative/null findings: todas as perdas/zeros e testes não significativos permanecem nas tabelas; não aplicar conclusões a condições ausentes.
## Data Sources and Traceability

Original-file mapping: `SOURCE_FILES.parquet`, one row per supplemental experiment_id; all eligible IDs are included. Primary analytical inputs: `<PROJECT_ROOT>/artigo/complementos_generalizacao_v1/full/analysis/master_results.parquet`, `SOURCE_LINEAGE.parquet`, `raw_vs_canonicalized_pairs.parquet`, `id_vs_ood_same_test.parquet`, `fixed_validation_contribution.parquet`. Globs for underlying artifacts: `<PROJECT_ROOT>/artigo/complementos_generalizacao_v1/full/runs/SUPP_*/metrics.json`, `feature_importance.parquet`, `predictions.parquet`; these are not all opened indiscriminately. Selected prediction IDs/criteria: `selected_runs/cases.csv`. Exact unique files read, counts by extension, projected columns, hashes and sizes: `FILES_READ.csv`, `ANALYSIS_AUDIT.json`. No checkpoint contents read, no training, no raw payload reads. Historical audit uses only `<PROJECT_ROOT>/artigo/complementos_generalizacao_v1/existing_analysis/split_audit/SUMMARY.json`; individual historical results remain separate.

Filters: completed consolidated runs, pilot_cap=0, one execution context, unique IDs; specific kind/target/model/view/source filters and formulas in `TRACEABILITY.csv` and `ANALYSIS_METHOD.md`. All scientific table rows contain row_id and experiment_ids. Seeds are summarized inside target/condition, never independent targets; absent comparisons remain absent. `TRACEABILITY.csv` records source columns, grouping/formula, command, figure source table, and each derived artifact. Original arrays for controlled cohorts remain in cache paths referenced by metrics.json; `tables/paired_dataset_characterization.csv` links dataset hashes. All tables: `tables/`, per-seed intermediates: `derived/`, statistics: `statistics/`, figures PNG/PDF: `figures/`. Figure/table relationships are explicit in TRACEABILITY.csv.

Script: `<PROJECT_ROOT>/artigo/scripts/analyze_supplemental_results.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analyze_supplemental_results.py`. Code hash, run counts, actual file counts, generation timestamp, runtime, peak RAM and reproducibility checks: `ANALYSIS_AUDIT.json`. Complete cell-to-source reconstruction example: table row → experiment_ids → SOURCE_FILES.parquet metric_file → original metrics.json. Random reconstructed values are in `tables/reproducibility_audit.csv`. This report keeps the historical protocol and new RAW-derived paired protocol separate.
