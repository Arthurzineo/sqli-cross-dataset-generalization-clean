from pathlib import Path
from functools import lru_cache
import yaml

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=None)
def load_yaml(relative):
    path = ROOT / relative
    with open(path, encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def datasets_config():
    return load_yaml("config/datasets.yaml")["datasets"]


def experiment_config():
    return load_yaml("config/experiments.yaml")


def models_config():
    return load_yaml("config/models.yaml")["models"]


def seeds():
    return load_yaml("config/seeds.yaml")["seeds"]
