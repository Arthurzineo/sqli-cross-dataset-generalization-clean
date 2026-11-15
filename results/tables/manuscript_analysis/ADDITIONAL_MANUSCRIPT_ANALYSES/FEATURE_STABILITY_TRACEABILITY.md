# Cross-dataset stable features — traceability



Source CSV: `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stable_features.csv`. Requested historical Parquet counterpart exists: **False**.

The absent historical Parquet was not replaced by the supplemental table with the same basename. `derived/historical_stable_features_snapshot.parquet` is an explicitly new format-only copy of the historical CSV, not an original counterpart.

Filter: historical lodo_C_complete, CatBoost, lex64, RAW/CANONICALIZED, eligible completed runs. Saved source table already contains aggregation. The selected statistics are copied exactly, not recalculated. Ranking: Top-10 frequency descending; mean rank ascending; mean importance descending; feature-name last tie-break. Exactly ten features per view.

Top-10 frequency = proportion of eligible LODO CatBoost models in which the feature appears among the ten highest-ranked engineered features. The original routine used saved average rank ≤10; its saved ranks were checked to select exactly ten in all eligible models (no boundary-tie ambiguity here).

Eligibility: 70 models total, 5 seeds, 7 targets. Each view has 35 models. Source importance units are CatBoost native importance points, not causal effects. See copied n_runs/n_seeds in the output table.

Output table: `tables/top10_cross_dataset_stable_features.csv` and .parquet. Figure: `figures/cross_dataset_stable_features.pdf` and 300-dpi .png. All experiment IDs are in the table; original sources resolve through SOURCE_LINEAGE.parquet. Output hashes are in ARTIFACT_MANIFEST.json.

Terminology: **most stable features across unseen targets**. These are not demonstrated best transferable features, and no causal ranking is claimed.
## Data Sources and Traceability

Script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.
Inputs and output SHA-256: `ARTIFACT_MANIFEST.json`. Exact filters, columns and aggregation recipes: `TRACEABILITY.csv`.
Primary analytical input: `artigo/analise_resultados_tcc/_global/master_results.parquet`; only usable historical contribution/lex64/nonpilot models and RAW/CANONICALIZED, plus historical LODO C CatBoost IDs for features. No supplemental results are mixed in.
Every output table has row_id and experiment_ids. Resolve IDs with `SOURCE_LINEAGE.parquet`, which preserves original metric, feature-importance, manifest, predictions and score paths without opening those files. Nested-edge tables also expose before/after IDs; per-seed matches are in `derived/matched_source_additions_per_seed.parquet`. Formatting-only feature snapshot and original input-row IDs are preserved.
Seeds: equal weight within exact effective coalition; nested edges use only identical seeds. Coalition distribution: equal distinct effective pools after verified duplicate alias collapse. Target macro: equal outer-target means, not weighting by number of coalitions. Marginal effects: after minus before of saved F1/MCC/AP; sample SD uses ddof=1; quartiles use linear interpolation; |delta|≤1e-9 is numerical zero, not practical equivalence. No hypothesis tests, predictions, training or importance recomputation.
Generated tables/figures, source paths/row filters and formulas are listed in TRACEABILITY.csv. Exact source-value audits are in tables/derivation_audit.csv. Scientific coverage checks: tables/coalition_coverage.csv and tables/marginal_edge_coverage.csv. Unavailable or unsupported conclusions are explicitly NOT VERIFIED FOR PAPER.
