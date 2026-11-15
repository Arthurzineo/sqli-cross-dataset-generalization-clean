#!/usr/bin/env python3
"""Importância pós-hoc. Usa o teste somente para explicação, nunca para seleção."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from src.data.loader import load_many
from src.features.lexical import extract,feature_set
from src.utils.config import ROOT


p=argparse.ArgumentParser();p.add_argument("experiment_id");p.add_argument("--method",choices=["native","permutation","shap"],default="permutation")
p.add_argument("--repeats",type=int,default=10);p.add_argument("--cap",type=int,default=5000);p.add_argument("--seed",type=int,default=42);args=p.parse_args()
result=json.loads((ROOT/f"results/raw/{args.experiment_id}.json").read_text())
if result["representation"] not in {"raw","decoded"}: raise SystemExit("Este script cobre experimentos léxicos RAW/DECODED.")
bundle=joblib.load(ROOT/f"runs/checkpoints/{args.experiment_id}.joblib")
split_path=ROOT/f"runs/manifests/{args.experiment_id}_split.csv.gz"
if not split_path.exists(): split_path=ROOT/f"runs/manifests/{args.experiment_id}_split.csv"
split=pd.read_csv(split_path);ids=sorted(set(result["train_datasets"]+[result["target"]]))
data=load_many(ids,result["representation"]);test_ids=set(split.query("split == 'test'").sample_id)
test=data[data.sample_id.isin(test_ids)].copy()
if args.cap and len(test)>args.cap: test=test.sample(args.cap,random_state=args.seed)
matrix=feature_set(extract(test),result["feature_set"]);X=bundle["transform"].transform(matrix.to_numpy());model=bundle["model"]
if args.method=="native":
    if hasattr(model,"get_feature_importance"): values=np.asarray(model.get_feature_importance())
    elif hasattr(model,"coef_"): values=np.abs(model.coef_[0])
    else: raise SystemExit("Modelo sem importância nativa.")
elif args.method=="permutation":
    values=permutation_importance(model,X,test.y,scoring="f1",n_repeats=args.repeats,random_state=args.seed,n_jobs=1).importances_mean
else:
    import shap
    if not hasattr(model,"get_feature_importance"): raise SystemExit("SHAP configurado apenas para CatBoost.")
    sample=X[:min(len(X),args.cap)] if args.cap else X
    explanation=shap.TreeExplainer(model).shap_values(sample);values=np.mean(np.abs(np.asarray(explanation)),axis=0)
out=pd.DataFrame({"experiment_id":args.experiment_id,"method":args.method,"feature":bundle["features"],"importance":values,
                  "evaluation_split":"test_posthoc_not_for_selection","n":len(test)})
out.to_csv(ROOT/f"runs/feature_importance/{args.experiment_id}_{args.method}.csv",index=False)
print(out.sort_values("importance",ascending=False).head(20).to_string(index=False))
