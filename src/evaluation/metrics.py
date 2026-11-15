import numpy as np
from sklearn.metrics import (average_precision_score, balanced_accuracy_score, brier_score_loss,
    confusion_matrix, f1_score, matthews_corrcoef, precision_score, recall_score, roc_auc_score)


def threshold_for_f1(y, scores):
    candidates = np.unique(np.r_[0.0, scores, 1.0])
    if len(candidates) > 5000: candidates = np.quantile(candidates, np.linspace(0, 1, 5000))
    values = np.array([f1_score(y, scores >= value, zero_division=0) for value in candidates])
    return float(candidates[np.argmax(values)]), float(values.max())


def expected_calibration_error(y, scores, bins=10):
    edges = np.linspace(0, 1, bins + 1); total = len(y); result = 0.0
    for left, right in zip(edges[:-1], edges[1:]):
        mask = (scores >= left) & (scores < right if right < 1 else scores <= right)
        if mask.any(): result += mask.mean() * abs(scores[mask].mean() - y[mask].mean())
    return float(result)


def calculate(y, scores, threshold=.5):
    y = np.asarray(y); scores = np.asarray(scores); predicted = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel().astype(int)
    both = len(np.unique(y)) == 2
    return {"threshold": float(threshold), "precision": float(precision_score(y, predicted, zero_division=0)),
            "recall": float(recall_score(y, predicted, zero_division=0)), "f1": float(f1_score(y, predicted, zero_division=0)),
            "macro_f1": float(f1_score(y, predicted, average="macro", zero_division=0)) if both else None,
            "balanced_accuracy": float(balanced_accuracy_score(y, predicted)) if both else None,
            "specificity": tn / (tn + fp) if tn + fp else None, "mcc": float(matthews_corrcoef(y, predicted)) if both else None,
            "pr_auc": float(average_precision_score(y, scores)) if both else None,
            "roc_auc": float(roc_auc_score(y, scores)) if both else None,
            "brier": float(brier_score_loss(y, scores)) if both else None, "ece_10": expected_calibration_error(y, scores) if both else None,
            "fpr": fp / (tn + fp) if tn + fp else None, "fnr": fn / (tp + fn) if tp + fn else None,
            "tn": tn, "fp": fp, "fn": fn, "tp": tp, "n": int(len(y)), "n_attack": int(y.sum())}

