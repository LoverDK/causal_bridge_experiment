"""Complete acquisition prefixes paired with the unchanged first-release policy.

Planning uses the original design-only planner. Prediction accepts observed
summaries; scoring is a separate operation and cannot change acquisition.
No interval-width stopping rule is introduced here.
"""
import json
import math
from time import perf_counter

import numpy as np
import pandas as pd

from .core import calibrated_quantile
from .workflow import (Design, certificate, collect, execute, make_world,
                       multipliers, plan, refusal_envelope)


WORLD_KEYS = ['surface', 'scenario', 'replicate']
ROW_KEYS = WORLD_KEYS + ['method', 'tolerance', 'budget']


def radius_decomposition(design, ids, weights, mode):
    """Explain a saved feasible certificate without optimizing again."""
    ids = list(ids)
    a = np.asarray(weights, dtype=float)
    centers = design.centers[ids]
    r = design.radii[ids]
    s = design.noise_sd[ids]
    mismatch = design.L * float(np.linalg.norm(a @ centers - design.target_center))
    uncertainty = design.L * float(design.target_radius + a @ r)
    pair = np.linalg.norm(centers[:, None] - centers[None, :], axis=2) + r[:, None] + r[None, :]
    np.fill_diagonal(pair, 0.)
    curvature = design.H / 4 * float(a @ (pair ** 2) @ a)
    barycentric = mismatch + uncertainty + curvature
    lipschitz = design.L * float(a @ (np.linalg.norm(centers - design.target_center, axis=1)
                                      + r + design.target_radius))
    q, coordinate_q = multipliers(design, mode)
    noise = q * (float(a @ s) if mode == 'rinf' else float(np.linalg.norm(a * s)))
    return dict(barycentric_mismatch=mismatch, set_uncertainty=uncertainty,
                curvature=curvature, barycentric_bound=barycentric,
                lipschitz_bound=lipschitz, noise_term=noise,
                chosen_geometric_branch='barycentric' if barycentric <= lipschitz else 'lipschitz',
                geometric_bound=min(barycentric, lipschitz), noise_multiplier=q,
                coordinate_multiplier=coordinate_q)


def target_decomposition(design, radius):
    return dict(barycentric_mismatch=0., set_uncertainty=0., curvature=0.,
                barycentric_bound=0., lipschitz_bound=0., noise_term=radius,
                chosen_geometric_branch='target_only', geometric_bound=0.,
                noise_multiplier=math.sqrt(2 * math.log(2 * design.budget / (design.eta + design.zeta))),
                coordinate_multiplier=math.nan)


def predict_snapshot(design, method, budget, path, observations, target_effects):
    """Predict from observed data only; neither generator nor scoring truth enters."""
    mode = 'rinf' if method == 'rinf_targeted' else 'r2'
    if method == 'target_only':
        estimate = float(np.mean(target_effects)) if target_effects else 0.
        q = math.sqrt(2 * math.log(2 * design.budget / (design.eta + design.zeta)))
        # Every batch has the prespecified candidate sample size.
        n_batch = 1 / design.noise_sd[design.initial] ** 2
        radius = q / math.sqrt(len(target_effects) * n_batch) if target_effects else math.inf
        return dict(ids=[], weights=[], radius=radius, estimate=estimate,
                    refusal_lower=estimate-radius, refusal_upper=estimate+radius,
                    solver_failures=0, **target_decomposition(design, radius))
    p = path[min(budget, len(path)-1)]
    ids = p['ids']
    a = np.asarray(p['weights'])
    estimate = float(a @ [observations[j]['effect'] for j in ids])
    lower, upper = refusal_envelope(design, ids, observations, mode)
    return dict(ids=ids, weights=p['weights'], radius=p['radius'], estimate=estimate,
                refusal_lower=lower, refusal_upper=upper, solver_failures=p['solver_failures'],
                **radius_decomposition(design, ids, a, mode))


def collect_full_prefix(cfg, world, method, path):
    """Actually collect all planned batches, including after an earlier release.

    Called once per world/method, then reused for both tolerance evaluations.
    Source-specific random streams pair modes, methods and tolerances.
    """
    design = world['design']
    observations = {} if method == 'target_only' else {
        j: collect(world, j, cfg['archive_participants']) for j in range(design.initial)}
    events, snapshots, target_effects = [], [], []
    for budget in range(design.budget + 1):
        before = len(events)
        if method == 'target_only' and budget:
            obs = collect(world, len(world['truth']) - 1,
                          cfg['participants_per_bridge'], target_batch=budget)
            target_effects.append(obs['effect'])
            events.append(dict(stage=budget, **obs))
        elif method != 'target_only':
            for source_id in path[min(budget, len(path)-1)]['ids']:
                if source_id not in observations:
                    obs = collect(world, source_id, cfg['participants_per_bridge'])
                    observations[source_id] = obs
                    events.append(dict(stage=budget, **obs))
        prediction = predict_snapshot(design, method, budget, path, observations, target_effects)
        snapshots.append(dict(budget=budget, actual_bridges=len(events),
                              new_n=sum(e['n'] for e in events),
                              selected=json.dumps([e['source_id'] for e in events]),
                              new_observation=len(events) > before, **prediction))
    return snapshots, events


def enrich_output(row, method, mode, design):
    """Keep radius, returned halfwidth and diagnostic midpoint distinct."""
    row = dict(row)
    status = row['interval_status']
    finite = status == 'finite'
    kind = (status if not finite else 'target_interval' if method == 'target_only'
            else 'released_interval' if row['released'] else 'refusal_outer')
    row.update(mode=mode, output_kind=kind,
               output_halfwidth=row['width']/2,
               midpoint=(row['lower'] + row['upper'])/2 if finite else math.nan)
    row['midpoint_abs_error'] = abs(row['midpoint'] - row['truth']) if finite else math.nan
    if mode == 'prefix':
        row['acquisition_status'] = ('static_no_acquisition' if method == 'r2_static' else
                                     'prefix_budget_completed' if row['budget'] == design.budget else
                                     'continue_full_prefix')
    else:
        row['acquisition_status'] = ('released_and_stopped' if row['released'] else
                                     'static_no_acquisition' if method == 'r2_static' else
                                     'budget_exhausted' if row['budget'] == design.budget else
                                     'continue_until_release')
    return row


def evaluate_prefix(design, method, snapshots, tolerance, score_truth, joint_set_covered):
    """Apply the original output rule to every prefix, then score frozen outputs."""
    states = []
    path_covered = True
    for snapshot in snapshots:
        p = dict(snapshot)
        ids, weights = p.pop('ids'), p.pop('weights')
        radius, estimate = p['radius'], p['estimate']
        released = bool(radius <= tolerance)
        lower, upper = ((estimate-radius, estimate+radius) if released else
                        (p['refusal_lower'], p['refusal_upper']))
        status = ('inconsistent' if lower > upper else
                  'unbounded' if not math.isfinite(upper-lower) else 'finite')
        # Decision and interval endpoints above have no dependency on score_truth.
        covered = bool(lower <= score_truth <= upper)
        path_covered = path_covered and covered
        error = abs(estimate - score_truth)
        row = dict(**p, source_ids=json.dumps(ids), weights=json.dumps(weights),
                   truth=float(score_truth), error=error, released=released,
                   bad_release=bool(released and error > tolerance),
                   lower=lower, upper=upper, width=upper-lower if lower <= upper else math.nan,
                   interval_status=status, covered=covered, path_covered=path_covered,
                   certificate_covered=bool(estimate-radius <= score_truth <= estimate+radius),
                   joint_set_covered=bool(joint_set_covered),
                   refusal_reason=('released' if released else 'no_bridge_policy' if method == 'r2_static'
                                   else 'budget_exhausted' if p['budget'] == design.budget
                                   else 'radius_above_tolerance'))
        states.append(enrich_output(row, method, 'prefix', design))
    return states


def execute_prefix(cfg, world, method, path, tolerance, score_truth=None):
    snapshots, events = collect_full_prefix(cfg, world, method, path)
    truth = float(world['truth'][-1]) if score_truth is None else score_truth
    return evaluate_prefix(world['design'], method, snapshots, tolerance, truth,
                           world['joint_set_covered']), events


def reconstruct_calibration(cfg, world):
    """Recreate unsaved scores from the frozen original generator's RNG sequence.

    This is explicitly a reconstruction, not a claim that old logs contained
    the scores. The source-jitter draw precedes calibration in make_world().
    """
    rng = np.random.default_rng(np.random.SeedSequence(
        [cfg['seed'], world['surface_id'], world['scenario_id'], world['replicate'], 0]))
    rng.normal(0, .025, (cfg['initial_sources'] + cfg['candidate_bridges'], 2))
    errors = rng.normal(size=(cfg['calibration_archives'], len(world['locations']), 2))
    scores = np.linalg.norm(errors, axis=2).max(axis=1)
    q = calibrated_quantile(scores, cfg['eta'])
    if q != world['calibration_q']:
        raise AssertionError('Reconstructed calibration does not match the world generator')
    return dict(provenance='reconstructed_from_frozen_generator_seed', seed=cfg['seed'],
                calibration_archives=len(scores), entities=len(world['locations']),
                rank=int(math.ceil((len(scores)+1)*(1-cfg['eta']))),
                scores=scores.tolist(), quantile=q, radius=cfg['proxy_scale']*q,
                original_world_quantile=world['calibration_q'], quantile_matches=True)


def run_world(task):
    cfg, surface_id, scenario_id, rep = task
    started = perf_counter()
    world = make_world(cfg, surface_id, scenario_id, rep)
    meta = {key: world[key] for key in WORLD_KEYS}
    d = world['design']
    random_order = np.random.default_rng(np.random.SeedSequence(
        [cfg['seed'], surface_id, scenario_id, rep, 20])).permutation(np.arange(4, 10))
    prefix_rows, stopped_rows, events, plans, choices = [], [], [], [], []
    for method in cfg['methods']:
        path, diagnostics = ([], []) if method == 'target_only' else plan(d, method, random_order)
        for stage, p in enumerate(path):
            mode = 'rinf' if method == 'rinf_targeted' else 'r2'
            plans.append(dict(**meta, method=method, stage=stage, **p,
                              **radius_decomposition(d, p['ids'], p['weights'], mode)))
        choices.extend(dict(**meta, method=method, **r) for r in diagnostics)
        snapshots, prefix_events = collect_full_prefix(cfg, world, method, path)
        for tolerance in cfg['tolerances']:
            base = dict(**meta, method=method, tolerance=tolerance)
            prefix = evaluate_prefix(d, method, snapshots, tolerance,
                                     float(world['truth'][-1]), world['joint_set_covered'])
            stopped, stopped_events = execute(cfg, world, method, path, tolerance)
            prefix_rows.extend(dict(**base, **r) for r in prefix)
            for r in stopped:
                parts = (target_decomposition(d, r['radius']) if method == 'target_only' else
                         radius_decomposition(d, json.loads(r['source_ids']), json.loads(r['weights']),
                                              'rinf' if method == 'rinf_targeted' else 'r2'))
                stopped_rows.append(dict(**base, **enrich_output(dict(**r, **parts), method, 'stopped', d)))
            for mode, acquired in [('prefix', prefix_events), ('stopped', stopped_events)]:
                events.extend(dict(**base, mode=mode, treated_n=e['n']//2, control_n=e['n']//2,
                                   observation_stream='paired_source_stream', **e) for e in acquired)
    audit = dict(**meta, seed=cfg['seed'], surface_id=surface_id, scenario_id=scenario_id,
                 joint_set_covered=world['joint_set_covered'], calibration_q=world['calibration_q'],
                 max_standardized_proxy_error=world['max_standardized_proxy_error'],
                 calibration_max=world['calibration_max'], L=d.L, H=d.H,
                 true_locations=world['locations'].tolist(), true_effects=world['truth'].tolist(),
                 proxies=d.centers.tolist(), target_proxy=d.target_center.tolist(), radius=d.target_radius,
                 archive_observations=[collect(world, j, cfg['archive_participants']) for j in range(4)],
                 random_bridge_order=random_order.tolist(), elapsed_seconds=perf_counter()-started,
                 truth_usage='generator_and_scorer_only; planner receives Design')
    return dict(prefix_records=prefix_rows, stopped_records=stopped_rows, acquisitions=events,
                plans=plans, candidate_scores=choices, world_audit=audit,
                calibration=dict(**meta, **reconstruct_calibration(cfg, world)))


def validate_outputs(cfg, out):
    """Recompute saved outputs from logged observations and the legacy radius API."""
    from scipy.stats import binom
    frames = {mode: pd.read_csv(out/f'{mode}_records.csv') for mode in ['prefix', 'stopped']}
    events = pd.read_csv(out/'acquisitions.csv')
    audits = pd.read_json(out/'world_audits.jsonl', lines=True)
    calibrations = [json.loads(line) for line in (out/'calibration_scores.jsonl').read_text('utf-8').splitlines()]
    plans = pd.read_json(out/'plans.jsonl', lines=True)
    checks = []
    def check(name, passed, detail=''):
        checks.append(dict(name=name, passed=bool(passed), detail=detail))
    nw = cfg['repetitions_per_cell'] * len(cfg['surfaces']) * len(cfg['scenarios'])
    nr = nw * len(cfg['methods']) * len(cfg['tolerances']) * (cfg['max_bridges']+1)
    check('complete and unique world audits', len(audits) == nw and not audits.duplicated(WORLD_KEYS).any())
    check('one reconstructed calibration per world', len(calibrations) == nw and
          len({tuple(c[k] for k in WORLD_KEYS) for c in calibrations}) == nw)
    calibration_ok = True
    for c in calibrations:
        scores = np.asarray(c['scores'])
        rank = math.ceil((len(scores)+1)*(1-cfg['eta']))
        calibration_ok &= (len(scores) == cfg['calibration_archives'] and c['entities'] == 11
                           and c['provenance'] == 'reconstructed_from_frozen_generator_seed'
                           and c['rank'] == rank and float(np.sort(scores)[rank-1]) == c['quantile']
                           and c['quantile'] == c['original_world_quantile'])
    check('reconstructed scores reproduce the declared order statistic', calibration_ok)
    check('no global optimality claim', not plans.global_optimum_certified.any())
    check('two arms reconstruct every acquired effect',
          np.allclose(events.effect, events.treated_mean-events.control_mean, atol=1e-12, rtol=0)
          and (events.treated_n+events.control_n == events.n).all())
    design_index = {}
    for w in audits.itertuples(index=False):
        d = Design(np.asarray(w.proxies), np.full(10, w.radius), np.asarray(w.target_proxy), w.radius,
                   1/np.sqrt(np.r_[np.full(4, cfg['archive_participants']),
                                  np.full(6, cfg['participants_per_bridge'])]),
                   w.L, w.H, 4, cfg['max_bridges'], cfg['eta'], cfg['zeta'])
        design_index[(w.surface, w.scenario, w.replicate)] = (d, w)
    acquisition_index = {tuple(key): group.sort_values('stage') for key, group in
                         events.groupby(['mode'] + WORLD_KEYS + ['method', 'tolerance'])}
    groups = {}
    stats = []
    for mode, df in frames.items():
        check(f'{mode}: balanced unique records', len(df) == nr and not df.duplicated(ROW_KEYS).any())
        check(f'{mode}: mode labels match file', df['mode'].eq(mode).all())
        check(f'{mode}: original release event preserved', np.array_equal(df.released, df.radius <= df.tolerance))
        check(f'{mode}: error release event is unconditional',
              np.array_equal(df.bad_release, df.released & (df.error > df.tolerance)))
        check(f'{mode}: halfwidth is returned width, not certificate radius',
              np.allclose(df.output_halfwidth, df.width/2, equal_nan=True))
        finite = df.interval_status.eq('finite')
        check(f'{mode}: diagnostic midpoint only for finite nonempty intervals',
              np.allclose(df.loc[finite, 'midpoint'], (df.loc[finite, 'lower']+df.loc[finite, 'upper'])/2)
              and df.loc[~finite, 'midpoint'].isna().all())
        max_estimate_error = max_radius_error = max_endpoint_error = 0.
        costs_ok = availability_ok = paths_ok = states_ok = decomposition_ok = True
        groups[mode] = {tuple(k): g.sort_values('budget') for k, g in df.groupby(WORLD_KEYS+['method','tolerance'])}
        for key, group in groups[mode].items():
            d, w = design_index[key[:3]]
            method = key[3]
            acquired = acquisition_index.get((mode,)+key, events.iloc[:0])
            base = {e['source_id']: e for e in w.archive_observations}
            coverage = True
            last_cost = 0
            stop_row = None
            for row in group.itertuples(index=False):
                observed = acquired[acquired.stage <= row.budget]
                costs_ok &= (len(observed) == row.actual_bridges and observed.n.sum() == row.new_n
                             and row.new_n == row.actual_bridges*cfg['participants_per_bridge'])
                costs_ok &= json.loads(row.selected) == observed.source_id.tolist()
                if mode == 'prefix':
                    costs_ok &= row.actual_bridges == (0 if method == 'r2_static' else row.budget)
                states_ok &= row.new_observation == (row.new_n > last_cost)
                last_cost = row.new_n
                if mode == 'stopped' and stop_row is not None:
                    states_ok &= all(getattr(row, k) == getattr(stop_row, k)
                                     for k in ['new_n','selected','estimate','radius','lower','upper'])
                if row.released and stop_row is None:
                    stop_row = row
                if method == 'target_only':
                    estimate = observed.effect.mean() if len(observed) else 0.
                    q = math.sqrt(2*math.log(2*d.budget/(d.eta+d.zeta)))
                    radius = q/math.sqrt(row.new_n) if row.new_n else math.inf
                    refusal_low, refusal_high = estimate-radius, estimate+radius
                else:
                    obs = base | {int(e.source_id): dict(effect=e.effect) for e in observed.itertuples(index=False)}
                    ids, a = json.loads(row.source_ids), np.asarray(json.loads(row.weights))
                    availability_ok &= all(i in obs for i in ids) and a.min() >= 0 and abs(a.sum()-1) < 1e-8
                    estimate = float(a @ [obs[i]['effect'] for i in ids])
                    noise_mode = 'rinf' if method == 'rinf_targeted' else 'r2'
                    radius = certificate(d, ids, a, noise_mode)
                    coord = math.sqrt(2*math.log(2*len(d.centers)/(d.zeta if noise_mode == 'rinf' else d.zeta/2)))
                    widths = coord*d.noise_sd[ids] + d.L*(np.linalg.norm(d.centers[ids]-d.target_center, axis=1)
                                                         +d.radii[ids]+d.target_radius)
                    estimates = np.array([obs[i]['effect'] for i in ids])
                    refusal_low, refusal_high = float(max(estimates-widths)), float(min(estimates+widths))
                max_estimate_error = max(max_estimate_error, abs(estimate-row.estimate))
                if math.isfinite(radius):
                    max_radius_error = max(max_radius_error, abs(radius-row.radius))
                    decomposition_ok &= abs(min(row.barycentric_bound,row.lipschitz_bound)+row.noise_term-radius) < 1e-8
                else:
                    states_ok &= math.isinf(row.radius)
                low, high = ((estimate-radius, estimate+radius) if row.released else (refusal_low, refusal_high))
                for value, saved in [(low,row.lower),(high,row.upper),(refusal_low,row.refusal_lower),(refusal_high,row.refusal_upper)]:
                    if math.isfinite(value):
                        max_endpoint_error = max(max_endpoint_error, abs(value-saved))
                    else:
                        states_ok &= value == saved
                status = ('inconsistent' if low > high else 'unbounded' if not math.isfinite(high-low) else 'finite')
                states_ok &= row.interval_status == status
                if status == 'inconsistent':
                    states_ok &= math.isnan(row.width)
                elif status == 'unbounded':
                    states_ok &= math.isinf(row.width)
                else:
                    states_ok &= abs(row.width-(high-low)) < 1e-8
                cover = low <= row.truth <= high
                coverage = coverage and cover
                paths_ok &= row.covered == cover and row.path_covered == coverage
        check(f'{mode}: actual cost, acquisition count and selected IDs agree', costs_ok)
        check(f'{mode}: all weighted sources available and weights feasible', availability_ok)
        check(f'{mode}: predictions reconstructed from actual arm summaries', max_estimate_error < 1e-8, str(max_estimate_error))
        check(f'{mode}: legacy certificate matches saved decomposition', max_radius_error < 1e-8 and decomposition_ok, str(max_radius_error))
        check(f'{mode}: returned and refused endpoints independently reconstructed', max_endpoint_error < 1e-8, str(max_endpoint_error))
        check(f'{mode}: acquisition and interval states remain consistent', states_ok)
        check(f'{mode}: path coverage is conjunction across all reported outputs', paths_ok)
        final = df[df.budget == cfg['max_bridges']]
        for keys, g in final.groupby(['surface','scenario','method','tolerance']):
            failures = int((~g.path_covered).sum())
            stats.append(dict(mode=mode, **dict(zip(['surface','scenario','method','tolerance'],keys)),
                              test='path_miscoverage', n=len(g), failures=failures,
                              failure_budget=cfg['eta']+cfg['zeta'],
                              p_value=float(binom.sf(failures-1,len(g),cfg['eta']+cfg['zeta']))))
    agreement = True
    for key, stopped in groups['stopped'].items():
        prefix = groups['prefix'][key].set_index('budget')
        for row in stopped.itertuples(index=False):
            other = prefix.loc[row.budget]
            # Equality is required through the first stop, not after it.
            for name in ['estimate','radius','lower','upper','new_n']:
                agreement &= bool(np.isclose(getattr(row,name),other[name],rtol=0,atol=1e-9,equal_nan=True))
            agreement &= row.selected == other.selected and row.weights == other.weights
            if row.released or row.method == 'r2_static':
                break
    check('prefix and original stopped modes agree through first stop', agreement)
    for keys, g in audits.groupby(['surface','scenario']):
        failures = int((~g.joint_set_covered).sum())
        stats.append(dict(mode='shared',surface=keys[0],scenario=keys[1],method='all',tolerance=math.nan,
                          test='joint_set_miscoverage', n=len(g), failures=failures,
                          failure_budget=cfg['eta'],p_value=float(binom.sf(failures-1,len(g),cfg['eta']))))
    stat = pd.DataFrame(stats)
    stat['familywise_alpha'] = .01/len(stat)
    stat['violation_detected'] = stat.p_value < stat.familywise_alpha
    stat.to_csv(out/'statistical_calibration_checks.csv',index=False,float_format='%.15g')
    # A diagnostic signal is preserved in raw output, not suppressed by a retry.
    (out/'validation_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    return checks, int(stat.violation_detected.sum())
