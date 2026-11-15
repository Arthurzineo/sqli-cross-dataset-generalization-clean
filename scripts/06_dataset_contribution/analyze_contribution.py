#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import pandas as pd
from src.utils.config import ROOT


values=[]
for path in (ROOT/"results/raw").glob("*.json"):
    row=json.loads(path.read_text())
    if row.get("chapter")=="contribution" and row.get("status")=="COMPLETED": values.append(row)
index={(v["target"],v["model"],v["representation"],v["feature_set"],v["seed"],frozenset(v["train_datasets"])):v for v in values}
rows=[]
for key,base in index.items():
    target,model,representation,feature,seed,coalition=key
    for added in set().union(*(set(k[-1]) for k in index if k[:5]==key[:5]))-set(coalition):
        augmented=index.get(key[:5]+(coalition|{added},))
        if not augmented: continue
        rows.append({"target":target,"model":model,"representation":representation,"feature_set":feature,"seed":seed,
          "base_train":"+".join(sorted(coalition)),"added_dataset":added,"augmented_train":"+".join(sorted(coalition|{added})),
          **{f"delta_{metric}":augmented["metrics_source"].get(metric)-base["metrics_source"].get(metric)
             if augmented["metrics_source"].get(metric) is not None and base["metrics_source"].get(metric) is not None else None
             for metric in ("f1","mcc","pr_auc","recall","fpr")}})
pd.DataFrame(rows).to_csv(ROOT/"results/runs/historical/index/dataset_contribution_deltas.csv",index=False)
print(f"{len(rows)} contribuições marginais pareadas")
