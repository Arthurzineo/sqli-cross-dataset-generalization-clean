# Definição dos 64 atributos

A implementação normativa é `src/features/lexical.py`.

- 22 contagens literais: aspas simples e duplas, `<`, `>`, parênteses,
  ponto-e-vírgula, `=`, `&`, `%`, `+`, `-`, `*`, `/`, `|`, `#`, `?`, `@`,
  `:`, vírgula, ponto e espaço ASCII;
- 19 palavras SQL: `select`, `union`, `insert`, `update`, `delete`, `drop`,
  `where`, `from`, `or`, `and`, `exec`, `order`, `by`, `waitfor`, `delay`,
  `cast`, `table`, `database`, `like`;
- 2 contagens de comentário: `--` e a soma de `/*` com `*/`;
- 14 termos web/XSS: `script`, `alert`, `javascript`, `onerror`, `onload`,
  `document`, `cookie`, `src`, `iframe`, `style`, `background`, `location`,
  `eval`, `prompt`;
- 7 atributos estruturais/estatísticos: `len_total`, `path_depth`,
  `ratio_digits`, `ratio_nonalnum`, `enc_pct`, `path_traversal`, `entropy`.

`path_depth` conta barras na URL armazenada; `enc_pct` conta ocorrências `%XX`
em URL e corpo e não é uma porcentagem. A implementação em
`src/features/lexical.py` contém a lista normativa e o cálculo de cada atributo.
