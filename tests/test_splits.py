import pandas as pd
import pytest
from src.data.splits import SplitNotViableError, make_split


def test_target_overlap_is_removed():
    rows=[]
    for dataset,family in (("a","a"),("b","b"),("target","target")):
        for y in (0,1):
            for i in range(20):
                key=f"{dataset}-{y}-{i}"
                rows.append({"dataset":dataset,"family":family,"y":y,"canonical_hash":key,"sample_id":key})
    rows.append({"dataset":"a","family":"a","y":1,"canonical_hash":"target-1-0","sample_id":"leak"})
    frame=pd.DataFrame(rows)
    train,val,test,audit=make_split(frame,"lodo","target",42,["a","b"],False)
    assert not set(train.canonical_hash)&set(test.canonical_hash)
    assert not set(val.canonical_hash)&set(test.canonical_hash)
    assert audit["target_overlap_removed"]["a"]==1


def test_family_control_can_make_contribution_split_not_viable():
    frame = pd.DataFrame({
        "dataset": ["source", "source", "target", "target"],
        "family": ["shared", "shared", "shared", "shared"],
        "y": [0, 1, 0, 1],
        "canonical_hash": ["a", "b", "c", "d"],
    })
    with pytest.raises(SplitNotViableError, match="No development samples remain"):
        make_split(frame, "contribution", "target", train_datasets=["source"])
