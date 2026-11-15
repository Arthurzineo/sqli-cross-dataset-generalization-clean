# SQLi cross-dataset generalization

Material de código, rastreabilidade e resultados compactos do artigo **“O que
faz um detector de injeção de SQL generalizar? Um estudo empírico sobre
composição de bases, estabilidade de atributos, limiares de decisão e
canonicalização da entrada”**.

## Escopo

- todos os scripts relevantes encontrados para preparação, geração, coleta,
  treinamento, avaliação, robustez, estatística, tabelas e figuras;
- código ativo em `src/`, `scripts/`, `config/`, `analysis/` e `generators/`;
- resultados agregados necessários para conferir tabelas e figuras;
- sem predições completas por amostra, probabilidades completas, embeddings,
  caches ou checkpoints.

As bases ECML/PKDD e CSIC não são redistribuídas porque suas licenças de dados
não foram confirmadas. A base `proprio` não é redistribuída por conter material
potencialmente pessoal ou operacional. Consulte `datasets/README.md`.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `src/` | implementação ativa de dados, atributos, modelos e métricas |
| `scripts/` | pipeline executável na estrutura original do artigo |
| `config/` | datasets, modelos, sementes e grades experimentais |
| `experiments/` | cópias organizadas por histórico, controlado, robustez e exploração |
| `analysis/` | análises, estatística e renderização |
| `generators/` | artificial, sites de laboratório, CSIC, SR-BH e campanha OJS |
| `results/` | métricas e tabelas agregadas, sem artefatos por amostra |
| `docs/` | suplemento, segurança, atributos e instruções de reprodução |

## Ambiente

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
```

As versões registradas originalmente estão em
`environment/pip-freeze.txt` e `environment/environment.json`.

## Reprodução

O pipeline ativo preserva a organização esperada pelo código original:

```bash
python scripts/run_all.py --stage audit
python scripts/run_all.py --stage baseline
python scripts/run_all.py --stage pairwise
python scripts/run_all.py --stage lodo
python scripts/run_all.py --stage contribution
python scripts/run_all.py --stage statistics
python scripts/run_all.py --stage figures
```

As bases devem ser obtidas ou construídas antes dessas etapas. Consulte
`docs/reproducibility.md`. `--stage all` executa todas as etapas e não deve ser
usado como verificação rápida.

## Coleções experimentais

- Registro histórico: **16.650** execuções utilizáveis.
- Análise histórica de composição: **13.170** execuções.
- Coleção controlada: **1.434** execuções — 210 ID, 210 LODO, 984 remoções e
  30 execuções do classificador de origem.
- Robustez posterior: **829** ajustes fora desses totais.

Histórico e controlado são coleções distintas; 1.434 não deve ser subtraído de
16.650.

O registro histórico de 16.650 execuções contém 13.170 composições de fontes,
1.260 avaliações entre pares, 1.260 ablações, 210 baselines ID, 210 LODO C
completos, 210 LODO com embeddings, 180 LODO B e 150 LODO A. O artigo usa
diretamente as composições, a avaliação entre pares e o LODO C completo; este
último também sustenta a recorrência de atributos da Figura 6a.

## Rastreamento do artigo

A correspondência abaixo segue a numeração das duas versões do artigo.
Nesta tabela, `S` representa
`results/tables/manuscript_analysis/SUPPLEMENTAL_CONTROLLED_ANALYSIS`.

| Completa | Reduzida | Conteúdo | Dados/configuração | Script principal |
|---|---|---|---|---|
| Fig. 1 | Fig. 1 | fluxo do estudo | desenho metodológico | diagrama final fornecido pelo autor |
| Fig. 2 | Fig. 2 | protocolo LODO | `config/experiments.yaml` | diagrama final fornecido pelo autor |
| Fig. 3 | Fig. 3 | LODO e lacuna ID–OOD | `S/tables/lodo_by_target.csv`; `S/tables/id_ood_same_test.csv` | `scripts/analyze_supplemental_results.py` |
| Fig. 4 | Fig. 4 | número de fontes | `results/tables/manuscript_analysis/ADDITIONAL_MANUSCRIPT_ANALYSES/` | `analysis/manuscript_additional/additional_analyses.py` |
| Fig. 5 | Fig. 5 | ganho fonte–alvo | tabelas de interações entre fontes | `analysis/source_interactions/finalize_source_interactions.py` |
| Fig. 6 | Fig. 6 | atributos e Jaccard | tabelas de estabilidade e LODO C | `analysis/manuscript_additional/additional_analyses.py` |
| Tab. 1 | Tab. 1 | trabalhos relacionados | texto do artigo | edição LaTeX |
| Tab. 2 | Tab. 2 | bases | `datasets/metadata/dataset_manifest.csv` | `scripts/02_dataset_characterization/characterize.py` |
| Tab. 3 | Tab. B1 | modelos | `config/models.yaml` | `src/models/classical.py` |
| Tab. 4 | Tab. B2 | protocolos | `config/experiments.yaml` | `src/data/splits.py` |
| Tab. 5 | Tab. C3 | desempenho LODO macro | `S/tables/lodo_macro_summary.csv` | `scripts/analyze_supplemental_results.py` |
| Tab. 6 | Tab. C4 | contribuição marginal | `results/tables/manuscript_analysis/ADDITIONAL_MANUSCRIPT_ANALYSES/SOURCE_INTERACTIONS/tables/marginal_gain_by_added_source_and_pool_size.csv` | `analysis/source_interactions/finalize_source_interactions.py` |
| Tab. 7 | Tab. C5 | transferência de limiar | `S/tables/decision_by_target.csv` | `scripts/analyze_supplemental_results.py` |
| Tab. 8 | Tab. C6 | estabilidade | `S/tables/feature_stability.csv` | `scripts/analyze_supplemental_results.py` |
| Tab. 9 | Tab. C7 | separabilidade | `S/tables/separability.csv` | `scripts/analyze_supplemental_results.py` |
| Tab. 10 | Tab. D9 | robustez | `experiments/robustness/` | `experiments/robustness/consolidar_artefatos.py` |
| Tab. 11 | Tab. C8 | Wilcoxon da canonicalização | `S/statistics/tests_holm.csv` (família `canonicalization`) | `scripts/analyze_supplemental_results.py` |

Os estágios `07_shapley`, `13_embeddings` e `14_ablation` são exploratórios e
não fornecem resultados reportados no corpo ou nos apêndices do artigo final.

## Licença e citação

Nenhuma `LICENSE` foi criada: a licença ainda deve ser escolhida pelo autor.
Há um rascunho sem DOI em `CITATION.cff`.
