#!/usr/bin/env python3
from collections import defaultdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from src.utils.config import ROOT


def main():
    experiments = []
    for path in (ROOT / "results/raw").glob("*.json"):
        value = json.loads(path.read_text())
        if value.get("chapter") == "contribution": experiments.append(value)
    groups = defaultdict(dict)
    for value in experiments:
        group = (value["target"], value["model"], value["representation"], value["feature_set"], value["seed"])
        groups[group][frozenset(value["train_datasets"])] = value
    rows = []
    for group, coalitions in groups.items():
        players = set().union(*coalitions) if coalitions else set()
        for player in players:
            deltas = defaultdict(list)
            for coalition, result in coalitions.items():
                if player in coalition: continue
                augmented = coalition | {player}
                if augmented not in coalitions: continue
                for metric in ["f1", "mcc", "pr_auc", "recall", "fpr"]:
                    deltas[metric].append(coalitions[augmented]["metrics_source"][metric] - result["metrics_source"][metric])
            rows.append({"target": group[0], "model": group[1], "representation": group[2], "feature_set": group[3],
                         "seed": group[4], "dataset": player, **{f"shapley_{key}": sum(value)/len(value) if value else None for key, value in deltas.items()},
                         "n_marginals": len(deltas.get("f1", []))})
    pd.DataFrame(rows).to_csv(ROOT / "results/runs/historical/index/dataset_shapley.csv", index=False)
    print(f"{len(rows)} valores Shapley")


if __name__ == "__main__": main()

