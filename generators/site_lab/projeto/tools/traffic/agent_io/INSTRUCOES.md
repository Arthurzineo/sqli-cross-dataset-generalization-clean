# INSTRUÇÕES — Protocolo de conteúdo por arquivos (agente ↔ gerador)

Você (agente: Antigravity ou Codex) é o **gerador de conteúdo** do laboratório. O content service
te aciona por um **toque curto via Orca** com um **ID único**. Sua tarefa é sempre a mesma:

1. **Ler** o arquivo `tools/traffic/agent_io/requests/<ID>.json`.
2. **Gerar** o conteúdo pedido (ver `type` + `topic` + `count`), em **inglês**, realista e variado.
3. **Escrever** o resultado em `tools/traffic/agent_io/responses/<ID>.json` no formato desta doc.
4. **Avisar** no terminal exatamente: `SAVED <ID>` (para o service saber que terminou).

> Regra de ouro: **NÃO** responda o conteúdo no chat. O conteúdo vai **só no arquivo de resposta**.
> Responda no chat apenas `SAVED <ID>`. Um request = um response com o **mesmo ID**.

## Formato do request (o service escreve; você lê)
```json
{
  "id": "abc123",
  "type": "answers | question | comment | reply | searchterm | name | tags",
  "topic": "join",              // tópico SQL/SGBD (select, where, join, union, group-by, ...)
  "count": 3,                    // p/ answers: quantas personas responder (1 nos demais)
  "context": {                   // presente quando você responde a algo específico
    "title": "Why does WHERE col = NULL return no rows?",
    "body": "..."
  },
  "status": "pending"
}
```

## Formato do response (você escreve)
Sempre com o **mesmo `id`**, `status:"done"`, e `items` conforme o `type`:

- **answers** / **reply** (múltiplas personas): cada item = uma persona diferente, estilo variado.
  ```json
  { "id":"abc123", "type":"answers", "status":"done", "items":[
      {"persona":"dba_veteran", "text":"..."},
      {"persona":"junior_dev",  "text":"..."},
      {"persona":"concise_kim", "text":"..."}
  ]}
  ```
- **question** (dúvida simulada): item com `title` + `body`.
  ```json
  { "id":"abc123", "type":"question", "status":"done", "items":[
      {"title":"How does LEFT JOIN differ from INNER JOIN?", "body":"..."}
  ]}
  ```
- **comment**: um item com `text` (e opcional `author`).
  ```json
  { "id":"abc123", "type":"comment", "status":"done", "items":[ {"author":"Ana", "text":"..."} ] }
  ```
- **searchterm** / **name** / **tags**: um item com `text` (curto).
  ```json
  { "id":"abc123", "type":"searchterm", "status":"done", "items":[ {"text":"inner join example"} ] }
  ```

## Personas (para answers/reply) — varie estilo/tom/comprimento
`dba_veteran` (preciso), `junior_dev` (iniciante), `backend_carla` (pragmática), `prof_okonkwo`
(didática), `skeptic_sam` (questiona), `concise_kim` (1 linha), `verbose_victor` (longo),
`ops_maria` (produção), `consultant_raj` (trade-offs), `student_lee`, `night_owl_nadia` (casual).

## Regras
- Conteúdo em **inglês**, plausível e **condicionado ao `topic`**. Pode conter tokens SQL.
- **Cru:** pode ter aspas, `--`, etc. — não sanitizar. É conteúdo benigno (sem ataque aqui).
- Não invente campos fora do schema. `id` do response = `id` do request. Termine com `SAVED <ID>`.
