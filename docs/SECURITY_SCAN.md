# Varredura de segurança

Varredura final executada em 23 de novembro de 2026 sobre a árvore de trabalho.

- Ferramenta: gitleaks 8.30.1.
- Configuração: `.gitleaks.toml`.
- Escopo: toda a raiz desta pasta.
- Resultado: nenhuma ocorrência (`no leaks found`).
- Volume examinado pelo gitleaks: aproximadamente 523,59 MB.
- Busca pelo domínio institucional real: 0 linhas e 0 arquivos.
- Prefixo absoluto do diretório pessoal nos arquivos textuais tratados: 0 ocorrência.
- A busca recursiva pelo mesmo prefixo: 9 arquivos binários Parquet com metadados de
  procedência; nenhum é script, configuração ou documento de execução.
- Arquivos individuais acima de 100 MB: 0.

Os oito JWTs presentes nas quatro cópias de `site_sqli.csv` são dados
sintéticos e expirados do laboratório. A exceção correspondente está limitada
a esses caminhos e ao formato JWT HS256 em `.gitleaks.toml`.

As cópias processadas usadas no estudo de ECML e CSIC estão incluídas; os
arquivos-fonte originais não integram o repositório. A base `proprio` permanece
fora do pacote por conter material operacional potencialmente sensível.
