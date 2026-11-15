from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import socket
import subprocess


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    def compatible(item):
        if isinstance(item, Path): return str(item)
        if isinstance(item, set): return sorted(item)
        try:
            import numpy as np
            if isinstance(item, np.generic): return item.item()
            if isinstance(item, np.ndarray): return item.tolist()
        except ImportError:
            pass
        raise TypeError(f"{type(item).__name__} não é serializável em JSON")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=compatible))
    temporary.replace(path)


def git_commit(root):
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def hardware():
    memory = None
    try:
        memory = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError):
        pass
    gpu, cuda = None, None
    try:
        output = subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"], text=True)
        gpu = output.strip().splitlines()
    except Exception:
        pass
    try:
        import torch
        cuda = torch.version.cuda
    except Exception:
        pass
    return {"hostname": socket.gethostname(), "os": platform.platform(), "python": platform.python_version(),
            "cpu_count": os.cpu_count(), "ram_bytes": memory, "gpu": gpu, "cuda": cuda}


def software_versions():
    result = {}
    for package in ["numpy", "pandas", "scikit-learn", "scipy", "catboost", "torch", "transformers", "PyYAML", "matplotlib"]:
        try: result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError: result[package] = None
    return result


def stable_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
