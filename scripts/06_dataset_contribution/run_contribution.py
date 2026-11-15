#!/usr/bin/env python3
from itertools import combinations
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.grid import parser, dimensions
from src.evaluation.runner import run_experiment
from src.utils.config import experiment_config

p = parser("Contribuição de subconjuntos"); p.add_argument("--max-subset-size", type=int); args = p.parse_args()
targets, models, representations, features, seeds = dimensions(args)
pool = experiment_config()["dataset_policy"]["primary_datasets"]
for target in targets:
    candidates = [value for value in pool if value != target]
    maximum = args.max_subset_size or len(candidates)
    subsets = [list(value) for size in range(1, maximum + 1) for value in combinations(candidates, size)]
    for train in subsets:
        for representation in representations:
            for feature in features:
                for model in models:
                    for seed in seeds:
                        run_experiment("contribution", "contribution", target, train, representation, feature, model, seed,
                                       args.pilot, args.resume)

