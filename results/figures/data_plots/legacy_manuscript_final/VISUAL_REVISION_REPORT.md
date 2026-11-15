# Final visual revision report

NO TRAINING · NO PREDICTION REGENERATION · NO METRIC RECOMPUTATION · NO STATISTICAL TEST RECOMPUTATION

All analytical tables and saved values remained unchanged. Revised figures replaced the same LaTeX-facing filenames in manuscript_final. Existing revised-name PNGs are replaced in place; no _v2/_new/_updated files or old/new PDF duplicates are retained in that directory. Upstream historical analytical figures were not modified.

## Changed figures

- `04_marginal_gain_per_added_source.pdf` and `04_marginal_gain_per_added_source.png`: Edge-distribution boxplots → Target-macro connected points with signed values and aligned negative-addition percentage strips.
- `05_marginal_gain_by_source_and_pool_size.pdf` and `05_marginal_gain_by_source_and_pool_size.png`: Unannotated six-panel heatmap → Annotated heatmap; 2 representation rows ×3 model columns; four transitions.
- `06_marginal_gain_by_source_and_target.pdf` and `06_marginal_gain_by_source_and_target.png`: Unannotated six-panel heatmap → Annotated heatmap; 3 model rows ×2 representation columns.
- `07_source_contribution.pdf` and `07_source_contribution.png`: Unannotated six-panel heatmap → Annotated heatmap; 3 model rows ×2 representation columns.
- `11_controlled_separability.pdf` and `11_controlled_separability.png`: Grouped bars with seed-SD error bars → Paired dumbbell/connected-dot plot, direct RAW/CANONICALIZED labels and saved paired deltas; SD bars omitted.

## Intentionally unchanged

01_lodo_by_target.pdf and10_canonicalization_effect.pdf already have readable numeric annotations and were checked without rerendering. Non-heatmaps02,03,08,09 were intentionally left unchanged; their SHA-256 values match the pre-revision files.

## Numerical and visual checks

- CSV/Parquet source values agree exactly; Matplotlib data arrays match the saved source values before label formatting.
- Three decimals affect annotation text only. No value was rounded before plotting. Negative percentages use the saved target-macro fraction, multiplied by100 only for display.
- Figure11 deltas come directly from the existing separability_paired_deltas table; no new metric or paired-difference aggregation was computed.
- Heatmap text contrast maximizes black/white contrast using sRGB relative luminance; contrast ≥4.5. Missing/ineligible cells remain gray and unannotated. Scales remain symmetric and exactly zero-centered.
- Numeric labels are checked against cell borders and canvas bounds, and against other annotations for overlap.
- Revised PDFs contain vector graphics and embedded TrueType fonts. Each was rasterized with pdftoppm at300 dpi to produce its delivered PNG.
- PDF-to-PNG visual inspection: CONFIRMED for all five revised figures.

## Data Sources and Traceability

Per-figure old/new type, source table, columns, filters, existing aggregation, plotting-only operations and PDF/PNG hashes: MANUSCRIPT_FIGURE_TRACEABILITY.md. Updated captions/LaTeX paths: LATEX_FIGURE_INDEX.md.
Script: `artigo/scripts/revise_manuscript_visuals.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/revise_manuscript_visuals.py`. Audit: `artigo/figures/visual_revision_audit/VISUAL_REVISION_AUDIT.json`. Exact plotted source values, hex-float values, source row IDs and experiment IDs: `artigo/figures/visual_revision_audit/PLOTTED_SOURCE_VALUES.csv`.
Figure04 filters n_sources_before=1..4, all seven targets; figure05 likewise omits5→6. Figure06/07 use all existing eligible cells. Figure11 uses all three saved conditions. No seeds, targets, coalition contexts, SDs, thresholds, feature importances or statistical tests were reaggregated. Source SHA-256 values were checked unchanged before installation.
The PNGs and the two updated figures04/11 supersede only their manuscript renderings; all prior scientific source tables remain valid. The directory now intentionally contains the PNGs and revision report explicitly requested in this revision, in addition to its existing PDFs and documentation.
