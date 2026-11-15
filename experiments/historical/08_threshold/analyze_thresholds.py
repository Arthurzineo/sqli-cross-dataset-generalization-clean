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
    status=ROOT/'runs/status'/f"{value.get('experiment_id')}.json"
    if not status.exists() or json.loads(status.read_text()).get('status')!='COMPLETED': continue
    if 'thresholds' not in value: continue
    rows.append({"experiment_id":value['experiment_id'],"chapter":value['chapter'],"target":value['target'],
        "model":value['model'],"representation":value['representation'],
        "feature_set":value.get('feature_set','codebert_frozen' if value.get('representation')=='embedding' else 'lex64+codebert'),
        "seed":value['seed'],"pilot":value.get('pilot',0),
        **value['thresholds'],"f1_source":value['metrics_source']['f1'],"f1_oracle":value['metrics_oracle_diagnostic']['f1'],
        "pr_auc":value['metrics_source']['pr_auc']})
pd.DataFrame(rows).to_csv(ROOT/'results/runs/historical/index/threshold_transfer.csv',index=False)
print(f'{len(rows)} thresholds consolidados')
