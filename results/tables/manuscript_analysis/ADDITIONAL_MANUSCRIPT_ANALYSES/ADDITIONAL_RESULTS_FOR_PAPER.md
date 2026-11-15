# Additional manuscript results



Descriptive re-use of completed historical results only. No fit, importance, model prediction or statistical test was recomputed. F1/MCC/AP originals remain unchanged; this analysis computes only requested summaries and nested differences.



## Scope and scientific checks



Eligible completed historical source-composition runs: **13170**. After collapsing identical requested aliases at the same seed: **11310** effective coalition/seed conditions; **2262** seed-aggregated target/model/view/coalition conditions. Source: `derived/effective_coalition_seed_results.csv` and `derived/seed_aggregated_coalitions.csv` (all rows).

Targets: artificial_sqli, csic, ecml, proprio, site_cooking, site_sqli, srbh; models: Logistic Regression, CatBoost, MLP; RAW/CANONICALIZED; seeds: [np.int64(42), np.int64(123), np.int64(1337), np.int64(2026), np.int64(9001)]. Seed coverage and absence are recorded, never filled.

**Meaning of S:** the effective development pool (union of training and validation sources), after the historical target-family exclusion. This is the coalition specified to the training procedure, NOT necessarily the files seen by the optimizer. `n_actual_training_sources_min/max` and per-seed validation/training lists expose the distinction. A literal optimizer-only source-diversity effect independent of validation: NOT VERIFIED FOR PAPER.

site_cooking and site_sqli share site_lab. When either is the target, the other is purged, so only five source files are eligible. For the other targets six source files include these two related sources; six files do not mean six independent families. Requested aliases have exactly identical saved metrics, threshold and split-count metadata; they are counted once with all IDs preserved. Seven outer targets include only six provenance families. No inferential p-values are produced.

Coverage per source-count level (take each target/model/view separately; counts vary combinatorially):

| target | n_sources | expected_coalitions | observed_coalitions | missing_seed_models | status |
|---|---|---|---|---|---|
| artificial_sqli | 1 | 6 | 6 | 0 | complete |
| artificial_sqli | 2 | 15 | 15 | 0 | complete |
| artificial_sqli | 3 | 20 | 20 | 0 | complete |
| artificial_sqli | 4 | 15 | 15 | 0 | complete |
| artificial_sqli | 5 | 6 | 6 | 0 | complete |
| artificial_sqli | 6 | 1 | 1 | 0 | complete |
| csic | 1 | 6 | 6 | 0 | complete |
| csic | 2 | 15 | 15 | 0 | complete |
| csic | 3 | 20 | 20 | 0 | complete |
| csic | 4 | 15 | 15 | 0 | complete |
| csic | 5 | 6 | 6 | 0 | complete |
| csic | 6 | 1 | 1 | 0 | complete |
| ecml | 1 | 6 | 6 | 0 | complete |
| ecml | 2 | 15 | 15 | 0 | complete |
| ecml | 3 | 20 | 20 | 0 | complete |
| ecml | 4 | 15 | 15 | 0 | complete |
| ecml | 5 | 6 | 6 | 0 | complete |
| ecml | 6 | 1 | 1 | 0 | complete |
| proprio | 1 | 6 | 6 | 0 | complete |
| proprio | 2 | 15 | 15 | 0 | complete |
| proprio | 3 | 20 | 20 | 0 | complete |
| proprio | 4 | 15 | 15 | 0 | complete |
| proprio | 5 | 6 | 6 | 0 | complete |
| proprio | 6 | 1 | 1 | 0 | complete |
| site_cooking | 1 | 5 | 5 | 0 | complete |
| site_cooking | 2 | 10 | 10 | 0 | complete |
| site_cooking | 3 | 10 | 10 | 0 | complete |
| site_cooking | 4 | 5 | 5 | 0 | complete |
| site_cooking | 5 | 1 | 1 | 0 | complete |
| site_cooking | 6 | 0 | 0 | 0 | structurally_unavailable |
| site_sqli | 1 | 5 | 5 | 0 | complete |
| site_sqli | 2 | 10 | 10 | 0 | complete |
| site_sqli | 3 | 10 | 10 | 0 | complete |
| site_sqli | 4 | 5 | 5 | 0 | complete |
| site_sqli | 5 | 1 | 1 | 0 | complete |
| site_sqli | 6 | 0 | 0 | 0 | structurally_unavailable |
| srbh | 1 | 6 | 6 | 0 | complete |
| srbh | 2 | 15 | 15 | 0 | complete |
| srbh | 3 | 20 | 20 | 0 | complete |
| srbh | 4 | 15 | 15 | 0 | complete |
| srbh | 5 | 6 | 6 | 0 | complete |
| srbh | 6 | 1 | 1 | 0 | complete |

Source: `tables/coalition_coverage.csv`, filter model=catboost, representation=RAW; all model/view checks in full table. Structural absence at k=6 for site targets is NOT an execution failure. `tables/missing_coalition_seed_conditions.csv` enumerates any genuine missing seeds.

Nested edges: **6480**, using **32400** matched-seed pairs. All edges match target/model/representation and saved configuration ID; no unpaired fallback. Historical config IDs were derived from current configuration, not immutable per-run snapshots. `tables/marginal_edge_coverage.csv` gives exact expected/observed counts.

Validation source changes in **10746/32400** seed pairs; the added source is in optimizer training in **21954/32400** pairs. These counts are read from `derived/matched_source_additions_per_seed.csv` (boolean filters). Marginal gains measure the whole historical procedure, not a causal isolated addition of training examples.



## 1. How does OOD F1 change as source-pool size increases?



| model | representation | n_sources | n_targets | f1_mean | f1_q25 | f1_q75 |
|---|---|---|---|---|---|---|
| catboost | CANONICALIZED | 1 | 7 | 0.720244 | 0.679537 | 0.744871 |
| catboost | CANONICALIZED | 2 | 7 | 0.779983 | 0.740834 | 0.797985 |
| catboost | CANONICALIZED | 3 | 7 | 0.820308 | 0.774178 | 0.857667 |
| catboost | CANONICALIZED | 4 | 7 | 0.848570 | 0.793493 | 0.894840 |
| catboost | CANONICALIZED | 5 | 7 | 0.873385 | 0.856945 | 0.896861 |
| catboost | CANONICALIZED | 6 | 5 | 0.887740 | 0.873127 | 0.940107 |
| catboost | RAW | 1 | 7 | 0.693771 | 0.650566 | 0.712357 |
| catboost | RAW | 2 | 7 | 0.716631 | 0.701504 | 0.731920 |
| catboost | RAW | 3 | 7 | 0.713625 | 0.692984 | 0.743574 |
| catboost | RAW | 4 | 7 | 0.744034 | 0.692189 | 0.800961 |
| catboost | RAW | 5 | 7 | 0.760911 | 0.710882 | 0.811081 |
| catboost | RAW | 6 | 5 | 0.752420 | 0.721472 | 0.803198 |
| logistic | CANONICALIZED | 1 | 7 | 0.758939 | 0.682372 | 0.812907 |
| logistic | CANONICALIZED | 2 | 7 | 0.772781 | 0.718430 | 0.817360 |
| logistic | CANONICALIZED | 3 | 7 | 0.813541 | 0.783863 | 0.848653 |
| logistic | CANONICALIZED | 4 | 7 | 0.839814 | 0.810298 | 0.872790 |
| logistic | CANONICALIZED | 5 | 7 | 0.851426 | 0.828007 | 0.882946 |
| logistic | CANONICALIZED | 6 | 5 | 0.845835 | 0.804328 | 0.917066 |
| logistic | RAW | 1 | 7 | 0.668210 | 0.613164 | 0.716055 |
| logistic | RAW | 2 | 7 | 0.693425 | 0.669016 | 0.720518 |
| logistic | RAW | 3 | 7 | 0.724344 | 0.688168 | 0.783544 |
| logistic | RAW | 4 | 7 | 0.728258 | 0.680472 | 0.798174 |
| logistic | RAW | 5 | 7 | 0.731485 | 0.679824 | 0.806532 |
| logistic | RAW | 6 | 5 | 0.744382 | 0.743503 | 0.781135 |
| mlp | CANONICALIZED | 1 | 7 | 0.769347 | 0.720384 | 0.812036 |
| mlp | CANONICALIZED | 2 | 7 | 0.764968 | 0.723607 | 0.813376 |
| mlp | CANONICALIZED | 3 | 7 | 0.804598 | 0.761957 | 0.837981 |
| mlp | CANONICALIZED | 4 | 7 | 0.842780 | 0.813735 | 0.877921 |
| mlp | CANONICALIZED | 5 | 7 | 0.872822 | 0.857989 | 0.908368 |
| mlp | CANONICALIZED | 6 | 5 | 0.871731 | 0.822240 | 0.944519 |
| mlp | RAW | 1 | 7 | 0.663015 | 0.608651 | 0.701835 |
| mlp | RAW | 2 | 7 | 0.674229 | 0.651453 | 0.690988 |
| mlp | RAW | 3 | 7 | 0.745928 | 0.712325 | 0.780822 |
| mlp | RAW | 4 | 7 | 0.778486 | 0.736838 | 0.828988 |
| mlp | RAW | 5 | 7 | 0.801256 | 0.765190 | 0.849485 |
| mlp | RAW | 6 | 5 | 0.804393 | 0.748191 | 0.859971 |

Source: `tables/performance_by_source_count_macro.csv`; each displayed row identifies its filter. **Each target receives equal weight after seed and coalition aggregation.** Band: IQR across target coalition-means, not confidence interval. Use seven-target results for k=1..5. At k=6 only five targets remain; never attribute the cross-cohort difference between k=5 and k=6 solely to source count.

Fixed common-target sensitivity uses artificial_sqli, csic, ecml, proprio, srbh:

| model | representation | n_sources | n_targets | f1_mean |
|---|---|---|---|---|
| catboost | CANONICALIZED | 1 | 5 | 0.748990 |
| catboost | CANONICALIZED | 6 | 5 | 0.887740 |
| catboost | RAW | 1 | 5 | 0.686962 |
| catboost | RAW | 6 | 5 | 0.752420 |
| logistic | CANONICALIZED | 1 | 5 | 0.791802 |
| logistic | CANONICALIZED | 6 | 5 | 0.845835 |
| logistic | RAW | 1 | 5 | 0.651767 |
| logistic | RAW | 6 | 5 | 0.744382 |
| mlp | CANONICALIZED | 1 | 5 | 0.794003 |
| mlp | CANONICALIZED | 6 | 5 | 0.871731 |
| mlp | RAW | 1 | 5 | 0.647487 |
| mlp | RAW | 6 | 5 | 0.804393 |

Source: `tables/performance_by_source_count_macro_common_targets.csv`, n_sources in {1,6}. Intermediate levels are also available. This preserves identical targets across the whole range, without dropping any result from the main available-target tables.



## 2–3. Diminishing marginal benefit and frequency of negative additions



| model | representation | n_sources_before | n_additions | mean_delta_f1 | median_delta_f1 | fraction_negative | fraction_positive | fraction_zero |
|---|---|---|---|---|---|---|---|---|
| catboost | CANONICALIZED | 1 | 190 | 0.057382 | 0.007437 | 0.447368 | 0.552632 | 0.000000 |
| catboost | CANONICALIZED | 2 | 360 | 0.045345 | 0.029248 | 0.302778 | 0.697222 | 0.000000 |
| catboost | CANONICALIZED | 3 | 340 | 0.023686 | 0.007970 | 0.405882 | 0.594118 | 0.000000 |
| catboost | CANONICALIZED | 4 | 160 | 0.007210 | -0.001147 | 0.525000 | 0.475000 | 0.000000 |
| catboost | CANONICALIZED | 5 | 30 | 0.012829 | 0.003742 | 0.366667 | 0.633333 | 0.000000 |
| catboost | RAW | 1 | 190 | 0.024148 | -0.005741 | 0.515789 | 0.484211 | 0.000000 |
| catboost | RAW | 2 | 360 | -0.007201 | -0.000733 | 0.505556 | 0.494444 | 0.000000 |
| catboost | RAW | 3 | 340 | 0.021462 | 0.022738 | 0.402941 | 0.597059 | 0.000000 |
| catboost | RAW | 4 | 160 | 0.016288 | 0.004810 | 0.462500 | 0.537500 | 0.000000 |
| catboost | RAW | 5 | 30 | 0.019453 | -0.000783 | 0.500000 | 0.500000 | 0.000000 |
| logistic | CANONICALIZED | 1 | 190 | 0.011189 | 0.012734 | 0.452632 | 0.547368 | 0.000000 |
| logistic | CANONICALIZED | 2 | 360 | 0.036213 | 0.034154 | 0.308333 | 0.691667 | 0.000000 |
| logistic | CANONICALIZED | 3 | 340 | 0.020990 | 0.016360 | 0.376471 | 0.623529 | 0.000000 |
| logistic | CANONICALIZED | 4 | 160 | 0.006328 | 0.005155 | 0.475000 | 0.525000 | 0.000000 |
| logistic | CANONICALIZED | 5 | 30 | -0.001717 | 0.001933 | 0.500000 | 0.500000 | 0.000000 |
| logistic | RAW | 1 | 190 | 0.030161 | 0.018806 | 0.447368 | 0.552632 | 0.000000 |
| logistic | RAW | 2 | 360 | 0.032812 | 0.022087 | 0.383333 | 0.611111 | 0.005556 |
| logistic | RAW | 3 | 340 | 0.001852 | 0.004853 | 0.458824 | 0.541176 | 0.000000 |
| logistic | RAW | 4 | 160 | 0.007011 | 0.003808 | 0.456250 | 0.543750 | 0.000000 |
| logistic | RAW | 5 | 30 | 0.004664 | -0.000821 | 0.533333 | 0.466667 | 0.000000 |
| mlp | CANONICALIZED | 1 | 190 | -0.003416 | 0.012097 | 0.473684 | 0.526316 | 0.000000 |
| mlp | CANONICALIZED | 2 | 360 | 0.036028 | 0.030968 | 0.325000 | 0.675000 | 0.000000 |
| mlp | CANONICALIZED | 3 | 340 | 0.033446 | 0.021834 | 0.338235 | 0.661765 | 0.000000 |
| mlp | CANONICALIZED | 4 | 160 | 0.017217 | 0.010578 | 0.412500 | 0.587500 | 0.000000 |
| mlp | CANONICALIZED | 5 | 30 | 0.003707 | 0.011144 | 0.466667 | 0.533333 | 0.000000 |
| mlp | RAW | 1 | 190 | 0.018529 | -0.002919 | 0.515789 | 0.484211 | 0.000000 |
| mlp | RAW | 2 | 360 | 0.072537 | 0.052185 | 0.272222 | 0.727778 | 0.000000 |
| mlp | RAW | 3 | 340 | 0.032081 | 0.015238 | 0.361765 | 0.638235 | 0.000000 |
| mlp | RAW | 4 | 160 | 0.018258 | 0.009852 | 0.431250 | 0.568750 | 0.000000 |
| mlp | RAW | 5 | 30 | -0.004556 | -0.005328 | 0.533333 | 0.466667 | 0.000000 |

Source: `tables/marginal_gain_by_pool_size.csv`; rows match model/view/k. These means and fractions describe nested EDGES after matched-seed aggregation, not independent target observations. Equal-target counterparts are in `tables/marginal_gain_by_pool_size_target_macro.csv`.

| model | representation | n_sources_before | n_targets | target_macro_mean_delta_f1 | target_macro_fraction_negative |
|---|---|---|---|---|---|
| catboost | CANONICALIZED | 1 | 7 | 0.059738 | 0.440476 |
| catboost | CANONICALIZED | 2 | 7 | 0.040325 | 0.333333 |
| catboost | CANONICALIZED | 3 | 7 | 0.028262 | 0.395238 |
| catboost | CANONICALIZED | 4 | 7 | 0.024814 | 0.495238 |
| catboost | CANONICALIZED | 5 | 5 | 0.012829 | 0.366667 |
| catboost | RAW | 1 | 7 | 0.022860 | 0.519048 |
| catboost | RAW | 2 | 7 | -0.003006 | 0.502381 |
| catboost | RAW | 3 | 7 | 0.030409 | 0.359524 |
| catboost | RAW | 4 | 7 | 0.016877 | 0.447619 |
| catboost | RAW | 5 | 5 | 0.019453 | 0.500000 |
| logistic | CANONICALIZED | 1 | 7 | 0.013842 | 0.442857 |
| logistic | CANONICALIZED | 2 | 7 | 0.040760 | 0.292857 |
| logistic | CANONICALIZED | 3 | 7 | 0.026273 | 0.342857 |
| logistic | CANONICALIZED | 4 | 7 | 0.011612 | 0.504762 |
| logistic | CANONICALIZED | 5 | 5 | -0.001717 | 0.500000 |
| logistic | RAW | 1 | 7 | 0.025215 | 0.447619 |
| logistic | RAW | 2 | 7 | 0.030919 | 0.402381 |
| logistic | RAW | 3 | 7 | 0.003914 | 0.442857 |
| logistic | RAW | 4 | 7 | 0.003227 | 0.419048 |
| logistic | RAW | 5 | 5 | 0.004664 | 0.533333 |
| mlp | CANONICALIZED | 1 | 7 | -0.004379 | 0.476190 |
| mlp | CANONICALIZED | 2 | 7 | 0.039630 | 0.302381 |
| mlp | CANONICALIZED | 3 | 7 | 0.038182 | 0.321429 |
| mlp | CANONICALIZED | 4 | 7 | 0.030042 | 0.361905 |
| mlp | CANONICALIZED | 5 | 5 | 0.003707 | 0.466667 |
| mlp | RAW | 1 | 7 | 0.011214 | 0.528571 |
| mlp | RAW | 2 | 7 | 0.071699 | 0.252381 |
| mlp | RAW | 3 | 7 | 0.032557 | 0.350000 |
| mlp | RAW | 4 | 7 | 0.022770 | 0.447619 |
| mlp | RAW | 5 | 5 | -0.004556 | 0.533333 |

Source: `tables/marginal_gain_by_pool_size_target_macro.csv`; row filters are the displayed keys. Compare k=1..4 within seven targets; k=5 involves five targets. There is no fitted diminishing-returns law or inferential test.



CatBoost / CANONICALIZED: highest negative-addition fraction at 4→5: **0.525000** (160 edges; marginal_gain_by_pool_size.csv row_id `220071ea39db4f9bf83cd2e2`). Across the fixed seven-target transitions 1→2 through 4→5, macro mean benefit decreases at every step: **True** (target_macro table, same model/view, n_sources_before≤4). This is descriptive, not a universal diminishing-returns claim.

CatBoost / RAW: highest negative-addition fraction at 1→2: **0.515789** (190 edges; marginal_gain_by_pool_size.csv row_id `52ce63a5d099acc6e54d7e56`). Across the fixed seven-target transitions 1→2 through 4→5, macro mean benefit decreases at every step: **False** (target_macro table, same model/view, n_sources_before≤4). This is descriptive, not a universal diminishing-returns claim.

Logistic Regression / CANONICALIZED: highest negative-addition fraction at 5→6: **0.500000** (30 edges; marginal_gain_by_pool_size.csv row_id `995beb6f25599028b230b55c`). Across the fixed seven-target transitions 1→2 through 4→5, macro mean benefit decreases at every step: **False** (target_macro table, same model/view, n_sources_before≤4). This is descriptive, not a universal diminishing-returns claim.

Logistic Regression / RAW: highest negative-addition fraction at 5→6: **0.533333** (30 edges; marginal_gain_by_pool_size.csv row_id `677d3893507b98e1a0e607f5`). Across the fixed seven-target transitions 1→2 through 4→5, macro mean benefit decreases at every step: **False** (target_macro table, same model/view, n_sources_before≤4). This is descriptive, not a universal diminishing-returns claim.

MLP / CANONICALIZED: highest negative-addition fraction at 1→2: **0.473684** (190 edges; marginal_gain_by_pool_size.csv row_id `ed8cd54ec4738fc2fee5cb4b`). Across the fixed seven-target transitions 1→2 through 4→5, macro mean benefit decreases at every step: **False** (target_macro table, same model/view, n_sources_before≤4). This is descriptive, not a universal diminishing-returns claim.

MLP / RAW: highest negative-addition fraction at 5→6: **0.533333** (30 edges; marginal_gain_by_pool_size.csv row_id `d31b4e324d075ad974f7c28a`). Across the fixed seven-target transitions 1→2 through 4→5, macro mean benefit decreases at every step: **False** (target_macro table, same model/view, n_sources_before≤4). This is descriptive, not a universal diminishing-returns claim.



## 4–5. Representations and model-dependent behavior



Use the complete model/view curves above, not only the best line. The RAW/CANONICALIZED historical datasets came from separate files; identical payload populations across views are not established by these coalition summaries. A causal canonicalization effect from these curves is **NOT VERIFIED FOR PAPER**. Within each view, nested comparisons preserve the target and matched seed; dataset size, validation selection and source composition can all change.

Numeric end-point differences on the SAME seven targets (k=1 vs k=5):

- Logistic Regression / RAW: F1 0.668210 → 0.731485; delta **+0.063275**. Source: performance_by_source_count_macro.csv, model=logistic, representation=RAW, n_sources∈{1,5}; IDs are the union of those two rows.

- Logistic Regression / CANONICALIZED: F1 0.758939 → 0.851426; delta **+0.092487**. Source: performance_by_source_count_macro.csv, model=logistic, representation=CANONICALIZED, n_sources∈{1,5}; IDs are the union of those two rows.

- CatBoost / RAW: F1 0.693771 → 0.760911; delta **+0.067139**. Source: performance_by_source_count_macro.csv, model=catboost, representation=RAW, n_sources∈{1,5}; IDs are the union of those two rows.

- CatBoost / CANONICALIZED: F1 0.720244 → 0.873385; delta **+0.153140**. Source: performance_by_source_count_macro.csv, model=catboost, representation=CANONICALIZED, n_sources∈{1,5}; IDs are the union of those two rows.

- MLP / RAW: F1 0.663015 → 0.801256; delta **+0.138241**. Source: performance_by_source_count_macro.csv, model=mlp, representation=RAW, n_sources∈{1,5}; IDs are the union of those two rows.

- MLP / CANONICALIZED: F1 0.769347 → 0.872822; delta **+0.103475**. Source: performance_by_source_count_macro.csv, model=mlp, representation=CANONICALIZED, n_sources∈{1,5}; IDs are the union of those two rows.



## 6–7. Sources with consistent positive versus target-dependent effects



The full table includes every source, model and view. mean_delta_f1 is TARGET-MACRO (each target first averages its nested edges); median/fractions are edge descriptive and labeled accordingly. targets_helped/harmed use the sign of each target’s mean effect. Do not describe any source as universally good or bad.

| added_source | model | representation | mean_delta_f1 | targets_helped | targets_harmed | n_targets | fraction_positive | fraction_negative | number_of_valid_additions | target_mean_std |
|---|---|---|---|---|---|---|---|---|---|---|
| artificial_sqli | catboost | CANONICALIZED | 0.088922 | 6 | 0 | 6 | 0.733766 | 0.266234 | 154 | 0.065941 |
| artificial_sqli | catboost | RAW | 0.042794 | 4 | 2 | 6 | 0.636364 | 0.363636 | 154 | 0.062622 |
| artificial_sqli | logistic | CANONICALIZED | 0.067130 | 6 | 0 | 6 | 0.792208 | 0.207792 | 154 | 0.046041 |
| artificial_sqli | logistic | RAW | 0.035496 | 5 | 1 | 6 | 0.688312 | 0.311688 | 154 | 0.037618 |
| artificial_sqli | mlp | CANONICALIZED | 0.090582 | 6 | 0 | 6 | 0.844156 | 0.155844 | 154 | 0.055597 |
| artificial_sqli | mlp | RAW | 0.086039 | 6 | 0 | 6 | 0.785714 | 0.214286 | 154 | 0.041812 |
| csic | catboost | CANONICALIZED | 0.018516 | 4 | 2 | 6 | 0.603896 | 0.396104 | 154 | 0.038606 |
| csic | catboost | RAW | 0.012689 | 5 | 1 | 6 | 0.597403 | 0.402597 | 154 | 0.056431 |
| csic | logistic | CANONICALIZED | 0.018815 | 6 | 0 | 6 | 0.655844 | 0.344156 | 154 | 0.013457 |
| csic | logistic | RAW | 0.015395 | 4 | 2 | 6 | 0.629870 | 0.370130 | 154 | 0.022720 |
| csic | mlp | CANONICALIZED | -0.004729 | 2 | 4 | 6 | 0.480519 | 0.519481 | 154 | 0.024246 |
| csic | mlp | RAW | 0.018309 | 6 | 0 | 6 | 0.610390 | 0.389610 | 154 | 0.013315 |
| ecml | catboost | CANONICALIZED | 0.049845 | 6 | 0 | 6 | 0.701299 | 0.298701 | 154 | 0.013007 |
| ecml | catboost | RAW | 0.043775 | 4 | 2 | 6 | 0.714286 | 0.285714 | 154 | 0.063833 |
| ecml | logistic | CANONICALIZED | 0.031862 | 5 | 1 | 6 | 0.798701 | 0.201299 | 154 | 0.023323 |
| ecml | logistic | RAW | 0.075628 | 6 | 0 | 6 | 0.831169 | 0.168831 | 154 | 0.055947 |
| ecml | mlp | CANONICALIZED | 0.042440 | 6 | 0 | 6 | 0.818182 | 0.181818 | 154 | 0.027482 |
| ecml | mlp | RAW | 0.081284 | 6 | 0 | 6 | 0.857143 | 0.142857 | 154 | 0.058611 |
| proprio | catboost | CANONICALIZED | 0.054496 | 6 | 0 | 6 | 0.714286 | 0.285714 | 154 | 0.024453 |
| proprio | catboost | RAW | -0.044579 | 2 | 4 | 6 | 0.266234 | 0.733766 | 154 | 0.063448 |
| proprio | logistic | CANONICALIZED | 0.078580 | 6 | 0 | 6 | 0.727273 | 0.272727 | 154 | 0.058263 |
| proprio | logistic | RAW | -0.049171 | 0 | 6 | 6 | 0.305195 | 0.694805 | 154 | 0.013760 |
| proprio | mlp | CANONICALIZED | 0.063427 | 6 | 0 | 6 | 0.876623 | 0.123377 | 154 | 0.015540 |
| proprio | mlp | RAW | -0.003451 | 2 | 4 | 6 | 0.512987 | 0.487013 | 154 | 0.026195 |
| site_cooking | catboost | CANONICALIZED | -0.003108 | 3 | 2 | 5 | 0.445161 | 0.554839 | 155 | 0.019839 |
| site_cooking | catboost | RAW | -0.001562 | 2 | 3 | 5 | 0.393548 | 0.606452 | 155 | 0.030054 |
| site_cooking | logistic | CANONICALIZED | -0.012921 | 1 | 4 | 5 | 0.445161 | 0.554839 | 155 | 0.013006 |
| site_cooking | logistic | RAW | -0.006108 | 2 | 3 | 5 | 0.393548 | 0.593548 | 155 | 0.037649 |
| site_cooking | mlp | CANONICALIZED | -0.019656 | 0 | 5 | 5 | 0.329032 | 0.670968 | 155 | 0.009921 |
| site_cooking | mlp | RAW | 0.023448 | 4 | 1 | 5 | 0.503226 | 0.496774 | 155 | 0.039330 |
| site_sqli | catboost | CANONICALIZED | 0.003191 | 2 | 3 | 5 | 0.432258 | 0.567742 | 155 | 0.014999 |
| site_sqli | catboost | RAW | -0.011653 | 2 | 3 | 5 | 0.425806 | 0.574194 | 155 | 0.037261 |
| site_sqli | logistic | CANONICALIZED | -0.041921 | 0 | 5 | 5 | 0.264516 | 0.735484 | 155 | 0.042896 |
| site_sqli | logistic | RAW | -0.025103 | 1 | 4 | 5 | 0.400000 | 0.600000 | 155 | 0.048342 |
| site_sqli | mlp | CANONICALIZED | -0.034909 | 1 | 4 | 5 | 0.264516 | 0.735484 | 155 | 0.022349 |
| site_sqli | mlp | RAW | 0.024787 | 3 | 2 | 5 | 0.477419 | 0.522581 | 155 | 0.048508 |
| srbh | catboost | CANONICALIZED | 0.024049 | 4 | 2 | 6 | 0.603896 | 0.396104 | 154 | 0.063127 |
| srbh | catboost | RAW | 0.050280 | 6 | 0 | 6 | 0.688312 | 0.311688 | 154 | 0.042865 |
| srbh | logistic | CANONICALIZED | 0.019550 | 4 | 2 | 6 | 0.623377 | 0.376623 | 154 | 0.037301 |
| srbh | logistic | RAW | 0.057282 | 5 | 1 | 6 | 0.707792 | 0.292208 | 154 | 0.062449 |
| srbh | mlp | CANONICALIZED | 0.031960 | 4 | 2 | 6 | 0.785714 | 0.214286 | 154 | 0.048548 |
| srbh | mlp | RAW | 0.030198 | 4 | 2 | 6 | 0.636364 | 0.363636 | 154 | 0.060856 |

Source: `tables/marginal_gain_by_added_source.csv`, all rows. Target dependence is described by SD and min/max of TARGET mean gains, not a new stability score. Exact target-specific signs and values are in `tables/marginal_gain_by_added_source_target.csv`.

CatBoost / CANONICALIZED: most consistently positive by helped-target fraction, then target-macro positive-edge fraction: **artificial_sqli**, 6/6 targets, macro ΔF1=+0.088922; row_id `378ef3c7b83b549e6a196f2c`. Largest between-target SD: **artificial_sqli**, SD=0.065941, target-mean range [+0.004065, +0.168301]; row_id `378ef3c7b83b549e6a196f2c`. Ties follow the declared order; this is not an intrinsic dataset-quality rank.

CatBoost / RAW: most consistently positive by helped-target fraction, then target-macro positive-edge fraction: **srbh**, 6/6 targets, macro ΔF1=+0.050280; row_id `ea4c45efe664a18532dbb93e`. Largest between-target SD: **ecml**, SD=0.063833, target-mean range [-0.010909, +0.147104]; row_id `1df8f79ae79253ceca9ba26b`. Ties follow the declared order; this is not an intrinsic dataset-quality rank.

Logistic Regression / CANONICALIZED: most consistently positive by helped-target fraction, then target-macro positive-edge fraction: **artificial_sqli**, 6/6 targets, macro ΔF1=+0.067130; row_id `27f15fd5dd32b2058bc892c2`. Largest between-target SD: **proprio**, SD=0.058263, target-mean range [+0.019198, +0.155575]; row_id `f91a5c8041ae9c6f6284fba9`. Ties follow the declared order; this is not an intrinsic dataset-quality rank.

Logistic Regression / RAW: most consistently positive by helped-target fraction, then target-macro positive-edge fraction: **ecml**, 6/6 targets, macro ΔF1=+0.075628; row_id `ed9ccc4d39ed5004f70f2e68`. Largest between-target SD: **srbh**, SD=0.062449, target-mean range [-0.021833, +0.167410]; row_id `a9c47661cfee23b91ae40f48`. Ties follow the declared order; this is not an intrinsic dataset-quality rank.

MLP / CANONICALIZED: most consistently positive by helped-target fraction, then target-macro positive-edge fraction: **proprio**, 6/6 targets, macro ΔF1=+0.063427; row_id `2cbc74c62ddbef10df8e5f0a`. Largest between-target SD: **artificial_sqli**, SD=0.055597, target-mean range [+0.018450, +0.161845]; row_id `38db2d178e0b4e9f0a74743f`. Ties follow the declared order; this is not an intrinsic dataset-quality rank.

MLP / RAW: most consistently positive by helped-target fraction, then target-macro positive-edge fraction: **ecml**, 6/6 targets, macro ΔF1=+0.081284; row_id `b59cc90b7861f0e29deb0325`. Largest between-target SD: **srbh**, SD=0.060856, target-mean range [-0.042452, +0.123742]; row_id `1ca2308897a63cd501136fa5`. Ties follow the declared order; this is not an intrinsic dataset-quality rank.



## 8. Which ten engineered features are most stable?



| representation | feature | top_k_frequency | rank_mean | rank_std | importance_mean | importance_std | n_runs | n_seeds |
|---|---|---|---|---|---|---|---|---|
| CANONICALIZED | char_equals | 1.000000 | 5.628571 | 1.214755 | 7.044073 | 2.126508 | 35 | 5 |
| CANONICALIZED | char_sq | 0.971429 | 6.314286 | 2.897985 | 7.686192 | 4.641470 | 35 | 5 |
| CANONICALIZED | char_space | 0.942857 | 2.971429 | 2.843835 | 12.498597 | 3.782297 | 35 | 5 |
| CANONICALIZED | char_rparen | 0.942857 | 3.685714 | 2.846788 | 12.431460 | 8.144355 | 35 | 5 |
| CANONICALIZED | sql_comment_dash | 0.857143 | 6.514286 | 7.257335 | 8.279275 | 5.840933 | 35 | 5 |
| CANONICALIZED | ratio_nonalnum | 0.828571 | 7.285714 | 3.959883 | 6.753775 | 4.037782 | 35 | 5 |
| CANONICALIZED | sql_select | 0.828571 | 7.842857 | 10.536192 | 9.502631 | 6.410870 | 35 | 5 |
| CANONICALIZED | sql_or | 0.800000 | 9.000000 | 2.786522 | 3.710357 | 1.594530 | 35 | 5 |
| CANONICALIZED | sql_and | 0.600000 | 15.942857 | 14.593901 | 3.825686 | 3.327024 | 35 | 5 |
| CANONICALIZED | sql_comment_block | 0.485714 | 12.057143 | 7.565179 | 5.513893 | 5.066905 | 35 | 5 |
| RAW | sql_comment_dash | 1.000000 | 3.914286 | 3.193481 | 15.196501 | 10.100430 | 35 | 5 |
| RAW | enc_pct | 1.000000 | 5.857143 | 2.211505 | 7.079273 | 3.955998 | 35 | 5 |
| RAW | ratio_nonalnum | 0.828571 | 6.857143 | 4.001050 | 6.991958 | 4.621460 | 35 | 5 |
| RAW | char_pct | 0.800000 | 7.371429 | 3.020379 | 5.107199 | 2.519081 | 35 | 5 |
| RAW | char_rparen | 0.800000 | 9.914286 | 16.228373 | 13.183220 | 11.062463 | 35 | 5 |
| RAW | char_space | 0.714286 | 8.714286 | 6.551028 | 6.146241 | 5.396630 | 35 | 5 |
| RAW | sql_select | 0.657143 | 12.057143 | 13.518925 | 5.520166 | 3.983064 | 35 | 5 |
| RAW | sql_or | 0.628571 | 10.500000 | 7.756402 | 3.376261 | 1.732988 | 35 | 5 |
| RAW | sql_and | 0.628571 | 17.014286 | 16.687211 | 3.977686 | 3.106696 | 35 | 5 |
| RAW | char_equals | 0.571429 | 8.857143 | 4.440077 | 4.892526 | 3.910417 | 35 | 5 |

Source: `tables/top10_cross_dataset_stable_features.csv`, representation/feature keys; original stable_features.csv input_row_id and experiment_ids preserved. These are **most stable features across unseen targets**, not proven best transferable features. Importances are model-specific descriptive support, not causal contribution.



## 9. How do stable-feature sets differ after canonicalization?



Overlap: **8/10**. Shared: char_equals, char_rparen, char_space, ratio_nonalnum, sql_and, sql_comment_dash, sql_or, sql_select. RAW-only: char_pct, enc_pct. CANONICALIZED-only: char_sq, sql_comment_block. Source: top10_cross_dataset_stable_features.csv, set intersection/differences by representation, all selected rows; no new importance computation.

A representation-dependent top-ten set does not demonstrate invariant features or causal improvement. Historical RAW/CAN population differences remain a limitation.



## Negative findings, limitations and manuscript use



Negative additions remain in all distributions and summaries, including boxplot fliers. Numerical zero is not practical equivalence. Coalition sizes have different numbers of combinations; full pools have one coalition, so within-level sample SD is undefined, not zero. The targets are not all independent provenance families. Repeated coalitions share runs and targets, so no p-values are computed from edges.

Figure captions and exact figure-source mappings: TRACEABILITY.csv. Main figures: cross_dataset_stable_features, generalization_vs_source_count, marginal_gain_per_added_source (vector PDF plus 300-dpi PNG). Figure B1 uses a detached k=6 point to avoid presenting a target-cohort change as an extra-source gain. Its detached vertical interval is the IQR across five targets; earlier bands are IQR across seven target means.

NOT VERIFIED FOR PAPER: causal feature effects; universally beneficial sources; a guaranteed monotonic/diminishing law; causal RAW/CAN gain on identical historical samples; optimizer-only diversity independent of validation; significance or generality beyond these targets. All reported numbers are descriptive and traceable, not inferential guarantees.

## Source Identity and Coalition Context



The following analyses reuse **6480** valid nested coalition contexts and **32400** saved matched-seed pairs; all contexts have five seed pairs. The requested seed means already exist and were not replaced. Sources: `tables/marginal_source_additions.parquet` and `derived/matched_source_additions_per_seed.parquet`; row keys target/model/representation/base_sources/added_source. Verification: `SOURCE_INTERACTIONS/derived/input_pair_verification.parquet`. Each target receives equal macro weight in Analysis A.

All numeric rows below identify model and representation and carry n_contexts (or n_coalition_contexts/n_valid_coalition_contexts), row_id and experiment_ids in their named CSV/Parquet. Script and all IDs resolve through the provenance section and SOURCE_INTERACTIONS/SOURCE_LINEAGE.parquet. RAW/CAN are historical views, not a newly established identical-payload causal comparison.



### 1. Largest average marginal gains



Compare only as descriptive averages over eligible targets; eligibility differs by added source. These are not intrinsic dataset-quality ranks. Full source/model/view results, including negative means, are in `SOURCE_INTERACTIONS/tables/source_identity_overview.csv`.

| added_source | model | representation | mean_target_delta_f1 | n_targets | n_coalition_contexts | row_id |
|---|---|---|---|---|---|---|
| artificial_sqli | mlp | CANONICALIZED | 0.090582 | 6 | 154 | 52a3a1de9269b5718c5514fe |
| artificial_sqli | catboost | CANONICALIZED | 0.088922 | 6 | 154 | 46929a6dcff5aac5b26b6586 |
| artificial_sqli | mlp | RAW | 0.086039 | 6 | 154 | 6c4701f555e4e70b75a7e88b |
| proprio | logistic | CANONICALIZED | 0.078580 | 6 | 154 | de23605ba51ceb31a6ba864f |
| ecml | logistic | RAW | 0.075628 | 6 | 154 | 27a6518c6dda98239b38b612 |
| srbh | catboost | RAW | 0.050280 | 6 | 154 | a66f6f72442fa65a66f8d724 |



### 2. Same source, different pool sizes



The complete table below reports target-macro ΔF1 at each eligible size; these values describe all matching coalition contexts, not an arbitrary addition order. Source: `SOURCE_INTERACTIONS/tables/marginal_gain_by_added_source_and_pool_size.csv`, filter each displayed added_source/model/representation/n_sources_before. k=1..4 has a stable target set for each source; k=5 may change it.

| added_source | model | representation | n_sources_before | n_targets | n_coalition_contexts | mean_target_delta_f1 |
|---|---|---|---|---|---|---|
| artificial_sqli | catboost | CANONICALIZED | 1 | 6 | 28 | 0.152657 |
| artificial_sqli | catboost | CANONICALIZED | 2 | 6 | 52 | 0.095427 |
| artificial_sqli | catboost | CANONICALIZED | 3 | 6 | 48 | 0.067967 |
| artificial_sqli | catboost | CANONICALIZED | 4 | 6 | 22 | 0.057536 |
| artificial_sqli | catboost | CANONICALIZED | 5 | 4 | 4 | 0.002765 |
| artificial_sqli | catboost | RAW | 1 | 6 | 28 | 0.075699 |
| artificial_sqli | catboost | RAW | 2 | 6 | 52 | 0.032285 |
| artificial_sqli | catboost | RAW | 3 | 6 | 48 | 0.048774 |
| artificial_sqli | catboost | RAW | 4 | 6 | 22 | 0.023885 |
| artificial_sqli | catboost | RAW | 5 | 4 | 4 | -0.012771 |
| artificial_sqli | logistic | CANONICALIZED | 1 | 6 | 28 | 0.090866 |
| artificial_sqli | logistic | CANONICALIZED | 2 | 6 | 52 | 0.088881 |
| artificial_sqli | logistic | CANONICALIZED | 3 | 6 | 48 | 0.054077 |
| artificial_sqli | logistic | CANONICALIZED | 4 | 6 | 22 | 0.031650 |
| artificial_sqli | logistic | CANONICALIZED | 5 | 4 | 4 | -0.023250 |
| artificial_sqli | logistic | RAW | 1 | 6 | 28 | 0.082139 |
| artificial_sqli | logistic | RAW | 2 | 6 | 52 | 0.041201 |
| artificial_sqli | logistic | RAW | 3 | 6 | 48 | 0.014607 |
| artificial_sqli | logistic | RAW | 4 | 6 | 22 | 0.012686 |
| artificial_sqli | logistic | RAW | 5 | 4 | 4 | 0.029436 |
| artificial_sqli | mlp | CANONICALIZED | 1 | 6 | 28 | 0.061789 |
| artificial_sqli | mlp | CANONICALIZED | 2 | 6 | 52 | 0.105694 |
| artificial_sqli | mlp | CANONICALIZED | 3 | 6 | 48 | 0.105411 |
| artificial_sqli | mlp | CANONICALIZED | 4 | 6 | 22 | 0.098091 |
| artificial_sqli | mlp | CANONICALIZED | 5 | 4 | 4 | 0.007095 |
| artificial_sqli | mlp | RAW | 1 | 6 | 28 | 0.104521 |
| artificial_sqli | mlp | RAW | 2 | 6 | 52 | 0.115037 |
| artificial_sqli | mlp | RAW | 3 | 6 | 48 | 0.069834 |
| artificial_sqli | mlp | RAW | 4 | 6 | 22 | 0.063534 |
| artificial_sqli | mlp | RAW | 5 | 4 | 4 | 0.021450 |
| csic | catboost | CANONICALIZED | 1 | 6 | 28 | -0.009543 |
| csic | catboost | CANONICALIZED | 2 | 6 | 52 | 0.039405 |
| csic | catboost | CANONICALIZED | 3 | 6 | 48 | 0.024739 |
| csic | catboost | CANONICALIZED | 4 | 6 | 22 | 0.006040 |
| csic | catboost | CANONICALIZED | 5 | 4 | 4 | 0.008149 |
| csic | catboost | RAW | 1 | 6 | 28 | 0.030587 |
| csic | catboost | RAW | 2 | 6 | 52 | -0.005948 |
| csic | catboost | RAW | 3 | 6 | 48 | 0.028708 |
| csic | catboost | RAW | 4 | 6 | 22 | 0.009944 |
| csic | catboost | RAW | 5 | 4 | 4 | 0.016096 |
| csic | logistic | CANONICALIZED | 1 | 6 | 28 | -0.000134 |
| csic | logistic | CANONICALIZED | 2 | 6 | 52 | 0.032615 |
| csic | logistic | CANONICALIZED | 3 | 6 | 48 | 0.019072 |
| csic | logistic | CANONICALIZED | 4 | 6 | 22 | 0.014038 |
| csic | logistic | CANONICALIZED | 5 | 4 | 4 | 0.010685 |
| csic | logistic | RAW | 1 | 6 | 28 | -0.041835 |
| csic | logistic | RAW | 2 | 6 | 52 | 0.029689 |
| csic | logistic | RAW | 3 | 6 | 48 | 0.034750 |
| csic | logistic | RAW | 4 | 6 | 22 | 0.035010 |
| csic | logistic | RAW | 5 | 4 | 4 | 0.048800 |
| csic | mlp | CANONICALIZED | 1 | 6 | 28 | -0.041290 |
| csic | mlp | CANONICALIZED | 2 | 6 | 52 | 0.014035 |
| csic | mlp | CANONICALIZED | 3 | 6 | 48 | 0.003650 |
| csic | mlp | CANONICALIZED | 4 | 6 | 22 | -0.008316 |
| csic | mlp | CANONICALIZED | 5 | 4 | 4 | -0.017037 |
| csic | mlp | RAW | 1 | 6 | 28 | -0.068265 |
| csic | mlp | RAW | 2 | 6 | 52 | 0.059592 |
| csic | mlp | RAW | 3 | 6 | 48 | 0.027678 |
| csic | mlp | RAW | 4 | 6 | 22 | 0.014925 |
| csic | mlp | RAW | 5 | 4 | 4 | 0.006006 |
| ecml | catboost | CANONICALIZED | 1 | 6 | 28 | 0.096388 |
| ecml | catboost | CANONICALIZED | 2 | 6 | 52 | 0.052770 |
| ecml | catboost | CANONICALIZED | 3 | 6 | 48 | 0.037629 |
| ecml | catboost | CANONICALIZED | 4 | 6 | 22 | 0.036539 |
| ecml | catboost | CANONICALIZED | 5 | 4 | 4 | 0.012505 |
| ecml | catboost | RAW | 1 | 6 | 28 | 0.035056 |
| ecml | catboost | RAW | 2 | 6 | 52 | 0.021556 |
| ecml | catboost | RAW | 3 | 6 | 48 | 0.062001 |
| ecml | catboost | RAW | 4 | 6 | 22 | 0.054191 |
| ecml | catboost | RAW | 5 | 4 | 4 | 0.112969 |
| ecml | logistic | CANONICALIZED | 1 | 6 | 28 | 0.015067 |
| ecml | logistic | CANONICALIZED | 2 | 6 | 52 | 0.052790 |
| ecml | logistic | CANONICALIZED | 3 | 6 | 48 | 0.032624 |
| ecml | logistic | CANONICALIZED | 4 | 6 | 22 | 0.011855 |
| ecml | logistic | CANONICALIZED | 5 | 4 | 4 | 0.003214 |
| ecml | logistic | RAW | 1 | 6 | 28 | 0.136251 |
| ecml | logistic | RAW | 2 | 6 | 52 | 0.096862 |
| ecml | logistic | RAW | 3 | 6 | 48 | 0.046852 |
| ecml | logistic | RAW | 4 | 6 | 22 | 0.049085 |
| ecml | logistic | RAW | 5 | 4 | 4 | 0.028406 |
| ecml | mlp | CANONICALIZED | 1 | 6 | 28 | 0.038985 |
| ecml | mlp | CANONICALIZED | 2 | 6 | 52 | 0.061786 |
| ecml | mlp | CANONICALIZED | 3 | 6 | 48 | 0.037919 |
| ecml | mlp | CANONICALIZED | 4 | 6 | 22 | 0.019783 |
| ecml | mlp | CANONICALIZED | 5 | 4 | 4 | 0.005804 |
| ecml | mlp | RAW | 1 | 6 | 28 | 0.104894 |
| ecml | mlp | RAW | 2 | 6 | 52 | 0.128092 |
| ecml | mlp | RAW | 3 | 6 | 48 | 0.050910 |
| ecml | mlp | RAW | 4 | 6 | 22 | 0.028802 |
| ecml | mlp | RAW | 5 | 4 | 4 | 0.050854 |
| proprio | catboost | CANONICALIZED | 1 | 6 | 28 | 0.076156 |
| proprio | catboost | CANONICALIZED | 2 | 6 | 52 | 0.051753 |
| proprio | catboost | CANONICALIZED | 3 | 6 | 48 | 0.050579 |
| proprio | catboost | CANONICALIZED | 4 | 6 | 22 | 0.055663 |
| proprio | catboost | CANONICALIZED | 5 | 4 | 4 | 0.021124 |
| proprio | catboost | RAW | 1 | 6 | 28 | -0.062092 |
| proprio | catboost | RAW | 2 | 6 | 52 | -0.046841 |
| proprio | catboost | RAW | 3 | 6 | 48 | -0.025508 |
| proprio | catboost | RAW | 4 | 6 | 22 | -0.033786 |
| proprio | catboost | RAW | 5 | 4 | 4 | -0.061876 |
| proprio | logistic | CANONICALIZED | 1 | 6 | 28 | 0.082683 |
| proprio | logistic | CANONICALIZED | 2 | 6 | 52 | 0.092222 |
| proprio | logistic | CANONICALIZED | 3 | 6 | 48 | 0.074276 |
| proprio | logistic | CANONICALIZED | 4 | 6 | 22 | 0.040948 |
| proprio | logistic | CANONICALIZED | 5 | 4 | 4 | -0.012030 |
| proprio | logistic | RAW | 1 | 6 | 28 | -0.007870 |
| proprio | logistic | RAW | 2 | 6 | 52 | -0.027615 |
| proprio | logistic | RAW | 3 | 6 | 48 | -0.074717 |
| proprio | logistic | RAW | 4 | 6 | 22 | -0.092966 |
| proprio | logistic | RAW | 5 | 4 | 4 | -0.088302 |
| proprio | mlp | CANONICALIZED | 1 | 6 | 28 | 0.035840 |
| proprio | mlp | CANONICALIZED | 2 | 6 | 52 | 0.075231 |
| proprio | mlp | CANONICALIZED | 3 | 6 | 48 | 0.080720 |
| proprio | mlp | CANONICALIZED | 4 | 6 | 22 | 0.061160 |
| proprio | mlp | CANONICALIZED | 5 | 4 | 4 | 0.016993 |
| proprio | mlp | RAW | 1 | 6 | 28 | -0.056680 |
| proprio | mlp | RAW | 2 | 6 | 52 | 0.026381 |
| proprio | mlp | RAW | 3 | 6 | 48 | 0.005797 |
| proprio | mlp | RAW | 4 | 6 | 22 | -0.009883 |
| proprio | mlp | RAW | 5 | 4 | 4 | -0.046822 |
| site_cooking | catboost | CANONICALIZED | 1 | 5 | 25 | -0.012618 |
| site_cooking | catboost | CANONICALIZED | 2 | 5 | 50 | 0.007666 |
| site_cooking | catboost | CANONICALIZED | 3 | 5 | 50 | -0.000012 |
| site_cooking | catboost | CANONICALIZED | 4 | 5 | 25 | -0.017826 |
| site_cooking | catboost | CANONICALIZED | 5 | 5 | 5 | -0.020669 |
| site_cooking | catboost | RAW | 1 | 5 | 25 | 0.008320 |
| site_cooking | catboost | RAW | 2 | 5 | 50 | -0.023873 |
| site_cooking | catboost | RAW | 3 | 5 | 50 | 0.012895 |
| site_cooking | catboost | RAW | 4 | 5 | 25 | 0.006813 |
| site_cooking | catboost | RAW | 5 | 5 | 5 | -0.014323 |
| site_cooking | logistic | CANONICALIZED | 1 | 5 | 25 | -0.056342 |
| site_cooking | logistic | CANONICALIZED | 2 | 5 | 50 | -0.010192 |
| site_cooking | logistic | CANONICALIZED | 3 | 5 | 50 | -0.002182 |
| site_cooking | logistic | CANONICALIZED | 4 | 5 | 25 | -0.001254 |
| site_cooking | logistic | CANONICALIZED | 5 | 5 | 5 | 0.011162 |
| site_cooking | logistic | RAW | 1 | 5 | 25 | -0.003928 |
| site_cooking | logistic | RAW | 2 | 5 | 50 | 0.009520 |
| site_cooking | logistic | RAW | 3 | 5 | 50 | -0.019306 |
| site_cooking | logistic | RAW | 4 | 5 | 25 | -0.013406 |
| site_cooking | logistic | RAW | 5 | 5 | 5 | -0.004829 |
| site_cooking | mlp | CANONICALIZED | 1 | 5 | 25 | -0.048922 |
| site_cooking | mlp | CANONICALIZED | 2 | 5 | 50 | -0.018065 |
| site_cooking | mlp | CANONICALIZED | 3 | 5 | 50 | -0.012181 |
| site_cooking | mlp | CANONICALIZED | 4 | 5 | 25 | -0.011238 |
| site_cooking | mlp | CANONICALIZED | 5 | 5 | 5 | -0.006093 |
| site_cooking | mlp | RAW | 1 | 5 | 25 | 0.020066 |
| site_cooking | mlp | RAW | 2 | 5 | 50 | 0.048515 |
| site_cooking | mlp | RAW | 3 | 5 | 50 | 0.014106 |
| site_cooking | mlp | RAW | 4 | 5 | 25 | 0.003872 |
| site_cooking | mlp | RAW | 5 | 5 | 5 | -0.019009 |
| site_sqli | catboost | CANONICALIZED | 1 | 5 | 25 | 0.028792 |
| site_sqli | catboost | CANONICALIZED | 2 | 5 | 50 | 0.019363 |
| site_sqli | catboost | CANONICALIZED | 3 | 5 | 50 | -0.012990 |
| site_sqli | catboost | CANONICALIZED | 4 | 5 | 25 | -0.021245 |
| site_sqli | catboost | CANONICALIZED | 5 | 5 | 5 | -0.002530 |
| site_sqli | catboost | RAW | 1 | 5 | 25 | 0.027221 |
| site_sqli | catboost | RAW | 2 | 5 | 50 | -0.026887 |
| site_sqli | catboost | RAW | 3 | 5 | 50 | -0.006384 |
| site_sqli | catboost | RAW | 4 | 5 | 25 | -0.024359 |
| site_sqli | catboost | RAW | 5 | 5 | 5 | -0.042845 |
| site_sqli | logistic | CANONICALIZED | 1 | 5 | 25 | -0.079544 |
| site_sqli | logistic | CANONICALIZED | 2 | 5 | 50 | -0.038375 |
| site_sqli | logistic | CANONICALIZED | 3 | 5 | 50 | -0.036563 |
| site_sqli | logistic | CANONICALIZED | 4 | 5 | 25 | -0.027887 |
| site_sqli | logistic | CANONICALIZED | 5 | 5 | 5 | -0.013028 |
| site_sqli | logistic | RAW | 1 | 5 | 25 | -0.061585 |
| site_sqli | logistic | RAW | 2 | 5 | 50 | -0.008088 |
| site_sqli | logistic | RAW | 3 | 5 | 50 | -0.028979 |
| site_sqli | logistic | RAW | 4 | 5 | 25 | -0.015273 |
| site_sqli | logistic | RAW | 5 | 5 | 5 | -0.023222 |
| site_sqli | mlp | CANONICALIZED | 1 | 5 | 25 | -0.083754 |
| site_sqli | mlp | CANONICALIZED | 2 | 5 | 50 | -0.035954 |
| site_sqli | mlp | CANONICALIZED | 3 | 5 | 50 | -0.019502 |
| site_sqli | mlp | CANONICALIZED | 4 | 5 | 25 | -0.018465 |
| site_sqli | mlp | CANONICALIZED | 5 | 5 | 5 | -0.016539 |
| site_sqli | mlp | RAW | 1 | 5 | 25 | 0.022543 |
| site_sqli | mlp | RAW | 2 | 5 | 50 | 0.060350 |
| site_sqli | mlp | RAW | 3 | 5 | 50 | 0.010257 |
| site_sqli | mlp | RAW | 4 | 5 | 25 | -0.003775 |
| site_sqli | mlp | RAW | 5 | 5 | 5 | -0.031516 |
| srbh | catboost | CANONICALIZED | 1 | 6 | 28 | 0.061659 |
| srbh | catboost | CANONICALIZED | 2 | 6 | 52 | 0.016996 |
| srbh | catboost | CANONICALIZED | 3 | 6 | 48 | 0.011853 |
| srbh | catboost | CANONICALIZED | 4 | 6 | 22 | 0.023432 |
| srbh | catboost | CANONICALIZED | 5 | 4 | 4 | 0.080670 |
| srbh | catboost | RAW | 1 | 6 | 28 | 0.047611 |
| srbh | catboost | RAW | 2 | 6 | 52 | 0.012816 |
| srbh | catboost | RAW | 3 | 6 | 48 | 0.070650 |
| srbh | catboost | RAW | 4 | 6 | 22 | 0.072273 |
| srbh | catboost | RAW | 5 | 4 | 4 | 0.162937 |
| srbh | logistic | CANONICALIZED | 1 | 6 | 28 | 0.008636 |
| srbh | logistic | CANONICALIZED | 2 | 6 | 52 | 0.036604 |
| srbh | logistic | CANONICALIZED | 3 | 6 | 48 | 0.019908 |
| srbh | logistic | CANONICALIZED | 4 | 6 | 22 | -0.002429 |
| srbh | logistic | CANONICALIZED | 5 | 4 | 4 | 0.010834 |
| srbh | logistic | RAW | 1 | 6 | 28 | 0.069675 |
| srbh | logistic | RAW | 2 | 6 | 52 | 0.068581 |
| srbh | logistic | RAW | 3 | 6 | 48 | 0.041920 |
| srbh | logistic | RAW | 4 | 6 | 22 | 0.045632 |
| srbh | logistic | RAW | 5 | 4 | 4 | 0.051702 |
| srbh | mlp | CANONICALIZED | 1 | 6 | 28 | -0.010906 |
| srbh | mlp | CANONICALIZED | 2 | 6 | 52 | 0.045265 |
| srbh | mlp | CANONICALIZED | 3 | 6 | 48 | 0.046540 |
| srbh | mlp | CANONICALIZED | 4 | 6 | 22 | 0.040633 |
| srbh | mlp | CANONICALIZED | 5 | 4 | 4 | 0.043236 |
| srbh | mlp | RAW | 1 | 6 | 28 | -0.022054 |
| srbh | mlp | RAW | 2 | 6 | 52 | 0.059848 |
| srbh | mlp | RAW | 3 | 6 | 48 | 0.041852 |
| srbh | mlp | RAW | 4 | 6 | 22 | 0.049530 |
| srbh | mlp | RAW | 5 | 4 | 4 | -0.002505 |



### 3. Sign changes as the pool grows



Adjacent sign reversals below preserve identical eligible target sets (base sizes 1..4 only). Positive-to-negative transitions directly answer the requested reversal question; reverse transitions are retained rather than hidden. Source: `SOURCE_INTERACTIONS/tables/source_pool_sign_changes.csv`; linked smaller_row_id/larger_row_id resolve the original A cells and IDs.

| added_source | model | representation | k_before | k_after | direction | delta_at_smaller_pool | delta_at_larger_pool | n_targets | contexts_smaller | contexts_larger |
|---|---|---|---|---|---|---|---|---|---|---|
| csic | catboost | CANONICALIZED | 1 | 2 | negative_to_positive | -0.009543 | 0.039405 | 6 | 28 | 52 |
| csic | catboost | RAW | 1 | 2 | positive_to_negative | 0.030587 | -0.005948 | 6 | 28 | 52 |
| csic | catboost | RAW | 2 | 3 | negative_to_positive | -0.005948 | 0.028708 | 6 | 52 | 48 |
| csic | logistic | CANONICALIZED | 1 | 2 | negative_to_positive | -0.000134 | 0.032615 | 6 | 28 | 52 |
| csic | logistic | RAW | 1 | 2 | negative_to_positive | -0.041835 | 0.029689 | 6 | 28 | 52 |
| csic | mlp | CANONICALIZED | 1 | 2 | negative_to_positive | -0.041290 | 0.014035 | 6 | 28 | 52 |
| csic | mlp | CANONICALIZED | 3 | 4 | positive_to_negative | 0.003650 | -0.008316 | 6 | 48 | 22 |
| csic | mlp | RAW | 1 | 2 | negative_to_positive | -0.068265 | 0.059592 | 6 | 28 | 52 |
| proprio | mlp | RAW | 1 | 2 | negative_to_positive | -0.056680 | 0.026381 | 6 | 28 | 52 |
| proprio | mlp | RAW | 3 | 4 | positive_to_negative | 0.005797 | -0.009883 | 6 | 48 | 22 |
| site_cooking | catboost | CANONICALIZED | 1 | 2 | negative_to_positive | -0.012618 | 0.007666 | 5 | 25 | 50 |
| site_cooking | catboost | CANONICALIZED | 2 | 3 | positive_to_negative | 0.007666 | -0.000012 | 5 | 50 | 50 |
| site_cooking | catboost | RAW | 1 | 2 | positive_to_negative | 0.008320 | -0.023873 | 5 | 25 | 50 |
| site_cooking | catboost | RAW | 2 | 3 | negative_to_positive | -0.023873 | 0.012895 | 5 | 50 | 50 |
| site_cooking | logistic | RAW | 1 | 2 | negative_to_positive | -0.003928 | 0.009520 | 5 | 25 | 50 |
| site_cooking | logistic | RAW | 2 | 3 | positive_to_negative | 0.009520 | -0.019306 | 5 | 50 | 50 |
| site_sqli | catboost | CANONICALIZED | 2 | 3 | positive_to_negative | 0.019363 | -0.012990 | 5 | 50 | 50 |
| site_sqli | catboost | RAW | 1 | 2 | positive_to_negative | 0.027221 | -0.026887 | 5 | 25 | 50 |
| site_sqli | mlp | RAW | 3 | 4 | positive_to_negative | 0.010257 | -0.003775 | 5 | 50 | 25 |
| srbh | logistic | CANONICALIZED | 3 | 4 | positive_to_negative | 0.019908 | -0.002429 | 6 | 48 | 22 |
| srbh | mlp | CANONICALIZED | 1 | 2 | negative_to_positive | -0.010906 | 0.045265 | 6 | 28 | 52 |
| srbh | mlp | RAW | 1 | 2 | negative_to_positive | -0.022054 | 0.059848 | 6 | 28 | 52 |



### 4–5. Targets helped most and hurt most by each source



Extrema of mean context effects for every source/model/view. A positive lowest value means **no negative target-average effect was observed**, not that the source never hurt an individual context. Negative contexts can coexist with a positive mean. Source: `SOURCE_INTERACTIONS/tables/source_identity_overview.csv`; best_row_id/lowest_row_id point into `SOURCE_INTERACTIONS/tables/marginal_gain_by_added_source_target.csv`.

| added_source | model | representation | best_target | best_target_delta_f1 | best_target_contexts | lowest_target | lowest_target_delta_f1 | lowest_target_contexts |
|---|---|---|---|---|---|---|---|---|
| artificial_sqli | catboost | CANONICALIZED | site_cooking | 0.168301 | 15 | srbh | 0.004065 | 31 |
| artificial_sqli | catboost | RAW | site_cooking | 0.119527 | 15 | proprio | -0.025346 | 31 |
| artificial_sqli | logistic | CANONICALIZED | site_cooking | 0.127487 | 15 | srbh | 0.019253 | 31 |
| artificial_sqli | logistic | RAW | proprio | 0.097239 | 31 | srbh | -0.011935 | 31 |
| artificial_sqli | mlp | CANONICALIZED | site_cooking | 0.161845 | 15 | srbh | 0.018450 | 31 |
| artificial_sqli | mlp | RAW | proprio | 0.137130 | 31 | srbh | 0.038797 | 31 |
| csic | catboost | CANONICALIZED | ecml | 0.067019 | 31 | site_sqli | -0.023957 | 15 |
| csic | catboost | RAW | artificial_sqli | 0.057167 | 31 | proprio | -0.096038 | 31 |
| csic | logistic | CANONICALIZED | proprio | 0.035262 | 31 | site_sqli | 0.000535 | 15 |
| csic | logistic | RAW | ecml | 0.041741 | 31 | site_cooking | -0.010907 | 15 |
| csic | mlp | CANONICALIZED | ecml | 0.039855 | 31 | artificial_sqli | -0.026880 | 31 |
| csic | mlp | RAW | ecml | 0.044221 | 31 | srbh | 0.006406 | 31 |
| ecml | catboost | CANONICALIZED | srbh | 0.072129 | 31 | artificial_sqli | 0.033680 | 31 |
| ecml | catboost | RAW | srbh | 0.147104 | 31 | site_sqli | -0.010909 | 15 |
| ecml | logistic | CANONICALIZED | srbh | 0.059145 | 31 | site_cooking | -0.001590 | 15 |
| ecml | logistic | RAW | srbh | 0.140623 | 31 | site_sqli | 0.007692 | 15 |
| ecml | mlp | CANONICALIZED | csic | 0.092626 | 31 | site_cooking | 0.018711 | 15 |
| ecml | mlp | RAW | csic | 0.162444 | 31 | site_sqli | 0.013677 | 15 |
| proprio | catboost | CANONICALIZED | site_sqli | 0.080431 | 15 | ecml | 0.022162 | 31 |
| proprio | catboost | RAW | site_cooking | 0.047158 | 15 | ecml | -0.120441 | 31 |
| proprio | logistic | CANONICALIZED | site_cooking | 0.155575 | 15 | srbh | 0.019198 | 31 |
| proprio | logistic | RAW | artificial_sqli | -0.030449 | 31 | srbh | -0.069145 | 31 |
| proprio | mlp | CANONICALIZED | ecml | 0.090763 | 31 | srbh | 0.044193 | 31 |
| proprio | mlp | RAW | ecml | 0.034486 | 31 | site_sqli | -0.031722 | 15 |
| site_cooking | catboost | CANONICALIZED | proprio | 0.015802 | 31 | csic | -0.032406 | 31 |
| site_cooking | catboost | RAW | proprio | 0.042783 | 31 | artificial_sqli | -0.040055 | 31 |
| site_cooking | logistic | CANONICALIZED | srbh | 0.000720 | 31 | csic | -0.030583 | 31 |
| site_cooking | logistic | RAW | proprio | 0.034037 | 31 | ecml | -0.059193 | 31 |
| site_cooking | mlp | CANONICALIZED | ecml | -0.012340 | 31 | srbh | -0.036168 | 31 |
| site_cooking | mlp | RAW | proprio | 0.088924 | 31 | ecml | -0.013772 | 31 |
| site_sqli | catboost | CANONICALIZED | proprio | 0.024161 | 31 | srbh | -0.012239 | 31 |
| site_sqli | catboost | RAW | csic | 0.027259 | 31 | srbh | -0.069060 | 31 |
| site_sqli | logistic | CANONICALIZED | proprio | -0.001958 | 31 | ecml | -0.111034 | 31 |
| site_sqli | logistic | RAW | proprio | 0.043140 | 31 | ecml | -0.083419 | 31 |
| site_sqli | mlp | CANONICALIZED | proprio | 0.001190 | 31 | csic | -0.052863 | 31 |
| site_sqli | mlp | RAW | proprio | 0.102576 | 31 | ecml | -0.023060 | 31 |
| srbh | catboost | CANONICALIZED | ecml | 0.126436 | 31 | site_cooking | -0.049473 | 15 |
| srbh | catboost | RAW | ecml | 0.123258 | 31 | site_sqli | 0.005411 | 15 |
| srbh | logistic | CANONICALIZED | ecml | 0.047072 | 31 | site_sqli | -0.034187 | 15 |
| srbh | logistic | RAW | ecml | 0.167410 | 31 | proprio | -0.021833 | 31 |
| srbh | mlp | CANONICALIZED | ecml | 0.106272 | 31 | site_sqli | -0.018624 | 15 |
| srbh | mlp | RAW | ecml | 0.123742 | 31 | proprio | -0.042452 | 31 |



### 6. Strongest target-dependent behavior



Descriptive operational definition: largest max–min range of target-mean effects within a model/view; sample SD is also shown. Not a significance test. Full context counts and endpoints are retained. Source: `SOURCE_INTERACTIONS/tables/source_identity_overview.csv`.

| added_source | model | representation | target_range_delta_f1 | std_target_delta_f1 | n_targets | n_coalition_contexts | row_id |
|---|---|---|---|---|---|---|---|
| srbh | logistic | RAW | 0.189243 | 0.062449 | 6 | 154 | 8de011dc0f0c3bc36247dd1e |
| srbh | catboost | CANONICALIZED | 0.175909 | 0.063127 | 6 | 154 | 214c0b6652242b68faacf0f3 |
| proprio | catboost | RAW | 0.167600 | 0.063448 | 6 | 154 | 1fa792188edf25f13aeb244a |
| srbh | mlp | RAW | 0.166194 | 0.060856 | 6 | 154 | 46471e89d61a40b8080ad2b1 |
| artificial_sqli | mlp | CANONICALIZED | 0.143395 | 0.055597 | 6 | 154 | 52a3a1de9269b5718c5514fe |
| proprio | logistic | CANONICALIZED | 0.136377 | 0.058263 | 6 | 154 | de23605ba51ceb31a6ba864f |



### 7. Positive effects across many contexts



The following lists every source, including weak or inconsistent ones. mean_target_fraction_positive first computes the proportion of positive contexts within each target, then weights targets equally. targets_positive/negative classify target MEANS; neither is a guarantee for every coalition. Numerical sign tolerance is 1e-9, not a scientific equivalence margin. Source: `SOURCE_INTERACTIONS/tables/source_identity_overview.csv`.

| added_source | model | representation | mean_target_fraction_positive | targets_positive | targets_negative | n_targets | n_coalition_contexts |
|---|---|---|---|---|---|---|---|
| artificial_sqli | catboost | CANONICALIZED | 0.779570 | 6 | 0 | 6 | 154 |
| artificial_sqli | catboost | RAW | 0.675986 | 4 | 2 | 6 | 154 |
| artificial_sqli | logistic | CANONICALIZED | 0.827957 | 6 | 0 | 6 | 154 |
| artificial_sqli | logistic | RAW | 0.690323 | 5 | 1 | 6 | 154 |
| artificial_sqli | mlp | CANONICALIZED | 0.859498 | 6 | 0 | 6 | 154 |
| artificial_sqli | mlp | RAW | 0.816846 | 6 | 0 | 6 | 154 |
| csic | catboost | CANONICALIZED | 0.540143 | 4 | 2 | 6 | 154 |
| csic | catboost | RAW | 0.580645 | 5 | 1 | 6 | 154 |
| csic | logistic | CANONICALIZED | 0.634767 | 6 | 0 | 6 | 154 |
| csic | logistic | RAW | 0.613262 | 4 | 2 | 6 | 154 |
| csic | mlp | CANONICALIZED | 0.483871 | 2 | 4 | 6 | 154 |
| csic | mlp | RAW | 0.614337 | 6 | 0 | 6 | 154 |
| ecml | catboost | CANONICALIZED | 0.683871 | 6 | 0 | 6 | 154 |
| ecml | catboost | RAW | 0.643011 | 4 | 2 | 6 | 154 |
| ecml | logistic | CANONICALIZED | 0.793190 | 5 | 1 | 6 | 154 |
| ecml | logistic | RAW | 0.785663 | 6 | 0 | 6 | 154 |
| ecml | mlp | CANONICALIZED | 0.815054 | 6 | 0 | 6 | 154 |
| ecml | mlp | RAW | 0.818638 | 6 | 0 | 6 | 154 |
| proprio | catboost | CANONICALIZED | 0.740502 | 6 | 0 | 6 | 154 |
| proprio | catboost | RAW | 0.352330 | 2 | 4 | 6 | 154 |
| proprio | logistic | CANONICALIZED | 0.774194 | 6 | 0 | 6 | 154 |
| proprio | logistic | RAW | 0.304301 | 0 | 6 | 6 | 154 |
| proprio | mlp | CANONICALIZED | 0.869176 | 6 | 0 | 6 | 154 |
| proprio | mlp | RAW | 0.516487 | 2 | 4 | 6 | 154 |
| site_cooking | catboost | CANONICALIZED | 0.445161 | 3 | 2 | 5 | 155 |
| site_cooking | catboost | RAW | 0.393548 | 2 | 3 | 5 | 155 |
| site_cooking | logistic | CANONICALIZED | 0.445161 | 1 | 4 | 5 | 155 |
| site_cooking | logistic | RAW | 0.393548 | 2 | 3 | 5 | 155 |
| site_cooking | mlp | CANONICALIZED | 0.329032 | 0 | 5 | 5 | 155 |
| site_cooking | mlp | RAW | 0.503226 | 4 | 1 | 5 | 155 |
| site_sqli | catboost | CANONICALIZED | 0.432258 | 2 | 3 | 5 | 155 |
| site_sqli | catboost | RAW | 0.425806 | 2 | 3 | 5 | 155 |
| site_sqli | logistic | CANONICALIZED | 0.264516 | 0 | 5 | 5 | 155 |
| site_sqli | logistic | RAW | 0.400000 | 1 | 4 | 5 | 155 |
| site_sqli | mlp | CANONICALIZED | 0.264516 | 1 | 4 | 5 | 155 |
| site_sqli | mlp | RAW | 0.477419 | 3 | 2 | 5 | 155 |
| srbh | catboost | CANONICALIZED | 0.528674 | 4 | 2 | 6 | 154 |
| srbh | catboost | RAW | 0.655914 | 6 | 0 | 6 | 154 |
| srbh | logistic | CANONICALIZED | 0.579211 | 4 | 2 | 6 | 154 |
| srbh | logistic | RAW | 0.700717 | 5 | 1 | 6 | 154 |
| srbh | mlp | CANONICALIZED | 0.742294 | 4 | 2 | 6 | 154 |
| srbh | mlp | RAW | 0.618638 | 4 | 2 | 6 | 154 |



### 8. Direct evidence of coalition-conditional contribution



Below are automatically selected largest-spread examples per model/view where the SAME source has positive and negative existing marginal effects for the SAME target AND pool size, but different base coalitions. Every displayed context has five matched seeds. These extrema illustrate conditionality, not population frequency or causality. The full qualifying table is `SOURCE_INTERACTIONS/tables/context_sign_reversals_same_target_and_size.csv`; negative_context_id/positive_context_id resolve original marginal_source_additions rows and before/after IDs.

| target | added_source | model | representation | n_sources_before | n_contexts | negative_base_sources | negative_delta_f1 | positive_base_sources | positive_delta_f1 | row_id |
|---|---|---|---|---|---|---|---|---|---|---|
| proprio | site_cooking | catboost | RAW | 3 | 10 | artificial_sqli+csic+ecml | -0.344132 | csic+ecml+srbh | 0.535213 | 75ef1a8320a5fcccf036f997 |
| srbh | proprio | logistic | RAW | 1 | 5 | artificial_sqli | -0.208468 | site_sqli | 0.570322 | 3d2b19d328db2bcb498b64ec |
| srbh | proprio | catboost | CANONICALIZED | 1 | 5 | site_cooking | -0.183824 | csic | 0.572680 | f07c87651f1b4ac2273b7047 |
| proprio | srbh | mlp | RAW | 2 | 10 | csic+ecml | -0.437932 | csic+site_cooking | 0.308430 | af742ca83d99718c554d7222 |
| ecml | site_sqli | logistic | CANONICALIZED | 2 | 10 | artificial_sqli+csic | -0.462521 | artificial_sqli+site_cooking | 0.035361 | 149882833114cfa7a509b6d8 |
| proprio | csic | mlp | CANONICALIZED | 1 | 5 | artificial_sqli | -0.296564 | srbh | 0.175891 | 751001cf0d41c927ff7ac61a |



### Interpretation limits and preservation



Adding a source may also change validation domains, early stopping and thresholds; the historical comparisons are not interventions that isolate only optimizer training data. Larger pools do not make a source intrinsically useful. No new statistical inference was performed. Causal source effects, universal source rankings, and sign-change claims comparing unmatched target cohorts are **NOT VERIFIED FOR PAPER**.

The existing source-count, marginal-distribution and stable-feature PDFs remain unchanged and are retained alongside the two new interaction views. The new tables live under SOURCE_INTERACTIONS/ to avoid modifying earlier validated analytical tables. No approved final experimental-design PDF was found in the existing figure/analysis directories; no such figure was invented.

## Data Sources and Traceability

Script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.
Inputs and output SHA-256: `ARTIFACT_MANIFEST.json`. Exact filters, columns and aggregation recipes: `TRACEABILITY.csv`.
Primary analytical input: `artigo/analise_resultados_tcc/_global/master_results.parquet`; only usable historical contribution/lex64/nonpilot models and RAW/CANONICALIZED, plus historical LODO C CatBoost IDs for features. No supplemental results are mixed in.
Every output table has row_id and experiment_ids. Resolve IDs with `SOURCE_LINEAGE.parquet`, which preserves original metric, feature-importance, manifest, predictions and score paths without opening those files. Nested-edge tables also expose before/after IDs; per-seed matches are in `derived/matched_source_additions_per_seed.parquet`. Formatting-only feature snapshot and original input-row IDs are preserved.
Seeds: equal weight within exact effective coalition; nested edges use only identical seeds. Coalition distribution: equal distinct effective pools after verified duplicate alias collapse. Target macro: equal outer-target means, not weighting by number of coalitions. Marginal effects: after minus before of saved F1/MCC/AP; sample SD uses ddof=1; quartiles use linear interpolation; |delta|≤1e-9 is numerical zero, not practical equivalence. No hypothesis tests, predictions, training or importance recomputation.
Generated tables/figures, source paths/row filters and formulas are listed in TRACEABILITY.csv. Exact source-value audits are in tables/derivation_audit.csv. Scientific coverage checks: tables/coalition_coverage.csv and tables/marginal_edge_coverage.csv. Unavailable or unsupported conclusions are explicitly NOT VERIFIED FOR PAPER.


Source-interaction extension: `SOURCE_INTERACTIONS/SOURCE_IDENTITY_RESULTS.md`, `SOURCE_INTERACTIONS/TRACEABILITY.csv` and `SOURCE_INTERACTIONS/ARTIFACT_MANIFEST.json`. Original pre-extension report preserved in SOURCE_INTERACTIONS/evidence/. The parent ARTIFACT_MANIFEST.json remains the historical pre-extension snapshot; its report hash is superseded only by the revision entry in the extension manifest.
