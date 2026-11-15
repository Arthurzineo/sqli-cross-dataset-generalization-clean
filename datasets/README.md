# Bases e disponibilidade

Os dados não foram copiados indiscriminadamente para esta pasta. O repositório
preserva scripts de obtenção/preparação, documentação, hashes e metadados, e
inclui em `processed/` somente as vistas publicáveis de `artificial_sqli`,
`site_sqli`, `site_cooking` e `srbh`.

| Base | Origem e licença | Geração/coleta e rotulagem | Família | N RAW | N CAN histórico |
|---|---|---|---|---:|---:|
| ECML/PKDD 2007 | benchmark público; redistribuição não confirmada | requisições do desafio; `SqlInjection` é ataque e `Valid` é benigno | `ecml` | 3.300 | 3.300 |
| HTTP CSIC 2010 | benchmark público; redistribuição não confirmada | tráfego sintético de comércio eletrônico; derivação `legitimate`/`sqli`/`xss`, usando legítimos e SQLi na tarefa binária | `csic` | 2.354 | 2.136 |
| SR-BH 2020 | Harvard Dataverse, CC0 1.0, DOI `10.7910/DVN/OGOIXX` | honeypot WordPress; CAPEC-66 é ataque e `000 - Normal` é benigno, com curadoria lexical documentada | `srbh` | 106.580 | 103.092 |
| `artificial_sqli` | base própria sintética | gerador parametrizado de SQLi; classe determinada pelo ramo de geração, com benignos do gerador original | `artificial` | 5.000 | 5.000 |
| `site_sqli` | base própria de laboratório | aplicação de documentação/fórum; navegação gera benignos e a campanha em GET, formulário, JSON e GraphQL gera ataques | `site_lab` | 9.122 | 9.122 |
| `site_cooking` | base própria de laboratório | aplicação culinária com termos SQL em linguagem natural; navegação gera benignos e a campanha controlada gera ataques | `site_lab` | 7.334 | 7.332 |
| `proprio` | coleta própria restrita | aplicação OJS; SQLi da campanha controlada (`sqli=1`, `xss=0`) e tráfego normal do período como benigno | `ojs` | 37.232 | 37.212 |

As vistas controladas são derivadas das mesmas linhas RAW; portanto, RAW e
CANONICALIZED têm o mesmo número de registros dentro desse protocolo. As
diferenças da última coluna pertencem às cópias históricas, preparadas e
deduplicadas separadamente. ECML e CSIC são distribuídos apenas por instruções
de obtenção e preparação; `proprio` permanece restrito. As bases publicáveis
incluídas são `artificial_sqli`, `site_sqli`, `site_cooking` e `srbh`.

As cópias do srbh são um recorte filtrado da base pública SR-BH 2020 (CC0 1.0), coletada em um honeypot. O conteúdo das requisições, inclusive campos de formulário preenchidos por scanners como o OWASP ZAP, não foi alterado.

O manifesto dos 16 arquivos processados está em `processed/manifest.csv`.
As vistas históricas foram conferidas contra `metadata/dataset_manifest.csv`;
as vistas controladas preservam as mesmas linhas RAW e são reproduzíveis por
`processed/build_controlled_views.py`.
