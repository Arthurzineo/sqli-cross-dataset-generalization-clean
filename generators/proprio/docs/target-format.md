# Formato de alvos e de escopo

## targets.txt

**Uma URL por linha. Nada mais.**

```
http://app.lab.local/login.php?user=test
http://app.lab.local/vulnerabilities/sqli/?id=1&Submit=Submit
http://api.lab.local/v1/users?id=1
```

Regras:

- Linhas vazias e comentários (`#`) são ignorados.
- Toda URL deve usar `http`/`https`, ter host e não conter fragmento `#`.
- Toda URL é validada contra `config/scope.txt`.

### GET e POST automáticos

Para cada URL, o script gera duas variantes automaticamente:

| Variante | O que faz |
|----------|-----------|
| **GET**  | Testa a URL como está (parâmetros na query string). |
| **POST** | Reaproveita os parâmetros da query como corpo `application/x-www-form-urlencoded`, testando a mesma URL base via POST. |

Se a URL **não tiver parâmetros** (`?...`), a variante POST é pulada — não há
parâmetro para injetar — e isso fica registrado no ledger da execução.

## scope.txt

Uma entrada por linha:

```
app.lab.local
api.lab.local:8443
10.10.20.15
10.10.30.0/24
*.sqli.lab.local
```

Aceita host exato, host:porta, IPv4, CIDR IPv4 e wildcard de subdomínio
intencional. **Rejeita** curingas amplos: `*`, `*.com`, `0.0.0.0/0`, TLDs
inteiros e URLs com caminho. Hostnames são normalizados para minúsculas.
