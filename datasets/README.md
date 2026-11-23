# Bases e disponibilidade

O repositório preserva scripts de obtenção/preparação, documentação, hashes e
metadados, e inclui em `processed/` as vistas finais usadas no estudo, exceto a
base restrita `proprio`.

| Base | Origem e licença | Geração/coleta e rotulagem | Família | N RAW | N CAN histórico |
|---|---|---|---|---:|---:|
| ECML/PKDD 2007 | [repositório do conjunto](https://gitlab.fing.edu.uy/gsi/web-application-attacks-datasets/-/tree/master/ecml_pkdd) e [página do desafio](https://www.lirmm.fr/pkdd2007-challenge/) | requisições do desafio; `SqlInjection` é ataque e `Valid` é benigno | `ecml` | 3.300 | 3.300 |
| HTTP CSIC 2010 | [repositório do conjunto](https://gitlab.fing.edu.uy/gsi/web-application-attacks-datasets/-/tree/master/csic_2010) e [página do CSIC](https://www.tic.itefi.csic.es/dataset/) | tráfego sintético de comércio eletrônico; derivação local `legitimate`/`sqli`/`xss`, usando legítimos e SQLi na tarefa binária | `csic` | 2.354 | 2.136 |
| SR-BH 2020 | Harvard Dataverse, CC0 1.0, DOI `10.7910/DVN/OGOIXX` | honeypot WordPress; CAPEC-66 é ataque e `000 - Normal` é benigno, com curadoria lexical documentada | `srbh` | 106.580 | 103.092 |
| `artificial_sqli` | base própria sintética | gerador parametrizado de SQLi; classe determinada pelo ramo de geração, com benignos do gerador original | `artificial` | 5.000 | 5.000 |
| `site_sqli` | base própria de laboratório | aplicação de documentação/fórum; navegação gera benignos e a campanha em GET, formulário, JSON e GraphQL gera ataques | `site_lab` | 9.122 | 9.122 |
| `site_cooking` | base própria de laboratório | aplicação culinária com termos SQL em linguagem natural; navegação gera benignos e a campanha controlada gera ataques | `site_lab` | 7.334 | 7.332 |
| `proprio` | coleta própria restrita | aplicação OJS; SQLi da campanha controlada (`sqli=1`, `xss=0`) e tráfego normal do período como benigno | `ojs` | 37.232 | 37.212 |

As vistas controladas são derivadas das mesmas linhas RAW; portanto, RAW e
CANONICALIZED têm o mesmo número de registros dentro desse protocolo. As
diferenças da última coluna pertencem às cópias históricas, preparadas e
deduplicadas separadamente. `proprio` permanece restrito. O arquivo XML de
origem do ECML e os arquivos HTTP originais do CSIC não são incluídos; o pacote
contém apenas as cópias processadas efetivamente usadas nos experimentos.

A variante auxiliar `artificial` também está em `processed/`: sua vista RAW
SQLi-only tem 5.000 registros e sua vista histórica canonicalizada tem 4.626
após deduplicação. Ela foi gerada pelo código de
[`generators/artificial_sqli/`](../generators/artificial_sqli/) e pertence à
mesma família de `artificial_sqli`; as duas não devem ser tratadas como fontes
independentes na mesma composição.

As cópias do srbh são um recorte filtrado da base pública SR-BH 2020 (CC0 1.0), coletada em um honeypot. O conteúdo das requisições, inclusive campos de formulário preenchidos por scanners como o OWASP ZAP, não foi alterado.

O manifesto dos 28 arquivos processados está em `processed/manifest.csv`.
As vistas históricas foram conferidas contra `metadata/dataset_manifest.csv`;
as vistas controladas preservam as mesmas linhas RAW e são reproduzíveis por
`processed/build_controlled_views.py`.
