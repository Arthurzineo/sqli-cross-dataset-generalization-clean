# Corpus próprio — `DATASET_METODO_BALANCEADO`

Requisições da aplicação própria (OJS/revistas), coletadas em 2026. É o único
corpus da fase capturado por nós, e o único cujo tráfego benigno é produção real
não ofuscada.

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `../../scripts/filtrar_sqli.py` | `datasets/originais/DATASET_METODO_BALANCEADO_sqli.tsv` |
| 2 | (já existia decodificado a montante) | `datasets/decodificados/DATASET_METODO_BALANCEADO_decodificado_sqli.tsv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/DATASET_METODO_BALANCEADO_decodificado_sqli.tsv` |

## Números

| etapa | n | SQLi | benignas |
|---|---|---|---|
| origem (SQLi + XSS) | 74.510 | 18.634 | 37.255 |
| após filtro SQLi | 37.240 | 18.620 | 18.620 |
| **final (deduplicado)** | **37.212** | **18.606** | **18.606** |

Mantido: **99,9 %**. É o corpus mais limpo da fase.

## Decisões

**XSS descartado, não convertido em benigno.** 18.635 amostras de XSS saíram do
corpus. Rotular ataque como benigno envenenaria a validação — mesmo critério da
preparação do ECML.

**14 amostras com `sqli=1` e `xss=1` simultâneos foram descartadas.** Regra de
rótulo único: uma amostra que é SQLi *e* XSS não pertence limpo a nenhum lado de
um alvo binário. Por isso 18.620 e não 18.634.

**14 duplicatas exatas removidas** (+ 14 da classe oposta no rebalanceamento).
Volume irrelevante — o corpus foi construído corretamente na origem, como o t1
da auditoria anterior já havia mostrado (zero duplicatas no texto cru completo).

## Ressalvas

- **Aplicação única.** Um host, 2 valores no primeiro segmento do path, 78,4 %
  de reuso de caminho.
- Foi neste corpus que se mediu a inversão do `path_depth`: caminho fundo indica
  **benigno** aqui (são as URLs reais de `/etc/revistas/index.php/...`) e o
  contrário no CSIC. É o exemplo canônico de artefato de coleta do trabalho.
- No original, 5,1 % das linhas tinham `%XX` — e **0,0 % dos ataques**, contra
  ~10 % das benignas. Sinal invertido em relação ao CSIC e ao SR-BH; ver
  `../../datasets/README.md`.
