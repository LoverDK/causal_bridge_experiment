"""Design-only planning and finite-horizon release with calibrated mechanism balls."""
from dataclasses import dataclass
from itertools import product
import json
import math
from time import perf_counter

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from .core import calibrated_quantile


@dataclass(frozen=True)
class Design:
    centers: np.ndarray
    radii: np.ndarray
    target_center: np.ndarray
    target_radius: float
    noise_sd: np.ndarray
    L: float
    H: float
    initial: int
    budget: int
    eta: float
    zeta: float


def surface(name, locations):
    x, y = np.asarray(locations).T
    if name == 'linear':
        return .55*x + .3*y, math.hypot(.55, .3), 0.
    if name == 'quadratic':
        return .5*x + .2*y + .06*(x*x+y*y), math.hypot(.62, .32), .12
    if name == 'sinusoidal':
        return .45*x + .2*y + .08*np.sin(2*x), math.hypot(.61, .2), .32
    raise ValueError(name)


def make_world(cfg, surface_id, scenario_id, replicate):
    rng = np.random.default_rng(np.random.SeedSequence(
        [cfg['seed'], surface_id, scenario_id, replicate, 0]))
    scenario = cfg['scenarios'][scenario_id]
    if scenario == 'supported':
        archive = [[.35,.10],[.15,.30],[.25,-.05],[.05,.15]]
        candidates = [[.2,.1],[-.1,.25],[.4,-.2],[-.35,.15],[.05,-.35],[-.2,-.15]]
        target = [.20,.12]
    elif scenario == 'bridgeable':
        archive = [[-.75,-.55],[-.65,-.35],[-.55,-.70],[-.40,-.50]]
        candidates = [[-.25,-.20],[.0,-.05],[.25,.10],[.45,.30],[.65,.45],[.75,.60]]
        target = [.0,-.05]
    elif scenario == 'unreachable':
        archive = [[-.85,-.65],[-.72,-.55],[-.62,-.75],[-.48,-.58]]
        candidates = [[-.80,-.40],[-.65,-.30],[-.50,-.22],[-.42,-.12],[-.30,-.18],[-.20,-.05]]
        target = [.88,.82]
    else:
        raise ValueError(scenario)
    source_locations = np.vstack([archive, candidates])
    source_locations += rng.normal(0, .025, source_locations.shape)
    locations = np.vstack([np.clip(source_locations, -1, 1), target])
    # Calibration precedes the test proxy and uses separate labelled audit worlds.
    cal_errors = rng.normal(size=(cfg['calibration_archives'], len(locations), 2))
    cal_scores = np.linalg.norm(cal_errors, axis=2).max(axis=1)
    q = calibrated_quantile(cal_scores, cfg['eta'])
    radius = cfg['proxy_scale']*q
    proxies = np.clip(locations + cfg['proxy_scale']*rng.normal(size=locations.shape), -1, 1)
    truth, L, H = surface(cfg['surfaces'][surface_id], locations)
    counts = np.r_[np.full(4, cfg['archive_participants']),
                   np.full(6, cfg['participants_per_bridge'])]
    design = Design(proxies[:-1], np.full(10, radius), proxies[-1], radius,
                    1/np.sqrt(counts), L, H, 4, cfg['max_bridges'], cfg['eta'], cfg['zeta'])
    distances = np.linalg.norm(proxies-locations, axis=1)
    world = dict(surface=cfg['surfaces'][surface_id], scenario=scenario, replicate=replicate,
                 surface_id=surface_id, scenario_id=scenario_id, seed=cfg['seed'],
                 locations=locations, truth=truth, design=design,
                 joint_set_covered=bool(np.all(distances <= radius)), calibration_q=q,
                 calibration_max=float(cal_scores.max()),
                 max_standardized_proxy_error=float(distances.max()/cfg['proxy_scale']))
    return world


def multipliers(design, mode):
    if mode == 'rinf':
        q = math.sqrt(2*math.log(2*len(design.centers)/design.zeta))
        return q, q
    if mode != 'r2':
        raise ValueError(mode)
    return (math.sqrt(2*math.log(2*(design.budget+1)/(design.zeta/2))),
            math.sqrt(2*math.log(2*len(design.centers)/(design.zeta/2))))


def objective_parts(design, ids, mode):
    centers, r, s = design.centers[ids], design.radii[ids], design.noise_sd[ids]
    pair = np.linalg.norm(centers[:,None]-centers[None,:], axis=2) + r[:,None]+r[None,:]
    np.fill_diagonal(pair, 0.)
    pair2 = pair**2
    target_distances = np.linalg.norm(centers-design.target_center, axis=1) + r+design.target_radius
    q, _ = multipliers(design, mode)

    def evaluate(a, branch):
        if branch == 'barycentric':
            offset = a@centers-design.target_center
            distance = np.linalg.norm(offset)
            gradient = design.L*(r+(centers@offset/distance if distance > 1e-14 else 0.))
            geom = design.L*(distance+design.target_radius+a@r)
            geom += design.H/4*float(a@pair2@a)
            gradient += design.H/2*(pair2@a)
        else:
            geom = design.L*float(a@target_distances)
            gradient = design.L*target_distances
        if mode == 'rinf':
            noise = q*float(a@s)
            gradient = gradient+q*s
        else:
            scale = np.linalg.norm(a*s)
            noise = q*scale
            gradient = gradient+q*a*s*s/max(scale, 1e-30)
        return float(geom+noise), gradient
    return evaluate


def certificate(design, ids, weights, mode):
    a = np.asarray(weights, float)
    if len(a) != len(ids) or not np.isfinite(a).all() or a.min() < 0 or abs(a.sum()-1) > 1e-8:
        raise ValueError('Certificate requires finite simplex weights')
    objective = objective_parts(design, list(ids), mode)
    return min(objective(a, 'barycentric')[0], objective(a, 'lipschitz')[0])


def optimize(design, ids, mode, warm=None):
    ids = list(ids); k = len(ids)
    objective = objective_parts(design, ids, mode)
    uniform = np.full(k, 1/k)
    candidates = [uniform, *np.eye(k)]
    if warm is not None:
        candidates.append(np.asarray(warm, float))
    feasible = [(certificate(design, ids, a, mode), a.copy()) for a in candidates]
    best_vertex = min(feasible[1:k+1], key=lambda item: item[0])[1]
    successes = failures = 0
    starts = [uniform, best_vertex]
    for branch in ['barycentric', 'lipschitz']:
        for start in starts:
            result = minimize(lambda a: objective(a, branch), start, jac=True, method='SLSQP',
                              bounds=[(0, 1)]*k,
                              constraints={'type':'eq', 'fun':lambda a: a.sum()-1,
                                           'jac':lambda a: np.ones(k)},
                              options={'maxiter':70, 'ftol':1e-8})
            if result.success and np.isfinite(result.x).all() and result.x.sum() > 0:
                a = np.maximum(result.x, 0.); a /= a.sum()
                feasible.append((certificate(design, ids, a, mode), a)); successes += 1
            else:
                failures += 1
    value, alpha = min(feasible, key=lambda item: item[0])
    return dict(ids=ids, weights=alpha.tolist(), radius=value,
                solver_successes=successes, solver_failures=failures,
                global_optimum_certified=False)


def plan(design, method, random_order):
    """No outcomes or mechanism truth are accepted by the planner."""
    mode = 'rinf' if method == 'rinf_targeted' else 'r2'
    initial = optimize(design, list(range(design.initial)), mode)
    path = [initial]; diagnostics = []
    if method == 'r2_static':
        return path, diagnostics
    for stage in range(1, design.budget+1):
        prev = path[-1]; available = [j for j in range(design.initial, len(design.centers))
                                    if j not in prev['ids']]
        warm = np.r_[prev['weights'], 0.]
        if method.endswith('targeted'):
            options = []
            for candidate in available:
                result = optimize(design, prev['ids']+[candidate], mode, warm)
                options.append((result['radius'], candidate, result))
                diagnostics.append(dict(stage=stage, candidate=candidate,
                                        planned_radius=result['radius'],
                                        solver_failures=result['solver_failures']))
            _, chosen, result = min(options, key=lambda x: (x[0], x[1]))
        else:
            if method == 'r2_random':
                chosen = next(j for j in random_order if j in available)
            elif method == 'r2_nearest':
                chosen = min(available, key=lambda j: np.linalg.norm(design.centers[j]-design.target_center))
            else:
                raise ValueError(method)
            chosen = int(chosen)
            result = optimize(design, prev['ids']+[chosen], mode, warm)
        if result['radius'] > prev['radius'] + 1e-8:
            raise AssertionError('Adding an optional source worsened feasible radius')
        result['chosen'] = int(chosen); path.append(result)
    return path, diagnostics


def collect(world, source_id, n, target_batch=None):
    """Generate an actual balanced randomized experiment only when requested.

    Source-specific streams pair methods without letting future outcomes enter
    planning. Direct target batches are independent of all archive/bridge data.
    """
    if n < 2 or n % 2:
        raise ValueError('An even positive participant count is required')
    token = source_id if target_batch is None else 100+target_batch
    rng = np.random.default_rng(np.random.SeedSequence(
        [world['seed'], world['surface_id'], world['scenario_id'], world['replicate'], 10, token]))
    mu = world['truth'][source_id]
    treated = rng.normal(mu, .5, n//2)
    control = rng.normal(0, .5, n//2)
    return dict(source_id=source_id, n=n, treated_mean=float(treated.mean()),
                control_mean=float(control.mean()), effect=float(treated.mean()-control.mean()),
                noise_sd=1/math.sqrt(n), target_batch=target_batch)


def refusal_envelope(design, ids, observations, mode):
    _, q = multipliers(design, mode)
    ids = list(ids)
    distances = (np.linalg.norm(design.centers[ids]-design.target_center, axis=1)
                 +design.radii[ids]+design.target_radius)
    effects = np.array([observations[j]['effect'] for j in ids])
    width = q*design.noise_sd[ids]+design.L*distances
    return float(np.max(effects-width)), float(np.min(effects+width))


def execute(cfg, world, method, path, tolerance):
    """Execute only to first release or budget exhaustion; score truth last."""
    design = world['design']; mode = 'rinf' if method == 'rinf_targeted' else 'r2'
    obs = {}; events = []; states = []; target_effects = []
    if method != 'target_only':
        obs = {j: collect(world, j, cfg['archive_participants']) for j in range(design.initial)}
    stopped = False; path_covered = True; last = None
    for budget in range(design.budget+1):
        if stopped:
            carried = dict(last, budget=budget, new_observation=False)
            states.append(carried); continue
        if method == 'target_only':
            if budget == 0:
                estimate = 0.; radius = np.inf; ids = []; weights = []
            else:
                observation = collect(world, len(world['truth'])-1,
                                      cfg['participants_per_bridge'], target_batch=budget)
                target_effects.append(observation['effect']); events.append(dict(stage=budget, **observation))
                estimate = float(np.mean(target_effects)); ids = []; weights = []
                q = math.sqrt(2*math.log(2*design.budget/(design.eta+design.zeta)))
                radius = q/math.sqrt(budget*cfg['participants_per_bridge'])
            refusal_lower, refusal_upper = estimate-radius, estimate+radius
            solver_failures = 0
        else:
            p = path[min(budget, len(path)-1)]
            ids, weights, radius = p['ids'], p['weights'], p['radius']
            for j in ids:
                if j not in obs:
                    obs[j] = collect(world, j, cfg['participants_per_bridge'])
                    events.append(dict(stage=budget, **obs[j]))
            estimate = float(np.asarray(weights) @ [obs[j]['effect'] for j in ids])
            refusal_lower, refusal_upper = refusal_envelope(design, ids, obs, mode)
            solver_failures = p['solver_failures']
        released = bool(radius <= tolerance)
        lower, upper = ((estimate-radius, estimate+radius) if released else
                        (refusal_lower, refusal_upper))
        # All decisions above are frozen before reading the target truth here.
        truth = float(world['truth'][-1]); error = abs(estimate-truth)
        covered = lower <= truth <= upper
        path_covered = path_covered and covered
        actual_bridges = len(events)
        last = dict(budget=budget, actual_bridges=actual_bridges,
                    new_n=actual_bridges*cfg['participants_per_bridge'],
                    selected=json.dumps([e['source_id'] for e in events]),
                    source_ids=json.dumps(ids), weights=json.dumps(weights),
                    radius=radius, estimate=estimate, truth=truth, error=error,
                    released=released, bad_release=bool(released and error > tolerance),
                    lower=lower, upper=upper, width=upper-lower if lower<=upper else np.nan,
                    interval_status=('inconsistent' if lower>upper else
                                     'unbounded' if not np.isfinite(upper-lower) else 'finite'),
                    covered=covered, path_covered=path_covered,
                    certificate_covered=bool(estimate-radius<=truth<=estimate+radius),
                    refusal_lower=refusal_lower, refusal_upper=refusal_upper,
                    joint_set_covered=world['joint_set_covered'],
                    solver_failures=solver_failures, new_observation=(budget>0),
                    refusal_reason=('released' if released else 'no_bridge_policy' if method=='r2_static'
                                    else 'budget_exhausted' if budget==design.budget else 'radius_above_tolerance'))
        states.append(last)
        stopped = released or method == 'r2_static'
    return states, events


def run_world(task):
    cfg, surface_id, scenario_id, rep = task
    started = perf_counter(); world = make_world(cfg, surface_id, scenario_id, rep)
    meta = {key:world[key] for key in ['surface','scenario','replicate']}
    rng = np.random.default_rng(np.random.SeedSequence([cfg['seed'],surface_id,scenario_id,rep,20]))
    order = rng.permutation(np.arange(4,10))
    rows, events, plans, choices = [], [], [], []
    for method in cfg['methods']:
        path, diagnostics = ([], []) if method=='target_only' else plan(world['design'],method,order)
        for stage, p in enumerate(path):
            plans.append(dict(**meta, method=method, stage=stage, **p))
        choices.extend(dict(**meta, method=method, **d) for d in diagnostics)
        for tolerance in cfg['tolerances']:
            states, collected = execute(cfg, world, method, path, tolerance)
            rows.extend(dict(**meta,method=method,tolerance=tolerance,**s) for s in states)
            events.extend(dict(**meta,method=method,tolerance=tolerance,**e) for e in collected)
    d = world['design']
    audit = dict(**meta, joint_set_covered=world['joint_set_covered'], calibration_q=world['calibration_q'],
                 max_standardized_proxy_error=world['max_standardized_proxy_error'],
                 calibration_max=world['calibration_max'], L=d.L, H=d.H,
                 true_locations=world['locations'].tolist(), proxies=d.centers.tolist(),
                 target_proxy=d.target_center.tolist(), radius=d.target_radius,
                 archive_observations=[collect(world,j,cfg['archive_participants']) for j in range(4)],
                 elapsed_seconds=perf_counter()-started)
    return rows, events, plans, choices, audit


def tasks(cfg):
    return [(cfg,s,g,r) for s,g,r in product(range(len(cfg['surfaces'])),
            range(len(cfg['scenarios'])),range(cfg['repetitions_per_cell']))]
