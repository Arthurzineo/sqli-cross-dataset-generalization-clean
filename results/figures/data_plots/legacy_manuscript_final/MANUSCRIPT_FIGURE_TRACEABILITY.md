# Manuscript figure traceability



The initial collection copied validated PDFs byte-for-byte. The current visual revision replaces only04,05,06,07,11 in place; their updated sections supersede the initial collection hashes. All other manuscript PDFs and every upstream analytical table remain unchanged. Model labels: Logistic Regression, CatBoost, MLP; representations: RAW, CANONICALIZED. Original analytical figures and metrics remain unchanged; only the explicitly requested Results-report extension was applied, with a preserved pre-extension copy.



Collection script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.

New interaction evidence: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS`. Pair checks: `derived/input_pair_verification.parquet`. Total valid contexts=6480; matched seed pairs=32400; five matched seeds/context. The underlying complete interaction tables cover that same set; revised figure05 displays only base sizes1..4, whereas figure06 retains all valid contexts. Counting an edge in multiple summaries does not create independent observations.

Analysis A: seed-matched nested edge means → equal coalition contexts within each target/source/model/view/k → equal targets. Analysis B: seed-matched nested edge means → equal contexts within source/target/model/view across all eligible sizes. Ineligible cells remain absent and plot gray; never zero-filled. No inference treats contexts or seeds as independent targets.



## 01_lodo_by_target.pdf



- Final PDF: `artigo/figures/manuscript_final/01_lodo_by_target.pdf`.

- Original PDF (copied): `artigo/figures/final/lodo_by_target.pdf`.

- Source Parquet: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_by_target.parquet`; corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_by_target.csv`.

- Columns: target, model, representation, test_f1_mean; experiment_ids and row_id for lineage.

- Filters / aggregation: All targets/models/views; saved seed means; no pooled test samples.

- Experiment IDs: in source analytical rows; original artifact mapping: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet`.

- Rendering script: `artigo/scripts/render_final_manuscript_figures.py`.

- Rendering command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/render_final_manuscript_figures.py --overwrite  # backups preserved by renderer; NOT executed in this task`.

- Collection command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.

- Final PDF SHA-256: `5d047b90447e777b34ef7b81545a4308397f4195f174f1368a5dd78ac4bc74ef`.



## 02_id_ood_common_test_gap.pdf



- Final PDF: `artigo/figures/manuscript_final/02_id_ood_common_test_gap.pdf`.

- Original PDF (copied): `artigo/figures/final/id_ood_common_test_gap.pdf`.

- Source Parquet: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/id_ood_same_test.parquet`; corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/id_ood_same_test.csv`.

- Columns: target, model, representation, gap_f1_mean; experiment_ids and row_id for lineage.

- Filters / aggregation: All saved target/model/view means over paired seeds; identical evaluated holdout.

- Experiment IDs: in source analytical rows; original artifact mapping: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet`.

- Rendering script: `artigo/scripts/render_final_manuscript_figures.py`.

- Rendering command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/render_final_manuscript_figures.py --overwrite  # backups preserved by renderer; NOT executed in this task`.

- Collection command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.

- Final PDF SHA-256: `2428c52c6bdc944ad317a25b875da622dd437fe5efea7b2e96812da44ee0faa3`.



## 03_generalization_vs_source_count.pdf



- Final PDF: `artigo/figures/manuscript_final/03_generalization_vs_source_count.pdf`.

- Original PDF (copied): `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/figures/generalization_vs_source_count.pdf`.

- Source Parquet: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/performance_by_source_count_macro.parquet`; corresponding CSV: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/performance_by_source_count_macro.csv`.

- Columns: model, representation, n_sources, n_targets, f1_mean, f1_q25, f1_q75; experiment_ids and row_id for lineage.

- Filters / aggregation: All historical usable effective coalitions; seed mean then coalition mean inside target, then equal targets. Seven targets for1..5, five for6; no connection across cohort change.

- Experiment IDs: in source analytical rows; original artifact mapping: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_LINEAGE.parquet`.

- Rendering script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.

- Rendering command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.

- Collection command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.

- Final PDF SHA-256: `ec483733c6a704ab2bc1ee2bf78c0e6dacb3cc36d6ee0d39b482eede718f7fb3`.



## 04_marginal_gain_per_added_source.pdf

- Final PDF: `artigo/figures/manuscript_final/04_marginal_gain_per_added_source.pdf`.
- Final PNG: `artigo/figures/manuscript_final/04_marginal_gain_per_added_source.png`; rasterized directly from revised vector PDF at300 dpi.
- Old visualization: Edge-distribution boxplots.
- New visualization: Target-macro connected points with signed values and aligned negative-addition percentage strips.
- Source analytical tables: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/marginal_gain_by_pool_size_target_macro.parquet`; corresponding CSV files verified exactly against Parquet.
- Columns: model, representation, n_sources_before, n_targets, target_macro_mean_delta_f1, target_macro_fraction_negative; row_id and experiment_ids retained in `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.
- Filters: n_sources_before in {1,2,3,4}; exactly seven targets in every plotted row. 5→6 omitted from this main figure; data remain unchanged in source.
- Aggregation ALREADY PRESENT: Already saved: matched-seed means within exact edges; within-target edge means/fractions; equal target macro means. No edge-weighted replacement.
- Plotting-only calculations: Coordinates copied exactly; signed values formatted to3 decimals; target_macro_fraction_negative ×100 rounded to whole percent for display only. No aggregation or metrics recalculated.
- Experiment lineage: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_LINEAGE.parquet`; saved source-row IDs and experiment IDs resolve the displayed values.
- Rendering script: `artigo/scripts/revise_manuscript_visuals.py`.
- Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/revise_manuscript_visuals.py`. Does not execute any upstream analysis runner.
- Previous manuscript PDF SHA-256 (replaced, no duplicate retained in manuscript_final): `147e3aeb6f17f69bac0ca07aec5583ee8e42717ddbdd8999219bf5628de4fd5d`.
- Current PDF SHA-256: `2c9a2502d7fcae388f173db1be2afcb5c778f5f524ffa7b912172c3688e2c710`.
- Current PNG SHA-256: `5243beedf5375a95c0fca1ff0c6a8043e3ce52c575ac63dc084ce9251e8b91ef`.
- NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION.

Suggested caption: Target-macro marginal F1 change after adding one source, across seven targets. Each target receives equal weight after matched-seed and coalition-context aggregation. The lower strips show target-macro percentages of negative additions. Dashed line: zero gain. Only transitions1→2 through4→5 are connected;5→6 is omitted because its target cohort differs.

## 05_marginal_gain_by_source_and_pool_size.pdf

- Final PDF: `artigo/figures/manuscript_final/05_marginal_gain_by_source_and_pool_size.pdf`.
- Final PNG: `artigo/figures/manuscript_final/05_marginal_gain_by_source_and_pool_size.png`; rasterized directly from revised vector PDF at300 dpi.
- Old visualization: Unannotated six-panel heatmap.
- New visualization: Annotated heatmap; 2 representation rows ×3 model columns; four transitions.
- Source analytical tables: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/tables/marginal_gain_by_added_source_and_pool_size.parquet`; corresponding CSV files verified exactly against Parquet.
- Columns: added_source, n_sources_before, model, representation, mean_target_delta_f1; row_id and experiment_ids retained in `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.
- Filters: n_sources_before in {1,2,3,4}
- Aggregation ALREADY PRESENT: Already saved: matched-seed edge means → contexts within target/source/model/view/k → equal targets.
- Plotting-only calculations: Existing cell values plotted without rounding; annotations only use signed3 decimals. Symmetric scale [−0.1683007296151595,+0.1683007296151595], zero center. Automatic black/white text maximizes sRGB luminance contrast; missing cells masked gray and unannotated.
- Experiment lineage: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/SOURCE_LINEAGE.parquet`; saved source-row IDs and experiment IDs resolve the displayed values.
- Rendering script: `artigo/scripts/revise_manuscript_visuals.py`.
- Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/revise_manuscript_visuals.py`. Does not execute any upstream analysis runner.
- Previous manuscript PDF SHA-256 (replaced, no duplicate retained in manuscript_final): `61bec85843cd50f1d4da0b0720cf9abfa75bcea3a63df2b615f3896be4fafdda`.
- Current PDF SHA-256: `7b0cd941add0c9fcf20b3e05b8fee883391146a05a09526f4145b1c4ab6bc95f`.
- Current PNG SHA-256: `d63b4c924c1b202ed7fa0db11ff3beb23a7bea1bf8e0c0cb06cd8cf6c8c131f1`.
- NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION.

Suggested caption: Target-macro marginal F1 change by added source and existing pool size. Numeric annotations show signed effects; zero-centered colors are shared across all panels. Targets have equal weight after seed and within-target coalition aggregation. Only1→2 through4→5 are shown, preserving each source’s eligible target set. The5→6 results remain in the analytical table but are omitted here.

## 06_marginal_gain_by_source_and_target.pdf

- Final PDF: `artigo/figures/manuscript_final/06_marginal_gain_by_source_and_target.pdf`.
- Final PNG: `artigo/figures/manuscript_final/06_marginal_gain_by_source_and_target.png`; rasterized directly from revised vector PDF at300 dpi.
- Old visualization: Unannotated six-panel heatmap.
- New visualization: Annotated heatmap; 3 model rows ×2 representation columns.
- Source analytical tables: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/tables/marginal_gain_by_added_source_target.parquet`; corresponding CSV files verified exactly against Parquet.
- Columns: added_source, target, model, representation, mean_delta_f1; row_id and experiment_ids retained in `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.
- Filters: All existing eligible rows; missing grid combinations remain missing.
- Aggregation ALREADY PRESENT: Already saved: matched-seed means within edges, then equal coalition contexts within source/target/model/view. Not independent targets or an arbitrary addition order.
- Plotting-only calculations: Existing cell values plotted without rounding; annotations only use signed3 decimals. Symmetric scale [−0.1683007296151595,+0.1683007296151595], zero center. Automatic black/white text maximizes sRGB luminance contrast; missing cells masked gray and unannotated.
- Experiment lineage: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/SOURCE_LINEAGE.parquet`; saved source-row IDs and experiment IDs resolve the displayed values.
- Rendering script: `artigo/scripts/revise_manuscript_visuals.py`.
- Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/revise_manuscript_visuals.py`. Does not execute any upstream analysis runner.
- Previous manuscript PDF SHA-256 (replaced, no duplicate retained in manuscript_final): `10db60c57662ac90c3c3c62f365042d8e2a56b59deb750099e00b11d191576d8`.
- Current PDF SHA-256: `913dbc5300a8b830673484489fa83872fbcc42ebf771d3c96dea211883931429`.
- Current PNG SHA-256: `0340785fe7c6a30af6a5751a775dee885374d6e3ceb040d7bb53451d66a1e9a6`.
- NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION.

Suggested caption: Mean marginal change in target F1 when a source was added across all valid existing coalition contexts, not one dataset-addition order. Signed cell values and a shared zero-centered scale show magnitude and sign. Gray cells are self-target or otherwise ineligible. Six panels are arranged as model rows and representation columns for readable annotations.

## 07_source_contribution.pdf

- Final PDF: `artigo/figures/manuscript_final/07_source_contribution.pdf`.
- Final PNG: `artigo/figures/manuscript_final/07_source_contribution.png`; rasterized directly from revised vector PDF at300 dpi.
- Old visualization: Unannotated six-panel heatmap.
- New visualization: Annotated heatmap; 3 model rows ×2 representation columns.
- Source analytical tables: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/source_contribution_by_target.parquet`; corresponding CSV files verified exactly against Parquet.
- Columns: removed_source, target, model, representation, delta_f1_mean; row_id and experiment_ids retained in `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.
- Filters: All existing eligible rows; missing grid combinations remain missing.
- Aggregation ALREADY PRESENT: Already saved controlled supplement: same eligible seed pairs, fixed validation/test, full-pool minus source-removed F1. Original sign convention preserved.
- Plotting-only calculations: Existing cell values plotted without rounding; annotations only use signed3 decimals. Symmetric scale [−0.49575353288241103,+0.49575353288241103], zero center. Automatic black/white text maximizes sRGB luminance contrast; missing cells masked gray and unannotated.
- Experiment lineage: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet`; saved source-row IDs and experiment IDs resolve the displayed values.
- Rendering script: `artigo/scripts/revise_manuscript_visuals.py`.
- Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/revise_manuscript_visuals.py`. Does not execute any upstream analysis runner.
- Previous manuscript PDF SHA-256 (replaced, no duplicate retained in manuscript_final): `6a8ca81be033d0064fc599987fbd3237afd17633bc9fd3fe3f89d9c0f3fc5cdd`.
- Current PDF SHA-256: `031ba96c3d69dd051fdac6b7b22c8408b97638a745eed59caeabbe50e2a9ae5a`.
- Current PNG SHA-256: `9d2b94e71771084edd284e083508efefbb0ae976d233b5923d43f0b8f4d260a3`.
- NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION.

Suggested caption: Controlled leave-one-source-out contribution: full-pool F1 minus source-removed F1. Positive values mean the source was beneficial because removing it reduced F1; negative values mean removing the source improved F1. Eligible matched-seed means are annotated; missing combinations remain gray. Six panels use model rows and representation columns.

## 08_selected_score_shift.pdf



- Final PDF: `artigo/figures/manuscript_final/08_selected_score_shift.pdf`.

- Original PDF (copied): `artigo/figures/final/selected_score_shift.pdf`.

- Source Parquet: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/derived/selected_score_histograms.parquet`; corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/derived/selected_score_histograms.csv`.

- Columns: role, label, left, right, fraction, experiment_ids; experiment_ids and row_id for lineage.

- Filters / aggregation: Existing selected_runs/cases first largest_oracle_gap ID; exact singleton experiment_ids filter. Plot existing fraction at (left+right)/2. No scores or predictions recomputed.

- Experiment IDs: in source analytical rows; original artifact mapping: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet`.

- Rendering script: `artigo/scripts/render_final_manuscript_figures.py`.

- Rendering command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/render_final_manuscript_figures.py --overwrite  # backups preserved by renderer; NOT executed in this task`.

- Collection command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.

- Final PDF SHA-256: `4c9bcaa4cc6011f5dcdf27330d26e39269ebfffa6b20f713206c195aaf23a99c`.

- Selection source: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/selected_runs/cases.parquet` (criterion,experiment_ids); selected ID: `SUPP_70be6ed68f2790ad3c5251d9ccfa`.



## 09_cross_dataset_stable_features.pdf



- Final PDF: `artigo/figures/manuscript_final/09_cross_dataset_stable_features.pdf`.

- Original PDF (copied): `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/figures/cross_dataset_stable_features.pdf`.

- Source Parquet: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/top10_cross_dataset_stable_features.parquet`; corresponding CSV: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/tables/top10_cross_dataset_stable_features.csv`.

- Columns: representation, feature, top_k_frequency, rank_mean, importance_mean; experiment_ids and row_id for lineage.

- Filters / aggregation: Historical CatBoost lex64 LODO C. Exactly10/view ordered frequency descending,mean rank ascending,importance descending; saved importance/frequency unchanged.

- Experiment IDs: in source analytical rows; original artifact mapping: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_LINEAGE.parquet`.

- Rendering script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.

- Rendering command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.

- Collection command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.

- Final PDF SHA-256: `6867b5beaf5d880a5d1ed7a97b7433967c592256820e06bac437988fb6c11390`.



## 10_canonicalization_effect.pdf



- Final PDF: `artigo/figures/manuscript_final/10_canonicalization_effect.pdf`.

- Original PDF (copied): `artigo/figures/final/canonicalization_effect.pdf`.

- Source Parquet: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/canonicalization_by_target.parquet`; corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/canonicalization_by_target.csv`.

- Columns: target, model, delta_test_f1_mean; experiment_ids and row_id for lineage.

- Filters / aggregation: Exact existing RAW/CAN pairs; mean paired seed deltas. Zero-centered symmetric scale; losses retained.

- Experiment IDs: in source analytical rows; original artifact mapping: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet`.

- Rendering script: `artigo/scripts/render_final_manuscript_figures.py`.

- Rendering command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/render_final_manuscript_figures.py --overwrite  # backups preserved by renderer; NOT executed in this task`.

- Collection command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.

- Final PDF SHA-256: `d6a1011d2de1fd46b4bec48d41328d30b64f7814ad5b315b3f629a838875b136`.



## 11_controlled_separability.pdf

- Final PDF: `artigo/figures/manuscript_final/11_controlled_separability.pdf`.
- Final PNG: `artigo/figures/manuscript_final/11_controlled_separability.png`; rasterized directly from revised vector PDF at300 dpi.
- Old visualization: Grouped bars with seed-SD error bars.
- New visualization: Paired dumbbell/connected-dot plot, direct RAW/CANONICALIZED labels and saved paired deltas; SD bars omitted.
- Source analytical tables: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/separability.parquet`, `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/separability_paired_deltas.parquet`; corresponding CSV files verified exactly against Parquet.
- Columns: condition, representation, origin_macro_f1_mean, origin_chance_accuracy_uniform_mean, delta_origin_macro_f1_mean; row_id and experiment_ids retained in `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.
- Filters: Conditions all,benign,malicious in that order; RAW and CANONICALIZED; x-axis0..1.
- Aggregation ALREADY PRESENT: Already saved seed means and saved mean paired CANONICALIZED-minus-RAW deltas; no recalculation. Chance copied from existing table.
- Plotting-only calculations: No new metric calculations: coordinates and delta annotations from saved columns; labels rounded to3 decimals. Connect paired means visually; omit SD only from rendering.
- Experiment lineage: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet`; saved source-row IDs and experiment IDs resolve the displayed values.
- Rendering script: `artigo/scripts/revise_manuscript_visuals.py`.
- Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/revise_manuscript_visuals.py`. Does not execute any upstream analysis runner.
- Previous manuscript PDF SHA-256 (replaced, no duplicate retained in manuscript_final): `3adf36df0a2f63628e0e5c42fa5ca2c512a3dd13e54d65c9a9a5f705acf9baf7`.
- Current PDF SHA-256: `f017e53579a8bed7ba98df546406bec707b889fb7cac719f00d86cb0955e36ef`.
- Current PNG SHA-256: `015c1c1f8eb4ac2497bde111c4cb7b7fffb2f8f2a954dc9d7e3f25d773fffbc1`.
- NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION.

Suggested caption: Dataset-origin separability as paired RAW and CANONICALIZED seed means for all samples, benign-only and malicious-only conditions. Labels show both saved means and saved paired Δ (CANONICALIZED minus RAW). The vertical dashed uniform reference is approximately0.143 (1/7; an asymptotic balanced macro-F1 reference, not a finite-sample guarantee). The x-axis spans0–1; seed SD is omitted for clarity.

## Data Sources and Traceability

Per-figure sources, filters, aggregation, rendering scripts and original PDF paths are documented in MANUSCRIPT_FIGURE_TRACEABILITY.md in this directory. The collection and new analysis were performed by `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`, command `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`. Full copy manifest and input/output hashes are in `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/ARTIFACT_MANIFEST.json`. Each figure’s analytical source carries experiment_ids; follow the listed lineage file to original experimental artifacts. Historical source-count/coalition and feature-stability results remain separate from the controlled supplement. No models, predictions, importance metrics or validated source tables were altered.

Visual revision audit: `artigo/figures/visual_revision_audit/VISUAL_REVISION_AUDIT.json`. NO TRAINING; NO PREDICTION REGENERATION; NO METRIC RECOMPUTATION; NO STATISTICAL TEST RECOMPUTATION. The original collection manifest is a historical snapshot; current hashes for revised figures are in this audit and the updated traceability sections.
