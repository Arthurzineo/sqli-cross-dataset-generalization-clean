#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

import numpy as np
import pandas as pd
from src.data.loader import load_many
from src.utils.config import ROOT,datasets_config


def patterns(text):
    value=str(text).lower()
    return {"has_encoding":"%" in value,"has_comment":"--" in value or "/*" in value,
            "has_union":"union" in value,"has_boolean":" or " in value or " and " in value,
            "has_quote":"'" in value or '"' in value,"long_input":len(value)>256}


files=[]
for path in (ROOT/"runs/predictions").glob("*.csv"):
    status=ROOT/"runs/status"/f"{path.stem}.json"
    if status.exists() and json.loads(status.read_text()).get("status")=="COMPLETED": files.append(path)
if not files:
    raise SystemExit("Nenhuma prediction encontrada; execute pelo menos um experimento.")
data=load_many(list(datasets_config()),"decoded")[["decoded_input_hash","text"]].drop_duplicates("decoded_input_hash")
text_by_hash=data.set_index("decoded_input_hash").text.to_dict(); del data
summaries=[]; samples=[]; cap_per_experiment_error=10
for file_number,path in enumerate(sorted(files)):
    pred=pd.read_csv(path)
    pred["error_type"]=np.select([(pred.true_label==0)&(pred.predicted_label==1),(pred.true_label==1)&(pred.predicted_label==0)],
                                  ["false_positive","false_negative"],default="correct")
    errors=pred[pred.error_type!="correct"].copy()
    if errors.empty: continue
    errors["text"]=errors.decoded_input_hash.map(text_by_hash).fillna("")
    descriptors=pd.DataFrame([patterns(value) for value in errors.text],index=errors.index)
    enriched=pd.concat([errors,descriptors],axis=1)
    for keys,group in enriched.groupby(["dataset","error_type"],dropna=False):
        summaries.append({"dataset":keys[0],"error_type":keys[1],"n":len(group),"score_sum":group.score.sum(),
            "encoded_sum":group.has_encoding.sum(),"comment_sum":group.has_comment.sum(),"union_sum":group.has_union.sum(),
            "quote_sum":group.has_quote.sum(),"long_sum":group.long_input.sum()})
        chosen=group.sample(min(cap_per_experiment_error,len(group)),random_state=42+file_number).drop(columns="text")
        chosen["sampled_from_n"]=len(group);chosen["sampling_cap_per_experiment_error"]=cap_per_experiment_error
        samples.append(chosen)
detail=pd.concat(samples,ignore_index=True) if samples else pd.DataFrame()
detail.to_csv(ROOT/"results/runs/historical/index/error_samples.csv",index=False)
summary=pd.DataFrame(summaries).groupby(["dataset","error_type"],as_index=False).sum()
summary["mean_score"]=summary.score_sum/summary.n;summary["encoded_rate"]=summary.encoded_sum/summary.n
summary["comment_rate"]=summary.comment_sum/summary.n;summary["union_rate"]=summary.union_sum/summary.n
summary["quote_rate"]=summary.quote_sum/summary.n;summary["long_rate"]=summary.long_sum/summary.n
summary=summary[["dataset","error_type","n","mean_score","encoded_rate","comment_rate","union_rate","quote_rate","long_rate"]]
summary.to_csv(ROOT/"results/runs/historical/index/error_analysis.csv",index=False)

# Mudanças são rastreadas apenas na amostra explicitamente limitada acima.
changes=detail.groupby(["decoded_input_hash","dataset"]).agg(n_predictions=("predicted_label","size"),
    n_distinct_decisions=("predicted_label","nunique"),score_min=("score","min"),score_max=("score","max")).reset_index()
changes[changes.n_distinct_decisions>1].assign(sampled_analysis=True).to_csv(ROOT/"results/runs/historical/index/decision_changes.csv",index=False)
print(f"{int(summary.n.sum())} erros agregados exatamente; {len(detail)} exemplos amostrados; "
      f"{int((changes.n_distinct_decisions>1).sum())} mudanças na amostra")
