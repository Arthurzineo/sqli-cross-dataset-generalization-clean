#!/usr/bin/env python
# Regera APENAS a porcao SQLi do dataset artificial, corrigindo o vies de
# tecnica do gerador original. Benignas e XSS sao copiadas byte a byte do
# dataset_artificial_ia.tsv, para que qualquer diferenca de resultado seja
# atribuivel so a mudanca no SQLi (teste de variavel unica).
#
# MOTIVO (medido sobre o CSIC decodificado x artificial original):
#
#   tecnica            CSIC (real)   artificial (gerado)
#   WAITFOR/DELAY          52,5%            5,0%
#   stacked queries        62,2%           15,1%
#   tautologia OR           0,1%           41,1%
#   UNION                   0,0%           10,2%
#   SLEEP/pg_sleep          0,0%           10,2%
#
# O gerador gastava 41% das amostras em ' OR '1'='1, padrao que praticamente
# nao existe no trafego real, e quase nao produzia as duas tecnicas que
# dominam. Resultado: a Fusao Combinada Balanceada erra 249 de 2104 SQLi
# (11,8%) enquanto erra 1 de 1504 XSS (0,07%).
#
# ESTRUTURA (inspirada em geradores conhecidos):
#   - sistema de BOUNDARIES prefixo/sufixo, como o boundaries.xml do sqlmap:
#     o payload e montado como <prefixo><corpo><sufixo>, cobrindo contexto de
#     string ('), string dupla ("), numerico (sem aspa) e parenteses.
#   - CATEGORIAS de tecnica com peso, como a organizacao do
#     PayloadsAllTheThings: time-based, stacked, boolean-blind, error-based,
#     union, tautologia.
#   - MUTACOES de evasao (espaco -> /**/ ou +, case aleatorio, comentario
#     inline), em vez de strings literais fixas.
#   - variedade de DBMS: MSSQL, MySQL, PostgreSQL, Oracle.
#
# NAO incluido de proposito (fica para a proxima iteracao, para nao misturar
# variaveis): payloads de "injecao minima" (aspa solta) e hard negatives
# benignos com aspa.
#
# Uso:  python gerar_sqli_melhorado.py

import random
import string

import gerar_dataset_artificial as g   # reusa dominios, contextos e helpers

SEED = 20260823
random.seed(SEED)

ENTRADA = "dataset_artificial_ia.tsv"
SAIDA = "dataset_artificial_ia_v2.tsv"

N_SQLI = 2500
PROB_URL_ENCODE = 0.15    # mesma taxa do gerador original
PROB_MUTACAO = 0.35       # chance de aplicar evasao ao corpo do payload


# --------------------------------------------------------------------------- #
# Boundaries: contexto de injecao (prefixo) e fechamento (sufixo).
# Espelha a ideia do boundaries.xml do sqlmap: o mesmo corpo de payload
# precisa de delimitadores diferentes conforme onde ele cai na query.
# --------------------------------------------------------------------------- #
PREFIXOS = [
    ("'", 34),      # string simples - o caso mais comum
    ("", 22),       # contexto numerico, sem aspa
    ("')", 12),
    ('"', 9),
    ("'))", 6),
    ('")', 5),
    ("1'", 5),
    ("%27", 4),     # ja encodado na origem
    ("`", 3),
]

SUFIXOS = [
    ("-- -", 30),   # comentario de linha (com espaco, forma segura)
    (";--", 18),
    ("--", 14),
    ("#", 10),
    ("", 14),       # sem fechamento
    ("/*", 8),
    ("%00", 3),
    ("AND '1'='1", 3),
]


def _sortear(pares):
    itens = [i for i, _ in pares]
    pesos = [p for _, p in pares]
    return random.choices(itens, weights=pesos, k=1)[0]


# --------------------------------------------------------------------------- #
# Corpos de payload por categoria
# --------------------------------------------------------------------------- #
TABELAS = ["usuarios", "clientes", "pedidos", "produtos", "admin", "contas", "logins"]
COLUNAS = ["usuario", "senha", "email", "nome", "id", "token", "cpf"]


def corpo_time_based():
    """Blind baseado em tempo - a t
