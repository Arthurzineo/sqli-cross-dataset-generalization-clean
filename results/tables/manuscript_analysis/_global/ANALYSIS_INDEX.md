# Analysis Index

## Complemento controlado — RQ1 a RQ4

Folder: `artigo/analise_resultados_tcc/SUPPLEMENTAL_CONTROLLED_ANALYSIS/`

Status: análise pós-treinamento dos controles novos; limitações e verificações em `ANALYSIS_AUDIT.json`. O índice abaixo permanece referente à bateria histórica, sem misturar populações.

Method: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/ANALYSIS_METHOD.md`.
Results: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/RESULTS.md`.
Chapter guide: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/FINAL_TCC_RESULTS_GUIDE.md`.

Main tables: `tables/lodo_by_target.csv`, `tables/id_ood_same_test.csv`, `tables/source_contribution_by_target.csv`, `tables/decision_by_target.csv`, `tables/stable_features.csv`, `tables/canonicalization_by_target.csv`, `tables/separability.csv`, `statistics/tests_holm.csv`, `statistics/canonicalization_family_sensitivity.csv`, `tables/reproducibility_audit.csv` (todos relativos ao complemento).

Main figures: `figures/lodo_by_target.pdf`, `figures/id_ood_common_test_gap.pdf`, `figures/source_contribution.pdf`, `figures/canonicalization_effect.pdf`, `figures/controlled_separability.pdf`, `figures/selected_score_shift.pdf`.

Provenance: `SOURCE_FILES.parquet` e `TRACEABILITY.csv` do complemento; cada linha científica tem `row_id` e `experiment_ids`. Script: `artigo/scripts/analyze_supplemental_results.py`; comando igual ao script com o Python do projeto, registrado em `ANALYSIS_AUDIT.json`. O histórico continua válido somente com as ressalvas do seu protocolo; estes novos controles não corrigem retroativamente arquivos antigos.

---

## Methodology 4.1 -> Results 5.1

Folder: `M04_01_Experimental_Design__C05_01_Experimental_Coverage`

Status: Complete

Main tables:

- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/coverage_matrix.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/missing_runs.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/excluded_runs.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_counts.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_type.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_target.csv`

Main figures:


Method: `M04_01_Experimental_Design__C05_01_Experimental_Coverage/ANALYSIS_METHOD.md`

Results: `M04_01_Experimental_Design__C05_01_Experimental_Coverage/RESULTS.md`

---

## Methodology 4.2 -> Results 5.2

Folder: `M04_02_Datasets_Provenance__C05_02_Dataset_Characterization`

Status: Complete

Main tables:

- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_characterization.csv`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_class_distribution.csv`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_textual_characteristics.csv`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_provenance.csv`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/selected_class_controlled_lexical_differences.csv`

Main figures:

- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/figures/length_by_class.pdf`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/figures/encoding_by_class.pdf`

Method: `M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/ANALYSIS_METHOD.md`

Results: `M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/RESULTS.md`

---

## Methodology 4.3 -> Results 5.1

Folder: `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity`

Status: Partial

Main tables:

- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/duplicate_audit.csv`
- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/cross_dataset_overlap.csv`
- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/label_conflicts.csv`
- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/before_after_audit.csv`
- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/leakage_checks.csv`
- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/selected_split_hash_audit.csv`

Main figures:

- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/figures/cross_dataset_overlap.pdf`

Method: `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/ANALYSIS_METHOD.md`

Results: `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/RESULTS.md`

---

## Methodology 4.4 -> Results 5.2

Folder: `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization`

Status: Complete

Main tables:

- `artigo/analise_resultados_tcc/M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/engineered_features.csv`
- `artigo/analise_resultados_tcc/M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/representations.csv`
- `artigo/analise_resultados_tcc/M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/canonicalization_effects.csv`
- `artigo/analise_resultados_tcc/M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/embedding_metadata.csv`

Main figures:


Method: `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/ANALYSIS_METHOD.md`

Results: `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/RESULTS.md`

---

## Methodology 4.5 -> Results 5.2

Folder: `M04_05_Models_Training__C05_02_Model_Characterization`

Status: Complete

Main tables:

- `artigo/analise_resultados_tcc/M04_05_Models_Training__C05_02_Model_Characterization/tables/models.csv`
- `artigo/analise_resultados_tcc/M04_05_Models_Training__C05_02_Model_Characterization/tables/model_hyperparameters.csv`
- `artigo/analise_resultados_tcc/M04_05_Models_Training__C05_02_Model_Characterization/tables/model_run_counts.csv`
- `artigo/analise_resultados_tcc/M04_05_Models_Training__C05_02_Model_Characterization/tables/model_runtime.csv`
- `artigo/analise_resultados_tcc/M04_05_Models_Training__C05_02_Model_Characterization/tables/selected_configs_by_target.csv`

Main figures:


Method: `M04_05_Models_Training__C05_02_Model_Characterization/ANALYSIS_METHOD.md`

Results: `M04_05_Models_Training__C05_02_Model_Characterization/RESULTS.md`

---

## Methodology 4.6 -> Results 5.3

Folder: `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization`

Status: Partial

Main tables:

- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/ID/tables/id_results.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/pairwise_results.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/source_average.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/target_average.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/transfer_asymmetry.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/matrix_f1.csv`

Main figures:

- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_f1.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_mcc.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_pr_auc.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/lodo_RAW.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/gap_RAW.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/lodo_CANONICALIZED.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/gap_CANONICALIZED.pdf`

Method: `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/ANALYSIS_METHOD.md`

Results: `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/RESULTS.md`

---

## Methodology 4.7 -> Results 5.4

Folder: `M04_07_Source_Contribution__C05_04_RQ2_Contribution`

Status: Complete

Main tables:

- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_contribution_full.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_target_matrix_f1.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_target_matrix_mcc.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_summary.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/target_summary.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/negative_transfer.csv`

Main figures:

- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/figures/source_contribution.pdf`

Method: `M04_07_Source_Contribution__C05_04_RQ2_Contribution/ANALYSIS_METHOD.md`

Results: `M04_07_Source_Contribution__C05_04_RQ2_Contribution/RESULTS.md`

---

## Methodology 4.8 -> Results 5.5

Folder: `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration`

Status: Partial

Main tables:

- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_results.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_drift.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/oracle_gap.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/calibration_results.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/calibration_id_vs_ood.csv`

Main figures:

- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/figures/selected_score_distributions.pdf`

Method: `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/ANALYSIS_METHOD.md`

Results: `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/RESULTS.md`

---

## Methodology 4.9 -> Results 5.6

Folder: `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability`

Status: Complete

Main tables:

- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_rankings_by_target.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stable_features.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_stability.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_rank_correlations.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/jaccard_topk.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/source_removal_feature_effects.csv`

Main figures:

- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/figures/stable_features.pdf`

Method: `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/ANALYSIS_METHOD.md`

Results: `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/RESULTS.md`

---

## Methodology 4.10 -> Results 5.7

Folder: `M04_10_Canonicalization_Separability__C05_07_RQ4`

Status: Partial

Main tables:

- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/pairing_audit.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/paired_results.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/by_target.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/by_model.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/win_tie_loss.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/DATASET_SEPARABILITY/tables/separability_all.csv`

Main figures:


Method: `M04_10_Canonicalization_Separability__C05_07_RQ4/ANALYSIS_METHOD.md`

Results: `M04_10_Canonicalization_Separability__C05_07_RQ4/RESULTS.md`

---

## Methodology 4.11 -> Results 5.8

Folder: `M04_11_Statistics__C05_08_Statistical_Synthesis`

Status: Partial

Main tables:


Main figures:


Method: `M04_11_Statistics__C05_08_Statistical_Synthesis/ANALYSIS_METHOD.md`

Results: `M04_11_Statistics__C05_08_Statistical_Synthesis/RESULTS.md`

---

## Methodology 4.12 -> Results 5.9

Folder: `M04_12_Reproducibility__C05_09_Reproducibility`

Status: Partial

Main tables:

- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/runtime_summary.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/storage_summary.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/artifact_completeness.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/reproducibility_audit.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/selected_prediction_metric_audit.csv`

Main figures:


Method: `M04_12_Reproducibility__C05_09_Reproducibility/ANALYSIS_METHOD.md`

Results: `M04_12_Reproducibility__C05_09_Reproducibility/RESULTS.md`

---

## Methodology 4.13 -> Results NO EXPERIMENTAL RESULTS

Folder: `M04_13_AI_Use__NO_EXPERIMENTAL_RESULTS`

Status: Not applicable

---

## Data Sources and Traceability

Original inputs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`, `artigo/docs/experiment_registry/experiments.csv`, original dataset metadata/configuration, and selected predictions/features/splits only. Full paths and IDs: `_global/SOURCE_LINEAGE.parquet` and `_global/SOURCE_FILES.parquet`. Actual unique files read and byte counts: `_global/FILES_READ.parquet`, `_global/file_read_summary.csv`. No checkpoint content read.

Master table: `_global/master_results.parquet`; registry: `_global/run_registry.parquet`. Columns, exact row filters, groupings, artifacts/tables/figures and formulas are documented per section in TRACEABILITY.csv, ANALYSIS_METHOD.md and Metric Provenance. Seeds are averaged within condition; targets are the statistical units. Each reported value is linked to a table row_id with experiment_ids. Missing conditions are not imputed. Complete generated artifact catalog: `_global/ARTIFACT_CATALOG.csv`.

Script: `artigo/scripts/analysis/final_analysis.py`. Config: `artigo/scripts/analysis/config.json`. Command: `<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json`. Derived outputs are all within `artigo/analise_resultados_tcc/`. Follow each section's SOURCE_FILES.parquet for original metrics, predictions, scores, thresholds, features and manifests. Use trace_value.py for a specific cell.
