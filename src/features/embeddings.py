import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from src.data.loader import dataset_path, load_dataset
from src.utils.config import ROOT, models_config
from src.utils.provenance import atomic_json, sha256, stable_hash


def cache_directory(model_name="codebert"):
    config = models_config()[model_name]
    identity = stable_hash({key: config[key] for key in ("model", "revision", "max_length", "pooling")})[:16]
    return ROOT / "datasets/processed/embeddings" / f"{model_name}_{identity}"


def cache_stem(dataset_id, representation):
    content_hash=sha256(dataset_path(dataset_id,representation))
    return f"{dataset_id}_{representation}_{content_hash[:16]}",content_hash


def extract_dataset(dataset_id, representation="decoded", model_name="codebert", batch_size=None, device=None,
                    resume=True):
    """Extract frozen embeddings. The cache key includes input and model configuration."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    config = models_config()[model_name]
    output = cache_directory(model_name)
    output.mkdir(parents=True, exist_ok=True)
    stem,input_file_sha256 = cache_stem(dataset_id,representation)
    matrix_path, index_path, metadata_path = output / f"{stem}.npy", output / f"{stem}.csv", output / f"{stem}.json"
    if resume and all(path.exists() for path in (matrix_path, index_path, metadata_path)):
        return matrix_path
    frame = load_dataset(dataset_id, representation)
    tokenizer = AutoTokenizer.from_pretrained(config["model"], revision=config["revision"])
    encoder = AutoModel.from_pretrained(config["model"], revision=config["revision"])
    selected_device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    encoder.to(selected_device).eval()
    if selected_device.startswith("cuda"):
        torch.cuda.reset_peak_memory_stats()
    batch = int(batch_size or config.get("batch_size", 8)); maximum = int(config["max_length"])
    vectors, truncated, effective_batches = [], [], []
    started = time.perf_counter(); cursor = 0
    while cursor < len(frame):
        current = min(batch, len(frame) - cursor)
        texts = frame.text.iloc[cursor:cursor + current].tolist()
        try:
            lengths = tokenizer(texts, add_special_tokens=True, truncation=False, return_length=True)["length"]
            encoded = tokenizer(texts, padding=True, truncation=True, max_length=maximum, return_tensors="pt")
            encoded = {key: value.to(selected_device) for key, value in encoded.items()}
            with torch.inference_mode():
                hidden = encoder(**encoded).last_hidden_state
                if config["pooling"] == "mean":
                    mask = encoded["attention_mask"].unsqueeze(-1)
                    pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1)
                else:
                    pooled = hidden[:, 0, :]
            vectors.append(pooled.float().cpu().numpy())
            truncated.extend(int(length > maximum) for length in lengths)
            effective_batches.append(current); cursor += current
        except RuntimeError as error:
            if "out of memory" not in str(error).lower() or current == 1:
                raise
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            batch = max(1, current // 2)
    matrix = np.concatenate(vectors).astype("float32")
    np.save(matrix_path, matrix)
    frame[["sample_id", "dataset", "y", "text_hash", "canonical_hash"]].assign(
        embedding_row=np.arange(len(frame)), truncated=truncated).to_csv(index_path, index=False)
    atomic_json(metadata_path, {"dataset": dataset_id, "representation": representation, "model": config,
        "n": len(frame), "dimensions": int(matrix.shape[1]), "input_file_sha256":input_file_sha256,
        "truncated_n": int(sum(truncated)),
        "truncated_fraction": float(np.mean(truncated)), "requested_batch_size": batch_size or config.get("batch_size", 8),
        "final_configured_batch_size":batch,"smallest_observed_batch_including_last_partial":min(effective_batches), "device": selected_device,
        "elapsed_seconds": time.perf_counter() - started,
        "peak_vram_mib": float(torch.cuda.max_memory_allocated()/1024**2) if selected_device.startswith("cuda") else None})
    del encoder
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return matrix_path


def load_cached(dataset_ids, representation="decoded", model_name="codebert"):
    directory = cache_directory(model_name); matrices, indices = [], []
    offset = 0
    for dataset_id in dataset_ids:
        stem,_ = cache_stem(dataset_id,representation)
        matrix = np.load(directory / f"{stem}.npy", mmap_mode="r")
        index = pd.read_csv(directory / f"{stem}.csv")
        if len(matrix) != len(index):
            raise ValueError(f"Cache inconsistente para {dataset_id}")
        matrices.append(np.asarray(matrix)); indices.append(index.assign(global_row=np.arange(len(index)) + offset))
        offset += len(index)
    return np.concatenate(matrices), pd.concat(indices, ignore_index=True)
