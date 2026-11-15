import copy
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.metrics import log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def fit(name, X, y, validation_X, validation_y, config, seed=42, threads=2):
    transform = make_pipeline(SimpleImputer(strategy="median"), StandardScaler())
    X = transform.fit_transform(X).astype("float32")
    validation_X = transform.transform(validation_X).astype("float32")
    params = config[name]
    if name == "catboost":
        from catboost import CatBoostClassifier
        model = CatBoostClassifier(iterations=params["iterations"], depth=params["depth"],
            learning_rate=params["learning_rate"], random_seed=seed, thread_count=threads,
            verbose=False, allow_writing_files=False, task_type="CPU")
        model.fit(X, y, eval_set=(validation_X, validation_y), early_stopping_rounds=params["patience"])
        iterations = int(model.tree_count_)
    elif name == "logistic":
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(C=params["C"], max_iter=params["max_iter"], random_state=seed)
        model.fit(X, y); iterations = int(model.n_iter_[0])
    elif name == "mlp":
        from sklearn.neural_network import MLPClassifier
        model = MLPClassifier(hidden_layer_sizes=tuple(params["hidden"]), batch_size=min(params["batch_size"], len(y)),
                              random_state=seed, early_stopping=False)
        best, stale, checkpoint, iterations = float("inf"), 0, None, 0
        for epoch in range(params["epochs"]):
            model.partial_fit(X, y, classes=np.array([0, 1]))
            loss = log_loss(validation_y, model.predict_proba(validation_X), labels=[0, 1])
            if loss < best - 1e-5:
                best, stale, checkpoint, iterations = loss, 0, copy.deepcopy(model), epoch + 1
            else: stale += 1
            if stale >= params["patience"]: break
        model = checkpoint
    else: raise ValueError(name)
    return model, transform, iterations
