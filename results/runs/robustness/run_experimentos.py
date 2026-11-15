#!/usr/bin/env python3
"""Executa as análises de revisão 3.1, 3.2, 3.3 e o complemento de esqueletos.

Todo artefato escrito fica abaixo deste diretório. As entradas da coleção
controlada e os datasets do projeto são tratados como somente leitura.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "2"

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ARTICLE = ROOT / "artigo"
CONTROL = ARTICLE / "complementos_generalizacao_v1" / "full"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ARTICLE))
sys.path.insert(0, str(ARTICLE / "scripts" / "supplemental"))
sys.path.insert(0, str(ROOT / "SQLI" / "scripts"))

from src.data.loader import canonical, clean_url, decode_until_stable, digest, make_text
from src.evaluation.metrics import calculate
from src.features.lexical import extract
from src.models.classical import fit
from src.utils.provenance import sha256
from common import fast_threshold, paired_views
from analisar_rotulos import PADRAO_SQL_ESTRITO
from remover_benignas_com_payload import FAMILIAS

SEEDS = [42, 123, 2026, 1337, 9001]
MODELS = ["logistic", "catboost", "mlp"]
REPS = ["RAW", "CANONICALIZED"]
BASE_CONFIG = {
    "logistic": {"C": 1.0, "max_iter": 500},
    "catboost": {"iterations": 200, "depth": 5, "learning_rate": 0.05, "patience": 15},
    "mlp": {"hidden": [64, 32], "epochs": 40, "batch_size": 128, "patience": 6},
}


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    frame.to_csv(temp, index=False)
    temp.replace(path)


def write_json(value: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    def convert(item):
        if isinstance(item, np.integer): return int(item)
        if isinstance(item, np.floating): return float(item)
        if isinstance(item, np.ndarray): return item.tolist()
        if pd.isna(item): return None
        raise TypeError(f"não serializável: {type(item)}")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=convert))
    temp.replace(path)


def json_list(value) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return json.loads(value)
    return []


def stable_seed(*parts: object) -> int:
    raw = "|".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:4], "big") & 0x7FFFFFFF


class Context:
    def __init__(self) -> None:
        self.master = pd.read_parquet(CONTROL / "analysis" / "master_results.parquet")
        first = json.loads(Path(self.master.original_metric_file.iloc[0]).read_text())
        self.cache = Path(first["cache"])
        self.cohort = pd.read_parquet(self.cache / "cohort.parquet")
        self.arrays = {rep: np.load(self.cache / f"{rep}.npy", mmap_mode="r") for rep in REPS}
        self._split_cache: dict[tuple[str, int], pd.DataFrame] = {}

    def base_row(self, target: str, seed: int, model: str = "logistic", rep: str = "RAW") -> pd.Series:
        rows = self.master[(self.master.kind == "lodo") & (self.master.target == target) &
                           (self.master.seed == seed) & (self.master.model == model) &
                           (self.master.representation == rep)]
        if len(rows) != 1:
            raise RuntimeError(f"LODO base não único: {target}/{seed}/{model}/{rep}: {len(rows)}")
        return rows.iloc[0]

    def split(self, target: str, seed: int) -> pd.DataFrame:
        key = (target, seed)
        if key not in self._split_cache:
            meta = json.loads(Path(self.base_row(target, seed).original_metric_file).read_text())
            self._split_cache[key] = pd.read_parquet(meta["split_file"])
        return self._split_cache[key].copy()


def isolate(parts: dict[str, pd.DataFrame]) -> None:
    for a, b in (("train", "validation"), ("train", "test"), ("validation", "test")):
        overlap = set(parts[a].canonical_hash) & set(parts[b].canonical_hash)
        if overlap:
            raise AssertionError(f"vazamento canônico {a}/{b}: {len(overlap)}")
    for name in ("train", "validation"):
        if parts[name].empty or parts[name].y.nunique() != 2:
            raise RuntimeError(f"{name} sem duas classes")
    if parts["test"].empty:
        raise RuntimeError("teste vazio")


def get_matrix(frame: pd.DataFrame, rep: str, ctx: Context,
               variant_arrays: dict[str, np.ndarray] | None = None) -> np.ndarray:
    if "matrix_origin" not in frame:
        return np.asarray(ctx.arrays[rep][frame.feature_row.to_numpy(dtype=int)], dtype="float32")
    result = np.empty((len(frame), ctx.arrays[rep].shape[1]), dtype="float32")
    base_mask = frame.matrix_origin.eq("base").to_numpy()
    if base_mask.any():
        result[base_mask] = ctx.arrays[rep][frame.loc[base_mask, "feature_row"].to_numpy(dtype=int)]
    variant_mask = ~base_mask
    if variant_mask.any():
        if variant_arrays is None:
            raise RuntimeError("matriz variante ausente")
        result[variant_mask] = variant_arrays[rep][frame.loc[variant_mask, "variant_row"].to_numpy(dtype=int)]
    return result


def execute_fit(ctx: Context, model_name: str, rep: str, config: dict, seed: int,
                train: pd.DataFrame, validation: pd.DataFrame, test: pd.DataFrame,
                variant_arrays: dict[str, np.ndarray] | None = None,
                groups: pd.Series | None = None) -> tuple[dict, pd.DataFrame | None]:
    isolate({"train": train, "validation": validation, "test": test})
    started = time.perf_counter()
    X = get_matrix(train, rep, ctx, variant_arrays)
    V = get_matrix(validation, rep, ctx, variant_arrays)
    T = get_matrix(test, rep, ctx, variant_arrays)
    with threadpool_limits(limits=2):
        model, transform, iterations = fit(model_name, X, train.y.to_numpy(), V,
                                           validation.y.to_numpy(), config, seed, 2)
        validation_scores = model.predict_proba(transform.transform(V))[:, 1]
        threshold, validation_f1 = fast_threshold(validation.y, validation_scores)
        test_scores = model.predict_proba(transform.transform(T))[:, 1]
    metrics = calculate(test.y, test_scores, threshold)
    row = {
        "model": model_name, "representation": rep, "seed": seed,
        "train_n": len(train), "validation_n": len(validation), "test_n": len(test),
        "threshold": threshold, "validation_f1": validation_f1,
        "selected_iterations": iterations, "wall_seconds": time.perf_counter() - started,
        **{f"test_{key}": value for key, value in metrics.items()},
    }
    group_metrics = None
    if groups is not None:
        records = []
        prediction = test_scores >= threshold
        for group in sorted(groups.dropna().unique()):
            mask = groups.eq(group).to_numpy()
            y = test.y.to_numpy()[mask]
            pred = prediction[mask]
            # Grupos dos filtros são uniclasse. Métricas inaplicáveis ficam NA.
            records.append({
                "filter_group": group, "n": int(mask.sum()), "n_attack": int(y.sum()),
                "f1_attack": (float(2 * pred.sum() / (pred.sum() + len(y))) if np.all(y == 1) else np.nan),
                "recall": (float(pred.mean()) if np.all(y == 1) else np.nan),
                "fpr": (float(pred.mean()) if np.all(y == 0) else np.nan),
            })
        group_metrics = pd.DataFrame(records)
    return row, group_metrics


def save_run(row: dict, folder: Path, run_id: str) -> None:
    write_json(row, folder / "runs" / f"{run_id}.json")


def load_run_rows(folder: Path) -> pd.DataFrame:
    return pd.DataFrame([json.loads(path.read_text()) for path in sorted((folder / "runs").glob("*.json"))])


def analysis_3_1(ctx: Context) -> None:
    out = HERE / "3_1_tamanho_controlado"
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    selection_records = []
    targets = sorted(ctx.master[ctx.master.kind == "lodo"].target.unique())
    for target in targets:
        for seed in SEEDS:
            split = ctx.split(target, seed)
            train = split[split.split == "train"].copy()
            validation = split[split.split == "validation"].copy()
            test = split[split.split == "test"].copy()
            counts = train.groupby(["dataset", "y"]).size()
            n_per_class = int(counts.min())
            selected = []
            for (source, y), group in train.groupby(["dataset", "y"], sort=True):
                sampling_seed = stable_seed("3.1", target, source, seed, int(y))
                chosen = group.sample(n=n_per_class, random_state=sampling_seed).copy()
                selected.append(chosen)
                selection_records.extend({
                    "target": target, "seed": seed, "source": source, "y": int(y),
                    "sample_id": value.sample_id, "row_number": int(value.row_number),
                    "sampling_seed": sampling_seed, "n_per_class": n_per_class,
                } for value in chosen.itertuples())
            selected_train = pd.concat(selected, ignore_index=True)
            sources = sorted(selected_train.dataset.unique())
            cases = [("complete", None, selected_train)] + [
                ("removed", source, selected_train[selected_train.dataset != source].copy()) for source in sources
            ]
            for kind, removed, case_train in cases:
                run_id = f"{target}__{seed}__{kind}__{removed or 'none'}"
                if (out / "runs" / f"{run_id}.json").exists():
                    continue
                row, _ = execute_fit(ctx, "catboost", "CANONICALIZED", BASE_CONFIG, seed,
                                     case_train, validation, test)
                row.update({"analysis": "3.1", "target": target, "kind": kind,
                            "removed_source": removed, "n_per_source_class": n_per_class,
                            "training_sources": sorted(case_train.dataset.unique())})
                save_run(row, out, run_id)
    selection = pd.DataFrame(selection_records).drop_duplicates(["target", "seed", "sample_id"])
    write_csv(selection, out / "manifesto_linhas_selecionadas.csv")
    rows = load_run_rows(out)
    write_csv(rows.sort_values(["target", "seed", "kind", "removed_source"], na_position="first"),
              out / "resultados_por_semente.csv")

    full = rows[rows.kind == "complete"][["target", "seed", "test_f1"]].rename(columns={"test_f1": "f1_complete_controlled"})
    removed = rows[rows.kind == "removed"][["target", "seed", "removed_source", "test_f1"]].rename(columns={"test_f1": "f1_removed_controlled"})
    new = removed.merge(full, on=["target", "seed"], validate="many_to_one")
    new["C_size_controlled"] = new.f1_complete_controlled - new.f1_removed_controlled
    original = pd.read_parquet(ARTICLE / "analise_resultados_tcc" / "SUPPLEMENTAL_CONTROLLED_ANALYSIS" /
                               "derived" / "source_contribution_per_seed.parquet")
    original = original[(original.model == "catboost") & (original.representation == "CANONICALIZED")]
    original = original[["target", "seed", "removed_source", "full_f1", "removed_f1", "delta_f1"]].rename(
        columns={"delta_f1": "C_original", "full_f1": "f1_complete_original", "removed_f1": "f1_removed_original"})
    paired = original.merge(new, on=["target", "seed", "removed_source"], validate="one_to_one")
    paired["sign_changed_seed"] = np.sign(paired.C_original) != np.sign(paired.C_size_controlled)
    write_csv(paired.sort_values(["target", "removed_source", "seed"]), out / "contribuicoes_por_semente.csv")
    mean = paired.groupby(["target", "removed_source"], as_index=False).agg(
        C_original=("C_original", "mean"), C_size_controlled=("C_size_controlled", "mean"),
        n_seeds=("seed", "nunique"), sign_changes_seed=("sign_changed_seed", "sum"))
    mean["sign_changed_mean"] = np.sign(mean.C_original) != np.sign(mean.C_size_controlled)
    write_csv(mean, out / "contribuicoes_media_alvo_fonte.csv")
    rho_seed = spearmanr(paired.C_original, paired.C_size_controlled)
    rho_mean = spearmanr(mean.C_original, mean.C_size_controlled)
    summary = {
        "n_pairs_seed": len(paired), "n_pairs_target_source": len(mean),
        "sign_changes_seed": int(paired.sign_changed_seed.sum()),
        "sign_changes_target_source_mean": int(mean.sign_changed_mean.sum()),
        "spearman_seed": float(rho_seed.statistic), "spearman_seed_p": float(rho_seed.pvalue),
        "spearman_target_source_mean": float(rho_mean.statistic), "spearman_target_source_mean_p": float(rho_mean.pvalue),
        "original_remove_increased_f1_mean": int((mean.C_original < 0).sum()),
        "original_remove_reduced_f1_mean": int((mean.C_original > 0).sum()),
        "controlled_remove_increased_f1_mean": int((mean.C_size_controlled < 0).sum()),
        "controlled_remove_reduced_f1_mean": int((mean.C_size_controlled > 0).sum()),
        "original_remove_increased_f1_seed": int((paired.C_original < 0).sum()),
        "original_remove_reduced_f1_seed": int((paired.C_original > 0).sum()),
        "controlled_remove_increased_f1_seed": int((paired.C_size_controlled < 0).sum()),
        "controlled_remove_reduced_f1_seed": int((paired.C_size_controlled > 0).sum()),
        "wall_seconds_this_invocation": time.perf_counter() - started,
    }
    write_json(summary, out / "resumo_numerico.json")
    sizes = selection.groupby(["target", "seed"], as_index=False).agg(
        n_per_class=("n_per_class", "first"), n_sources=("source", "nunique"), selected_rows=("sample_id", "size"))
    write_csv(sizes, out / "tamanho_por_classe_alvo_semente.csv")
    write_json({"analysis": "3.1", "wall_seconds": time.perf_counter() - started,
                "completed_at": pd.Timestamp.now().isoformat()}, out / "tempo_parede.json")


def _balance(frame: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, set[int]]:
    labels = frame.classification.astype(int)
    i1 = frame.index[labels == 1]
    i0 = frame.index[labels == 0]
    n = min(len(i1), len(i0))
    if len(i1) > n:
        i1 = pd.Series(i1).sample(n=n, random_state=seed).to_numpy()
    if len(i0) > n:
        i0 = pd.Series(i0).sample(n=n, random_state=seed).to_numpy()
    keep = set(map(int, np.r_[i1, i0]))
    return frame.loc[sorted(keep)].copy(), set(map(int, frame.index)) - keep


def prepare_srbh_variant() -> None:
    out = HERE / "3_2_srbh_sem_filtros" / "variant"
    ready = out / "READY.json"
    if ready.exists():
        return
    started = time.perf_counter()
    source = ROOT / "SQLI" / "datasets" / "originais" / "srbh_completo_sqli.csv"
    original = pd.read_csv(source, low_memory=False)
    original["source_row"] = np.arange(1, len(original) + 1)
    key = (original.URL.fillna("").astype(str) + " " + original.content.fillna("").astype(str)).str.strip()
    conflict = original.classification.groupby(key).transform("nunique") > 1
    no_conflict = original.loc[~conflict].copy()
    key_nc = key.loc[~conflict]
    dedup = no_conflict.loc[~key_nc.duplicated()].copy()
    unfiltered, _ = _balance(dedup, 42)
    if unfiltered.classification.value_counts().to_dict() != {0: 89292, 1: 89292}:
        raise AssertionError(f"contagem SRBH sem filtro inesperada: {unfiltered.classification.value_counts().to_dict()}")
    unfiltered = unfiltered.reset_index(drop=True)
    unfiltered["variant_row"] = np.arange(len(unfiltered))
    status = pd.Series("not_reached_after_rebalance", index=unfiltered.index, dtype="object")
    family_match = pd.Series("", index=unfiltered.index, dtype="object")

    work = unfiltered.copy()
    f1 = (work.classification == 1) & (work.tem_indicador_sqli == 0)
    status.loc[work.index[f1]] = "filter_1_sqli_sem_indicador"
    before = work.loc[~f1].copy()
    work, removed = _balance(before, 42)
    status.loc[list(removed)] = "rebalance_1"

    decoded = (work.URL.map(decode_until_stable) + " " + work.content.map(decode_until_stable)).str.strip()
    f2 = (work.classification == 1) & ~decoded.str.contains(PADRAO_SQL_ESTRITO)
    status.loc[work.index[f2]] = "filter_2_sqli_fora_padrao_estrito"
    before = work.loc[~f2].copy()
    work, removed = _balance(before, 42)
    status.loc[list(removed)] = "rebalance_2"

    decoded = (work.URL.map(decode_until_stable) + " " + work.content.map(decode_until_stable)).str.strip()
    benign = work.classification == 0
    f3 = pd.Series(False, index=work.index)
    for name, pattern in FAMILIAS:
        current = benign & ~f3 & decoded.str.contains(pattern, regex=True)
        family_match.loc[work.index[current]] = name
        f3 |= current
    status.loc[work.index[f3]] = "filter_3_benigno_padrao_ataque"
    before = work.loc[~f3].copy()
    work, removed = _balance(before, 42)
    status.loc[list(removed)] = "rebalance_final"
    status.loc[work.index] = "final_kept"

    expected = {
        "filter_1_sqli_sem_indicador": 7043,
        "filter_2_sqli_fora_padrao_estrito": 7398,
        "filter_3_benigno_padrao_ataque": 21561,
        "final_kept": 106580,
    }
    observed = status.value_counts().to_dict()
    for key_name, value in expected.items():
        if observed.get(key_name) != value:
            raise AssertionError(f"{key_name}: {observed.get(key_name)} != {value}")

    filtered = pd.read_csv(ARTICLE / "datasets" / "original_copies" / "raw" / "srbh.csv", low_memory=False)
    key_final = set((work.URL.fillna("").astype(str) + "\0" + work.content.fillna("").astype(str)).tolist())
    key_saved = set((filtered.URL.fillna("").astype(str) + "\0" + filtered.content.fillna("").astype(str)).tolist())
    if key_final != key_saved or len(work) != len(filtered):
        raise AssertionError(f"final reconstruído não coincide: apenas reconstruído={len(key_final-key_saved)}, apenas salvo={len(key_saved-key_final)}")

    raw = pd.DataFrame({
        "dataset": "srbh", "family": "srbh", "row_number": unfiltered.variant_row + 1,
        "y": unfiltered.classification.astype("int8"), "url": unfiltered.URL.fillna("").astype(str),
        "body": unfiltered.content.fillna("").astype(str),
    })
    raw["text"] = [make_text(url, body, decode=False) for url, body in zip(raw.url, raw.body)]
    raw_view, can_view = paired_views(raw, sha256(source))
    matrices = {}
    for rep, frame in (("RAW", raw_view), ("CANONICALIZED", can_view)):
        matrix = extract(frame).to_numpy(dtype="float32")
        path = out / f"{rep}.npy"
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, matrix)
        matrices[rep] = path
    meta = raw_view[["sample_id", "dataset", "family", "row_number", "y", "canonical_hash"]].copy()
    meta["variant_row"] = np.arange(len(meta))
    meta["matrix_origin"] = "variant"
    meta["filter_group"] = status.to_numpy()
    meta["filter_family"] = family_match.to_numpy()
    meta["source_row"] = unfiltered.source_row.to_numpy()
    meta.to_parquet(out / "cohort.parquet", index=False)
    manifest = meta[["sample_id", "row_number", "source_row", "y", "canonical_hash", "filter_group", "filter_family"]]
    write_csv(manifest, out / "manifesto_linhas_srbh_sem_filtros.csv")
    write_csv(unfiltered.drop(columns=["variant_row"]), out / "srbh_sem_filtros_raw.csv")
    counts = pd.DataFrame([
        {"stage": "original_selection", "n": len(original), "benign": int((original.classification == 0).sum()), "attack": int((original.classification == 1).sum())},
        {"stage": "after_conflicts", "n": len(no_conflict), "benign": int((no_conflict.classification == 0).sum()), "attack": int((no_conflict.classification == 1).sum())},
        {"stage": "after_exact_dedup", "n": len(dedup), "benign": int((dedup.classification == 0).sum()), "attack": int((dedup.classification == 1).sum())},
        {"stage": "balanced_unfiltered", "n": len(unfiltered), "benign": int((unfiltered.classification == 0).sum()), "attack": int((unfiltered.classification == 1).sum())},
        {"stage": "reconstructed_final", "n": len(work), "benign": int((work.classification == 0).sum()), "attack": int((work.classification == 1).sum())},
    ])
    write_csv(counts, out / "contagens_preparacao.csv")
    write_json({
        "source": str(source), "source_sha256": sha256(source), "n": len(meta),
        "filter_status_counts": observed, "final_matches_existing_raw": True,
        "matrix_sha256": {rep: sha256(path) for rep, path in matrices.items()},
        "wall_seconds": time.perf_counter() - started,
    }, ready)


def load_variant() -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    prepare_srbh_variant()
    folder = HERE / "3_2_srbh_sem_filtros" / "variant"
    meta = pd.read_parquet(folder / "cohort.parquet")
    arrays = {rep: np.load(folder / f"{rep}.npy", mmap_mode="r") for rep in REPS}
    return meta, arrays


def _base_parts(ctx: Context, target: str, seed: int) -> dict[str, pd.DataFrame]:
    split = ctx.split(target, seed)
    result = {name: split[split.split == name].copy() for name in ["train", "validation", "test"]}
    for frame in result.values():
        frame["matrix_origin"] = "base"
        frame["variant_row"] = -1
    return result


def analysis_3_2_target(ctx: Context) -> None:
    out = HERE / "3_2_srbh_sem_filtros" / "como_alvo"
    out.mkdir(parents=True, exist_ok=True)
    variant, arrays = load_variant()
    started = time.perf_counter()
    audit_rows, group_rows = [], []
    for seed in SEEDS:
        parts = _base_parts(ctx, "srbh", seed)
        test_hash = set(variant.canonical_hash)
        purged = {}
        for name in ["train", "validation"]:
            mask = parts[name].canonical_hash.isin(test_hash)
            purged[name] = int(mask.sum())
            parts[name] = parts[name].loc[~mask].copy()
        test = variant.copy()
        audit_rows.append({"seed": seed, "train_purged_new_target_overlap": purged["train"],
                           "validation_purged_new_target_overlap": purged["validation"],
                           "train_n": len(parts["train"]), "validation_n": len(parts["validation"]), "test_n": len(test)})
        for model in MODELS:
            for rep in REPS:
                run_id = f"srbh__{seed}__{model}__{rep}"
                run_path = out / "runs" / f"{run_id}.json"
                group_path = out / "groups" / f"{run_id}.csv"
                if run_path.exists() and group_path.exists():
                    continue
                row, groups = execute_fit(ctx, model, rep, BASE_CONFIG, seed, parts["train"], parts["validation"],
                                          test, arrays, test.filter_group)
                base = ctx.base_row("srbh", seed, model, rep)
                row.update({"analysis": "3.2a", "target": "srbh", "variant": "unfiltered",
                            "article_f1": base.test_f1, "article_pr_auc": base.test_pr_auc,
                            "article_recall": base.test_recall, "article_fpr": base.test_fpr})
                save_run(row, out, run_id)
                groups.insert(0, "representation", rep); groups.insert(0, "model", model); groups.insert(0, "seed", seed)
                write_csv(groups, group_path)
    write_csv(pd.DataFrame(audit_rows), out / "auditoria_splits.csv")
    rows = load_run_rows(out)
    for metric in ["f1", "pr_auc", "recall", "fpr"]:
        rows[f"delta_{metric}"] = rows[f"test_{metric}"] - rows[f"article_{metric}"]
    write_csv(rows.sort_values(["model", "representation", "seed"]), out / "resultados_por_semente.csv")
    mean = rows.groupby(["model", "representation"], as_index=False).agg(
        **{f"unfiltered_{m}": (f"test_{m}", "mean") for m in ["f1", "pr_auc", "recall", "fpr"]},
        **{f"article_{m}": (f"article_{m}", "mean") for m in ["f1", "pr_auc", "recall", "fpr"]},
        **{f"delta_{m}": (f"delta_{m}", "mean") for m in ["f1", "pr_auc", "recall", "fpr"]},
        n_seeds=("seed", "nunique"))
    write_csv(mean, out / "comparacao_media.csv")
    all_groups = pd.concat([pd.read_csv(path) for path in sorted((out / "groups").glob("*.csv"))], ignore_index=True)
    write_csv(all_groups, out / "metricas_grupos_removidos_por_semente.csv")
    write_csv(all_groups.groupby(["model", "representation", "filter_group"], as_index=False).agg(
        n=("n", "first"), f1_attack=("f1_attack", "mean"), recall=("recall", "mean"), fpr=("fpr", "mean"),
        n_seeds=("seed", "nunique")), out / "metricas_grupos_removidos_media.csv")
    write_json({"analysis": "3.2a", "wall_seconds": time.perf_counter() - started,
                "completed_at": pd.Timestamp.now().isoformat()}, out / "tempo_parede.json")


def replace_srbh(parts: dict[str, pd.DataFrame], variant: pd.DataFrame) -> tuple[dict[str, pd.DataFrame], dict]:
    locations = [name for name in ["train", "validation"] if (parts[name].dataset == "srbh").any()]
    if len(locations) != 1:
        raise RuntimeError(f"SRBH deveria estar em uma única partição: {locations}")
    location = locations[0]
    old_n = int((parts[location].dataset == "srbh").sum())
    for name in ["train", "validation"]:
        parts[name] = parts[name][parts[name].dataset != "srbh"].copy()
    candidate = variant.sort_values("row_number").drop_duplicates("canonical_hash").copy()
    target_hash = set(parts["test"].canonical_hash)
    target_overlap = candidate.canonical_hash.isin(target_hash)
    candidate = candidate.loc[~target_overlap].copy()
    existing_hash = set(pd.concat([parts["train"], parts["validation"]]).canonical_hash)
    development_overlap = candidate.canonical_hash.isin(existing_hash)
    candidate = candidate.loc[~development_overlap].copy()
    candidate["split"] = location
    candidate["is_common_test"] = False
    parts[location] = pd.concat([parts[location], candidate], ignore_index=True, sort=False)
    isolate(parts)
    return parts, {"srbh_partition": location, "old_srbh_n": old_n, "new_srbh_n": len(candidate),
                   "variant_internal_canonical_duplicates": len(variant) - variant.canonical_hash.nunique(),
                   "removed_target_overlap": int(target_overlap.sum()),
                   "removed_existing_development_overlap": int(development_overlap.sum())}


def analysis_3_2_source(ctx: Context) -> None:
    out = HERE / "3_2_srbh_sem_filtros" / "como_fonte"
    out.mkdir(parents=True, exist_ok=True)
    variant, arrays = load_variant()
    started = time.perf_counter()
    targets = sorted(set(ctx.master[ctx.master.kind == "lodo"].target.unique()) - {"srbh"})
    audits = []
    for target in targets:
        for seed in SEEDS:
            parts = _base_parts(ctx, target, seed)
            parts, audit = replace_srbh(parts, variant)
            audits.append({"target": target, "seed": seed, **audit})
            for model in MODELS:
                for rep in REPS:
                    run_id = f"{target}__{seed}__{model}__{rep}"
                    if (out / "runs" / f"{run_id}.json").exists():
                        continue
                    row, _ = execute_fit(ctx, model, rep, BASE_CONFIG, seed, parts["train"], parts["validation"],
                                         parts["test"], arrays)
                    base = ctx.base_row(target, seed, model, rep)
                    row.update({"analysis": "3.2b", "target": target, "variant": "srbh_unfiltered_as_source",
                                "article_f1": base.test_f1, "delta_f1": row["test_f1"] - base.test_f1,
                                **audit})
                    save_run(row, out, run_id)
    write_csv(pd.DataFrame(audits).drop_duplicates(["target", "seed"]), out / "auditoria_substituicao.csv")
    rows = load_run_rows(out)
    write_csv(rows.sort_values(["target", "model", "representation", "seed"]), out / "resultados_por_semente.csv")
    by_target = rows.groupby(["target", "model", "representation"], as_index=False).agg(
        article_f1=("article_f1", "mean"), unfiltered_source_f1=("test_f1", "mean"),
        delta_f1=("delta_f1", "mean"), n_seeds=("seed", "nunique"))
    write_csv(by_target, out / "comparacao_por_alvo.csv")
    macro = by_target.groupby(["model", "representation"], as_index=False).agg(
        article_f1_macro=("article_f1", "mean"), unfiltered_source_f1_macro=("unfiltered_source_f1", "mean"),
        delta_f1_macro=("delta_f1", "mean"), n_targets=("target", "nunique"))
    write_csv(macro, out / "comparacao_macro.csv")
    write_json({"analysis": "3.2b", "wall_seconds": time.perf_counter() - started,
                "completed_at": pd.Timestamp.now().isoformat()}, out / "tempo_parede.json")


SENSITIVITY = {
    "logistic_C0.1": ("logistic", {**BASE_CONFIG, "logistic": {"C": 0.1, "max_iter": 500}}),
    "logistic_C10": ("logistic", {**BASE_CONFIG, "logistic": {"C": 10.0, "max_iter": 500}}),
    "catboost_100_d4": ("catboost", {**BASE_CONFIG, "catboost": {"iterations": 100, "depth": 4, "learning_rate": 0.05, "patience": 15}}),
    "catboost_400_d6": ("catboost", {**BASE_CONFIG, "catboost": {"iterations": 400, "depth": 6, "learning_rate": 0.05, "patience": 15}}),
    "mlp_32": ("mlp", {**BASE_CONFIG, "mlp": {"hidden": [32], "epochs": 40, "batch_size": 128, "patience": 6}}),
    "mlp_128_64": ("mlp", {**BASE_CONFIG, "mlp": {"hidden": [128, 64], "epochs": 40, "batch_size": 128, "patience": 6}}),
}


def analysis_3_3(ctx: Context) -> None:
    out = HERE / "3_3_sensibilidade_hiperparametros"
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    targets = sorted(ctx.master[ctx.master.kind == "lodo"].target.unique())
    for config_id, (model, config) in SENSITIVITY.items():
        for target in targets:
            for seed in SEEDS:
                parts = _base_parts(ctx, target, seed)
                for rep in REPS:
                    run_id = f"{config_id}__{target}__{seed}__{rep}"
                    if (out / "runs" / f"{run_id}.json").exists():
                        continue
                    row, _ = execute_fit(ctx, model, rep, config, seed, parts["train"], parts["validation"], parts["test"])
                    row.update({"analysis": "3.3", "config_id": config_id, "target": target,
                                "config": config[model], "id_ood_gap": None,
                                "id_ood_gap_reason": "não calculado: exigiria mais 420 ajustes ID"})
                    save_run(row, out, run_id)
    rows = load_run_rows(out)
    write_csv(rows.drop(columns=["config"], errors="ignore").sort_values(["config_id", "target", "representation", "seed"]),
              out / "resultados_por_semente.csv")
    target = rows.groupby(["config_id", "model", "target", "representation"], as_index=False).agg(
        f1=("test_f1", "mean"), pr_auc=("test_pr_auc", "mean"), recall=("test_recall", "mean"),
        fpr=("test_fpr", "mean"), n_seeds=("seed", "nunique"))
    write_csv(target, out / "resultados_por_alvo.csv")
    macro = target.groupby(["config_id", "model", "representation"], as_index=False).agg(
        f1_macro=("f1", "mean"), n_targets=("target", "nunique"))
    write_csv(macro, out / "f1_macro.csv")
    wide = target.pivot(index=["config_id", "model", "target"], columns="representation", values="f1").reset_index()
    wide["delta_CAN_minus_RAW"] = wide.CANONICALIZED - wide.RAW
    delta = wide.groupby(["config_id", "model"], as_index=False).agg(
        delta_CAN_minus_RAW_mean=("delta_CAN_minus_RAW", "mean"),
        targets_CAN_improved=("delta_CAN_minus_RAW", lambda x: int((x > 0).sum())),
        n_targets=("target", "nunique"))
    write_csv(delta, out / "efeito_canonicalizacao.csv")

    baseline = ctx.master[ctx.master.kind == "lodo"].groupby(["model", "target", "representation"], as_index=False).test_f1.mean()
    baseline_macro = baseline.groupby(["model", "representation"], as_index=False).test_f1.mean()
    scenarios = {
        "baseline": {"logistic": "baseline", "catboost": "baseline", "mlp": "baseline"},
        "lower_capacity": {"logistic": "logistic_C0.1", "catboost": "catboost_100_d4", "mlp": "mlp_32"},
        "higher_capacity": {"logistic": "logistic_C10", "catboost": "catboost_400_d6", "mlp": "mlp_128_64"},
    }
    order_rows = []
    for scenario, mapping in scenarios.items():
        for rep in REPS:
            values = {}
            for model, config_id in mapping.items():
                if config_id == "baseline":
                    values[model] = float(baseline_macro[(baseline_macro.model == model) & (baseline_macro.representation == rep)].test_f1.iloc[0])
                else:
                    values[model] = float(macro[(macro.config_id == config_id) & (macro.representation == rep)].f1_macro.iloc[0])
            ordered = sorted(values, key=values.get, reverse=True)
            order_rows.append({"scenario": scenario, "representation": rep, "order": " > ".join(ordered), **values})
    write_csv(pd.DataFrame(order_rows), out / "ordem_modelos.csv")
    write_json({"analysis": "3.3", "wall_seconds": time.perf_counter() - started,
                "id_ood_gap_calculated": False,
                "reason": "LODO solicitado totalizou 420 fits; gaps válidos exigiriam mais 420 fits ID",
                "completed_at": pd.Timestamp.now().isoformat()}, out / "tempo_parede.json")


def skeleton_tokens(url: str, body: str) -> set[str]:
    url_d = decode_until_stable(clean_url(url)).lower()
    body_d = decode_until_stable(body).lower()
    parsed = urlparse(url_d)
    tokens: set[str] = set()

    def norm(value: object) -> str:
        return re.sub(r"\d", "0", re.sub(r"\s+", " ", str(value).strip().lower()))

    if parsed.path:
        tokens.add("path:" + norm(parsed.path))
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        tokens.add("query:" + norm(key) + "=" + norm(value))
    stripped = body_d.strip()
    if stripped:
        parsed_body = False
        try:
            value = json.loads(stripped)
            parsed_body = True

            def walk(item, path="json"):
                if isinstance(item, dict):
                    for key, child in item.items():
                        walk(child, path + "." + norm(key))
                elif isinstance(item, list):
                    for child in item:
                        walk(child, path + "[]")
                else:
                    tokens.add(path + "=" + norm(item))
            walk(value)
        except Exception:
            pass
        if not parsed_body:
            pairs = parse_qsl(stripped, keep_blank_values=True)
            if pairs and any(key for key, _ in pairs):
                for key, value in pairs:
                    tokens.add("body:" + norm(key) + "=" + norm(value))
            else:
                tokens.add("body_raw:" + norm(stripped))
    return {token for token in tokens if token and token not in {"path:", "body_raw:"}}


def extra_skeletons(ctx: Context) -> None:
    out = HERE / "extra_esqueletos"
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    # Recupera URL/corpo das cópias RAW via row_number.
    from analises_revisao_v2.extrair_analises import load_raw_and_sample_map
    _, samples = load_raw_and_sample_map()
    lookup = samples.set_index("sample_id")
    source_rows, token_rows = [], []
    for target in ["proprio", "artificial_sqli"]:
        split = ctx.split(target, 42)
        development = split[split.split.isin(["train", "validation"])].copy()
        target_rows = ctx.cohort[ctx.cohort.dataset == target].copy()
        target_rows = target_rows.join(lookup[["url_value", "body_value"]], on="sample_id", validate="one_to_one")
        source_token_sets: dict[str, set[str]] = {}
        for source, group in development.groupby("dataset"):
            group = group.join(lookup[["url_value", "body_value"]], on="sample_id", validate="one_to_one")
            source_token_sets[source] = set().union(*(skeleton_tokens(row.url_value, row.body_value) for row in group.itertuples()))
        token_frequency: dict[tuple[str, str], int] = {}
        request_match: dict[str, int] = {source: 0 for source in source_token_sets}
        for row in target_rows.itertuples():
            tokens = skeleton_tokens(row.url_value, row.body_value)
            for source, source_tokens in source_token_sets.items():
                matches = tokens & source_tokens
                if matches:
                    request_match[source] += 1
                for token in matches:
                    token_frequency[(source, token)] = token_frequency.get((source, token), 0) + 1
        for source, count in request_match.items():
            source_rows.append({"target": target, "source": source, "n_target": len(target_rows),
                                "n_requests_with_match": count, "fraction": count / len(target_rows)})
        for (source, token), count in token_frequency.items():
            token_rows.append({"target": target, "source": source, "token": token, "request_frequency": count,
                               "fraction_target": count / len(target_rows), "component": token.split(":", 1)[0],
                               "likely_boilerplate": token.startswith("path:") or ("=" in token and len(token.split("=", 1)[1]) < 4)})
    sources = pd.DataFrame(source_rows)
    tokens = pd.DataFrame(token_rows).sort_values(["target", "request_frequency"], ascending=[True, False])
    tokens["rank_within_target"] = tokens.groupby("target").request_frequency.rank(method="first", ascending=False).astype(int)
    write_csv(sources, out / "coincidencias_por_fonte.csv")
    write_csv(tokens, out / "tokens_coincidentes_todos.csv")
    write_csv(tokens[tokens.rank_within_target <= 10], out / "top10_tokens_por_alvo.csv")
    unique_tokens = (tokens.groupby(["target", "token", "component", "likely_boilerplate"], as_index=False)
                     .agg(request_frequency=("request_frequency", "max"),
                          sources=("source", lambda values: ";".join(sorted(set(values))))))
    unique_tokens = unique_tokens.sort_values(["target", "request_frequency", "token"],
                                              ascending=[True, False, True])
    unique_tokens["rank_within_target"] = unique_tokens.groupby("target").cumcount() + 1
    write_csv(unique_tokens[unique_tokens.rank_within_target <= 10],
              out / "top10_tokens_unicos_por_alvo.csv")
    write_json({"analysis": "extra_esqueletos", "wall_seconds": time.perf_counter() - started,
                "completed_at": pd.Timestamp.now().isoformat()}, out / "tempo_parede.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", choices=["3.1", "3.2-prepare", "3.2a", "3.2b", "3.3", "extra"])
    args = parser.parse_args()
    if args.analysis == "3.2-prepare":
        prepare_srbh_variant()
        return
    context = Context()
    if args.analysis == "3.1": analysis_3_1(context)
    elif args.analysis == "3.2a": analysis_3_2_target(context)
    elif args.analysis == "3.2b": analysis_3_2_source(context)
    elif args.analysis == "3.3": analysis_3_3(context)
    elif args.analysis == "extra": extra_skeletons(context)


if __name__ == "__main__":
    main()
