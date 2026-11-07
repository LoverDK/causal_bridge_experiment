"""Read-only deterministic allocation audit: no outcome simulation.

The optimizer supplies feasible allocations; a separate analytic inequality
supplies global lower bounds regardless of optimizer convergence.
"""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import time
import numpy as np
import scipy
from scipy.optimize import minimize, brentq

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'reproduced/main_theorem_workflow01/full'
ARCHIVE = ROOT / 'current_method/results/full/bridge_designs.json'
QREQ = .05 * .30**2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_one(d):
    did = d['replicate']
    P = np.asarray(d['prior'], float)
    B = np.linalg.inv(P)
    X = np.asarray(d['design'], float)
    v = np.asarray(d['sigma'], float)**2
    t = np.asarray(d['target'], float)
    plans = json.loads((RAW / f'design_{did:03d}_plans.json').read_text())
    g = plans['target_radius']['path'][-1]
    greedy = np.asarray(g['counts'][:len(X)], float)
    direct = plans['direct_target']['stop_stage']
    scale = greedy.sum()

    def evaluate(n):
        A = B + np.einsum('i,ij,ik->jk', n/v, X, X)
        z = np.linalg.solve(A, t)
        return float(t @ z), z

    def fun(w):
        return float(np.sum(w))

    def jac(w):
        return np.ones_like(w)

    def constraint(w):
        q, _ = evaluate(scale*w)
        return 1 - q/QREQ

    def cjac(w):
        _, z = evaluate(scale*w)
        return scale * (X @ z)**2/v/QREQ

    start = time.perf_counter()
    opt = minimize(fun, greedy/scale, jac=jac, bounds=[(0, None)]*len(X),
                   constraints={'type':'ineq', 'fun':constraint, 'jac':cjac},
                   method='SLSQP', options={'maxiter':1000, 'ftol':1e-12})
    n = np.maximum(opt.x*scale, 0)
    n[n < 1e-8] = 0  # Remove numerical inactive coordinates, then restore feasibility.
    q, z = evaluate(n)
    if q > QREQ*(1-1e-10):
        hi = 1.001
        while evaluate(hi*n)[0] > QREQ*(1-1e-10):
            hi *= 2
        multiplier = brentq(lambda a:evaluate(a*n)[0]-QREQ*(1-1e-10),
                            1, hi, xtol=1e-13)
        n *= multiplier
    q, z = evaluate(n)

    def certificate(direction):
        direction = direction / np.linalg.norm(direction)
        numerator = float(t @ direction)**2/QREQ-float(direction @ B @ direction)
        denominator = float(np.max((X @ direction)**2/v))
        if denominator <= 0:
            return dict(z=direction.tolist(), numerator=numerator,
                        denominator=denominator, lower=float('inf') if numerator>0 else 0.)
        return dict(z=direction.tolist(), numerator=numerator, denominator=denominator,
                    lower=max(0., numerator/denominator))

    _, zg = evaluate(greedy)
    cg, co = certificate(zg), certificate(z)
    cert = max([cg, co], key=lambda c:c['lower'])
    lower = cert['lower']
    margin = max(1., abs(lower))*1e-6
    lower_safe = max(0., lower-margin)
    # Each coordinate rounds upward, so information increases. Explicitly check.
    integer = np.ceil(n).astype(int)
    ceil_cost = int(integer.sum())
    ceil_q, _ = evaluate(integer)
    assert ceil_q <= QREQ*(1+1e-10)
    # Remove redundant rounded-up observations when feasibility remains intact.
    while True:
        removals = []
        for k in np.flatnonzero(integer):
            trial = integer.copy(); trial[k] -= 1
            trial_q, _ = evaluate(trial)
            if trial_q <= QREQ*(1-1e-10):
                removals.append((trial_q, int(k), trial))
        if not removals:
            break
        integer = min(removals, key=lambda item:(item[0], item[1]))[2]
    integer_q, _ = evaluate(integer)
    assert q <= QREQ*(1+1e-10)
    assert lower <= n.sum() + 1e-6*max(1., n.sum())
    assert integer_q <= QREQ*(1+1e-10)
    assert int(integer.sum()) >= lower_safe
    row = dict(design_id=did, greedy_cost=int(scale), direct_cost=int(direct),
               optimizer_success=bool(opt.success), optimizer_status=int(opt.status),
               optimizer_iterations=int(opt.nit), continuous_feasible_cost=float(n.sum()),
               continuous_q=q, global_lower_bound=lower, numeric_margin=margin,
               conservative_lower_bound=lower_safe,
               continuous_gap=float(n.sum()-lower),
               relative_gap=float((n.sum()-lower)/max(1., n.sum())),
               greedy_direction_lower_bound=cg['lower'],
               optimized_direction_lower_bound=co['lower'],
               ceil_integer_upper=ceil_cost, integer_feasible_upper=int(integer.sum()),
               integer_q=integer_q, lower_exceeds_direct=lower_safe>direct,
               lower_excludes_strict_saving=lower_safe>direct-1,
               integer_upper_cheaper_than_direct=int(integer.sum())<direct,
               lower_minus_direct=lower-direct,
               elapsed_seconds=time.perf_counter()-start)
    detail = dict(**row, optimizer_message=str(opt.message), continuous_allocation=n.tolist(),
                  integer_allocation=integer.tolist(), greedy_allocation=greedy.tolist(),
                  selected_certificate=cert, greedy_certificate=cg,
                  optimized_certificate=co)
    return row, detail


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=200)
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    out=Path(args.output); out.mkdir(parents=True, exist_ok=False)
    start=time.perf_counter()
    designs=json.loads(ARCHIVE.read_text())[:args.limit]
    rows=[];details=[]
    for d in designs:
        row, detail=solve_one(d)
        rows.append(row);details.append(detail)
        if len(rows)%10==0 or len(rows)==len(designs):
            print(f'Allocation audit {len(rows)}/{len(designs)}; elapsed {time.perf_counter()-start:.2f}s', flush=True)
    with (out/'per_design_bounds.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/'allocation_certificates.json').write_text(json.dumps(details,indent=2),encoding='utf-8')
    arr=lambda key:np.asarray([r[key] for r in rows])
    summary=dict(status='complete',kind='deterministic_design_audit_no_outcome_sampling',
        design_count=len(rows),q_threshold=QREQ,alpha=.05,full_width_threshold=.60,
        archive_sha256=sha(ARCHIVE),main_manifest_sha256=sha(RAW/'run_manifest.json'),
        script_sha256=sha(Path(__file__)),scipy_version=scipy.__version__,numpy_version=np.__version__,
        optimizer_success_count=int(arr('optimizer_success').sum()),
        lower_exceeds_direct_count=int(arr('lower_exceeds_direct').sum()),
        lower_excludes_strict_saving_count=int(arr('lower_excludes_strict_saving').sum()),
        integer_feasible_cheaper_count=int(arr('integer_upper_cheaper_than_direct').sum()),
        max_continuous_gap=float(arr('continuous_gap').max()),
        max_relative_gap=float(arr('relative_gap').max()),
        median_greedy_over_lower=float(np.median(arr('greedy_cost')/arr('global_lower_bound'))),
        max_greedy_over_lower=float(np.max(arr('greedy_cost')/arr('global_lower_bound'))),
        median_continuous_cost=float(np.median(arr('continuous_feasible_cost'))),
        median_integer_upper=float(np.median(arr('integer_feasible_upper'))),
        min_lower_minus_direct=float(arr('lower_minus_direct').min()),
        elapsed_seconds=time.perf_counter()-start,
        numerical_scope='Float64 analytic lower-bound certificates with 1e-6 relative downward safety margin; not interval-arithmetic or Lean validation.',
        scientific_scope='Fixed archived candidates, known prior/noise moments, unit study costs, linear moment-optimal W. Not impossibility for every statistical method or new candidate menu.')
    (out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':
    main()
