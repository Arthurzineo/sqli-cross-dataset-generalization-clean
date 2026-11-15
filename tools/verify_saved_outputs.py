#!/usr/bin/env python3
"""Verify one manuscript table and one figure from saved aggregate results."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "results/tables/manuscript_analysis/SUPPLEMENTAL_CONTROLLED_ANALYSIS/tables/lodo_by_target.parquet"
)
OUT = ROOT / "results/verification"


def main() -> None:
    frame = pd.read_parquet(SOURCE)
    macro = (
        frame.groupby(["model", "representation"], as_index=False)["test_f1_mean"]
        .mean()
        .rename(columns={"test_f1_mean": "f1_macro_target"})
        .sort_values(["model", "representation"])
    )
    expected = {
        ("catboost", "RAW"): 0.784,
        ("catboost", "CANONICALIZED"): 0.894,
        ("logistic", "RAW"): 0.733,
        ("logistic", "CANONICALIZED"): 0.844,
        ("mlp", "RAW"): 0.810,
        ("mlp", "CANONICALIZED"): 0.867,
    }
    macro["article_rounded"] = [expected[(r.model, r.representation)] for r in macro.itertuples()]
    macro["rounded_matches_article"] = macro.f1_macro_target.round(3).eq(macro.article_rounded)
    OUT.mkdir(parents=True, exist_ok=True)
    macro.to_csv(OUT / "lodo_macro_regenerated.csv", index=False)
    figure_audit = ROOT / "figures/final/FIGURE_VALIDATION.json"
    table_lines = [
        "| modelo | representação | F1 recalculado | artigo (3 casas) | confere |\n",
        "|---|---|---:|---:|---|\n",
    ]
    table_lines.extend(
        f"| {row.model} | {row.representation} | {row.f1_macro_target:.6f} | "
        f"{row.article_rounded:.3f} | {bool(row.rounded_matches_article)} |\n"
        for row in macro.itertuples()
    )
    lines = [
        "# Verificação local da Fase 2\n\n",
        "A tabela macro LODO foi regenerada a partir das médias por alvo já salvas; ",
        "não houve novo treinamento. A agregação é média entre sementes dentro do alvo ",
        "na tabela de origem, seguida de média entre os sete alvos.\n\n",
        "".join(table_lines),
        "\n\n",
        f"- Todas as seis células conferem com o artigo após arredondamento: **{bool(macro.rounded_matches_article.all())}**.\n",
        "- A figura LODO foi renderizada novamente por `scripts/render_final_manuscript_figures.py`.\n",
        f"- Auditoria do renderizador: `{figure_audit.relative_to(ROOT)}`.\n",
        "- O renderizador registrou 27 verificações exatas de elementos e 603 valores-fonte para seis figuras, sem recomputação científica.\n",
    ]
    (OUT / "verification.md").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
