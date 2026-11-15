import hashlib
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


class SplitNotViableError(ValueError):
    """Raised when leakage controls leave no valid development split."""


def _group_split(frame, seed, validation_fraction=.2, test_fraction=0):
    splitter = GroupShuffleSplit(n_splits=1, test_size=(validation_fraction + test_fraction), random_state=seed)
    train_idx, held_idx = next(splitter.split(frame, frame.y, groups=frame.canonical_hash))
    train, held = frame.iloc[train_idx].copy(), frame.iloc[held_idx].copy()
    if not test_fraction:
        return train, held
    relative = test_fraction / (validation_fraction + test_fraction)
    second = GroupShuffleSplit(n_splits=1, test_size=relative, random_state=seed + 1)
    val_idx, test_idx = next(second.split(held, held.y, groups=held.canonical_hash))
    return train, held.iloc[val_idx].copy(), held.iloc[test_idx].copy()


def _purge(development, test, key="canonical_hash"):
    mask = development[key].isin(set(test[key]))
    removed = development.loc[mask].groupby("dataset").size().to_dict()
    return development.loc[~mask].copy(), removed


def _cap(frame, cap, seed):
    if not cap: return frame
    return pd.concat([group.sample(min(cap, len(group)), random_state=seed)
                      for _, group in frame.groupby(["dataset", "y"], sort=True)], ignore_index=True)


def _remove_label_conflicts(frame):
    conflicting = frame.groupby("canonical_hash").y.nunique()
    keys = set(conflicting[conflicting > 1].index)
    removed = frame[frame.canonical_hash.isin(keys)].groupby("dataset").size().to_dict()
    return frame[~frame.canonical_hash.isin(keys)].copy(), removed


def make_split(frame, mode, target, seed=42, train_datasets=None, family_aware=True, cap=0, pilot_test=False):
    audit = {"mode": mode, "target": target, "seed": seed, "cap_per_dataset_class": cap}
    if mode == "id":
        source, audit["development_label_conflicts_removed"] = _remove_label_conflicts(frame[frame.dataset == target])
        source = source.drop_duplicates("canonical_hash")
        train, validation, test = _group_split(source, seed, .2, .2)
    else:
        test = frame[frame.dataset == target].copy()
        allowed = set(train_datasets or set(frame.dataset) - {target})
        development = frame[frame.dataset.isin(allowed) & (frame.dataset != target)].copy()
        if family_aware:
            target_family = set(test.family)
            same = development.family.isin(target_family)
            audit["same_family_removed"] = development.loc[same].groupby("dataset").size().to_dict()
            development = development.loc[~same]
        development, audit["target_overlap_removed"] = _purge(development, test)
        development, audit["development_label_conflicts_removed"] = _remove_label_conflicts(development)
        development = development.drop_duplicates("canonical_hash")
        if development.empty:
            raise SplitNotViableError(
                f"No development samples remain for target={target!r}; "
                "the selected training datasets were removed by family/leakage controls."
            )
        families = sorted(development.family.unique(), key=lambda x: hashlib.sha256(f"{seed}:{x}".encode()).hexdigest())
        validation = train = None
        for family in families:
            candidate = development[development.family == family]
            remainder = development[development.family != family]
            if candidate.y.nunique() == 2 and remainder.y.nunique() == 2:
                validation, train = candidate.copy(), remainder.copy(); break
        if train is None:
            train, validation = _group_split(development, seed, .2)
        train, extra = _purge(train, validation)
        audit["train_validation_overlap_removed"] = extra
    train, validation = _cap(train, cap, seed), _cap(validation, cap, seed)
    if pilot_test: test = _cap(test, cap, seed)
    for a, b in ((train, validation), (train, test), (validation, test)):
        assert not set(a.canonical_hash) & set(b.canonical_hash)
    audit["counts"] = {name: value.groupby(["dataset", "y"]).size().rename("n").reset_index().to_dict("records")
                       for name, value in (("train", train), ("validation", validation), ("test", test))}
    return train, validation, test, audit
