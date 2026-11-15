#!/usr/bin/env python
# Decodifica o URL-encoding do dataset artificial na FONTE e regera as suas
# features (lexicas + CodeBERT), na mesma convencao ja aplicada ao CSIC por
# decodificar_csic.py.
#
# MOTIVO: enc_pct e a unica feature calculada sobre o texto CRU, e ela estava
# significando coisas diferentes em cada corpus:
#     dataset grande : 9,98% dos benignos com %XX /  0,00% dos ataques -> indica BENIGNO
#     artificial     : 11,58% dos benignos        / 80,40% dos ataques -> indica MALICIOSO
#     CSIC original  : 41,99% dos benignos        /  100% dos ataques  -> indica MALICIOSO
# O artificial herdou a convencao do CSIC (o gerador aplica quote_plus nos
# payloads), nao a do dataset grande. Decodificando-o, enc_pct zera nos dois
# lados e deixa de carregar informacao de metodo de captura.
#
# A extracao e copia fiel de extrair_features_artificial.py, para o schema
# sair identico ao artificial_features_*.csv e continuar concatenavel com o
# dataset grande.
#
# Uso:
#     python decodificar_artificial.py              # fonte + features lexicas
#     python decodificar_artificial.py --codebert   # tambem regera os embeddings

import argparse
import math
import re
from urllib.parse import urlparse, unquote_plus

import numpy as np
import pandas as pd

ENTRADA = "dataset_artificial_ia.tsv"
SAIDA_FONTE = "dataset_artificial_ia_decodificado.tsv"
SAIDA_LEXICO = "artificial_features_lexicas_decodificado.csv"
SAIDA_CODEBERT = "artificial_features_codebert_decodificado.csv"

COLS_TEXTO = ["url", "body"]
COLS_ROTULO = ["malicioso", "xss", "sqli"]

# Decodifica ate estabilizar (nao um numero fixo de passadas): o gerador
# aplicou enc() sobre payloads que ja eram literais pre-codificados, entao
# 67 linhas tem 3 camadas de encoding e as duas passadas de montar_texto nao
# dariam conta. Distribuicao medida: 4595 linhas com 0 camadas, 4360 com 1,
# 978 com 2 e 67 com 3.
PASSADAS_MAX = 10

CODEBERT_MODEL = "microsoft/codebert-base"
CODEBERT_MAX_LEN = 256
CODEBERT_BATCH = 32


def decodificar(valor, passadas_max=PASSADAS_MAX):
    """Aplica unquote_plus repetidamente ate o texto parar de mudar, e
    neutraliza tab/quebra de linha, que quebrariam o formato TSV se
    aparecessem via %09 / %0A."""
    if pd.isna(valor):
        return valor
    texto = str(valor)
    for _ in range(passadas_max):
        novo = unquote_plus(texto)
        if novo == texto:
            break
        texto = novo
    return texto.replace("\t", " ").replace("\r", " ").replace("\n", " ")


# --------------------------------------------------------------------------- #
# Extracao - copia fiel de extrair_features_artificial.py
# --------------------------------------------------------------------------- #
def montar_texto(url, body):
    url = "" if pd.isna(url) else str(url)
    body = "" if pd.isna(body) or str(body) == "-" else str(body)
    texto = (url + " " + body).strip()
    return unquote_plus(unquote_plus(texto))


def entropia(s):
    if not s:
        return 0.0
    n = len(s)
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


CARACTERES = {
    "sq": "'", "dq": '"', "lt": "<", "gt": ">", "lparen": "(", "rparen": ")",
    "semicolon": ";", "equals": "=", "amp": "&", "pct": "%", "plus": "+",
    "minus": "-", "star": "*", "slash": "/", "pipe": "|", "hash": "#",
    "quest": "?", "at": "@", "colon": ":", "comma": ",", "dot": ".", "space": " ",
}
PALAVRAS_SQL = [
    "select", "union", "insert", "update", "delete", "drop", "where", "from",
    "or", "and", "exec", "order", "by", "waitfor", "delay", "cast", "table",
    "database", "like",
]
PALAVRAS_XSS = [
    "script", "alert", "javascript", "onerror", "onload", "document", "cookie",
    "src", "iframe", "style", "background", "location", "eval", "prompt",
]


def extrair_lexicas(df):
    texto = [montar_texto(u, b) for u, b in zip(df["url"], df["body"])]
    texto = pd.Series(texto).str.lower()

    f = pd.DataFrame()
    for nome, ch in CARACTERES.items():
        f["char_" + nome] = texto.str.count(re.escape(ch))
    for kw in PALAVRAS_SQL:
        f["sql_" + kw] = texto.str.count(rf"\b{kw}\b")
    f["sql_comment_dash"] = texto.str.count(r"--")
    f["sql_comment_block"] = texto.str.count(r"/\*") + texto.str.count(r"\*/")
    for kw in PALAVRAS_XSS:
        f["xss_" + kw] = texto.str.count(rf"\b{kw}\b")

    f["len_total"] = texto.str.len()
    f["path_depth"] = df["url"].fillna("").map(lambda u: urlparse(str(u)).path.count("/"))
    L = f["len_total"].replace(0, 1)
    f["ratio_digits"] = texto.str.count(r"\d") / L
    f["ratio_nonalnum"] = texto.str.count(r"[^a-z0-9]") / L

    texto_raw = (df["url"].fillna("").astype(str) + " " +
                 df["body"].fillna("").astype(str))
    f["enc_pct"] = texto_raw.str.count(r"%[0-9a-fA-F]{2}")
    f["path_traversal"] = texto.str.count(r"\.\./")
    f["entropy"] = texto.map(entropia)
    return f


def extrair_codebert(df):
    import torch
    from transformers import AutoTokenizer, AutoModel

    textos = [montar_texto(u, b) for u, b in zip(df["url"], df["body"])]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  CodeBERT rodando em: {device}")
    tokenizer = AutoTokenizer.from_pretrained(CODEBERT_MODEL)
    modelo = AutoModel.from_pretrained(CODEBERT_MODEL).to(device).eval()

    saidas = []
    with torch.no_grad():
        for i in range(0, len(textos), CODEBERT_BATCH):
            lote = textos[i:i + CODEBERT_BATCH]
            enc = tokenizer(lote, padding=True, truncation=True,
                            max_length=CODEBERT_MAX_LEN, return_tensors="pt").to(device)
            cls = modelo(**enc).last_hidden_state[:, 0, :]
            saidas.append(cls.cpu().numpy())

    emb = np.vstack(saidas).astype(np.float32)
    return pd.DataFrame(emb, columns=[f"emb_{j}" for j in range(emb.shape[1])])


# --------------------------------------------------------------------------- #
def relatorio(df_antes, df_depois, lex_antes, lex_depois):
    print("\n" + "=" * 66)
    print("# Relatorio: efeito da decodificacao")
    print("=" * 66)

    def pct(df):
        cru = (df["url"].fillna("").astype(str) + " " +
               df["body"].fillna("").astype(str))
        tem = cru.str.contains(r"%[0-9a-fA-F]{2}", regex=True)
        y = df["malicioso"].astype(int)
        return tem[y == 0].mean() * 100, tem[y == 1].mean() * 100

    ba, ma = pct(df_antes)
    bd, md = pct(df_depois)
    print("\nlinhas com %XX no texto cru:")
    print(f"  {'':10s} {'antes':>12s} {'depois':>12s}")
    print(f"  {'benigno':10s} {ba:11.2f}% {bd:11.2f}%")
    print(f"  {'malicioso':10s} {ma:11.2f}% {md:11.2f}%")

    print("\nfeatures lexicas que mudaram (media por classe):")
    y = df_antes["malicioso"].astype(int).values
    mudou = False
    for col in lex_depois.columns:
        if col not in lex_antes.columns or lex_antes[col].equals(lex_depois[col]):
            continue
        mudou = True
        for v, nome in [(0, "benigno"), (1, "malicioso")]:
            a = lex_antes.loc[y == v, col].mean()
            d = lex_depois.loc[y == v, col].mean()
            print(f"  {col:16s} {nome:10s} {a:10.4f} -> {d:10.4f}  ({d - a:+.4f})")
    if not mudou:
        print("  (nenhuma)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--codebert", action="store_true",
                    help="tambem regera os embeddings CodeBERT (lento)")
    ap.add_argument("--entrada", default=ENTRADA)
    args = ap.parse_args()

    print(f"Lendo {args.entrada}...")
    df = pd.read_csv(args.entrada, sep="\t", encoding="latin-1")
    print(f"  {len(df)} linhas, colunas: {list(df.columns)}")

    df_dec = df.copy()
    for col in COLS_TEXTO:
        if col not in df_dec.columns:
            raise SystemExit(f"coluna esperada ausente: {col}")
        df_dec[col] = df_dec[col].map(decodificar)

    alteradas = sum((df[c].fillna("") != df_dec[c].fillna("")).sum() for c in COLS_TEXTO)
    print(f"  campos alterados pela decodificacao: {alteradas}")

    df_dec.to_csv(SAIDA_FONTE, sep="\t", index=False, encoding="utf-8")
    print(f"[ok] {SAIDA_FONTE}: fonte decodificada")

    print("\nExtraindo features lexicas...")
    lex_antes = extrair_lexicas(df)
    lex_depois = extrair_lexicas(df_dec)
    rotulos = df_dec[COLS_ROTULO].reset_index(drop=True)
    saida_lex = pd.concat([rotulos, lex_depois.reset_index(drop=True)], axis=1)
    saida_lex.to_csv(SAIDA_LEXICO, index=False)
    print(f"[ok] {SAIDA_LEXICO}: {saida_lex.shape[0]} linhas, "
          f"{lex_depois.shape[1]} features lexicas")

    if args.codebert:
        print("\nExtraindo embeddings CodeBERT...")
        emb = extrair_codebert(df_dec)
        saida_bert = pd.concat([rotulos, emb.reset_index(drop=True)], axis=1)
        saida_bert.to_csv(SAIDA_CODEBERT, index=False)
        print(f"[ok] {SAIDA_CODEBERT}: {saida_bert.shape[0]} linhas, "
              f"{emb.shape[1]} dimensoes")

    relatorio(df, df_dec, lex_antes, lex_depois)


if __name__ == "__main__":
    main()
