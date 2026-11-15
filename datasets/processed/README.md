# Bases processadas publicáveis

Contém somente `artificial_sqli`, `site_sqli`, `site_cooking` e `srbh`.

`historical/raw/` e `historical/canonicalized/` são as cópias históricas finais.
Seus hashes coincidem com `datasets/metadata/dataset_manifest.csv`.
`controlled/raw/` preserva as mesmas linhas RAW usadas no protocolo controlado.
`controlled/canonicalized/` decodifica as mesmas linhas sem deduplicá-las.
Por isso, suas contagens podem diferir das cópias históricas canonicalizadas.
`build_controlled_views.py` refaz as vistas pareadas sem bibliotecas externas.
`manifest.csv` registra coleção, representação, linhas, bytes e SHA-256.

ECML, CSIC e `proprio` não estão nesta pasta.
Nenhum arquivo excede o limite de 100 MB do GitHub.
