# Coleta de dados e correlação de amostras

## Identificadores

- **RUN_ID**: `YYYYMMDD-HHMMSS-<random6>` (ex.: `20260728-083012-a4f92c`).
- **Sample ID**: `<tool>-<target_id>-<category>-<sequence>`
  (ex.: `ffuf-login-form-sqli-raw-000042`).

Quando `ENABLE_SAMPLE_HEADERS=1`, cada requisição pode carregar:

```
X-Research-Sample-ID: ffuf-login-form-sqli-raw-000042
X-Research-Run-ID: 20260728-083012-a4f92c
```

permitindo correlacionar requisição, resposta, alerta de WAF/IDS, evento de
SIEM e a classificação do dataset.

## Estrutura de saída

```
output/<RUN_ID>/
├── metadata.json
├── manifest.tsv
├── sqlmap/  ffuf/  dalfox/  xsstrike/
logs/<RUN_ID>/
├── orchestrator.log  sqlmap.log  ffuf.log  dalfox.log  xsstrike.log
```

## manifest.tsv

Colunas: `run_id, sample_id, tool, target_id, timestamp, method, url_redacted,
payload_category, wordlist_source, command_hash, exit_code,
output_path`. Nunca armazena credenciais em claro — apenas versão mascarada,
hash do comando normalizado e referência ao arquivo seguro.

## Viés de dataset (User-Agent)

`UA_MODE=fixed` marca todo o tráfego de ataque com um UA próprio, tornando a
rotulagem trivial e o treino inútil (o modelo aprende a string). O default é
`mixed`: metade dos passes com UA fixo (rotulável) e metade com `--random-agent`
(treinável). Registre o `ua_mode` por amostra para poder filtrar.
