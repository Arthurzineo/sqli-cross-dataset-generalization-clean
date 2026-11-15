#!/usr/bin/env python3
"""Orquestrador sequencial. Nunca paraleliza treinamentos e nunca executa tudo sem --stage all."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
STAGES={
 "setup":["00_setup/copy_datasets.py","00_setup/capture_environment.py"],
 "audit":["01_audit/audit_datasets.py","01_audit/build_inventory_report.py"],
 "characterize":["02_dataset_characterization/characterize.py","02_dataset_characterization/compare_domains.py"],
 "baseline":["03_baseline_id/run_baseline.py"],
 "pairwise":["04_pairwise_cross_dataset/run_pairwise.py"],
 "lodo":["05_lodo/run_lodo.py"],
 "contribution":["06_dataset_contribution/run_contribution.py","06_dataset_contribution/analyze_contribution.py"],
 "shapley":["07_shapley/compute_shapley.py"],
 "threshold":["08_threshold/analyze_thresholds.py"],
 "calibration":["09_calibration/analyze_calibration.py"],
 "feature_stability":["10_feature_stability/analyze_stability.py"],
 "raw_vs_decoded":["11_raw_vs_decoded/compare_raw_decoded.py"],
 "separability":["12_dataset_separability/run_separability.py"],
 "embeddings":["13_embeddings/extract_embeddings.py","13_embeddings/analyze_embeddings.py","13_embeddings/run_embedding_lodo.py"],
 "ablation":["14_ablation/run_ablation.py"],
 "errors":["15_error_analysis/analyze_errors.py"],
 "statistics":["16_statistics/analyze_statistics.py","16_statistics/test_hypotheses.py"],
 "figures":["17_figures_tables/consolidate_results.py","17_figures_tables/generate_figures.py"],
}
ORDER=list(STAGES)
p=argparse.ArgumentParser();p.add_argument("--stage",choices=ORDER+["all"],required=True)
p.add_argument("--pilot",type=int,default=0);p.add_argument("--resume",action="store_true")
p.add_argument("--targets");p.add_argument("--models");p.add_argument("--representations");p.add_argument("--features");p.add_argument("--seeds")
p.add_argument("--scenario",choices=["A_base","B_base_plus_cooking","C_complete"],default="C_complete")
args=p.parse_args(); selected=ORDER if args.stage=="all" else [args.stage]
grid_stages={"baseline","pairwise","lodo","contribution","ablation"}
for stage in selected:
 for relative in STAGES[stage]:
  command=[sys.executable,str(ROOT/"scripts"/relative)]
  if stage in grid_stages and relative.startswith(("03_","04_","05_","06_dataset_contribution/run_","14_")):
   if args.pilot: command += ["--pilot",str(args.pilot)]
   if args.resume: command += ["--resume"]
   for name in ("targets","models","representations","features","seeds"):
    value=getattr(args,name)
    if value: command += [f"--{name}",value]
   if stage=="lodo": command += ["--scenario",args.scenario]
  elif stage=="embeddings" and relative.endswith("run_embedding_lodo.py"):
   if args.pilot: command += ["--pilot",str(args.pilot)]
   if args.resume: command += ["--resume"]
   for name in ("targets","models","representations","seeds"):
    value=getattr(args,name)
    if value: command += [f"--{name}",value]
  print("RUN",*command,flush=True)
  environment=os.environ.copy()
  environment.update({"OMP_NUM_THREADS":"2","MKL_NUM_THREADS":"2","OPENBLAS_NUM_THREADS":"2","NUMEXPR_NUM_THREADS":"2","TOKENIZERS_PARALLELISM":"false"})
  subprocess.run(command,cwd=ROOT,check=True,env=environment)
