"""Independent audit and report for MAIN-THEOREM-WORKFLOW01; never samples data."""
import os
for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_name] = '1'
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
METHODS = ('target_radius', 'logdet', 'frozen_random', 'direct_target')
LABELS = dict(target_radius='Target-radius', logdet='Logdet',
              frozen_random='Fixed random', direct_target='Direct target')
COLORS = dict(target_radius='#0F4D92', logdet='#42949E',
              frozen_random='#B64342', direct_target='#767676')


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8', newline='\n')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(k, n):
    z = 1.959963984540054
    p = k / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return float(max(0, center-half)), float(min(1, center+half))


def audit(raw):
    """Recompute algebra from archived inputs without importing implementation."""
    manifest = read_json(raw/'run_manifest.json')
    assert manifest['status'] == 'complete'
    cfg = manifest['config']; profile = cfg['profiles'][manifest['profile']]
    source = raw/'source_snapshot'/cfg['archive_path']
    assert sha256(source) == cfg['archive_sha256']
    archive = read_json(source)
    used = read_json(raw/'archive_designs_used.json')
    assert used == [archive[i] for i in profile['design_indices']]
    for name, digest in manifest['artifact_sha256'].items():
        assert sha256(raw/name) == digest, name
    for name, digest in manifest['source_sha256'].items():
        assert sha256(raw/'source_snapshot'/name) == digest, name
    records = pd.read_csv(raw/'terminal_records.csv')
    assert len(records) == len(used)*profile['worlds_per_design']*4
    assert not records.duplicated(['design_id', 'replicate', 'method']).any()
    assert records.groupby(['design_id','method']).size().eq(profile['worlds_per_design']).all()
    assert set(records.method) == set(METHODS)
    differences = dict(W=0., q=0., weight=0., radius=0., selected_next_W=0., type_stat_weight=0., estimate=0., trace_estimate=0.)
    endpoints = []; expected_types=[]; trajectories = {}; nstates = 0; nchoices = 0
    for design in used:
        ident = design['replicate']; prior = np.asarray(design['prior'])
        target = np.asarray(design['target']); x = np.vstack([design['design'], target])
        var = np.append(np.asarray(design['sigma'])**2, cfg['direct_noise_sd']**2)
        assert x.shape == (13,6) and np.allclose(var, .25)
        pinv = np.linalg.inv(prior)
        plans = read_json(raw/f'design_{ident:03d}_plans.json')
        for method, plan in plans.items():
            path = plan['path']; nstates += len(path)
            c = np.asarray([s['counts'] for s in path])
            assert np.array_equal(c.sum(axis=1), np.arange(len(path)))
            V = np.linalg.inv(pinv + np.einsum('ni,ij,ik->njk', c/var, x, x))
            u = V @ target
            w = (u @ x.T) / var
            residual = (c*w)@x - target
            parameter = np.einsum('ni,ij,nj->n', residual, prior, residual)
            noise = np.sum(c*w*w*var, axis=1)
            W = parameter+noise; q = u@target
            saved_W = np.asarray([s['W'] for s in path])
            saved_w = np.asarray([s['weights'] for s in path])
            radius = np.sqrt(W/cfg['failure_probability'])
            for key, a, b in [('W',W,saved_W), ('q',W,q), ('weight',w,saved_w),
                              ('radius',radius,[s['radius'] for s in path])]:
                differences[key] = max(differences[key],float(np.max(np.abs(a-b))))
            assert plan['attained'] and radius[-1] <= cfg['scientific_halfwidth']+1e-12
            assert np.all(radius[:-1] > cfg['scientific_halfwidth'])
            assert np.all(np.diff(W) <= 1e-11)
            selected = np.array([s['selected'] for s in path[1:]],dtype=int)
            increments = np.diff(c,axis=0)
            assert np.array_equal(increments,np.eye(13,dtype=int)[selected])
            assert all(s['visit']==c[j-1,s['selected']] for j,s in enumerate(path[1:],1))
            if method == 'direct_target':
                assert np.all(selected==12)
            else:
                assert np.all(selected<12)
                vx = V[:-1] @ x[:12].T
                xv = np.einsum('ik,nki->ni',x[:12],vx)
                cov = u[:-1] @ x[:12].T
                gain = cov*cov/(var[:12]+xv)
                new_W = W[:-1,None]-gain
                actual = new_W[np.arange(len(selected)),selected]
                differences['selected_next_W'] = max(differences['selected_next_W'],float(np.max(np.abs(actual-W[1:]))))
                if method=='target_radius':
                    assert np.all(actual<=new_W.min(axis=1)+1e-11)
                elif method=='logdet':
                    objective=.5*np.log1p(xv/var[:12])
                    assert np.all(objective[np.arange(len(selected)),selected]>=objective.max(axis=1)-1e-11)
                else:
                    expected = np.asarray(plan['random_order'])[np.arange(len(selected))%12]
                    assert np.array_equal(selected,expected)
                nchoices += len(selected)
            terminal = records[(records.design_id==ident)&(records.method==method)]
            assert terminal.study_observations.eq(len(path)-1).all()
            assert np.allclose(terminal.width,2*radius[-1],atol=1e-10,rtol=0)
            endpoints.append(dict(design_id=ident,method=method,cost=len(path)-1,
                                  width=float(2*radius[-1]),previous_width=float(2*radius[-2]),
                                  W=float(W[-1]),parameter_component=float(parameter[-1]),noise_component=float(noise[-1])))
            expected_types.extend(dict(design_id=ident,method=method,candidate_type=k,
                expected_count=int(c[-1,k]),expected_weight=float(w[-1,k])) for k in range(13) if c[-1,k])
            trajectories[(ident,method)]=np.asarray([s['width'] for s in path])
    sums = []
    expected_types=pd.DataFrame(expected_types)
    for chunk in pd.read_csv(raw/'final_type_stats.csv', chunksize=200000):
        chunk=chunk.merge(expected_types,on=['design_id','method','candidate_type'],how='left',validate='many_to_one')
        assert chunk.expected_count.notna().all() and chunk.observations.eq(chunk.expected_count).all()
        differences['type_stat_weight']=max(differences['type_stat_weight'],float(np.max(np.abs(chunk.weight_per_observation-chunk.expected_weight))))
        chunk['contribution']=chunk.sum_y*chunk.weight_per_observation
        sums.append(chunk.groupby(['design_id','replicate','method'])[['contribution','observations']].sum())
    reconstructed=pd.concat(sums).groupby(level=[0,1,2]).sum()
    joined=records.set_index(['design_id','replicate','method']).join(reconstructed)
    assert joined.observations.eq(joined.study_observations).all()
    differences['estimate']=float(np.max(np.abs(joined.estimate-joined.contribution)))
    assert records.covered.eq(records.truth.between(records.lower,records.upper)).all()
    assert records.bad_release_scientific.eq(records.attained & records.absolute_error.gt(cfg['scientific_halfwidth'])).all()
    assert records.interval_miss_on_release.eq(records.attained & ~records.covered).all()
    assert np.allclose(records.error,records.estimate-records.truth)
    trace=pd.read_csv(raw/'single_world_trace.csv')
    observations=pd.read_csv(raw/'single_world_observations.csv')
    assert trace.design_id.eq(cfg['trace_design_id']).all() and trace.replicate.eq(cfg['trace_world']).all()
    design=archive[cfg['trace_design_id']]; prior=np.array(design['prior']); t=np.array(design['target'])
    x=np.vstack([design['design'],t]); pi=np.linalg.inv(prior); var=np.append(np.array(design['sigma'])**2,.25)
    paired={}
    for method in METHODS:
        rows=trace[trace.method==method].sort_values('stage')
        obs=observations[observations.method==method].sort_values('stage')
        precision=pi.copy(); z=np.zeros(6)
        estimates=[0.]
        for row in obs.itertuples():
            kind=row.candidate_type; precision+=np.outer(x[kind],x[kind])/var[kind]
            z+=x[kind]*row.observed_y/var[kind]
            estimates.append(float(t@np.linalg.solve(precision,z)))
            key=(kind,row.visit)
            if key in paired: assert paired[key]==row.observed_y
            paired[key]=row.observed_y
        differences['trace_estimate']=max(differences['trace_estimate'],float(np.max(np.abs(rows.estimate-estimates))))
        assert rows.released.iloc[-1] and not rows.released.iloc[:-1].any()
    assert max(differences.values())<1e-9,differences
    evidence=dict(status='passed',profile=manifest['profile'],source_archive_sha256=sha256(source),
                  designs=len(used),worlds=len(used)*profile['worlds_per_design'],endpoints=len(records),
                  audited_path_states=nstates,audited_bridge_choices=nchoices,max_absolute_differences=differences,
                  notes=['No experiment implementation imported; algebra recomputed from archived inputs.',
                         'Sampling-law independence is established by source inspection, not inferred from empirical histograms.',
                         'Path checks do not confer simultaneous coverage; only the design-only stop is evaluated.'])
    return manifest,records,pd.DataFrame(endpoints),trajectories,trace,observations,evidence


def summarize(records, costs, trajectories):
    cost_rows=[]; outcomes=[]; per_design=[]
    for method in METHODS:
        group=costs[costs.method==method]
        cost_rows.append(dict(method=method,designs=len(group),min_cost=int(group.cost.min()),
            q10_cost=float(group.cost.quantile(.1)),median_cost=float(group.cost.median()),
            mean_cost=float(group.cost.mean()),q90_cost=float(group.cost.quantile(.9)),max_cost=int(group.cost.max()),
            min_width=float(group.width.min()),median_width=float(group.width.median()),max_width=float(group.width.max())))
        g=records[records.method==method]
        outcomes.append(dict(method=method,worlds=len(g),covered_count=int(g.covered.sum()),
            covered_rate=float(g.covered.mean()),interval_misses=int(g.interval_miss_on_release.sum()),
            scientific_errors=int(g.bad_release_scientific.sum()),mae=float(g.absolute_error.mean()),
            rmse=float(np.sqrt(g.squared_error.mean()))))
    for (ident,method),g in records.groupby(['design_id','method']):
        k=int(g.covered.sum()); lo,hi=wilson(k,len(g))
        per_design.append(dict(design_id=ident,method=method,n_worlds=len(g),covered_count=k,
            coverage=k/len(g),wilson95_low=lo,wilson95_high=hi,interval_misses=int((~g.covered).sum()),
            scientific_errors=int(g.bad_release_scientific.sum()),rmse=float(np.sqrt(g.squared_error.mean()))))
    pivot=costs.pivot(index='design_id',columns='method',values='cost')
    widths=costs.pivot(index='design_id',columns='method',values='width')
    paired=[]; detail=pivot.copy()
    for comparator in METHODS[1:]:
        ratio=pivot.target_radius/pivot[comparator]
        detail[f'target_over_{comparator}']=ratio
        paired.append(dict(comparator=comparator,designs=len(ratio),target_cheaper=int((ratio<1).sum()),
            equal_cost=int((ratio==1).sum()),target_costlier=int((ratio>1).sum()),
            median_ratio=float(ratio.median()),q10_ratio=float(ratio.quantile(.1)),q90_ratio=float(ratio.quantile(.9)),
            mean_ratio=float(ratio.mean()),ratio_of_total_cost=float(pivot.target_radius.sum()/pivot[comparator].sum()),
            cheaper_and_no_wider=int(((ratio<1)&(widths.target_radius<=widths[comparator])).sum())))
    fixed=[]
    for budget in (0,1,4,8,16,32,55,56):
        eligible=[i for i in pivot.index if all(len(trajectories[i,m])>budget for m in METHODS)]
        for method in METHODS:
            vals=np.array([trajectories[i,method][budget] for i in eligible])
            if len(vals): fixed.append(dict(study_observations=budget,method=method,common_designs=len(vals),
                median_width=float(np.median(vals)),q10_width=float(np.quantile(vals,.1)),q90_width=float(np.quantile(vals,.9))))
    return tuple(pd.DataFrame(x) for x in (cost_rows,outcomes,per_design,paired)),detail.reset_index(),pd.DataFrame(fixed)


def figures(out,costs,paired_details,per_design,trace):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,
        'svg.fonttype':'none','savefig.facecolor':'white','axes.facecolor':'white'})
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=300,bbox_inches='tight')
        fig.savefig(out/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(13.2,3.8),layout='constrained')
    for method in METHODS:
        v=np.sort(costs[costs.method==method].cost)
        axs[0].step(v,np.arange(1,len(v)+1)/len(v),where='post',label=LABELS[method],color=COLORS[method],lw=1.8)
    axs[0].set(xscale='log',xlabel='Study observations at first width ≤ 0.60',ylabel='Fraction of 200 archived designs',title='A  Cost to meet the same criterion',ylim=(0,1.02))
    axs[0].legend(frameon=False,fontsize=8,loc='lower right')
    for comparator in METHODS[1:]:
        v=np.sort(paired_details['target_over_'+comparator])
        axs[1].step(v,np.arange(1,len(v)+1)/len(v),where='post',label=LABELS[comparator],color=COLORS[comparator],lw=1.8)
    axs[1].axvline(1,color='#333333',lw=.8,ls='--')
    axs[1].set(xscale='log',xlabel='Target-radius cost / comparator cost',ylabel='Fraction of 200 archived designs',title='B  Paired costs across designs',ylim=(0,1.02))
    axs[1].legend(frameon=False,fontsize=8,loc='lower right')
    for j,method in enumerate(METHODS):
        values=per_design[per_design.method==method].coverage.to_numpy()
        # Horizontal offsets only separate equal observations; deterministic, no new sampling.
        offset=((np.arange(len(values))*37)%len(values)/len(values)-.5)*.35
        axs[2].scatter(j+offset,values,s=9,color=COLORS[method],alpha=.35,edgecolors='none')
    axs[2].axhline(.95,color='#333333',lw=.8,ls='--')
    axs[2].set(xticks=range(4),xticklabels=['Target','Logdet','Random','Direct'],ylabel='Empirical stopped coverage (200 worlds/design)',title='C  Reliability at the planned stop',ylim=(min(.945,float(per_design.coverage.min())-.005),1.004))
    save(fig,'main_cost_and_reliability')
    fig,axs=plt.subplots(1,3,figsize=(13.2,3.8),layout='constrained')
    for method in METHODS:
        g=trace[trace.method==method].sort_values('stage')
        axs[0].plot(g.stage,g.width,label=LABELS[method],color=COLORS[method],lw=1.7)
        axs[0].scatter([g.stage.iloc[-1]],[g.width.iloc[-1]],s=20,color=COLORS[method])
    axs[0].axhline(.60,color='#555555',ls='--',lw=.8)
    axs[0].set(yscale='log',xlabel='Actual study observations',ylabel='Certificate interval width',title='A  Design 0: each method stops at first crossing')
    axs[0].legend(frameon=False,fontsize=8)
    g=trace[trace.method=='target_radius'].sort_values('stage')
    axs[1].fill_between(g.stage,g.lower,g.upper,color=COLORS['target_radius'],alpha=.16,label='Pointwise certificate')
    axs[1].plot(g.stage,g.estimate,color=COLORS['target_radius'],lw=1.5,label='Estimate')
    axs[1].axhline(float(g.truth.iloc[0]),color='#222222',ls='--',lw=1,label='Truth (scoring only)')
    axs[1].set(xlabel='Actual study observations',ylabel='Target effect',title='B  Design 0 / world 0: observations update center')
    axs[1].legend(frameon=False,fontsize=8)
    axs[2].plot(g.stage,g.parameter_component,color='#42949E',label='Parameter component',lw=1.6)
    axs[2].plot(g.stage,g.noise_component,color='#B64342',label='Noise component',lw=1.6)
    axs[2].plot(g.stage,g.W,color='#0F4D92',label='Total W',lw=1.6)
    axs[2].axhline(.05*.3**2,color='#555555',ls='--',lw=.8)
    axs[2].set(yscale='log',xlabel='Actual study observations',ylabel='Second-moment error budget',title='C  The two terms of the certificate')
    axs[2].legend(frameon=False,fontsize=8)
    save(fig,'single_world_workflow')


def markdown_table(frame,formats=None):
    formats=formats or {}; columns=list(frame.columns)
    def cell(name,value):
        if name in formats:return formats[name](value)
        if isinstance(value,(float,np.floating)):return f'{value:.4g}'
        return str(value)
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join('---' for _ in columns)+' |']
    lines.extend('| '+' | '.join(cell(c,row[c]) for c in columns)+' |' for _,row in frame.iterrows())
    return '\n'.join(lines)


def report(out,manifest,records,costs,summaries,detail,fixed,trace,observations,audit_result):
    cost_summary,outcome_summary,per_design,paired=summaries
    cfg=manifest['config']; ndesign=costs.design_id.nunique(); nworld=manifest['counts']['worlds']
    example=costs[costs.design_id==0][['method','cost','width','previous_width']]
    g=trace[trace.method=='target_radius'].sort_values('stage')
    selected_stages=sorted(set([0,1,2,3,4,int(g.stage.max())-1,int(g.stage.max())]))
    worked=g[g.stage.isin(selected_stages)][['stage','selected','estimate','lower','upper','width','released']].copy()
    ys=observations[observations.method=='target_radius'].set_index('stage').observed_y
    worked.insert(2,'observed_y',worked.stage.map(ys))
    worked['selected']=worked.selected.map(lambda x:'—' if pd.isna(x) else f'b{int(x)}')
    worked=worked.fillna('—')
    target_direct=paired[paired.comparator=='direct_target'].iloc[0]
    target_logdet=paired[paired.comparator=='logdet'].iloc[0]
    target_random=paired[paired.comparator=='frozen_random'].iloc[0]
    fixed_table=fixed.pivot(index=['study_observations','common_designs'],columns='method',values='median_width').reset_index()
    text=rf'''# 原论文设计上的非高斯选桥主实验

本轮完成 {ndesign} 个原论文存档设计、每设计 {cfg['profiles'][manifest['profile']]['worlds_per_design']} 个世界，共 {nworld:,} 个世界。四方法全部在冻结的完整区间宽度 ≤ 0.60 处停止。成本单位为一次独立研究级效果观测，原 σ=0.5；不换算参与者人数或人民币。此报告的主数据是 `{manifest['profile']}`，不合并 smoke、旧压力测试或旧 5,400 世界。

## 主要结论

以达到同一精度门槛所需的观测次数比较，target-radius 在 {int(target_logdet.target_cheaper)}/{ndesign} 个设计中少于 logdet，在 {int(target_random.target_cheaper)}/{ndesign} 个设计中少于固定随机。相对直接目标观测，则有 {int(target_direct.target_cheaper)}/{ndesign} 个设计更省，{int(target_direct.equal_cost)}/{ndesign} 个相同，{int(target_direct.target_costlier)}/{ndesign} 个更贵；逐设计成本比的中位数为 {target_direct.median_ratio:.4g}。

这些结果检验了新定理在原存档设计中的执行和选桥效用。它们不能证明桥接普遍比直接目标实验便宜；原档案自身是随机合成设计，候选方向和幅度来自原生成器。这里没有为了本轮结果另设 0.1 或 2 的载荷，也没有筛除不利设计。费用比较是**相同宽度门槛**，不是每个最终区间恰好等宽；停止时越过门槛的幅度单独保留。

## 输入与概率含义

- 全部 200 组原始 p=6、12 候选的 prior、target、design、sigma 原样保留。源 SHA256：`{cfg['archive_sha256']}`。
- beta = Cholesky(prior) z，z 的坐标独立标准化 Student-t5；每次观测噪声也是真实独立的标准化 Student-t5 乘原 sigma。参数与噪声独立。没有 Gaussian 近似采样。
- 每个候选允许独立重复观测；这是新流程相对原论文“四个不同候选子集比较”的明确变化。原先验二阶矩、噪声和几何均假定已知，没有完成真实数据校准。
- 所有方法共享相同参数、同类同访问序号的配对观测；不同访问生成新噪声。前三个方法仅改变选桥规则；direct 采用同先验、同 σ 直接观测目标。
- 半径与路径仅依赖已知设计；观测只更新区间中心。保证是每个固定设计下对随机参数和噪声的联合边际覆盖，不是固定 beta 条件覆盖、给定数据后的后验覆盖或全路径同时覆盖。

## 实际计算的公式

设候选类型 k 被独立观测 c_k 次，方差 v_k，P 为原先验协方差，t 为目标方向：

$$V=(P^{{-1}}+\sum_k c_k x_kx_k^\top/v_k)^{{-1}},\qquad a_k=x_k^\top Vt/v_k.$$

$$\widehat\tau=\sum_k a_k\sum_{{j=1}}^{{c_k}}Y_{{kj}},\quad d=\sum_k c_ka_kx_k-t,\quad W=d^\top Pd+\sum_k c_ka_k^2v_k=t^\top Vt.$$

$$I=[\widehat\tau-R,\widehat\tau+R],\qquad R=\sqrt{{W/0.05}}.$$

下一个候选 b 的实际更新满足

$$W_{{next}}(b)=W-\frac{{(t^\top Vx_b)^2}}{{v_b+x_b^\top Vx_b}}.$$

target-radius 枚举 12 个候选的实际新 W 并选最小者；代码同时核对该闭式增益。logdet 最大化 $\frac12\log(1+x_b^\top Vx_b/v_b)$；随机法循环预先冻结的随机排列。选择最小下一步 W 是单步最优，不自动成为整个停止预算的全局最优。

只要 R>0.30，就不宣告达到预设精度；采集所选类型的一次新观测后，重新计算全部权重、中心和半径。首次 R≤0.30 即停止。停止点由设计预先确定，因此本报告在该点使用 α=0.05，不把所有沿途区间解释为同时覆盖。Lean 验证的概率界和矩阵单步更新与本程序的对象相对应；实际 a、W 与矩阵 q 的连接由这里的独立数值审计核对，不声称 Python 程序本身经 Lean 验证。

## 成本与精度

成本分布的分母为 **{ndesign} 个设计**，同一设计的 200 个随机世界不构成 200 份新的成本证据。

{markdown_table(cost_summary, {'mean_cost': lambda value: f'{value:.3f}'})}

配对成本比为 target-radius / 对照。`cheaper_and_no_wider` 进一步要求实际停止区间不比对照宽，可支持这些设计内的成本—宽度优势；它不代表全体设计的严格等宽比较。

{markdown_table(paired)}

![成本与可靠性](main_cost_and_reliability.png)

固定已采观测次数下的宽度中位数如下。每个预算只保留四种方法**都实际采集到该步**的相同设计子集，`common_designs` 明示分母；未假装已停止方法继续采样。预算越大，该子集可能变化，不能把各行差异直接当作同一总体的学习曲线。完整 q10/q90 见 `fixed_budget_widths.csv`。

{markdown_table(fixed_table)}

## 停止时的可靠性

{markdown_table(outcome_summary, {'covered_rate': lambda value: f'{value:.6f}'})}

上表是对全部原设计等量汇总的描述率；没有把方法配对或多个时点当成额外独立世界。`per_design_reliability.csv` 对每设计每方法的 200 个世界记录覆盖数及 95% Wilson 区间。这些区间未作跨设计多重比较校正，单个设计的经验覆盖低于 95% 本身不足以推翻或验证理论。Chebyshev 二阶矩界可较保守，高覆盖不等于成本效率高。

`interval_misses` 是真实目标落在实际返回区间之外；`scientific_errors` 是已达标时点估计误差超过 0.30。由于实际 R≤0.30，后一个事件包含于前一个事件，两者不能混为同一个指标。

## 固定单世界：设计 0、世界 0

该示例在运行前指定。真目标为 {g.truth.iloc[0]:.6g}，只用于事后评分，没有进入选桥、权重或停止决策。设计 0 四种方法的停止结果：

{markdown_table(example)}

下表逐行是“决定类型 → 获得该次观测 → 更新估计与区间 → 判断精度”。stage 0 尚无观测，中心为先验均值 0；每类尚未被观测时，其权重不贡献估计。b0–b11 为原存档候选的零起始编号。

{markdown_table(worked)}

完整每一步可查原始 `single_world_trace.csv` 和 `single_world_observations.csv`；`single_world_steps.csv` 是便于阅读的合并副本。图中区间带是各时点区间的展示，未宣称整条带同时覆盖。

![单世界流程](single_world_workflow.png)

## 独立核验与可追溯性

运行代码 Git：`{manifest['git_revision']}`。冻结协议：`revision/MAIN_THEOREM_WORKFLOW01.json`。原 full 运行耗时 {manifest['elapsed_seconds']:.1f} 秒，9 项实现测试及 {len(manifest['checks'])} 项运行检查全部通过。分析与绘图没有预先单独计时，因此不追记其耗时。

本报告分析器不导入实验实现，没有重新生成样本。它从源快照独立重算 {audit_result['audited_path_states']:,} 个路径状态的矩阵、实际权重、W 两项、半径和第一停止点；核对 {audit_result['audited_bridge_choices']:,} 次候选选择；从各类观测和重建全部 {len(records):,} 个端点估计，并从逐次观测重建固定示例。路径状态与候选次数是重复核对的数量，不能当作独立统计样本量。

最大绝对差：`{json.dumps(audit_result['max_absolute_differences'])}`。全部源文件与产物哈希已核对，详情见 `independent_audit.json`；原运行测试与检查见 raw 目录中的 `test_log.txt` 和 `run_manifest.json`。

## 全部审稿问题回顾

| 问题 | 本轮新增证据 | 仍未覆盖 |
| --- | --- | --- |
| REV-01 / nrhq：解释与首现定义 | 预先指定的逐次流程、公式和可复核观测 | 正文可读性仍需作者审阅 |
| REV-02：R∞ 的适应性用途 | 明确本轮是设计型选择与停止 | 未测试 outcome-adaptive 权重或 sample splitting |
| REV-03：数字归因 | 新数字明确归属此非高斯结构化分支 | 未自动更新摘要或全论文旧数字 |
| REV-04：真实机制与 L,H | 原存档与已知二阶矩来源可追溯 | 无真实机制集合/二阶矩校准 |
| REV-05：真实闭环 | 合成线性流程实际采样、更新、停止 | 无真实应用闭环 |
| REV-06：Many Labs 噪声 | 无新增证据 | 本轮不是 Many Labs |
| REV-07：基线与成本 | 同精度门槛、三种选桥与 direct、全部不利设计保留 | 费用按研究观测计；现实成本与任务差异未验证 |
| REV-08：新颖性与相关工作 | 无新增证据 | 仍需文献比较 |
| REV-09：simplex 估计类 | 明确使用结构化线性权重 | 不证明原 simplex 类普适最优 |
| REV-10 / KoBT.W4：Gaussian 与选桥定理 | 非高斯真实抽样；W 直接驱动下一步区间选择；独立公式核对 | 保留线性模型、已知二阶矩；单步最优不等于全预算最优 |
| REV-11：版本与命名 | 主分支、协议、代码、结果来源明确 | 全文命名与旧结果归属仍需系统整理 |
| REV-12：拒绝、停止与风险 | 首次精度停止、区间漏盖和科学错误分开，逐设计可靠性 | 不给真实校准或 outcome-driven 可选停止保证 |

本轮推进 REV-07、REV-10、REV-12 的限定证据，并帮助 REV-01；不因运行完成将任何问题自动改成 resolved。原一般 U/L/H 机制工作流与此已知矩结构化分支的范围必须在论文中明确区分。
'''
    (out/'RESULTS.md').write_text(text,encoding='utf-8', newline='\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); raw=args.raw.resolve();out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a fresh report directory.')
    result=audit(raw)
    manifest,records,costs,trajectories,trace,observations,evidence=result
    summaries,detail,fixed=summarize(records,costs,trajectories)
    out.mkdir(parents=True)
    names=['cost_summary','pooled_descriptive_reliability','per_design_reliability','paired_cost_summary']
    for name,frame in zip(names,summaries):frame.to_csv(out/(name+'.csv'),index=False,float_format='%.17g',lineterminator='\n')
    costs.to_csv(out/'design_costs.csv',index=False,float_format='%.17g',lineterminator='\n')
    detail.to_csv(out/'paired_design_costs.csv',index=False,float_format='%.17g',lineterminator='\n')
    fixed.to_csv(out/'fixed_budget_widths.csv',index=False,float_format='%.17g',lineterminator='\n')
    trace.merge(observations[['method','stage','observed_y']],on=['method','stage'],how='left').to_csv(out/'single_world_steps.csv',index=False,float_format='%.17g',lineterminator='\n')
    save_json(out/'independent_audit.json',evidence)
    figures(out,costs,detail,summaries[2],trace)
    report(out,manifest,records,costs,summaries,detail,fixed,trace,observations,evidence)
    save_json(out/'analysis_manifest.json',dict(raw_directory=str(raw),raw_manifest_sha256=sha256(raw/'run_manifest.json'),
        analysis_script_sha256=sha256(Path(__file__)),command=sys.argv,source_profile=manifest['profile'],
        sampling_performed=False,output_sha256={p.name:sha256(p) for p in out.iterdir() if p.is_file()}))
    print(json.dumps(dict(output=str(out),audit=evidence,cost_summary=summaries[0].to_dict('records'),
        paired_cost_summary=summaries[3].to_dict('records'),reliability=summaries[1].to_dict('records')),ensure_ascii=False))


if __name__=='__main__':main()
