"""Reconstrói o recorte SQLi do ECML/PKDD preservando URL-encoding.

O preparador histórico decodificava antes de salvar, por isso não havia fonte
crua em ``datasets/originais``. Este script repete o mesmo parse, descartes e
amostragens (seed 42), mas grava antes de qualquer ``unquote_plus``.

Uso: python preparar_ecml_codificado.py --xml learning_dataset.xml
"""
import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
DATASETS_PROJETO = RAIZ.parents[1] / "datasets"
sys.path.insert(0, str(DATASETS_PROJETO))

import preparar_ecml as ecml  # noqa: E402


SEED = 42
SHA256_XML = "9c058f33049f16c08449948266b5ce7733c232a64e34b436fdf6f1be076a4ecb"
SAIDA = RAIZ / "datasets" / "originais" / "ecml_balanceado_sqli.csv"


def sha256(caminho):
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", required=True, type=Path)
    parser.add_argument("--forcar", action="store_true")
    parser.add_argument("--ignorar-hash", action="store_true")
    args = parser.parse_args()

    if SAIDA.exists() and not args.forcar:
        print(f"[pula] {SAIDA} já existe (use --forcar para regravar)")
        return
    hash_real = sha256(args.xml)
    if not args.ignorar_hash and hash_real != SHA256_XML:
        raise SystemExit(f"hash inesperado: {hash_real} != {SHA256_XML}")

    df, descartes = ecml.parsear(args.xml, incluir_headers=False)
    df = ecml.balancear(df, balancear_tipos=False)

    sqli = df.attack_type == "sqli"
    benigno = df.attack_type == "legitimate"
    i_sqli = sqli[sqli].index
    i_benigno = pd.Index(
        pd.Series(benigno[benigno].index).sample(
            n=len(i_sqli), random_state=SEED
        ).values
    )
    saida = df.loc[i_sqli.union(i_benigno).sort_values()]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    saida.to_csv(SAIDA, index=False)
    print(f"[ok] {SAIDA}: {len(saida)} linhas "
          f"({int((saida.attack_type == 'sqli').sum())} SQLi + "
          f"{int((saida.attack_type == 'legitimate').sum())} benignas)")
    print(f"descartes herdados: {descartes}")


if __name__ == "__main__":
    main()
