#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np,pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score,f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src.data.loader import load_many
from src.features.lexical import extract,feature_set
from src.utils.config import ROOT,experiment_config

p=argparse.ArgumentParser();p.add_argument('--representations',default='raw,decoded');p.add_argument('--cap',type=int,default=2500);p.add_argument('--seed',type=int,default=42);args=p.parse_args()
datasets=experiment_config()['dataset_policy']['primary_datasets'];rows=[]
for representation in args.representations.split(','):
    frame=load_many(datasets,representation)
    frame=pd.concat([group.sample(min(args.cap,len(group)),random_state=args.seed) for _,group in frame.groupby(['dataset','y'])],ignore_index=True)
    X=feature_set(extract(frame),'lex64'); y=pd.Categorical(frame.dataset,categories=datasets).codes
    train,test=train_test_split(np.arange(len(frame)),test_size=.25,random_state=args.seed,stratify=y)
    model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=500,random_state=args.seed,n_jobs=2))
    model.fit(X.iloc[train],y[train]);pred=model.predict(X.iloc[test])
    rows.append({"representation":representation,"accuracy":accuracy_score(y[test],pred),"macro_f1":f1_score(y[test],pred,average='macro'),
                 "chance_accuracy":1/len(datasets),"n":len(frame),"seed":args.seed})
pd.DataFrame(rows).to_csv(ROOT/'results/runs/historical/index/dataset_separability.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False))

