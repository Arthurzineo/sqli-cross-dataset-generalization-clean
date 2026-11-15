# Filtros do SR-BH

Scripts usados para selecionar e curar a tarefa binária de SQLi.

`preparar_srbh.py` seleciona CAPEC-66 e registros normais.
`descartar_srbh_sem_sinal.py` aplica o primeiro corte lexical.
`filtrar_semantica_sql.py` aplica o filtro semântico estrito.
`remover_benignas_com_payload.py` remove benignos com padrões de ataque.
`analisar_rotulos.py` e `classificar_srbh_sem_sinal.py` apoiam a auditoria.

As expressões regulares consolidadas estão em `docs/srbh_regex.md`.
O artigo discute o viés potencial introduzido por esses cortes.
A cópia filtrada publicável está em `datasets/processed/` sob CC0 1.0.
A variante sem filtros pertence aos experimentos de robustez.
