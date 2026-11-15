#!/usr/bin/env python
"""Autonomous benign traffic campaign runner for the English cooking wiki.

Objetivo: gerar ~TARGET requisicoes no Nginx (lab.jsonl) rodando sessoes benignas do
generator.py. Live content agents are optional; validated English cooking fallbacks keep
the high-volume campaign deterministic when no agent pool is configured.

Caracteristicas:
- Inicio imediato por padrao; START_HHMM e opcional.
- RESUMIVEL: gera TARGET requisicoes adicionais a partir do contador inicial.
- Self-healing: reinicia o content service se cair.
- Loga progresso em tools/traffic/campaign/progress.log.
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # projeto/
TRAFFIC = ROOT / "tools" / "traffic"
CAMPAIGN_DIR = TRAFFIC / "campaign"
CAMPAIGN_DIR.mkdir(parents=True, exist_ok=True)
LAB = ROOT / "logs" / "lab.jsonl"
PROGRESS = CAMPAIGN_DIR / "progress.log"
CS_LOG = CAMPAIGN_DIR / "content_service.log"
GEN_LOG = CAMPAIGN_DIR / "generator.log"

TARGET = int(os.environ.get("CAMPAIGN_TARGET", "30000"))
START_HHMM = os.environ.get("CAMPAIGN_START", "").strip()   # optional HHMM local
BASE_URL = os.environ.get("TRAFFIC_BASE_URL", "https://localhost:8444")
CONTENT_PORT = os.environ.get("TRAFFIC_CONTENT_PORT", "8877")
BATCH_SESSIONS = int(os.environ.get("CAMPAIGN_BATCH_SESSIONS", "24"))
BATCH_CONCURRENCY = int(os.environ.get("CAMPAIGN_CONCURRENCY", "6"))
PY = os.environ.get("CAMPAIGN_PY", sys.executable)


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with PROGRESS.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def lab_count() -> int:
    try:
        with LAB.open("r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
    except FileNotFoundError:
        return 0


def app_up() -> bool:
    try:
        r = subprocess.run(["curl", "-sk", "-o", os.devnull, "-w", "%{http_code}",
                            f"{BASE_URL}/"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() == "200"
    except Exception:
        return False


def ensure_app() -> None:
    if app_up():
        return
    log("app fora do ar -> docker compose up -d")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(ROOT), capture_output=True, text=True)
    for _ in range(30):
        if app_up():
            log("app no ar")
            return
        time.sleep(2)
    log("AVISO: app nao subiu")


def start_content_service() -> subprocess.Popen:
    env = dict(os.environ)
    env.setdefault("TRAFFIC_AGENTS", "")
    env.setdefault("TRAFFIC_AGENT_TIMEOUT", "80")
    env["TRAFFIC_CONTENT_PORT"] = CONTENT_PORT
    env["PYTHONUNBUFFERED"] = "1"
    fh = CS_LOG.open("a", encoding="utf-8")
    proc = subprocess.Popen([PY, "-u", str(TRAFFIC / "content_service.py")],
                            cwd=str(ROOT), env=env, stdout=fh, stderr=subprocess.STDOUT)
    mode = "live validated agents" if env["TRAFFIC_AGENTS"] else "validated English cooking fallbacks"
    log(f"content service iniciado (pid {proc.pid}) mode={mode}")
    return proc


def run_batch() -> int:
    env = dict(os.environ)
    env["TRAFFIC_BASE_URL"] = BASE_URL
    env["TRAFFIC_CONTENT_URL"] = f"http://127.0.0.1:{CONTENT_PORT}"
    env.setdefault("TRAFFIC_PAUSE_MIN", "0.02")
    env.setdefault("TRAFFIC_PAUSE_MAX", "0.08")
    env["PYTHONUNBUFFERED"] = "1"
    fh = GEN_LOG.open("a", encoding="utf-8")
    r = subprocess.run([PY, "-u", str(TRAFFIC / "generator.py"),
                        "--sessions", str(BATCH_SESSIONS), "--concurrency", str(BATCH_CONCURRENCY)],
                       cwd=str(ROOT), env=env, stdout=fh, stderr=subprocess.STDOUT, timeout=3600)
    return r.returncode


def wait_until_start() -> None:
    if not START_HHMM:
        return
    log(f"aguardando ate {START_HHMM} para iniciar a campanha (alvo {TARGET})...")
    while datetime.now().strftime("%H%M") < START_HHMM:
        time.sleep(20)


def main() -> int:
    wait_until_start()
    log(f"=== CAMPANHA INICIADA (alvo {TARGET} requisicoes) ===")
    ensure_app()

    # The runtime log is not reset: TARGET means new requests beyond this baseline.
    start_count = lab_count()
    target_count = start_count + TARGET
    log(f"lab.jsonl comeca em {start_count} linhas")

    cs = start_content_service()
    batches = 0
    try:
        while True:
            count = lab_count()
            log(f"progresso: +{count - start_count} / +{TARGET} (total={count})")
            if count >= target_count:
                log("*** ALVO ATINGIDO ***")
                break
            ensure_app()
            # content service vivo?
            if cs.poll() is not None:
                log("content service caiu -> reiniciando")
                cs = start_content_service()
            try:
                rc = run_batch()
                if rc != 0:
                    log(f"batch retornou rc={rc} (segue)")
            except Exception as e:
                log(f"batch falhou: {e} (retry em 10s)")
                time.sleep(10)
            batches += 1
    finally:
        try:
            cs.terminate()
        except Exception:
            pass
    log(f"=== CAMPANHA FINALIZADA: {lab_count()} linhas no lab.jsonl ({batches} batches) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
