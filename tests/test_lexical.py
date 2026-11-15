import pandas as pd
from src.features.lexical import extract,feature_set


def test_lexical_has_64_features_and_ablation_is_strict():
    frame=pd.DataFrame({"text":["/x?id=1 UNION SELECT 1--"],"url":["/x?id=1"],"body":["UNION SELECT 1--"]})
    matrix=extract(frame)
    assert matrix.shape==(1,64)
    assert matrix.loc[0,"sql_union"]==1
    assert feature_set(matrix,"no_sql_keywords").shape[1]<64
