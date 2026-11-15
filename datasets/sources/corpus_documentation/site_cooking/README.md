# site-cooking — hard-negatives semânticos do SQLi Dataset Lab

Variante em inglês de um wiki/fórum culinário. O conteúdo benigno usa de forma
intencional palavras ambíguas como *select*, *where*, *union*, *sleep*, *join*,
*group by* e *order by* em linguagem natural. O objetivo é medir falsos
positivos de detectores que memorizam vocabulário em vez de estrutura SQL.

Fonte: [`Arthurzineo/sqli-dataset-lab`](https://github.com/Arthurzineo/sqli-dataset-lab/tree/Arthurzineo/TCC/site-cooking),
branch `Arthurzineo/TCC`, commit
`86e743c3c44c70a9f140710a132cdc3d09d7f597`.

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `../../scripts/importar_site_lab.py` | `datasets/originais/site_cooking.csv` |
| 2 | `../../scripts/decodificar.py` | `datasets/decodificados/site_cooking_decodificado.csv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/site_cooking_decodificado.csv` |
| 3b | `../../scripts/deduplicar_codificados.py` | `datasets/deduplicados_codificados/site_cooking.csv` |

Entradas: `site-cooking/log/benigno.jsonl` (31.161) e
`site-cooking/log/malicioso.jsonl` (30.000).

## Números

| etapa | n | SQLi | benignas |
|---|---:|---:|---:|
| JSONL de origem | 61.161 | 30.000 | 31.161 |
| textos únicos após decodificação | 32.129 | 28.446 | 3.683 |
| − sobreposição com site-sqli | 28.945 | 25.279 | 3.666 |
| **final balanceado** | **7.332** | **3.666** | **3.666** |

Mantido: **12,0 %**. Não houve conflito de rótulo nem texto vazio. Foram
removidas 29.032 duplicatas internas, 3.184 textos presentes também no
site-sqli e 21.613 ataques excedentes no balanceamento final.

### Ramo codificado

O conjunto `deduplicados_codificados/site_cooking.csv` tem **7.334 linhas
(3.667 + 3.667)**, das quais **2.290 preservam `%XX`**. No texto cru foram
removidas 27.775 duplicatas internas, 2.771 sobreposições com site-sqli e
23.281 ataques excedentes no balanceamento. As duas linhas adicionais em
relação ao ramo decodificado deixam de ser únicas depois de `unquote_plus`.

## Decisões

**Schema e prevenção de vazamento.** A conversão mantém timestamp, método, URI
e corpo e usa o schema `timestamp,method,url,body,malicioso,xss,sqli`.
Metadados de infraestrutura (IP, User-Agent, latência, status etc.) não entram.

**Decodificação separada.** No original, 57,4 % dos ataques e 3,8 % das
benignas contêm `%XX`; 19.680 linhas mudaram. A versão decodificada tem zero
sequência `%XX`.

**Descontaminação pareada antes do balanceamento.** Os 3.184 textos também
presentes no site-sqli foram removidos de ambos os corpora antes da amostragem
50/50, evitando contaminação direta em treino→alvo.

**UTF-8.** Um byte inválido no JSONL malicioso foi substituído por U+FFFD, como
documentado na fonte. O importador confere os hashes dos quatro JSONL.

## Ressalvas

- Corpus sintético de laboratório, de uma única aplicação.
- É um alvo adversarialmente difícil: termos SQL aparecem legitimamente no
  domínio culinário e corpos JSON contêm aspas por construção. Por isso a
  heurística lexical ampla marca 97,4 % das benignas; filtrá-las por essa
  heurística destruiria justamente o propósito do corpus.
- Só 3.683 dos 31.161 textos benignos eram únicos depois da decodificação.
