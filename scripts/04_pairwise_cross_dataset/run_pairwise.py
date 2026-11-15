#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.utils.grid import parser, dimensions
from src.evaluation.runner import run_experiment

p = parser("Matriz cross-dataset"); p.add_argument("--sources"); args = p.parse_args()
targets, models, representations, features, seeds = dimensions(args)
sources = args.sources.split(",") if args.sources else targets
for source in sources:
    for target in targets:
        if source == target: continue
        for representation in representations:
            for feature in features:
                for model in models:
                    for seed in seeds:
                        run_experiment("pairwise", "pairwise", target, [source], representation, feature, model, seed,
                                       args.pilot, args.resume, family_aware=False,
                                       notes="Mesmo-family é cenário cross-domain controlado, registrado explicitamente.")

