# site-sqli — baseline técnica do SQLi Dataset Lab

Corpus de laboratório de uma aplicação de documentação e fórum, coletado no
Nginx. Os ataques foram injetados em GET, formulário, JSON e GraphQL; o banco da
aplicação permaneceu parametrizado e não explorável.

Fonte: [`Arthurzineo/sqli-dataset-lab`](https://github.com/Arthurzineo/sqli-dataset-lab/tree/Arthurzineo/TCC/site-sqli),
branch `Arthurzineo/TCC`, commit
`86e743c3c44c70a9f140710a132cdc3d09d7f597`.

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `../../scripts/importar_site_lab.py` | `datasets/originais/site_sqli.csv` |
| 2 | `../../scripts/decodificar.py` | `datasets/decodificados/site_sqli_decodificado.csv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/site_sqli_decodificado.csv` |
| 3b | `../../scripts/deduplicar_codificados.py` | `datasets/deduplicados_codificados/site_sqli.csv` |

Entradas: `site-sqli/log/benigno.jsonl` (30.113) e
`site-sqli/log/malicioso.jsonl` (30.000). O arquivo determina o rótulo; nenhum
campo de ferramenta, IP ou status é usado para rotular.

## Números

| etapa | n | SQLi | benignas |
|---|---:|---:|---:|
| JSONL de origem | 60.113 | 30.000 | 30.113 |
| textos únicos após decodificação | 33.159 | 28.581 | 4.578 |
| − sobreposição com site-cooking | 29.975 | 25.414 | 4.561 |
| **final balanceado** | **9.122** | **4.561** | **4.561** |

Mantido: **15,2 %**. Não houve conflito de rótulo nem texto vazio. Foram
removidas 26.954 duplicatas internas, 3.184 textos presentes também no
site-cooking e 20.853 ataques excedentes no balanceamento final.

### Ramo codificado

O conjunto `deduplicados_codificados/site_sqli.csv` também tem **9.122 linhas
(4.561 + 4.561)**, das quais **3.513 preservam `%XX`**. No texto cru foram
removidas 25.896 duplicatas internas, 2.771 sobreposições com site-cooking e
22.324 ataques excedentes no balanceamento.

## Decisões

**Schema local de sete colunas.** Dos 13 campos Nginx foram mantidos apenas
timestamp, método, URI e corpo, convertidos para
`timestamp,method,url,body,malicioso,xss,sqli`. IP, User-Agent, latência,
status e demais metadados foram descartados porque não existem nos outros
corpora e revelam a infraestrutura/classe da coleta.

**Decodificação separada.** No original, 68,0 % dos ataques e 6,5 % das
benignas contêm `%XX`; 23.334 linhas mudaram. A versão decodificada tem zero
sequência `%XX`, mantendo o original para ablação.

**Descontaminação pareada antes do balanceamento.** site-sqli e site-cooking
usam a mesma wordlist e compartilham endpoints. Os 3.184 textos comuns foram
descartados de ambos para permitir avaliação cruzada sem exemplos idênticos.

**UTF-8.** Um byte inválido no JSONL malicioso foi substituído por U+FFFD,
seguindo a política documentada pela própria fonte. Os hashes brutos são
validados pelo importador.

## Ressalvas

- Corpus sintético de laboratório, de uma única aplicação.
- O tráfego benigno contém documentação e conversas técnicas sobre SQL. A
  heurística lexical ampla marca 91,7 % das benignas; isso é uma propriedade
  intencional de hard-negative, não justificativa automática para removê-las.
- A classe benigna tinha muita navegação repetida: só 4.578 textos únicos em
  30.113 requisições. Avaliar antes da deduplicação inflaria as métricas.
