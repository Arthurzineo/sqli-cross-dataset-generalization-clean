from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import resource
import time
import joblib
import numpy as np
import pandas as pd

from src.data.loader import dataset_path, load_many
from src.data.splits import SplitNotViableError, make_split
from src.evaluation.metrics import calculate, threshold_for_f1
from src.evaluation.registry import append, completed
from src.features.lexical import extract, feature_set
from src.models.classical import fit
from src.utils.config import ROOT, datasets_config, experiment_config, models_config
from src.utils.provenance import atomic_json, git_commit, hardware, now, sha256, software_versions, stable_hash


def _features(frame, name):
    matrix = feature_set(extract(frame), name)
    return matrix, list(matrix.columns)


def run_experiment(chapter, mode, target, train_datasets, representation, feature_name, model_name, seed,
                   pilot=0, resume=False, notes="", family_aware=None):
    config = experiment_config()
    spec = {"chapter": chapter, "mode": mode, "target": target, "train_datasets": sorted(train_datasets or []),
            "representation": representation, "feature_set": feature_name, "model": model_name, "seed": seed,
            "pilot": pilot, "family_aware": config["family_aware"] if family_aware is None else family_aware,
            "near_dedup": config["near_dedup"]}
    key = stable_hash(spec)
    registry_path = ROOT / "docs/experiment_registry/experiments.csv"
    if resume and completed(registry_path, key): return None
    model_config = models_config()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    experiment_id = f"EXP_{chapter.upper()}_{model_name.upper()}_{target.upper()}_{representation.upper()}_{seed}_{stamp}"
    log_path = ROOT / "runs/logs" / f"{experiment_id}.log"
    logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    started = now(); clock = time.perf_counter()
    status_path = ROOT / "runs/status" / f"{experiment_id}.json"
    atomic_json(status_path, {"experiment_id": experiment_id, "status": "RUNNING", "started_at": started})
    try:
        ids = sorted(set((train_datasets or []) + [target]))
        data = load_many(ids, representation)
        split_mode = "id" if mode == "id" else mode
        train, validation, test, audit = make_split(data, split_mode, target, seed, train_datasets,
            family_aware=spec["family_aware"], cap=pilot, pilot_test=bool(pilot))
        X, names = _features(train, feature_name); V, _ = _features(validation, feature_name); T, _ = _features(test, feature_name)
        extraction_seconds = time.perf_counter() - clock
        training_started = time.perf_counter()
        model, transform, iterations = fit(model_name, X.to_numpy(), train.y.to_numpy(), V.to_numpy(), validation.y.to_numpy(),
                                            model_config, seed, config["threads"])
        training_seconds = time.perf_counter() - training_started
        inference_started = time.perf_counter()
        validation_scores = model.predict_proba(transform.transform(V.to_numpy()))[:, 1]
        test_scores = model.predict_proba(transform.transform(T.to_numpy()))[:, 1]
        inference_seconds = time.perf_counter() - inference_started
        source_threshold, _ = threshold_for_f1(validation.y.to_numpy(), validation_scores)
        oracle_threshold, _ = threshold_for_f1(test.y.to_numpy(), test_scores)
        metrics_fixed = calculate(test.y, test_scores, config["fixed_threshold"])
        metrics_source = calculate(test.y, test_scores, source_threshold)
        metrics_oracle = calculate(test.y, test_scores, oracle_threshold)
        prediction_path = ROOT / "runs/predictions" / f"{experiment_id}.csv"
        predictions = pd.DataFrame({"experiment_id": experiment_id, "sample_id": test.sample_id, "dataset": test.dataset,
            "true_label": test.y, "predicted_label": (test_scores >= source_threshold).astype(int), "score": test_scores,
            "threshold": source_threshold, "split": "test", "raw_input_hash": test.raw_input_hash,
            "decoded_input_hash": test.decoded_input_hash})
        predictions.to_csv(prediction_path, index=False)
        probability_path = ROOT / "runs/probabilities" / f"{experiment_id}.npz"
        np.savez_compressed(probability_path, sample_id=test.sample_id.to_numpy(), y_true=test.y.to_numpy(),
                            score=test_scores, threshold=np.asarray([source_threshold]))
        split_path = ROOT / "runs/manifests" / f"{experiment_id}_split.csv.gz"
        pd.concat([part.assign(split=name)[["sample_id", "dataset", "family", "y", "canonical_hash", "split"]]
                   for name, part in (("train", train), ("validation", validation), ("test", test))],
                  ignore_index=True).to_csv(split_path, index=False, compression="gzip")
        threshold_path = ROOT / "runs/thresholds" / f"{experiment_id}.json"
        threshold_data = {"experiment_id": experiment_id, "threshold_default": config["fixed_threshold"],
            "threshold_source": source_threshold, "threshold_frozen": source_threshold, "threshold_oracle": oracle_threshold,
            "threshold_drift": abs(source_threshold - oracle_threshold), "oracle_gap": metrics_oracle["f1"] - metrics_source["f1"]}
        atomic_json(threshold_path, threshold_data)
        importance_path = None
        if model_name == "catboost":
            importance_path = ROOT / "runs/feature_importance" / f"{experiment_id}.csv"
            pd.DataFrame({"experiment_id": experiment_id, "feature": names,
                          "importance": model.get_feature_importance()}).to_csv(importance_path, index=False)
        checkpoint_path = ROOT / "runs/checkpoints" / f"{experiment_id}.joblib"
        joblib.dump({"model": model, "transform": transform, "features": names}, checkpoint_path)
        runtime = time.perf_counter() - clock
        result = spec | {"experiment_id": experiment_id, "experiment_key": key, "status": "COMPLETED",
            "started_at": started, "finished_at": now(), "runtime": runtime, "extraction_seconds": extraction_seconds,
            "training_seconds": training_seconds, "inference_seconds": inference_seconds, "selected_iterations": iterations,
            "train_n": len(train), "validation_n": len(validation), "test_n": len(test), "split_audit": audit,
            "metrics_fixed": metrics_fixed, "metrics_source": metrics_source, "metrics_oracle_diagnostic": metrics_oracle,
            "thresholds": threshold_data, "rss_peak_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
        result_path = ROOT / "results/raw" / f"{experiment_id}.json"; atomic_json(result_path, result)
        dataset_files = {value: {"path": str(dataset_path(value, representation)),
                                 "sha256": sha256(dataset_path(value, representation))}
                         for value in ids}
        manifest = {**result, "script": __file__, "git_commit": git_commit(ROOT), "hardware": hardware(),
                    "software_versions": software_versions(), "dataset_files": dataset_files,
                    "output_files": [str(result_path), str(prediction_path), str(probability_path), str(split_path),
                                     str(threshold_path), str(checkpoint_path), str(importance_path) if importance_path else None]}
        atomic_json(ROOT / "runs/manifests" / f"{experiment_id}.json", manifest)
        append(registry_path, {"experiment_id": experiment_id, "experiment_key": key, "chapter": chapter, "status": "COMPLETED",
            "script": __file__, "config": json.dumps(spec), "target": target, "training_pool": "+".join(train_datasets or []),
            "model": model_name, "representation": representation, "feature_set": feature_name, "seed": seed,
            "started_at": started, "finished_at": result["finished_at"], "runtime": runtime, "result_path": result_path, "notes": notes})
        atomic_json(status_path, {"experiment_id": experiment_id, "status": "COMPLETED", "finished_at": result["finished_at"]})
        logging.info("COMPLETED %s", metrics_source)
        return result
    except SplitNotViableError as error:
        finished = now()
        atomic_json(status_path, {"experiment_id": experiment_id, "status": "SKIPPED",
                                  "reason": str(error), "finished_at": finished})
        append(registry_path, {"experiment_id": experiment_id, "experiment_key": key, "chapter": chapter,
                              "status": "SKIPPED", "script": __file__, "config": json.dumps(spec),
                              "target": target, "training_pool": "+".join(train_datasets or []),
                              "model": model_name, "representation": representation,
                              "feature_set": feature_name, "seed": seed, "started_at": started,
                              "finished_at": finished, "runtime": time.perf_counter() - clock,
                              "notes": str(error)})
        logging.warning("SKIPPED %s", error)
        return {**spec, "experiment_id": experiment_id, "experiment_key": key,
                "status": "SKIPPED", "reason": str(error)}
    except Exception as error:
        atomic_json(status_path, {"experiment_id": experiment_id, "status": "FAILED", "error": repr(error), "finished_at": now()})
        append(registry_path, {"experiment_id": experiment_id, "experiment_key": key, "chapter": chapter, "status": "FAILED",
                              "target": target, "training_pool": "+".join(train_datasets or []), "model": model_name,
                              "representation": representation, "feature_set": feature_name, "seed": seed, "started_at": started,
                              "finished_at": now(), "notes": repr(error)})
        logging.exception("FAILED"); raise
