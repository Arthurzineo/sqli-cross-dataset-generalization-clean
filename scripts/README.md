# Índice do pipeline

Os estágios devem ser executados pela raiz, preferencialmente via `run_all.py`.

- `00_setup`–`02_dataset_characterization`: ambiente, auditoria e bases.
- `03_baseline_id`: referência intrabase da QP1.
- `04_pairwise_cross_dataset`: transferências diretas da QP1.
- `05_lodo`: avaliação multifonte principal da QP1.
- `06_dataset_contribution`: coalizões e contribuições da QP2.
- `07_shapley`: exploratório, não reportado no artigo final.
- `08_threshold`–`10_feature_stability`: diagnósticos da QP3.
- `11_raw_vs_decoded`–`12_dataset_separability`: análises da QP4.
- `13_embeddings` e `14_ablation`: exploratórios, não reportados.
- `15_error_analysis`–`17_figures_tables`: erros, estatística e saídas.
- `supplemental/`: coleção controlada, remoções e separabilidade.

Leia o README de cada estágio antes de executar treinamentos.
