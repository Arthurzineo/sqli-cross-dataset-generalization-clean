# Filtros lexicais do SR-BH

As expressões normativas estão nos seguintes arquivos, preservados sem alterar
o comportamento:

1. `generators/srbh_filters/analisar_rotulos.py`: `PADRAO_SQLI`,
   `PADRAO_SQL_ESTRITO` e `PADRAO_OUTRA_CLASSE`;
2. `generators/srbh_filters/descartar_srbh_sem_sinal.py`: primeiro corte;
3. `generators/srbh_filters/filtrar_semantica_sql.py`: segundo corte;
4. `generators/srbh_filters/remover_benignas_com_payload.py`: sete famílias
   (`path_traversal`, `sql_keyword`, `sql_booleano`, `command_injection`,
   `code_injection`, `ssi` e `xss`).

Este documento aponta para o código para evitar que uma cópia textual da regex
divirja da implementação. A descrição, justificativa e contagens históricas
estão em `datasets/sources/corpus_documentation/srbh/README.md`.

