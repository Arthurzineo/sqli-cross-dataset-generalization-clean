#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.features.embeddings import extract_dataset
from src.utils.config import experiment_config


parser = argparse.ArgumentParser(description="Extrai embeddings congelados e persistentes, um dataset por vez.")
parser.add_argument("--datasets", default="")
parser.add_argument("--representations", default="decoded")
parser.add_argument("--model", default="codebert")
parser.add_argument("--batch-size", type=int)
parser.add_argument("--device")
parser.add_argument("--no-resume", action="store_true")
args = parser.parse_args()
datasets = args.datasets.split(",") if args.datasets else experiment_config()["dataset_policy"]["primary_datasets"]
for representation in args.representations.split(","):
    for dataset in datasets:
        path = extract_dataset(dataset, representation, args.model, args.batch_size, args.device, not args.no_resume)
        print(path, flush=True)
