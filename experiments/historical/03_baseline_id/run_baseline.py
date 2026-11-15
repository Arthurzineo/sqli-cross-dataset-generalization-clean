#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.grid import parser, dimensions
from src.evaluation.runner import run_experiment

args = parser("Baseline in-dataset").parse_args()
targets, models, representations, features, seeds = dimensions(args)
for target in targets:
    for representation in representations:
        for feature in features:
            for model in models:
                for seed in seeds:
                    run_experiment("baseline_id", "id", target, [], representation, feature, model, seed, args.pilot, args.resume)

