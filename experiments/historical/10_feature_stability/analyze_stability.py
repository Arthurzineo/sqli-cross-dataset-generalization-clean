#!/usr/bin/env python3
from itertools import combinations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from scipy.stats import kendalltau,spearmanr
from src.utils.config import ROOT

files=list((ROOT/'runs/feature_importance').glob('*.csv')); rows=[]
for left,right in combinations(files,2):
    a,b=pd.read_csv(left),pd.read_csv(right); joined=a.merge(b,on='feature',suffixes=('_a','_b'))
    if len(joined)<2: continue
    top_a=set(a.nlargest(10,'importance').feature); top_b=set(b.nlargest(10,'importance').feature)
    rows.append({"experiment_A":left.stem,"experiment_B":right.stem,"n_common":len(joined),
        "spearman":spearmanr(joined.importance_a,joined.importance_b).statistic,
        "kendall":kendalltau(joined.importance_a,joined.importance_b).statistic,
        "jaccard_top10":len(top_a&top_b)/max(1,len(top_a|top_b))})
pd.DataFrame(rows).to_csv(ROOT/'results/runs/historical/index/feature_stability.csv',index=False)
print(f'{len(rows)} comparações de ranking')

