"""Fixed-design moment-only bridge experiment; truth is confined to generator/scorer.

This is a new linear model experiment, not the original Causal ATLAS workflow.
The certificate is marginal over the declared random parameter and sampling noise.
"""
from __future__ import annotations

import copy
import itertools
import math

import numpy as np

METHODS = ('target_radius', 'logdet', 'frozen_random', 'direct_target')
FAMILIES = ('gaussian', 'rademacher', 'student_t5')


def normalized_config(frozen):
    """Map the frozen protocol schema; retain its values without rewriting the file."""
    cfg = copy.deepcopy(frozen)
    if frozen['parameter_distributions'] != frozen['noise_distributions']:
        raise ValueError('The protocol specifies the same three families in each factorial axis')
    cfg.update(noise_sd=frozen['individual_noise_sd'], max_batches=frozen['new_batches'],
               alpha=frozen['failure_probability'], main_halfwidth=frozen['scientific_halfwidth'],
               width_thresholds=frozen['full_width_thresholds'], distributions=frozen['parameter_distributions'],
               random_path_seed=frozen['seeds']['random_path'])
    cfg['history'] = [dict(id=f'h{i}', source_id=h['id'], feature=h['x'], participants=h['participants'])
                      for i, h in enumerate(frozen['initial_history'])]
    cfg['profiles'] = {profile: dict(seed=frozen['seeds'][profile], worlds_per_cell=frozen['replicates'][profile])
                       for profile in ['smoke', 'full']}
    return cfg


def standardized(rng, family, size):
    """Analytically centered, unit-variance primitives; never sample-standardized."""
    if family == 'gaussian':
        return rng.standard_normal(size)
    if family == 'rademacher':
        return 2.0 * rng.integers(0, 2, size=size) - 1.0
    if family == 'student_t5':
        return rng.standard_t(5, size=size) * math.sqrt(3.0 / 5.0)
    raise ValueError(f'Unrecognized distribution: {family}')


def validate_config(cfg):
    prior = np.asarray(cfg['prior_covariance'], float)
    target = np.asarray(cfg['target'], float)
    if prior.shape != (3, 3) or target.shape != (3,):
        raise ValueError('This frozen experiment uses three-dimensional features')
    np.linalg.cholesky(prior)
    if not np.allclose(prior, prior.T) or not 0 < cfg['alpha'] < 1:
        raise ValueError('Symmetric covariance and probability alpha are required')
    if cfg['noise_sd'] <= 0 or cfg['max_batches'] != 4:
        raise ValueError('Positive noise standard deviation and four batches required')
    if cfg['batch_participants'] % 2 or any(h['participants'] % 2 for h in cfg['history']):
        raise ValueError('Balanced treatment/control arms require even participant counts')
    if cfg['distributions'] != list(FAMILIES):
        raise ValueError('Preserve all three prespecified distribution families')
    for candidates in cfg['geometries'].values():
        if np.asarray(candidates).shape != (6, 3):
            raise ValueError('Each geometry has six three-dimensional candidate features')


def state_from_design(cfg, observations):
    """Compute the estimator and exact primitive moment budget, using design only."""
    prior = np.asarray(cfg['prior_covariance'], float)
    target = np.asarray(cfg['target'], float)
    features = np.asarray([o['feature'] for o in observations], float)
    variances = np.array([4 * cfg['noise_sd'] ** 2 / o['participants'] for o in observations])
    precision = np.linalg.inv(prior) + features.T @ (features / variances[:, None])
    inverse_precision = np.linalg.inv(precision)
    weights = (features @ inverse_precision @ target) / variances
    parameter_coefficients = features.T @ weights - target
    parameter_component = float(parameter_coefficients @ prior @ parameter_coefficients)
    noise_component = float(np.dot(weights * weights, variances))
    W = parameter_component + noise_component
    q = float(target @ inverse_precision @ target)
    if not np.isclose(W, q, rtol=1e-10, atol=1e-13):
        raise AssertionError('Primitive W must equal the LMMSE quadratic form q')
    return dict(ids=[o['id'] for o in observations], observations=copy.deepcopy(observations),
                features=features.tolist(), variances=variances.tolist(),
                inverse_precision=inverse_precision.tolist(), weights=weights.tolist(),
                parameter_coefficients=parameter_coefficients.tolist(),
                parameter_component=parameter_component, noise_component=noise_component,
                W=W, q=q, radius=math.sqrt(W / cfg['alpha']),
                path_radius=math.sqrt(W * (cfg['max_batches'] + 1) / cfg['alpha']))


def make_plans(cfg):
    """Freeze all paths before drawing any parameter or outcome."""
    validate_config(cfg)
    plans, scores, random_paths = {}, [], {}
    for geometry_index, (geometry, vectors) in enumerate(cfg['geometries'].items()):
        candidates = [dict(id=f'b{i}', feature=vector, participants=cfg['batch_participants'])
                      for i, vector in enumerate(vectors)]
        rng = np.random.default_rng(np.random.SeedSequence([cfg['random_path_seed'], geometry_index]))
        random_order = rng.permutation(len(candidates)).tolist()
        random_paths[geometry] = [f'b{i}' for i in random_order]
        for method in METHODS:
            observations = copy.deepcopy(cfg['history'])
            path = [state_from_design(cfg, observations)]
            path[0].update(stage=0, cost=0, selected=None)
            remaining = list(range(len(candidates)))
            for stage in range(1, cfg['max_batches'] + 1):
                current = path[-1]
                inverse_precision = np.asarray(current['inverse_precision'])
                target = np.asarray(cfg['target'])
                if method == 'direct_target':
                    selected = dict(id=f't{stage-1}', feature=cfg['target'],
                                    participants=cfg['batch_participants'])
                else:
                    evaluated = []
                    for i in remaining:
                        candidate = candidates[i]
                        nxt = state_from_design(cfg, observations + [candidate])
                        x = np.asarray(candidate['feature'])
                        noise_variance = 4 * cfg['noise_sd'] ** 2 / candidate['participants']
                        denom = noise_variance + float(x @ inverse_precision @ x)
                        sherman_gain = float(target @ inverse_precision @ x) ** 2 / denom
                        exact_gain = current['W'] - nxt['W']
                        if not np.isclose(exact_gain, sherman_gain, rtol=1e-9, atol=1e-13):
                            raise AssertionError('Exact W enumeration disagrees with Sherman gain')
                        score = dict(geometry=geometry, method=method, stage=stage,
                                     candidate=candidate['id'], W_before=current['W'], W_after=nxt['W'],
                                     exact_gain=exact_gain, sherman_gain=sherman_gain,
                                     logdet_gain=0.5 * math.log1p(float(x @ inverse_precision @ x) / noise_variance),
                                     feature_norm=float(np.linalg.norm(x)), noise_variance=noise_variance)
                        evaluated.append((i, score))
                    if method == 'target_radius':
                        chosen = min(evaluated, key=lambda z: (z[1]['W_after'], z[0]))[0]
                    elif method == 'logdet':
                        chosen = min(evaluated, key=lambda z: (-z[1]['logdet_gain'], z[0]))[0]
                    else:
                        chosen = next(i for i in random_order if i in remaining)
                    for i, score in evaluated:
                        score['selected'] = i == chosen
                        scores.append(score)
                    selected = candidates[chosen]
                    remaining.remove(chosen)
                observations.append(copy.deepcopy(selected))
                nxt = state_from_design(cfg, observations)
                nxt.update(stage=stage, cost=stage * cfg['batch_participants'], selected=selected['id'])
                if nxt['W'] > current['W'] + 1e-12:
                    raise AssertionError('Adding a fixed observation increased the moment variance')
                path.append(nxt)
            plans[(geometry, method)] = path
    return plans, scores, random_paths


class ObservationOracle:
    """Simulator only. The policy receives acquire(), never the latent parameter."""
    def __init__(self, cfg, seed, geometry_index, beta_index, noise_index, replicate):
        self.cfg = cfg
        self.key = [int(seed), geometry_index, beta_index, noise_index, replicate]
        self.noise_family = cfg['distributions'][noise_index]
        rng = np.random.default_rng(np.random.SeedSequence(self.key + [0]))
        primitive = standardized(rng, cfg['distributions'][beta_index], 3)
        self._beta = np.linalg.cholesky(np.asarray(cfg['prior_covariance'])) @ primitive
        self._cache = {}

    def acquire(self, observation):
        obsid = observation['id']
        if obsid not in self._cache:
            # Each arm and acquisition has an independent stream. Methods may reuse the
            # identical experimental action as paired potential observations, never across visits.
            channel = {'h': 10, 'b': 20, 't': 30}[obsid[0]]
            ordinal = int(obsid[1:])
            n = observation['participants']
            arms = []
            for arm in [0, 1]:
                rng = np.random.default_rng(np.random.SeedSequence(self.key + [channel, ordinal, arm]))
                arms.append(self.cfg['noise_sd'] * standardized(rng, self.noise_family, n // 2))
            effect = float(np.dot(observation['feature'], self._beta))
            control_mean = float(arms[0].mean())
            treated_mean = effect + float(arms[1].mean())
            self._cache[obsid] = dict(id=obsid, source_id=observation.get('source_id', obsid),
                                     feature=list(observation['feature']), participants=n,
                                     treated_n=n // 2, control_n=n // 2, treated_mean=treated_mean,
                                     control_mean=control_mean, observed_effect=treated_mean-control_mean,
                                     noise_variance=4 * self.cfg['noise_sd'] ** 2 / n,
                                     stream_key=self.key + [channel, ordinal])
        cached = self._cache[obsid]
        if cached['feature'] != list(observation['feature']) or cached['participants'] != observation['participants']:
            raise AssertionError('One acquisition identifier was reused for a different design')
        return copy.deepcopy(cached)

    def scoring_truth(self):
        return float(np.dot(self.cfg['target'], self._beta))

    def trace_truth(self):
        return dict(beta=self._beta.tolist(), target=self.scoring_truth())


def collect_mode(cfg, path, acquire, mode):
    """A real stopped acquisition or a real full prefix; no truth argument."""
    observations = {o['id']: acquire(o) for o in path[0]['observations']}
    rows, acquisitions = [], []
    stopped = False
    actual_stage = 0
    for budget_stage in range(cfg['max_batches'] + 1):
        if budget_stage and not stopped:
            actual_stage = budget_stage
            obs = acquire(path[actual_stage]['observations'][-1])
            observations[obs['id']] = obs
            acquisitions.append(dict(obs, stage=actual_stage))
        state = path[actual_stage]
        estimate = float(np.dot(state['weights'], [observations[i]['observed_effect'] for i in state['ids']]))
        released = state['radius'] <= cfg['main_halfwidth']
        row = dict(mode=mode, budget_stage=budget_stage, actual_stage=actual_stage,
                   available_participants=budget_stage * cfg['batch_participants'],
                   new_participants=state['cost'],
                   history_participants=sum(o['participants'] for o in cfg['history']),
                   total_participants=sum(o['participants'] for o in cfg['history'])+state['cost'],
                   estimate=estimate, radius=state['radius'],
                   width=2 * state['radius'], lower=estimate-state['radius'], upper=estimate+state['radius'],
                   path_radius=state['path_radius'], path_width=2 * state['path_radius'],
                   path_lower=estimate-state['path_radius'], path_upper=estimate+state['path_radius'],
                   W=state['W'], q=state['q'], parameter_component=state['parameter_component'],
                   noise_component=state['noise_component'], released=released,
                   scientific_halfwidth=cfg['main_halfwidth'],
                   output_type='released_estimate_and_moment_interval' if released else 'moment_interval_only',
                   selected=state['selected'], new_observation=bool(budget_stage and not stopped))
        rows.append(row)
        if mode == 'stopped' and released:
            stopped = True
    return rows, acquisitions


def score_rows(rows, truth):
    """Post-processing only: scoring truth cannot influence acquisition or release."""
    result = []
    prefix_covered = joint_covered = True
    for row in rows:
        scored = dict(row)
        error = row['estimate'] - truth
        covered = row['lower'] <= truth <= row['upper']
        simultaneous_covered = row['path_lower'] <= truth <= row['path_upper']
        prefix_covered = prefix_covered and covered
        joint_covered = joint_covered and simultaneous_covered
        scored.update(truth=truth, error=error, squared_error=error**2, absolute_error=abs(error),
                      covered=covered, path_interval_covered=simultaneous_covered,
                      all_pointwise_prefix_covered=prefix_covered, all_joint_prefix_covered=joint_covered,
                      interval_miss_on_release=bool(row['released'] and not covered),
                      bad_release_scientific=bool(row['released'] and abs(error) > row['scientific_halfwidth']))
        result.append(scored)
    return result


def run_world(cfg, profile, plans, geometry_index, beta_index, noise_index, replicate):
    geometry = list(cfg['geometries'])[geometry_index]
    oracle = ObservationOracle(cfg, cfg['profiles'][profile]['seed'], geometry_index,
                               beta_index, noise_index, replicate)
    identity = dict(geometry=geometry, beta_family=cfg['distributions'][beta_index],
                    noise_family=cfg['distributions'][noise_index], replicate=replicate,
                    world_id=f'{geometry_index}-{beta_index}-{noise_index}-{replicate}')
    records, acquisitions = [], []
    for method in METHODS:
        for mode in ['stopped', 'prefix']:
            rows, events = collect_mode(cfg, plans[(geometry, method)], oracle.acquire, mode)
            records.extend(dict(identity, method=method, **row) for row in score_rows(rows, oracle.scoring_truth()))
            acquisitions.extend(dict(identity, method=method, mode=mode, **event) for event in events)
    trace = None
    if replicate == 0:
        trace = dict(identity, scoring_truth=oracle.trace_truth(), history=[oracle.acquire(o) for o in cfg['history']],
                     records=records, acquisitions=acquisitions)
    history_records = [dict(identity, **oracle.acquire(o)) for o in cfg['history']]
    return records, acquisitions, trace, history_records


def jobs(cfg, profile):
    return itertools.product(range(len(cfg['geometries'])), range(len(cfg['distributions'])),
                             range(len(cfg['distributions'])), range(cfg['profiles'][profile]['worlds_per_cell']))
