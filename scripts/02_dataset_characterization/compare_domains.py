#!/usr/bin/env python3
import argparse
from itertools import combinations
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import wasserstein_distance
from src.data.loader import load_dataset
from src.features.lexical import extract
from src.utils.config import ROOT,datasets_config


p=argparse.ArgumentParser();p.add_argument("--representations",default="raw,decoded");p.add_argument("--cap",type=int,default=0)
p.add_argument("--seed",type=int,default=42);args=p.parse_args();rows=[]
for representation in args.representations.split(","):
    matrices={}
    for dataset in datasets_config():
        frame=load_dataset(dataset,representation);matrix=extract(frame);matrix["y"]=frame.y.to_numpy()
        if args.cap:
            matrix=pd.concat([g.sample(min(args.cap,len(g)),random_state=args.seed) for _,g in matrix.groupby("y")])
        matrices[dataset]=matrix
    features=[column for column in next(iter(matrices.values())).columns if column!="y"]
    for left,right in combinations(matrices,2):
      for label in (0,1):
       a=matrices[left].query("y == @label");b=matrices[right].query("y == @label")
       for feature in features:
        x=a[feature].to_numpy();y=b[feature].to_numpy(); pooled=np.r_[x,y]
        edges=np.histogram_bin_edges(pooled,bins=64)
        if len(np.unique(edges))<2: js=0.0
        else:
            hx,_=np.histogram(x,bins=edges);hy,_=np.histogram(y,bins=edges)
            js=float(jensenshannon(hx+1e-12,hy+1e-12,base=2)**2)
        rows.append({"representation":representation,"dataset_a":left,"dataset_b":right,"class":label,"feature":feature,
          "wasserstein":wasserstein_distance(x,y),"jensen_shannon":js,"n_a":len(x),"n_b":len(y),"cap_per_class":args.cap})
pd.DataFrame(rows).to_csv(ROOT/"results/runs/historical/index/lexical_domain_distances.csv",index=False)
print(f"{len(rows)} distâncias dataset-classe-feature")
