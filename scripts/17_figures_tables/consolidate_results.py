#!/usr/bin/env python3
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import pandas as pd
from src.utils.config import ROOT


rows=[]
for path in sorted((ROOT/"results/raw").glob("*.json")):
    value=json.loads(path.read_text())
    status_path=ROOT/"runs/status"/f"{value.get('experiment_id')}.json"
    if not status_path.exists() or json.loads(status_path.read_text()).get("status")!="COMPLETED": continue
    if value.get("status")!="COMPLETED": continue
    base={key:value.get(key) for key in ("experiment_id","experiment_key","chapter","mode","target","model","representation","feature_set","seed","pilot","train_n","validation_n","test_n","runtime","extraction_seconds","training_seconds","inference_seconds","rss_peak_mib")}
    base["train_datasets"]="+".join(value.get("train_datasets",[]))
    for protocol in ("metrics_fixed","metrics_source","metrics_oracle_diagnostic"):
        for key,metric_value in value.get(protocol,{}).items(): base[f"{protocol}_{key}"]=metric_value
    rows.append(base)
master=pd.DataFrame(rows); master.to_csv(ROOT/"results/runs/historical/index/all_experiments.csv",index=False)
if not master.empty:
    master[master.pilot.fillna(0).astype(int)>0].to_csv(ROOT/"results/tables/smoke_tests_only.csv",index=False)
    eligible=master[master.pilot.fillna(0).astype(int)==0]
    lodo=eligible[eligible.chapter.astype(str).str.startswith("lodo_") | eligible.chapter.isin(["lodo","ablation","embedding_lodo"])]
    lodo.to_csv(ROOT/"results/tables/table_D_lodo.csv",index=False)
    baseline=eligible[eligible.chapter=="baseline_id"]
    baseline.to_csv(ROOT/"results/tables/table_B_in_dataset.csv",index=False)
    pair=eligible[eligible.chapter=="pairwise"]
    pair.to_csv(ROOT/"results/tables/table_C_pairwise.csv",index=False)
    if not baseline.empty and not lodo.empty:
        keys=["target","model","representation","feature_set","seed"]
        gap=baseline.merge(lodo,on=keys,suffixes=("_id","_lodo"))
        gap["generalization_gap_f1"]=gap.metrics_source_f1_id-gap.metrics_source_f1_lodo
        gap.to_csv(ROOT/"results/tables/table_E_generalization_gap.csv",index=False)
    else:
        pd.DataFrame(columns=["target","model","representation","feature_set","seed","generalization_gap_f1"]).to_csv(
            ROOT/"results/tables/table_E_generalization_gap.csv",index=False)
print(f"{len(master)} experimentos consolidados")

# Nomes estáveis das tabelas obrigatórias; arquivos vazios significam etapa ainda não executada.
sources={"F_dataset_contribution":"dataset_contribution_deltas.csv","G_shapley":"dataset_shapley.csv",
         "H_threshold":"threshold_transfer.csv","I_feature_stability":"feature_stability.csv",
         "J_raw_vs_decoded":"raw_vs_decoded.csv","K_dataset_separability":"dataset_separability.csv"}
for label,source in sources.items():
    source_path=ROOT/"results/runs/historical/index"/source
    data=pd.read_csv(source_path) if source_path.exists() and source_path.stat().st_size else pd.DataFrame()
    if "pilot" in data: data=data[data.pilot.fillna(0).astype(int)==0]
    data.to_csv(ROOT/f"results/tables/table_{label}.csv",index=False)
