"""Cost/precision analysis of frozen full-prefix and stopped-policy outputs.

No simulator is called here. Empty, infinite and not-yet-attained outputs remain
visible; pairing is by world and pooled bootstrap resampling stays within surface.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

WORLD = ['surface', 'scenario', 'replicate']
CELL = ['surface', 'scenario', 'method', 'tolerance', 'budget']
LABELS = {'r2_targeted': 'Targeted R2', 'rinf_targeted': 'Targeted R-infinity',
          'r2_random': 'Random R2', 'r2_nearest': 'Nearest R2',
          'r2_static': 'Archive only', 'target_only': 'Direct target'}
COLORS = {'r2_targeted': '#0F4D92', 'rinf_targeted': '#3775BA',
          'r2_random': '#42949E', 'r2_nearest': '#8E6A23',
          'r2_static': '#767676', 'target_only': '#B64342'}
MARKERS = {'r2_targeted': 'o', 'rinf_targeted': 's', 'r2_random': '^',
           'r2_nearest': 'D', 'r2_static': 'X', 'target_only': 'v'}
ANALYSIS_SEED = 2026110799


def save(frame, path):
    frame.to_csv(path, index=False, float_format='%.12g')


def wilson(k, n, z=1.959963984540054):
    if not n:
        return math.nan, math.nan
    p = k/n
    den = 1 + z*z/n
    mid = (p + z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return max(0., mid-half), min(1., mid+half)


def strict_mean(values):
    x = np.asarray(values, dtype=float)
    return float(np.mean(x)) if len(x) and not np.isnan(x).any() else math.nan


def strict_quantile(values, p):
    x = np.asarray(values, dtype=float)
    # Order statistics avoid inf - inf interpolation at the unbounded origin.
    return float(np.quantile(x, p, method='inverted_cdf')) if len(x) and not np.isnan(x).any() else math.nan


def load_records(path):
    df = pd.read_csv(path)
    for col in ['released', 'bad_release', 'covered', 'path_covered', 'joint_set_covered']:
        if df[col].dtype != bool:
            mapping = {'True': True, 'False': False, 'true': True, 'false': False,
                       '1': True, '0': False}
            converted = df[col].astype(str).map(mapping)
            if converted.isna().any():
                raise ValueError(f'Invalid Boolean in {path.name}: {col}')
            df[col] = converted.astype(bool)
    df['release_tolerance'] = df['tolerance']
    df['valid_finite_interval'] = (df.interval_status.eq('finite') &
        np.isfinite(df.lower) & np.isfinite(df.upper) & (df.lower <= df.upper))
    df['interval_precision_met'] = (df.valid_finite_interval &
        (df.output_halfwidth <= df.tolerance))
    return df


def validate_inputs(cfg, frames):
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
    expected_worlds = len(cfg['surfaces'])*len(cfg['scenarios'])*cfg['repetitions_per_cell']
    expected = expected_worlds*len(cfg['methods'])*len(cfg['tolerances'])*(cfg['max_bridges']+1)
    for mode, df in frames.items():
        check(mode+' balanced record count', len(df) == expected)
        check(mode+' unique world method tolerance budget', not df.duplicated(WORLD+['method','tolerance','budget']).any())
        check(mode+' all expected worlds', len(df[WORLD].drop_duplicates()) == expected_worlds)
        finite = df.valid_finite_interval
        check(mode+' finite halfwidth matches endpoints', np.allclose(
            df.loc[finite, 'output_halfwidth'],
            (df.loc[finite, 'upper']-df.loc[finite, 'lower'])/2, rtol=0, atol=1e-8))
        check(mode+' original release rule unchanged', np.array_equal(df.released, df.radius <= df.tolerance))
        check(mode+' invalid not counted as precision success',
              not df.loc[~finite, 'interval_precision_met'].any())
        check(mode+' target origin explicitly unbounded',
              np.isposinf(df[(df.method=='target_only') & (df.budget==0)].output_halfwidth).all())
        if mode == 'prefix':
            active = df.method.ne('r2_static')
            check('prefix actual cost equals sampled budget',
                  (df.loc[active, 'new_n'] == df.loc[active, 'budget']*cfg['participants_per_bridge']).all())
            check('static cost stays zero', (df.loc[~active, 'new_n']==0).all())
    failed = [r['name'] for r in checks if not r['passed']]
    if failed:
        raise AssertionError('; '.join(failed))
    return checks


def one_summary(meta, g):
    h = g.output_halfwidth.to_numpy(float)
    finite = g.valid_finite_interval.to_numpy(bool)
    row = dict(meta, n_worlds=len(g), release_tolerance=float(meta['tolerance']),
        mean_actual_cost=float(g.new_n.mean()), min_actual_cost=float(g.new_n.min()),
        max_actual_cost=float(g.new_n.max()),
        n_finite=int(finite.sum()), n_unbounded=int(g.interval_status.eq('unbounded').sum()),
        n_inconsistent=int(g.interval_status.eq('inconsistent').sum()),
        n_missing_halfwidth=int(np.isnan(h).sum()),
        mean_halfwidth=strict_mean(h), median_halfwidth=strict_quantile(h,.5),
        q10_halfwidth=strict_quantile(h,.1), q90_halfwidth=strict_quantile(h,.9),
        mean_halfwidth_given_finite=strict_mean(h[finite]),
        mean_certificate_radius=strict_mean(g.radius),
        midpoint_mae_given_finite=strict_mean(g.loc[finite,'midpoint_abs_error']),
        n_released=int(g.released.sum()),
        original_point_mae_given_released=strict_mean(g.loc[g.released,'error']),
        n_original_estimates_with_observations=int((g.source_ids.ne('[]') | g.new_n.gt(0)).sum()))
    observed = g.source_ids.ne('[]') | g.new_n.gt(0)
    row['original_point_mae_observed_diagnostic'] = strict_mean(g.loc[observed,'error'])
    for col in ['covered','path_covered','released','bad_release','interval_precision_met']:
        k = int(g[col].sum()); row[col] = k/len(g)
        row[col+'_lower'], row[col+'_upper'] = wilson(k,len(g))
    return row


def summaries(cfg, frames):
    result=[]
    for mode, df in frames.items():
        for keys,g in df.groupby(CELL,sort=True):
            meta=dict(zip(CELL,keys),mode=mode,scope='cell')
            meta['available_budget_n']=int(meta['budget']*cfg['participants_per_bridge'])
            result.append(one_summary(meta,g))
        cols=['scenario','method','tolerance','budget']
        for keys,g in df.groupby(cols,sort=True):
            # Balanced cells make the all-world mean equal to equal-surface mean.
            if g.groupby('surface').size().nunique()!=1:
                raise AssertionError('Pooled summary requires equal-sized surface strata')
            meta=dict(zip(cols,keys),surface='ALL',mode=mode,scope='pooled')
            meta['available_budget_n']=int(meta['budget']*cfg['participants_per_bridge'])
            result.append(one_summary(meta,g))
    return pd.DataFrame(result)


def attainment_records(cfg, prefix):
    rows=[]
    keys=WORLD+['method','tolerance']
    for values,g in prefix.groupby(keys,sort=True):
        meta=dict(zip(keys,values)); g=g.sort_values('budget')
        for criterion in ['certificate','returned_interval']:
            hit = g.released if criterion=='certificate' else g.interval_precision_met
            attained=bool(hit.any()); first=g[hit].iloc[0] if attained else None
            row=dict(meta, release_tolerance=float(meta['tolerance']),
                precision_target=float(meta['tolerance']), criterion=criterion,
                attained=attained, right_censored=not attained,
                first_hit_budget=int(first.budget) if attained else math.nan,
                first_hit_cost=float(first.new_n) if attained else math.nan,
                spent_until_hit_or_horizon=float(first.new_n if attained else g.iloc[-1].new_n),
                horizon_actual_cost=float(g.iloc[-1].new_n),
                first_hit_halfwidth=float(first.output_halfwidth) if attained else math.nan,
                first_hit_radius=float(first.radius) if attained else math.nan,
                hit_error=float(first.error if criterion=='certificate' else first.midpoint_abs_error) if attained else math.nan,
                hit_covered=bool(first.covered) if attained else False,
                path_covered=bool(g.iloc[-1].path_covered))
            row['bad_attainment']=bool(attained and row['hit_error'] > row['precision_target'])
            rows.append(row)
    return pd.DataFrame(rows)


def attainment_summary(cfg, records):
    rows=[]
    for scope,cols in [('cell',['surface','scenario','method','tolerance','criterion']),
                       ('pooled',['scenario','method','tolerance','criterion'])]:
        for keys,g in records.groupby(cols,sort=True):
            meta=dict(zip(cols,keys),scope=scope); meta.setdefault('surface','ALL')
            meta['release_tolerance']=float(meta['tolerance'])
            meta['precision_target']=float(meta['tolerance'])
            for budget in range(cfg['max_bridges']+1):
                reached=g.attained & g.first_hit_budget.le(budget)
                costs=np.where(reached,g.first_hit_cost,
                    np.minimum(g.horizon_actual_cost,budget*cfg['participants_per_bridge']))
                k=int(reached.sum()); n=len(g)
                lo,hi=wilson(k,n)
                rows.append(dict(meta,budget=budget,available_budget_n=budget*cfg['participants_per_bridge'],
                    n_worlds=n,n_attained=k,n_not_attained=n-k,attainment_rate=k/n,
                    attainment_lower=lo,attainment_upper=hi,
                    mean_spent_until_hit_or_budget=float(np.mean(costs)),
                    mean_hit_cost_given_attained=strict_mean(g.loc[reached,'first_hit_cost']),
                    mean_cost_to_attainment_all_worlds=float(g.first_hit_cost.mean()) if k==n else math.inf,
                    bad_attainment_rate=float((reached & g.bad_attainment).mean()),
                    hit_coverage_given_attained=float(g.loc[reached,'hit_covered'].mean()) if k else math.nan))
    return pd.DataFrame(rows)


def bootstrap_differences(diff, strata, key, repetitions):
    """Pointwise percentile CIs; all rows of one world stay paired."""
    digest=hashlib.sha256(str(key).encode('utf-8')).digest()
    rng=np.random.default_rng(np.random.SeedSequence([ANALYSIS_SEED,int.from_bytes(digest[:4],'little')]))
    x=np.asarray(diff,float); strata=np.asarray(strata)
    draws=np.zeros((repetitions,x.shape[1]))
    levels=np.unique(strata)
    for level in levels:
        xs=x[strata==level]
        varied=np.ptp(xs,axis=0)>1e-14
        contribution=np.tile(xs.mean(axis=0),(repetitions,1))
        if varied.any():
            indices=rng.integers(len(xs),size=(repetitions,len(xs)))
            contribution[:,varied]=xs[:,varied][indices].mean(axis=1)
        draws+=contribution/len(levels)
    return np.quantile(draws,[.025,.975],axis=0)


def paired_comparisons(cfg,prefix):
    rows=[]; B=int(cfg.get('bootstrap_repetitions',2000))
    for scope,cols in [('cell',['surface','scenario','tolerance','budget']),
                       ('pooled',['scenario','tolerance','budget'])]:
        for values,g in prefix.groupby(cols,sort=True):
            meta=dict(zip(cols,values),scope=scope);meta.setdefault('surface','ALL')
            a=g[g.method=='r2_targeted'].set_index(WORLD).sort_index()
            for comparator in cfg['methods']:
                if comparator=='r2_targeted':continue
                b=g[g.method==comparator].set_index(WORLD).reindex(a.index)
                if b.method.isna().any():raise AssertionError('Unmatched world in paired comparison')
                metrics=['output_halfwidth','new_n','covered','path_covered','interval_precision_met','released']
                diffs={}
                common=dict(meta,comparator=comparator,n_pairs=len(a),release_tolerance=float(meta['tolerance']),
                    matched_actual_cost=bool(np.array_equal(a.new_n.to_numpy(),b.new_n.to_numpy())))
                for metric in metrics:
                    av=a[metric].to_numpy(float);bv=b[metric].to_numpy(float)
                    finite=np.isfinite(av)&np.isfinite(bv)
                    base=dict(common,metric=metric,n_finite_pairs=int(finite.sum()))
                    if not finite.all():
                        rows.append(dict(base,targeted_minus_comparator=math.nan,lower=math.nan,upper=math.nan,
                            comparison_status='undefined_all_world_mean_nonfinite_present'))
                    else:diffs[metric]=av-bv
                if diffs:
                    matrix=np.column_stack(list(diffs.values()))
                    ci=bootstrap_differences(matrix,a.index.get_level_values('surface'),
                        (scope,tuple(values),comparator),B)
                    for j,(metric,diff) in enumerate(diffs.items()):
                        rows.append(dict(common,metric=metric,n_finite_pairs=len(diff),
                            targeted_minus_comparator=float(diff.mean()),lower=float(ci[0,j]),upper=float(ci[1,j]),
                            comparison_status='finite_world_paired_pointwise_ci'))
    return pd.DataFrame(rows)


def paired_attainment(cfg,records):
    rows=[];B=int(cfg.get('bootstrap_repetitions',2000))
    for scope,cols in [('cell',['surface','scenario','tolerance','criterion']),
                       ('pooled',['scenario','tolerance','criterion'])]:
        for values,g in records.groupby(cols,sort=True):
            meta=dict(zip(cols,values),scope=scope);meta.setdefault('surface','ALL')
            a=g[g.method=='r2_targeted'].set_index(WORLD).sort_index()
            for comparator in cfg['methods']:
                if comparator=='r2_targeted':continue
                b=g[g.method==comparator].set_index(WORLD).reindex(a.index)
                metrics=['attained','spent_until_hit_or_horizon','bad_attainment']
                matrix=a[metrics].to_numpy(float)-b[metrics].to_numpy(float)
                ci=bootstrap_differences(matrix,a.index.get_level_values('surface'),
                    ('attainment',scope,tuple(values),comparator),B)
                for j,metric in enumerate(metrics):
                    rows.append(dict(meta,release_tolerance=float(meta['tolerance']),precision_target=float(meta['tolerance']),
                        comparator=comparator,metric=metric,n_pairs=len(a),
                        targeted_minus_comparator=float(matrix[:,j].mean()),lower=float(ci[0,j]),upper=float(ci[1,j])))
    return pd.DataFrame(rows)


def plot_style():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
        'font.size':12,'axes.titlesize':13,'axes.labelsize':12,'axes.linewidth':1.4,
        'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,
        'pdf.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'})
    return plt


def save_figure(fig,path):
    for extension in ['pdf','png']:
        fig.savefig(path.with_suffix('.'+extension),dpi=300,bbox_inches='tight',pad_inches=.12)


def make_figures(cfg,summary,attain,out):
    plt=plot_style(); figdir=out/'figures';figdir.mkdir()
    from matplotlib.lines import Line2D
    handles=[Line2D([0],[0],color=COLORS[m],marker=MARKERS[m],lw=2,label=LABELS[m],
        linestyle='--' if m=='rinf_targeted' else '-') for m in cfg['methods']]
    for delta in cfg['tolerances']:
        tag=str(delta).replace('.','p')
        sel=summary[(summary.scope=='cell')&(summary['mode']=='prefix')&(summary.tolerance==delta)]
        fig,axes=plt.subplots(len(cfg['surfaces']),len(cfg['scenarios']),figsize=(15.5,10.8),squeeze=False)
        for i,surface in enumerate(cfg['surfaces']):
            for j,scenario in enumerate(cfg['scenarios']):
                ax=axes[i,j];cell=sel[(sel.surface==surface)&(sel.scenario==scenario)]
                for method in cfg['methods']:
                    g=cell[cell.method==method].sort_values('budget')
                    if method=='r2_static':g=g[g.budget==0]
                    x=g.mean_actual_cost.to_numpy(float);y=g.mean_halfwidth.to_numpy(float)
                    finite=np.isfinite(y)
                    ax.plot(x[finite],y[finite],color=COLORS[method],marker=MARKERS[method],lw=2,
                        linestyle='--' if method=='rinf_targeted' else '-',ms=5)
                    if method in ['r2_targeted','target_only']:
                        low=g.q10_halfwidth.to_numpy(float);high=g.q90_halfwidth.to_numpy(float)
                        ok=finite&np.isfinite(low)&np.isfinite(high)
                        ax.fill_between(x[ok],low[ok],high[ok],color=COLORS[method],alpha=.10,linewidth=0)
                ax.axhline(delta,color='#a0a0a0',ls=':',lw=1)
                ax.set_title(f'{surface.capitalize()} / {scenario}')
                ax.set_xticks([0,96,192,288]);ax.set_xlim(-9,297);ax.set_ylim(bottom=0)
                if i==len(cfg['surfaces'])-1:ax.set_xlabel('Actual new participants')
                if j==0:ax.set_ylabel('Mean returned half-width')
                ax.text(.02,.97,'Direct target at n=0: unbounded',transform=ax.transAxes,va='top',fontsize=8,color='#555555')
        fig.suptitle(f'Cost and interval precision | release tolerance = {delta:g}',fontsize=17,y=.998)
        fig.legend(handles=handles,loc='lower center',ncol=3,bbox_to_anchor=(.5,-.015),fontsize=11)
        fig.text(.5,.035,'Full acquisition prefixes; bands: 10th–90th world percentiles (targeted R2 and direct target).\nStatic archive is a zero-cost point. Returned half-width is not always the original certificate radius.',ha='center',fontsize=9)
        fig.tight_layout(rect=[0,.095,1,.96],pad=1.5)
        save_figure(fig,figdir/f'cost_precision_delta_{tag}');plt.close(fig)

        fig,axes=plt.subplots(len(cfg['surfaces']),len(cfg['scenarios']),figsize=(15.5,10.8),squeeze=False)
        for i,surface in enumerate(cfg['surfaces']):
            for j,scenario in enumerate(cfg['scenarios']):
                ax=axes[i,j];cell=sel[(sel.surface==surface)&(sel.scenario==scenario)]
                for k,method in enumerate(cfg['methods']):
                    g=cell[cell.method==method].sort_values('budget')
                    x=g.available_budget_n.to_numpy(float)+(k-2.5)*2.1
                    y=g.path_covered.to_numpy(float)
                    ax.errorbar(x,y,yerr=[y-g.path_covered_lower.to_numpy(float),g.path_covered_upper.to_numpy(float)-y],
                        color=COLORS[method],marker=MARKERS[method],lw=1.2,ms=4,capsize=2,
                        linestyle='--' if method=='rinf_targeted' else '-')
                ax.axhline(1-cfg['eta']-cfg['zeta'],color='#555555',ls=':',lw=1)
                ax.set_title(f'{surface.capitalize()} / {scenario}')
                ymin=max(0.,min(.84,float(cell.path_covered_lower.min())-.02))
                ax.set_ylim(ymin,1.01);ax.set_xlim(-12,300);ax.set_xticks([0,96,192,288])
                if i==len(cfg['surfaces'])-1:ax.set_xlabel('Available acquisition budget')
                if j==0:ax.set_ylabel('Path coverage through budget')
        fig.suptitle(f'Reliability of complete prefixes | release tolerance = {delta:g}',fontsize=17,y=.998)
        fig.legend(handles=handles,loc='lower center',ncol=3,bbox_to_anchor=(.5,-.015),fontsize=11)
        fig.text(.5,.045,'Points: empirical path coverage; bars: pointwise Wilson 95% intervals. Dotted line: nominal lower bound.\nHorizontal offsets separate methods; they do not represent different budgets.',ha='center',fontsize=9)
        fig.tight_layout(rect=[0,.095,1,.96],pad=1.5)
        save_figure(fig,figdir/f'path_coverage_delta_{tag}');plt.close(fig)

        for criterion in ['returned_interval','certificate']:
            a=attain[(attain.scope=='cell')&(attain.tolerance==delta)&(attain.criterion==criterion)]
            fig,axes=plt.subplots(len(cfg['surfaces']),len(cfg['scenarios']),figsize=(15.5,10.8),squeeze=False)
            for i,surface in enumerate(cfg['surfaces']):
                for j,scenario in enumerate(cfg['scenarios']):
                    ax=axes[i,j];cell=a[(a.surface==surface)&(a.scenario==scenario)]
                    for method in cfg['methods']:
                        g=cell[cell.method==method].sort_values('budget')
                        ax.plot(g.available_budget_n,g.attainment_rate,color=COLORS[method],marker=MARKERS[method],lw=2,ms=5,
                            linestyle='--' if method=='rinf_targeted' else '-')
                    ax.set_title(f'{surface.capitalize()} / {scenario}')
                    ax.set_ylim(-.02,1.03);ax.set_xlim(-9,297);ax.set_xticks([0,96,192,288])
                    if i==len(cfg['surfaces'])-1:ax.set_xlabel('Available new-participant budget')
                    if j==0:ax.set_ylabel('Fraction attaining precision')
            rule='returned interval half-width' if criterion=='returned_interval' else 'original certificate radius'
            fig.suptitle(f'First attainment: {rule} ≤ {delta:g}',fontsize=17,y=.998)
            fig.legend(handles=handles,loc='lower center',ncol=3,bbox_to_anchor=(.5,-.015),fontsize=11)
            fig.text(.5,.045,f'Output release tolerance = precision target = {delta:g}. All worlds remain in the denominator.\nFirst-hit analysis of full prefixes; interval task is distinct from original point release.',ha='center',fontsize=9)
            fig.tight_layout(rect=[0,.095,1,.96],pad=1.5)
            save_figure(fig,figdir/f'attainment_{criterion}_delta_{tag}');plt.close(fig)


def markdown_table(df,columns):
    def fmt(x):
        if isinstance(x,(float,np.floating)):
            if np.isnan(x):return 'undefined'
            if np.isposinf(x):return 'infinity'
            return f'{x:.4f}'
        return str(x)
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    lines += ['| '+' | '.join(fmt(x) for x in row)+' |' for row in df[columns].itertuples(index=False,name=None)]
    return '\n'.join(lines)


def write_report(cfg,summary,attain,paired,out):
    final=summary[(summary['mode']=='prefix')&(summary.scope=='cell')&(summary.budget==cfg['max_bridges'])]
    pooled=summary[(summary['mode']=='prefix')&(summary.scope=='pooled')&(summary.budget==cfg['max_bridges'])]
    lines=['# 成本与精度共同评价：新独立模拟结果','',
        f"模拟种子 `{cfg['seed']}`；{len(cfg['surfaces'])*len(cfg['scenarios'])*cfg['repetitions_per_cell']} 个独立世界；每单元 {cfg['repetitions_per_cell']} 世界。分析重采样种子 `{ANALYSIS_SEED}`。",
        '', '本报告比较完整采集前缀；原首次发布停止策略单独保存在 summary.csv 的 mode=stopped。每个世界的方法、阈值和预算重复行不算独立样本。',
        '', '## 阅读规则', '',
        '- 成本是实际新增参与者，不含历史档案、校准、审计和部署成本。静态档案一直是零成本参照。',
        '- 精度为实际返回区间半宽，包含拒绝后的外区间；它不一定是原加权点估计的误差半径。',
        '- release_tolerance 决定返回发布区间还是拒绝外区间；precision_target 决定首次达标任务。本轮两者数值相同，但属于不同概念；两个阈值对应两种输出规则。',
        '- 窄区间必须与覆盖一起解读。无界半宽保留 infinity；不一致区间不记为零宽，相关总体均值记 undefined。finite 条件统计仅作明确标注的辅助项。',
        '- certificate 达标沿用原点发布标准；returned_interval 达标按有限非空区间半宽，是另一项预声明任务。区间中点误差只作为该任务诊断，不能改写为原估计器表现。',
        '- 达标成本为首次命中；未达标者保留且标为右删失。平均实际支出包括失败者；mean_hit_cost_given_attained 仅为条件诊断，不可单独比较成本。',
        '- 方法差异使用世界配对、曲面内分层 bootstrap 的点态 95% 区间，未作全家族多重校正；避免据多个有利区间声称普遍优越。',
        '', '## 全场景最终前缀精度与可靠性', '',
        markdown_table(pooled,['scenario','method','tolerance','mean_actual_cost','mean_halfwidth','path_covered','path_covered_lower','released']),
        '', '## 分曲面结果：不由合并平均掩盖差异', '',
        markdown_table(final[final.method.isin(['r2_targeted','rinf_targeted','target_only'])],
            ['surface','scenario','method','tolerance','mean_actual_cost','mean_halfwidth','path_covered']),
        '', '## 达到指定精度的概率与实际支出', '',
        markdown_table(attain[(attain.scope=='pooled')&(attain.budget==cfg['max_bridges'])],
            ['scenario','method','tolerance','criterion','attainment_rate','mean_spent_until_hit_or_budget','n_not_attained']),
        '', '## 定向 R2 的配对精度差异', '',
        '下表差值为定向 R2 减去对照；负半宽差表示返回区间更窄。比较静态方法时实际成本不同，不属于等成本优势。', '',
        markdown_table(paired[(paired.scope=='pooled')&(paired.metric=='output_halfwidth')&(paired.budget==cfg['max_bridges'])],
            ['scenario','tolerance','comparator','matched_actual_cost','targeted_minus_comparator','lower','upper']),
        '', '## 能回答和不能回答的审稿问题', '',
        '本轮为 nrhq 的替代方法比较（REV-07）增加在共同模拟条件下的成本、精度和可靠性证据；为拒绝输出及停止口径（REV-12）提供完整记录。应根据逐场景结果决定支持范围，不能仅因运行完成而认定审稿意见解决。',
        '', '本轮仍是设计驱动权重与一步半径桥接启发式。它没有验证结果自适应选择的实际收益，不能据此关闭 WGDN 的选择安全效用质疑；也没有补齐真实机制集合、真实应用或近邻新颖性。',
        '', '## 图表与机器记录', '',
        '- `summary.csv`：逐单元与等权汇总，prefix/stopped 分开，包含全分母状态与覆盖区间。',
        '- `attainment.csv` / `attainment_summary.csv`：每世界首次命中、未命中状态及成本。',
        '- `paired_comparisons.csv` / `paired_attainment.csv`：配对点态区间。',
        '- `figures/`：成本—半宽、路径覆盖、两种达标任务，均导出 PDF 与 PNG。',
        '- `analysis_validation.json` / `analysis_manifest.json`：分析校验、哈希、版本与口径。', '']
    (out/'report.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')


def analyze(cfg,input_dir,out):
    input_dir=Path(input_dir);out=Path(out)
    frames={mode:load_records(input_dir/f'{name}_records.csv')
        for mode,name in [('prefix','prefix'),('stopped','stopped')]}
    checks=validate_inputs(cfg,frames)
    summary=summaries(cfg,frames);save(summary,out/'summary.csv')
    records=attainment_records(cfg,frames['prefix']);save(records,out/'attainment.csv')
    attained=attainment_summary(cfg,records);save(attained,out/'attainment_summary.csv')
    paired=paired_comparisons(cfg,frames['prefix']);save(paired,out/'paired_comparisons.csv')
    paired_hit=paired_attainment(cfg,records);save(paired_hit,out/'paired_attainment.csv')
    checks.append({'name':'attainment all-world denominator preserved',
        'passed':bool(len(records)==len(frames['prefix'])/(cfg['max_bridges']+1)*2)})
    checks.append({'name':'nonattainment has missing success cost and observed spending',
        'passed':bool(records.loc[~records.attained,'first_hit_cost'].isna().all() and
            records.spent_until_hit_or_horizon.notna().all())})
    (out/'analysis_validation.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    if not all(x['passed'] for x in checks):raise AssertionError('Analysis checks failed')
    make_figures(cfg,summary,attained,out)
    write_report(cfg,summary,attained,paired,out)
    return {'summary_rows':len(summary),'attainment_world_rows':len(records),
            'paired_precision_rows':len(paired),'paired_attainment_rows':len(paired_hit),
            'checks':checks}
