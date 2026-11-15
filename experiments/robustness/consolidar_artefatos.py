#!/usr/bin/env python3
"""Consolida manifestos de execução e tempos sem tocar nas entradas do projeto."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CONTROL = ROOT / "artigo" / "complementos_generalizacao_v1" / "full"


def main() -> None:
    master = pd.read_parquet(CONTROL / "analysis" / "master_results.parquet")
    split_map = (master[master.kind == "lodo"]
                 [["target", "seed", "split_id"]]
                 .drop_duplicates(["target", "seed"]))

    specs = [
        ("3.1", HERE / "3_1_tamanho_controlado" / "resultados_por_semente.csv", "kind"),
        ("3.2a", HERE / "3_2_srbh_sem_filtros" / "como_alvo" / "resultados_por_semente.csv", "variant"),
        ("3.2b", HERE / "3_2_srbh_sem_filtros" / "como_fonte" / "resultados_por_semente.csv", "variant"),
        ("3.3", HERE / "3_3_sensibilidade_hiperparametros" / "resultados_por_semente.csv", "config_id"),
    ]
    frames = []
    for analysis, path, condition_column in specs:
        frame = pd.read_csv(path)
        frame.insert(0, "analysis_group", analysis)
        if condition_column in frame:
            frame["condition"] = frame[condition_column]
        if "removed_source" in frame:
            mask = frame.removed_source.notna()
            frame.loc[mask, "condition"] = "removed:" + frame.loc[mask, "removed_source"].astype(str)
        keep = [column for column in [
            "analysis_group", "target", "seed", "model", "representation", "condition",
            "train_n", "validation_n", "test_n", "selected_iterations", "wall_seconds",
        ] if column in frame]
        frames.append(frame[keep])
    manifest = pd.concat(frames, ignore_index=True, sort=False)
    manifest = manifest.merge(split_map, on=["target", "seed"], how="left", validate="many_to_one")
    manifest.to_csv(HERE / "manifesto_execucoes.csv", index=False)

    time_specs = [
        ("3.1", HERE / "3_1_tamanho_controlado" / "tempo_parede.json"),
        ("3.2_preparacao", HERE / "3_2_srbh_sem_filtros" / "variant" / "READY.json"),
        ("3.2_como_alvo", HERE / "3_2_srbh_sem_filtros" / "como_alvo" / "tempo_parede.json"),
        ("3.2_como_fonte", HERE / "3_2_srbh_sem_filtros" / "como_fonte" / "tempo_parede.json"),
        ("3.3", HERE / "3_3_sensibilidade_hiperparametros" / "tempo_parede.json"),
        ("extra_esqueletos", HERE / "extra_esqueletos" / "tempo_parede.json"),
    ]
    times = []
    for analysis, path in time_specs:
        data = json.loads(path.read_text())
        times.append({"analysis": analysis, "wall_seconds": data["wall_seconds"],
                      "wall_minutes": data["wall_seconds"] / 60})
    table = pd.DataFrame(times)
    total_32 = table[table.analysis.str.startswith("3.2")].wall_seconds.sum()
    table = pd.concat([table, pd.DataFrame([{
        "analysis": "3.2_total", "wall_seconds": total_32, "wall_minutes": total_32 / 60,
    }])], ignore_index=True)
    table.to_csv(HERE / "tempos_parede.csv", index=False)


if __name__ == "__main__":
    main()
