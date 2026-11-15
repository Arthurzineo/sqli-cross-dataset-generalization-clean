#!/usr/bin/env python
# Pipeline do experimento "SQLi melhorado": extrai features do dataset
# artificial com SQLi regenerado e o combina com o dataset grande, produzindo
# os arquivos de treino para o re-teste.
#
# Replica EXATAMENTE a receita da Fusao balanceada campea (artificial NAO
# decodificado, combinado com o grande), trocando apenas os features do
# artificial - assim o experimento isola o efeito das novas tecnicas de SQLi.
#
# Saidas:
#   artificial_features_lexicas_sqli_melhorado.csv
#   artificial_features_codebert_sqli_melhorado.csv
#   dataset_features_lexicas_combinado_sqli_melhorado.csv
#   dataset_features_codebert_combinado_sqli_melhorado.csv

import pandas as pd

import extrair_features_artificial as ext

TSV = "dataset_artificial_ia_sqli_melhorado.tsv"
ART_LEX = "artificial_features_lexicas_sqli_melhorado.csv"
ART_BERT = "artificial_features_codebert_sqli_melhorado.csv"
GRANDE_LEX = "dataset_features_lexicas.csv"
GRANDE_BERT = "dataset_features_codebert.csv"
COMB_LEX = "dataset_features_lexicas_combinado_sqli_melhorado.csv"
COMB_BERT = "dataset_features_codebert_combinado_sqli_melhorado.csv"
COLS_ROTULO = ["malicioso", "xss", "sqli"]


def combinar(grande, artificial, saida):
    g = pd.read_csv(grande); a = pd.read_csv(artificial)
    assert list(g.columns) == list(a.columns), f"schema incompativel: {saida}"
    c = pd.concat([g, a], ignore_index=True)
    c.to_csv(saida, index=False)
    print(f"[ok] {saida}: {len(c)} linhas ({len(g)}+{len(a)}), {c.shape[1]} colunas")


def main():
    print(f"Lendo {TSV}...")
    df = pd.read_csv(TSV, sep="\t", encoding="latin-1")
    rotulos = df[COLS_ROTULO].reset_index(drop=True)

    print("Extraindo features lexicas...")
    lex = ext.extrair_lexicas(df).reset_index(drop=True)
    pd.concat([rotulos, lex], axis=1).to_csv(ART_LEX, index=False)
    print(f"[ok] {ART_LEX}: {len(df)} linhas, {lex.shape[1]} features")

    print("Extraindo embeddings CodeBERT...")
    bert = ext.extrair_codebert(df).reset_index(drop=True)
    pd.concat([rotulos, bert], axis=1).to_csv(ART_BERT, index=False)
    print(f"[ok] {ART_BERT}: {len(df)} linhas, {bert.shape[1]} dimensoes")

    print("\nCombinando com o dataset grande...")
    combinar(GRANDE_LEX, ART_LEX, COMB_LEX)
    combinar(GRANDE_BERT, ART_BERT, COMB_BERT)


if __name__ == "__main__":
    main()
