#!/usr/bin/env python
# Decodifica o URL-encoding do dataset CSIC na FONTE, para deixa-lo na mesma
# convencao do dataset grande (DATASET_METODO_BALANCEADO.tsv), cujos ataques
# foram capturados/salvos ja decodificados.
#
# MOTIVO: a feature enc_pct e a unica calculada sobre o texto CRU (todas as
# outras usam montar_texto, que ja aplica unquote_plus duas vezes). Como o
# dataset grande foi salvo decodificado e o CSIC nao, enc_pct virou um sinal
# invertido entre os dois:
#     dataset grande : 0,00% dos ataques com %XX   / 9,98% dos benignos com %XX
#     CSIC           :  100% dos ataques com %XX   / 41,99% dos benignos com %XX
# Isto e, "tem encoding" indicava BENIGNO no treino e MALICIOSO na validacao -
# artefato de captura, nao sinal de ataque, e um suspeito direto pela queda de
# desempenho no cenario cross-dataset.
#
# O QUE O SCRIPT FAZ: aplica unquote_plus duas vezes (exatamente o numero de
# passadas que montar_texto usa em pipe_cisc.py / main.py) nas colunas URL e
# content, e regrava a fonte + as features lexicas. Como a decodificacao ja
# acontecia dentro da extracao, o texto lexico final nao muda; o que muda e
# enc_pct (e char_pct, que conta '%' no texto). Os embeddings CodeBERT tambem
# usam montar_texto, entao sao praticamente identicos - por isso a regeracao
# deles fica atras da flag --codebert (custa rodar o modelo).
#
# Uso:
#     python decodificar_csic.py              # fonte + features lexicas
#     python decodificar_csic.py --codebert   # tambem regera os embeddings

import argparse
import math
import re
from urllib.parse import urlparse, unquote_plus

import numpy as np
import pandas as pd

ENTRADA = "csic_sqli_xss_balanceado.csv"
SAIDA_FONTE = "csic_sqli_xss_balanceado_decodificado.csv"
SAIDA_LEXICO = "csic_dataset_lexicas_decodificado.csv"
SAIDA_CODEBERT = "csic_dataset_codebert_decodificado.csv"

COLS_TEXTO = ["URL", "content"]
COLS_ROTULO = ["classification", "attack_type"]

# Decodifica ate estabilizar (mesma regra de decodificar_artificial.py).
# No CSIC duas passadas ja bastam, mas o criterio correto e "nada codificado",
# nao um numero fixo de passadas.
PASSADAS_MAX = 10

CODEBERT_MODEL = "microsoft/codebert-base"
CODEBERT_MAX_LEN = 256
CODEBERT_BATCH = 32


# --------------------------------------------------------------------------- #
# Decodificacao
# --------------------------------------------------------------------------- #
def decodificar(valor, passadas_max=PASSADAS_MAX):
    """Aplica unquote_plus ate o texto parar de mudar. Preserva NaN."""
    if pd.isna(valor):
        return valor
    texto = str(valor)
    for _ in range(passadas_max):
        novo = unquote_plus(texto)
        if novo == texto:
            break
        texto = novo
    return texto


# --------------------------------------------------------------------------- #
# Extracao lexica - copia fiel da logica de pipe_cisc.py, para o schema sair
# identico ao csic_dataset_lexicas.csv original
# --------------------------------------------------------------------------- #
def limpar_url(url):
    """Remove o sufixo ' HTTP/1.x' e o prefixo http://host, deixando apenas o
    caminho + query + fragmento.

    CORRECAO: a versao anterior devolvia so path + query, descartando o
    FRAGMENTO (tudo apos '#'). Isso truncava payloads de ataque, porque
    entidades HTML numericas contem '#' - em '&#058;alert(...)' o urlparse
    trata '058;alert(...)' como fragmento e jogava fora o resto do payload.
    No CSIC o efeito era nulo (0% das URLs tem '#'), mas no ECML/PKDD atingia
    2,2% dos ataques. O main.py (corpus de treino) nunca teve o problema
    porque nao chama esta funcao - usa a URL crua."""
    if pd.isna(url):
        return ""
    u = str(url)
    u = re.sub(r"\s+HTTP/1\.[01]\s*$", "", u)
    p = urlparse(u)
    return (p.path
            + (("?" + p.query) if p.query else "")
            + (("#" + p.fragment) if p.fragment else ""))


def montar_texto(url_limpa, body):
    body = "" if pd.isna(body) or str(body) == "nan" else str(body)
    texto = (str(url_limpa) + " " + body).strip()
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


def extrair_lexicas(url_limpa, body):
    texto = pd.Series([montar_texto(u, b) for u, b in zip(url_limpa, body)]).str.lower()

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
    f["path_depth"] = pd.Series(list(url_limpa)).map(lambda u: str(u).count("/"))
    L = f["len_total"].replace(0, 1)
    f["ratio_digits"] = texto.str.count(r"\d") / L
    f["ratio_nonalnum"] = texto.str.count(r"[^a-z0-9]") / L
    f["enc_pct"] = pd.Series([str(u) + " " + ("" if pd.isna(b) else str(b))
                              for u, b in zip(url_limpa, body)]).str.count(r"%[0-9a-fA-F]{2}")
    f["path_traversal"] = texto.str.count(r"\.\./")
    f["entropy"] = texto.map(entropia)
    return f


def extrair_codebert(url_limpa, body):
    import torch
    from transformers import AutoTokenizer, AutoModel

    textos = [montar_texto(u, b) for u, b in zip(url_limpa, body)]
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
# Relatorio antes/depois
# --------------------------------------------------------------------------- #
def pct_com_encoding(df):
    """% de linhas com pelo menos um %XX no texto cru, por classe."""
    cru = (df["URL"].fillna("").astype(str) + " " +
           df["content"].fillna("").astype(str))
    tem = cru.str.contains(r"%[0-9a-fA-F]{2}", regex=True)
    y = df["classification"].astype(int)
    return (tem[y == 0].mean() * 100, tem[y == 1].mean() * 100)


def relatorio(df_antes, df_depois, lex_antes, lex_depois):
    print("\n" + "=" * 66)
    print("# Relatorio: efeito da decodificacao")
    print("=" * 66)

    ba, ma = pct_com_encoding(df_antes)
    bd, md = pct_com_encoding(df_depois)
    print("\nlinhas com %XX no texto cru:")
    print(f"  {'':10s} {'antes':>12s} {'depois':>12s}")
    print(f"  {'benigno':10s} {ba:11.2f}% {bd:11.2f}%")
    print(f"  {'malicioso':10s} {ma:11.2f}% {md:11.2f}%")

    if lex_antes is None:
        return

    print("\nfeatures lexicas que mudaram (media por classe):")
    y = df_antes["classification"].astype(int).values
    mudou = False
    for col in lex_depois.columns:
        if col not in lex_antes.columns:
            continue
        if lex_antes[col].equals(lex_depois[col]):
            continue
        mudou = True
        for v, nome in [(0, "benigno"), (1, "malicioso")]:
            a = lex_antes.loc[y == v, col].mean()
            d = lex_depois.loc[y == v, col].mean()
            print(f"  {col:16s} {nome:10s} {a:10.4f} -> {d:10.4f}  ({d - a:+.4f})")
    if not mudou:
        print("  (nenhuma)")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--codebert", action="store_true",
                    help="tambem regera os embeddings CodeBERT (lento)")
    ap.add_argument("--entrada", default=ENTRADA)
    args = ap.parse_args()

    print(f"Lendo {args.entrada}...")
    df = pd.read_csv(args.entrada)
    print(f"  {len(df)} linhas, colunas: {list(df.columns)}")

    df_dec = df.copy()
    for col in COLS_TEXTO:
        if col not in df_dec.columns:
            raise SystemExit(f"coluna esperada ausente: {col}")
        df_dec[col] = df_dec[col].map(decodificar)

    alteradas = sum((df[c].fillna("") != df_dec[c].fillna("")).sum() for c in COLS_TEXTO)
    print(f"  campos alterados pela decodificacao: {alteradas}")

    df_dec.to_csv(SAIDA_FONTE, index=False)
    print(f"[ok] {SAIDA_FONTE}: fonte decodificada")

    # features lexicas, antes e depois (o 'antes' e so para o relatorio)
    print("\nExtraindo features lexicas...")
    url_antes = df["URL"].map(limpar_url)
    url_depois = df_dec["URL"].map(limpar_url)
    lex_antes = extrair_lexicas(url_antes, df["content"])
    lex_depois = extrair_lexicas(url_depois, df_dec["content"])

    saida_lex = pd.concat([df_dec[COLS_ROTULO].reset_index(drop=True),
                           lex_depois.reset_index(drop=True)], axis=1)
    saida_lex.to_csv(SAIDA_LEXICO, index=False)
    print(f"[ok] {SAIDA_LEXICO}: {saida_lex.shape[0]} linhas, "
          f"{lex_depois.shape[1]} features lexicas")

    if args.codebert:
        print("\nExtraindo embeddings CodeBERT...")
        emb = extrair_codebert(url_depois, df_dec["content"])
        saida_bert = pd.concat([df_dec[COLS_ROTULO].reset_index(drop=True),
                                emb.reset_index(drop=True)], axis=1)
        saida_bert.to_csv(SAIDA_CODEBERT, index=False)
        print(f"[ok] {SAIDA_CODEBERT}: {saida_bert.shape[0]} linhas, "
              f"{emb.shape[1]} dimensoes")

    relatorio(df, df_dec, lex_antes, lex_depois)


if __name__ == "__main__":
    main()
