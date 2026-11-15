import hashlib
import re
from urllib.parse import unquote_plus, urlparse
import pandas as pd

from src.utils.config import ROOT, datasets_config


def decode_until_stable(value, passes=10):
    text = "" if pd.isna(value) else str(value)
    for _ in range(passes):
        new = unquote_plus(text)
        if new == text: break
        text = new
    return text


def clean_url(value):
    value = "" if pd.isna(value) else re.sub(r"\s+HTTP/1\.[01]\s*$", "", str(value))
    parsed = urlparse(value)
    return parsed.path + (("?" + parsed.query) if parsed.query else "") + (("#" + parsed.fragment) if parsed.fragment else "")


def make_text(url, body, decode=True):
    url = clean_url(url)
    body = "" if pd.isna(body) or str(body) == "nan" else str(body)
    text = (url + " " + body).strip()
    return decode_until_stable(text) if decode else text


def digest(text):
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def canonical(text):
    decoded = decode_until_stable(text).casefold()
    return re.sub(r"\s+", " ", decoded).strip()


def dataset_path(dataset_id, representation):
    spec = datasets_config()[dataset_id]
    if representation not in {"raw", "decoded"}:
        raise ValueError("representation deve ser 'raw' ou 'decoded'")
    source_key = f"{representation}_source"
    path = (ROOT / spec[source_key]).resolve()
    if not path.is_file():
        availability = spec.get("availability", "não informada")
        raise FileNotFoundError(
            f"Base {dataset_id!r} ({availability}) não encontrada em {path}. "
            "Consulte docs/reproducibility.md."
        )
    return path


def load_dataset(dataset_id, representation="decoded"):
    spec = datasets_config()[dataset_id]
    path = dataset_path(dataset_id, representation)
    frame = pd.read_csv(path, sep=spec["separator"], encoding=spec["encoding"], keep_default_na=False, low_memory=False)
    url_col, body_col = spec["text_columns"]
    label_col = spec["label_column"]
    labels = pd.to_numeric(frame[label_col], errors="raise").astype("int8")
    if not set(labels.unique()) <= {0, 1}: raise ValueError(f"Rótulos inválidos em {dataset_id}")
    texts = [make_text(u, b, decode=(representation == "decoded")) for u, b in zip(frame[url_col], frame[body_col])]
    raw_texts = [(clean_url(u) + " " + str(b)).strip() for u, b in zip(frame[url_col], frame[body_col])]
    result = pd.DataFrame({
        "dataset": dataset_id, "family": spec["family"], "row_number": range(1, len(frame) + 1),
        "y": labels.to_numpy(), "url": frame[url_col].astype(str), "body": frame[body_col].astype(str), "text": texts,
    })
    result["raw_input_hash"] = [digest(value) for value in raw_texts]
    result["decoded_input_hash"] = [digest(decode_until_stable(value)) for value in raw_texts]
    result["text_hash"] = result.text.map(digest)
    result["canonical_hash"] = result.text.map(lambda value: digest(canonical(value)))
    result["sample_id"] = [digest(f"{representation}:{dataset_id}:{row}:{value}") for row, value in zip(result.row_number, result.text_hash)]
    return result


def load_many(dataset_ids, representation="decoded"):
    return pd.concat([load_dataset(value, representation) for value in dataset_ids], ignore_index=True)
