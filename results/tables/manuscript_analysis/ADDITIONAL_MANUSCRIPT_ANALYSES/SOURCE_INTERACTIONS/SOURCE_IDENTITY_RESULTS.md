# Source-interaction manuscript results

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

Script: `artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`. Command: `<PROJECT_ROOT>/../../venv/bin/python artigo/analise_resultados_tcc/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/scripts/finalize_source_interactions.py`.
Inputs: existing `ADDITIONAL_MANUSCRIPT_ANALYSES/tables/marginal_source_additions.csv` and .parquet, existing `derived/matched_source_additions_per_seed.parquet`, historical `_global/master_results.parquet` (metadata validation), and existing source lineage. No prediction, checkpoint, dataset payload or model file was read.
Per-table columns/filters/formulas: `SOURCE_INTERACTIONS/TRACEABILITY.csv` (relative to ADDITIONAL_MANUSCRIPT_ANALYSES). Full input/output SHA-256 and report revision: `SOURCE_INTERACTIONS/ARTIFACT_MANIFEST.json`. Each row carries experiment_ids; resolve them through `SOURCE_INTERACTIONS/SOURCE_LINEAGE.parquet`. The new derived target/source/pool table carries original context row IDs. Existing edge table supplies before/after experiment IDs; existing per-seed table supplies exact seed matches.
Seeds are already averaged inside exact nested coalition edges; these existing deltas were reused unchanged, validated against their saved seed-pair means. Analysis A: equal coalition-context means within each target/source/model/view/k, then equal targets. Analysis B: equal context means for each source/target/model/view across all eligible sizes, not equal weighting of size levels and not one addition order. n_seed_pairs counts context-specific pairs, not independent targets. SD is ddof=1. Sign tolerance1e-9 is numerical, not practical equivalence. No hypothesis tests.
Missing cells remain missing. Context counts differ combinatorially; related site sources and target-family exclusion limit independent diversity. k=5→6 has fewer eligible targets; sign-switch claims use k≤4 with identical target sets. Source pools mean effective training+validation files, not necessarily optimizer-only files. Validation changes are inherited from the historical procedure. Contributions are conditional/descriptive, not causal or intrinsic source quality.
