# Teste exploratório: CatBoost LODO com Top-10 estável canonicalizado

## Resultado

Com a semente 42, reduzir de 64 para dez atributos diminuiu o F1 de ataque médio entre os sete alvos de **0,858328 para 0,820254** (diferença de **−0,038075**). Houve melhora em dois alvos e piora em cinco.

| Alvo | F1 com 64 atributos | F1 com 10 atributos | Diferença |
|---|---:|---:|---:|
| artificial_sqli | 0,915490 | 0,922791 | +0,007301 |
| csic | 0,707721 | 0,960371 | +0,252650 |
| ecml | 0,943113 | 0,935764 | −0,007349 |
| proprio | 0,972265 | 0,797559 | −0,174707 |
| site_cooking | 0,813583 | 0,637813 | −0,175770 |
| site_sqli | 0,798109 | 0,644231 | −0,153878 |
| srbh | 0,858016 | 0,843247 | −0,014769 |
| Média entre alvos | 0,858328 | 0,820254 | −0,038075 |

Outras médias entre alvos:

| Métrica | 64 atributos | 10 atributos |
|---|---:|---:|
| MCC | 0,689674 | 0,539860 |
| Average precision (PR-AUC) | 0,970025 | 0,962705 |
| Precisão | 0,787866 | 0,734437 |
| Recall | 0,956814 | 0,954893 |
| FPR | 0,293579 | 0,422721 |
| Brier | 0,072079 | 0,078937 |
| ECE (10 faixas) | 0,099151 | 0,129040 |

A redução de atributos não trouxe ganho geral nesta rodada. O recall médio permaneceu próximo, mas a FPR média aumentou de 29,36% para 42,27%. A AP média mudou menos que o F1; esses resultados, isoladamente, não identificam o mecanismo da perda.

## Atributos

Top-10 de recorrência no ranking histórico CANONICALIZED utilizado no artigo:

1. char_equals
2. char_sq
3. char_space
4. char_rparen
5. sql_comment_dash
6. ratio_nonalnum
7. sql_select
8. sql_or
9. sql_and
10. sql_comment_block

A matriz reduzida preservou a ordem relativa original das colunas. Frequências de recorrência estão em `selected_features.csv`.

## Protocolo e comparação

- Sete novos ajustes CatBoost, vista CANONICALIZED, semente 42, exclusão da família do alvo conforme o protocolo controlado.
- Mesmas linhas, partições e controles de sobreposição das execuções controladas originais, reutilizados diretamente dos manifestos salvos.
- Mesmo código de treinamento e métricas, versões das bibliotecas, hiperparâmetros e dois threads; os hashes dos arquivos de código da referência foram conferidos.
- Até 200 árvores, profundidade 5, taxa 0,05, parada antecipada com paciência 15.
- Imputação e padronização ajustadas no treino. O limiar é reestimado na validação das fontes para cada novo modelo e mantido fixo durante o teste.
- Avaliação no alvo completo. Os 64 atributos são a referência já salva da mesma semente e das mesmas partições, não uma nova rodada de treinamento.
- Conferidos os hashes dos caches e das partições, contagens de treino/validação/teste e versões de software. O F1 foi também recalculado a partir das predições salvas dos sete novos ajustes; todos coincidiram. Cada modelo possui dez importâncias de atributos e um único limiar aplicado ao teste.

## Interpretação

Este é um teste exploratório de uma semente, não a comparação com a média de cinco sementes do artigo (0,894). A referência correta desta rodada é 0,858328.

O conjunto de atributos foi escolhido pelo ranking histórico global, não por seleção aninhada dentro das fontes de cada alvo. Outros folds históricos podem ter utilizado a atual base-alvo como fonte na construção desse ranking. Portanto, esta ablação retrospectiva não constitui uma nova avaliação inteiramente independente quanto à seleção de atributos.

O resultado mostra que recorrência de importância não garante que apenas esses dez atributos sejam suficientes para manter o desempenho. Não permite concluir superioridade geral de uma configuração com apenas uma semente.

## Artefatos

- `comparison.csv`: comparação por alvo, métricas, limiares, iterações e referências aos arquivos originais.
- `summary.json`: médias e contagem de ganhos/perdas.
- `manifest.json`: procedência do ranking e hashes do código.
- `runs/`: configurações, logs, métricas, predições, importâncias e checkpoints dos sete novos modelos.
- `cache/`: matriz reduzida, sem alteração do cache original.
- Script: `artigo/scripts/test_top10_canonicalized_lodo.py --seed 42`.

Nenhum resultado principal, dado de entrada ou trecho do manuscrito foi sobrescrito.
