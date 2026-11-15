# Manuscript figure captions

## figures/cross_dataset_stable_features

Most stable engineered features across unseen targets; CatBoost historical LODO C. Top-10 frequency = proportion of eligible LODO CatBoost models in which the feature appears among the ten highest-ranked engineered features. Ranking by frequency, then mean rank, then importance; bars only frequency; no causal claim.

Data: ["tables/top10_cross_dataset_stable_features.csv"]. Output: figures/cross_dataset_stable_features.pdf and .png.

## figures/generalization_vs_source_count

Each target receives equal weight after seed and coalition aggregation. Lines/bands: seven-target macro mean and IQR of target means at k=1..5. Detached hollow k=6: five-target macro mean with IQR across those targets; not connected because target cohort changes. Source count is effective train+validation pool, not optimizer-only files nor independent family count.

Data: ["tables/performance_by_source_count_macro.csv"]. Output: figures/generalization_vs_source_count.pdf and .png.

## figures/marginal_gain_per_added_source

Distribution across nested effective coalition edges after matched-seed averaging; same target/model/view before/after. Boxes q25/median/q75, whiskers 1.5 IQR, all fliers shown. Edges are not independent targets. Changes may include validation/early-stopping/threshold selection; 5→6 lacks the two site targets. Zero line explicit; numerical sign tolerance1e-9 is not practical equivalence.

Data: ["tables/marginal_source_additions.csv"]. Output: figures/marginal_gain_per_added_source.pdf and .png.

## Data Sources and Traceability

Script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.
Inputs and output SHA-256: `ARTIFACT_MANIFEST.json`. Exact filters, columns and aggregation recipes: `TRACEABILITY.csv`.
Primary analytical input: `artigo/analise_resultados_tcc/_global/master_results.parquet`; only usable historical contribution/lex64/nonpilot models and RAW/CANONICALIZED, plus historical LODO C CatBoost IDs for features. No supplemental results are mixed in.
Every output table has row_id and experiment_ids. Resolve IDs with `SOURCE_LINEAGE.parquet`, which preserves original metric, feature-importance, manifest, predictions and score paths without opening those files. Nested-edge tables also expose before/after IDs; per-seed matches are in `derived/matched_source_additions_per_seed.parquet`. Formatting-only feature snapshot and original input-row IDs are preserved.
Seeds: equal weight within exact effective coalition; nested edges use only identical seeds. Coalition distribution: equal distinct effective pools after verified duplicate alias collapse. Target macro: equal outer-target means, not weighting by number of coalitions. Marginal effects: after minus before of saved F1/MCC/AP; sample SD uses ddof=1; quartiles use linear interpolation; |delta|≤1e-9 is numerical zero, not practical equivalence. No hypothesis tests, predictions, training or importance recomputation.
Generated tables/figures, source paths/row filters and formulas are listed in TRACEABILITY.csv. Exact source-value audits are in tables/derivation_audit.csv. Scientific coverage checks: tables/coalition_coverage.csv and tables/marginal_edge_coverage.csv. Unavailable or unsupported conclusions are explicitly NOT VERIFIED FOR PAPER.
