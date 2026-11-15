# Campanha OJS (`proprio`)

Scripts legados da campanha autorizada que originou a base `proprio`. Eles
orquestram `sqlmap`, `ffuf`, `dalfox` e `XSStrike`, além de wordlists de
SecLists, PayloadsAllTheThings, FuzzDB e listas próprias.

O material sustenta a descrição de procedência e coleta da base OJS. A base
processada não é distribuída: pode conter material pessoal ou operacional e
continua condicionada à decisão do autor.

Todos os destinos versionados são exemplos sob `https://ojs.example.org`.
`revista-a` e `revista-b` são nomes fictícios. Os launchers leem destinos reais
de `config/targets.txt`, que está no `.gitignore`; copie
`config/targets.txt.example` e edite apenas em ambiente local autorizado.

Cookies, tokens CSRF e demais credenciais entram exclusivamente por variáveis
de ambiente ou arquivos ignorados. Nunca versione `.env`, `targets.txt`, logs
ou saídas de campanha.

Para inspecionar sem enviar tráfego:

```bash
cp .env.example .env
cp config/targets.txt.example config/targets.txt
AUTHORIZED_SECURITY_TESTING=YES DRY_RUN=1 bash scripts/run-all.sh --profile safe \
  --targets ./config/targets.txt --scope ./config/scope.txt
```

Os lançadores `run-*.sh` da raiz executam campanhas agressivas e exigem,
sempre, `AUTHORIZED_SECURITY_TESTING=YES` e `DANGEROUS_ACK=YES`. Enumeração,
dump, crawl e cadeias de tampers para todos os SGBDs ficam desativados por
padrão no lançador SQLmap legado.

Use somente contra sistemas próprios ou com autorização formal. O conteúdo é
mantido para procedência; não integra automaticamente o pipeline experimental
ativo do artigo.
