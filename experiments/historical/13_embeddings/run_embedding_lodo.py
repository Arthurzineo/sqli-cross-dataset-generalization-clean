#!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import resource
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import joblib
import numpy as np
import pandas as pd

from src.data.loader import load_many
from src.data.splits import make_split
from src.evaluation.metrics import calculate, threshold_for_f1
from src.evaluation.registry import append
from src.features.embeddings import load_cached
from src.features.lexical import extract
from src.models.classical import fit
from src.utils.config import ROOT, experiment_config, models_config
from src.utils.provenance import atomic_json, now, stable_hash


def matrix_for(part, embedding, lookup, lexical, representation):
    rows=np.asarray([lookup[value] for value in part.sample_id])
    dense=np.asarray(embedding[rows],dtype="float32")
    if representation == "early_fusion":
        lex=extract(part).to_numpy(dtype="float32")
        dense=np.concatenate([lex,dense],axis=1)
    return dense


p=argparse.ArgumentParser(description="LODO com CodeBERT congelado, isolado ou em early fusion.")
p.add_argument("--targets",default="");p.add_argument("--models",default="logistic,catboost,mlp")
p.add_argument("--representations",default="embedding,early_fusion");p.add_argument("--seeds",default="42,123,2026,1337,9001")
p.add_argument("--pilot",type=int,default=0);p.add_argument("--resume",action="store_true");args=p.parse_args()
datasets=experiment_config()["dataset_policy"]["primary_datasets"]; targets=args.targets.split(",") if args.targets else datasets
embedding,index=load_cached(datasets,"decoded","codebert"); lookup=dict(zip(index.sample_id,index.global_row))
cfg,model_cfg=experiment_config(),models_config()
for target in targets:
  train_ids=[value for value in datasets if value!=target]
  frame=load_many(datasets,"decoded")
  for representation in args.representations.split(","):
   for model_name in args.models.split(","):
    for seed in map(int,args.seeds.split(",")):
     spec={"chapter":"embedding_lodo","target":target,"train_datasets":train_ids,"representation":representation,
           "model":model_name,"seed":seed,"pilot":args.pilot,"encoder_frozen":True}
     key=stable_hash(spec); previous=list((ROOT/"results/raw").glob("EXP_EMBEDDING_LODO_*.json"))
     if args.resume and any(json.loads(path.read_text()).get("experiment_key")==key for path in previous): continue
     stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f"); eid=f"EXP_EMBEDDING_LODO_{model_name.upper()}_{target.upper()}_{representation.upper()}_{seed}_{stamp}"
     started=now();status_path=ROOT/f"runs/status/{eid}.json";atomic_json(status_path,{"experiment_id":eid,"status":"RUNNING","started_at":started})
     start=time.perf_counter(); train,val,test,audit=make_split(frame,"lodo",target,seed,train_ids,True,args.pilot,bool(args.pilot))
     X=matrix_for(train,embedding,lookup,None,representation);V=matrix_for(val,embedding,lookup,None,representation);T=matrix_for(test,embedding,lookup,None,representation)
     model,transform,iters=fit(model_name,X,train.y.to_numpy(),V,val.y.to_numpy(),model_cfg,seed,cfg["threads"])
     val_score=model.predict_proba(transform.transform(V))[:,1];score=model.predict_proba(transform.transform(T))[:,1]
     threshold,_=threshold_for_f1(val.y,val_score);oracle_threshold,_=threshold_for_f1(test.y,score)
     metrics=calculate(test.y,score,threshold);metrics_fixed=calculate(test.y,score,cfg["fixed_threshold"])
     metrics_oracle=calculate(test.y,score,oracle_threshold)
     predictions=pd.DataFrame({"experiment_id":eid,"sample_id":test.sample_id,"dataset":test.dataset,"true_label":test.y,
        "predicted_label":score>=threshold,"score":score,"threshold":threshold,"split":"test",
        "raw_input_hash":test.raw_input_hash,"decoded_input_hash":test.decoded_input_hash})
     pred_path=ROOT/f"runs/predictions/{eid}.csv";predictions.to_csv(pred_path,index=False)
     np.savez_compressed(ROOT/f"runs/probabilities/{eid}.npz",sample_id=test.sample_id.to_numpy(),y_true=test.y.to_numpy(),score=score,threshold=[threshold])
     joblib.dump({"model":model,"transform":transform,"representation":representation},ROOT/f"runs/checkpoints/{eid}.joblib")
     split_path=ROOT/f"runs/manifests/{eid}_split.csv"
     pd.concat([part.assign(split=name)[["sample_id","dataset","family","y","canonical_hash","split"]]
                for name,part in (("train",train),("validation",val),("test",test))],ignore_index=True).to_csv(split_path,index=False)
     threshold_data={"experiment_id":eid,"threshold_default":cfg["fixed_threshold"],"threshold_source":threshold,
       "threshold_frozen":threshold,"threshold_oracle":oracle_threshold,"threshold_drift":abs(threshold-oracle_threshold),
       "oracle_gap":metrics_oracle["f1"]-metrics["f1"]}
     atomic_json(ROOT/f"runs/thresholds/{eid}.json",threshold_data)
     result=spec|{"experiment_id":eid,"experiment_key":key,"status":"COMPLETED","started_at":started,
       "metrics_fixed":metrics_fixed,"metrics_source":metrics,"metrics_oracle_diagnostic":metrics_oracle,"thresholds":threshold_data,
       "train_n":len(train),"validation_n":len(val),"test_n":len(test),"split_audit":audit,"selected_iterations":iters,
       "runtime":time.perf_counter()-start,"rss_peak_mib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,"finished_at":now()}
     result_path=ROOT/f"results/raw/{eid}.json";atomic_json(result_path,result)
     atomic_json(ROOT/f"runs/manifests/{eid}.json",result|{"script":__file__,"encoder_cache":"codebert frozen decoded","prediction_file":str(pred_path)})
     append(ROOT/"docs/experiment_registry/experiments.csv",{"experiment_id":eid,"experiment_key":key,"chapter":"embedding_lodo",
       "status":"COMPLETED","script":__file__,"config":json.dumps(spec),"target":target,"training_pool":"+".join(train_ids),
       "model":model_name,"representation":representation,"feature_set":"codebert_frozen" if representation=="embedding" else "lex64+codebert",
       "seed":seed,"started_at":started,"finished_at":result["finished_at"],"runtime":result["runtime"],"result_path":result_path})
     atomic_json(status_path,{"experiment_id":eid,"status":"COMPLETED","finished_at":result["finished_at"]})
     print(eid,metrics["f1"],flush=True)
