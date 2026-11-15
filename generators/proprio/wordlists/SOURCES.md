# Fontes das wordlists de payload

Registro das origens usadas para montar os corpora de payloads SQLi e XSS deste
projeto. Todas são repositórios públicos do GitHub, coletados manualmente para
uso em **laboratório autorizado**. Os arquivos baixados **não são versionados**
(ver `.gitignore`); este documento + `MANIFEST.sha256` garantem a rastreabilidade.

- **Data de coleta:** 2026-07-29
- **Consolidação:** por categoria, **preservando bytes de controle** (`\r`,
  null bytes) por serem parte de ataques (CRLF / null-byte injection); remove
  apenas linhas de tamanho zero e **duplicatas exatas** (byte-a-byte). Resultado
  em `custom/sqli.txt` e `custom/xss.txt`.
- **Payloads destrutivos são mantidos** (DROP/DELETE/TRUNCATE/`xp_cmdshell`/
  `EXEC`/`INTO OUTFILE` etc.) — necessários para a completude do dataset. Nenhum
  payload é filtrado por conteúdo.
- **Integridade:** hash SHA-256 de cada arquivo de origem e consolidado em
  `wordlists/MANIFEST.sha256`.

---

## SQL Injection

| Fonte | Repositório | Caminho no repo | Arquivos | Destino local |
|---|---|---|---|---|
| PayloadsAllTheThings | `github.com/swisskyrepo/PayloadsAllTheThings` | `SQL Injection/Intruder/*.txt` | 15 | `payloadsallthethings/sqli/` |
| SecLists | `github.com/danielmiessler/SecLists` | `Fuzzing/login_bypass.txt` + `Fuzzing/Databases/*.txt` | 6 | `seclists/sqli/` |
| FuzzDB | `github.com/fuzzdb-project/fuzzdb` | `attack/sql-injection/{detect,exploit,payloads-sql-blind}/*.txt` | 18 | `fuzzdb/sqli/` |
| payload-box | `github.com/payload-box/sql-injection-payload-list` | `*.txt` na raiz (mssql/mysql/oracle/postgresql/sqlite + burp-intruder) | 6 | `payload-box/sqli/` |

**Consolidado (web, limpo):** `wordlists/base/sqli-web.txt` — **2.276 payloads
únicos** (bruto 3.480 − 1.204 de lixo HTML/CSS). Compõe o dataset final de 15k.

## Cross-Site Scripting (XSS)

| Fonte | Repositório | Caminho no repo | Arquivos | Destino local |
|---|---|---|---|---|
| PayloadsAllTheThings | `github.com/swisskyrepo/PayloadsAllTheThings` | `XSS Injection/Intruders/*.txt` | 15 | `payloadsallthethings/xss/` |
| SecLists | `github.com/danielmiessler/SecLists` | `Fuzzing/XSS/robot-friendly/*.txt` + `Fuzzing/XSS/Polyglots/*.txt` + `Fuzzing/URI-XSS.fuzzdb.txt` | 20 | `seclists/xss/` |

**Consolidado (web, limpo):** `wordlists/base/xss-web.txt` — **9.841 payloads
únicos** (bruto 10.836 − 995 de lixo HTML/CSS). Compõe o dataset final de 15k.

---

## Licenças

Cada repositório tem sua própria licença — consulte o `LICENSE` no upstream
antes de redistribuir. Uso aqui é acadêmico/laboratorial. Referências:

- PayloadsAllTheThings — MIT (ver `LICENSE` no repo).
- SecLists — MIT (ver `LICENSE` no repo).
- FuzzDB — licença própria (Creative Commons / GPL; ver `_copyright.txt`/`LICENSE`).
- payload-box/sql-injection-payload-list — ver `LICENSE` no repo.

> Os créditos pertencem aos autores/mantenedores originais de cada projeto.

---

## Como reobter

Os arquivos foram baixados via API de conteúdo do GitHub
(`api.github.com/repos/<owner>/<repo>/contents/<path>` → campo `download_url`)
e `raw.githubusercontent.com`. Para atualizar, repita a coleta a partir dos
caminhos acima e refaça a consolidação + `MANIFEST.sha256`.

## Não usado (decisão de escopo)

Variações com **encoding** (URL/double-URL/HTML) em `wordlists/generated/` **não**
são geradas — os encoders/tampers das próprias ferramentas (sqlmap/dalfox) cobrem
isso em tempo de execução.
