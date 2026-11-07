"""Run the frozen moment-only target-bridge experiment in a fresh directory."""
import os
for variable in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[variable] = '1'

import argparse
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

import numpy as np
import pandas as pd

from atlas_new.non_gaussian_target_bridge import (METHODS, jobs, make_plans, normalized_config, run_world)

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args):
    result = subprocess.run(['git', *args], cwd=REPO, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    return result.stdout.strip() if result.returncode == 0 else None


def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def wilson(successes, total):
    z = 1.959963984540054
    p = successes / total
    den = 1 + z*z/total
    center = (p + z*z/(2*total))/den
    half = z*np.sqrt(p*(1-p)/total + z*z/(4*total*total))/den
    return float(center-half), float(center+half)


def summaries(cfg, frame, out):
    cell = ['geometry', 'beta_family', 'noise_family', 'method']
    summary = []
    for key, group in frame.groupby(cell + ['mode', 'budget_stage'], sort=True):
        row = dict(zip(cell + ['mode', 'budget_stage'], key))
        row['n_worlds'] = len(group)
        for field in ['new_participants', 'width', 'path_width', 'W', 'absolute_error',
                      'squared_error', 'released', 'covered', 'path_interval_covered',
                      'interval_miss_on_release', 'bad_release_scientific']:
            row[f'mean_{field}'] = float(group[field].mean())
        for field in ['covered', 'path_interval_covered', 'interval_miss_on_release', 'bad_release_scientific']:
            row[f'{field}_ci_low'], row[f'{field}_ci_high'] = wilson(int(group[field].sum()), len(group))
        row['rmse'] = float(np.sqrt(group['squared_error'].mean()))
        summary.append(row)
    pd.DataFrame(summary).to_csv(out/'summary.csv', index=False, float_format='%.15g')
    prefixes = frame[frame['mode'] == 'prefix']
    terminal = prefixes[prefixes['budget_stage'] == cfg['max_batches']]
    path_rows = []
    for key, group in terminal.groupby(cell, sort=True):
        row = dict(zip(cell, key))
        row['n_worlds'] = len(group)
        for field in ['all_pointwise_prefix_covered', 'all_joint_prefix_covered']:
            row[field] = float(group[field].mean())
            row[f'{field}_ci_low'], row[f'{field}_ci_high'] = wilson(int(group[field].sum()), len(group))
        path_rows.append(row)
    pd.DataFrame(path_rows).to_csv(out/'path_coverage.csv', index=False, float_format='%.15g')
    hits = []
    for key, group in prefixes.groupby(cell + ['replicate'], sort=True):
        for width in cfg['width_thresholds']:
            eligible = group[group['width'] <= width].sort_values('budget_stage')
            success = len(eligible) > 0
            hits.append(dict(zip(cell + ['replicate'], key)) | dict(
                full_width_threshold=width, attained=success,
                first_cost=int(eligible.iloc[0]['new_participants']) if success else None,
                capped_cost=int(eligible.iloc[0]['new_participants']) if success else cfg['max_batches']*cfg['batch_participants']))
    hit_frame = pd.DataFrame(hits)
    hit_frame.to_csv(out/'attainment_records.csv', index=False)
    hit_frame.groupby(cell + ['full_width_threshold'], as_index=False).agg(
        n_worlds=('attained', 'size'), attained_rate=('attained', 'mean'),
        mean_cost_among_attained=('first_cost', 'mean'), mean_capped_cost=('capped_cost', 'mean')
        ).to_csv(out/'attainment_summary.csv', index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=['smoke', 'full'], required=True)
    parser.add_argument('--config', type=Path, default=REPO/'revision'/'NON_GAUSSIAN_TARGET_RUN01.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads(args.config.read_text('utf-8'))
    cfg = normalized_config(frozen)
    out = args.output.resolve()
    if out.exists():
        raise FileExistsError(f'Use a new output directory, preserving previous runs: {out}')
    out.mkdir(parents=True)
    sources = [ROOT/'atlas_new'/'non_gaussian_target_bridge.py', Path(__file__),
               ROOT/'tests'/'test_non_gaussian_target_bridge.py', args.config.resolve(),
               REPO/'revision'/'NON_GAUSSIAN_TARGET_RUN01.md']
    snapshot = out/'source_snapshot'
    for source in sources:
        target = snapshot/source.relative_to(REPO)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    manifest = dict(status='running', experiment_id=frozen['experiment_id'], profile=args.profile,
                    started_utc=datetime.now(timezone.utc).isoformat(), command=[sys.executable, *sys.argv],
                    git_revision=git_value('rev-parse', 'HEAD'), git_status=git_value('status', '--short'),
                    config_sha256=digest(args.config), config=frozen, python=sys.version, platform=platform.platform(),
                    packages={k: importlib.metadata.version(k) for k in ['numpy', 'pandas']},
                    source_sha256={p.relative_to(REPO).as_posix(): digest(p) for p in sources},
                    moments_source='synthetic_known',
                    coverage_scope='Marginal over random beta and noise. Pointwise intervals at each fixed design; stopped design is precomputed. Joint prefix intervals use alpha/5. No coverage conditional on realized beta or release outcomes.',
                    sampling_scope='Paired methods share only an identical acquisition identity; distinct arms, sites and visits use separate independent streams.',
                    cost_scope='Actual additional participants; 64 common historical participants excluded from incremental cost.',
                    comparison_scope='Target-informative advantage comes from explicit feature loading, not lower noise or hidden cost. No universal superiority.')
    write_json(out/'run_manifest.json', manifest)
    write_json(out/'config.json', frozen)
    start = time.perf_counter()
    try:
        test = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                               '-p', 'test_non_gaussian_target_bridge.py', '-v'], cwd=ROOT,
                              capture_output=True, text=True, encoding='utf-8', errors='replace')
        (out/'test_log.txt').write_text(test.stdout + test.stderr, encoding='utf-8')
        if test.returncode:
            raise AssertionError('Unit checks failed; see test_log.txt')
        plans, scores, random_paths = make_plans(cfg)
        write_json(out/'design_plans.json', {f'{g}/{m}': p for (g, m), p in plans.items()})
        write_json(out/'random_paths.json', random_paths)
        pd.DataFrame(scores).to_csv(out/'candidate_scores.csv', index=False, float_format='%.15g')
        records, acquisitions, traces, history_records = [], [], [], []
        tasks = list(jobs(cfg, args.profile))
        for n, task in enumerate(tasks, 1):
            rows, events, trace, history = run_world(cfg, args.profile, plans, *task)
            records.extend(rows)
            acquisitions.extend(events)
            history_records.extend(history)
            if trace is not None:
                traces.append(trace)
            if n % 200 == 0 or n == len(tasks):
                print(f'Worlds {n}/{len(tasks)}; elapsed {time.perf_counter()-start:.1f}s', flush=True)
        frame = pd.DataFrame(records)
        frame.to_csv(out/'records.csv', index=False, float_format='%.15g')
        pd.DataFrame(acquisitions).to_csv(out/'acquisitions.csv', index=False, float_format='%.15g')
        pd.DataFrame(history_records).to_csv(out/'history_observations.csv', index=False, float_format='%.15g')
        with (out/'traces.jsonl').open('w', encoding='utf-8') as handle:
            for trace in traces:
                handle.write(json.dumps(trace, ensure_ascii=False, allow_nan=False) + '\n')
        expected = len(tasks)*len(METHODS)*2*(cfg['max_batches']+1)
        checks = dict(record_count=len(frame) == expected,
                      history_count=len(history_records) == len(tasks)*len(cfg['history']),
                      actual_cost_matches_stage=bool((frame['new_participants'] == frame['actual_stage']*cfg['batch_participants']).all()),
                      spent_not_above_available=bool((frame['new_participants'] <= frame['available_participants']).all()),
                      finite_outputs=bool(np.isfinite(frame[['estimate', 'W', 'radius', 'path_radius', 'error']]).all().all()),
                      primitive_W_equals_q=bool(np.allclose(frame['W'], frame['q'], rtol=1e-10, atol=1e-13)),
                      pointwise_radius_budget=bool(np.allclose(frame['radius']**2*cfg['alpha'], frame['W'])),
                      path_radius_budget=bool(np.allclose(frame['path_radius']**2*cfg['alpha']/5, frame['W'])))
        manifest.update(checks=checks, counts=dict(worlds=len(tasks), records=len(frame), acquisitions=len(acquisitions),
                                                 history_observations=len(history_records), traces=len(traces)))
        if not all(checks.values()):
            raise AssertionError(f'Output checks failed: {checks}')
        summaries(cfg, frame, out)
        manifest['status'] = 'complete'
    except Exception as exc:
        manifest.update(status='failed', error=repr(exc))
        raise
    finally:
        manifest['elapsed_seconds'] = time.perf_counter() - start
        manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
        manifest['artifact_sha256'] = {p.name: digest(p) for p in out.iterdir() if p.is_file() and p.name != 'run_manifest.json'}
        write_json(out/'run_manifest.json', manifest)


if __name__ == '__main__':
    main()
