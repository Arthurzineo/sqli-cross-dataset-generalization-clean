# Corpus artificial — variante SQLi melhorado

Mesmo corpus artificial, com as **técnicas de SQLi regeneradas**: distribuição de
ataques mais realista e de alta cardinalidade, inspirada em sqlmap e
PayloadsAllTheThings. Gerado por `datasets/gerar_sqli_melhorado.py` +
`datasets/regenerar_sqli_artificial.py`, payloads em `datasets/sqli_payloads.py`.

É a variante mais relevante para uma fase de SQLi: é a que tem os payloads mais
próximos de ataque real.

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `../../scripts/filtrar_sqli.py` | `datasets/originais/dataset_artificial_ia_sqli_melhorado_sqli.tsv` |
| 2 | `../../scripts/decodificar.py` | `datasets/decodificados/dataset_artificial_ia_sqli_melhorado_decodificado_sqli.tsv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/dataset_artificial_ia_sqli_melhorado_decodificado_sqli.tsv` |

## Números

| etapa | n | SQLi | benignas |
|---|---|---|---|
| origem | 10.000 | 2.500 | 5.000 |
| após filtro SQLi | 5.000 | 2.500 | 2.500 |
| **final (deduplicado)** | **5.000** | **2.500** | **2.500** |

Mantido: **100 %** — zero duplicatas, zero conflitos. A regeneração de alta
cardinalidade eliminou as 187 colisões que a versão anterior tinha.

## Decisões

**Decodificado nesta fase.** Era o único corpus da fase sem versão decodificada —
estava com **89,6 % dos ataques** e 11,6 % das benignas contendo `%XX`, o mesmo
padrão de sinal invertido dos demais. 57,5 % das linhas foram alteradas pela
decodificação.

**Não deve ser usado junto com o artificial padrão.** São duas versões do mesmo
corpus: o lado benigno é idêntico (2.502 textos em comum). Escolher uma das duas.

## Ressalvas

- Sintético, como o artificial padrão — aditivo de treino, não corpus alvo.
- A maior cardinalidade dos payloads é a razão de não haver duplicatas; isso
  também significa que o corpus é *mais fácil* de deduplicar mas não
  necessariamente mais representativo de tráfego real.
