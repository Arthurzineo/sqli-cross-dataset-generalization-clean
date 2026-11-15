"""Runtime configuration for the laboratory application."""

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("LAB_DB_PATH", str(PROJECT_ROOT / "db" / "lab.db"))
HOST = os.environ.get("LAB_HOST", "127.0.0.1")
PORT = int(os.environ.get("LAB_PORT", "5000"))
JWT_SECRET = os.environ.get("LAB_JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("LAB_JWT_SECRET must be set in the environment")
