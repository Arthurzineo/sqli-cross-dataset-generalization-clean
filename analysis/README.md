# Análises

Scripts que transformam resultados salvos em tabelas, figuras e verificações,
sem retreinar os detectores.

- `manuscript_additional/additional_analyses.py`: tabelas e gráficos de número
  de fontes, adições marginais e recorrência dos atributos.
- `source_interactions/finalize_source_interactions.py`: tabelas e gráficos das
  interações fonte–alvo e fonte–coalizão.
- `render_final_manuscript_figures.py`: renderiza os gráficos analíticos salvos
  em `results/figures/data_plots/legacy_final/`, com rastreabilidade.
- `revise_manuscript_visuals.py`: revisa a apresentação dos gráficos antigos e
  salva auditoria dos valores plotados.
- `extrair_analises.py`: extrações específicas da revisão em
  `analises_revisao_v2/`; não é etapa do pipeline principal.
- `build_final_evidence_package.py`: empacota tabelas, recomendações e livro de
  verificação da documentação.

O inventário amplo de resultados é produzido pelas versões ativas em
`scripts/analysis/`.

Wilcoxon, Friedman, Holm e estabilidade também aparecem em
`scripts/16_statistics/`. Execute pela raiz do repositório e preserve IDs,
hashes e arquivos de origem nas saídas.
