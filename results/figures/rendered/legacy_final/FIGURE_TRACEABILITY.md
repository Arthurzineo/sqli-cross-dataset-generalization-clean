# Final manuscript figure traceability

Visual formatting only. No experiments, metrics, statistical tests, model outputs, seed aggregation, or histograms were recomputed. Only the saved analytical tables were read. CSV values parsed with float_precision=round_trip match their Parquet counterparts exactly. Matplotlib artist data are checked against those values before any figure is saved.

Original plotting recipe: `artigo/scripts/analyze_supplemental_results.py`, `Analysis.plots`; not imported or executed. Source PDF/PNG files remain untouched. The existing representative score run, all seed means/SDs, heatmap bounds, missing cells and chance reference are preserved. Annotation precision remains three decimals; plotted values are never rounded.

Format: vector PDF (embedded TrueType DejaVu Sans, no rasterized heatmaps), PNG at 300 dpi; 174 mm full two-column width, 7.5–9 pt labels. Do not shrink these multi-panel figures to single-column width. Okabe–Ito blue/orange distinguish representations/classes; RdBu is a diverging zero-centered scale. Model labels: Logistic Regression, CatBoost, MLP. Representations: RAW, CANONICALIZED. Captions belong in the manuscript.

**Status:** Rendered and verified.

## Data Sources and Traceability

Exactly seven existing CSV/Parquet table pairs are read (six data tables and one existing selection table). Full paths, columns, filters, hashes and row counts are below and in `FIGURE_VALIDATION.json`. Each plotted source value, original row_id and experiment_ids are recorded in `PLOTTED_VALUES.csv`; float64_hex preserves the exact binary value. No new means, SDs, thresholds, metrics or tests were computed.

Script: `artigo/scripts/render_final_manuscript_figures.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/render_final_manuscript_figures.py`. Script SHA-256: `9b3e3eef740e9b3401016a60ba939c030ad6a3790c8b36467435cb56b4a4460e`.

Seed aggregation is inherited unchanged from each existing analytical table. All figures use saved seed means; controlled_separability additionally uses the saved seed SD, not a confidence interval. Score fractions were already computed by the original analysis; the sole plotting coordinate formula is x=(left+right)/2 for those existing bins.

## lodo_by_target

- Source table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_by_target.parquet`.
- Corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_by_target.csv`.
- Columns: `target`, `model`, `representation`, `test_f1_mean`, `row_id`, `experiment_ids`.
- Filters: All saved rows; model/representation panels subset the rows without aggregation; targets in sorted order.
- Script: `artigo/scripts/render_final_manuscript_figures.py`; original recipe: `Analysis.plots` in `artigo/scripts/analyze_supplemental_results.py`.
- Output PDF: `artigo/figures/final/lodo_by_target.pdf`.
- Output PNG: `artigo/figures/final/lodo_by_target.png`.
- Source .parquet SHA-256: `cce36a0673e88e7e06fa2545b2e227fa45ab1230c0f53619c05feb9225eef8af`.
- Source .csv SHA-256: `700594756aecaf04f5a375db67a37cb718cd0ddfde29850b33bee59fdcb3e644`.
- Output .pdf SHA-256: `5d047b90447e777b34ef7b81545a4308397f4195f174f1368a5dd78ac4bc74ef`.
- Output .png SHA-256: `356f98f0d8b0044172d7df48e742cc717b087ed4205a2a082d5aea0c3a2065d6`.

## id_ood_common_test_gap

- Source table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/id_ood_same_test.parquet`.
- Corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/id_ood_same_test.csv`.
- Columns: `target`, `model`, `representation`, `gap_f1_mean`, `row_id`, `experiment_ids`.
- Filters: All saved rows; model/representation panels subset the rows without aggregation; targets in sorted order.
- Script: `artigo/scripts/render_final_manuscript_figures.py`; original recipe: `Analysis.plots` in `artigo/scripts/analyze_supplemental_results.py`.
- Output PDF: `artigo/figures/final/id_ood_common_test_gap.pdf`.
- Output PNG: `artigo/figures/final/id_ood_common_test_gap.png`.
- Source .parquet SHA-256: `b1bfc08ba943c8b4230cf92a0f6710437849fa66fb0164466c96648b81ee46d0`.
- Source .csv SHA-256: `1ef3161c688d808d6c1d2c29965ebc97ad38473b1a777c3e4903cb52cb20164e`.
- Output .pdf SHA-256: `2428c52c6bdc944ad317a25b875da622dd437fe5efea7b2e96812da44ee0faa3`.
- Output .png SHA-256: `c7f4ccaaf19b82fdb5033ac1e3a6c7b1ebf7ba572ce80b8fbd95b105f9679a60`.

## source_contribution

- Source table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/source_contribution_by_target.parquet`.
- Corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/source_contribution_by_target.csv`.
- Columns: `target`, `removed_source`, `model`, `representation`, `delta_f1_mean`, `row_id`, `experiment_ids`.
- Filters: All saved rows; model/representation panels subset the rows without aggregation; targets in sorted order.
- Script: `artigo/scripts/render_final_manuscript_figures.py`; original recipe: `Analysis.plots` in `artigo/scripts/analyze_supplemental_results.py`.
- Output PDF: `artigo/figures/final/source_contribution.pdf`.
- Output PNG: `artigo/figures/final/source_contribution.png`.
- Sign: **full-pool F1 minus source-removed F1**. Shared symmetric color bounds use the existing maximum absolute delta; zero is the center. Gray cells remain missing/ineligible, never zero-filled.
- Source .parquet SHA-256: `6dddb8a33199cf41b50c16225251368cd8318a956a6dceca6db06cfdab54e9ba`.
- Source .csv SHA-256: `c5e3c3d5617774a3a88d267ae1a4daf1de2ab61191c487b0544f0dd7235d1050`.
- Output .pdf SHA-256: `6a8ca81be033d0064fc599987fbd3237afd17633bc9fd3fe3f89d9c0f3fc5cdd`.
- Output .png SHA-256: `8b34615e93764b7c5b74e0a4790777cea30f4cc99a4f335e9c583433d8e99e0b`.

## selected_score_shift

- Source table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/derived/selected_score_histograms.parquet`.
- Corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/derived/selected_score_histograms.csv`.
- Columns: `role`, `label`, `left`, `right`, `fraction`, `row_id`, `experiment_ids`.
- Filters: experiment_ids == json.dumps([first ID in first selected_runs/cases row with criterion == largest_oracle_gap]); SUPP_70be6ed68f2790ad3c5251d9ccfa
- Script: `artigo/scripts/render_final_manuscript_figures.py`; original recipe: `Analysis.plots` in `artigo/scripts/analyze_supplemental_results.py`.
- Output PDF: `artigo/figures/final/selected_score_shift.pdf`.
- Output PNG: `artigo/figures/final/selected_score_shift.png`.
- Selection table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/selected_runs/cases.parquet`; columns criterion, experiment_ids, row_id. Same saved selection, no reselection or score loading.
- Selected experiment ID: `SUPP_70be6ed68f2790ad3c5251d9ccfa`.
- Source .parquet SHA-256: `617655ed821685314616e5ecb2937f38c27efb80ca7efa095ef05a05e3c1f5a2`.
- Source .csv SHA-256: `6e819b88907829609bafd395a55895aaa8b41e343c179e4dd948f020582a4b7a`.
- Output .pdf SHA-256: `4c9bcaa4cc6011f5dcdf27330d26e39269ebfffa6b20f713206c195aaf23a99c`.
- Output .png SHA-256: `e73b6ac7033651359c7ce24ad2dc6e6daae27655f9bb74dad80d262d4b9518ba`.

## canonicalization_effect

- Source table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/canonicalization_by_target.parquet`.
- Corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/canonicalization_by_target.csv`.
- Columns: `target`, `model`, `delta_test_f1_mean`, `row_id`, `experiment_ids`.
- Filters: All saved rows; model/representation panels subset the rows without aggregation; targets in sorted order.
- Script: `artigo/scripts/render_final_manuscript_figures.py`; original recipe: `Analysis.plots` in `artigo/scripts/analyze_supplemental_results.py`.
- Output PDF: `artigo/figures/final/canonicalization_effect.pdf`.
- Output PNG: `artigo/figures/final/canonicalization_effect.png`.
- Source .parquet SHA-256: `9e1bd4a6e20a28877099b7c0071bc65a7161cc0ce5a6bf326ddb73ac6383b15b`.
- Source .csv SHA-256: `0650831814fb2e3b79b7d277f2f13fef63c1d2b09893fe3424bc48cc9f6b0f25`.
- Output .pdf SHA-256: `d6a1011d2de1fd46b4bec48d41328d30b64f7814ad5b315b3f629a838875b136`.
- Output .png SHA-256: `14ccd25ced5c3870f27d3ca262413d52758a51280cf26c0bc217401945d21d07`.

## controlled_separability

- Source table: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/separability.parquet`.
- Corresponding CSV: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/separability.csv`.
- Columns: `condition`, `representation`, `origin_macro_f1_mean`, `origin_macro_f1_std`, `origin_chance_accuracy_uniform_mean`, `row_id`, `experiment_ids`.
- Filters: All saved rows; model/representation panels subset the rows without aggregation; targets in sorted order.
- Script: `artigo/scripts/render_final_manuscript_figures.py`; original recipe: `Analysis.plots` in `artigo/scripts/analyze_supplemental_results.py`.
- Output PDF: `artigo/figures/final/controlled_separability.pdf`.
- Output PNG: `artigo/figures/final/controlled_separability.png`.
- Chance-reference line is copied from origin_chance_accuracy_uniform_mean.iloc[0]; label retains the original asymptotic-reference qualification.
- Source .parquet SHA-256: `50b92254db7648d7cee6c3786d5103d7adea190cf7b96479cfc20a6aa2d2a59f`.
- Source .csv SHA-256: `1b75f6be07faeab8f45b6885f6bdf6efb5b03d69237279022b80c9e466415612`.
- Output .pdf SHA-256: `3adf36df0a2f63628e0e5c42fa5ca2c512a3dd13e54d65c9a9a5f705acf9baf7`.
- Output .png SHA-256: `fd9c7db6e1b8aa2a3eb5d935e4ac45d5539f912010ee63679d53257c3f96e418`.

