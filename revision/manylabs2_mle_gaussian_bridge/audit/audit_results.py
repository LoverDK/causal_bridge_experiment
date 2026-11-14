"""Independent numerical reconciliation; reads only new-branch simulated outputs.

No real target outcome file is read. This script does not run simulations or
change scientific outputs. Findings are written only inside the audit folder.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def run(result_dir=None):
    results = Path(result_dir) if result_dir else ROOT / 'results'
    diag = pd.read_csv(results / 'gaussian_approximation_results.csv')
    cells = pd.read_csv(results / 'simulation_cell_counts.csv')
    findings = []
    checks = []
    freeze_path = ROOT / 'audit' / 'full_run_freeze.json'
    if freeze_path.exists():
        freeze = json.loads(freeze_path.read_text(encoding='utf-8-sig'))
        mismatches = [name for name, digest in freeze['files'].items()
                      if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest]
        checks.append({'check': 'pre_run_frozen_inputs_and_code', 'frozen_files': len(freeze['files']),
                       'mismatches': mismatches})
        if mismatches:
            findings.append('REVIEW: frozen files differ; assess any explicitly recorded technical amendment')
    keys = ['scenario', 'dgp', 'scale', 'site']
    expected = []
    for key, g in cells.groupby(keys, sort=False):
        active = g['profile'].to_numpy() > 0
        n = g['n'].to_numpy(dtype=int)
        q = g['q'].to_numpy(dtype=float)
        p = g['profile'].to_numpy(dtype=float)
        occupied = (n > 0) | ~active
        identified = bool(occupied.all())
        s = float(np.prod(1 - q[active] ** n[active] - (1 - q[active]) ** n[active])) if identified else 0.
        variance = float(np.sum(p[active] ** 2 * q[active] * (1 - q[active]) / n[active])) if identified else np.nan
        cumulant4 = float(np.sum(p[active] ** 4 * q[active] * (1 - q[active]) * (1 - 6*q[active]*(1-q[active])) / n[active]**3)) if identified else np.nan
        expected.append(dict(zip(keys, key)) | {'exact_finite_beta_rate': s, 'exact_identified': identified,
                                               'exact_variance': variance, 'exact_fourth_cumulant': cumulant4,
                                               'exact_n': int(n.sum())})
    exact = pd.DataFrame(expected)
    joined = diag.merge(exact, on=keys, how='left', validate='many_to_one')
    if joined['exact_n'].isna().any():
        findings.append('FAIL: diagnostic rows without matching count schedules')
    if not np.array_equal(joined['n'].to_numpy(), joined['exact_n'].to_numpy()):
        findings.append('FAIL: count totals disagree with diagnostic n')
    if not np.array_equal(joined['identified'].to_numpy(), joined['exact_identified'].to_numpy()):
        findings.append('FAIL: active-cell identifiability flags disagree')
    unique = joined.drop_duplicates(keys)
    tolerance = 6 * np.sqrt(unique['exact_finite_beta_rate'] * (1 - unique['exact_finite_beta_rate']) / unique['replications']) + 1 / unique['replications']
    outside = abs(unique['finite_beta_rate'] - unique['exact_finite_beta_rate']) > tolerance
    if outside.any():
        findings.append(f'REVIEW: {int(outside.sum())} finite-MLE frequencies exceed six-MCSE analytic tolerance')
    checks.append({'check': 'finite_MLE_analytic_probability', 'rows': len(unique), 'outside_six_MCSE': int(outside.sum()),
                   'max_absolute_error': float(abs(unique['finite_beta_rate'] - unique['exact_finite_beta_rate']).max())})
    oracle = joined[(joined['estimator'] == 'extended_probability_mle') & (joined['variance'] == 'oracle')]
    mask = oracle['exact_identified']
    rel = abs(oracle.loc[mask, 'mean_delta_variance'] / oracle.loc[mask, 'exact_variance'] - 1)
    if (rel > 1e-10).any():
        findings.append('FAIL: oracle variance differs from independently computed exact binomial variance')
    checks.append({'check': 'oracle_variance_identity', 'identified_rows': int(mask.sum()),
                   'max_relative_error': float(rel.max()) if len(rel) else None})
    ident = oracle.loc[mask].copy()
    mean_z = abs(ident['bias']) / np.sqrt(ident['exact_variance'] / ident['replications'])
    variance_mcse = np.sqrt(np.maximum(0, ident['exact_fourth_cumulant']/ident['replications'] +
                                      2*ident['exact_variance']**2/(ident['replications']-1)))
    variance_z = abs(ident['empirical_variance'] - ident['exact_variance']) / variance_mcse
    checks.append({'check': 'extended_estimator_exact_moment_MC_reconciliation',
                   'max_absolute_bias_MC_z': float(mean_z.max()) if len(mean_z) else None,
                   'max_absolute_variance_MC_z': float(variance_z.max()) if len(variance_z) else None,
                   'bias_outside_six_MCSE': int((mean_z > 6).sum()),
                   'variance_outside_six_MCSE': int((variance_z > 6).sum())})
    if (mean_z > 6).any() or (variance_z > 6).any():
        findings.append('REVIEW: extended estimator moment deviates from exact expectation by more than six MCSE')
    grouped = diag.groupby(['scenario', 'dgp', 'scale', 'estimator', 'variance']).size()
    if not (grouped == 57).all():
        findings.append('FAIL: at least one condition/estimator/variance has a denominator other than 57 sites')
    checks.append({'check': 'all_site_denominators', 'groups': len(grouped),
                   'minimum_rows': int(grouped.min()), 'maximum_rows': int(grouped.max())})
    if not ((diag['coverage90_unconditional'] <= diag['valid_rate'] + 1e-12) &
            (diag['coverage95_unconditional'] <= diag['valid_rate'] + 1e-12)).all():
        findings.append('FAIL: unconditional coverage exceeds estimator/SE valid mass')
    # All probabilities below are simulation truths, not real target outcomes.
    if not ((cells['q'] > 0) & (cells['q'] < 1)).all():
        findings.append('FAIL: DGP probabilities leave open unit interval')
    if not (cells['n'] >= 0).all():
        findings.append('FAIL: negative allocation')
    protocol_path = ROOT / 'protocol' / 'execution.json'
    if protocol_path.exists():
        protocol = json.loads(protocol_path.read_text(encoding='utf-8-sig'))
        arms = {site: np.asarray(protocol['arm_sizes'][j]) for j, site in enumerate(protocol['sites'])}
        observed_totals = cells.groupby(keys + ['treatment'])['n'].sum().reset_index()
        bad_totals = sum(int(row.n) != int(row.scale)*int(arms[row.site][int(row.treatment)])
                         for row in observed_totals.itertuples())
        checks.append({'check': 'historical_arm_ratio_and_scaled_size_preservation',
                       'arm_schedules': len(observed_totals), 'disagreements': bad_totals})
        if bad_totals:
            findings.append('FAIL: simulated arm totals do not preserve original scaled arm sizes')
    exhaustive_path = results / 'bernoulli_monte_carlo_results.csv'
    comparison_path = results / 'bridge_design_comparison.csv'
    if exhaustive_path.exists() and comparison_path.exists():
        risks = pd.read_csv(exhaustive_path)
        policies = pd.read_csv(comparison_path)
        z = abs(risks['extended_mc_mse'] - risks['exact_bernoulli_mse']) / risks['extended_mc_mse_se']
        checks.append({'check': 'exhaustive_expected_risk_MC_reconciliation', 'rows': len(risks),
                       'maximum_absolute_MC_z': float(z.max()), 'outside_six_MCSE': int((z > 6).sum())})
        if (z > 6).any():
            findings.append('REVIEW: at least one exhaustive subset MC risk differs from exact risk by more than six MCSE')
        policy_keys = ['scenario', 'dgp', 'scale', 'noise_model', 'budget']
        wrong_mc = wrong_exact = wrong_logdet = bad_greedy = bad_random = 0
        for key, g in risks.groupby(policy_keys, sort=False):
            subset = policies.copy()
            for field, value in zip(policy_keys, key):
                subset = subset[subset[field] == value]
            subset = subset[subset['estimator'] == 'extended_probability_mle']
            by_policy = subset.set_index('policy')
            if by_policy.empty:
                continue
            exact_row = g.loc[g['exact_bernoulli_mse'].idxmin()]
            mc_row = g.loc[g['pilot_mc_mse'].idxmin()]
            log_row = g.loc[g['information_gain'].idxmax()]
            wrong_mc += int(by_policy.loc['bernoulli_mc_exhaustive_oracle', 'selected_sites'] != mc_row['subset'])
            wrong_exact += int(by_policy.loc['bernoulli_exhaustive_oracle', 'selected_sites'] != exact_row['subset'])
            wrong_logdet += int(by_policy.loc['logdet_exhaustive', 'selected_sites'] != log_row['subset'])
            b = int(key[-1])
            bad_greedy += int(by_policy.loc['logdet_greedy', 'information_gain'] + 1e-10 < (1-(1-1/b)**b)*log_row['information_gain'])
            bad_random += int(abs(by_policy.loc['random_uniform_expectation', 'exact_bernoulli_mse'] - g['exact_bernoulli_mse'].mean()) > 1e-12)
        checks.append({'check': 'independent_subset_policy_reconstruction', 'mc_oracle_mismatches': wrong_mc,
                       'analytic_oracle_mismatches': wrong_exact, 'logdet_optimum_mismatches': wrong_logdet,
                       'greedy_bound_violations': bad_greedy, 'uniform_risk_average_mismatches': bad_random})
        if wrong_mc + wrong_exact + wrong_logdet + bad_greedy + bad_random:
            findings.append('FAIL: at least one exhaustive policy or objective invariant does not reconstruct')
    output = {'result_directory': str(results.resolve()), 'findings': findings,
              'checks': checks, 'diagnostic_rows': len(diag), 'cell_rows': len(cells)}
    (ROOT / 'audit' / 'numerical_audit_summary.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    joined.to_csv(ROOT / 'audit' / 'analytic_failure_reconciliation.csv', index=False)
    print(json.dumps(output, indent=2))
    return output


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--results', type=Path)
    args = parser.parse_args()
    run(args.results)
