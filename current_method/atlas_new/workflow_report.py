"""Audit stopped policies, report paired comparisons, plot only saved data."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import binom

from .experiments import wilson
from .workflow import Design, certificate, surface

KEYS = ['surface','scenario','replicate']
LABELS = {'r2_targeted':'Targeted R2', 'rinf_targeted':'Targeted R-infinity',
          'r2_random':'Random + R2', 'r2_nearest':'Nearest + R2',
          'r2_static':'Archive only R2', 'target_only':'Target experiment'}
COLORS = {'r2_targeted':'#0F4D92','rinf_targeted':'#9A4D8E','r2_random':'#B64342',
          'r2_nearest':'#42949E','r2_static':'#767676','target_only':'#272727'}


def save(frame, path):
    frame.to_csv(path,index=False,float_format='%.12g')


def validate(cfg, out):
    df=pd.read_csv(out/'workflow_records.csv'); audits=pd.read_json(out/'world_audits.jsonl',lines=True)
    plans=pd.read_json(out/'plans.jsonl',lines=True)
    events=pd.read_csv(out/'acquisitions.csv')
    checks=[]
    def check(name,passed,detail=''):
        checks.append(dict(name=name,passed=bool(passed),detail=detail))
    nw=cfg['repetitions_per_cell']*len(cfg['surfaces'])*len(cfg['scenarios'])
    check('complete balanced factorial records',len(df)==nw*len(cfg['methods'])*len(cfg['tolerances'])*(cfg['max_bridges']+1))
    check('unique world policy tolerance budget',not df.duplicated(KEYS+['method','tolerance','budget']).any())
    check('one calibration audit per independent world',len(audits)==nw and not audits.duplicated(KEYS).any())
    check('declared cost is actual observed participants',(df.new_n==df.actual_bridges*cfg['participants_per_bridge']).all())
    check('no source or target budget overrun',(df.actual_bridges<=df.budget).all())
    check('optimizer makes no global optimality assertion',not plans.global_optimum_certified.any())
    check('no finite wrong-width or fabricated zero-width interval',
          ((df.interval_status=='inconsistent') | (df.width>=0)).all())
    check('no missing certificate or estimate',not df[['radius','estimate','truth','error']].isna().any().any())
    check('no missing causal score',not df[['covered','path_covered','bad_release','released']].isna().any().any())
    check('bad release uses unconditional event',
          np.array_equal(df.bad_release,df.released & (df.error>df.tolerance)))
    check('release uses prespecified tolerance only',np.array_equal(df.released,df.radius<=df.tolerance))
    check('target outcome hidden at budget zero',
          np.isinf(df[(df.method=='target_only')&(df.budget==0)].radius).all())
    check('initial bridge policies receive identical information',
          df[(df.method!='target_only')&(df.budget==0)].source_ids.eq('[0, 1, 2, 3]').all())
    maximum_radius_error=0.; monotone=True; numerical_feasible=True
    design_index={}
    for w in audits.itertuples(index=False):
        d=Design(np.array(w.proxies),np.full(10,w.radius),np.array(w.target_proxy),w.radius,
                 1/np.sqrt(np.r_[np.full(4,cfg['archive_participants']),np.full(6,cfg['participants_per_bridge'])]),
                 w.L,w.H,4,cfg['max_bridges'],cfg['eta'],cfg['zeta'])
        design_index[(w.surface,w.scenario,w.replicate)]=(d,w)
    for _,g in plans.groupby(KEYS+['method'],sort=False):
        g=g.sort_values('stage');monotone &= bool((np.diff(g.radius)<=1e-8).all())
        for p in g.itertuples(index=False):
            d,_=design_index[(p.surface,p.scenario,p.replicate)]
            a=np.asarray(p.weights)
            numerical_feasible &= bool(a.min()>=0 and abs(a.sum()-1)<1e-8)
            actual=certificate(d,p.ids,a,'rinf' if p.method=='rinf_targeted' else 'r2')
            maximum_radius_error=max(maximum_radius_error,abs(actual-p.radius))
    check('saved weights feasible and independently re-evaluated',numerical_feasible and maximum_radius_error<1e-7,str(maximum_radius_error))
    check('prospective certificate does not worsen when sources added',monotone)
    # Verify acquisition log against every prediction, including carried stops.
    acquisition_index={tuple(key):g.sort_values('stage') for key,g in events.groupby(KEYS+['method','tolerance'])}
    cost_ok=stop_ok=effects_ok=path_ok=True; max_prediction_error=0.
    for key,g in df.groupby(KEYS+['method','tolerance'],sort=False):
        g=g.sort_values('budget'); d,w=design_index[key[:3]]
        ev=acquisition_index.get(tuple(key),events.iloc[:0])
        cost_ok &= len(ev)==int(g.iloc[-1].actual_bridges)
        stop_seen=None;cover=True
        base={r['source_id']:r['effect'] for r in w.archive_observations}
        for row in g.itertuples(index=False):
            observed=ev[ev.stage<=row.budget]
            cost_ok &= len(observed)==row.actual_bridges
            cover=cover and (row.lower<=row.truth<=row.upper)
            path_ok &= bool(cover==row.path_covered)
            if stop_seen is not None:
                stop_ok &= (row.new_n==stop_seen.new_n and row.estimate==stop_seen.estimate
                            and row.radius==stop_seen.radius and row.selected==stop_seen.selected)
            if row.released and stop_seen is None:stop_seen=row
            if row.method=='target_only':
                predicted=observed.effect.mean() if len(observed) else 0.
            else:
                available=base|dict(zip(observed.source_id,observed.effect))
                ids=json.loads(row.source_ids);a=json.loads(row.weights)
                effects_ok &= all(i in available for i in ids)
                predicted=sum(t*available[i] for t,i in zip(a,ids))
            max_prediction_error=max(max_prediction_error,abs(predicted-row.estimate))
    check('cost and source availability match acquisition log',cost_ok and effects_ok)
    check('stopped policies do not acquire or update after release',stop_ok)
    check('predictions recomputed from actually collected outcomes',max_prediction_error<1e-8,str(max_prediction_error))
    check('path coverage is conjunction across actual outputs',path_ok)
    check('two randomized arms reconstruct each acquired effect',
          np.allclose(events.effect,events.treated_mean-events.control_mean,rtol=0,atol=1e-9))
    # Scientific validity tests are distinct from performance comparisons.
    statistical=[]
    for keys,g in df[df.budget==cfg['max_bridges']].groupby(['surface','scenario','method','tolerance']):
        failures=int((~g.path_covered).sum()); n=len(g)
        statistical.append(dict(zip(['surface','scenario','method','tolerance'],keys))|
            dict(test='path miscoverage',failures=failures,n=n,budget=cfg['eta']+cfg['zeta'],
                 p_value=float(binom.sf(failures-1,n,cfg['eta']+cfg['zeta']))))
    for keys,g in audits.groupby(['surface','scenario']):
        failures=int((~g.joint_set_covered).sum());n=len(g)
        statistical.append(dict(surface=keys[0],scenario=keys[1],method='all',tolerance=np.nan,
            test='joint set miscoverage',failures=failures,n=n,budget=cfg['eta'],
            p_value=float(binom.sf(failures-1,n,cfg['eta']))))
    stat=pd.DataFrame(statistical);stat['familywise_alpha']=.01/len(stat)
    stat['violation_detected']=stat.p_value<stat.familywise_alpha
    save(stat,out/'statistical_calibration_checks.csv')
    check('no calibrated path or set violation detected at familywise .01',not stat.violation_detected.any(),
          'Failure to reject is not a proof; nominal path guarantee follows from the protocol assumptions.')
    (out/'validation_checks.json').write_text(json.dumps(checks,indent=2,ensure_ascii=False),encoding='utf-8')
    return checks


def summarize(cfg,out):
    df=pd.read_csv(out/'workflow_records.csv'); summary=[]
    for keys,g in df.groupby(['surface','scenario','method','tolerance','budget'],sort=True):
        row=dict(zip(['surface','scenario','method','tolerance','budget'],keys));n=len(g)
        row.update(n=n,mean_new_n=g.new_n.mean(),mean_actual_bridges=g.actual_bridges.mean(),
                   n_released=int(g.released.sum()),released_mae=g[g.released].error.mean(),
                   released_bad_rate=g[g.released].bad_release.mean(),
                   mean_certificate_radius=g.radius.mean(),
                   mean_output_width=g.width.mean(),inconsistent_fraction=g.interval_status.eq('inconsistent').mean())
        for metric in ['released','bad_release','path_covered','covered','joint_set_covered']:
            row[metric]=g[metric].mean()
            row[metric+'_lower'],row[metric+'_upper']=wilson(int(g[metric].sum()),n)
        summary.append(row)
    save(pd.DataFrame(summary),out/'workflow_summary.csv')
    # World-paired, cell-stratified bootstrap. Do not treat methods or thresholds
    # as independent replications and do not resample individual acquisition rows.
    rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],700]))
    B=cfg['bootstrap_repetitions'];pooled=[]
    for keys,g in df.groupby(['scenario','method','tolerance','budget'],sort=True):
        row=dict(zip(['scenario','method','tolerance','budget'],keys));row['n_worlds']=len(g)
        strata=[s.sort_values('replicate') for _,s in g.groupby('surface')]
        metrics=['released','bad_release','path_covered','new_n']
        draws=np.zeros((B,len(metrics)))
        for stratum in strata:
            x=stratum[metrics].to_numpy(dtype=float);indices=rng.integers(len(x),size=(B,len(x)))
            draws+=x[indices].mean(axis=1)/len(strata)
        for i,metric in enumerate(metrics):
            row[metric]=g[metric].mean()
            row[metric+'_lower'],row[metric+'_upper']=np.quantile(draws[:,i],[.025,.975])
        row['released_mae']=g[g.released].error.mean()
        row['released_bad_rate']=g[g.released].bad_release.mean()
        row['mean_output_width']=g.width.mean()
        row['mean_refusal_width']=g[~g.released].width.mean()
        row['mean_certificate_radius']=g.radius.mean()
        row['n_released']=int(g.released.sum())
        pooled.append(row)
    save(pd.DataFrame(pooled),out/'pooled_summary.csv')
    differences=[]
    final=df[df.budget==cfg['max_bridges']]
    for scope,group_columns in [('cell',['surface','scenario','tolerance']),('pooled',['scenario','tolerance'])]:
        for keys,g in final.groupby(group_columns,sort=True):
            meta=dict(zip(group_columns,keys));meta.setdefault('surface','ALL')
            for comparator in cfg['methods']:
                if comparator=='r2_targeted':continue
                a=g[g.method=='r2_targeted'].set_index(KEYS).sort_index()
                b=g[g.method==comparator].set_index(KEYS).reindex(a.index)
                metrics=['released','new_n','bad_release'];diff=a[metrics].astype(float)-b[metrics].astype(float)
                boot=np.zeros((B,len(metrics)))
                strata=list(diff.groupby(level='surface'))
                for _,stratum in strata:
                    x=stratum.to_numpy();indices=rng.integers(len(x),size=(B,len(x)))
                    boot+=x[indices].mean(axis=1)/len(strata)
                for j,metric in enumerate(metrics):
                    lower,upper=np.quantile(boot[:,j],[.025,.975])
                    differences.append(dict(**meta,scope=scope,comparator=comparator,metric=metric,
                        targeted_minus_comparator=diff[metric].mean(),lower=lower,upper=upper,n_pairs=len(diff)))
    save(pd.DataFrame(differences),out/'paired_comparisons.csv')


def figures(cfg,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Helvetica','DejaVu Sans'],
        'font.size':12,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':1.4,
        'legend.frameon':False,'svg.fonttype':'none','pdf.fonttype':42,'savefig.dpi':300})
    folder=out/'figures';folder.mkdir(exist_ok=True)
    pooled=pd.read_csv(out/'pooled_summary.csv'); handles=[]
    shown=['r2_targeted','rinf_targeted','r2_random','target_only']
    styles=['-','--','-.',':']
    for method,style in zip(shown,styles):
        handles.append(Line2D([0],[0],color=COLORS[method],ls=style,marker='o',label=LABELS[method]))
    fig,axes=plt.subplots(2,3,figsize=(14,8.4),layout='constrained')
    for i,tolerance in enumerate(cfg['tolerances']):
        for j,scenario in enumerate(cfg['scenarios']):
            ax=axes[i,j]
            for method,style in zip(shown,styles):
                g=pooled[(pooled.scenario==scenario)&(pooled.method==method)&(pooled.tolerance==tolerance)].sort_values('budget')
                x=g.budget*cfg['participants_per_bridge']
                ax.plot(x,g.released,style,color=COLORS[method],marker='o',ms=4,lw=2)
                ax.fill_between(x,g.released_lower,g.released_upper,color=COLORS[method],alpha=.10)
            ax.set(title=f'{scenario.capitalize()} | tolerance {tolerance:g}',xlabel='Available new participants',
                   ylabel='Fraction released',ylim=(-.025,1.035),xticks=np.arange(4)*cfg['participants_per_bridge'])
    fig.legend(handles=handles,loc='outside lower center',ncol=4,fontsize=11)
    for ext in ['png','svg','pdf']:fig.savefig(folder/f'workflow_release_frontier.{ext}',bbox_inches='tight',facecolor='white')
    plt.close(fig)
    final=pooled[pooled.budget==cfg['max_bridges']]
    fig,axes=plt.subplots(2,3,figsize=(14,8.4),layout='constrained')
    for i,tolerance in enumerate(cfg['tolerances']):
        for j,scenario in enumerate(cfg['scenarios']):
            ax=axes[i,j]
            g=final[(final.scenario==scenario)&(final.tolerance==tolerance)].set_index('method').reindex(cfg['methods'])
            x=np.arange(len(g))
            ax.bar(x,g.new_n,color=[COLORS[m] for m in g.index],edgecolor='black',linewidth=.5)
            ax.errorbar(x,g.new_n,yerr=[g.new_n-g.new_n_lower,g.new_n_upper-g.new_n],fmt='none',ecolor='black',capsize=3)
            for pos,r in enumerate(g.itertuples()):
                ax.text(pos,r.new_n+7,f'{100*r.released:.0f}%',ha='center',va='bottom',fontsize=10)
            ax.set(title=f'{scenario.capitalize()} | tolerance {tolerance:g}',ylabel='Actual additional participants',
                   ylim=(0,cfg['max_bridges']*cfg['participants_per_bridge']*1.19),
                   xticks=x,xticklabels=['R2\ntarget','Rinf\ntarget','R2\nrandom','R2\nnear','No\nbridge','Target\ntrial'])
    fig.suptitle('Cost at the maximum budget; labels show release rate (refusal is not a saving)',fontsize=13)
    for ext in ['png','svg','pdf']:fig.savefig(folder/f'workflow_cost_and_release.{ext}',bbox_inches='tight',facecolor='white')
    plt.close(fig)


def report(cfg,out):
    from .report import table
    pooled=pd.read_csv(out/'pooled_summary.csv');pairs=pd.read_csv(out/'paired_comparisons.csv')
    records=pd.read_csv(out/'workflow_records.csv')
    cells=pd.read_csv(out/'workflow_summary.csv');audit=pd.read_json(out/'world_audits.jsonl',lines=True)
    plans=pd.read_json(out/'plans.jsonl',lines=True)
    checks=json.loads((out/'validation_checks.json').read_text(encoding='utf-8'))
    final=pooled[pooled.budget==cfg['max_bridges']]
    lines=['# 完整流程实验结果', '',f"配置：{cfg['profile']}。共 {len(audit)} 个独立世界，3 个二维效应函数 × 3 类支持几何；每个世界 6 种策略、2 个预先固定容忍度配对比较。",
           '', '这次实际模拟了联合机制审计、历史随机试验、拒绝、采集桥接试验两臂观测、重新估计及首次发布后的停止。输出没有把未采集候选或目标真值输入规划器。',
           '', '## 1. 同一预算下，发布与成本必须一起读', '',
           '表中 released 是累计发布率；new_n 是实际额外受试者，最多 288 人；path_covered 是该方法截至该预算全部实际输出同时覆盖真值的比例。按三个函数等权汇总；各函数结果另存 workflow_summary.csv。', '']
    for tolerance in cfg['tolerances']:
        lines += [f'### 容忍度 {tolerance:g}', '',table(final[final.tolerance==tolerance],
            ['scenario','method','released','new_n','bad_release','path_covered','released_mae']), '']
    example=records[(records.surface=='linear')&(records.scenario=='bridgeable')&
                    (records.replicate==0)&(records.method=='r2_targeted')&(records.tolerance==cfg['tolerances'][0])]
    lines += ['## 2. 一个完整轨迹（固定选择 linear / bridgeable / replicate=0）','',
              '此例按索引固定展示，不按成功与否挑选；发布后的预算行仅结转既有结果，不继续收集数据。','',
              table(example,['budget','selected','estimate','radius','released','new_n','refusal_lower','refusal_upper','path_covered']), '',
              '## 3. 配对比较：不把不同方法当独立样本', '',
              '以下为 targeted R2 减去比较方法，最终预算 288 人；released 为正意味着更多发布，new_n 为负意味着实际采集更少。成本优势必须同时检查发布率；无桥接方法零成本并不意味着完成了任务。95% 区间来自按世界配对、按函数分层的 bootstrap，非多重比较调整后的确认性区间。','',
              table(pairs[(pairs.scope=='pooled')&(pairs.metric.isin(['released','new_n']))],
                    ['scenario','tolerance','comparator','metric','targeted_minus_comparator','lower','upper']), '']
    valid=cells[cells.budget==cfg['max_bridges']]
    lines += ['## 4. 覆盖与软件验收', '',
        f"- 联合机制集合覆盖：{audit.joint_set_covered.mean():.4f}，声明下界 .95（有限模拟存在波动）。",
        f"- 各独立单元×方法×阈值的完整路径经验覆盖最小值：{valid.path_covered.min():.4f}；声明下界 .90。",
        f"- 各单元无条件错误发布率最大值：{valid.bad_release.max():.4f}。",
        f"- 正确性及统计验收：{sum(c['passed'] for c in checks)}/{len(checks)} 通过。统计检验不拒绝并不证明前提成立；保证来自协议中的联合事件推导。",
        f"- 实际路径的 SLSQP 起点失败数：{int(plans.solver_failures.sum())}；所有结果均为可行上界，不是全局最优声明。所有候选求解器诊断另见 candidate_scores.csv。", '',
        'R∞ 在完整候选库上建立一次噪声事件；R2 为加权区间的 4 轮检查和拒绝外区间分配预算。target-only 无需机制校准，用相同总失败预算 .10 分配给 3 个累计试验。没有把每轮 90% 当成整条路径 90%。', '',
        '## 5. 怎样解释正面和负面结果', '',
        '- supported 测试旧档案能否避免无必要新增试验；bridgeable 测试新来源能否填补支持；unreachable 检验给定候选菜单的边界。',
        '- 若 targeted R2 的配对成本区间全小于零且发布率未下降，才有支持节约新增实验的证据；这不是所有方法/场景的统一优越性结论。',
        '- R∞ 更保守或发布更少不构成代码失败；它允许更广的选权方式，而本轮 R2 的策略严格按设计规划。',
        '- 若直接重做目标更有效，应据此建议直接实验，不能隐藏该基线。',
        '- 已覆盖的宽区间、无限区间及拒绝都不能单独作为有效性的胜利；图表并列展示发布与成本。', '',
        '## 6. 这轮完成了什么、没有完成什么', '',
        '完成了可重跑的二维完整合成流程和真实生成的新随机实验观测；没有执行 Many Labs 等真实数据上的机制集合校准。校准标签、解析 L/H、已知 Gaussian 噪声、候选实验菜单和统一受试者成本是明确的模拟前提。未包含机制审计的共同前置成本，也未比较不同试验的部署成本。', '',
        '半径使用球集合的 sup G 外上界，并与逐源 Lipschitz 因果误差界取较小值。这是同一机制覆盖事件上的有效收紧；后者不必上界 G，不称为论文 B_U 的精确求解。方法名 R2/R∞ 指其噪声控制形式。桥接按下一轮证书半径作逐步数值选择，不宣称 PI sharpness、桥接全局最优或次模保证。有限预算联合界也不是无限时域或任意 outcome-adaptive 政策保证。', '',
        '数据入口：workflow_records.csv（含停止后的预算结转）、acquisitions.csv（真正采集的两臂摘要）、plans.jsonl（无结果规划）、world_audits.jsonl（评分后公开真值与校准信息）、paired_comparisons.csv、statistical_calibration_checks.csv。', '',
        '![发布前沿](figures/workflow_release_frontier.png)', '',
        '![成本与发布](figures/workflow_cost_and_release.png)']
    (out/'完整流程实验结果.md').write_text('\n'.join(lines),encoding='utf-8')
