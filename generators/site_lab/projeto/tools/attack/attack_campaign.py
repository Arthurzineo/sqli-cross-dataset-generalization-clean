#!/usr/bin/env python3
"""Orchestrate the isolated phase-22 attack window and final labeled dataset."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_LOGS = ROOT / "logs"
FINAL_LOGS = ROOT / "log"
DATASET_DIR = ROOT / "dataset"
EVIDENCE = DATASET_DIR / "evidence"
LAB = RUNTIME_LOGS / "lab.jsonl"
BENIGN = FINAL_LOGS / "benigno.jsonl"
ATTACK = FINAL_LOGS / "malicioso.jsonl"
DATASET = DATASET_DIR / "dataset_final.jsonl"
MANIFEST = DATASET_DIR / "manifesto.json"
VALIDATION = DATASET_DIR / "validacao.json"
PRE_ATTACK = EVIDENCE / "log_antes_ataque.jsonl"
DIAGNOSTICS = EVIDENCE / "diagnosticos_pre_ataque.jsonl"
STATE = EVIDENCE / "estado_campanha.json"
REJECTED = EVIDENCE / "transporte_rejeitado.jsonl"
TOOL_LOGS = EVIDENCE / "ferramentas"
BENIGN_COUNT = 30113
ATTACK_TARGET = 30000
COMPOSE = ["docker", "compose", "--project-directory", str(ROOT), "--profile", "attack-tools"]


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as source:
        return sum(1 for _ in source)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_json(STATE, state)


def ensure_services() -> None:
    for directory in (RUNTIME_LOGS, FINAL_LOGS, DATASET_DIR, EVIDENCE):
        directory.mkdir(parents=True, exist_ok=True)
    subprocess.run(COMPOSE + ["up", "--detach", "app", "nginx"], check=True)
    subprocess.run(COMPOSE + ["up", "--detach", "--no-deps", "kali-tools"], check=True)
    container = subprocess.check_output(COMPOSE + ["ps", "--status", "running", "--quiet", "kali-tools"], text=True).strip()
    if not container:
        raise RuntimeError("kali-tools nao esta em execucao")


def prepare_window(state: dict) -> None:
    if state.get("prepared"):
        return
    if any(path.exists() for path in (BENIGN, PRE_ATTACK, ATTACK, DATASET, MANIFEST)):
        raise RuntimeError("artefatos de campanha ja existem; recusei sobrescrever")
    lines = LAB.read_bytes().splitlines(keepends=True)
    if len(lines) < BENIGN_COUNT:
        raise RuntimeError(f"lab.jsonl possui somente {len(lines)} linhas; benigno requer {BENIGN_COUNT}")
    PRE_ATTACK.write_bytes(b"".join(lines))
    BENIGN.write_bytes(b"".join(lines[:BENIGN_COUNT]))
    DIAGNOSTICS.write_bytes(b"".join(lines[BENIGN_COUNT:]))
    # Truncation keeps the inode that Nginx already has open. All previous bytes were
    # preserved above before the attack-label window begins.
    LAB.write_bytes(b"")
    state.update({
        "prepared": True,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "benign_count": BENIGN_COUNT,
        "pre_attack_count": len(lines),
        "diagnostic_count": len(lines) - BENIGN_COUNT,
        "tool_stages": {},
        "injector_rounds": [],
    })
    save_state(state)


def run_tool(state: dict, name: str, args: list[str], timeout: int) -> None:
    if name in state["tool_stages"]:
        return
    TOOL_LOGS.mkdir(parents=True, exist_ok=True)
    before = line_count(LAB)
    started = datetime.now(timezone.utc).isoformat()
    with (TOOL_LOGS / f"{name}.log").open("w", encoding="utf-8") as output:
        try:
            completed = subprocess.run(
                [str(ROOT / "tools" / "kali_toolbox.sh"), "run", *args],
                stdout=output, stderr=subprocess.STDOUT, text=True, timeout=timeout, check=False,
            )
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
    time.sleep(1)
    after = line_count(LAB)
    state["tool_stages"][name] = {
        "started_at": started, "finished_at": datetime.now(timezone.utc).isoformat(),
        "return_code": return_code, "requests": after - before, "args": args,
    }
    save_state(state)


def run_injector(state: dict, count: int, round_number: int) -> None:
    before = line_count(LAB)
    command = COMPOSE + [
        "exec", "-T", "-e", "LAB_ATTACK_CONFIRM=phase22", "kali-tools",
        "attack-injector", "--count", str(count), "--offset", str(before),
        "--seed", str(2200 + round_number), "--workers", "16", "--rate", "120",
        "--manifest", f"/workspace/attack-injector-{round_number}.manifest.json", "--execute",
    ]
    TOOL_LOGS.mkdir(parents=True, exist_ok=True)
    with (TOOL_LOGS / f"injector-{round_number}.log").open("w", encoding="utf-8") as output:
        completed = subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, text=True, timeout=1800, check=False)
    time.sleep(1)
    after = line_count(LAB)
    state["injector_rounds"].append({
        "round": round_number, "requested": count, "logged": after - before,
        "return_code": completed.returncode, "before": before, "after": after,
    })
    save_state(state)


def remove_invalid_transport_records(state: dict) -> int:
    """Drop malformed Nginx request-line records while preserving their evidence."""
    if not LAB.exists():
        return 0
    valid: list[bytes] = []
    rejected: list[bytes] = []
    for line in LAB.read_bytes().splitlines(keepends=True):
        try:
            row = json.loads(line.decode("utf-8", errors="surrogateescape"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            rejected.append(line)
            continue
        if row.get("request_method") in {"GET", "POST"} and row.get("request_uri"):
            valid.append(line)
        else:
            rejected.append(line)
    if not rejected:
        return 0
    # Open/truncate the existing inode: Nginx keeps this file open while the lab runs.
    with LAB.open("wb") as destination:
        destination.writelines(valid)
    with REJECTED.open("ab") as destination:
        destination.writelines(rejected)
    state.setdefault("rejected_transport_records", 0)
    state["rejected_transport_records"] += len(rejected)
    state["rejected_artifact"] = str(REJECTED)
    save_state(state)
    return len(rejected)


def finalize(state: dict) -> dict:
    count = line_count(LAB)
    if count != ATTACK_TARGET:
        raise RuntimeError(f"janela de ataque esperada={ATTACK_TARGET}, obtida={count}")
    shutil.copyfile(LAB, ATTACK)
    validation_command = [
        sys.executable, str(ROOT / "tools" / "attack" / "validate_dataset.py"),
        "--benign", str(BENIGN), "--attack", str(ATTACK), "--output", str(DATASET),
        "--report", str(VALIDATION), "--expected-benign", str(BENIGN_COUNT),
        "--expected-attack", str(ATTACK_TARGET),
    ]
    subprocess.run(validation_command, check=True, stdout=subprocess.DEVNULL)
    validation = json.loads(VALIDATION.read_text())
    manifest = {
        "campaign": "attack_campaign_01", "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "target": "https://nginx", "isolated_container": "kali-tools",
        "tool_stages": state["tool_stages"], "injector_rounds": state["injector_rounds"],
        "repair": state.get("repair"),
        "artifacts": {
            "benign": str(BENIGN), "attack": str(ATTACK), "dataset": str(DATASET),
            "validation": str(VALIDATION), "pre_attack_backup": str(PRE_ATTACK),
            "pre_attack_diagnostics": str(DIAGNOSTICS),
            "rejected_transport_records": str(REJECTED) if REJECTED.exists() else None,
        },
        "validation": validation,
    }
    write_json(MANIFEST, manifest)
    state["completed"] = True
    save_state(state)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"mode": "plan", "benign": BENIGN_COUNT, "attack": ATTACK_TARGET, "uses_antigravity": False}, indent=2))
        return 0
    ensure_services()
    state = load_state()
    prepare_window(state)
    # Small, bounded contributions from each installed tool. Return code 124 is an expected
    # bounded timeout; the exact remaining count is filled by attack-injector afterwards.
    stages = [
        ("ffuf-get", ["ffuf", "get-search", "--rate", "20", "--threads", "2", "--max-seconds", "15"], 60),
        ("ffuf-post", ["ffuf", "post-login-json", "--rate", "20", "--threads", "2", "--max-seconds", "15"], 60),
        ("wfuzz-get", ["wfuzz", "get-docs", "--rate", "20", "--threads", "2", "--max-seconds", "15"], 60),
        ("wfuzz-post", ["wfuzz", "post-graphql-json", "--rate", "20", "--threads", "2", "--max-seconds", "15"], 60),
        ("sqlmap-get", ["sqlmap", "get-search", "--rate", "10", "--threads", "1", "--max-seconds", "30", "--tamper", "space2comment"], 90),
        ("sqlmap-post", ["sqlmap", "post-login-json", "--rate", "10", "--threads", "1", "--max-seconds", "30", "--tamper", "randomcase"], 90),
    ]
    for name, tool_args, timeout in stages:
        run_tool(state, name, tool_args, timeout)
        if line_count(LAB) >= ATTACK_TARGET:
            break
    for round_number in range(1, 11):
        remove_invalid_transport_records(state)
        remaining = ATTACK_TARGET - line_count(LAB)
        if remaining <= 0:
            break
        run_injector(state, remaining, round_number)
        remove_invalid_transport_records(state)
    remove_invalid_transport_records(state)
    manifest = finalize(state)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
