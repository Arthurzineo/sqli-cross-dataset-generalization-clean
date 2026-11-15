#!/usr/bin/env python3
"""Detached sequential execution with restartable jobs and 20-minute disk reports."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ARTIGO = Path(__file__).resolve().parents[1]
BASE = ARTIGO / 'complementos_generalizacao_v1'
CONTROL = BASE / 'sequence'
SCRIPTS = ARTIGO / 'scripts/supplemental'


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    temporary.replace(path)


def progress():
    counts = Counter()
    active = []
    for path in (BASE / 'full/runs').glob('SUPP_*/status.json'):
        record = json.loads(path.read_text())
        counts[record['status']] += 1
        if record['status'] in ('RUNNING', 'FAILED'):
            active.append({'experiment_id': record['experiment_id'], 'status_file': str(path), **record})
    available = next((int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')), None)
    return {'checked_at': now(), 'counts': dict(counts), 'active_or_failed': active,
            'available_ram_bytes': available, 'free_disk_bytes': shutil.disk_usage(BASE).free}


def execute():
    CONTROL.mkdir(parents=True, exist_ok=True)
    with (CONTROL / 'sequence.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        snapshot = CONTROL / 'source_snapshots' / tag
        files = [*SCRIPTS.glob('*.py'), *SCRIPTS.glob('*.json'), *SCRIPTS.glob('*.md'),
                 *SCRIPTS.glob('*.csv'), Path(__file__).resolve(),
                 * (ARTIGO / 'src').rglob('*.py'), *(ARTIGO / 'config').glob('*.yaml')]
        hashes = {}
        for path in files:
            destination = snapshot / path.relative_to(ARTIGO)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        atomic(snapshot / 'SHA256.json', hashes)
        py = sys.executable
        steps = [
            ('paired', [py, str(SCRIPTS/'run.py'), '--stage', 'paired']),
            ('consolidate_paired', [py, str(SCRIPTS/'consolidate.py')]),
            ('separability', [py, str(SCRIPTS/'run.py'), '--stage', 'separability']),
            ('consolidate_separability', [py, str(SCRIPTS/'consolidate.py')]),
            ('contribution', [py, str(SCRIPTS/'run.py'), '--stage', 'contribution']),
            ('consolidate_final', [py, str(SCRIPTS/'consolidate.py')]),
            ('audit_splits', [py, str(SCRIPTS/'existing_analysis.py'), '--stage', 'audit-splits']),
        ]
        state = {'status': 'RUNNING', 'pid': os.getpid(), 'started_at': now(), 'snapshot': str(snapshot),
                 'completed_stages_this_invocation': [], 'monitor_interval_seconds': 1200,
                 'steps': [{'stage': name, 'command': command} for name, command in steps],
                 'resume': 'Repeat --launch; completed fits are checksum-verified and skipped',
                 'shutdown_at_end': False}
        child = None
        try:
            # Pilot must be successful before any full-scale training starts.
            audit_path = BASE/'pilot_cap_50/analysis/AUDIT.json'
            pilot = json.loads(audit_path.read_text())
            if pilot['completed_runs'] < 4 or pilot['common_test_pairs'] < 2:
                raise RuntimeError('Pilot is incomplete; refusing to start full-scale training')
            for name, command in steps:
                if shutil.disk_usage(BASE).free < 5*2**30:
                    raise RuntimeError('Less than 5 GiB free disk; stopping safely')
                state.update(stage=name, command=command, stage_started_at=now())
                log_path = CONTROL/f'{tag}_{name}.log'
                state['stage_log'] = str(log_path)
                with log_path.open('a') as log:
                    child = subprocess.Popen(command, cwd=ARTIGO.parent, stdin=subprocess.DEVNULL,
                                             stdout=log, stderr=subprocess.STDOUT)
                    state.update(child_pid=child.pid, progress=progress())
                    atomic(CONTROL/'STATE.json', state)
                    print(now(), 'START', name, child.pid, flush=True)
                    next_report = time.monotonic()+1200
                    while True:
                        try:
                            code = child.wait(timeout=60)
                            break
                        except subprocess.TimeoutExpired:
                            state['last_liveness_check'] = now()
                            atomic(CONTROL/'STATE.json', state)
                            if time.monotonic() >= next_report:
                                state['progress'] = progress()
                                atomic(CONTROL/'STATE.json', state)
                                with (CONTROL/'monitor_20min.jsonl').open('a') as history:
                                    history.write(json.dumps({'stage': name, 'child_alive': child.poll() is None,
                                                              **state['progress']})+'\n')
                                print(now(), 'MONITOR', name, state['progress']['counts'], flush=True)
                                next_report = time.monotonic()+1200
                    if code:
                        raise RuntimeError(f'Stage {name} failed with exit code {code}; see {log_path}')
                state['completed_stages_this_invocation'].append(name)
                state['progress'] = progress()
                atomic(CONTROL/'STATE.json', state)
                print(now(), 'COMPLETE', name, flush=True)
            state.update(status='COMPLETED', finished_at=now())
        except BaseException as error:
            state.update(status='FAILED', error=repr(error), finished_at=now())
            atomic(CONTROL/'STATE.json', state)
            raise
        finally:
            atomic(CONTROL/'STATE.json', state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--launch', action='store_true')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.execute:
        execute()
    elif args.launch:
        CONTROL.mkdir(parents=True, exist_ok=True)
        # Check existing supervisor lock before spawning another process.
        with (CONTROL/'sequence.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        command = [sys.executable, str(Path(__file__).resolve()), '--execute']
        if shutil.which('systemd-inhibit'):
            command = ['systemd-inhibit', '--what=sleep', '--mode=block', '--who=SQLi-complementos',
                       '--why=Experimentos sequenciais de generalizacao', *command]
        with (CONTROL/'supervisor.log').open('a') as log:
            process = subprocess.Popen(command, cwd=ARTIGO.parent, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        print(json.dumps({'launcher_pid': process.pid, 'state_file': str(CONTROL/'STATE.json'),
                          'log_file': str(CONTROL/'supervisor.log')}, indent=2))
    else:
        print((CONTROL/'STATE.json').read_text() if (CONTROL/'STATE.json').exists() else 'Not started')


if __name__ == '__main__':
    main()
