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
## Data Sources and Traceability

Script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/scripts/additional_analyses.py`.
Inputs and output SHA-256: `ARTIFACT_MANIFEST.json`. Exact filters, columns and aggregation recipes: `TRACEABILITY.csv`.
Primary analytical input: `artigo/analise_resultados_tcc/_global/master_results.parquet`; only usable historical contribution/lex64/nonpilot models and RAW/CANONICALIZED, plus historical LODO C CatBoost IDs for features. No supplemental results are mixed in.
Every output table has row_id and experiment_ids. Resolve IDs with `SOURCE_LINEAGE.parquet`, which preserves original metric, feature-importance, manifest, predictions and score paths without opening those files. Nested-edge tables also expose before/after IDs; per-seed matches are in `derived/matched_source_additions_per_seed.parquet`. Formatting-only feature snapshot and original input-row IDs are preserved.
Seeds: equal weight within exact effective coalition; nested edges use only identical seeds. Coalition distribution: equal distinct effective pools after verified duplicate alias collapse. Target macro: equal outer-target means, not weighting by number of coalitions. Marginal effects: after minus before of saved F1/MCC/AP; sample SD uses ddof=1; quartiles use linear interpolation; |delta|≤1e-9 is numerical zero, not practical equivalence. No hypothesis tests, predictions, training or importance recomputation.
Generated tables/figures, source paths/row filters and formulas are listed in TRACEABILITY.csv. Exact source-value audits are in tables/derivation_audit.csv. Scientific coverage checks: tables/coalition_coverage.csv and tables/marginal_edge_coverage.csv. Unavailable or unsupported conclusions are explicitly NOT VERIFIED FOR PAPER.
