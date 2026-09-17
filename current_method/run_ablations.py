"""Run the two attribution experiments without replacing any earlier result."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import pandas as pd

from atlas_new.ablations import run_world
from atlas_new.ablation_report import summarize, validate, write_report
from atlas_new.workflow import tasks

ROOT = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['smoke','full'], default='full')
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    if args.workers<1:
        parser.error('--workers must be positive')
    cfg = json.loads((ROOT/'configs/workflow_full.json').read_text())
    cfg.update(profile='ablations_'+args.profile, workers=args.workers,
               schedules=['random','nearest'], modes=['r2','rinf'],
               bootstrap_seed=2026091702, bootstrap_repetitions=2000)
    if args.profile == 'smoke':
        cfg['repetitions_per_cell'] = 3
        cfg['bootstrap_repetitions'] = 100
    out = ROOT/'results'/cfg['profile']
    out.mkdir(parents=True, exist_ok=False)
    files = [Path(__file__), ROOT/'atlas_new/ablations.py', ROOT/'atlas_new/ablation_report.py',
             ROOT/'atlas_new/workflow.py', ROOT/'atlas_new/core.py', ROOT/'configs/workflow_full.json',
             ROOT/'tests/test_ablations.py', ROOT/'docs/ablation_protocol.md']
    manifest = dict(status='running', config=cfg, started_utc=datetime.now(timezone.utc).isoformat(),
                    command=sys.argv, python=sys.version, platform=platform.platform(),
                    packages={n:importlib.metadata.version(n) for n in ['numpy','scipy','pandas']},
                    source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
                    scope='Post-review attribution on existing synthetic DGP; no ExAtlas comparison; local optimization.')
    target = out/'run_manifest.json'
    def checkpoint():
        target.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    checkpoint()
    started = time.perf_counter()
    try:
        test = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'], cwd=ROOT,
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        (out/'test_log.txt').write_text(test.stdout+test.stderr, encoding='utf-8')
        if test.returncode:
            raise AssertionError('Tests failed')
        rows, plans = [], []
        jobs = tasks(cfg)
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_world, t) for t in jobs]
            for n, future in enumerate(as_completed(futures), 1):
                r, p = future.result(); rows.extend(r); plans.extend(p)
                if n%50 == 0 or n==len(jobs):
                    print(f'Worlds {n}/{len(jobs)}; {time.perf_counter()-started:.1f}s', flush=True)
        keys = ['surface','scenario','replicate','schedule','mode','method']
        frame = pd.DataFrame(rows).sort_values(keys+['tolerance','budget'])
        frame.to_csv(out/'records.csv', index=False, float_format='%.15g')
        plans.sort(key=lambda r:tuple(r[k] for k in keys)+ (r['stage'],))
        with (out/'plans.jsonl').open('w', encoding='utf-8') as f:
            for p in plans:
                f.write(json.dumps(p, allow_nan=False)+'\n')
        manifest['counts'] = dict(worlds=len(jobs), records=len(rows), planned_states=len(plans))
        manifest['checks'] = validate(cfg, frame, pd.DataFrame(plans), out)
        summarize(cfg, frame, pd.DataFrame(plans), out)
        write_report(cfg, out)
        manifest['status'] = 'complete'
    except Exception as error:
        manifest.update(status='failed', error=repr(error))
        raise
    finally:
        manifest.update(finished_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.perf_counter()-started)
        manifest['artifacts'] = {p.name:dict(sha256=sha(p), bytes=p.stat().st_size)
                                 for p in out.iterdir() if p.is_file() and p!=target}
        checkpoint()
    print('COMPLETE', out, flush=True)


if __name__ == '__main__':
    main()
