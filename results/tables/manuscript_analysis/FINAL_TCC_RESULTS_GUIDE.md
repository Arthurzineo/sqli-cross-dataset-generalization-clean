# Chapter 5 — Results and Analysis

Este guia apresenta achados rastreáveis. “Complete” significa análise possível concluída; “Partial” sinaliza limitações de evidência que impedem parte das perguntas. Não preencher essas lacunas com resultados inventados.

## Complemento controlado posterior — ler junto com este guia

Os novos controles concluídos possuem guia próprio em [SUPPLEMENTAL_CONTROLLED_ANALYSIS/FINAL_TCC_RESULTS_GUIDE.md](SUPPLEMENTAL_CONTROLLED_ANALYSIS/FINAL_TCC_RESULTS_GUIDE.md) e resultados em [SUPPLEMENTAL_CONTROLLED_ANALYSIS/RESULTS.md](SUPPLEMENTAL_CONTROLLED_ANALYSIS/RESULTS.md).

Para discutir **o efeito isolado da canonicalização**, **o gap ID/OOD no mesmo teste**, **a remoção de fontes com validação fixa** e **a separabilidade com tamanho/classes controlados**, priorizar as tabelas desse complemento. As seções abaixo continuam documentando os experimentos históricos: seus números, configurações e populações não foram substituídos. CANONICALIZED novo deriva das mesmas linhas RAW, inclusive URL/body; não é idêntico ao pipeline decoded histórico. A classificação permanece lexical, sem novo experimento de embeddings.

A auditoria de manifests históricos agora foi completada; a conclusão se limita às verificações efetivamente realizadas, não à ausência universal de leakage. Estado: `../complementos_generalizacao_v1/existing_analysis/split_audit/SUMMARY.json`. Rastreabilidade do complemento: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/SOURCE_FILES.parquet`, `TRACEABILITY.csv`, `ANALYSIS_METHOD.md`, `tables/reproducibility_audit.csv`; comando `python artigo/scripts/analyze_supplemental_results.py`. Consultar também a sensibilidade estatística aos alvos relacionados: `SUPPLEMENTAL_CONTROLLED_ANALYSIS/statistics/canonicalization_family_sensitivity.csv`.

## 5.1 Experimental Coverage and Integrity

Main findings:

Fonte analítica: `M04_01_Experimental_Design__C05_01_Experimental_Coverage/RESULTS.md`.

Inventário completo e contribuição são populações distintas. Contagens verificadas em `M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_counts.csv`; distribuição em `M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_type.csv`.

As exclusões incluem pilotos, falhas históricas e coalizões removidas pelo controle de família; nenhuma exclusão é apagada (`M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/excluded_runs.csv`).

Foram contabilizados 16715 IDs, 16650 runs utilizáveis e 13170 de contribuição; 65 IDs excluídos com motivo. Fonte: `M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_counts.csv`, coluna n e chave category.

Fonte analítica: `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/RESULTS.md`.

Duplicatas e conflitos estão quantificados em `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/duplicate_audit.csv` e `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/label_conflicts.csv`; remoções por fold em `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/before_after_audit.csv`.

Pairwise permite pares da mesma família e precisa identificá-los. LODO e contribuição aplicam controle de família. Oracle usa o target somente como diagnóstico (`M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/leakage_checks.csv`).

srbh/CANONICALIZED tem 68 chaves canônicas com rótulos conflitantes (`M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/tables/label_conflicts.csv`, row_id 4195c512d8ad927b7091). O teste preserva essas entradas; esse ruído limita o desempenho interpretável.

Tables to include:

- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/coverage_matrix.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/missing_runs.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/excluded_runs.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_counts.csv`
- `artigo/analise_resultados_tcc/M04_01_Experimental_Design__C05_01_Experimental_Coverage/tables/run_coverage_by_type.csv`

Figures to include:

- `artigo/analise_resultados_tcc/M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity/figures/cross_dataset_overlap.pdf`

Source analysis folders:

- `M04_01_Experimental_Design__C05_01_Experimental_Coverage`
- `M04_03_Data_Audit_Leakage__C05_01_Experimental_Integrity`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Grade esperada reconstruída dos scripts de execução, cenários, seis ablações efetivamente solicitadas e cinco seeds. Métricas exigem status COMPLETED, pilot=0 e campos válidos. Falhas não são substituídas por zeros. RQs se sobrepõem; suas contagens não devem ser somadas.
Lowercase e whitespace auditados separadamente nesta análise; chave canônica combina URL decode recursivo, casefold e normalização whitespace. Overlaps inter-dataset reutilizados da auditoria salva. Alvo preservado; remoções de conflitos e overlap ocorrem no desenvolvimento. Validação reserva uma família inteira quando ambas as partições têm duas classes; fallback GroupShuffleSplit. Não houve busca source-aware de hiperparâmetros.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.2 Dataset, Representation, and Model Characterization

Main findings:

Fonte analítica: `M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/RESULTS.md`.

Distribuições de classes, tamanho e diversidade estão em `M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_characterization.csv`; diferenças lexicais são estratificadas por classe em `M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_textual_characteristics.csv`.

RAW e CANONICALIZED são arquivos distintos, com tamanhos diferentes em parte das fontes. artificial é documentado, mas artificial_sqli é a variante da grade principal.

As 14 versões das fontes primárias têm prevalência positiva 0.500000 a 0.500000 (`M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_characterization.csv`, filtro primary=True). Isso controla a prevalência global entre arquivos, mas não torna os conteúdos equivalentes nem garante balanço após remoções no desenvolvimento.

Fonte analítica: `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/RESULTS.md`.

Dimensões e features reais constam em `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/representations.csv` e `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/engineered_features.csv`; truncamento CodeBERT em `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/embedding_metadata.csv`.

CANONICALIZED designa a representação decoded. Não significa que casefold e whitespace tenham sido aplicados ao texto do CodeBERT. Transformações isoladas do RAW estão em `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/canonicalization_effects.csv`, com escopo explícito.

Fonte analítica: `M04_05_Models_Training__C05_02_Model_Characterization/RESULTS.md`.

MLP compacto usa sklearn e CPU, com arquitetura e procedimento listados em `M04_05_Models_Training__C05_02_Model_Characterization/tables/models.csv` e `M04_05_Models_Training__C05_02_Model_Characterization/tables/model_hyperparameters.csv`.

Não há evidência de busca de hiperparâmetros entre configurações; selected_iterations descreve early stopping (`M04_05_Models_Training__C05_02_Model_Characterization/tables/selected_configs_by_target.csv`).

Tables to include:

- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_characterization.csv`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_class_distribution.csv`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_textual_characteristics.csv`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/tables/dataset_provenance.csv`
- `artigo/analise_resultados_tcc/M04_04_Input_Feature_Representations__C05_02_Representation_Characterization/tables/engineered_features.csv`

Figures to include:

- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/figures/length_by_class.pdf`
- `artigo/analise_resultados_tcc/M04_02_Datasets_Provenance__C05_02_Dataset_Characterization/figures/encoding_by_class.pdf`

Source analysis folders:

- `M04_02_Datasets_Provenance__C05_02_Dataset_Characterization`
- `M04_04_Input_Feature_Representations__C05_02_Representation_Characterization`
- `M04_05_Models_Training__C05_02_Model_Characterization`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Arquivos originais processados um dataset por vez; sem treino. Caracterização lexical existente reutilizada com sua procedência. n_unique refere-se ao texto realmente carregado; prevalência é ataques/n. DOI, ano e método de geração permanecem ausentes quando não registrados.
Dimensões calculadas pelo extrator existente em uma entrada sintética, sem fit. CodeBERT congelado: versão, max_length, pooling e truncamento lidos dos metadados do cache; dimensões densas não recebem interpretação semântica.
Contagens de todos os runs utilizáveis; custo por modelo/protocolo. Transformação median imputer + StandardScaler ajustada exclusivamente no treino. CatBoost até 200 árvores, MLP até 40 épocas; configurações descritas a partir dos arquivos atuais e suas limitações históricas.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.3 Cross-Dataset Generalization — RQ1

Main findings:

Fonte analítica: `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/RESULTS.md`.

Resultado principal: LODO C por target/modelo em `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/lodo_by_target.csv`; ID separado em `ID/tables/id_results.csv`.

Gap e razão de generalização estão em `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/generalization_gap.csv` e `generalization_ratio.csv`. Targets ruins permanecem nas tabelas; médias macro não os substituem.

Comparações A/B/C usam somente targets comuns (`M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/scenario_common_targets.csv`). Pares da mesma família são identificados e excluídos das médias de transferência independente.

Embeddings e early fusion estão em `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/embedding_and_fusion_results.csv`. Não existem scores internos suficientes para afirmar associação validação→OOD.

CANONICALIZED: menor F1 médio por condição = 0.681626 (srbh/logistic); maior = 0.977740 (proprio/catboost). Fonte: `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/lodo_by_target.csv`, row_id d2e53f0571c59f89f1ae e 6c75323536f9aeac2026. Maior gap ID−OOD = 0.301450 (srbh/logistic); `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/generalization_gap.csv`, row_id 508fbf5749b4ae69dbe8.

RAW: menor F1 médio por condição = 0.577788 (srbh/logistic); maior = 0.926085 (proprio/mlp). Fonte: `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/lodo_by_target.csv`, row_id fb8f2bded56927baf083 e e59d22380d8329934616. Maior gap ID−OOD = 0.360289 (srbh/logistic); `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/generalization_gap.csv`, row_id f56061c7fe01b36a916c.

CANONICALIZED: catboost teve maior média não ponderada de F1 entre targets (0.882548); trata-se de ranking descritivo, não superioridade universal. `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/lodo_macro_summary.csv`, row_id 05ab85daff406336b5be.

RAW: mlp teve maior média não ponderada de F1 entre targets (0.798002); trata-se de ranking descritivo, não superioridade universal. `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/LODO/tables/lodo_macro_summary.csv`, row_id 160991492c0a740d3ff8.

A associação pairwise médio→LODO não foi detectada após Holm em 6 de 6 estratos modelo/representação; ver M04.11/statistics/pairwise_vs_lodo.csv, filtro p_holm≥0.05. Isso não prova ausência de associação; há poucos targets.

Tables to include:

- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/ID/tables/id_results.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/pairwise_results.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/source_average.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/target_average.csv`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/PAIRWISE/tables/transfer_asymmetry.csv`

Figures to include:

- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_f1.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_mcc.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/pairwise_pr_auc.pdf`
- `artigo/analise_resultados_tcc/M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization/figures/lodo_RAW.pdf`

Source analysis folders:

- `M04_06_Cross_Dataset_Protocol__C05_03_RQ1_Generalization`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Principal metrics_source, threshold escolhido na validação de origem. PR-AUC=average_precision_score (não trapezoidal). Seeds resumidas dentro de cada condição. Gap=M_ID−M_OOD; razão F1_OOD/F1_ID, indefinida se denominador zero. Cenários não são combinados. SOURCE_AWARE_VALIDATION documenta somente os domínios e early stopping realmente existentes.

Direct RQ answer: há transferência com magnitude heterogênea e perdas frente ao ID; os piores targets/condições e ranking descritivo estão nas tabelas citadas. Relação pairwise→LODO em LODO/tables/pairwise_vs_lodo.csv e M04.11/statistics/pairwise_vs_lodo.csv. Não alegar generalização universal.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.4 Source-Dataset Contribution — RQ2

Main findings:

Fonte analítica: `M04_07_Source_Contribution__C05_04_RQ2_Contribution/RESULTS.md`.

A contribuição principal usa pool completo menos uma fonte com mesmo target/modelo/representação/seed (`M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_contribution_full.csv`).

Os casos de negative transfer estão em `M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/negative_transfer.csv`; efeitos positivos e nulos também são preservados. Fontes removidas automaticamente pelo filtro de família ficam em `M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/family_filtered_noops.csv`.

O arquivo legado dataset_shapley.csv não é utilizado como estimativa Shapley clássica.

Há 111 condições com contribuição F1 negativa, 129 positiva e 0 neutra após média das seeds (`M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/negative_transfer.csv`, `positive_transfer.csv`, `neutral_transfer.csv`; contagem de linhas). Portanto mais fontes não ajudaram sempre. Maior caso negativo: proprio→srbh, logistic/RAW: F1 full=0.577788, sem fonte=0.741797, contribuição=-0.164008; row_id 8af155769200c509eb5e de `negative_transfer.csv`.

CANONICALIZED: maior contribuição média descritiva entre modelos/targets é artificial_sqli (0.055983); menor é site_sqli (-0.010699). `M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_overall_summary.csv`, row_id 523c8f05df36686d5c71 e 24fb56d0a7eba51399f4. Os contadores targets_helped/harmed em `source_summary.csv` mostram exceções; média positiva não implica ajuda consistente.

RAW: maior contribuição média descritiva entre modelos/targets é srbh (0.052204); menor é proprio (-0.050563). `M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_overall_summary.csv`, row_id 7307a099cef5da8f3e8b e 0e82bb04c13f09477a38. Os contadores targets_helped/harmed em `source_summary.csv` mostram exceções; média positiva não implica ajuda consistente.

Tables to include:

- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_contribution_full.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_target_matrix_f1.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_target_matrix_mcc.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/source_summary.csv`
- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/tables/target_summary.csv`

Figures to include:

- `artigo/analise_resultados_tcc/M04_07_Source_Contribution__C05_04_RQ2_Contribution/figures/source_contribution.pdf`

Source analysis folders:

- `M04_07_Source_Contribution__C05_04_RQ2_Contribution`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

C_i=M(full)−M(without_i); positivo indica contribuição para F1/MCC/AP/recall. Para FPR/FNR benefit=erro(without)−erro(full). Seeds pareadas primeiro; médias e desvios dentro da condição. Alteração de validação é registrada por par. Não interpretar o efeito como causalidade.

Direct RQ answer: mais fontes nem sempre ajudam; negative transfer é observado nas condições citadas. O sinal depende do target/modelo e mudanças na validação; não é causalidade isolada de uma fonte.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.5 Decision Behavior — RQ3

Main findings:

Fonte analítica: `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/RESULTS.md`.

Threshold drift e oracle gap estão separados em `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_drift.csv` e `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/oracle_gap.csv`; oracle é diagnóstico pós-teste.

Brier e ECE-10 já estavam nos arquivos de métricas e foram reutilizados (`M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/calibration_results.csv`). Não houve treinamento de calibrador.

Scores são inspecionados somente nos casos selecionados (`selected_runs/threshold_cases.csv`). Scores de validação/source não foram salvos; comparação source vs target não é reconstruída.

Maior oracle gap LODO C = 0.405255, em proprio/catboost/RAW, seed 123. F1 com threshold de origem=0.529767; F1 oracle diagnóstico=0.935021; AP=0.887015. `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_results.csv`, row_id e8f6dbc2bdb16152927b. Isso mostra margem diagnóstica de decisão para o ranking existente; não demonstra que retuning no target seria permitido.

Tables to include:

- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_results.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/threshold_drift.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/oracle_gap.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/calibration_results.csv`
- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/tables/calibration_id_vs_ood.csv`

Figures to include:

- `artigo/analise_resultados_tcc/M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration/figures/selected_score_distributions.pdf`

Source analysis folders:

- `M04_08_Decision_Behavior__C05_05_RQ3_Thresholds_Calibration`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Drift=abs(t_source−t_oracle); oracle gap=F1_oracle−F1_source. ECE usa 10 intervalos uniformes [0,1]; Brier=mean((p−y)^2). Probabilidades não são assumidas calibradas. Mudança ID/OOD inclui populações de teste diferentes. Associações usam seeds resumidas e targets como unidades.

Direct RQ answer: oracle gap positivo quantifica margem de decisão, mas não prova que toda queda OOD decorra do threshold. Não escolher t_oracle para deployment ou avaliação principal.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.6 Feature Stability — RQ3

Main findings:

Fonte analítica: `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/RESULTS.md`.

Rankings CatBoost e estabilidade estão em `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_rankings_by_target.csv`, `stable_features.csv` e `feature_stability.csv`.

Alterações por remoção de fonte e sua coincidência com F1/MCC/recall/FPR estão em `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/source_removal_feature_effects.csv`.

Ablações existentes são incluídas em `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_ablation_by_target.csv`. Dimensões dos embeddings não foram interpretadas como features semânticas.

CANONICALIZED: char_equals lidera por frequência Top-10 (1.000000), importância média 7.044073; `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stable_features.csv`, row_id 80409a145b8b015694bf. É estabilidade observada do ranking CatBoost, não invariância causal.

RAW: sql_comment_dash lidera por frequência Top-10 (1.000000), importância média 15.196501; `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stable_features.csv`, row_id e1bd6646c83296e33b4f. É estabilidade observada do ranking CatBoost, não invariância causal.

full_vs_removed/CANONICALIZED: média descritiva de Spearman=0.864649, Jaccard Top-10=0.722791; `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stability_overview.csv`, row_id b24855dae0b981e96bf0. A média de condições não é tratada como n de targets independentes.

full_vs_removed/RAW: média descritiva de Spearman=0.809984, Jaccard Top-10=0.658153; `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stability_overview.csv`, row_id be367e68ad162b445832. A média de condições não é tratada como n de targets independentes.

target_vs_target/CANONICALIZED: média descritiva de Spearman=0.820234, Jaccard Top-10=0.662290; `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stability_overview.csv`, row_id 72291a41fbaad64d9259. A média de condições não é tratada como n de targets independentes.

target_vs_target/RAW: média descritiva de Spearman=0.792028, Jaccard Top-10=0.582311; `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stability_overview.csv`, row_id 051f1be03d30922f24c1. A média de condições não é tratada como n de targets independentes.

Não foi detectada associação ajustada entre instabilidade e OOD F1, gap ou negative transfer nos estratos avaliados. Fonte: M04.11/statistics/cross_rq_relationships.csv, filtro relationship.startswith(feature_instability); p_Holm≥0.05. Não significa que as relações sejam inexistentes.

Ablações CANONICALIZED: maior melhora observada vs lex64 = 0.132225 (ecml/logistic/no_special_chars); maior queda = -0.247626 (csic/catboost/char_rates). `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/ablation_effects_by_target.csv`, row_id 0c43cc829fa611b1327e e cee06f8f931fc60e666e. São extremos descritivos pós-teste, não seleção de features validada para deployment.

Ablações RAW: maior melhora observada vs lex64 = 0.166924 (ecml/logistic/no_special_chars); maior queda = -0.220080 (csic/logistic/char_rates). `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/ablation_effects_by_target.csv`, row_id f649d0e94abc09b0dc4c e b1ceb88aac1b12dac5b9. São extremos descritivos pós-teste, não seleção de features validada para deployment.

Tables to include:

- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_rankings_by_target.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/stable_features.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_stability.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/feature_rank_correlations.csv`
- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/tables/jaccard_topk.csv`

Figures to include:

- `artigo/analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/figures/stable_features.pdf`

Source analysis folders:

- `M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Somente importâncias CatBoost já existentes, lex64, LODO C e coalizões full/leave-one-source. Spearman/Kendall entre ranks médios, empates com average rank. Top-10 desempata por nome; Jaccard=interseção/união. Importância é model-specific e não causal; estável não implica invariância universal. RAW vs CANONICALIZED depende do pareamento auditado na fase RQ4.

Direct RQ answer: estabilidade é propriedade observada dos rankings CatBoost; features associadas a uma origem são possíveis dependências do dataset. Não chamar features de invariantes causais.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.7 Canonicalization and Dataset Separability — RQ4

Main findings:

Fonte analítica: `M04_10_Canonicalization_Separability__C05_07_RQ4/RESULTS.md`.

A elegibilidade pareada de cada comparação está em `RAW_VS_CANONICALIZED/tables/pairing_audit.csv`; apenas execuções elegíveis alimentam `paired_results.csv`.

Separabilidade existente é exploratória: os tamanhos por origem não são iguais e duplicatas não foram controladas (`DATASET_SEPARABILITY/tables/separability_all.csv`). Os experimentos benign-only e malicious-only não existem.

Sem observações de separabilidade por target, as relações separabilidade→generalização não são estimáveis (`RELATIONSHIPS/tables/separability_vs_generalization.csv`).

Dos 8220 candidatos pareados por configuração, 15 satisfizeram igualdade de amostras por split. Protocolos elegíveis: baseline_id; targets: ecml. Fonte: `RAW_VS_CANONICALIZED/tables/pairing_audit.csv` e `paired_results.csv`. Não há estimativa pareada LODO do efeito isolado da canonicalização.

Separabilidade exploratória RAW: Macro-F1=0.854330, n=30654, seed=42; `DATASET_SEPARABILITY/tables/separability_all.csv`, row_id 942361a1b4c01196ea6d. Sem controles suficientes, isso não prova redução controlada de separabilidade.

Separabilidade exploratória CANONICALIZED: Macro-F1=0.822894, n=30436, seed=42; `DATASET_SEPARABILITY/tables/separability_all.csv`, row_id 646fce9b57d77aebf01a. Sem controles suficientes, isso não prova redução controlada de separabilidade.

Tables to include:

- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/pairing_audit.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/paired_results.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/by_target.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/by_model.csv`
- `artigo/analise_resultados_tcc/M04_10_Canonicalization_Separability__C05_07_RQ4/RAW_VS_CANONICALIZED/tables/win_tie_loss.csv`

Figures to include:


Source analysis folders:

- `M04_10_Canonicalization_Separability__C05_07_RQ4`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Parear protocolo/target/fontes/modelo/config/feature/seed/family policy. Exigir contagens iguais e multiconjuntos dataset+canonical_hash+label+split iguais. Delta=CANONICALIZED−RAW. O hash canônico permite alinhamento sem IDs dependentes de representação. Mesmo multiconjunto não prova equivalência individual de rótulos conflitantes; casos de erro serão pareados somente por chave única. Não realizar treino adicional para preencher condições ausentes.

Direct RQ answer: efeito isolado de canonicalização em OOD não identificável no protocolo salvo. Separabilidade disponível é exploratória e não sustenta a hipótese controlada RAW vs CANONICALIZED. Não generalizar os pares ID/ECML para LODO.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.8 Statistical Synthesis

Main findings:

Fonte analítica: `M04_11_Statistics__C05_08_Statistical_Synthesis/RESULTS.md`.

As unidades estatísticas são targets após resumo das seeds (`M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/descriptive_summary.csv`). Intervalos bootstrap são exploratórios para este conjunto de fontes.

Wilcoxon, Friedman e correção Holm estão em `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/wilcoxon_results.csv`, `friedman_results.csv` e `holm_adjusted.csv`.

Associações previstas aparecem em `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`; correlações entre número de fontes e F1 dentro de cada target são descritivas em `source_count_within_target.csv`.

Entre 132 testes com p ajustado disponível, 0 têm p_Holm<0.05, nas famílias pré-especificadas no arquivo. `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/holm_adjusted.csv`, filtro p_holm.notna(); isso não converte ausência de detecção nos demais testes em prova de equivalência.

Nenhum ranking de modelos é confirmado pelos testes Friedman corrigidos quando p_Holm≥0.05; 6 de 6 omnibus nessa situação (`M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/holm_adjusted.csv`, filtro test=friedman). Post-hoc só seria realizado após omnibus ajustado significativo.

Relação brier_vs_ood_f1: 2 de 6 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=brier_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação calibration_degradation_vs_ood_f1: 1 de 6 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=calibration_degradation_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação feature_instability_vs_generalization_gap: 0 de 2 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=feature_instability_vs_generalization_gap. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação feature_instability_vs_negative_transfer: 0 de 2 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=feature_instability_vs_negative_transfer. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação feature_instability_vs_ood_f1: 0 de 2 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=feature_instability_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação oracle_gap_vs_ood_f1: 0 de 6 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=oracle_gap_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação source_contribution_vs_ood_f1: 0 de 6 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=source_contribution_vs_ood_f1. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Relação threshold_drift_vs_generalization_gap: 0 de 6 estratos com p_Holm<0.05; tabela `M04_11_Statistics__C05_08_Statistical_Synthesis/statistics/cross_rq_relationships.csv`, filtro relationship=threshold_drift_vs_generalization_gap. P-valor de Spearman por permutação exata; tratar resultados como exploratórios.

Tables to include:


Figures to include:


Source analysis folders:

- `M04_11_Statistics__C05_08_Statistical_Synthesis`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Seeds não são unidades independentes. Wilcoxon bilateral sobre diferenças entre targets; mínimo cinco targets; Holm por família registrada. Friedman por representação/métrica para três modelos (aproximação qui-quadrado, n pequeno); post-hoc somente se omnibus p_Holm<.05. Spearman cross-RQ com permutação bilateral exata até oito targets, uma observação por target; sem inferência quando constante ou n<5. Não usar resultados estatísticos legados com pseudo-replicação. Brier combina calibração/discriminação e compartilha predições com F1; correlação não isola mecanismos.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## 5.9 Reproducibility

Main findings:

Fonte analítica: `M04_12_Reproducibility__C05_09_Reproducibility/RESULTS.md`.

Custo reconstruído por soma dos tempos registrados em `M04_12_Reproducibility__C05_09_Reproducibility/tables/runtime_summary.csv`; não representa tempo de calendário, nem todos os custos de extração do encoder.

Arquivos e espaço constam em `M04_12_Reproducibility__C05_09_Reproducibility/tables/storage_summary.csv`; completude de metadados em `M04_12_Reproducibility__C05_09_Reproducibility/tables/artifact_completeness.csv`.

Valores de tabelas foram escolhidos com seed fixa e recalculados dos JSON originais (`M04_12_Reproducibility__C05_09_Reproducibility/tables/reproducibility_audit.csv`).

Foram reconstruídos 15 valores finais diretamente dos JSON originais; 15 conferiram à tolerância 1e-12. Fonte: `M04_12_Reproducibility__C05_09_Reproducibility/tables/reproducibility_audit.csv`, coluna match.

Tables to include:

- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/runtime_summary.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/storage_summary.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/artifact_completeness.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/reproducibility_audit.csv`
- `artigo/analise_resultados_tcc/M04_12_Reproducibility__C05_09_Reproducibility/tables/selected_prediction_metric_audit.csv`

Figures to include:


Source analysis folders:

- `M04_12_Reproducibility__C05_09_Reproducibility`

Supplementary: todas as tabelas por target, source composition, modelo e representação; seeds e pares exatos nos derived; arquivos SOURCE_FILES e TRACEABILITY. Não substituir tabelas por target apenas por médias globais.

Important limitations:

Somente stat dos artefatos grandes; checkpoints não são lidos. Runtime somado apenas para runs utilizáveis, falhas sem duração não imputadas. RSS é pico cumulativo do processo, não memória incremental por fold. Configuração atual tem hash, porém histórico imutável não existe. Auditoria numérica seleciona linhas de tabelas ID/LODO/threshold e reabre os JSON de métricas para média independente.

Negative/null findings: manter todas as linhas de efeito negativo/zero e testes não significativos. Ausência de dados ou condições não executadas é limitação, não resultado nulo.

Safe conclusions: somente descritivas nas condições/targets observados e inferências exploratórias que respeitam unidade target e Holm. Unjustified conclusions: causalidade, equivalência a partir de p>0.05, generalização universal ou atribuição de diferenças a uma transformação sem pareamento.

---

## Data Sources and Traceability

Original inputs: `artigo/results/raw/EXP_*.json`, `artigo/runs/status/EXP_*.json`, `artigo/runs/manifests/EXP_*.json`, `artigo/docs/experiment_registry/experiments.csv`, original dataset metadata/configuration, and selected predictions/features/splits only. Full paths and IDs: `_global/SOURCE_LINEAGE.parquet` and `_global/SOURCE_FILES.parquet`. Actual unique files read and byte counts: `_global/FILES_READ.parquet`, `_global/file_read_summary.csv`. No checkpoint content read.

Master table: `_global/master_results.parquet`; registry: `_global/run_registry.parquet`. Columns, exact row filters, groupings, artifacts/tables/figures and formulas are documented per section in TRACEABILITY.csv, ANALYSIS_METHOD.md and Metric Provenance. Seeds are averaged within condition; targets are the statistical units. Each reported value is linked to a table row_id with experiment_ids. Missing conditions are not imputed. Complete generated artifact catalog: `_global/ARTIFACT_CATALOG.csv`.

Script: `artigo/scripts/analysis/final_analysis.py`. Config: `artigo/scripts/analysis/config.json`. Command: `<PROJECT_ROOT>/../../venv/bin/python <PROJECT_ROOT>/artigo/scripts/analysis/final_analysis.py --config <PROJECT_ROOT>/artigo/scripts/analysis/config.json`. Derived outputs are all within `artigo/analise_resultados_tcc/`. Follow each section's SOURCE_FILES.parquet for original metrics, predictions, scores, thresholds, features and manifests. Use trace_value.py for a specific cell.
