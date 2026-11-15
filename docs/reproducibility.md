# Reprodução

## 1. Ambiente

Crie um ambiente virtual e instale `environment/requirements.txt`. Não presuma
que caminhos absolutos preservados em documentos históricos sejam válidos.

## 2. Dados

As quatro bases redistribuíveis já estão em `datasets/processed/`. O arquivo
`config/datasets.yaml` aponta para as vistas históricas RAW e CANONICALIZED de
`artificial_sqli`, `site_sqli`, `site_cooking` e `srbh` por caminhos relativos
à raiz do repositório.

ECML/PKDD 2007 e HTTP CSIC 2010 não são redistribuídos. Obtenha os arquivos de
origem conforme `datasets/sources/README.md`, confira seus termos de uso e
execute os scripts de preparação de `datasets/sources/ecml/` e
`datasets/sources/csic/`. Coloque as cópias binárias finais nestes caminhos:

```text
datasets/external/ecml/raw/ecml.csv
datasets/external/ecml/canonicalized/ecml.csv
datasets/external/csic/raw/csic.csv
datasets/external/csic/canonicalized/csic.csv
```

Para ECML, a preparação parte de `learning_dataset.xml`; para CSIC, parte da
derivação rotulada descrita em `generators/csic_labeling/README.md`. Os nomes,
separadores, colunas e codificações esperados constam de
`config/datasets.yaml`. A base `proprio` é restrita e só pode ser configurada
por quem tenha autorização para usar e sanitizar a coleta.

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
