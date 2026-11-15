# Wordlists

Este projeto **localiza** wordlists existentes, mas **não as baixa automaticamente**
pelos scripts de sweep. Os payloads de terceiros foram coletados manualmente e
os datasets sintéticos são gerados localmente (sem rede).

## Variáveis esperadas

```bash
SECLISTS_DIR=/opt/SecLists
PAYLOADS_ALL_THE_THINGS_DIR=/opt/PayloadsAllTheThings
FUZZDB_DIR=/opt/fuzzdb
CUSTOM_WORDLIST_DIR=./wordlists/custom
```

## Estrutura

- `custom/` — listas usadas pelos sweeps. `sqli.txt` e `xss.txt` são os
  **datasets finais de 15.000 payloads** (corpus real + sintéticos). Só os
  `*.example` são versionados.
- `base/` — corpus **real** consolidado da web, **limpo** de lixo não-payload
  (`sqli-web.txt`=2.276, `xss-web.txt`=9.841); o bruto fica em `*-web.raw.txt`.
  Fonte estável para (re)gerar o dataset. Não versionado.
- `synthetic/` — apenas os payloads **sintéticos novos** + `labels.tsv`
  (rastreabilidade: `sha256 | tipo | gerador | técnica`). Não versionado.
- `dataset/` — cópias dos finais de 15k + `manifest.json`. Não versionado.
- `payloadsallthethings/`, `seclists/`, `fuzzdb/`, `payload-box/` — arquivos
  originais de terceiros. Não versionados.

## Fontes de terceiros

Ver [`SOURCES.md`](SOURCES.md) (repos, caminhos, licenças) e
[`STATS.md`](STATS.md) (original × após deduplicação por lista). Resumo:

- **SQLi:** PayloadsAllTheThings + SecLists + FuzzDB + payload-box → `base/sqli-web.txt` (**2.276** únicos, após limpeza).
- **XSS:** PayloadsAllTheThings + SecLists → `base/xss-web.txt` (**9.841** únicos, após limpeza).

Consolidação **preserva bytes de controle** (`\r`, null) e **mantém payloads
destrutivos** (DROP/DELETE/`xp_cmdshell`/etc.); remove linhas vazias, duplicatas
byte-exatas e **lixo não-payload** (base64 de fonte/imagem e CSS que vieram como
dump de HTML em 2 arquivos de origem). Integridade em `MANIFEST.sha256`.

## Datasets finais (15.000 por tipo)

`scripts/generate-payloads.py` preenche o déficit até 15.000 com payloads
**sintéticos**, preservando 100% do `base/` e escrevendo em `custom/`:

```bash
python3 scripts/generate-payloads.py            # gera sqli e xss
python3 scripts/generate-payloads.py --check    # revalida
```

- `custom/sqli.txt` — **15.000** (2.276 reais limpos + 12.724 sintéticos).
- `custom/xss.txt` — **15.000** (9.841 reais limpos + 5.159 sintéticos).

Geração usa **3 geradores estruturais por tipo** (booleano/tautologia,
técnica/SGBD, mutação estrutural — para SQLi; tag/evento, mutação, polyglot —
para XSS), com dedup byte-exato, embaralhamento por seed e rótulos em
`synthetic/labels.tsv`.

> **Sem encoding.** As variações sintéticas são **estruturais** (não há
> URL/HTML/unicode encode) — decisão de escopo; os encoders/tampers das próprias
> ferramentas cobrem encoding em tempo de execução. **Sem marcadores** dentro do
> payload (rastreabilidade fica em `labels.tsv`).

> Nenhuma wordlist é baixada pelos **scripts de sweep**. Traga as suas e ajuste
> os caminhos.
