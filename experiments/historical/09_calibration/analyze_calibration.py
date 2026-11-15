#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np,pandas as pd
from src.utils.config import ROOT

rows=[]; curves=[]
for path in (ROOT/'runs/predictions').glob('*.csv'):
    frame=pd.read_csv(path); experiment=frame.experiment_id.iloc[0]
    result_path=ROOT/'results/raw'/f'{experiment}.json'
    if not result_path.exists(): continue
    status_path=ROOT/'runs/status'/f'{experiment}.json'
    if not status_path.exists() or json.loads(status_path.read_text()).get('status')!='COMPLETED': continue
    result=json.loads(result_path.read_text())
    if result.get('status')!='COMPLETED' or result.get('metrics_source',{}).get('brier') is None: continue
    rows.append({"experiment_id":experiment,"target":result['target'],"model":result['model'],"representation":result['representation'],
                 "pilot":result.get('pilot',0),"brier":result['metrics_source']['brier'],"ece_10":result['metrics_source']['ece_10']})
    edges=np.linspace(0,1,11)
    for index,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
        mask=(frame.score>=left)&(frame.score<(right if right<1 else right+1e-12))
        if mask.any(): curves.append({"experiment_id":experiment,"bin":index,"mean_score":frame.loc[mask,'score'].mean(),
                                      "fraction_positive":frame.loc[mask,'true_label'].mean(),"n":int(mask.sum())})
pd.DataFrame(rows).to_csv(ROOT/'results/runs/historical/index/calibration_metrics.csv',index=False)
pd.DataFrame(curves).to_csv(ROOT/'results/raw/reliability_curves.csv',index=False)
print(f'{len(rows)} calibrações')
