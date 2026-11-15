# ECML/PKDD 2007

Segundo corpus alvo, de procedência totalmente distinta: coletado pela Gemius SA
(agência de pesquisa de mercado) em 4 semanas de tráfego na Europa
Central/Oriental, 2007.

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `datasets/preparar_ecml.py` (a montante) | `datasets/ecml_sqli_xss_balanceado_decodificado.csv` |
| 2 | `../../scripts/filtrar_sqli.py` | `datasets/decodificados/ecml_balanceado_decodificado_sqli.csv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/ecml_balanceado_decodificado_sqli.csv` |
| 1b | `../../scripts/preparar_ecml_codificado.py` | `datasets/originais/ecml_balanceado_sqli.csv` |
| 2b | `../../scripts/deduplicar_codificados.py` | `datasets/deduplicados_codificados/ecml_balanceado_sqli.csv` |

## Números

| etapa | n | SQLi | benignas |
|---|---|---|---|
| desafio original | 50.116 | — | — |
| após preparação | 6.326 | 1.650 | 3.163 |
| após filtro SQLi | 3.300 | 1.650 | 1.650 |
| **final (deduplicado)** | **3.300** | **1.650** | **1.650** |

Mantido: **100 %** — zero duplicatas, zero conflitos.

## Decisões

**1.513 amostras de XSS descartadas** nesta fase.

**Herdadas da preparação original** (ver `datasets/ECML_PKDD_2007.md`):
9.090 amostras de tipo fora do escopo, 2.180 multi-rótulo e 677 com o ataque
apenas em cabeçalho HTTP foram descartadas — esta última porque `montar_texto`
lê URL + body e não lê cabeçalho, então mantê-las injetaria falsos negativos que
medem a limitação do extrator, não a do modelo.

**Nenhuma decisão nova nesta fase.** O corpus passou íntegro pela deduplicação.

## Qualidade de rótulo — íntegro

Aplicado o mesmo critério estrito usado no SR-BH (`PADRAO_SQL_ESTRITO`, em
`../../scripts/analisar_rotulos.py`): **1.650 de 1.650 (100 %) têm sintaxe SQL
real.** Nenhum corte foi necessário.

### O critério precisou ser corrigido por causa deste corpus

Na primeira medição o ECML apareceu como o pior dos seis — 74,4 %, com 361
ataques sem sintaxe SQL. **Era erro do critério, não do corpus.** Os payloads do
ECML usam formas de evasão que a regex não cobria:

| forma | exemplo |
|---|---|
| remoção de espaço | `'UNIONALLSELECTfieldFROMalesasseWHERE''= '` |
| concatenação de string | `EXEC( 'UNI' 'ON' ' ...` |
| `IN` / `BETWEEN` | `OR 'twbheogeht' IN ( ' ' )` · `OR '0Oo4e' BETWEEN 'R' AND 'T'` |
| comparação `<` `>` | `OR 2 > 1` · `526 or id>6 or ls_id<0912` |
| identificador com ponto | `qwer' or Rl_v.Account='Tna@oo.com` |
| DDL | `;alter table riliiens set password = 'Isyty' where name = 'sedie';` |
| `--` colado no separador | `'; shutdown--&aemryab=...` |

O critério foi ampliado para cobrir todas elas. **Lição metodológica:** um
critério de qualidade de rótulo derivado num corpus (o SR-BH, cujos payloads são
do OWASP ZAP) não transfere para outro sem verificação — é o mesmo fenômeno que
a fase anterior documentou para features, aparecendo agora na régua de medição.

## Ressalvas

- **A versão `originais/` foi reconstruída do XML.** O arquivo
  `ecml_balanceado_sqli.csv` preserva encoding e, quando decodificado em memória,
  é célula por célula idêntico às 3.300 linhas da versão decodificada. Fonte:
  `msudol/Web-Application-Attack-Datasets`, commit
  `424c6e1c1951570473d9d6c0227eaaac6fdd6d02`; SHA-256 do XML:
  `9c058f33049f16c08449948266b5ce7733c232a64e34b436fdf6f1be076a4ecb`.
- **O tráfego benigno é ofuscado.** As URLs foram anonimizadas por substituição
  de caracteres, o que afeta diretamente `entropy`, `ratio_nonalnum` e as
  contagens de caractere.
- **25,4 % dos benignos contêm palavra de ataque** — o ofuscador injeta tokens
  em posições aleatórias. Como *substring*, `script` aparece em 8,9 % dos
  benignos; como palavra inteira (`\bscript\b`), em 0,2 %. É o mecanismo que
  separa features léxicas (que usam `\b` e escapam) de embeddings (que não).
- Os ataques foram gerados pelos organizadores, não capturados em produção.
