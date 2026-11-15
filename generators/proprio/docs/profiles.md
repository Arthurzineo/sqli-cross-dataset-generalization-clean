# Perfis de agressividade

Selecione com `PROFILE=<perfil>` ou `--profile <perfil>`. A carga de config é:
`defaults.env` → `profiles/<perfil>.env` → `.env` → variáveis de ambiente.

| Perfil       | Concorrência | Cobertura                          | Enum/Dump | Uso |
|--------------|--------------|------------------------------------|-----------|-----|
| `safe`       | mínima       | baixa (level 1, sem tampers/crawl) | não       | padrão, redes sensíveis |
| `standard`   | média        | intermediária (level 3, tampers)   | não       | coleta regular |
| `aggressive` | alta         | ampla (level 5, todos os tampers)  | não*      | laboratório isolado |
| `custom`     | você define  | você define                        | opcional  | ajuste fino |

\* Mesmo no `aggressive`, enumeração de metadados só ocorre com
`ALLOW_METADATA_ENUMERATION=YES`, e dump destrutivo é sempre proibido.

## Garantias do perfil aggressive

Exige `DANGEROUS_ACK=YES` além de `AUTHORIZED_SECURITY_TESTING=YES`, e continua
respeitando: escopo, limite global de requisições, limite de duração, espaço
em disco mínimo, e as proibições de pós-exploração, ações destrutivas e
callback externo.
