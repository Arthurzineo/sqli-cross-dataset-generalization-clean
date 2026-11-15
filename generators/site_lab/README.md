# Laboratório dos sites

Contém as aplicações `projeto/` e `Projeto 2/` usadas para os sites SQL e culinária.

Cada aplicação inclui Dockerfile, dependências e `docker-compose.yml`.
Os diretórios `tools/traffic/` contêm navegação Playwright e campanhas.
Agentes, personas e prompts preservados documentam o conteúdo benigno.
Wordlists e rotas de ataque pertencem à coleta maliciosa controlada.
`IMPLEMENTACAO-app-alvo-sqli.md` e `ROTAS.md` descrevem a construção.

Use apenas em ambiente local e verifique os `.env.example` antes de subir.
Os logs operacionais foram removidos do material publicável.
As bases finais `site_sqli` e `site_cooking` estão em `datasets/processed/`.
Consulte o README de cada aplicação para os comandos do laboratório.
