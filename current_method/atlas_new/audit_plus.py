"""Independent robustness audits for the selection-safe certificate.

These experiments are intentionally separate from the main suite. Every invalid
procedure is retained as an explicitly labelled negative control.
"""
from itertools import product
import json
import time
import numpy as np
import pandas as pd
from scipy.stats import t, norm
from .core import calibrated_quantile, optimize_radius, box_vertices, radius
from .experiments import save, wilson


def _record_coverage(rows, method, errors, bounds, **meta):
    errors=np.asarray(errors);bounds=np.asarray(bounds)
    hit=errors<=bounds
    lo,hi=wilson(int(hit.sum()),len(hit))
    rows.append(dict(method=method,n=len(hit),coverage=float(hit.mean()),mc_lower=lo,mc_upper=hi,
                     mean_radius=float(bounds.mean()),mae=float(errors.mean()),**meta))


def correlated_noise(cfg,out):
    """Correlation audit: coordinate-union is safe after selection; R2 needs measurability."""
    rng=np.random.default_rng(cfg['seed_correlated']);n=cfg['correlated_draws'];rows=[]
    k=8;sd=np.linspace(.06,.14,k);true=np.zeros(k)
    for rho in [0.,.3,.7]:
        sigma=np.outer(sd,sd)*(rho-np.eye(k)*rho)+np.diag(sd**2)
        errors=rng.multivariate_normal(true,sigma,size=n)
        for rule in ['fixed_equal','adaptive_max_abs','adaptive_softmax']:
            if rule=='fixed_equal': weights=np.full((n,k),1/k)
            elif rule=='adaptive_max_abs':
                weights=np.eye(k)[np.argmax(abs(errors),axis=1)]
            else:
                z=np.exp(abs(errors)/.04);weights=z/z.sum(axis=1,keepdims=True)
            estimate=np.sum(weights*errors,axis=1)
            # R_infty: coordinate sub-Gaussian union control; valid even for adaptive weights.
            rinf=np.sqrt(2*np.log(2*k/.05))*np.sum(weights*sd,axis=1)
            # R2 diagonal: only valid for fixed/design-measurable weights.
            r2diag=np.sqrt(2*np.log(2/.05))*np.sqrt(np.sum(weights**2*sd**2,axis=1))
            r2cov=np.sqrt(2*np.log(2/.05))*np.sqrt(np.einsum('ni,ij,nj->n',weights,sigma,weights))
            _record_coverage(rows,'Rinf_coordinate_union',abs(estimate),rinf,rho=rho,rule=rule,valid=True)
            # The diagonal formula additionally requires independent source
            # noise.  Fixed weights alone do not make it valid when rho > 0.
            _record_coverage(rows,'R2_diagonal',abs(estimate),r2diag,rho=rho,rule=rule,
                             valid=(rule=='fixed_equal' and rho == 0.))
            _record_coverage(rows,'R2_covariance',abs(estimate),r2cov,rho=rho,rule=rule,
                             valid=rule=='fixed_equal')
    return save(out,'plus_correlated_noise',rows)


def heavy_tails(cfg,out):
    """Gaussian certificate under valid Gaussian, t3, and contaminated errors."""
    rng=np.random.default_rng(cfg['seed_heavy_tail']);n=cfg['heavy_tail_draws'];rows=[];k=8
    sd=np.linspace(.06,.14,k)
    for distribution in ['gaussian','t3_unit_variance','contamination_1pct']:
        if distribution=='gaussian':e=rng.normal(size=(n,k))
        elif distribution=='t3_unit_variance':e=rng.standard_t(3,size=(n,k))/np.sqrt(3)
        else:
            e=rng.normal(size=(n,k));mask=rng.random((n,k))<.01;e[mask]=rng.normal(0,8,size=mask.sum())
        e=e*sd
        # Adaptive selection is deliberately made after seeing all source summaries.
        weights=np.eye(k)[np.argmax(abs(e),axis=1)]
        estimate=(weights*e).sum(axis=1)
        rinf=np.sqrt(2*np.log(2*k/.05))*np.sum(weights*sd,axis=1)
        _record_coverage(rows,'adaptive_Rinf_Gaussian_bound',abs(estimate),rinf,
                         distribution=distribution,assumption_valid=distribution=='gaussian')
        # Robust empirical calibrator is a diagnostic, not a finite-sample theorem.
        scores=np.max(abs(e[:n//2])/sd,axis=1);q=calibrated_quantile(scores,.05)
        empirical=np.full(n-n//2,q*sd.max())
        _record_coverage(rows,'historical_residual_calibration',abs(estimate[n//2:]),empirical,
                         distribution=distribution,assumption_valid=False,calibration_n=n//2)
    return save(out,'plus_heavy_tails',rows)


def calibration_sensitivity(cfg,out):
    """Finite calibration-size audit for joint mechanism-set coverage."""
    rng=np.random.default_rng(cfg['seed_calibration_sensitivity']);rows=[];kvals=[4,16,64]
    # Include genuinely small calibration archives: with eta=.05, n_cal < 19
    # has no finite conformal rank and must be represented as an infinite radius.
    for ncal in [5,9,19,49,99,199,499,999]:
        for k in kvals:
            for rep in range(cfg['calibration_sensitivity_repetitions']):
                cal=np.max(abs(rng.normal(size=(ncal,k+1))),axis=1)
                q=calibrated_quantile(cal,cfg['eta'])
                test=np.max(abs(rng.normal(size=k+1)))
                rows.append(dict(n_cal=ncal,k=k,replicate=rep,quantile=q,
                                 covered=bool(test<=q),test_max=test,is_infinite=not np.isfinite(q)))
    df=save(out,'plus_calibration_sensitivity_records',rows);summ=[]
    for (ncal,k),g in df.groupby(['n_cal','k']):
        lo,hi=wilson(int(g.covered.sum()),len(g))
        # Use explicit column indexing: ``DataFrame.quantile`` is a method and
        # would otherwise shadow the recorded calibration-quantile column.
        qvals = g['quantile'].replace(np.inf, np.nan)
        summ.append(dict(n_cal=ncal,k=k,n=len(g),coverage=g.covered.mean(),mc_lower=lo,mc_upper=hi,
                         mean_quantile=qvals.mean(),infinite_fraction=g['is_infinite'].mean()))
    save(out,'plus_calibration_sensitivity_summary',summ)
    return df


def optimizer_audit(cfg,out):
    """Compare SLSQP multi-start to an independent random simplex search.

    The random search is a diagnostic, never a global-optimality certificate.
    """
    rng=np.random.default_rng(cfg['seed_optimizer']);rows=[];k=5
    for rep in range(cfg['optimizer_repetitions']):
        centers=np.sort(rng.uniform(-.9,.9,k+1));half=rng.uniform(.02,.15,k+1)
        boxes=np.column_stack((np.maximum(-1,centers-half),np.minimum(1,centers+half)))
        noise=rng.uniform(.04,.16,k);beta=rng.uniform(0,.04,k)
        alpha,value,diag=optimize_radius(boxes,1.2,.6,noise,beta,.05)
        candidates=rng.dirichlet(np.ones(k),cfg['optimizer_random_weights'])
        vertices=box_vertices(boxes)
        vals=np.array([radius(a,vertices,1.2,.6,noise,beta,.05) for a in candidates])
        best=float(vals.min());rank=float(np.mean(vals<=value+1e-9));gap=value-best
        rows.append(dict(replicate=rep,slsqp=value,random_best=best,gap=gap,
                         relative_gap=gap/max(best,1e-12),random_rank_fraction=rank,
                         solver_successes=diag['solver_successes'],solver_failures=diag['solver_failures'],
                         global_optimum_certified=diag['global_optimum_certified']))
    return save(out,'plus_optimizer_audit',rows)


def assumptions_and_boundaries(cfg,out):
    """Machine-readable negative controls for invalid scientific inputs."""
    rows=[]
    def add(name,expected,got,detail):rows.append(dict(case=name,expected=expected,observed=got,detail=detail))
    boxes=np.array([[-.5,-.2],[.1,.3],[.4,.7]])
    try: box_vertices(np.array([[.4,.2],[0,1]]));add('empty_mechanism_set','reject','accepted','')
    except ValueError:add('empty_mechanism_set','reject','reject','box lower > upper')
    try: radius(np.array([.5,.6]),box_vertices(boxes),1,.2,[.1,.1],[0,0],.05);add('off_simplex','reject','accepted','')
    except ValueError:add('off_simplex','reject','reject','weights do not sum to one')
    try: radius(np.array([.5,.5]),box_vertices(boxes),-1,.2,[.1,.1],[0,0],.05);add('negative_L','reject','accepted','')
    except ValueError:add('negative_L','reject','reject','negative smoothness bound')
    try: calibrated_quantile(np.arange(10),.05);add('small_calibration','infinite','finite','')
    except Exception as e:add('small_calibration','raise or infinite','raise',type(e).__name__)
    add('selection_R2','invalid_if_adaptive','explicitly_labelled','plus_correlated_noise.csv')
    add('t3_gaussian_certificate','invalid_assumption','explicitly_labelled','plus_heavy_tails.csv')
    return save(out,'plus_assumption_boundaries',rows)


def report_plus(out):
    corr=pd.read_csv(out/'plus_correlated_noise.csv');tails=pd.read_csv(out/'plus_heavy_tails.csv')
    cal=pd.read_csv(out/'plus_calibration_sensitivity_summary.csv');opt=pd.read_csv(out/'plus_optimizer_audit.csv')
    lines=['# 新版实验第二轮复核结果','',
           '本目录是对 `results/full` 的独立复核，不覆盖原结果。新增实验使用独立随机种子和独立生成流程。',
           '', '## 1. 相关源噪声', '']
    lines.append('| rho | rule | method | valid | coverage | mean radius |')
    lines.append('| --- | --- | --- | --- | ---: | ---: |')
    for _,r in corr.groupby(['rho','rule','method','valid'],sort=True).coverage.mean().reset_index().iterrows():
        g=corr[(corr.rho==r.rho)&(corr.rule==r.rule)&(corr.method==r.method)&(corr.valid==r.valid)]
        lines.append(f"| {r.rho:.1f} | {r.rule} | {r.method} | {bool(r.valid)} | {g.coverage.iloc[0]:.4f} | {g.mean_radius.iloc[0]:.4f} |")
    lines += ['', 'R∞ 使用 coordinate-union，因此即使权重看过结果也按 valid 记录；R2 只有 fixed_equal 是设计可测权重。adaptive 的 R2 行是故意的失效对照。',
              '', '## 2. 非高斯尾部', '', '| distribution | method | valid | coverage | mean radius |', '| --- | --- | --- | ---: | ---: |']
    for _,r in tails.iterrows():lines.append(f"| {r.distribution} | {r.method} | {bool(r.assumption_valid)} | {r.coverage:.4f} | {r.mean_radius:.4f} |")
    lines += ['', 't3 和 contamination 不满足 Gaussian sub-Gaussian 前提；覆盖下降是预期的假设边界，不能被“校准区间表现”掩盖。历史残差校准只是经验诊断。',
              '', '## 3. 联合集合校准样本量', '', '| n_cal | k | coverage | 95% MC lower | infinite fraction |', '| ---: | ---: | ---: | ---: | ---: |']
    for _,r in cal.iterrows():lines.append(f"| {int(r.n_cal)} | {int(r.k)} | {r.coverage:.4f} | {r.mc_lower:.4f} | {r.infinite_fraction:.4f} |")
    lines += ['', '小校准档案在 conformal rank 上可能得到无限半径；代码保留该状态，不把其替换成任意有限值。',
              '', '## 4. 权重优化稳定性', '', '| metric | value |', '| --- | ---: |',
              f"| SLSQP minus random-search best (mean) | {opt.gap.mean():.6f} |",
              f"| relative gap (median) | {opt.relative_gap.median():.6f} |",
              f"| SLSQP solver failures | {int(opt.solver_failures.sum())} |",
              f"| runs claiming global optimum | {int(opt.global_optimum_certified.sum())} |",
              '', '随机 simplex 搜索只能作为独立数值诊断；本结果不把多起点 SLSQP 说成全局最优。',
              '', '## 5. 复核结论', '',
              '- 相关性不会破坏 coordinate-union 的选择后证书；它会破坏不具备测量性条件的 R2 解释。',
              '- 非 Gaussian 尾部会暴露 Gaussian 证书的适用边界；新版论文必须把 sub-Gaussian 条件写成真正的前提。',
              '- 联合集合覆盖需要足够的独立校准档案；样本太小时应拒绝或返回无限集合。',
              '- 现有权重优化是可行数值实现，不是全局算法定理；这是数值方法边界，不应与统计覆盖混在一起。']
    (out/'第二轮复核结果.md').write_text('\n'.join(lines),encoding='utf-8')


def run(cfg,out):
    out.mkdir(parents=True,exist_ok=True)
    correlated_noise(cfg,out);heavy_tails(cfg,out);calibration_sensitivity(cfg,out);optimizer_audit(cfg,out);assumptions_and_boundaries(cfg,out)
    report_plus(out)
