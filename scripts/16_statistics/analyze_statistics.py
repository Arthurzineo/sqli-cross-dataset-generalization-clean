#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from src.utils.config import ROOT,experiment_config


def load_results():
    rows=[]
    for path in (ROOT/"results/raw").glob("*.json"):
        value=json.loads(path.read_text())
        status=ROOT/"runs/status"/f"{value.get('experiment_id')}.json"
        if not status.exists() or json.loads(status.read_text()).get("status")!="COMPLETED": continue
        if value.get("status")!="COMPLETED" or "metrics_source" not in value: continue
        base={key:value.get(key) for key in ("experiment_id","chapter","mode","target","model","representation","feature_set","seed","pilot","train_n","test_n")}
        rows.append(base|value["metrics_source"])
    return pd.DataFrame(rows)


def bootstrap(values,iterations,seed=42):
    values=np.asarray(values,dtype=float); values=values[np.isfinite(values)]
    if not len(values): return np.nan,np.nan,np.nan
    rng=np.random.default_rng(seed); means=np.asarray([rng.choice(values,len(values),replace=True).mean() for _ in range(iterations)])
    return values.mean(),*np.quantile(means,[.025,.975])


frame=load_results()
if frame.empty: raise SystemExit("Nenhum resultado bruto completo.")
smoke=frame[frame.pilot.fillna(0).astype(int)>0] if "pilot" in frame else pd.DataFrame()
smoke.to_csv(ROOT/"results/statistics/smoke_experiments.csv",index=False)
frame=frame[frame.pilot.fillna(0).astype(int)==0] if "pilot" in frame else frame
if frame.empty:
    pd.DataFrame(columns=["chapter","model","representation","feature_set","metric","mean","ci95_low","ci95_high","n"]).to_csv(
        ROOT/"results/statistics/bootstrap_ci.csv",index=False)
    pd.DataFrame(columns=["left","right","metric","n_pairs","statistic","p_value","mean_delta","p_holm"]).to_csv(
        ROOT/"results/statistics/paired_tests_holm.csv",index=False)
    print("Somente pilotos disponíveis; estatísticas finais ficaram vazias e os pilotos foram separados.")
    raise SystemExit(0)
iterations=experiment_config()["bootstrap_iterations"]; ci=[]
group_cols=["chapter","model","representation","feature_set"]
for keys,group in frame.groupby(group_cols,dropna=False):
    for metric in ("f1","mcc","pr_auc","recall","fpr"):
        mean,low,high=bootstrap(group[metric],iterations)
        ci.append(dict(zip(group_cols,keys))|{"metric":metric,"mean":mean,"ci95_low":low,"ci95_high":high,"n":group[metric].notna().sum()})
pd.DataFrame(ci).to_csv(ROOT/"results/statistics/bootstrap_ci.csv",index=False)

# Comparações pareadas apenas em exatamente o mesmo alvo/modelo/feature/seed.
tests=[]; levels=sorted(frame.representation.dropna().unique())
for i,left in enumerate(levels):
 for right in levels[i+1:]:
  a=frame[frame.representation==left]; b=frame[frame.representation==right]
  keys=["chapter","target","model","feature_set","seed"]
  paired=a.merge(b,on=keys,suffixes=("_left","_right"))
  for metric in ("f1","mcc","pr_auc"):
   valid=paired[[f"{metric}_left",f"{metric}_right"]].dropna()
   if len(valid)<2 or np.allclose(valid.iloc[:,0],valid.iloc[:,1]): statistic,pvalue=np.nan,1.0
   else: statistic,pvalue=wilcoxon(valid.iloc[:,0],valid.iloc[:,1])
   tests.append({"left":left,"right":right,"metric":metric,"n_pairs":len(valid),"statistic":statistic,"p_value":pvalue,
                 "mean_delta":float((valid.iloc[:,0]-valid.iloc[:,1]).mean()) if len(valid) else np.nan})
columns=["left","right","metric","n_pairs","statistic","p_value","mean_delta"]
tests=pd.DataFrame(tests,columns=columns)
if not tests.empty:
    tests=tests.sort_values("p_value"); m=len(tests)
    tests["p_holm"]=np.maximum.accumulate(np.minimum(1,tests.p_value.to_numpy()*(m-np.arange(m))))
else:
    tests["p_holm"]=pd.Series(dtype=float)
tests.to_csv(ROOT/"results/statistics/paired_tests_holm.csv",index=False)
print(f"{len(ci)} intervalos e {len(tests)} testes pareados")
