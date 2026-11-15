# Partições experimentais

Manifestos das partições persistidas da coleção controlada.

`controlled/` contém os JSONs identificados pelo hash do split.
Cada manifesto registra cache, arquivo de partição, SHA-256 e contagens.
Os caminhos de arquivo aparecem relativos a `<PROJECT_ROOT>`, a raiz do projeto original.
Os arquivos Parquet volumosos correspondentes não foram duplicados aqui.
Consulte `docs/external-artifacts.md` para os artefatos não versionados.

As partições separam treino, validação e teste por hash canônico.
Não edite os manifests existentes: isso rompe a rastreabilidade dos IDs.
Novas execuções devem gerar novos identificadores.
O código de construção está em `scripts/supplemental/common.py`.
