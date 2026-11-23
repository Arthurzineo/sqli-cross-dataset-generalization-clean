# Bases processadas

Contém `artificial`, `artificial_sqli`, `csic`, `ecml`, `site_sqli`,
`site_cooking` e `srbh`. A base restrita `proprio` não é incluída.

`historical/raw/` e `historical/canonicalized/` são as cópias históricas finais.
Seus hashes coincidem com `datasets/metadata/dataset_manifest.csv`.
`controlled/raw/` preserva as mesmas linhas RAW usadas no protocolo controlado.
`controlled/canonicalized/` decodifica as mesmas linhas sem deduplicá-las.
Por isso, suas contagens podem diferir das cópias históricas canonicalizadas.
`build_controlled_views.py` refaz as vistas pareadas sem bibliotecas externas.
`manifest.csv` registra coleção, representação, linhas, bytes e SHA-256.

Os arquivos XML/HTTP de origem do ECML e do CSIC não estão nesta pasta; somente
as cópias processadas usadas no estudo são incluídas. Consulte
`datasets/README.md` para os repositórios de origem.
Nenhum arquivo excede o limite de 100 MB do GitHub.
