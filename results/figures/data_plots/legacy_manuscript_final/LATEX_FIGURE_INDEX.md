# LaTeX manuscript figure index



The inclusion directory contains eleven final PDFs, the requested revised-figure PNGs at300 dpi, and manuscript documentation. Analytical tables and plotting scripts remain outside it. All figures are intended for full two-column width (174 mm); use figure* in a two-column manuscript. Proposed order follows the Results narrative. No approved final experimental-design PDF was found; 00 is deliberately omitted.



## 01 — lodo by target



Filename: `01_lodo_by_target.pdf`. Section: 5.3 Cross-Dataset Generalization.

Purpose: Controlled LODO performance across unseen targets.

Source analytical table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_by_target.parquet`.

Label: `fig:lodo-by-target`. Suggested width: `\textwidth`.

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/01_lodo_by_target.pdf}
```

Suggested caption: Controlled LODO performance across unseen targets.



## 02 — id ood common test gap



Filename: `02_id_ood_common_test_gap.pdf`. Section: 5.3 Cross-Dataset Generalization.

Purpose: ID minus OOD F1 evaluated on exactly the same holdout.

Source analytical table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/id_ood_same_test.parquet`.

Label: `fig:id-ood-common-test-gap`. Suggested width: `\textwidth`.

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/02_id_ood_common_test_gap.pdf}
```

Suggested caption: ID minus OOD F1 evaluated on exactly the same holdout.



## 03 — generalization vs source count



Filename: `03_generalization_vs_source_count.pdf`. Section: 5.4 Source-Dataset Contribution.

Purpose: Historical OOD F1 versus effective source-pool size. Each target receives equal weight after seed and coalition aggregation. Bands show target IQR; the detached six-source point uses fewer eligible targets.

Source analytical table: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/performance_by_source_count_macro.parquet`.

Label: `fig:generalization-vs-source-count`. Suggested width: `\textwidth`.

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/03_generalization_vs_source_count.pdf}
```

Suggested caption: Historical OOD F1 versus effective source-pool size. Each target receives equal weight after seed and coalition aggregation. Bands show target IQR; the detached six-source point uses fewer eligible targets.



## 04 — marginal gain per added source

Filename: `04_marginal_gain_per_added_source.pdf`. Section: 5.4 Source-Dataset Contribution.

Purpose / suggested caption: Target-macro marginal F1 change after adding one source, across seven targets. Each target receives equal weight after matched-seed and coalition-context aggregation. The lower strips show target-macro percentages of negative additions. Dashed line: zero gain. Only transitions1→2 through4→5 are connected;5→6 is omitted because its target cohort differs.

Source analytical tables: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/marginal_gain_by_pool_size_target_macro.parquet`.

Label: `fig:marginal-gain-per-added-source`. Width: `\textwidth` (174 mm, full two-column figure*).

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/04_marginal_gain_per_added_source.pdf}
```

Visual revision: Edge-distribution boxplots → Target-macro connected points with signed values and aligned negative-addition percentage strips. Corresponding PDF-rendered PNG: `04_marginal_gain_per_added_source.png` (300 dpi). See MANUSCRIPT_FIGURE_TRACEABILITY.md for exact sources and hashes.

## 05 — marginal gain by source and pool size

Filename: `05_marginal_gain_by_source_and_pool_size.pdf`. Section: 5.4 Source-Dataset Contribution.

Purpose / suggested caption: Target-macro marginal F1 change by added source and existing pool size. Numeric annotations show signed effects; zero-centered colors are shared across all panels. Targets have equal weight after seed and within-target coalition aggregation. Only1→2 through4→5 are shown, preserving each source’s eligible target set. The5→6 results remain in the analytical table but are omitted here.

Source analytical tables: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/tables/marginal_gain_by_added_source_and_pool_size.parquet`.

Label: `fig:marginal-gain-by-source-and-pool-size`. Width: `\textwidth` (174 mm, full two-column figure*).

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/05_marginal_gain_by_source_and_pool_size.pdf}
```

Visual revision: Unannotated six-panel heatmap → Annotated heatmap; 2 representation rows ×3 model columns; four transitions. Corresponding PDF-rendered PNG: `05_marginal_gain_by_source_and_pool_size.png` (300 dpi). See MANUSCRIPT_FIGURE_TRACEABILITY.md for exact sources and hashes.

## 06 — marginal gain by source and target

Filename: `06_marginal_gain_by_source_and_target.pdf`. Section: 5.4 Source-Dataset Contribution.

Purpose / suggested caption: Mean marginal change in target F1 when a source was added across all valid existing coalition contexts, not one dataset-addition order. Signed cell values and a shared zero-centered scale show magnitude and sign. Gray cells are self-target or otherwise ineligible. Six panels are arranged as model rows and representation columns for readable annotations.

Source analytical tables: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/tables/marginal_gain_by_added_source_target.parquet`.

Label: `fig:marginal-gain-by-source-and-target`. Width: `\textwidth` (174 mm, full two-column figure*).

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/06_marginal_gain_by_source_and_target.pdf}
```

Visual revision: Unannotated six-panel heatmap → Annotated heatmap; 3 model rows ×2 representation columns. Corresponding PDF-rendered PNG: `06_marginal_gain_by_source_and_target.png` (300 dpi). See MANUSCRIPT_FIGURE_TRACEABILITY.md for exact sources and hashes.

## 07 — source contribution

Filename: `07_source_contribution.pdf`. Section: 5.4 Source-Dataset Contribution.

Purpose / suggested caption: Controlled leave-one-source-out contribution: full-pool F1 minus source-removed F1. Positive values mean the source was beneficial because removing it reduced F1; negative values mean removing the source improved F1. Eligible matched-seed means are annotated; missing combinations remain gray. Six panels use model rows and representation columns.

Source analytical tables: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/source_contribution_by_target.parquet`.

Label: `fig:source-contribution`. Width: `\textwidth` (174 mm, full two-column figure*).

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/07_source_contribution.pdf}
```

Visual revision: Unannotated six-panel heatmap → Annotated heatmap; 3 model rows ×2 representation columns. Corresponding PDF-rendered PNG: `07_source_contribution.png` (300 dpi). See MANUSCRIPT_FIGURE_TRACEABILITY.md for exact sources and hashes.

## 08 — selected score shift



Filename: `08_selected_score_shift.pdf`. Section: 5.5 Decision Behavior.

Purpose: Saved score distributions for the previously selected representative largest-oracle-gap condition. Oracle selection is diagnostic; source-validation and target-test histograms are stratified by class.

Source analytical table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/derived/selected_score_histograms.parquet`.

Label: `fig:selected-score-shift`. Suggested width: `\textwidth`.

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/08_selected_score_shift.pdf}
```

Suggested caption: Saved score distributions for the previously selected representative largest-oracle-gap condition. Oracle selection is diagnostic; source-validation and target-test histograms are stratified by class.



## 09 — cross dataset stable features



Filename: `09_cross_dataset_stable_features.pdf`. Section: 5.6 Feature Stability.

Purpose: Most stable engineered features across unseen targets in historical CatBoost LODO. Top-10 frequency is the proportion of eligible target/seed models containing the feature among their ten highest-ranked engineered features. This is recurrence, not causal transferability.

Source analytical table: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/top10_cross_dataset_stable_features.parquet`.

Label: `fig:cross-dataset-stable-features`. Suggested width: `\textwidth`.

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/09_cross_dataset_stable_features.pdf}
```

Suggested caption: Most stable engineered features across unseen targets in historical CatBoost LODO. Top-10 frequency is the proportion of eligible target/seed models containing the feature among their ten highest-ranked engineered features. This is recurrence, not causal transferability.



## 10 — canonicalization effect



Filename: `10_canonicalization_effect.pdf`. Section: 5.7 Canonicalization and Dataset Separability.

Purpose: Controlled paired F1 difference CANONICALIZED minus RAW on identical samples and partitions, summarized over seeds.

Source analytical table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/canonicalization_by_target.parquet`.

Label: `fig:canonicalization-effect`. Suggested width: `\textwidth`.

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/10_canonicalization_effect.pdf}
```

Suggested caption: Controlled paired F1 difference CANONICALIZED minus RAW on identical samples and partitions, summarized over seeds.



## 11 — controlled separability

Filename: `11_controlled_separability.pdf`. Section: 5.7 Canonicalization and Dataset Separability.

Purpose / suggested caption: Dataset-origin separability as paired RAW and CANONICALIZED seed means for all samples, benign-only and malicious-only conditions. Labels show both saved means and saved paired Δ (CANONICALIZED minus RAW). The vertical dashed uniform reference is approximately0.143 (1/7; an asymptotic balanced macro-F1 reference, not a finite-sample guarantee). The x-axis spans0–1; seed SD is omitted for clarity.

Source analytical tables: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/separability.parquet`, `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/separability_paired_deltas.parquet`.

Label: `fig:controlled-separability`. Width: `\textwidth` (174 mm, full two-column figure*).

```latex
\includegraphics[width=\textwidth]{figures/manuscript_final/11_controlled_separability.pdf}
```

Visual revision: Grouped bars with seed-SD error bars → Paired dumbbell/connected-dot plot, direct RAW/CANONICALIZED labels and saved paired deltas; SD bars omitted. Corresponding PDF-rendered PNG: `11_controlled_separability.png` (300 dpi). See MANUSCRIPT_FIGURE_TRACEABILITY.md for exact sources and hashes.

## Data Sources and Traceability

Per-figure sources, filters, aggregation, rendering scripts and original PDF paths are documented in MANUSCRIPT_FIGURE_TRACEABILITY.md in this directory. The collection and new analysis were performed by `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`, command `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`. Full copy manifest and input/output hashes are in `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/ARTIFACT_MANIFEST.json`. Each figure’s analytical source carries experiment_ids; follow the listed lineage file to original experimental artifacts. Historical source-count/coalition and feature-stability results remain separate from the controlled supplement. No models, predictions, importance metrics or validated source tables were altered.

Visual revision audit: `artigo/figures/visual_revision_audit/VISUAL_REVISION_AUDIT.json`. NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION. The original collection manifest is a historical snapshot; current hashes for revised figures are in this audit and the updated traceability sections.
