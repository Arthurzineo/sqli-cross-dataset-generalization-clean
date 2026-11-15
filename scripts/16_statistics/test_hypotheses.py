#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from src.utils.config import ROOT


rows=[]
threshold=ROOT/"results/runs/historical/index/threshold_transfer.csv"
if threshold.exists():
    data=pd.read_csv(threshold)
    if "pilot" in data: data=data[data.pilot.fillna(0).astype(int)==0]
    if len(data)>2:
        statistic,p=spearmanr(data.threshold_drift,data.f1_source,nan_policy="omit")
        rows.append({"hypothesis":"H3_threshold_drift_vs_f1","x":"threshold_drift","y":"f1_source","n":len(data),"spearman":statistic,"p_value":p})
distance=ROOT/"results/runs/historical/index/lexical_domain_distances.csv";master=ROOT/"results/runs/historical/index/all_experiments.csv"
if distance.exists() and master.exists():
    drift=pd.read_csv(distance).groupby(["representation","dataset_a","dataset_b"]).jensen_shannon.mean().reset_index()
    experiments=pd.read_csv(master)
    if "pilot" in experiments: experiments=experiments[experiments.pilot.fillna(0).astype(int)==0]
    pair=experiments[experiments.chapter=="pairwise"].copy()
    # Source é recuperável apenas de pools unitários.
    pair["dataset_a"]=pair.train_datasets.astype(str);pair["dataset_b"]=pair.target
    joined=pair.merge(drift,on=["representation","dataset_a","dataset_b"])
    if len(joined)>2:
        statistic,p=spearmanr(joined.jensen_shannon,joined.metrics_source_f1,nan_policy="omit")
        rows.append({"hypothesis":"H1_lexical_distance_vs_ood_f1","x":"mean_js","y":"f1","n":len(joined),"spearman":statistic,"p_value":p})
pd.DataFrame(rows,columns=["hypothesis","x","y","n","spearman","p_value"]).to_csv(ROOT/"results/statistics/hypothesis_tests.csv",index=False)
print(f"{len(rows)} hipóteses testáveis com os resultados disponíveis; demais permanecem pendentes")
