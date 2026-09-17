"""Matched-certificate weights and geometry on common design-only source paths."""
import json
from itertools import product

import numpy as np
from scipy.optimize import minimize

from .workflow import (make_world, objective_parts, certificate, optimize,
                       collect, execute, multipliers)

VARIANTS = [('optimized', 'minimum'), ('uniform', 'minimum'),
            ('inverse_variance', 'minimum'), ('nearest_source', 'minimum'),
            ('optimized', 'barycentric'), ('optimized', 'lipschitz')]


def weights(design, ids, rule):
    if rule == 'uniform':
        return np.full(len(ids), 1/len(ids))
    if rule == 'inverse_variance':
        precision = design.noise_sd[ids]**-2
        return precision/precision.sum()
    if rule == 'nearest_source':
        distance = np.linalg.norm(design.centers[ids]-design.target_center, axis=1)
        return np.eye(len(ids))[int(np.argmin(distance))]
    raise ValueError(rule)


def radius(design, ids, a, mode, bound):
    if bound == 'minimum':
        return certificate(design, ids, a, mode)
    if bound not in ('barycentric', 'lipschitz'):
        raise ValueError(bound)
    certificate(design, ids, a, mode)  # Validate the simplex independently of the branch.
    return objective_parts(design, ids, mode)(np.asarray(a), bound)[0]


def fit(design, ids, mode, rule, bound, warm=None):
    if rule != 'optimized':
        a = weights(design, ids, rule)
        return dict(ids=list(ids), weights=a.tolist(), radius=radius(design, ids, a, mode, bound),
                    solver_failures=0, solver_successes=0, global_optimum_certified=False)
    if bound == 'minimum':
        return optimize(design, ids, mode, warm)
    objective = objective_parts(design, ids, mode)
    k = len(ids)
    uniform = np.full(k, 1/k)
    candidates = [uniform, *np.eye(k)]
    if warm is not None:
        candidates.append(np.asarray(warm))
    scored = [(objective(a, bound)[0], a.copy()) for a in candidates]
    vertex = min(scored[1:k+1], key=lambda p: p[0])[1]
    failures = successes = 0
    for start in [uniform, vertex]:
        result = minimize(lambda a: objective(a, bound), start, jac=True, method='SLSQP',
                          bounds=[(0, 1)]*k,
                          constraints={'type':'eq', 'fun':lambda a:a.sum()-1,
                                       'jac':lambda a:np.ones(k)},
                          options={'maxiter':70, 'ftol':1e-8})
        if result.success and np.isfinite(result.x).all() and result.x.sum()>0:
            a = np.maximum(result.x, 0); a /= a.sum()
            scored.append((objective(a, bound)[0], a)); successes += 1
        else:
            failures += 1
    value, a = min(scored, key=lambda p:p[0])
    return dict(ids=list(ids), weights=a.tolist(), radius=value, solver_failures=failures,
                solver_successes=successes, global_optimum_certified=False)


def common_order(design, schedule, random_order):
    candidates = range(design.initial, len(design.centers))
    if schedule == 'random':
        return list(map(int, random_order))
    if schedule == 'nearest':
        return sorted(candidates, key=lambda j:(np.linalg.norm(design.centers[j]-design.target_center), j))
    raise ValueError(schedule)


def make_path(design, mode, rule, bound, order):
    path = []
    for stage in range(design.budget+1):
        ids = list(range(design.initial))+order[:stage]
        warm = np.r_[path[-1]['weights'], 0.] if path else None
        path.append(fit(design, ids, mode, rule, bound, warm))
    return path


def run_world(task):
    cfg, si, gi, rep = task
    world = make_world(cfg, si, gi, rep)
    design = world['design']
    meta = {k:world[k] for k in ['surface', 'scenario', 'replicate']}
    rng = np.random.default_rng(np.random.SeedSequence([cfg['seed'], si, gi, rep, 20]))
    random_order = rng.permutation(np.arange(4, 10))
    records, plans = [], []
    # These are fixed-budget counterfactual scores, never inputs to fit or order.
    observations = {j:collect(world, j, cfg['archive_participants'] if j<4 else
                              cfg['participants_per_bridge']) for j in range(10)}
    for schedule, mode, (rule, bound) in product(cfg['schedules'], cfg['modes'], VARIANTS):
        method = rule+'__'+bound
        tags = dict(**meta, schedule=schedule, mode=mode, method=method, weight_rule=rule, bound=bound)
        order = common_order(design, schedule, random_order)
        path = make_path(design, mode, rule, bound, order)
        for stage, p in enumerate(path):
            ids, a = p['ids'], np.array(p['weights'])
            q, _ = multipliers(design, mode)
            noise = q*(a@design.noise_sd[ids] if mode=='rinf' else np.linalg.norm(a*design.noise_sd[ids]))
            estimates = np.array([observations[j]['effect'] for j in ids])
            estimate = float(a@estimates)
            truth = float(world['truth'][-1])
            bounds = {b:radius(design, ids, a, mode, b) for b in ['minimum','barycentric','lipschitz']}
            error = abs(estimate-truth)
            causal_bias = abs(float(a@world['truth'][ids])-truth)
            if world['joint_set_covered'] and min(bounds.values())-noise+1e-9 < causal_bias:
                raise AssertionError('Geometric envelope failed on joint set event')
            plans.append(dict(**tags, stage=stage, **p, estimate=estimate, truth=truth,
                              error=error, certificate_covered=error<=p['radius'],
                              noise_radius=float(noise), causal_bias=causal_bias,
                              joint_set_covered=world['joint_set_covered'],
                              **{b+'_radius':v for b,v in bounds.items()}))
        for tolerance in cfg['tolerances']:
            # execute uses the certificate mode only; it does not choose weights.
            states, events = execute(cfg, world, 'rinf_targeted' if mode=='rinf' else 'r2_random', path, tolerance)
            for s in states:
                row = {k:s[k] for k in ['budget','new_n','radius','estimate','error','released','bad_release',
                                       'width','covered','path_covered','certificate_covered','joint_set_covered']}
                records.append(dict(**tags, tolerance=tolerance, **row))
            if len(events)*cfg['participants_per_bridge'] != states[-1]['new_n']:
                raise AssertionError('Actual stopped cost mismatch')
    return records, plans
