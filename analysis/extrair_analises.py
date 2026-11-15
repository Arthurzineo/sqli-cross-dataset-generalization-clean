#!/usr/bin/env python3
"""Auditoria derivada para responder aos comentários da orientadora.

Somente lê artefatos existentes e escreve dentro de analises_revisao_v2/.
Não treina modelos. As agregações seguem: sementes primeiro, alvos depois.
"""
from __future__ import annotations

import ast
import json
import math
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, unquote_plus, urlparse

import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import f1_score, recall_score


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analises_revisao_v2"
ARTICLE = ROOT / "artigo"
CONTROL = ARTICLE / "complementos_generalizacao_v1" / "full"
CONTROL_ANALYSIS = ARTICLE / "analise_resultados_tcc" / "SUPPLEMENTAL_CONTROLLED_ANALYSIS"
HIST_ANALYSIS = ARTICLE / "analise_resultados_tcc" / "ADDITIONAL_MANUSCRIPT_ANALYSES"
HIST_MASTER = ARTICLE / "analise_resultados_tcc" / "_global" / "master_results.parquet"
SQL = ["select", "union", "insert", "update", "delete", "drop", "where", "from", "or", "and",
       "exec", "order", "by", "waitfor", "delay", "cast", "table", "database", "like"]
XSS = ["script", "alert", "javascript", "onerror", "onload", "document", "cookie", "src", "iframe",
       "style", "background", "location", "eval", "prompt"]
CHARACTERS = ["sq", "dq", "lt", "gt", "lparen", "rparen", "semicolon", "equals", "amp", "pct",
              "plus", "minus", "star", "slash", "pipe", "hash", "quest", "at", "colon", "comma",
              "dot", "space"]


def save(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    frame.to_csv(OUT / name, index=False)
    return frame


def listish(value) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value]
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except Exception:
        pass
    return [x for x in text.split("+") if x]


def clean_url(value) -> str:
    value = "" if pd.isna(value) else re.sub(r"\s+HTTP/1\.[01]\s*$", "", str(value))
    parsed = urlparse(value)
    return parsed.path + (("?" + parsed.query) if parsed.query else "") + (("#" + parsed.fragment) if parsed.fragment else "")


def decode(value: str, limit: int = 10) -> str:
    text = "" if pd.isna(value) else str(value)
    for _ in range(limit):
        new = unquote_plus(text)
        if new == text:
            break
        text = new
    return text


def decode_passes(value: str, limit: int = 10) -> tuple[int, bool]:
    """Número de chamadas até estabilidade; 1 significa que a primeira não mudou."""
    text = "" if pd.isna(value) else str(value)
    for step in range(1, limit + 1):
        new = unquote_plus(text)
        if new == text:
            return step, False
        text = new
    return limit, unquote_plus(text) != text


def metric_row(y: np.ndarray, pred: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    pred = np.asarray(pred, dtype=int)
    tn = int(((y == 0) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum())
    return {
        "n": len(y),
        "f1": float(f1_score(y, pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y, pred, pos_label=1, zero_division=0)),
        "fpr": fp / (fp + tn) if fp + tn else np.nan,
    }


def source_contribution() -> None:
    per = pd.read_parquet(CONTROL_ANALYSIS / "derived/source_contribution_per_seed.parquet")
    cols = ["target", "model", "representation", "seed", "removed_source", "full_f1", "removed_f1", "delta_f1",
            "full_pr_auc", "removed_pr_auc", "delta_pr_auc", "full_recall", "removed_recall", "delta_recall",
            "full_fpr", "removed_fpr", "delta_fpr"]
    save(per[(per.target == "csic") & (per.removed_source == "artificial_sqli")][cols]
         .sort_values(["model", "representation", "seed"]), "1_1a_csic_sem_artificial_por_semente.csv")
    save(per[per.removed_source == "artificial_sqli"][cols]
         .sort_values(["target", "model", "representation", "seed"]), "1_1b_artificial_por_alvo.csv")
    save(per[per.target == "csic"][cols]
         .sort_values(["removed_source", "model", "representation", "seed"]), "1_1b_fontes_para_csic.csv")

    master = pd.read_parquet(CONTROL / "analysis/master_results.parquet")
    lodo = master[(master.kind == "lodo") & (master.target == "csic")].copy()
    lodo["artificial_na_validacao"] = lodo.validation_sources.map(lambda x: "artificial_sqli" in listish(x))
    seeds = lodo[["seed", "validation_sources", "artificial_na_validacao"]].drop_duplicates()
    save(seeds.sort_values("seed"), "1_1c_artificial_validacao_csic.csv")

    additions = pd.read_parquet(HIST_ANALYSIS / "derived/matched_source_additions_per_seed.parquet")
    a = additions[additions.added_source == "artificial_sqli"].copy()
    # Sementes dentro da mesma aresta; arestas dentro de alvo/modelo/vista; alvo por último.
    edge = a.groupby(["target", "model", "representation", "base_sources"], as_index=False).agg(
        delta_f1=("delta_f1", "mean"), n_seeds=("seed", "nunique"))
    by_target = edge.groupby(["target", "model", "representation"], as_index=False).agg(
        delta_f1_mean=("delta_f1", "mean"), n_contexts=("base_sources", "nunique"), n_seeds_min=("n_seeds", "min"))
    by_target["group"] = np.where(by_target.target == "csic", "csic", "outros_alvos")
    save(by_target, "1_1d_historico_artificial_por_alvo_modelo_vista.csv")
    overall = by_target.groupby("target", as_index=False).agg(delta_f1_mean=("delta_f1_mean", "mean"))
    compare = pd.DataFrame([
        {"grupo": "csic", "delta_f1_mean": overall.loc[overall.target == "csic", "delta_f1_mean"].mean(),
         "n_alvos": int((overall.target == "csic").sum())},
        {"grupo": "outros_alvos", "delta_f1_mean": overall.loc[overall.target != "csic", "delta_f1_mean"].mean(),
         "n_alvos": int((overall.target != "csic").sum())},
    ])
    save(compare, "1_1d_historico_csic_vs_outros.csv")


def historical_validation() -> None:
    master = pd.read_parquet(HIST_MASTER)
    h = master[(master.experiment_type == "contribution") & master.usable.fillna(False)].copy()
    meta = pd.read_csv(ARTICLE / "docs/method_inconsistency_evidence/B_validation_source_metadata.csv")
    h = h.merge(meta[["experiment_id", "source_overlap"]], on="experiment_id", how="left", validate="one_to_one")
    h["validation_strategy"] = np.where(h.source_overlap, "GroupShuffleSplit", "familia_retida")
    h["n_sources"] = h.n_effective_sources.astype(int)
    save(
        h[["experiment_id", "target_dataset", "model", "representation", "seed", "n_sources", "validation_strategy"]]
        .sort_values(["n_sources", "validation_strategy", "target_dataset", "model", "representation", "seed"]),
        "1_2a_validacao_historica_por_execucao.csv",
    )
    counts = h.groupby(["n_sources", "validation_strategy"]).size().unstack(fill_value=0).reset_index()
    save(counts, "1_2a_validacao_historica_contagens.csv")

    # Média de sementes por coalizão antes de coalizões/alvos.
    keys = ["target_dataset", "model", "representation", "effective_development_datasets", "n_sources", "validation_strategy"]
    coalition = h.groupby(keys, as_index=False).agg(f1=("f1", "mean"), threshold_drift=("threshold_drift", "mean"),
                                                    oracle_gap=("oracle_gap", "mean"), n_seeds=("seed", "nunique"))
    target = coalition.groupby(["target_dataset", "model", "representation", "n_sources", "validation_strategy"], as_index=False).agg(
        f1=("f1", "mean"), threshold_drift=("threshold_drift", "mean"), oracle_gap=("oracle_gap", "mean"),
        n_coalitions=("effective_development_datasets", "nunique"), n_seeds_min=("n_seeds", "min"))
    result = target.groupby(["model", "representation", "n_sources", "validation_strategy"], as_index=False).agg(
        f1_ood_macro=("f1", "mean"), threshold_drift_macro=("threshold_drift", "mean"),
        oracle_gap_macro=("oracle_gap", "mean"), n_targets=("target_dataset", "nunique"))
    both = result.groupby(["model", "representation", "n_sources"]).validation_strategy.transform("nunique") == 2
    save(result[both], "1_2b_metricas_por_estrategia.csv")

    coal = pd.read_parquet(HIST_ANALYSIS / "derived/effective_coalition_seed_results.parquet")
    train_sets = coal.actual_training_sources.map(lambda x: set(listish(x)))
    val_sets = coal.validation_sources.map(lambda x: set(listish(x)))
    coal["validation_strategy"] = ["GroupShuffleSplit" if a & b else "familia_retida" for a, b in zip(train_sets, val_sets)]
    def curve(frame: pd.DataFrame, label: str) -> pd.DataFrame:
        t = frame.groupby(["target", "model", "representation", "n_sources"], as_index=False).f1.mean()
        z = t.groupby(["model", "representation", "n_sources"], as_index=False).agg(
            f1_macro=("f1", "mean"), n_targets=("target", "nunique"))
        z["curve"] = label
        return z
    curves = pd.concat([curve(coal, "original"), curve(coal[coal.validation_strategy == "familia_retida"], "somente_familia_retida")])
    pivot = curves.pivot_table(index=["model", "representation", "n_sources"], columns="curve", values="f1_macro").reset_index()
    if {"original", "somente_familia_retida"} <= set(pivot.columns):
        pivot["delta_retida_menos_original"] = pivot.somente_familia_retida - pivot.original
    save(curves, "1_2c_curvas_validacao.csv")
    save(pivot, "1_2c_comparacao_curvas.csv")


def statistical_tests() -> None:
    tests = pd.read_parquet(CONTROL_ANALYSIS / "statistics/tests_holm.parquet")
    per = pd.read_parquet(CONTROL_ANALYSIS / "derived/source_contribution_per_seed.parquet")
    details = per.groupby(["removed_source", "model", "representation"], as_index=False).agg(
        n_alvos=("target", "nunique"), n_pares_semente=("seed", "size"), n_sementes_distintas=("seed", "nunique"),
        sementes_min_por_alvo=("seed", lambda x: int(x.groupby(per.loc[x.index, "target"]).nunique().min())),
        sementes_max_por_alvo=("seed", lambda x: int(x.groupby(per.loc[x.index, "target"]).nunique().max())))
    details["comparison"] = details.removed_source + " " + details.model + " " + details.representation
    s = tests[tests.family == "source_contribution"].merge(details, on="comparison", how="left", validate="one_to_one")
    save(s.drop(columns=["experiment_ids"]), "1_3a_testes_contribuicao_42.csv")
    save(tests[tests.family == "id_ood_gap"].drop(columns=["experiment_ids"]), "1_3c_testes_lacuna_id_ood.csv")
    save(tests[tests.family == "cross_rq_associations"].drop(columns=["experiment_ids"]), "1_3c_testes_associacoes_22.csv")


def load_raw_and_sample_map() -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    cfg = yaml.safe_load((ARTICLE / "config/datasets.yaml").read_text())["datasets"]
    cohort_path = next((CONTROL / "cache").glob("*/cohort.parquet"))
    cohort = pd.read_parquet(cohort_path)
    frames: dict[str, pd.DataFrame] = {}
    pieces = []
    for dataset in sorted(cohort.dataset.unique()):
        spec = cfg[dataset]
        path = ARTICLE / "datasets/original_copies/raw" / spec["raw_file"]
        raw = pd.read_csv(path, sep=spec["separator"], encoding=spec["encoding"], keep_default_na=False, low_memory=False)
        ucol, bcol = spec["text_columns"]
        raw = raw.copy()
        raw["row_number"] = np.arange(1, len(raw) + 1)
        raw["url_value"] = raw[ucol].astype(str)
        raw["body_value"] = raw[bcol].astype(str)
        raw["raw_text"] = [f"{clean_url(u)} {b}".strip() for u, b in zip(raw.url_value, raw.body_value)]
        raw["canonical_text"] = raw.raw_text.map(decode)
        frames[dataset] = raw
        c = cohort[cohort.dataset == dataset].merge(raw[["row_number", "url_value", "body_value", "raw_text", "canonical_text"]],
                                                     on="row_number", how="left", validate="one_to_one")
        pieces.append(c)
    return frames, pd.concat(pieces, ignore_index=True)


def canonical_passes_and_marker(frames: dict[str, pd.DataFrame], samples: pd.DataFrame) -> None:
    rows = []
    for dataset, frame in frames.items():
        label_col = yaml.safe_load((ARTICLE / "config/datasets.yaml").read_text())["datasets"][dataset]["label_column"]
        labels = pd.to_numeric(frame[label_col]).astype(int)
        values = frame.raw_text.map(decode_passes)
        steps = values.map(lambda x: x[0])
        limit = values.map(lambda x: x[1])
        for y in [0, 1]:
            s = steps[labels == y]
            lim = limit[labels == y]
            counts = Counter("4+" if x >= 4 else str(x) for x in s)
            total = len(s)
            rows.append({"dataset": dataset, "classe": "malicioso" if y else "benigno", "n": total,
                         **{f"passagens_{k}_n": counts.get(k, 0) for k in ["1", "2", "3", "4+"]},
                         **{f"passagens_{k}_pct": counts.get(k, 0) / total if total else np.nan for k in ["1", "2", "3", "4+"]},
                         "max_passagens": int(s.max()) if total else np.nan, "atingiu_limite_10": int(lim.sum())})
    save(pd.DataFrame(rows), "1_4_passagens_canonicalizacao.csv")

    marker_rows = []
    for dataset, frame in frames.items():
        spec = yaml.safe_load((ARTICLE / "config/datasets.yaml").read_text())["datasets"][dataset]
        labels = pd.to_numeric(frame[spec["label_column"]]).astype(int)
        found = frame.raw_text.str.contains("INJECTED_PARAM", case=False, regex=False)
        for y in [0, 1]:
            marker_rows.append({"dataset": dataset, "classe": "malicioso" if y else "benigno",
                                "n_injected_param": int((found & (labels == y)).sum()), "n_classe": int((labels == y).sum())})
    save(pd.DataFrame(marker_rows), "1_5a_1_5c_injected_param_por_base.csv")


def predictions_analyses(samples: pd.DataFrame) -> None:
    master = pd.read_parquet(CONTROL / "analysis/master_results.parquet")
    lodo = master[master.kind == "lodo"].copy()
    lookup = samples.set_index("sample_id")[["dataset", "row_number", "y", "raw_text", "canonical_text"]]
    csic_rows, keyword_rows = [], []
    keyword_re = re.compile(r"\b(?:" + "|".join(map(re.escape, SQL)) + r")\b", flags=re.I)
    for run in lodo.itertuples():
        pred = pd.read_parquet(CONTROL / "runs" / run.experiment_id / "predictions.parquet")
        pred = pred[pred.role == "test"].copy()
        pred = pred.join(lookup, on="sample_id", rsuffix="_lookup", validate="one_to_one")
        pred["yhat"] = (pred.score >= pred.threshold).astype(int)
        if run.target == "csic":
            keep = ~pred.raw_text.str.contains("INJECTED_PARAM", case=False, regex=False)
            full = metric_row(pred.y.to_numpy(), pred.yhat.to_numpy())
            clean = metric_row(pred.loc[keep, "y"].to_numpy(), pred.loc[keep, "yhat"].to_numpy())
            csic_rows.append({"model": run.model, "representation": run.representation, "seed": run.seed,
                              **{f"artigo_{k}": v for k, v in full.items()}, **{f"sem_marker_{k}": v for k, v in clean.items()},
                              "delta_f1": clean["f1"] - full["f1"], "delta_recall": clean["recall"] - full["recall"],
                              "delta_fpr": clean["fpr"] - full["fpr"]})
        benign = pred[pred.y == 0].copy()
        text_col = "canonical_text" if run.representation == "CANONICALIZED" else "raw_text"
        benign["tem_keyword_sql"] = benign[text_col].str.contains(keyword_re)
        for flag, group in benign.groupby("tem_keyword_sql"):
            keyword_rows.append({"target": run.target, "model": run.model, "representation": run.representation,
                                 "seed": run.seed, "grupo": "com_keyword_sql" if flag else "sem_keyword_sql",
                                 "n": len(group), "fp": int(group.yhat.sum()), "fpr": float(group.yhat.mean())})
    csic = pd.DataFrame(csic_rows)
    save(csic, "1_5b_csic_sem_injected_param_por_semente.csv")
    metric_columns = [column for column in csic.columns if column not in {"model", "representation", "seed"}]
    summary = csic.groupby(["model", "representation"], as_index=False)[metric_columns].mean()
    summary = summary.merge(
        csic.groupby(["model", "representation"]).size().rename("n_seeds").reset_index(),
        on=["model", "representation"],
        validate="one_to_one",
    )
    save(summary, "1_5b_csic_sem_injected_param_resumo.csv")
    kw = pd.DataFrame(keyword_rows)
    save(kw, "1_6ab_fpr_keywords_por_semente.csv")
    save(kw.groupby(["target", "model", "representation", "grupo"], as_index=False).agg(
        n=("n", "first"), fpr_media_sementes=("fpr", "mean"), fpr_dp_sementes=("fpr", "std")),
         "1_6ab_fpr_keywords_resumo.csv")


def skeleton_token(url: str, body: str) -> set[str]:
    """Esqueleto operacional: nome/caminho do parâmetro + valor canonicalizado com dígitos->0.

    Query, form e JSON são estruturados. Sem estrutura, usa caminho e/ou corpo como fallback.
    Não tenta decidir semanticamente qual trecho é ataque.
    """
    url_d, body_d = decode(clean_url(url)), decode(body)
    parsed = urlparse(url_d)
    tokens: set[str] = set()
    norm = lambda x: re.sub(r"\s+", " ", re.sub(r"\d", "0", str(x).casefold())).strip()
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        tokens.add("query:" + norm(key) + "=" + norm(value))
    structured_body = False
    if body_d.strip():
        try:
            obj = json.loads(body_d)
            structured_body = True
            def walk(value, path="json"):
                if isinstance(value, dict):
                    for k, v in value.items(): walk(v, path + "." + norm(k))
                elif isinstance(value, list):
                    for v in value: walk(v, path + "[]")
                else: tokens.add(path + "=" + norm(value))
            walk(obj)
        except Exception:
            pairs = parse_qsl(body_d, keep_blank_values=True)
            if pairs and ("=" in body_d or "&" in body_d):
                structured_body = True
                for key, value in pairs: tokens.add("body:" + norm(key) + "=" + norm(value))
        if not structured_body:
            tokens.add("body=" + norm(body_d))
    if not tokens and parsed.path:
        tokens.add("path=" + norm(parsed.path))
    return {x for x in tokens if x and not x.endswith("=")}


def skeleton_similarity(samples: pd.DataFrame) -> None:
    work = samples[["sample_id", "dataset", "family", "y", "url_value", "body_value"]].copy()
    work["tokens"] = [skeleton_token(u, b) for u, b in zip(work.url_value, work.body_value)]
    token_map = work.set_index("sample_id").tokens.to_dict()
    master = pd.read_parquet(CONTROL / "analysis/master_results.parquet")
    rows = []
    for target in sorted(work.dataset.unique()):
        run = master[(master.kind == "lodo") & (master.target == target) & (master.model == "catboost") &
                     (master.representation == "RAW") & (master.seed == 42)].iloc[0]
        split = pd.read_parquet(CONTROL / "splits" / f"{run.split_id}.parquet")
        source_ids = split.loc[split.split.isin(["train", "validation"]), "sample_id"]
        source_tokens = set().union(*(token_map.get(x, set()) for x in source_ids)) if len(source_ids) else set()
        target_part = work[work.dataset == target]
        for y in [0, 1]:
            g = target_part[target_part.y == y]
            has = g.tokens.map(bool)
            matched = g.tokens.map(lambda x: bool(x & source_tokens))
            rows.append({"target": target, "classe": "malicioso" if y else "benigno", "n": len(g),
                         "n_com_esqueleto_extraido": int(has.sum()), "cobertura_extracao": float(has.mean()),
                         "n_com_match": int(matched.sum()), "fracao_match_total": float(matched.mean()),
                         "fracao_match_entre_extraidos": float(matched[has].mean()) if has.any() else np.nan,
                         "split_referencia": run.split_id, "seed_referencia": 42})
    save(pd.DataFrame(rows), "1_7_similaridade_esqueletos.csv")


def id_stratification_and_groups(samples: pd.DataFrame) -> None:
    master = pd.read_parquet(CONTROL / "analysis/master_results.parquet")
    unique = master[master.kind == "id"][["target", "seed", "split_id"]].drop_duplicates()
    rows = []
    for r in unique.itertuples():
        split = pd.read_parquet(CONTROL / "splits" / f"{r.split_id}.parquet")
        for name, g in split.groupby("split"):
            rows.append({"target": r.target, "seed": r.seed, "split": name, "n": len(g),
                         "n_ataques": int(g.y.sum()), "proporcao_ataques": float(g.y.mean()), "split_id": r.split_id})
    save(pd.DataFrame(rows).sort_values(["target", "seed", "split"]), "1_8a_estratificacao_id.csv")
    rows = []
    for dataset, g in samples.groupby("dataset"):
        sizes = g.groupby("canonical_hash").size()
        for bucket, mask in [("1", sizes == 1), ("2", sizes == 2), ("3+", sizes >= 3)]:
            rows.append({"dataset": dataset, "tamanho_grupo": bucket, "n_grupos": int(mask.sum()),
                         "n_requisicoes": int(sizes[mask].sum()), "max_tamanho": int(sizes.max())})
    save(pd.DataFrame(rows), "1_8b_tamanho_grupos_equivalentes.csv")


def xss_importance() -> None:
    features = ["xss_" + x for x in XSS]
    controlled = pd.read_parquet(CONTROL_ANALYSIS / "derived/feature_importance_per_run.parquet")
    c = controlled[controlled.feature.isin(features)].copy()
    csum = c.groupby(["target", "representation", "seed", "kind", "removed_source"], dropna=False).importance_pct.sum().reset_index(name="xss_group_pct")
    save(c.groupby(["kind", "representation", "feature"], as_index=False).agg(
        posto_medio=("rank", "mean"), frequencia_top10=("top10", "mean"), importancia_media_pct=("importance_pct", "mean"),
        n_modelos=("experiment_ids", "size")), "1_9_xss_controlado_por_feature.csv")
    save(csum.groupby(["kind", "representation"], as_index=False).agg(
        importancia_grupo_media_pct=("xss_group_pct", "mean"), n_modelos=("xss_group_pct", "size")),
         "1_9_xss_controlado_grupo.csv")

    hi = pd.read_parquet(ARTICLE / "analise_resultados_tcc/M04_09_Feature_Stability__C05_06_RQ3_Feature_Stability/derived/selected_feature_importances.parquet")
    hm = pd.read_parquet(HIST_MASTER)[["experiment_id", "experiment_type", "representation", "target_dataset"]]
    hi = hi.merge(hm, on="experiment_id", how="left", validate="many_to_one")
    hi["scope"] = hi.experiment_type.replace({"lodo_C_complete": "lodo"})
    totals = hi.groupby("experiment_id").importance.transform("sum")
    hi["importance_pct"] = 100 * hi.importance / totals
    hi["top10"] = hi["rank"] <= 10
    hx = hi[hi.feature.isin(features)].copy()
    hsum = hx.groupby(["experiment_id", "scope", "representation"], as_index=False).importance_pct.sum().rename(columns={"importance_pct": "xss_group_pct"})
    save(hx.groupby(["scope", "representation", "feature"], as_index=False).agg(
        posto_medio=("rank", "mean"), frequencia_top10=("top10", "mean"), importancia_media_pct=("importance_pct", "mean"),
        n_modelos=("experiment_id", "nunique")), "1_9_xss_historico_por_feature.csv")
    save(hsum.groupby(["scope", "representation"], as_index=False).agg(
        importancia_grupo_media_pct=("xss_group_pct", "mean"), n_modelos=("experiment_id", "nunique")),
         "1_9_xss_historico_grupo.csv")


def feature_origin() -> None:
    rows = []
    for x in CHARACTERS:
        rows.append({"feature": "char_" + x, "grupo": "caractere", "origem": "herdado_extrator_anterior",
                     "observacao": "Mesmo nome e cálculo do extrair_features_artificial.py."})
    for x in SQL:
        rows.append({"feature": "sql_" + x, "grupo": "palavra_chave_SQL", "origem": "herdado_extrator_anterior",
                     "observacao": "Mesmo vocabulário e fronteira de palavra do extrator anterior."})
    rows += [
        {"feature": "sql_comment_dash", "grupo": "comentario_SQL", "origem": "herdado_extrator_anterior", "observacao": "Mesmo cálculo."},
        {"feature": "sql_comment_block", "grupo": "comentario_SQL", "origem": "herdado_extrator_anterior", "observacao": "Mesmo cálculo."},
    ]
    for x in XSS:
        rows.append({"feature": "xss_" + x, "grupo": "termo_web_XSS", "origem": "herdado_extrator_anterior",
                     "observacao": "Mesmo vocabulário e fronteira de palavra do extrator anterior."})
    for x in ["len_total", "ratio_digits", "ratio_nonalnum", "enc_pct", "path_traversal", "entropy"]:
        rows.append({"feature": x, "grupo": "estrutural_estatistico", "origem": "herdado_extrator_anterior",
                     "observacao": "Mesmo nome e fórmula; o pré-processamento textual passou de duas decodificações para iteração até estabilidade."})
    rows.append({"feature": "path_depth", "grupo": "estrutural_estatistico", "origem": "herdado_modificado",
                 "observacao": "Anterior contava barras no path parseado; atual conta barras na URL armazenada."})
    d = pd.DataFrame(rows)
    d["referencia_literatura_no_codigo"] = "não encontrada"
    d["fonte_anterior"] = "../datasets/extrair_features_artificial.py:44-89"
    d["fonte_atual"] = "artigo/src/features/lexical.py:6-36"
    save(d, "2_1_origem_64_atributos.csv")


def runtime_plan() -> None:
    master = pd.read_parquet(CONTROL / "analysis/master_results.parquet")
    lodo = master[master.kind == "lodo"]
    contribution = master[master.kind == "contribution_fixed_validation"]
    catcan = master[(master.model == "catboost") & (master.representation == "CANONICALIZED") &
                    master.kind.isin(["lodo", "contribution_fixed_validation"])]
    rows = [
        {"analise": "3.1 CatBoost CAN size-control", "execucoes_novas": len(catcan),
         "referencia_segundos": catcan.runtime_seconds.sum(), "criterio": "35 LODO completos + 164 remoções; soma observada dos mesmos tipos CatBoost/CAN"},
        {"analise": "3.2 SRBH como alvo", "execucoes_novas": 30,
         "referencia_segundos": lodo[lodo.target == "srbh"].runtime_seconds.sum(), "criterio": "3 modelos x 2 vistas x 5 sementes; soma observada do alvo SRBH filtrado"},
        {"analise": "3.2 SRBH não filtrado como fonte", "execucoes_novas": 180,
         "referencia_segundos": lodo[lodo.target != "srbh"].runtime_seconds.sum() * (178584 / 106580),
         "criterio": "6 alvos x 3 modelos x 2 vistas x 5; escala linear conservadora pelo volume 178584/106580"},
        {"analise": "3.3 grid 2 configs totais/modelo", "execucoes_novas": 210,
         "referencia_segundos": lodo.runtime_seconds.sum(), "criterio": "baseline existente + uma configuração nova; uma bateria LODO completa"},
        {"analise": "3.3 grid 3 configs totais/modelo", "execucoes_novas": 420,
         "referencia_segundos": 2 * lodo.runtime_seconds.sum(), "criterio": "baseline existente + duas configurações novas; duas baterias LODO completas"},
    ]
    hist = pd.read_parquet(HIST_MASTER)
    meta = pd.read_csv(ARTICLE / "docs/method_inconsistency_evidence/B_validation_source_metadata.csv")
    h = hist[(hist.experiment_type == "contribution") & hist.usable.fillna(False)].merge(
        meta[["experiment_id", "source_overlap"]], on="experiment_id", validate="one_to_one")
    fallback_small = h[h.source_overlap & (h.n_effective_sources <= 2)]
    fallback_two_sources = h[h.source_overlap & (h.n_effective_sources == 2)]
    rows.append({"analise": "3.4 refazer fallbacks composições <=2", "execucoes_novas": len(fallback_small),
                 "referencia_segundos": fallback_small.runtime.sum(),
                 "criterio": "execuções históricas existentes com overlap treino/validação e <=2 fontes; n=1 não admite família inteira retida"})
    rows.append({"analise": "3.4 mínimo viável: fallbacks com 2 fontes", "execucoes_novas": len(fallback_two_sources),
                 "referencia_segundos": fallback_two_sources.runtime.sum(),
                 "criterio": "somente as composições de 2 fontes, nas quais uma fonte inteira pode ser retida para validação"})
    plan = pd.DataFrame(rows)
    plan["referencia_horas"] = plan.referencia_segundos / 3600
    save(plan, "3_planejamento_custos.csv")


def sr_bh_counts() -> None:
    rows = [
        ("seleção CAPEC-66 ou Normal", 525195, 250311, "preparar_srbh.py"),
        ("remoção de conflitos", 501524, 244403, "deduplicar.py"),
        ("deduplicação", 89292, 184112, "deduplicar.py"),
        ("1º balanceamento", 89292, 89292, "deduplicar.py"),
        ("corte 1: sem indicador SQL", 89292, 82249, "deduplicar_codificados.py:64-66"),
        ("rebalanceamento 1", 82249, 82249, "deduplicar_codificados.py:65"),
        ("corte 2: sem padrão SQL estrito", 82249, 74851, "deduplicar_codificados.py:68-71"),
        ("rebalanceamento 2", 74851, 74851, "deduplicar_codificados.py:70"),
        ("corte 3: benignos com padrão de ataque", 53290, 74851, "deduplicar_codificados.py:73-79"),
        ("rebalanceamento final", 53290, 53290, "deduplicar_codificados.py:78"),
    ]
    save(pd.DataFrame([{"etapa": a, "benignos": b, "maliciosos": m, "total": b + m, "fonte": f} for a, b, m, f in rows]),
         "2_5_srbh_contagens_raw.csv")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    source_contribution()
    historical_validation()
    statistical_tests()
    frames, samples = load_raw_and_sample_map()
    canonical_passes_and_marker(frames, samples)
    predictions_analyses(samples)
    skeleton_similarity(samples)
    id_stratification_and_groups(samples)
    xss_importance()
    feature_origin()
    runtime_plan()
    sr_bh_counts()
    print(f"Saídas gravadas em {OUT}")


if __name__ == "__main__":
    main()
