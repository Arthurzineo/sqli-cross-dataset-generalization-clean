#!/usr/bin/env python3
import csv
from pathlib import Path
import shutil
import stat
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
from src.utils.config import ROOT, datasets_config
from src.utils.provenance import sha256


def main():
    rows = []
    for dataset_id, spec in datasets_config().items():
        for representation in ["raw", "decoded"]:
            source = (ROOT / spec[f"{representation}_source"]).resolve()
            destination = ROOT / "datasets/original_copies" / representation / spec[f"{representation}_file"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            source_hash = sha256(source)
            if not destination.exists() or sha256(destination) != source_hash:
                shutil.copy2(source, destination)
            copy_hash = sha256(destination)
            if source_hash != copy_hash: raise RuntimeError(f"Hash divergente: {destination}")
            frame = pd.read_csv(destination, sep=spec["separator"], encoding=spec["encoding"], low_memory=False)
            labels = pd.to_numeric(frame[spec["label_column"]], errors="raise")
            rows.append({"dataset_id": dataset_id, "dataset_name": dataset_id, "representation": representation,
                "original_path": str(source), "copied_path": str(destination), "original_filename": source.name,
                "copied_filename": destination.name, "sha256_original": source_hash, "sha256_copy": copy_hash,
                "file_size": destination.stat().st_size, "n_rows": len(frame), "label_column": spec["label_column"],
                "benign": int((labels == 0).sum()), "malicious": int((labels == 1).sum()),
                "source_type": spec["source_type"], "paper": spec.get("paper"), "year": spec.get("year"),
                "doi": spec.get("doi"), "url": spec.get("url"), "generation_method": spec.get("generation_method"),
                "attack_source": spec.get("attack_source"), "benign_source": spec.get("benign_source"), "notes": spec.get("notes")})
            destination.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    pd.DataFrame(rows).to_csv(ROOT / "datasets/metadata/dataset_manifest.csv", index=False)
    print(f"{len(rows)} cópias verificadas por SHA-256")


if __name__ == "__main__": main()

