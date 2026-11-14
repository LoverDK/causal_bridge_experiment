"""Generate a concise report and predetermined single-world explanation from full raw."""
from pathlib import Path
import csv, hashlib, json, math
import numpy as np

ROOT=Path(__file__).resolve().parent
METHODS=json.loads((ROOT/'config.json').read_text())['methods']

def main():
    run=ROOT/'full'; manifest=json.loads((run/'manifest.json').read_text())
    audit=json.loads((run/'independent_verification.json').read_text())
    rows=list(csv.DictReader((run/'summary.csv').open(encoding='utf-8')))
    pairs=list(csv.DictReader((run/'paired.csv').open(encoding='utf-8')))
    designs=json.loads((run/'designs.json').read_text())
    timing=json.loads((ROOT/'timing.json').read_text())
    def wilson(v,n):
        p=v/n;z=1.959963984540054;den=1+z*z/n
        mid=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
        return p,max(0.,mid-half),min(1.,mid+half)
    discord=[]
    for r in pairs:
        record={k:r[k] for k in ['cell','geometry','precision','surface','K','u','rho','delta','left','right']}
        record['worlds']=5000
        for name in ['left_release_right_refuse','right_release_left_refuse']:
            v=int(r[name]);record[name+'_n']=v
            record[name],record[name+'_lo'],record[name+'_hi']=wilson(v,5000)
        discord.append(record)
    with (ROOT/'paired_discordance.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(discord[0]));w.writeheader();w.writerows(discord)
    def row(cell,rho,method,delta):
        return next(r for r in rows if int(r['cell'])==cell and float(r['rho'])==rho and r['method']==method and float(r['delta'])==delta)
    def percent(v):
        return '--' if v=='' else f'{100*float(v):.2f}%'
    def rate(r,key):
        return 'undefined' if r[key]=='' else f"{percent(r[key])} [{percent(r[key+'_lo'])}, {percent(r[key+'_hi'])}]"
    text=['# Selection-safe finite-sample comparison',
          '',f"Executed {manifest['independent_worlds']:,} independent synthetic worlds: 72 prespecified cells ×5,000, six methods, two paired selection strengths and three thresholds. Full runner {manifest['total_seconds']:.2f}s; independent raw-data reconstruction {audit['seconds']:.2f}s. All results and unfavorable cells retained.",
          '', '**Scope first.** This tests finite-sample validity after empirical-effect screening. It does not establish that adaptive screening is a useful transport policy, that adaptation improves efficiency, or that real mechanism sets/smoothness can be calibrated. It uses known Gaussian source noise, always-containing synthetic mechanism sets and declared oracle L/H. The convex Taylor geometry is a conservative outer certificate rather than exact original barycentric geometry or a sharp refusal region.',
          '', '**Design-only radius dominance is mathematical.** At identical inputs/budgets, min R2 ≤ R2(a(Y)) ≤ Rinf(a(Y)). The convex optimization dual certificate brackets the global optimum; saved feasible weights are within the reported tolerance, rather than an exact symbolic optimizer. No Rinf-vs-global-design release reversal can be interpreted as a possible benefit. Observed impossible reversals: '+str(audit['impossible_global_optimized_release_reversals'])+'. Maximum primal/dual gap '+f"{max(d['dual_gap'] for d in designs):.3g}"+'.',
          '', '## Prespecified null check',
          '','Balanced-near, equal precision, flat surface, K=16, zero ambiguity (cell 2), strong selection rho=1. This isolates reused-noise selection without transport error. Intervals below are individual 95% Monte Carlo Wilson intervals; widths are full certificate widths, including refused worlds.']
    for method in METHODS:
        r=row(2,1.,method,.3)
        released_mae=f"{float(r['released_MAE']):.4f}" if r['released_MAE'] else 'undefined'
        text.append(f"- {method}: coverage {rate(r,'coverage')}; mean width {float(r['width']):.4f}; release at delta=.30 {rate(r,'release')}; all-world MAE {float(r['all_MAE']):.4f}; released-world MAE {released_mae}.")
    analytic=next(a for a in audit['analytic_null_comparisons'] if a['cell']==2)
    text += ['',f"Exact null coverages from the Gaussian maximum distribution: reused sub-Gaussian pointwise radius {analytic['naive_expected']:.6f}, simultaneous radius {analytic['simultaneous_expected']:.6f}. The empirical check uses no fitted or target-tuned thresholds.",
             '', '## Full grid and paired tradeoffs',
             '', 'The complete cell/rho/method/threshold results are in `full/summary.csv`; `full/paired.csv` contains world-paired differences, MC standard errors, individual normal 95% intervals and both directions of release discordance. `paired_discordance.csv` gives cell-level Wilson 95% intervals for each discordance direction. No denominator treats repeated thresholds, methods or strengths as new worlds. Zero-release conditional metrics are empty/undefined. Conditional coverage and selective risk have empirical denominators and no nominal conditional theorem guarantee.']
    for rho in [.2,1.]:
        relevant=[r for r in rows if float(r['rho'])==rho and float(r['delta'])==.3]
        text.append(f"\nAt rho={rho:g}, ranges over the 72 cells at delta=.30 (ranges are descriptive, not pooled coverage estimates):")
        for method in METHODS:
            subset=[r for r in relevant if r['method']==method]
            cv=[float(r['coverage']) for r in subset];rel=[float(r['release']) for r in subset];mae=[float(r['all_MAE']) for r in subset]
            text.append(f"- {method}: coverage {100*min(cv):.2f}–{100*max(cv):.2f}%; release {100*min(rel):.2f}–{100*max(rel):.2f}%; all-world MAE {min(mae):.4f}–{max(mae):.4f}.")
    text += ['', 'Release discordances summed over all prespecified cell/strength/threshold evaluations (these are overlapping decisions, not independent worlds):']
    for method in METHODS[1:]:
        subset=[r for r in pairs if r['right']==method]
        n1=sum(int(r['left_release_right_refuse']) for r in subset)
        n2=sum(int(r['right_release_left_refuse']) for r in subset)
        text.append(f'- Rinf releases / {method} refuses: {n1:,}; reverse direction: {n2:,}.')
    text += ['', 'The Rinf-over-inverse-variance discordances occur only in the weak mixture (80% optimized design weights) on one-distant/heterogeneous/curved cells 44, 45 and 47 at delta=.60. This is compatible with a benefit of avoiding a geometry-blind precise distant source; it is not evidence that outcome adaptation itself improves efficiency. Uniform and optimized design weights have no reverse-release losses against Rinf in this grid.']
    text += ['', '## Prespecified geometry examples',
             '', 'Cells 23, 41, 47, 71 were selected by their design descriptions before full results; all other cells remain in the CSV. These examples are explanatory, not a winning subset.']
    for cell in [23,41,47,71]:
        d=designs[cell]
        text.append(f"\nCell {cell}: {d['geometry']}, {d['precision']}, {d['surface']}, K={d['K']}, u={d['u']}, strong selection, delta=.30.")
        for method in METHODS:
            r=row(cell,1.,method,.3)
            text.append(f"- {method}: coverage {rate(r,'coverage')}, release {rate(r,'release')}, selective risk {rate(r,'selective_risk')}, conditional coverage {rate(r,'conditional_coverage')}, width {float(r['width']):.4f}, all-world MAE {float(r['all_MAE']):.4f}.")
    text += ['', '## Audit and limits',
             '', f"Independent verifier reconstructed {audit['summary_rows_recomputed']:,} complete summary rows plus all paired differences from NPZ half-sample means, source/target locations, fixed weights and selection indices. Maximum estimate/radius discrepancy {audit['max_formula_difference']:.3g}; maximum geometry-bound excess {audit['max_geometry_violation']:.3g} (floating point). Source-halves SD is sqrt(2) times the full SD. Target-truth flips cannot enter policies, and changing evaluation half2 cannot change honest-half selection. Design weights have no outcome argument.",
             '', 'Common source resources are identical; splitting pays by discarding the selection half from evaluation. This is not a comparison to additional independent data at zero cost. No target outcome/truth informs selection. All synthetic inputs qualify, so refusal means radius exceeds tolerance, and every refusal still returns its computed outer certificate interval. No sharp-region calculation, bridge acquisition, real calibration or operational deployment cost is evaluated.',
             '', 'The independent checker is a separate implementation written by the same agent; root review of formulas/aggregates remains a distinct oversight step. Individual Monte Carlo intervals have no familywise guarantee. Numerical validity checks do not prove scientific usefulness.',
             '', '## Numerical timing',
             '', f"The shared 72 convex-design optimizations took {timing['shared_design_optimization_seconds']:.4f}s total (maximum per cell {timing['max_design_optimization_seconds']:.4f}s). A separate three-repeat timing audit reloaded the fixed raw inputs in {timing['raw_load_seconds']:.3f}s and recomputed each method independently over 720,000 world-strength evaluations per repetition. These are arithmetic timings; optimizer/setup, raw loading, scoring, NPZ compression and I/O are distinguished from policy arithmetic. They are not deployment cost estimates."]
    for method,seconds in timing['per_method_seconds'].items():
        text.append(f"- {method}: median {np.median(seconds):.4f}s, range {min(seconds):.4f}–{max(seconds):.4f}s; {np.median(seconds)/720000*1e6:.3f} microseconds per world-strength evaluation.")
    text += [
             '', '## Review follow-up',
             '', 'REV-01: saved one-world explanation; author understanding remains unverified. REV-02/07: adds paired outcome-dependent, legal split, optimized and simple-design comparisons, explicitly retaining design dominance and adverse adaptive errors. REV-03/11: method, bound, seed, code/config/raw hashes recorded; no TeX, abstract or global naming changes. REV-04/05: synthetic oracle sets and L/H only, no real calibration/certificate. REV-06: no Many Labs evidence. REV-08: no novelty or closest-work resolution. REV-09: restricted simplex class, no broad optimality. REV-10: no bridge/non-Gaussian extension. REV-12: joint/conditional errors and zero denominators separated; no sharp-region claim. All 12 prior statuses retained; none resolved.',
             '', 'Reproduce in a fresh copy of the code/config files: `python run.py --profile smoke`, `python verify.py smoke`, then after full authorization `python run.py --profile full`, `python verify.py full`, `python timing.py`, `python report.py`, `python audit_intervals.py`, `python report.py`. Existing run directories are protected against overwrite. Frozen configurations and raw per-cell NPZ files permit complete recomputation.']
    (ROOT/'results.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    # Predetermined one_distant/heterogeneous/linear/K4/u=.025 world zero.
    ci=41;z=np.load(run/'raw'/f'cell_{ci:03d}.npz');d=designs[ci]
    trace=dict(cell=d,world=0,half1=z['half1'][0].tolist(),half2=z['half2'][0].tolist(),
               full_mean=((z['half1'][0]+z['half2'][0])/2).tolist(),source_true_positions=z['actual_source'][0].tolist(),
               target_true_position=float(z['actual_target'][0]),target_truth=float(z['target_truth'][0]),
               scoring_only_fields=['source_true_positions','target_true_position','target_truth'],
               methods=METHODS,selection_strengths=[.2,1.],selected=z['selected'][:,0].tolist(),
               split_selected=z['split_selected'][:,0].tolist(),estimate=z['estimate'][:,:,0].tolist(),radius=z['radius'][:,:,0].tolist())
    (ROOT/'single_world.json').write_text(json.dumps(trace,indent=2))
    before=json.loads((ROOT/'review_before.json').read_text(encoding='utf-8-sig'))
    after={**before,'phase':'after','statuses_unchanged':True,'findings':'See results.md; no issue resolved.'}
    (ROOT/'review_after.json').write_text(json.dumps(after,indent=2,ensure_ascii=False),encoding='utf-8')
    rawledger=[dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((run/'raw').glob('*.npz'))]
    with (ROOT/'raw_file_ledger.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader();w.writerows(rawledger)
    artifacts=[p for p in ROOT.rglob('*') if p.is_file() and p.name!='manifest.json' and '__pycache__' not in str(p)]
    output=dict(experiment_id='SELECTION-SAFE-COMPARISON01',full_run=manifest,
                verification=audit,raw_npz_count=72,
                raw_root_absolute=str((run/'raw').resolve()),
                raw_npz_total_bytes=sum(r['bytes'] for r in rawledger),
                raw_npz_max_bytes=max(p.stat().st_size for p in (run/'raw').glob('*.npz')),
                hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts})
    (ROOT/'manifest.json').write_text(json.dumps(output,indent=2))
    print('Wrote results.md, single_world.json, review_after.json and top-level manifest.json')

if __name__=='__main__': main()
