# Sanitização da base `proprio`

As cópias desta pasta foram geradas sem alterar os arquivos usados nos
experimentos. O script não persiste a relação entre valores originais e
marcadores sintéticos.

Para reproduzir a sanitização, as entradas restritas devem ser fornecidas em
`datasets/restricted/proprio/raw/proprio.tsv` e
`datasets/restricted/proprio/canonicalized/proprio.tsv`. Esses arquivos de
entrada não fazem parte do repositório.

## Arquivos

| Vista | Linhas | Benignas | Maliciosas | SHA-256 |
|---|---:|---:|---:|---|
| RAW | 37.232 | 18.616 | 18.616 | `28b355a0286fa46d0b0c8a0c95d9b057c7d78578ca3d93ec909076d4515eaf32` |
| CANONICALIZED | 37.212 | 18.606 | 18.606 | `2ce6cd0d7531c38673aa5cb6d6f6eeb2b336206f363b865ae24b80be718cbb31` |

## Palavras de troca

| Categoria | Marcador |
|---|---|
| nome de pessoa ou autor | `Jane Doe` |
| e-mail | `usuario_000001@example.invalid` |
| usuário ou senha | `removida` |
| token, sessão ou CSRF | `removido` |
| perfil, endereço ou afiliação | `PERFIL_REMOVIDO_000001` |
| telefone | `TELEFONE_REMOVIDO_000001` |
| ORCID | `ORCID_REMOVIDO_000001` |
| CPF/CNPJ ou sequência documental | `DOCUMENTO_REMOVIDO_000001` |
| texto editorial, parecer ou metadado textual | `TEXTO_CONFIDENCIAL_REMOVIDO_000001` |
| consulta (`query` ou `searchPhrase`) | `CONSULTAREMOVIDA000001` |
| campo `data` | `registro sintetico de teste 000001` |
| motivo de desativação | `desativado para teste editorial 000001` |
| nota editorial | `nota editorial sintetica 000001` |
| busca | `consulta editorial sintetica 000001` |
| termo | `termo academico sintetico 000001` |
| interesse | `interesse academico sintetico 000001` |
| fonte benigna | `referencia editorial sintetica 000001` |
| nome de periódico | `REVISTA_0001` |
| identificador operacional | número sintético iniciado por `900` |
| arquivo enviado | `ARQUIVO_000001.dat` |
| arquivo presente em caminho | `documento-sintetico-000001.ext` |
| segmento de proprietário | `usuario-exemplo-000001` |
| DOI | prefixo de teste `10.5555/` seguido de 12 dígitos determinísticos |
| domínio externo | `teste.com.br` |
| endereço IPv4 | faixa de documentação `192.0.2.0/24` |
| host absoluto | `https://ojs.example.org` |
| timestamp | sequência sintética iniciada em 1 de janeiro de 2000 |

Textos longos e campos de mensagens, comentários, pareceres, títulos,
resumos e biografias são substituídos integralmente. Isso prioriza a
privacidade e significa que estas cópias não são byte a byte equivalentes às
entradas usadas nos resultados do artigo.

## Verificação

- mesmas colunas, quantidades de linhas e distribuições de classe dos arquivos
  de entrada;
- nenhum e-mail fora de `example.invalid`;
- nenhum valor original extraído de campos de nome, perfil, credencial, token,
  telefone ou ORCID;
- nenhum valor original dos campos `query` e `searchPhrase`;
- nenhum timestamp ou identificador original de periódico;
- nenhum nome de arquivo, segmento de proprietário, DOI, domínio externo ou
  identificador editorial original nos campos tratados;
- nenhuma ocorrência de `ucs.br`, `/home/arthur` ou marcadores de
  correspondência pessoal;
- todos os valores restantes em chaves sensíveis seguem os marcadores acima;
- gitleaks 8.30.1: zero achados nos dois arquivos.

Os detalhes verificáveis, sem os valores originais, estão em
`verificacao.json`. Para reproduzir:

```bash
python3 datasets/sources/proprio/sanitize_proprio.py
```
