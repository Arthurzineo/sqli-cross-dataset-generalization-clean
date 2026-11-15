#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.grid import parser, dimensions
from src.evaluation.runner import run_experiment
from src.utils.config import experiment_config

p = parser("Leave-One-Dataset-Out"); p.add_argument("--scenario", default="C_complete")
args = p.parse_args()
targets, models, representations, features, seeds = dimensions(args)
policy = experiment_config()["dataset_policy"]
pool = policy.get("scenarios", {}).get(args.scenario, policy["primary_datasets"])
targets = [value for value in targets if value in pool] if args.targets else pool
for target in targets:
    train = [value for value in pool if value != target]
    for representation in representations:
        for feature in features:
            for model in models:
                for seed in seeds:
                    run_experiment(f"lodo_{args.scenario}", "lodo", target, train, representation, feature, model, seed,
                                   args.pilot, args.resume, notes=f"scenario={args.scenario}")
