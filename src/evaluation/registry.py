import csv
import fcntl
from pathlib import Path

FIELDS = ["experiment_id","experiment_key","chapter","status","script","config","target","training_pool","model",
          "representation","feature_set","seed","started_at","finished_at","runtime","result_path","notes"]
_terminal_keys = {}


def append(path, row):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a+", newline="", encoding="utf-8") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0, 2); empty = stream.tell() == 0
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        if empty: writer.writeheader()
        writer.writerow({field: row.get(field) for field in FIELDS})
    if row.get("status") in {"COMPLETED", "SKIPPED"} and path in _terminal_keys:
        _terminal_keys[path].add(row.get("experiment_key"))


def completed(path, experiment_key):
    path = Path(path)
    if not path.exists(): return False
    if path not in _terminal_keys:
        import json
        keys = set()
        with open(path, newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                if row["status"] not in {"COMPLETED", "SKIPPED"}: continue
                status_path=path.parents[2]/"runs/status"/f"{row['experiment_id']}.json"
                if status_path.exists() and json.loads(status_path.read_text()).get("status")==row["status"]:
                    keys.add(row["experiment_key"])
        _terminal_keys[path] = keys
    return experiment_key in _terminal_keys[path]
