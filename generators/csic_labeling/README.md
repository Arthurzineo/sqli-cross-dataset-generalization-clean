# Rotulagem do CSIC

Código da derivação `legitimate`/`sqli`/`xss` do HTTP CSIC 2010 usada no estudo.

- `clusterizacao_ataques_web.py`: versão executável do notebook.
- `Clusterizacao_Completo.ipynb`: atributos lexicais, CodeBERT, PCA e K-Means (`k=26`).
- `Relatorio_Clusterizacao.pdf` e `LEIA-ME.txt`: descrição do procedimento.

A rotulagem tem duas etapas. Primeiro, as requisições anômalas são agrupadas, e a
inspeção dos grupos identifica as assinaturas de SQLi e XSS. Depois, cada
requisição é rotulada pela presença dessas assinaturas, após decodificação dupla e
sem distinção de caixa.

Verificação manual: depois da rotulagem, 100 requisições maliciosas e 100 benignas
foram sorteadas aleatoriamente e inspecionadas uma a uma. Nenhuma das 200
apresentou rótulo incorreto. Em seguida, o arquivo rotulado passou por uma revisão
geral.

A base CSIC não é redistribuída. Consulte `datasets/sources/csic/` para obtê-la e
prepará-la.
