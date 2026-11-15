#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from src.utils.config import ROOT

rows=[]
for path in (ROOT/'results/raw').glob('*.json'):
    value=json.loads(path.read_text())
    if value.get('representation') in {'raw','decoded'}:
        rows.append({"experiment_id":value['experiment_id'],"chapter":value['chapter'],"target":value['target'],
            "train":"+".join(value['train_datasets']),"model":value['model'],"feature_set":value['feature_set'],"seed":value['seed'],
            "representation":value['representation'],"f1":value['metrics_source']['f1'],"mcc":value['metrics_source']['mcc'],
            "pr_auc":value['metrics_source']['pr_auc'],"threshold":value['thresholds']['threshold_source']})
frame=pd.DataFrame(rows)
if len(frame):
    keys=['chapter','target','train','model','feature_set','seed']
    paired=frame[frame.representation=='raw'].merge(frame[frame.representation=='decoded'],on=keys,suffixes=('_raw','_decoded'))
    for metric in ['f1','mcc','pr_auc','threshold']: paired['delta_'+metric+'_decoded_minus_raw']=paired[metric+'_decoded']-paired[metric+'_raw']
else: paired=pd.DataFrame()
paired.to_csv(ROOT/'results/runs/historical/index/raw_vs_decoded.csv',index=False)
print(f'{len(paired)} pares RAW/DECODED')

