# Complementos da análise de generalização

Status: scripts implementados; resultados antigos preservados. Após autorização para execução, o piloto real passou e a sequência completa foi preparada para execução supervisionada. Estado atual, sem inferir conclusão: `artigo/complementos_generalizacao_v1/sequence/STATE.json`. A validação sintética continua separada dos resultados científicos.

A coleção controlada complementa a coleção histórica com comparações pareadas: as vistas RAW e CANONICALIZED derivam das mesmas linhas, o teste é comum às condições ID e OOD, e a validação permanece fixa quando uma fonte é removida.

| Lacuna | Complemento | Novo treinamento? |
|---|---|---|
| RAW/decoded históricos com populações diferentes | Duas vistas das mesmas linhas RAW; splits idênticos | Sim, bateria `paired` |
| ID e OOD avaliados em populações diferentes | ID e LODO também avaliados no mesmo holdout do alvo | Incluído em `paired` |
| Separabilidade sem controle completo | Mesmos tamanhos por origem/classe, purge canônico, all/benign/malicious | Sim, `separability` |
| Remoção de fonte muda a validação | Remover apenas fontes de treino; validação/teste congelados | Sim, opcional `contribution` |
| Média de marginais chamada de Shapley | Pesos fatoriais e jogo completo com referência vazia explícita | Não, `existing_analysis.py` |
| Auditoria de hashes apenas em runs selecionados | Auditoria incremental dos manifests completos | Não, `existing_analysis.py` |

## Arquivos e ordem recomendada

- `config.json`: fontes, seeds, modelos e recursos.
- `common.py`: coorte pareada, 64 features existentes, cache, splits e controles.
- `run.py`: plano por padrão; preparação e treinamentos sequenciais somente com stage explícito.
- `existing_analysis.py`: recálculo de Shapley e auditoria de splits, sem fit.
- `consolidate.py`: pares RAW/CANONICALIZED, gap ID/OOD em teste comum e contribuição com validação fixa; resumos por seed e lineage.
- `test_supplemental.py`: testes sintéticos com processos reais dos modelos.
- `ANALYSIS_METHOD.md`: decisões do protocolo.

O plano padrão prevê até 420 ajustes binários (7 alvos × 5 seeds × 3 modelos × 2 vistas × ID/LODO) e 30 classificadores de origem (3 condições × 5 seeds × 2 vistas). São quantidades planejadas, não resultados concluídos. Condições inviáveis ficam registradas como `NOT_APPLICABLE`. A contribuição é opcional e sua quantidade depende das fontes efetivamente presentes no treino; seus modelos full LODO são reutilizados da etapa paired.

## Comandos

Executar na raiz `GENERALIZACAO`, com o ambiente existente:

```bash
PY=<PROJECT_ROOT>/../../venv/bin/python

# Só plano, sem ler datasets nem treinar
$PY artigo/scripts/supplemental/run.py --stage plan

# Testes sintéticos e relatório persistente
$PY artigo/scripts/supplemental/test_supplemental.py --report artigo/complementos_generalizacao_v1/VALIDATION.json

# Recalcular summaries existentes, sem treinamento
$PY artigo/scripts/supplemental/existing_analysis.py --stage shapley

# Auditoria incremental: até 10 novos manifests nesta chamada
$PY artigo/scripts/supplemental/existing_analysis.py --stage audit-splits --limit 10

# Auditoria completa, retomável, sem treinamento (pode exigir bastante I/O)
$PY artigo/scripts/supplemental/existing_analysis.py --stage audit-splits

# Piloto explícito: até 50 entradas por classe/arquivo, 4 fits binários
$PY artigo/scripts/supplemental/run.py --stage paired --targets ecml --models logistic --seeds 42 --pilot-cap 50 --max-runs 4
$PY artigo/scripts/supplemental/consolidate.py --root artigo/complementos_generalizacao_v1/pilot_cap_50

# Um alvo e seed, sem subamostragem
$PY artigo/scripts/supplemental/run.py --stage paired --targets csic --seeds 42

# Baterias principais, quando decidir iniciar novos treinamentos
$PY artigo/scripts/supplemental/run.py --stage paired
$PY artigo/scripts/supplemental/run.py --stage separability

# Complemento opcional: remoção com validação fixa
$PY artigo/scripts/supplemental/run.py --stage contribution

# Alternativa: todas as três etapas, em sequência
$PY artigo/scripts/supplemental/run.py --stage all
$PY artigo/scripts/supplemental/consolidate.py
```

Repetir exatamente o comando retoma apenas jobs não concluídos/íntegros. `--max-runs` limita novos fits por chamada. Alterar configuração, dados ou código gera novas identidades; a consolidação não mistura contextos diferentes. Não executar duas instâncias no mesmo diretório: há trava de execução.

### Execução supervisionada em segundo plano

O supervisor externo exige o piloto consolidado, executa paired → consolidação → separability → consolidação → contribution → consolidação → auditoria completa de splits. Não refaz o recálculo de Shapley já concluído. Um subprocesso de etapa por vez; cada etapa treina um modelo por vez. A fila para se uma etapa falhar, preservando métricas e logs. Guarda cópia dos scripts/configurações e seus hashes em `sequence/source_snapshots/`. Solicita bloqueio temporário de suspensão enquanto está executando, sem alterar permanentemente a configuração do computador e sem desligá-lo ao terminar.

```bash
# Iniciar ou retomar após interrupção (não executar se já estiver ativo)
$PY artigo/scripts/run_supplemental_sequence.py --launch

# Consultar o estado salvo
$PY artigo/scripts/run_supplemental_sequence.py
```

`sequence/STATE.json` registra etapa, PID, comando, log e última checagem de processo. `sequence/monitor_20min.jsonl` registra verificações periódicas de contagens, falhas, RAM disponível e disco livre, a cada 20 minutos enquanto a etapa está ativa. Isso é monitoramento local em arquivo, não envio automático de mensagens nesta conversa. Resultados são salvos por fit. Retomada após reiniciar o computador exige executar novamente `--launch`; não há serviço de inicialização automática.

## Recursos e armazenamento

CPU, um treinamento por processo e por vez; no máximo duas threads. Limite padrão de espaço virtual de 12 GiB por worker, não promessa de consumo físico de 12 GiB. Antes do fit exige pelo menos 2 GiB de RAM disponíveis. Falha de memória interrompe a fila e é registrada; não reduz dados silenciosamente. Ajustar recursos na configuração e retomar conscientemente. Não há GPU nem download de encoder nesta bateria.

Cache persistente de features float32; leitura mapeada, apenas subconjuntos necessários materializados. A preparação lê um dataset por vez, mas mantém as matrizes lexicais compactas para concatenar o cache. Não lê checkpoints antigos nem os 280 GB em RAM. Checkpoints novos desabilitados; guarda métricas, scores de validação/teste, manifests, importância CatBoost e hashes. Arquivos temporários dos testes sintéticos são descartados, sem tocar dados científicos.

## Data Sources and Traceability

As decisões específicas estão em `ANALYSIS_METHOD.md`. O plano é calculado de um arquivo `config.json`; nenhum resultado experimental é inferido do plano. Comando: `python artigo/scripts/supplemental/run.py --stage plan`; saída `artigo/complementos_generalizacao_v1/full/PLAN.json`.

Entradas de treino futuras: caminhos RAW resolvidos por `artigo/src/data/loader.py` e `artigo/config/datasets.yaml`; hashes/caminhos/quantidades efetivamente lidas ficam em `cache/*/READY.json`, `cohort.parquet` e `input_audit.parquet`. IDs futuros: `runs/SUPP_*/job.json`, `metrics.json`, `status.json`; não há IDs científicos novos neste README. Colunas, filtros, fórmulas e agregação de seeds: `ANALYSIS_METHOD.md`. Manifestos analíticos: `analysis/SOURCE_LINEAGE.parquet`; cada linha derivada contém `experiment_ids` e `row_id`. Nenhuma figura é produzida por esta preparação.

Recálculos antigos usam dois arquivos analíticos (`master_results.parquet` e `SOURCE_LINEAGE.parquet`), sem abrir métricas/checkpoints de cada run; `existing_analysis/EXECUTION.json` registra comando, hashes e contagem de IDs. `existing_analysis/SOURCE_FILES.parquet` aponta para os originais. Auditoria de splits: arquivos `EXP_*.json` e `SUMMARY.json` em `existing_analysis/split_audit/` registram cada leitura e sua abrangência. Validação sintética: `VALIDATION.json` guarda comando, hashes, número de testes e falhas.

Piloto real autorizado: `pilot_cap_50/analysis/AUDIT.json`, `master_results.parquet` e `SOURCE_LINEAGE.parquet`; comando paired com `--targets ecml --models logistic --seeds 42 --pilot-cap 50 --max-runs 4`. Seus quatro IDs constam da lineage desse piloto, não do inventário histórico. Supervisor: `artigo/scripts/run_supplemental_sequence.py --launch`; origem das contagens monitoradas: `full/runs/SUPP_*/status.json` (sem agregar métricas/seeds). Quantidade de arquivos de status lidos por verificação equivale à soma das contagens registradas. Logs e cópias de código: `sequence/`; nenhum resultado de generalização é inferido do estado dos processos.
