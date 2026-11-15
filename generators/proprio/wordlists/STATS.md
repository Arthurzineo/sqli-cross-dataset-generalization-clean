# Estatisticas das wordlists (web) - original x apos deduplicacao

- Gerado em: 2026-07-29T11:45:59Z
- **Linhas**: linhas nao-vazias do arquivo original.
- **Unicas na lista**: distintas dentro do proprio arquivo.
- **Novos apos dedup**: quantas linhas daquela lista entraram no consolidado
  (atribuidas a *primeira* lista que introduziu cada payload, na ordem de
  processamento). A soma da coluna = total consolidado unico.
- Preserva bytes de controle; mantem payloads destrutivos (ver `SOURCES.md`).

## SQL Injection - consolidado: 3480 payloads unicos

| Fonte | Lista | Linhas | Unicas na lista | Novos apos dedup |
|---|---|---:|---:|---:|
| PayloadsAllTheThings | `Auth_Bypass.txt` | 78 | 78 | 78 |
| PayloadsAllTheThings | `Auth_Bypass2.txt` | 121 | 119 | 117 |
| PayloadsAllTheThings | `FUZZDB_MSSQL-WHERE_Time.txt` | 40 | 40 | 40 |
| PayloadsAllTheThings | `FUZZDB_MSSQL.txt` | 17 | 17 | 16 |
| PayloadsAllTheThings | `FUZZDB_MSSQL_Enumeration.txt` | 15 | 15 | 15 |
| PayloadsAllTheThings | `FUZZDB_MYSQL.txt` | 6 | 6 | 6 |
| PayloadsAllTheThings | `FUZZDB_MySQL-WHERE_Time.txt` | 45 | 45 | 45 |
| PayloadsAllTheThings | `FUZZDB_MySQL_ReadLocalFiles.txt` | 3 | 3 | 3 |
| PayloadsAllTheThings | `FUZZDB_Oracle.txt` | 55 | 55 | 54 |
| PayloadsAllTheThings | `FUZZDB_Postgres_Enumeration.txt` | 20 | 19 | 19 |
| PayloadsAllTheThings | `Generic_ErrorBased.txt` | 154 | 154 | 154 |
| PayloadsAllTheThings | `Generic_Fuzz.txt` | 12 | 12 | 12 |
| PayloadsAllTheThings | `Generic_TimeBased.txt` | 105 | 105 | 105 |
| PayloadsAllTheThings | `Generic_UnionSelect.txt` | 424 | 421 | 421 |
| PayloadsAllTheThings | `SQLi_Polyglots.txt` | 2 | 2 | 2 |
| **PayloadsAllTheThings - subtotal** | 15 listas | **1097** | | **1087** |
| SecLists | `MSSQL-Enumeration.fuzzdb.txt` | 15 | 15 | 0 |
| SecLists | `MySQL-Read-Local-Files.fuzzdb.txt` | 3 | 3 | 0 |
| SecLists | `OracleDB-SID.txt` | 570 | 568 | 568 |
| SecLists | `Postgres-Enumeration.fuzzdb.txt` | 20 | 19 | 1 |
| SecLists | `db2enumeration.fuzzdb.txt` | 12 | 12 | 12 |
| SecLists | `login_bypass.txt` | 896 | 896 | 716 |
| **SecLists - subtotal** | 6 listas | **1516** | | **1297** |
| FuzzDB | `GenericBlind.txt` | 31 | 31 | 21 |
| FuzzDB | `Generic_SQLI.txt` | 0 | 0 | 0 |
| FuzzDB | `MSSQL.txt` | 12 | 12 | 4 |
| FuzzDB | `MSSQL_blind.txt` | 8 | 8 | 8 |
| FuzzDB | `MySQL.txt` | 9 | 9 | 3 |
| FuzzDB | `MySQL_MSSQL.txt` | 9 | 9 | 9 |
| FuzzDB | `oracle.txt` | 54 | 54 | 0 |
| FuzzDB | `xplatform.txt` | 193 | 193 | 167 |
| FuzzDB | `db2-enumeration.txt` | 12 | 12 | 0 |
| FuzzDB | `ms-sql-enumeration.txt` | 11 | 11 | 0 |
| FuzzDB | `mysql-injection-login-bypass.txt` | 5 | 5 | 5 |
| FuzzDB | `mysql-read-local-files.txt` | 1 | 1 | 0 |
| FuzzDB | `postgres-enumeration.txt` | 19 | 18 | 0 |
| FuzzDB | `payloads-sql-blind-MSSQL-INSERT.txt` | 107 | 107 | 107 |
| FuzzDB | `payloads-sql-blind-MSSQL-WHERE.txt` | 40 | 40 | 0 |
| FuzzDB | `payloads-sql-blind-MySQL-INSERT.txt` | 90 | 90 | 90 |
| FuzzDB | `payloads-sql-blind-MySQL-ORDER_BY.txt` | 18 | 18 | 18 |
| FuzzDB | `payloads-sql-blind-MySQL-WHERE.txt` | 45 | 45 | 0 |
| **FuzzDB - subtotal** | 18 listas | **664** | | **432** |
| payload-box | `burp-intruder-payloads.txt` | 105 | 89 | 81 |
| payload-box | `mssql-payloads.txt` | 13 | 13 | 7 |
| payload-box | `mysql-payloads.txt` | 21 | 21 | 7 |
| payload-box | `oracle-payloads.txt` | 11 | 11 | 7 |
| payload-box | `postgresql-payloads.txt` | 15 | 15 | 8 |
| payload-box | `sqlite-payloads.txt` | 797 | 554 | 554 |
| **payload-box - subtotal** | 6 listas | **962** | | **664** |
| **TOTAL** | | **4239** (bruto) | | **3480** (consolidado unico) |

## XSS - consolidado: 10836 payloads unicos

| Fonte | Lista | Linhas | Unicas na lista | Novos apos dedup |
|---|---|---:|---:|---:|
| PayloadsAllTheThings | `0xcela_event_handlers.txt` | 105 | 105 | 105 |
| PayloadsAllTheThings | `BRUTELOGIC-XSS-JS.txt` | 17 | 17 | 17 |
| PayloadsAllTheThings | `BRUTELOGIC-XSS-STRINGS.txt` | 110 | 110 | 110 |
| PayloadsAllTheThings | `IntrudersXSS.txt` | 179 | 176 | 68 |
| PayloadsAllTheThings | `JHADDIX_XSS.txt` | 110 | 107 | 107 |
| PayloadsAllTheThings | `MarioXSSVectors.txt` | 274 | 250 | 250 |
| PayloadsAllTheThings | `RSNAKE_XSS.txt` | 73 | 73 | 72 |
| PayloadsAllTheThings | `XSSDetection.txt` | 202 | 202 | 139 |
| PayloadsAllTheThings | `XSS_Polyglots.txt` | 16 | 16 | 5 |
| PayloadsAllTheThings | `jsonp_endpoint.txt` | 57 | 56 | 56 |
| PayloadsAllTheThings | `port_swigger_xss_cheatsheet_event_handlers.txt` | 114 | 114 | 114 |
| PayloadsAllTheThings | `xss_alert.txt` | 667 | 654 | 654 |
| PayloadsAllTheThings | `xss_alert_identifiable.txt` | 667 | 665 | 621 |
| PayloadsAllTheThings | `xss_payloads_quick.txt` | 39 | 34 | 34 |
| PayloadsAllTheThings | `xss_swf_fuzz.txt` | 24 | 24 | 24 |
| **PayloadsAllTheThings - subtotal** | 15 listas | **2654** | | **2376** |
| SecLists | `URI-XSS.fuzzdb.txt` | 5 | 5 | 5 |
| SecLists | `XSS-BruteLogic.txt` | 114 | 113 | 3 |
| SecLists | `XSS-Bypass-Strings-BruteLogic.txt` | 17 | 17 | 0 |
| SecLists | `XSS-Cheat-Sheet-PortSwigger.txt` | 6047 | 6047 | 6040 |
| SecLists | `XSS-EnDe-evation.txt` | 164 | 164 | 160 |
| SecLists | `XSS-EnDe-h4k.txt` | 206 | 204 | 134 |
| SecLists | `XSS-EnDe-mario.txt` | 52 | 52 | 31 |
| SecLists | `XSS-EnDe-xssAttacks.txt` | 109 | 109 | 8 |
| SecLists | `XSS-Fuzzing.txt` | 3807 | 556 | 473 |
| SecLists | `XSS-Jhaddix.txt` | 110 | 107 | 3 |
| SecLists | `XSS-OFJAAAH.txt` | 797 | 554 | 553 |
| SecLists | `XSS-Polyglot-Ultimate-0xsobky.txt` | 1 | 1 | 0 |
| SecLists | `XSS-Polyglots-Dmiessler.txt` | 11 | 11 | 0 |
| SecLists | `XSS-Polyglots.txt` | 14 | 14 | 0 |
| SecLists | `XSS-RSNAKE.txt` | 73 | 73 | 0 |
| SecLists | `XSS-Somdev.txt` | 22 | 22 | 22 |
| SecLists | `XSS-Vectors-Mario.txt` | 137 | 137 | 135 |
| SecLists | `XSS-innerht-ml.txt` | 49 | 48 | 48 |
| SecLists | `XSS-payloadbox.txt` | 2690 | 1544 | 837 |
| SecLists | `xss-without-parentheses-semi-colons-portswigger.txt` | 8 | 8 | 8 |
| **SecLists - subtotal** | 20 listas | **14433** | | **8460** |
| **TOTAL** | | **17087** (bruto) | | **10836** (consolidado unico) |

## Limpeza de lixo (nao-payloads)

Dois arquivos de origem vieram com uma PAGINA HTML inteira embutida (CSS reset,
base64 de fonte/imagem, SVG path, JS da UI "spoiler", barras de progresso,
tutorial e uma pagina de bloqueio do Kaspersky): `seclists/xss/XSS-OFJAAAH.txt`
e `payload-box/sqli/sqlite-payloads.txt`. O consolidador
`scripts/consolidate-corpus.py` aplica filtro AGRESSIVO nesses 2 arquivos
(mantendo so linhas com indicador de ataque real) e conservador nos demais;
tudo que tem tag `<` com sink de ataque e preservado. Bruto em `*-web.raw.txt`,
limpo em `*-web.txt`.

Inclui uma segunda passada de limpeza, removendo também comandos `pwd`,
`perl -e`, fixtures `Redirect 302`/admin e JavaScript de página
(`getTextWidth`, `copiedTextStub`, `nodesChild`, `getCssStyle`, `nodeValue`).

| Tipo | Web bruto | Removido (lixo) | Real LIMPO |
|---|---:|---:|---:|
| SQLi | 3480 | 1204 | 2276 |
| XSS  | 10836 | 995 | 9841 |

## Geracao artificial — CONCLUIDA

Sinteticos ESTRUTURAIS (sem encoding, sem marcadores no payload) gerados por
`scripts/generate-payloads.py`, preservando 100% do corpus real LIMPO. Dataset
final em `wordlists/custom/{sqli,xss}.txt`; rotulos em `synthetic/labels.tsv`.

| Tipo | Real limpo | Sintetico | **Final unico** |
|---|---:|---:|---:|
| SQLi | 2276 | 12724 | **15000** |
| XSS  | 9841 | 5159 | **15000** |

Validado: 15000 linhas byte-unicas por tipo; base 100% presente; encoding=0 e
marcadores=0 nos sinteticos; 0 tokens de pagina no SQLi (1 falso-positivo no XSS
= payload real); maior linha SQLi=315, XSS=3065 (sem base64/CSS/JS de pagina).
