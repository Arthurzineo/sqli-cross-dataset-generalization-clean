# Estado da implementação complementar

Status deste registro: validação e recálculos concluídos durante a preparação. Atualização de execução em 2026-09-24: após autorização, o piloto real foi concluído e a bateria completa foi iniciada em segundo plano. O estado atual está em `artigo/complementos_generalizacao_v1/sequence/STATE.json`; conclusões científicas da bateria completa ainda não foram consolidadas neste documento.

O piloto real ECML/logistic/seed42 com cap explícito de 50 exemplos por classe/arquivo completou quatro fits, dois pares RAW/CANONICALIZED e dois pares ID/OOD em teste comum. Fonte: `artigo/complementos_generalizacao_v1/pilot_cap_50/analysis/AUDIT.json`; IDs e originais: `pilot_cap_50/analysis/SOURCE_LINEAGE.parquet`. O piloto valida execução e controles; não substitui os testes completos.

## Verificações executadas

A suíte passou sete testes automatizados, incluindo uma execução ponta a ponta com 14 fits pequenos sobre exemplos fabricados, cobrindo regressão logística, CatBoost, MLP e classificação de origem. Esses fits são apenas testes de software, não entram no inventário científico. Evidência: `artigo/complementos_generalizacao_v1/VALIDATION.json`; a composição exata do teste está em `test_supplemental.py`.

Foram verificados: pareamento das linhas/vistas; isolamento canônico e de origem do alvo; preservação do teste comum ID/OOD; validação congelada ao remover fontes; equilíbrio por origem/classe; comportamento com alvo de classe única; threshold exato versus busca exaustiva; identidade de eficiência de Shapley; consolidação; retomada recusando artefato alterado. Isso valida essas propriedades nos casos sintéticos, não prova desempenho científico nem ausência universal de erros.

## Recálculo realizado sem treinamento

O jogo de Shapley explicitamente definido no método foi calculado em 1.260 combinações de condição e métrica, produzindo 7.200 atribuições fonte/métrica. Os experiment_ids utilizados cobrem 13.170 runs históricos de contribuição. São 1.260 jogos analíticos, não novos treinamentos. Evidências: `artigo/complementos_generalizacao_v1/existing_analysis/SHAPLEY_AUDIT.json`, `EXECUTION.json`, `shapley_games.parquet`, `exact_shapley.parquet`.

A identidade de eficiência foi satisfeita com resíduo máximo registrado no `SHAPLEY_AUDIT.json`. Atribuições dependem da referência vazia analítica todos-positivos e continuam refletindo a seleção/validação do procedimento histórico. Não afirmar que recuperam um treinamento vazio ausente nem que isolam causalmente o efeito da fonte. Os arquivos anteriores não foram substituídos.

## Pendente e interpretação

A comparação verdadeiramente pareada de RAW/CANONICALIZED, o gap em teste idêntico, a separabilidade controlada e a contribuição com validação congelada exigem executar as respectivas etapas novas. Quantidades planejadas estão em `artigo/complementos_generalizacao_v1/full/PLAN.json`; não confundir com cobertura concluída. A lista de limitações restantes e critérios de exclusão está em `ANALYSIS_METHOD.md`.

A execução dessas etapas foi iniciada por `python artigo/scripts/run_supplemental_sequence.py --launch`; a fila também inclui consolidação entre etapas e auditoria completa dos manifests ao final. O status da fila não significa aprovação científica dos resultados. O supervisor mantém logs por etapa e verificações locais em arquivo a cada 20 minutos.

Não existem ainda efeitos positivos, negativos ou nulos científicos dessa nova bateria. Não existem novas figuras científicas. As RQs só poderão ser respondidas por esses novos controles depois da execução e consolidação, sem substituir silenciosamente as condições históricas.

## Metric Provenance

| Metric/Result | Analytical file | Original source | Filter | Aggregation | Script |
|---|---|---|---|---|---|
| Software validation | VALIDATION.json | test_supplemental.py; synthetic fixture | unittest suite | pass/fail, no scientific aggregation | test_supplemental.py |
| Real pilot execution integrity | pilot_cap_50/analysis/AUDIT.json | pilot_cap_50/analysis/SOURCE_LINEAGE.parquet | ECML/logistic/seed42/pilot_cap50 | completed fits and checked pairs, no seed aggregation | run.py; consolidate.py |
| Shapley games and values | existing_analysis/SHAPLEY_AUDIT.json | existing_analysis/SOURCE_FILES.parquet | usable contribution, effective complete coalitions | separate target/model/representation/feature_set/seed/metric; factorial weights | existing_analysis.py |
| Historical experiment count | existing_analysis/EXECUTION.json | existing_analysis/SOURCE_FILES.parquet | IDs participating in declared games | distinct experiment_id | existing_analysis.py |
| Incremental audit coverage | existing_analysis/split_audit/SUMMARY.json | input_identity.file in EXP_*.json | first two eligible not-yet-audited manifests | manifest-level pass/fail | existing_analysis.py |
| Planned fits, not results | full/PLAN.json | config.json | configured targets/seeds/models/views | Cartesian product upper bound | run.py |

## Data Sources and Traceability

Output paths in the provenance table are relative to `artigo/complementos_generalizacao_v1/`. Complete original mapping: `existing_analysis/SOURCE_FILES.parquet` (13.170 experiment_ids). Its relative original paths are rooted at GENERALIZACAO. Recálculo opened two analytical inputs: `artigo/analise_resultados_tcc/_global/master_results.parquet` and `SOURCE_LINEAGE.parquet`; no per-run original metrics, scores or checkpoints were opened by Shapley. Columns: usable, experiment_type, target_dataset, model, representation, feature_set, seed, training_datasets, effective_development_datasets, test_n, n_attack, f1, mcc, pr_auc, recall, fpr, fnr, experiment_id. Filters, factorial formula, empty reference and no seed pooling: `ANALYSIS_METHOD.md`. Full contributing IDs are listed per game in `shapley_games.parquet`; values join by game_id. Missing conditions are not fabricated; exclusions are in `shapley_nonapplicable.parquet`.

Commands: `python artigo/scripts/supplemental/existing_analysis.py --stage shapley`; `python artigo/scripts/supplemental/existing_analysis.py --stage audit-splits --limit 2`; `python artigo/scripts/supplemental/test_supplemental.py --report artigo/complementos_generalizacao_v1/VALIDATION.json`; `python artigo/scripts/supplemental/run.py --stage plan`. Python environment and complete commands are in README.md. `EXECUTION.json` preserves actual source hashes and command. Split audit read two original manifests, projected to canonical_hash/split/dataset; actual file paths, hashes, counts and experiment_ids are in the two `split_audit/EXP_*.json` records. Validation uses zero research datasets; fixture definitions and code hashes are recorded in VALIDATION.json. Derived artifacts generated: declared-game Shapley tables/audit/lineage, two split-audit records/summary, validation report and plan. No figures generated.

Execution update sources: `pilot_cap_50/analysis/SOURCE_LINEAGE.parquet` maps the four real pilot metric files, predictions and splits; `pilot_cap_50/cache/*/READY.json` maps actual RAW source paths/hashes. Command: `python artigo/scripts/supplemental/run.py --stage paired --targets ecml --models logistic --seeds 42 --pilot-cap 50 --max-runs 4`, then consolidate with `--root artigo/complementos_generalizacao_v1/pilot_cap_50`. Columns: experiment_id, kind, representation, split_id, sample_id, role, is_common_test; integrity counts are per fit/pair, not averages of F1. Supervisor command: `python artigo/scripts/run_supplemental_sequence.py --launch`; its actual commands, source snapshots, stage logs and process status are in `sequence/STATE.json`. Full-run coverage comes from `full/runs/SUPP_*/status.json`, not from pilot counts. No full-battery scientific finding or new figure is asserted in this execution update.
