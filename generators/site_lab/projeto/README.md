# SQLi Laboratory Application

Aplicacao de laboratorio para instrumentacao de requisicoes relacionadas a SQL injection.
Ela usa Flask, Gunicorn, SQLite e Nginx. O Nginx e o ponto de entrada HTTP e registra cada
requisicao em JSON para coleta futura.

## Subir o laboratorio

No ambiente Linux deste host (ou qualquer host com Docker Engine e Docker Compose instalados), abra um terminal na pasta `projeto/` e execute:

```sh
docker compose up --build -d
```

A aplicacao e construida e executada localmente, sem dependencia de WSL, Docker Desktop ou maquina virtual Parrot externa.

A aplicacao fica acessivel pelo Nginx em HTTPS:

```text
https://localhost:8443/
https://localhost:8443/docs
https://localhost:8443/forum
https://localhost:8443/docs/SQL/postgres/
```

O certificado e self-signed e gerado automaticamente pelo container Nginx em cada
`docker compose up`; use `curl -k https://localhost:8443/` para testes de linha de comando.
O endereco `http://localhost:8080/` permanece disponivel apenas para redirecionar com 301 para
o HTTPS em `https://localhost:8443/`.

Para testar a conectividade local:

```sh
bash tools/traffic/conn_test.sh
```

## Toolbox Kali isolado

As ferramentas previstas para a campanha controlada (`sqlmap`, `ffuf` e `wfuzz`) ficam em
uma imagem Kali dedicada. Nada e instalado diretamente no host. O servico nao publica
portas, nao recebe privilegios, nao monta o socket do Docker e participa apenas da rede
interna `toolbox_net`, compartilhada com o Nginx do laboratorio.

Para construir e deixar o toolbox em execucao:

```sh
bash tools/kali_toolbox.sh up
bash tools/kali_toolbox.sh status
```

O laboratorio (`app` e `nginx`) deve estar iniciado antes. O helper usa `--no-deps` para
nao reconstruir nem reiniciar a aplicacao ao operar somente o Kali.

O alvo interno do laboratorio e disponibilizado no container como:

```text
TARGET_URL=https://nginx
```

As wordlists do diretorio raiz `PAYLOADS/` aparecem somente para leitura em `/payloads`.
Arquivos temporarios do toolbox devem ser gravados em `/workspace`, um volume gerenciado
pelo Docker. Para validar a instalacao e o isolamento sem iniciar uma campanha:

```sh
bash tools/kali_toolbox.sh versions
bash tools/kali_toolbox.sh doctor
```

Para abrir um shell sem instalar nada no host:

```sh
bash tools/kali_toolbox.sh shell
```

O helper tambem oferece `build`, `stop` e um comando `exec` restrito a `sqlmap`, `ffuf`,
`wfuzz`, `curl`, `jq` e `python3`. Por exemplo: `bash tools/kali_toolbox.sh exec sqlmap
--version`. Os argumentos sao enviados diretamente ao processo no container, sem `eval` ou
shell intermediario. A rede interna impede que essas ferramentas alcancem alvos externos.

Use `bash tools/kali_toolbox.sh --help` para ver todos os comandos. O comando `stop` para
somente o toolbox e preserva `/workspace`; ele nao remove volumes nem apaga resultados.

### Wrappers da fase 22

O executavel `lab-sqli-tools` fica dentro da imagem e oferece vetores controlados para
`sqlmap`, `ffuf` e `wfuzz`. O modo padrao e **plan**: ele mostra o comando e nao envia
requisicoes. Exemplos seguros:

```sh
bash tools/kali_toolbox.sh plan ffuf get-search
bash tools/kali_toolbox.sh plan wfuzz post-login-json
bash tools/kali_toolbox.sh plan sqlmap post-graphql-json --tamper space2comment
```

Vetores disponiveis: `get-search`, `get-docs`, `post-login-json`, `post-comment-form` e
`post-graphql-json`. O alvo e validado como exatamente `https://nginx`; taxa, concorrencia e
tempo possuem limites. Resultados de execucoes futuras ficam em `/workspace/runs`.

O comando `run` e a segunda trava de seguranca e deve ser usado apenas quando a janela de
ataque da fase 22 for iniciada conscientemente. Nenhum dos comandos `up`, `status`,
`versions`, `doctor` ou `plan` dispara payloads SQLi.

O toolbox e apenas um pre-requisito tecnico. Subi-lo nao inicia a campanha da fase 22.

### Campanha SQLi controlada

O orquestrador `tools/attack/attack_campaign.py` preserva a janela benigna, abre um log
novo, executa contribuicoes limitadas de `ffuf`, `wfuzz` e `sqlmap` exclusivamente contra
`https://nginx`, completa a janela com `attack-injector` e produz o dataset rotulado. Sem
`--execute`, ele apenas exibe o plano:

```sh
python3 tools/attack/attack_campaign.py
python3 tools/attack/attack_campaign.py --execute
```

A campanha 01 concluida possui 30.113 registros benignos e 30.000 de ataque. Os dois logs
canonicos ficam, sem copias, em `log/benigno.jsonl` e `log/malicioso.jsonl`. O dataset e seus
metadados ficam separados em `dataset/dataset_final.jsonl`, `dataset/validacao.json` e
`dataset/manifesto.json`. O validador exige contagens exatas, rotulos 0/1,
metodos de ataque somente GET/POST, equilibrio GET entre 47% e 53% e sinal SQLi reconhecivel
em pelo menos 70% da janela maliciosa.

Para acompanhar os servicos, use `docker compose ps` ou `docker compose logs -f`. Para
derrubar o ambiente, execute:

```sh
docker compose down
```

## Resetar o banco

O banco gerado e `db/lab.db`. O primeiro start do servico `app` o cria automaticamente
quando ele nao existe. Para restaurar os dados iniciais depois de alterar ou testar a app,
execute dentro do container:

```sh
docker compose exec app sh tools/reset_db.sh
```

O mesmo script pode ser usado fora do Docker em um ambiente que tenha o executavel
`sqlite3` instalado:

```sh
sh tools/reset_db.sh
```

O reset remove `db/lab.db` e recria o arquivo aplicando, nesta ordem, `db/schema.sql`,
`db/seed.sql` e `db/seed_forum.sql`.

## Log de requisicoes

O Nginx grava o log corrente no container em `/var/log/nginx/lab.jsonl`. Esse caminho esta
montado no host como `logs/lab.jsonl`, dentro de `projeto/`. A pasta `logs/` e somente de
runtime; os logs finais consolidados ficam na pasta singular `log/`.

Cada requisicao gera uma linha JSON com timestamp e milissegundos, metodo, URI crua com a
query string, protocolo, status, tamanho e tempo de resposta, user-agent, referer, IP remoto,
corpo da requisicao e content type. A URI usa `$request_uri`, portanto sequencias como `%27`
permanecem codificadas no log; corpos JSON, formulario e GraphQL sao registrados em
`request_body`.

## Nota de laboratorio

Este projeto e destinado somente a laboratorio e pesquisa controlada. Por design, ele nao
aplica sanitizacao de entrada, WAF, rate limit ou bloqueio de caracteres, para preservar a
requisicao original no log. Isso nao torna a aplicacao exploravel: todos os acessos ao SQLite
usam queries parametrizadas.

Os arquivos versionados que definem o ambiente sao `nginx/nginx.conf`, `db/schema.sql` e
`db/seed.sql`. `db/lab.db` e `logs/lab.jsonl` sao artefatos gerados localmente e nao devem ser
versionados.
