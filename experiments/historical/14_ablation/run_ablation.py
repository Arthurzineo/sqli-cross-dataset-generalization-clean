#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

from scripts.utils.grid import dimensions, parser
from src.evaluation.runner import run_experiment
from src.utils.config import experiment_config

p=parser("Ablações LODO de grupos léxicos sem tocar no dataset alvo.")
p.set_defaults(features="lex64,no_encoding,no_sql_keywords,no_length,no_special_chars,char_rates")
args=p.parse_args(); datasets=experiment_config()["dataset_policy"]["primary_datasets"]
targets,models,representations,features,seeds=dimensions(args)
for target in targets:
    train=[value for value in datasets if value!=target]
    for representation in representations:
      for feature in features:
       for model in models:
        for seed in seeds:
         run_experiment("ablation","lodo",target,train,representation,feature,model,seed,args.pilot,args.resume,
                        notes="ablação de grupo; nenhuma escolha usa o alvo")
