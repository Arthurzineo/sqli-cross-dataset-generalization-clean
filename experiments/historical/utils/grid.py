from argparse import ArgumentParser
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.evaluation.runner import run_experiment
from src.utils.config import datasets_config, experiment_config, seeds as configured_seeds


def parser(description):
    result = ArgumentParser(description=description)
    result.add_argument("--targets")
    result.add_argument("--models")
    result.add_argument("--representations")
    result.add_argument("--features")
    result.add_argument("--seeds")
    result.add_argument("--pilot", type=int, default=0)
    result.add_argument("--resume", action="store_true")
    return result


def values(argument, default, cast=str):
    return [cast(value) for value in argument.split(",")] if argument else list(default)


def dimensions(args):
    config = experiment_config()
    return (values(args.targets, config["dataset_policy"]["primary_datasets"]), values(args.models, config["models"]),
            values(args.representations, config["representations"]), values(args.features, ["lex64"]),
            values(args.seeds, configured_seeds(), int))

