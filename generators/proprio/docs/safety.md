# Segurança e limites

## Controles obrigatórios

1. **Autorização explícita** — `AUTHORIZED_SECURITY_TESTING=YES` (exato). O
   perfil `aggressive` exige também `DANGEROUS_ACK=YES`.
2. **Escopo** — todo alvo (e todo callback) é validado contra `config/scope.txt`.
   Alvos fora do escopo, esquemas diferentes de http/https e curingas amplos são
   recusados. Não seguir redirecionamento para host fora do escopo.
3. **Sem execução durante o desenvolvimento** — os scripts nunca são rodados
   contra alvos ao construir o projeto; apenas validação estática.

## Proibições

- Sem `--os-shell`, `--os-cmd`, `--os-pwn`, `--file-write`, `--file-dest`.
- Sem leitura/escrita de arquivos no servidor, takeover, pivoting.
- Sem `DROP`/`DELETE`/`TRUNCATE` ou payloads destrutivos; sem dump indiscriminado.
- Sem serviços públicos de blind XSS. Callback apenas para coletor **local** no escopo.
- Sem pós-exploração ou extração massiva de dados sensíveis.

## Segredos

Fornecidos por variáveis de ambiente ou arquivos `0600` fora do Git. Nunca
hardcode de senha/token, nem commit de cookies/Authorization. Logs e manifesto
mascaram `Authorization`, `Cookie`, `Set-Cookie`, senhas, tokens, API keys,
sessão e CSRF tokens.

## Limites operacionais (configuráveis)

`MAX_PARALLEL_JOBS`, `MAX_REQUESTS_PER_JOB`, `MAX_TOTAL_REQUESTS`,
`MAX_JOB_SECONDS`, `MAX_RUN_SECONDS`, `MAX_CRAWL_DEPTH`, `MAX_CRAWL_URLS`,
`MIN_FREE_DISK_GB`, `REQUEST_RATE`, `DELAY_MS`. Valores extremos devem exigir
confirmação adicional; o script deve parar de forma limpa ao atingir um limite.

## Validação estática permitida

```bash
bash -n scripts/*.sh
shellcheck scripts/*.sh   # quando disponível
bash tests/test_scope_validation.sh
bash tests/test_target_parser.sh
```

Proibido rodar as ferramentas ou qualquer sweep, mesmo em localhost.
