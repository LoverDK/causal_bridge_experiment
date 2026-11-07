"""Run new complete prefixes and paired original stopping rules in a fresh directory."""
import os
for variable in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[variable] = '1'

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import pandas as pd

from atlas_new.cost_precision import ROW_KEYS, WORLD_KEYS, run_world, validate_outputs
from atlas_new.workflow import tasks


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args):
    result = subprocess.run(['git', *args], cwd=REPO, capture_output=True,
                            text=True, encoding='utf-8', errors='replace')
    return result.stdout.strip() if result.returncode == 0 else None


def write_jsonl(path, records, sort_keys):
    records.sort(key=lambda row: tuple(row[key] for key in sort_keys))
    with path.open('w', encoding='utf-8', newline='\n') as handle:
        for row in records:
            handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['smoke', 'full'], required=True)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    cfg_path = ROOT/'configs'/f'cost_precision_{args.profile}.json'
    cfg = json.loads(cfg_path.read_text('utf-8'))
    cfg['workers'] = args.workers
    if cfg['dimension'] != 2 or cfg['initial_sources'] != 4 or cfg['candidate_bridges'] != 6:
        raise ValueError('This experiment preserves the original 2D, 4-source, 6-candidate DGP')
    if args.workers < 1 or cfg['max_bridges'] != 3:
        raise ValueError('Use at least one worker and the frozen three-batch horizon')
    out = args.output.resolve()
    if out.exists():
        raise FileExistsError(f'Preserve previous outputs; choose a new directory: {out}')
    out.mkdir(parents=True)
    sources = [ROOT/'run_cost_precision.py', ROOT/'atlas_new'/'cost_precision.py',
               ROOT/'atlas_new'/'workflow.py', ROOT/'atlas_new'/'core.py', cfg_path,
               ROOT/'tests'/'test_cost_precision.py', ROOT/'tests'/'test_workflow.py']
    for relative in ['revision/FIRST_WORKFLOW.md', 'revision/COST_PRECISION_RUN01.md']:
        if (REPO/relative).exists():
            sources.append(REPO/relative)
    snapshot = out/'source_snapshot'
    for source in sources:
        target = snapshot/source.relative_to(REPO)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    manifest = dict(
        schema_version='1.0', status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        command=[sys.executable, *sys.argv], config=cfg,
        git_revision=git_value('rev-parse', 'HEAD'), git_status_before_run=git_value('status', '--short'),
        python=sys.version, platform=platform.platform(),
        packages={name: importlib.metadata.version(name) for name in ['numpy','scipy','pandas','matplotlib']},
        source_sha256={source.relative_to(REPO).as_posix(): digest(source) for source in sources},
        modes={'prefix':'Actual complete acquisition prefix, no early stop, static remains zero cost',
               'stopped':'Unchanged legacy execute(); stop at first original-radius release'},
        score_scope='All truth is used only by the generator and separated scorer; no outcome-adaptive planning',
        reliability_scope='Nominal 90% per-policy, per-mode finite-path coverage under the declared DGP; not conditional-on-release or across-policy coverage',
        cost_scope='Additional randomized-trial participants only; historical, calibration and deployment costs excluded',
        acquisition_log_scope='Mode/tolerance rows reuse paired source streams; repeated rows are not independent experiments',
        calibration_provenance='199 scores per world independently reconstructed from frozen generator seed and checked against generator quantile',
        scope='New synthetic cost-precision experiment; no real mechanism calibration, no universal superiority claim')
    manifest_path = out/'run_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    started = time.perf_counter()
    try:
        test_logs = []
        for pattern in ['test_workflow.py', 'test_cost_precision.py']:
            result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v'],
                                    cwd=ROOT, capture_output=True, encoding='utf-8', errors='replace')
            test_logs.append(f'PATTERN {pattern}\n{result.stdout}{result.stderr}')
            (out/'test_log.txt').write_text('\n'.join(test_logs), encoding='utf-8')
            if result.returncode:
                raise AssertionError(f'Tests failed: {pattern}; see test_log.txt')
        jobs = tasks(cfg)
        buffers = {key: [] for key in ['prefix_records','stopped_records','acquisitions','plans','candidate_scores']}
        audits, calibrations = [], []
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(run_world, job) for job in jobs]
            for n, future in enumerate(as_completed(futures), 1):
                result = future.result()
                for key in buffers:
                    buffers[key].extend(result[key])
                audits.append(result['world_audit'])
                calibrations.append(result['calibration'])
                if n % 25 == 0 or n == len(jobs):
                    print(f'Worlds {n}/{len(jobs)}; elapsed {time.perf_counter()-started:.1f}s', flush=True)
        for name in ['prefix_records', 'stopped_records']:
            pd.DataFrame(buffers[name]).sort_values(ROW_KEYS).to_csv(
                out/f'{name}.csv', index=False, float_format='%.15g')
        pd.DataFrame(buffers['acquisitions']).sort_values(
            ['mode']+WORLD_KEYS+['method','tolerance','stage']).to_csv(
                out/'acquisitions.csv', index=False, float_format='%.15g')
        pd.DataFrame(buffers['candidate_scores']).sort_values(
            WORLD_KEYS+['method','stage','candidate']).to_csv(
                out/'candidate_scores.csv', index=False, float_format='%.15g')
        write_jsonl(out/'plans.jsonl', buffers['plans'], WORLD_KEYS+['method','stage'])
        write_jsonl(out/'world_audits.jsonl', audits, WORLD_KEYS)
        write_jsonl(out/'calibration_scores.jsonl', calibrations, WORLD_KEYS)
        manifest['counts'] = dict(independent_worlds=len(audits),
                                  prefix_records=len(buffers['prefix_records']),
                                  stopped_records=len(buffers['stopped_records']),
                                  acquisitions_logged=len(buffers['acquisitions']),
                                  planned_states=len(buffers['plans']),
                                  candidate_scores=len(buffers['candidate_scores']))
        checks, signals = validate_outputs(cfg, out)
        manifest['checks'] = checks
        manifest['statistical_diagnostic_signals'] = signals
        manifest['statistical_diagnostic_note'] = ('Signals are preserved for investigation, not retried away. '
                                                  'Failure to reject does not prove calibration or assumptions.')
        failures = [check['name'] for check in checks if not check['passed']]
        if failures:
            raise AssertionError('; '.join(failures))
        manifest['status'] = 'complete'
    except Exception as exc:
        manifest['status'] = 'failed'
        manifest['error'] = repr(exc)
        raise
    finally:
        manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
        manifest['elapsed_seconds'] = time.perf_counter()-started
        manifest['artifacts'] = {p.relative_to(out).as_posix(): dict(sha256=digest(p), bytes=p.stat().st_size)
                                 for p in out.rglob('*') if p.is_file() and p != manifest_path}
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'COMPLETE {out}', flush=True)


if __name__ == '__main__':
    main()
