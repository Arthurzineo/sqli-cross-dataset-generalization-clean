# Verificação local da Fase 2

A tabela macro LODO foi regenerada a partir das médias por alvo já salvas; não houve novo treinamento. A agregação é média entre sementes dentro do alvo na tabela de origem, seguida de média entre os sete alvos.

| modelo | representação | F1 recalculado | artigo (3 casas) | confere |
|---|---|---:|---:|---|
| catboost | CANONICALIZED | 0.893633 | 0.894 | True |
| catboost | RAW | 0.783927 | 0.784 | True |
| logistic | CANONICALIZED | 0.844105 | 0.844 | True |
| logistic | RAW | 0.733000 | 0.733 | True |
| mlp | CANONICALIZED | 0.866972 | 0.867 | True |
| mlp | RAW | 0.809730 | 0.810 | True |


- Todas as seis células conferem com o artigo após arredondamento: **True**.
- A figura LODO foi renderizada novamente por `scripts/render_final_manuscript_figures.py`.
- Auditoria do renderizador: `results/figures/data_plots/legacy_final/FIGURE_VALIDATION.json`.
- O renderizador registrou 27 verificações exatas de elementos e 603 valores-fonte para seis figuras, sem recomputação científica.
