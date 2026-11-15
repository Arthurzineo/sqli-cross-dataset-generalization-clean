# Varredura de segurança

Varredura final executada em 14 de novembro de 2026, antes da criação do
repositório Git.

- Ferramenta: gitleaks 8.30.1.
- Configuração: `.gitleaks.toml`.
- Escopo: toda a raiz desta pasta.
- Resultado: nenhuma ocorrência (`no leaks found`).
- Volume examinado pelo gitleaks: aproximadamente 546,38 MB.
- Busca pelo domínio institucional real: 0 linhas e 0 arquivos.
- Prefixo absoluto do diretório pessoal nos arquivos textuais tratados: 0 ocorrência.
- A busca recursiva pelo mesmo prefixo: 9 arquivos binários Parquet com metadados de
  procedência; nenhum é script, configuração ou documento de execução.
- Arquivos individuais acima de 100 MB: 0.

Os oito JWTs presentes nas quatro cópias de `site_sqli.csv` são dados
sintéticos e expirados do laboratório. A exceção correspondente está limitada
a esses caminhos e ao formato JWT HS256 em `.gitleaks.toml`.

As bases ECML e CSIC não são redistribuídas. A base `proprio` também permanece
fora do pacote por conter material operacional potencialmente sensível.
