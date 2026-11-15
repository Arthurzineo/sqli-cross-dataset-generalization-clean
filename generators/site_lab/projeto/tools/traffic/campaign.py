#!/usr/bin/env python
"""Autonomous benign traffic campaign runner (Fase 21, Opcao 1: agentes ao vivo).

Objetivo: gerar ~TARGET requisicoes no Nginx (lab.jsonl) rodando sessoes benignas do
generator.py, com conteudo ao vivo dos agentes Codex + Antigravity (content service pool).

Caracteristicas:
- Espera ate START_HHMM (default 18:00) para comecar.
- RESUMIVEL: continua ate lab.jsonl >= TARGET, entao pode ser relancado se cair.
- Self-healing: reinicia o content service se cair; re-detecta o handle do Antigravity
  (que muda quando o terminal reabre) periodicamente.
- Loga progresso em tools/traffic/campaign/progress.log.
"""
import json
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

ORCA_CMD = os.environ.get("ORCA_CMD", "orca")
CODEX_HANDLE = "term_c63c4431-a18c-4632-a54e-54f2317e1a95"

TARGET = int(os.environ.get("CAMPAIGN_TARGET", "30000"))
START_HHMM = os.environ.get("CAMPAIGN_START", "1800")   # HHMM local
BASE_URL = os.environ.get("TRAFFIC_BASE_URL", "https://localhost:8443")
CONTENT_PORT = os.environ.get("TRAFFIC_CONTENT_PORT", "8765")
BATCH_SESSIONS = int(os.environ.get("CAMPAIGN_BATCH_SESSIONS", "6"))
BATCH_CONCURRENCY = int(os.environ.get("CAMPAIGN_CONCURRENCY", "3"))
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


def orca_json(args):
    try:
        out = subprocess.run(["cmd.exe", "/d", "/s", "/c", ORCA_CMD, *args],
                             capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=30)
        return json.loads(out.stdout)
    except Exception:
        return None


def detect_antigravity() -> str | None:
    """Descobre o handle do terminal do Antigravity (muda quando reabre)."""
    ps = orca_json(["worktree", "ps", "--json"])
    tl = orca_json(["terminal", "list", "--json"])
    if not ps or not tl:
        return None
    # paneKey do agente antigravity = "<tabId>:<leafId>"
    tab_ids = set()
    for wt in ps.get("result", {}).get("worktrees", []):
        if wt.get("repo") != "SQLI":
            continue
        for ag in wt.get("agents", []):
            if ag.get("agentType") == "antigravity":
                pk = ag.get("paneKey", "")
                if ":" in pk:
                    tab_ids.add(pk.split(":", 1)[0])
    for t in tl.get("result", {}).get("terminals", []):
        if t.get("tabId") in tab_ids:
            return t.get("handle")
    # fallback: procurar por preview/banner Antigravity
    for t in tl.get("result", {}).get("terminals", []):
        if "SQLI" in (t.get("worktreePath") or "") and "Antigravity" in (t.get("preview") or ""):
            return t.get("handle")
    return None


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


def start_content_service(ag_handle: str) -> subprocess.Popen:
    env = dict(os.environ)
    env["TRAFFIC_AGENTS"] = f"antigravity:{ag_handle},codex:{CODEX_HANDLE}"
    env["TRAFFIC_AGENT_TIMEOUT"] = "80"
    env["TRAFFIC_CONTENT_PORT"] = CONTENT_PORT
    env["PYTHONUNBUFFERED"] = "1"
    fh = CS_LOG.open("a", encoding="utf-8")
    proc = subprocess.Popen([PY, "-u", str(TRAFFIC / "content_service.py")],
                            cwd=str(ROOT), env=env, stdout=fh, stderr=subprocess.STDOUT)
    log(f"content service iniciado (pid {proc.pid}) agents=antigravity:{ag_handle[-6:]},codex")
    return proc


def run_batch() -> int:
    env = dict(os.environ)
    env["TRAFFIC_BASE_URL"] = BASE_URL
    env["TRAFFIC_CONTENT_URL"] = f"http://127.0.0.1:{CONTENT_PORT}"
    env["PYTHONUNBUFFERED"] = "1"
    fh = GEN_LOG.open("a", encoding="utf-8")
    r = subprocess.run([PY, "-u", str(TRAFFIC / "generator.py"),
                        "--sessions", str(BATCH_SESSIONS), "--concurrency", str(BATCH_CONCURRENCY)],
                       cwd=str(ROOT), env=env, stdout=fh, stderr=subprocess.STDOUT, timeout=3600)
    return r.returncode


def wait_until_start() -> None:
    log(f"aguardando ate {START_HHMM} para iniciar a campanha (alvo {TARGET})...")
    while datetime.now().strftime("%H%M") < START_HHMM:
        time.sleep(20)


def main() -> int:
    wait_until_start()
    log(f"=== CAMPANHA INICIADA (alvo {TARGET} requisicoes) ===")
    ensure_app()

    ag = detect_antigravity() or "term_5f483217-ddc4-421d-bd47-cd08f7ad5686"
    log(f"handle Antigravity detectado: {ag}")

    # log NAO e zerado aqui (o coordenador zera antes); campanha e RESUMIVEL
    start_count = lab_count()
    log(f"lab.jsonl comeca em {start_count} linhas")

    cs = start_content_service(ag)
    batches = 0
    try:
        while True:
            count = lab_count()
            log(f"progresso: {count} / {TARGET} (+{count - start_count})")
            if count >= TARGET:
                log("*** ALVO ATINGIDO ***")
                break
            ensure_app()
            # content service vivo?
            if cs.poll() is not None:
                log("content service caiu -> reiniciando")
                cs = start_content_service(ag)
            # re-detectar Antigravity a cada 15 batches (handle pode mudar)
            if batches and batches % 15 == 0:
                new_ag = detect_antigravity()
                if new_ag and new_ag != ag:
                    log(f"handle Antigravity mudou: {ag} -> {new_ag}, reiniciando content service")
                    ag = new_ag
                    try:
                        cs.terminate()
                    except Exception:
                        pass
                    cs = start_content_service(ag)
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
