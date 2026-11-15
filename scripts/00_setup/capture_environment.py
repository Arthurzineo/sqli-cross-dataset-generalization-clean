#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.utils.config import ROOT
from src.utils.provenance import atomic_json, hardware, software_versions

atomic_json(ROOT / "docs/environment.json", {"hardware": hardware(), "software_versions": software_versions()})
with open(ROOT / "docs/pip_freeze.txt", "w") as stream:
    subprocess.run([sys.executable, "-m", "pip", "freeze"], stdout=stream, check=True)
print("Ambiente registrado")

