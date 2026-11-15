#!/usr/bin/env python3
from pathlib import Path
import itertools, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from src.data.loader import load_dataset
from src.utils.config import ROOT, datasets_config


def main():
    summaries, overlaps, conflicts = [], [], []
    for representation in ["raw", "decoded"]:
        frames = {name: load_dataset(name, representation) for name in datasets_config()}
        for name, frame in frames.items():
            duplicate = frame.duplicated("text_hash", keep=False)
            canonical_duplicate = frame.duplicated("canonical_hash", keep=False)
            label_conflict = frame.groupby("canonical_hash").y.nunique()
            summaries.append({"representation": representation, "dataset": name, "n": len(frame),
                "benign": int((frame.y == 0).sum()), "attack": int((frame.y == 1).sum()),
                "exact_duplicate_rows": int(duplicate.sum()), "canonical_duplicate_rows": int(canonical_duplicate.sum()),
                "label_conflict_keys": int((label_conflict > 1).sum()), "empty_text": int((frame.text.str.len() == 0).sum())})
            for key in label_conflict[label_conflict > 1].index:
                conflicts.append({"representation": representation, "dataset": name, "canonical_hash": key})
        for left, right in itertools.combinations(sorted(frames), 2):
            a, b = frames[left], frames[right]
            overlaps.append({"representation": representation, "a": left, "b": right,
                "exact_overlap": len(set(a.text_hash) & set(b.text_hash)),
                "canonical_overlap": len(set(a.canonical_hash) & set(b.canonical_hash)),
                "decoded_hash_overlap": len(set(a.decoded_input_hash) & set(b.decoded_input_hash))})
    pd.DataFrame(summaries).to_csv(ROOT / "datasets/metadata/audit_summary.csv", index=False)
    pd.DataFrame(overlaps).to_csv(ROOT / "datasets/metadata/inter_dataset_overlaps.csv", index=False)
    pd.DataFrame(conflicts).to_csv(ROOT / "datasets/metadata/label_conflicts.csv", index=False)
    print("Auditoria concluída")


if __name__ == "__main__": main()

