"""Synthetic archive-level calibration audit. Never reads real outcomes or fits."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
RULES = ('joint_max', 'entitywise_marginal', 'entitywise_bonferroni')
ROLES = ('joint', 'entity', 'source', 'bridge', 'target')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rank(n, alpha):
    value = (n + 1) * (1 - alpha)
    return (value.numerator + value.denominator - 1) // value.denominator


def quantile(values, r, axis=0):
    if r > values.shape[axis]:
        shape = list(values.shape)
        del shape[axis]
        return np.full(shape, np.inf)
    return np.partition(values, r - 1, axis=axis).take(r - 1, axis=axis)


def draw(rng, n, cell, missing, unreliable, cfg):
    m, p = cell['M'], cell['p']
    common = rng.standard_normal((n, 1, p))
    entity = rng.standard_normal((n, m, p))
    errors = math.sqrt(cell['rho']) * common + math.sqrt(1 - cell['rho']) * entity
    flags_missing = rng.random((n, m, p)) < missing
    noise_missing = rng.standard_normal((n, m, p))
    errors += cfg['missing_noise_sd'] * flags_missing * noise_missing
    flags_unreliable = rng.random((n, m, p)) < unreliable
    noise_unreliable = rng.standard_normal((n, m, p))
    errors += cfg['unreliable_noise_sd'] * flags_unreliable * noise_unreliable
    return errors, int(flags_missing.sum()), int(flags_unreliable.sum())


def simulate(cell, index, profile, cfg):
    count, seed = profile['worlds_per_cell'], profile['seed']
    m, n = cell['M'], cell['n_cal']
    alpha = Fraction(cfg['eta'])
    ranks = np.array([rank(n, alpha), rank(n, alpha), rank(n, alpha / m)], dtype=np.int64)
    radii = np.empty((count, 3, m))
    norms = np.empty((count, m))
    cal_maxima = np.empty(count)
    joint_scores = np.empty(count)
    flag_counts = np.empty((count, 4), dtype=np.int64)
    for world in range(count):
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed, index, world])))
        cal, cm, cu = draw(rng, n, cell, cell['missing_cal'], cell['unreliable_cal'], cfg)
        test, tm, tu = draw(rng, 1, cell, cell['missing_test'], cell['unreliable_test'], cfg)
        cal_norm = np.linalg.norm(cal, axis=-1)
        norms[world] = np.linalg.norm(test[0] * cell['scale_test'], axis=-1)
        maximum = cal_norm.max(axis=1)
        joint_scores[world] = quantile(maximum, ranks[0])
        cal_maxima[world] = maximum.max()
        radii[world, 0] = joint_scores[world]
        radii[world, 1] = quantile(cal_norm, ranks[1])
        radii[world, 2] = quantile(cal_norm, ranks[2])
        flag_counts[world] = (cm, cu, tm, tu)
    hits = norms[:, None, :] <= radii
    metric = np.empty((count, 3, 5))
    metric[:, :, 0] = hits.all(axis=-1)
    metric[:, :, 1] = hits.mean(axis=-1)
    metric[:, :, 2] = hits[:, :, :cell['K']].mean(axis=-1)
    b = cell['bridges']
    metric[:, :, 3] = hits[:, :, cell['K']:cell['K']+b].mean(axis=-1) if b else np.nan
    metric[:, :, 4] = hits[:, :, -1]
    return dict(radii=radii, test_norms=norms, calibration_max=cal_maxima,
                joint_order_statistic=joint_scores, perturbation_counts=flag_counts,
                ranks=ranks, hits=hits, metrics=metric,
                seed_components=np.array([seed, index], dtype=np.int64))


def wilson(hits, n):
    z = 1.959963984540054
    p = hits/n
    denominator = 1+z*z/n
    mid = (p+z*z/(2*n))/denominator
    half = z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return max(0.0, mid-half), min(1.0, mid+half)


def bootstrap_means(values, repeats, seed):
    """One row is one independent world; pair all rules and roles per resample."""
    rng = np.random.default_rng(seed)
    output = np.empty((repeats,)+values.shape[1:])
    for start in range(0, repeats, 50):
        stop = min(repeats, start+50)
        indices = rng.integers(0, len(values), (stop-start, len(values)))
        output[start:stop] = values[indices].mean(axis=1)
    return output


def summarize(cell, index, raw, profile, cfg):
    metrics, hits, radii = raw['metrics'], raw['hits'], raw['radii']
    boot = bootstrap_means(metrics, profile['bootstrap_repetitions'],
                           np.random.SeedSequence([cfg['bootstrap_seed'], profile['seed'], index]))
    rows, entity_rows, pair_rows = [], [], []
    n = len(metrics)
    for method, name in enumerate(RULES):
        row = dict(cell_id=cell['cell_id'], rule=name, worlds=n, **{k:v for k,v in cell.items() if k!='cell_id'})
        for role, label in enumerate(ROLES):
            values = metrics[:, method, role]
            if np.isnan(values).all():
                mean, lo, hi = None, None, None
            else:
                mean = float(values.mean())
                if role in (0, 4):
                    lo, hi = wilson(int(values.sum()), n)
                else:
                    lo, hi = np.quantile(boot[:, method, role], [.025, .975]).tolist()
            row[label+'_coverage'] = mean
            row[label+'_lower'] = lo
            row[label+'_upper'] = hi
        finite = radii[:, method, :][np.isfinite(radii[:, method, :])]
        row['infinite_radius_fraction'] = float(np.isposinf(radii[:, method]).mean())
        row['finite_radius_median'] = float(np.median(finite)) if len(finite) else None
        row['finite_radius_q95'] = float(np.quantile(finite, .95)) if len(finite) else None
        row['calibration_rank'] = int(raw['ranks'][method])
        rows.append(row)
        for slot in range(cell['M']):
            values = hits[:, method, slot]
            lo, hi = wilson(int(values.sum()), n)
            entity_rows.append(dict(cell_id=cell['cell_id'], rule=name, entity_slot=slot,
                                    role='source' if slot < cell['K'] else 'bridge' if slot < cell['M']-1 else 'target',
                                    worlds=n, coverage=float(values.mean()), lower=lo, upper=hi))
    for left, right in ((0,1),(0,2),(2,1)):
        for role in (0,1):
            differences = metrics[:,left,role]-metrics[:,right,role]
            boot_difference = boot[:,left,role]-boot[:,right,role]
            lo, hi = np.quantile(boot_difference, [.025,.975]).tolist()
            pair_rows.append(dict(cell_id=cell['cell_id'], left=RULES[left], right=RULES[right],
                                  metric=ROLES[role], worlds=n, difference=float(differences.mean()),lower=lo,upper=hi))
    return rows, entity_rows, pair_rows


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(profile_name, output):
    started = time.perf_counter()
    cfg = json.loads((ROOT/'stress_grid_config.json').read_text(encoding='utf-8'))
    profile = cfg['profiles'][profile_name]
    if output.exists():
        raise FileExistsError(f'Fresh output directory required: {output}')
    output.mkdir(parents=True)
    (output/'raw').mkdir()
    (output/'frozen_config.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    rows, entity_rows, pair_rows, timing = [], [], [], []
    for index, cell in enumerate(cfg['cells']):
        tick = time.perf_counter()
        raw = simulate(cell, index, profile, cfg)
        gen_seconds = time.perf_counter()-tick
        tick = time.perf_counter()
        np.savez_compressed(output/'raw'/f'{index:02d}_{cell["cell_id"]}.npz', **raw)
        cell_rows, cell_entity, cell_pairs = summarize(cell, index, raw, profile, cfg)
        rows.extend(cell_rows); entity_rows.extend(cell_entity); pair_rows.extend(cell_pairs)
        timing.append(dict(cell_id=cell['cell_id'],generation_seconds=gen_seconds,
                           storage_and_summary_seconds=time.perf_counter()-tick))
        print(f'{index+1:02d}/{len(cfg["cells"])} {cell["cell_id"]}: {gen_seconds:.3f}s generation',flush=True)
    write_csv(output/'summary.csv', rows)
    write_csv(output/'entity_summary.csv',entity_rows)
    write_csv(output/'paired_world_contrasts.csv',pair_rows)
    write_csv(output/'cell_timing.csv',timing)
    elapsed = time.perf_counter()-started
    manifest = dict(experiment_id=cfg['experiment_id'],profile=profile_name,status='executed_pending_independent_audit',
                    started_seed=profile['seed'],worlds_per_cell=profile['worlds_per_cell'],cells=len(cfg['cells']),
                    elapsed_seconds=elapsed,python=sys.version,numpy=np.__version__,platform=platform.platform(),
                    rng='NumPy Generator PCG64 with SeedSequence([profile_seed,cell_index,world_index])',
                    completed_utc=datetime.now(timezone.utc).isoformat(),
                    command=sys.argv,real_data_execution=False,outcome_data_used=False,
                    source_sha256={p.name:digest(p) for p in [Path(__file__),ROOT/'stress_grid_config.json',ROOT/'protocol.md',ROOT/'execution_amendment.md']},
                    artifacts={str(p.relative_to(output)):{'sha256':digest(p),'bytes':p.stat().st_size} for p in output.rglob('*') if p.is_file()})
    (output/'run_manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f'COMPLETE {output}: {elapsed:.3f}s; independent audit pending',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile',choices=['smoke','full'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    run(args.profile,args.output)
