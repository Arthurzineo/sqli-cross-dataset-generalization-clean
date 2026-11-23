# Reprodução

## 1. Ambiente

Crie um ambiente virtual e instale `environment/requirements.txt`. Não presuma
que caminhos absolutos preservados em documentos históricos sejam válidos.

## 2. Dados

As cópias processadas de `artificial`, `artificial_sqli`, `csic`, `ecml`,
`site_sqli`, `site_cooking` e `srbh` estão em `datasets/processed/`. O arquivo
`config/datasets.yaml` aponta para as vistas históricas RAW e CANONICALIZED por
caminhos relativos à raiz do repositório.

Os arquivos de origem do ECML/PKDD 2007 e HTTP CSIC 2010 não são necessários
para executar os experimentos a partir das cópias processadas. Para refazer a
preparação desde a origem, consulte os repositórios e páginas citados em
`datasets/sources/README.md` e execute os scripts de `datasets/sources/ecml/`,
`datasets/sources/csic/` e `generators/csic_labeling/`. O XML de origem do ECML
não integra este repositório. A base `proprio` é restrita e só pode ser
configurada por quem tenha autorização para usar e sanitizar a coleta.

## 3. Preparação e auditoria

```bash
python scripts/run_all.py --stage setup
python scripts/run_all.py --stage audit
python scripts/run_all.py --stage characterize
```

## 4. Experimentos

Execute individualmente `baseline`, `pairwise`, `lodo` e `contribution`. As
sementes e hiperparâmetros estão em `config/`. A coleção controlada usa
`scripts/supplemental/`; os experimentos posteriores usam
`experiments/robustness/run_experimentos.py`.

## 5. Análises e figuras

```bash
python scripts/run_all.py --stage statistics
python scripts/run_all.py --stage figures
python scripts/render_final_manuscript_figures.py --overwrite
```

As tabelas já consolidadas estão em `results/`; os artefatos por amostra foram
deliberadamente excluídos e precisam ser regenerados para análises novas.
