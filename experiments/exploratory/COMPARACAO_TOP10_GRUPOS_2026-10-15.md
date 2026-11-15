# Comparação exploratória de três conjuntos Top-10

Teste privado para investigação, sem alteração do manuscrito ou das análises principais.

## Desenho

Foram executados 14 novos ajustes: sete alvos LODO para cada um dos conjuntos SQL e textual. Todos usam CatBoost CANONICALIZED, semente 42, mesmas partições controladas e mesmos hiperparâmetros da comparação anterior. A referência de 64 atributos e o Top-10 estável anterior foram reutilizados dos resultados salvos. Cada novo modelo reestima seu limiar na validação das fontes e o mantém fixo no teste; a parada antecipada também pode selecionar números diferentes de árvores.

Seleção fixada antes dos novos ajustes: frequência histórica no Top-10 em ordem decrescente; desempate por posto médio crescente e nome do atributo. Os candidatos SQL são todos os atributos `sql_*`. Os candidatos textuais são caracteres e medidas estruturais/estatísticas, excluindo `sql_*`, `xss_*` e `path_traversal`.

As duas representações continuam sendo lexicais: o grupo SQL conta palavras-chave e comentários; não verifica sintaxe, executabilidade ou sucesso de uma injeção.

## Conjuntos utilizados

- **Top-10 estável anterior:** char_equals, char_sq, char_space, char_rparen, sql_comment_dash, ratio_nonalnum, sql_select, sql_or, sql_and, sql_comment_block.
- **SQL:** sql_comment_dash, sql_select, sql_or, sql_and, sql_comment_block, sql_from, sql_delete, sql_order, sql_table, sql_drop.
- **Textual/estrutural:** char_equals, char_sq, char_space, char_rparen, ratio_nonalnum, path_depth, char_hash, char_star, char_colon, len_total.

Somente cinco atributos SQL tinham frequência positiva no Top-10 global histórico. Os cinco restantes desse grupo foram escolhidos pelo posto médio, não por presença recorrente no Top-10 global. As colunas de entrada preservam a ordem relativa original do extrator.

## F1 da classe ataque

| Alvo | 64 atributos | Top-10 anterior | SQL 10 | Textual 10 |
|---|---:|---:|---:|---:|
| artificial_sqli | 0,915490 | 0,922791 | 0,977714 | 0,870121 |
| csic | 0,707721 | 0,960371 | 0,909511 | 0,705557 |
| ecml | 0,943113 | 0,935764 | 0,923920 | 0,838279 |
| proprio | 0,972265 | 0,797559 | 0,930860 | 0,950624 |
| site_cooking | 0,813583 | 0,637813 | 0,884610 | 0,888954 |
| site_sqli | 0,798109 | 0,644231 | 0,870876 | 0,896011 |
| srbh | 0,858016 | 0,843247 | 0,940732 | 0,801707 |
| **Média por alvo** | **0,858328** | **0,820254** | **0,919746** | **0,850179** |

SQL supera o Top-10 anterior em cinco alvos e os 64 atributos também em cinco alvos. Textual supera o Top-10 anterior em três alvos e os 64 atributos em dois. O ganho médio do SQL frente ao Top-10 anterior é +0,099492 de F1; frente aos 64 atributos, +0,061418.

## Outras métricas — médias não ponderadas entre alvos

| Métrica | 64 atributos | Top-10 anterior | SQL 10 | Textual 10 |
|---|---:|---:|---:|---:|
| MCC | 0,689674 | 0,539860 | 0,853609 | 0,693226 |
| AP (PR-AUC) | 0,970025 | 0,962705 | 0,942955 | 0,952464 |
| Precisão | 0,787866 | 0,734437 | 0,974447 | 0,845419 |
| Recall | 0,956814 | 0,954893 | 0,871443 | 0,879302 |
| FPR | 0,293579 | 0,422721 | 0,023037 | 0,207572 |
| Brier | 0,072079 | 0,078937 | 0,061509 | 0,107457 |
| ECE (10 faixas) | 0,099151 | 0,129040 | 0,052702 | 0,132792 |

## Leitura do teste

O subconjunto SQL foi o melhor em F1 médio no limiar escolhido nas fontes. A FPR média caiu para 2,30%, com precisão média de 97,44%, mas recall menor (87,14%). Sua AP média ficou abaixo das outras três configurações: o ganho não foi uniforme entre discriminação e métricas dependentes do limiar.

Um diagnóstico adicional ajuda a interpretar a diferença: o F1-oráculo médio do Top-10 anterior foi 0,939856, contra 0,936602 do SQL e 0,914760 do textual. Assim, a grande vantagem operacional do SQL sobre o Top-10 anterior não persistiu quando cada conjunto recebeu seu melhor limiar retrospectivo no alvo. Isso indica importância da adequação do ponto de decisão nesta rodada; não isola um mecanismo causal. O oráculo não foi usado na escolha dos limiares operacionais.

São resultados de uma semente e seleção retrospectiva baseada no ranking histórico global, sem seleção aninhada por alvo. A referência de 64 atributos é 0,858328 nesta semente, não a média de cinco sementes do artigo. O teste serve para explorar os recortes e não demonstra superioridade geral do grupo SQL.

## Verificação e artefatos

Foram conferidas as mesmas partições (hashes) entre todos os conjuntos e suas referências, as mesmas contagens de treino/validação/teste, versões das bibliotecas e hiperparâmetros. Nas 21 execuções reduzidas (sete anteriores e 14 novas), as predições salvas reproduziram o F1 e a FPR reportados, com dez atributos por modelo e um único limiar operacional por teste.

- [Top-10 anterior](top10_can_catboost_seed42_20261013T132301942701/comparison.csv)
- [SQL 10](top10_sqli_can_catboost_seed42_20261015T003100233573/comparison.csv)
- [Textual 10](top10_lexical_can_catboost_seed42_20261015T003122067661/comparison.csv)

Cada diretório contém manifestos, frequências e postos dos atributos escolhidos, resumos, logs, predições, métricas, importâncias e checkpoints. Os resultados anteriores não foram sobrescritos.

Reprodução com o mesmo ambiente Python do projeto:

```bash
<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/test_top10_canonicalized_lodo.py --seed 42 --feature-group sqli
<PROJECT_ROOT>/../../venv/bin/python artigo/scripts/test_top10_canonicalized_lodo.py --seed 42 --feature-group lexical
```
