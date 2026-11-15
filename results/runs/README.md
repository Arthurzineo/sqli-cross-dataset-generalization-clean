# Índices de execuções

Resultados consolidados e índices das coleções experimentais.

`historical/index/` contém as 16.650 linhas históricas utilizáveis.
`controlled/` contém masters e comparações da coleção controlada.
`robustness/` preserva outputs e manifestos das análises posteriores.

Campos recorrentes incluem ID da execução, alvo, fontes, modelo, vista e seed.
Métricas, limiares e tempos aparecem quando persistidos pela execução.
Ausências devem permanecer ausentes; não as converta em zero.
Os arquivos não substituem as predições por amostra que ficaram externas.
Use os scripts em `analysis/` para produzir agregados do artigo.
