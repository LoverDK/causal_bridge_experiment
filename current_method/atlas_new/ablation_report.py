"""Paired world-level summaries for the frozen attribution protocol."""
import json
import numpy as np
import pandas as pd
from scipy.stats import binom

from .ablations import VARIANTS

WORLD = ['surface','scenario','replicate']
METHOD = ['schedule','mode','method']
METRICS = ['released','bad_release','path_covered','new_n','error','width']


def save(df, out, name):
    df.to_csv(out/name, index=False, float_format='%.12g')


def validate(cfg, df, plans, out):
    checks = []
    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))
    worlds = cfg['repetitions_per_cell']*len(cfg['surfaces'])*len(cfg['scenarios'])
    variants = len(cfg['schedules'])*len(cfg['modes'])*len(VARIANTS)
    check('balanced plans', len(plans)==worlds*variants*(cfg['max_bridges']+1))
    check('balanced stopped records', len(df)==len(plans)*len(cfg['tolerances']))
    check('unique planned states', not plans.duplicated(WORLD+METHOD+['stage']).any())
    check('unique evaluated states', not df.duplicated(WORLD+METHOD+['tolerance','budget']).any())
    check('no unreported global optimum claim', not plans.global_optimum_certified.any())
    check('finite planned estimates and radii', np.isfinite(plans[['radius','estimate','error']]).all().all())
    check('same source prefixes across all variants',
          plans.assign(ids_key=plans.ids.map(tuple)).groupby(WORLD+['schedule','stage']).ids_key.nunique().eq(1).all())
    check('simplex feasible', all(min(a)>=0 and abs(sum(a)-1)<1e-8 for a in plans.weights))
    expected = plans.apply(lambda r:r[r['bound']+'_radius'], axis=1)
    check('saved radius is declared envelope', np.allclose(plans.radius, expected, rtol=0, atol=1e-10))
    check('minimum equals smaller bound at same weights',
          np.allclose(plans.minimum_radius, np.minimum(plans.barycentric_radius, plans.lipschitz_radius), atol=1e-10))
    covered = plans[plans.joint_set_covered]
    check('geometric bounds dominate actual causal bias on joint event',
          (covered.minimum_radius-covered.noise_radius+1e-9>=covered.causal_bias).all())
    check('release and bad release use prespecified tolerance',
          np.array_equal(df.released,df.radius<=df.tolerance) and
          np.array_equal(df.bad_release,df.released & (df.error>df.tolerance)))
    stop_valid = True
    for _, group in df.groupby(WORLD+METHOD+['tolerance'], sort=False):
        g = group.sort_values('budget')
        stop = g[g.released]
        if len(stop):
            first = stop.iloc[0]
            tail = g[g.budget>=first.budget]
            stop_valid &= all(tail[c].eq(first[c]).all() for c in ['new_n','radius','estimate','released'])
        stop_valid &= (g.new_n<=g.budget*cfg['participants_per_bridge']).all()
    check('actual cost and carry-forward stopping', stop_valid)
    for _, g in plans[plans.weight_rule.eq('optimized')].groupby(WORLD+METHOD, sort=False):
        if (np.diff(g.sort_values('stage').radius)>1e-8).any():
            check('optimized optional sources cannot worsen bound',False)
            break
    else:
        check('optimized optional sources cannot worsen bound',True)
    final = df[df.budget.eq(cfg['max_bridges'])]
    rows = []
    for keys,g in final.groupby(['surface','scenario']+METHOD+['tolerance']):
        failures = int((~g.path_covered).sum())
        rows.append(dict(zip(['surface','scenario']+METHOD+['tolerance'], keys))|
                    dict(n=len(g), failures=failures, p_value=float(binom.sf(failures-1,len(g),cfg['eta']+cfg['zeta']))))
    stat = pd.DataFrame(rows)
    stat['familywise_alpha'] = .01/len(stat)
    stat['violation_detected'] = stat.p_value<stat.familywise_alpha
    save(stat,out,'calibration_checks.csv')
    check('no path-coverage violation detected at familywise .01', not stat.violation_detected.any())
    (out/'validation_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    failures=[c['name'] for c in checks if not c['passed']]
    if failures:
        raise AssertionError('; '.join(failures))
    return checks


def summarize(cfg, df, plans, out):
    group = ['scenario']+METHOD+['tolerance','budget']
    def summary(frame, keys):
        records=[]
        for key,g in frame.groupby(keys):
            rel=g[g.released]
            row=dict(zip(keys,key))|dict(n_worlds=len(g),released_mae=rel.error.mean(),
                released_bad_rate=rel.bad_release.mean(),n_released=len(rel))
            row.update({m:float(g[m].mean()) for m in METRICS+['certificate_covered']})
            records.append(row)
        return pd.DataFrame(records)
    save(summary(df,group),out,'stopped_summary.csv')
    save(summary(df,['surface']+group),out,'stopped_cells.csv')
    fixed=[]
    for tolerance in cfg['tolerances']:
        f=plans.copy().rename(columns={'stage':'budget'})
        f['tolerance']=tolerance
        f['released']=f.radius<=tolerance
        f['bad_release']=f.released & (f.error>tolerance)
        f['width']=2*f.radius
        f['new_n']=f.budget*cfg['participants_per_bridge']
        # This is simultaneous coverage of release certificates along the full path.
        f=f.sort_values(WORLD+METHOD+['budget'])
        f['path_covered']=f.groupby(WORLD+METHOD).certificate_covered.cummin()
        fixed.append(f)
    fixed=pd.concat(fixed,ignore_index=True)
    save(summary(fixed,group),out,'fixed_budget_summary.csv')
    save(summary(fixed,['surface']+group),out,'fixed_budget_cells.csv')
    diagnostic=plans[plans.method.eq('optimized__minimum')].copy()
    diagnostic['bar_minus_min']=diagnostic.barycentric_radius-diagnostic.minimum_radius
    diagnostic['lip_minus_min']=diagnostic.lipschitz_radius-diagnostic.minimum_radius
    diagnostic['lip_tighter']=diagnostic.lipschitz_radius<diagnostic.barycentric_radius-1e-10
    diagnostic['bar_tighter']=diagnostic.barycentric_radius<diagnostic.lipschitz_radius-1e-10
    save(diagnostic.groupby(['surface','scenario','schedule','mode','stage'])[
        ['bar_minus_min','lip_minus_min','bar_tighter','lip_tighter']].mean().reset_index(),
        out,'same_weight_geometry.csv')
    # Resample independent worlds, preserving method pairs and surface strata.
    rng=np.random.default_rng(cfg['bootstrap_seed'])
    paired=[]
    for regime, frame in [('stopped',df),('fixed_budget',fixed)]:
        final=frame[frame.budget.eq(cfg['max_bridges'])]
        for keys,g in final.groupby(['scenario','schedule','mode','tolerance']):
            ref=g[g.method.eq('optimized__minimum')].set_index(['surface','replicate'])
            for method,h in g.groupby('method'):
                if method=='optimized__minimum':
                    continue
                comp=h.set_index(['surface','replicate']).reindex(ref.index)
                delta=ref[METRICS].astype(float)-comp[METRICS].astype(float)
                draws=np.zeros((cfg['bootstrap_repetitions'],len(METRICS)))
                for _,stratum in delta.groupby(level='surface'):
                    x=stratum.to_numpy()
                    sample=rng.integers(len(x),size=(cfg['bootstrap_repetitions'],len(x)))
                    draws+=x[sample].mean(axis=1)/len(cfg['surfaces'])
                for j,metric in enumerate(METRICS):
                    lo,hi=np.quantile(draws[:,j],[.025,.975])
                    paired.append(dict(zip(['scenario','schedule','mode','tolerance'],keys))|
                        dict(regime=regime,reference='optimized__minimum',comparator=method,metric=metric,
                             difference=delta[metric].mean(),lower=lo,upper=hi,n_worlds=len(ref)))
    save(pd.DataFrame(paired),out,'paired_differences.csv')


def write_report(cfg,out):
    frame=pd.read_csv(out/'stopped_summary.csv')
    pairs=pd.read_csv(out/'paired_differences.csv')
    lines=['# Weight and Geometry Attribution Experiments', '',
           f"Profile: {cfg['profile']}; independent worlds: {cfg['repetitions_per_cell']*9}.", '',
           'Post-review paired analysis on the existing synthetic DGP. These results do not compare ExAtlas.',
           'All bounds are valid under the declared model; local optimization is not globally certified.',
           'Common random and nearest acquisition prefixes isolate weights and envelopes. Each variant stops independently.',
           'Certificate guarantees are per policy, not simultaneous across all methods or conditional on release.', '',
           '## Final Stopped Outcomes', '',
           '| Scenario | Schedule | Certificate | Tolerance | Variant | Release % | Participants | Path coverage % | Bad release % | Released MAE |',
           '|---|---|---|---|---|---:|---:|---:|---:|---:|']
    for r in frame[frame.budget.eq(cfg['max_bridges'])].itertuples():
        mae='NA' if pd.isna(r.released_mae) else f'{r.released_mae:.4f}'
        lines.append(f'| {r.scenario} | {r.schedule} | {r.mode} | {r.tolerance} | {r.method} | {100*r.released:.2f} | {r.new_n:.2f} | {100*r.path_covered:.2f} | {100*r.bad_release:.2f} | {mae} |')
    lines+=['','## Paired Differences','',
            'Direction: optimized minimum minus comparator. Negative cost difference favors the reference.',
            'Intervals are individual exploratory 95% stratified paired bootstrap intervals, not familywise claims.','',
            '| Schedule | Certificate | Tolerance | Comparator | Metric | Difference | 95% interval |',
            '|---|---|---|---|---|---:|---|']
    selected=pairs[(pairs.scenario=='bridgeable')&(pairs.regime=='stopped')&pairs.metric.isin(['released','new_n'])]
    for r in selected.itertuples():
        lines.append(f'| {r.schedule} | {r.mode} | {r.tolerance} | {r.comparator} | {r.metric} | {r.difference:.4f} | [{r.lower:.4f}, {r.upper:.4f}] |')
    lines+=['','## Files','',
            '`records.csv`: all stopped outputs. `plans.jsonl`: all fixed-budget weights and counterfactual scores.',
            '`fixed_budget_summary.csv` and `stopped_summary.csv`: distinguish common-budget widths from refused-output widths.',
            '`same_weight_geometry.csv`: envelope gaps with exactly the same optimized-minimum weights.',
            '`paired_differences.csv`: all scenarios and both evaluation regimes; `stopped_cells.csv`: unpooled surfaces.',
            'No-release conditional MAEs remain missing. No negative results are omitted.']
    (out/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
