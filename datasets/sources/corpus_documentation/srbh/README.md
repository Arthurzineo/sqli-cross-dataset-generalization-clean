# SR-BH 2020

Honeypot WordPress exposto à Internet por 12 dias em julho de 2020. É o único
corpus da fase com **tráfego de ataque real e não solicitado**, e o mais recente.

Origem: Harvard Dataverse, DOI [`10.7910/DVN/OGOIXX`](https://doi.org/10.7910/DVN/OGOIXX),
licença **CC0 1.0**. Artigo: *A new multi-label dataset for Web attacks CAPEC
classification using machine learning techniques*, Computers & Security, 2022.

    curl -L "https://dataverse.harvard.edu/api/access/datafile/6319496?format=original" \
         -o datasets/SR_BH_2020/data_capec_multilabel.csv

## Pipeline

| # | script | saída |
|---|---|---|
| 1 | `../../scripts/preparar_srbh.py` | `datasets/originais/srbh_completo_sqli.csv` |
| 2 | `../../scripts/decodificar.py` | `datasets/decodificados/srbh_completo_decodificado_sqli.csv` |
| 3 | `../../scripts/deduplicar.py` | `datasets/deduplicados_decodificados/srbh_completo_decodificado_sqli.csv` |

## Números

| etapa | n | SQLi | benignas |
|---|---|---|---|
| corpus completo | 907.815 | 250.311 | 525.195 |
| SQLi + benignas (sem balancear) | 775.506 | 250.311 | 525.195 |
| − conflitos de rótulo (781 grupos) | 443.384 | | |
| − duplicatas | 272.033 | | |
| balanceado | 175.850 | 87.925 | 87.925 |
| − sem sinal léxico (corte 1) | 161.952 | 80.976 | 80.976 |
| semântica SQL (corte 2) | 145.606 | 72.803 | 72.803 |
| **final (benignas limpas, corte 3)** | **103.092** | **51.546** | **51.546** |

Mantido: **13,3 %** do original. É a maior perda da fase — e ainda assim sobra o
maior corpus, 3,9× o corpus próprio.

## Decisões

**Todas as requisições com a tag `66 - SQL Injection` foram mantidas**, inclusive
as 2.218 que têm outro rótulo CAPEC junto. Decisão explícita: o recorte é por
presença da tag, não por exclusividade dela.

**Sem balanceamento na extração — só no fim do pipeline.** *(Corrigido após
medir.)* A primeira versão amostrava 250.311 benignas logo na extração, e isso
jogava dados fora: as benignas são 525.195 linhas mas só **90.049 requisições
distintas** — a requisição `/` sozinha aparece **298.686 vezes**, e as 5 mais
repetidas somam 62 % do tráfego benigno. Amostrar linhas ao acaso capturava
apenas 48.418 distintas. Na ordem correta — extrair tudo → decodificar →
deduplicar → balancear — sobram 87.925 por classe, **1,83× mais dados**.

A deduplicação precisa vir **depois** da decodificação: duas formas codificadas
diferentes podem decodificar para o mesmo texto.

**781 grupos de rótulo conflitante descartados por completo** (332.122 linhas).
São textos idênticos que aparecem ora como benignos, ora como SQLi. Não há como
saber qual rótulo está certo, e manter qualquer um dos dois injeta erro conhecido
na validação. O maior grupo é `http://test-site.com/` — a home page — com 142.476
linhas benignas e 1 marcada como SQLi.

**Sem decodificação na extração, decodificação em etapa separada.** Permite
ablacionar a normalização; a versão crua fica em `datasets/originais/`.

## Ressalva central — a rotulagem é por sessão, não por requisição

O corpus foi rotulado marcando o tráfego gerado por ferramentas de varredura. Uma
execução de sqlmap emite centenas de requisições comuns de reconhecimento junto
com os payloads, e todas ficaram marcadas como SQL Injection.

Medido com `../../scripts/analisar_rotulos.py`, no corpus final:

| medida | valor |
|---|---|
| SQLi total | 87.925 |
| **SQLi sem nenhum sinal léxico de SQL** | **6.949 (7,9 %)** |

Exemplos rotulados **SQL Injection** que não têm payload de SQL:

    /wp-content/plugins/all-in-one-wp-security-and-firewall/
    /wp-content/plugins/all-in-one-wp-migration/
    /blog/{{ attachment.thumbnail.url }}/my-account/edit-profile/...

Os dois primeiros são enumeração de plugin — reconhecimento, não ataque. O
terceiro é sondagem de *template injection*, que é ataque mas **não é SQLi**.

### Comparação com os outros corpora

O mesmo critério, aplicado a todos, separa "rotulagem ruim" de "limite do
extrator" — os dois produzem o mesmo sintoma:

| corpus | SQLi sem sinal |
|---|---|
| CSIC 2010 | 0,0 % |
| Artificial | 0,0 % |
| Artificial SQLi+ | 0,4 % |
| Próprio | 0,6 % |
| ECML/PKDD 2007 | 4,0 % |
| **SR-BH 2020** | **7,9 %** |

O SR-BH é **2× o segundo pior** e ~13× o corpus próprio. Nos demais o resíduo é
teto de representação (payload que o extrator não enxerga); aqui é rotulagem.

### Correção de medida anterior

As primeiras medições reportaram **23,1 %** e depois **15,0 %**. Ambas estavam
erradas — a heurística não cobria injeção booleana cega (`" AND "1"="1`,
`AND 1923=7138`), então contava ataques legítimos como "sem sinal" e inflava o
número em todos os corpora. Corrigida em `analisar_rotulos.py` (aspas duplas,
comparação após AND/OR/XOR, comentário de bloco, ORDER/GROUP BY, literais hex).
**O número correto é 7,9 %.**

### A deduplicação não resolveu isso

Antes: 9,2 %. Depois: 7,9 %. A remoção dos 781 grupos conflitantes só atingiu
textos que apareciam **também** como benignos; as requisições de reconhecimento
que aparecem apenas com a tag SQLi sobreviveram inteiras.

### O que são, de fato, as 6.949

Classificadas por `../../scripts/classificar_srbh_sem_sinal.py` (saída em
`datasets/deduplicados_decodificados/SRBH_SEM_SINAL.csv`):

| categoria | n | % |
|---|---|---|
| sondagem de fuzzing (`/blog(`, `/blogNULL`, `/blog)`) | 4.013 | 57,7 % |
| template injection (`{{ }}`, `${@print(chr(...))}`) | 1.430 | 20,6 % |
| XML/CDATA (`]]>`, `<!DOCTYPE`) | 551 | 7,9 % |
| **tráfego normal de conta** | **577** | **8,3 %** |
| SSRF / redirect | 181 | 2,6 % |
| reconhecimento WordPress | 126 | 1,8 % |
| command injection (`|cat`, `` `cat ``) | 67 | 1,0 % |
| path traversal / LFI | 4 | 0,1 % |

**89,9 % são ataques — de outro tipo.** A pergunta "são realmente não-ataques?"
tem resposta majoritariamente negativa: são ataques reais rotulados na classe
errada, não tráfego benigno.

**8,3 % (577) é tráfego normal.** São POST de login, registro, troca e
recuperação de senha, e logout do WordPress — 555 POST com credenciais comuns e
22 GET de navegação e busca (`?s=cancer`, `?s=marketing`). Apenas 1 das 555 tem
payload (`_wp_http_referer=c:/`).

O teste decisivo: o **mesmo tipo de requisição aparece 2.799 vezes do lado
benigno** do próprio corpus. Os nomes de usuário saem do mesmo gerador
sintético dos dois lados (`euphoricWasp5`, `boastfulGelding1` de um lado;
`abjectCrane1`, `adoringSeagull7` do outro) sem nenhum nome em comum. São
requisições indistinguíveis, separadas apenas por terem caído dentro da janela
de uma sessão de varredura.

### A nuance das sondagens de fuzzing

Os 57,7 % de `/blog(`, `/blogNULL`, `/blog)` **são** parte de um ataque de SQLi:
é a fase de sondagem do sqlmap, que anexa marcadores ao caminho para descobrir
pontos de injeção. Um detector que os pegue detecta o ataque mais cedo.

Mas eles não carregam nenhuma semântica de SQL. Aprendê-los significa aprender
"caractere estranho colado no fim do caminho" — exatamente o tipo de atalho
estrutural que este trabalho documenta como artefato de coleta. É a mesma
armadilha do `path_depth`, com outra roupa.

### Os dois cortes aplicados

**Corte 1 — `../../scripts/descartar_srbh_sem_sinal.py`.** Removeu as 6.949 sem
sinal léxico. 175.850 → 161.952.

**Corte 2 — `../../scripts/filtrar_semantica_sql.py`.** O critério do corte 1
(`tem_indicador_sqli`) aceitava qualquer aspa ou ponto-e-vírgula mas **não**
aceitava `(`, `)` e `NULL`. Isso separou `/blog'` de `/blog(` por acidente da
regex: as quatro são a mesma família de sonda. Inspecionadas as 80.976 que
tinham sobrado:

| | n | % |
|---|---|---|
| SQL puro | 72.071 | 89,0 % |
| SQL + marca de outra classe | 732 | 0,9 % |
| **só outra classe (sem sintaxe SQL)** | **869** | **1,1 %** |
| **só aspa / ponto-e-vírgula** | **7.304** | **9,0 %** |

As duas últimas saíram. As 869 eram XSS (`'"<script>alert(1);</script>`) e SSI
(`"><!--#EXEC cmd="ls /"-->`) que passaram só por conter aspas. As 7.304 eram
sonda pura (`/blog'`, `/blog;`, `/blog'"`) — SQLi de verdade, mas só a fase de
sondagem, sem semântica de SQL.

**Critério final: exigir semântica de SQL** — palavra-chave (SELECT, UNION,
`information_schema`, sleep…), injeção booleana (`AND 1923=7138`) ou
comentário/literal SQL (`--`, `/*`, `@@`, `0x…`). Definido uma única vez em
`PADRAO_SQL_ESTRITO`, em `analisar_rotulos.py`.

161.952 → **145.606 (72.803 SQLi + 72.803 benignas)**, dos quais **99,0 % são
SQL puro** e 1,0 % é SQL com ruído de outra classe junto.

Nenhuma virou benigna — todas descartadas, mesma regra do XSS.

### Corte 3 — a classe benigna estava contaminada

`../../scripts/remover_benignas_com_payload.py`. O espelho do problema anterior:
a rotulagem por sessão marcou como `000 - Normal` o tráfego de ataque que caiu
fora da janela de uma sessão. **29,2 % das benignas (21.257 de 72.803) continham
payload de ataque real:**

| família | n | exemplo |
|---|---|---|
| path traversal / LFI | 17.131 | `/../../../../etc/passwd`, `boot.ini` |
| SSI injection | 2.426 | `<!--#EXEC cmd="ls /"-->` |
| XSS | 1.237 | `'"<script>alert(1);</script>` |
| SQL keyword | 322 | `%');SELECT SLEEP(5)#` |
| command injection | 121 | `/blog;sleep 15;/index.php/…` |
| code injection | 13 | `${@die(sha1(xyzt))}` |
| SQL booleano | 7 | `comment= AND 1=1 -- ` |

**Este é o pior dos três problemas.** Como alvo de validação, benigna mal
rotulada infla o FPR com **acertos**: um modelo que sinaliza corretamente
`/../../../etc/passwd` é contado como falso positivo. A métrica pune o detector
por funcionar.

145.606 → **103.092 (51.546 SQLi + 51.546 benignas)**. Resíduo: **0**.

**Controle do critério.** O mesmo padrão aplicado aos outros cinco corpora marca
0 no CSIC e nos dois artificiais. As 8 do corpus próprio e as 45 do ECML foram
inspecionadas uma a uma e são **falsos positivos**: no próprio, resumo acadêmico
em prosa que casa por acaso; no ECML, o ofuscador produzindo `b2amnboot.ini`,
`wjvNboot.ini` — a substring dentro de texto anonimizado aleatório. Nenhuma foi
removida. É a mesma lição de `\b` que o `ACHADOS.md` já registra.

### O que motivou o critério

Sonda sem semântica só é aprendível como "caractere estranho colado no
caminho". É o atalho estrutural que este trabalho documenta como artefato de
coleta — o `path_depth` com outra roupa. Um detector que aprende isso não
aprendeu SQLi; aprendeu a assinatura do ZAP.



A coluna **`tem_indicador_sqli`** (0/1) marca quais são, para permitir decidir
sem reprocessar o arquivo de 436 MB. Opções: (a) usar como está e reportar o
teto; (b) filtrar para o subconjunto com payload observável; (c) rodar as duas
versões e reportar ambas — a diferença entre elas *é* um resultado, e mostra que
a qualidade de rotulagem do corpus alvo domina a métrica.

## Colunas extras

Fora do schema comum, no fim do arquivo:

- **`tem_indicador_sqli`** — heurística de apoio, o padrão `PADRAO_SQLI` de
  `../../scripts/analisar_rotulos.py` (definição única, para a coluna gravada
  nunca divergir da análise que a interpreta). Não foi usada para filtrar nada.
- **`capec_n_rotulos`** — quantos rótulos CAPEC a linha tinha na origem.

## Ressalvas adicionais

- **Aplicação única** (um WordPress), como os outros três. Ter quatro corpora não
  resolve a limitação "todos de aplicação única".
- O host varia (o honeypot recebeu varredura de vários), mas a aplicação é uma só.
