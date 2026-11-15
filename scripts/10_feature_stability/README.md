# 10 — Estabilidade de features

`compute_importance.py EXP_ID --method permutation` gera importância pós-hoc (ou `native`/`shap`) sem usá-la para selecionar o fold. `analyze_stability.py` compara rankings por Spearman, Kendall e Jaccard top-10.
