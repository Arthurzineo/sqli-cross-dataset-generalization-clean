# Gerador `artificial_sqli`

Preserva o gerador inicial e a substituição parametrizada dos ataques SQLi.

`gerar_dataset_artificial.py` cria a base sintética inicial.
`sqli_payloads.py` implementa 41 formas distribuídas em seis técnicas.
As técnicas são booleana, temporal, erro, UNION, empilhada e bypass.
Os pesos registrados são 0,24, 0,24, 0,18, 0,14, 0,12 e 0,08.
`regenerar_sqli_artificial.py` substitui as linhas SQLi na base inicial.
`decodificar_artificial.py` pertence à preparação histórica.
Somente os geradores usados e sua documentação de procedência integram este
repositório.

O código registra que o redimensionamento foi informado por erros no CSIC.
A cópia final publicável está em `datasets/processed/`.
