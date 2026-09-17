"""Tables and figures are generated exclusively from saved results."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


def table(frame,columns=None):
    df=frame if columns is None else frame[columns]
    def cell(v):
        if pd.isna(v):return '—'
        if isinstance(v,(float,np.floating)):return f'{v:.4f}'
        return str(v)
    return '\n'.join(['| '+' | '.join(df.columns)+' |','| '+' | '.join(['---']*len(df.columns))+' |']+
                     ['| '+' | '.join(cell(v) for v in row)+' |' for row in df.itertuples(index=False,name=None)])


def figures(out):
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
        'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':1.1,
        'legend.frameon':False,'svg.fonttype':'none','savefig.dpi':300})
    folder=out/'figures';folder.mkdir(exist_ok=True)
    paths=[]
    def export(fig,name):
        fig.savefig(folder/f'{name}.png',bbox_inches='tight',facecolor='white')
        fig.savefig(folder/f'{name}.svg',bbox_inches='tight',facecolor='white')
        paths.append(str(folder/f'{name}.png'));plt.close(fig)
    hidden=pd.read_csv(out/'hidden_shift.csv');sel=pd.read_csv(out/'selection.csv')
    risk=pd.read_csv(out/'minimax.csv');bridge=pd.read_csv(out/'bridge_records.csv')
    fig,ax=plt.subplots(2,2,figsize=(12,9),layout='constrained')
    for method,label,color in [('semantic_gaussian','Semantic Gaussian','#B64342'),
                               ('paper_gaussian_set','Paper Gaussian + set','#3775BA'),
                               ('theorem_Rinf','Theorem R-infinity','#42949E')]:
        g=hidden[hidden.method.eq(method)];ax[0,0].plot(g['shift'],g.coverage,label=label,color=color)
        ax[0,0].fill_between(g['shift'],g.mc_lower,g.mc_upper,color=color,alpha=.15)
    ax[0,0].axvline(.3,color='grey',ls=':');ax[0,0].axhline(.95,color='grey',ls='--',lw=.8)
    ax[0,0].set(title='A  Hidden-mechanism boundary',xlabel='Hidden shift',ylabel='Effect coverage',ylim=(0,1.03));ax[0,0].legend(fontsize=9)
    for method,label,color in [('pointwise_after_max','Pointwise after selection','#B64342'),
                               ('gaussian_bonferroni','Gaussian Bonferroni','#3775BA'),('theorem_Rinf_max','Theorem R-infinity','#42949E')]:
        g=sel[sel.method.eq(method)];ax[0,1].plot(g.k,g.coverage,'o-',label=label,color=color,ms=4)
    ax[0,1].set(xscale='log',title='B  Post-selection uncertainty',xlabel='Archive size K',ylabel='Coverage',ylim=(0,1.03));ax[0,1].legend(fontsize=9)
    mat=risk.pivot(index='sigma',columns='ambiguity',values='risk')
    mesh=ax[1,0].pcolormesh(mat.columns,mat.index,mat.values,norm=LogNorm(),shading='nearest',cmap='cividis')
    ax[1,0].plot([.01,1],[.01,1],'--',color='#B64342')
    ax[1,0].set(xscale='log',yscale='log',title='C  Canonical estimator risk',xlabel='Mechanism ambiguity Ld',ylabel='Sampling scale');fig.colorbar(mesh,ax=ax[1,0],label='Worst-case MAE')
    for method,color in [('greedy','#3775BA'),('random','#767676')]:
        a=np.sort(bridge.loc[bridge.method.eq(method),'information_ratio']);ax[1,1].plot(a,np.arange(1,len(a)+1)/len(a),label=method,color=color)
    ax[1,1].axvline(1-1/np.e,ls='--',color='#B64342');ax[1,1].set(title='D  Log-det bridge objective',xlabel='Information / exhaustive optimum',ylabel='Empirical CDF');ax[1,1].legend()
    export(fig,'01_theory_audits')
    cal=pd.read_csv(out/'joint_calibration_summary.csv');front=pd.read_csv(out/'operational_frontier.csv')
    summ=pd.read_csv(out/'operational_summary.csv');pi=pd.read_csv(out/'pi_records.csv')
    fig,ax=plt.subplots(2,2,figsize=(12,9),layout='constrained')
    for method,color in [('joint_max','#3775BA'),('marginal_only_invalid','#B64342'),('gaussian_union','#42949E')]:
        g=cal[(cal.method==method)&(cal.test_scale==1)]
        ax[0,0].errorbar(g.k,g.joint_coverage,yerr=[g.joint_coverage-g.mc_lower,g.mc_upper-g.joint_coverage],label=method,color=color,marker='o')
    ax[0,0].axhline(.95,color='grey',ls='--');ax[0,0].set(title='A  Joint vs marginal calibration',xlabel='Number of source studies',ylabel='Joint mechanism coverage',ylim=(0,1.03));ax[0,0].legend(fontsize=9)
    for method,color in [('robust_Rinf','#3775BA'),('design_R2','#42949E'),('singleton_U','#B64342'),('no_curvature','#9A4D8E')]:
        g=front[(front.scenario=='nominal')&(front.method==method)]
        ax[0,1].plot(g.release_rate,g.released_mae,'o-',label=method,color=color,ms=4)
    ax[0,1].set(title='B  Prespecified tolerance frontier',xlabel='Release fraction',ylabel='MAE among releases');ax[0,1].legend(fontsize=9)
    g=summ[summ.method.eq('robust_Rinf')];ax[1,0].bar(np.arange(len(g)),g.coverage,color='#3775BA')
    ax[1,0].set_xticks(np.arange(len(g)),g.scenario,rotation=25,ha='right',fontsize=8)
    ax[1,0].axhline(.90,ls='--',color='#B64342',label='1 - eta - zeta (valid scenarios)')
    ax[1,0].set(title='C  Valid assumptions and stress cases',ylabel='Effect coverage',ylim=(0,1.03));ax[1,0].legend(fontsize=8)
    g=pi[pi['mode'].eq('noisy_sources')];ax[1,1].scatter(g.best_singleton_width,g.width,s=12,alpha=.5,color='#3775BA')
    lim=max(g.best_singleton_width.max(),g.width.max());ax[1,1].plot([0,lim],[0,lim],'--',color='grey')
    ax[1,1].set(title='D  Sharp finite-metric LP',xlabel='Best singleton interval width',ylabel='Joint LP target width')
    export(fig,'02_operational_extensions')
    fig,ax=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    g=bridge[bridge.method.eq('greedy')];sc=ax[0].scatter(g.information_ratio,g.target_radius_ratio,c=np.log10(g.condition),cmap='cividis',s=25,alpha=.7)
    fig.colorbar(sc,ax=ax[0],label='log10 posterior condition number',shrink=.85)
    ax[0].set(title='Information and target accuracy differ',xlabel='Greedy information / optimum',ylabel='Greedy target radius / target optimum')
    anis=pd.read_csv(out/'bridge_anisotropy.csv');ax[1].bar(['Log-det choice','Target-aware choice'],anis.target_radius,color=['#3775BA','#42949E'])
    ax[1].set(title='Anisotropic boundary example',ylabel='Target posterior radius')
    export(fig,'03_bridge_target_gap')
    if (out/'manylabs_holdouts.csv').exists():
        hold=pd.read_csv(out/'manylabs_holdouts.csv');fr=pd.read_csv(out/'manylabs_frontier.csv')
        fig,ax=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
        g=hold[hold.method.eq('random')];released=g.radius<=.15
        ax[0].scatter(g.loc[~released,'target_reference'],g.loc[~released,'estimate'],color='#B64342',s=25,label='Refused at half-width 0.15')
        ax[0].scatter(g.loc[released,'target_reference'],g.loc[released,'estimate'],color='#3775BA',s=30,label='Released at half-width 0.15')
        ax[0].legend(fontsize=9)
        ax[0].plot([-.2,.6],[-.2,.6],'--',color='grey');ax[0].set(title='Source-only random-effects predictions',xlabel='Held-out noisy reference (evaluation only)',ylabel='Frozen prediction')
        for method,color in [('fixed','#767676'),('random','#3775BA')]:
            g=fr[fr.method.eq(method)&(fr.n_released>0)];ax[1].plot(g.release_rate,g.reference_mae,label=method,color=color)
        ax[1].set(title='Outcome-blind threshold frontier',xlabel='Release fraction',ylabel='Noisy-reference MAE');ax[1].legend()
        export(fig,'04_manylabs_independent_sources')
    return paths


def validate_results(out):
    checks=[]
    def check(name,ok,detail=''):
        checks.append(dict(name=name,passed=bool(ok),detail=detail))
        if not ok: raise AssertionError(name+': '+detail)
    sel=pd.read_csv(out/'selection.csv');p=sel[sel.method.eq('pointwise_after_max')]
    check('exact pointwise coverage',np.allclose(p.analytic,.95**p.k))
    b=pd.read_csv(out/'bridge_records.csv');g=b[b.method.eq('greedy')]
    check('greedy approximation',bool((g.information_ratio>=1-1/np.e-1e-8).all()))
    check('all posterior radius bounds',bool((b.target_radius<=b.target_radius_bound+1e-8).all()))
    pi=pd.read_csv(out/'pi_records.csv');e=pi[pi['mode'].eq('exact_sources')]
    check('LP equals noiseless closed form',bool((e.closed_form_error<1e-8).all()))
    check('LP no wider than singleton',bool((pi.width<=pi.best_singleton_width+1e-8).all()))
    c=pd.read_csv(out/'bridge_complementarity.csv');check('PI complementarity widths',np.allclose(c.width,[2,2,2,0]))
    op=pd.read_csv(out/'operational_records.csv');r=op[op.method.eq('robust_Rinf')];f=op[op.method.eq('design_R2')]
    check('R2 evaluated at same design-only weights',r.weights.tolist()==f.weights.tolist())
    check('R2 sharper at same weights',bool((f.radius.to_numpy()<=r.radius.to_numpy()+1e-8).all()))
    check('No false global optimization claims',not op.global_optimum_certified.dropna().any())
    if (out/'manylabs_leakage_tests.csv').exists():
        ml=pd.read_csv(out/'manylabs_leakage_tests.csv')
        check('57 independent source folds',len(ml)==57)
        check('target outcome perturbation invariance',bool((ml.maximum_prediction_change==0).all()))
        check('target source excluded',bool(ml.no_target_source_in_training.all()))
    (out/'validation_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    return checks


def write_report(cfg,out):
    op=pd.read_csv(out/'operational_summary.csv');cal=pd.read_csv(out/'joint_calibration_summary.csv')
    sel=pd.read_csv(out/'selection.csv');br=pd.read_csv(out/'bridge_records.csv');pi=pd.read_csv(out/'pi_records.csv')
    g=br[br.method.eq('greedy')];random=br[br.method.eq('random')]
    report=f'''# 新版实验结果与阅读指南

运行 profile：**{cfg['profile']}**。配置和源文件哈希见 run_manifest.json；本报告从本次保存的 CSV 自动生成。
这是一套独立实现，复现论文协议与扩展验证，不承诺原稿未公开实现的逐位数值复现。
所有假设外结果均保留；smoke profile 不能用于论文统计结论。

## 你先看这几件事

1. 论文原有四个理论演示已独立运行；本套件另加 joint-set calibration、完整 R∞ 发布流程、sharp LP 和桥接目标差异。
2. 用 **joint-max** 校准是因为需要所有源和目标机制同时被覆盖。每个点各有 95% 覆盖，不代表整个档案有 95% 覆盖。
3. R∞ 的优势是证书在任意选权后仍有效，不是保证点预测 MAE 最小。几何选权不用效应结果时，R2 可以更窄。
4. LP 的 sharpness 是有限已知位置、L-Lipschitz 函数类的结论；box 模型的外包络不冒称 sharp。
5. log-det 保证信息增益近似最优；目标半径还依赖信息方向和条件数。
6. Many Labs 是固定/随机效应的无泄漏真实来源基准，尚无可信真实 U_i，因此没有伪造“真实 ATLAS 有限样本保证”。

## 如何解释新增实验的发现

- **先查集合，再查区间。** proxy_shift 下集合可能严重失准，但效应区间仍靠保守性保持高覆盖。高效应覆盖本身不能证明 Assumption 3.2 成立。
- **低报常数会误导发布。** understated_LH 同时影响权重和区间，是假设失效例子；该实验不是从数据中估计出了正确 L/H。
- **主证书有保守成本。** 设计可测 R2 与 robust R∞ 使用相同点权重，MAE 必须相同；差异体现在宽度、发布率及允许的选权方式。
- **信息最优不等于目标最优。** 即使 log-det greedy 接近其穷举最优，目标半径仍可能明显大于 target-aware 选择。应同时展示两个指标。

## E2 选择后的覆盖（K=128）

{table(sel[sel.k.eq(128)],['method','temperature','coverage','analytic','mean_width'])}

pointwise_after_max 的解析值为 0.95^128；continuous_R2_invalid 仅为违反权重独立条件的消融。

## E4b 联合集合校准（同分布）

{table(cal[cal.test_scale.eq(1)],['k','method','n','joint_coverage','mc_lower','mc_upper','mean_radius'])}

历史审计档案提供 proxy 与机制真值的配对。真实应用能否获得这种校准信息仍是研究问题。

## E4 完整流程：robust R∞

{table(op[op.method.eq('robust_Rinf')],['scenario','n','mae','coverage','mean_width','joint_set_coverage','solver_failures'])}

nominal、extrapolation、high_noise、bounded_nuisance_bias 为前提内；proxy_shift、understated_LH 是前提外压力测试。
所有 coverage 是测试目标效应的经验覆盖。空发布集合的条件 MAE 为缺失值，不能填 0。
`operational_frontier.csv` 单独报告无条件错误发布概率；这与给定发布的条件错误概率不同。
SLSQP 多起点不是全局优化证明；失败次数是各次起点失败数，不是自动等于档案失败。

## E5 sharp PI

{table(pi.groupby('mode').agg(n=('covered','size'),coverage=('covered','mean'),mean_width=('width','mean'),best_singleton_width=('best_singleton_width','mean')).reset_index())}

每个 LP 的完整端点见证在 pi_witnesses.json。不兼容源约束和无锚档案分别为 infeasible、unbounded，见 pi_boundary_cases.json。

## E6 桥接

- {len(g)} 个独立设计，log-det greedy / exact 信息比的最小、中位、均值：{g.information_ratio.min():.4f}、{g.information_ratio.median():.4f}、{g.information_ratio.mean():.4f}。
- random 信息比均值：{random.information_ratio.mean():.4f}；random 子集嵌套在设计中，不能当作同等数量独立设计。
- greedy 的目标半径 / target-aware optimum 平均比：{g.target_radius_ratio.mean():.4f}，最大比：{g.target_radius_ratio.max():.4f}。
- 互补性见证宽度为 (2,2,2,0)。各向异性例子另列 bridge_anisotropy.csv。
- 所有预算 4 子集的最大条件数逐实例穷举记录；大条件数下 radius 上界可能很松，不能把通过公式检查说成高效控制目标精度。
'''
    if (out/'manylabs_summary.csv').exists():
        ml=pd.read_csv(out/'manylabs_summary.csv');diag=json.loads((out/'manylabs_diagnostics.json').read_text())
        report+='\n## E7 Many Labs 2\n\n'+table(ml)+'\n\n'
        report+=f'全源固定效应均值 {diag["fixed_mean"]:.4f}，随机效应均值 {diag["random_mean"]:.4f}，I²={100*diag["I2"]:.3f}%。57 次目标响应翻转测试均不改变该 fold 预测。\n\n'
        report+='纳入率针对带噪来源效应估计，不是真实因果效应覆盖。各 fold 共享训练源，未生成假设 fold 独立的误差条。固定 .15 阈值只用于与论文比较；完整阈值曲线均保留。\n'
    else: report+='\n## E7 Many Labs 2\n\n本次未运行；不能把其状态写为完成。\n'
    report+='''
## 建议如何入文

- 主文保留 01_theory_audits 的四个对应定理演示；其中 Gaussian 特例与 R∞ 曲线分别标注。
- 新增 02_operational_extensions，展示集合校准、发布率/风险、失效边界和 sharp LP；这是原文缺少的完整流程证据。
- 03_bridge_target_gap 放在桥接讨论或附录，防止用信息增益偷换目标效应精度。
- 04_manylabs_independent_sources 作为真实基准；不要给它加“已校准 ATLAS”的方法标签。
- 旧 NSW / Hillstrom / 旧表格继续放 legacy/stress-test，不需要复制到本目录当成新方法结果。

## 本次没有声称完成的研究

真实跨干预 U_i 校准、一般非线性集合模型的全局最优求解、自适应桥接的 time-uniform 保证、不同 effect-family 的 estimand harmonization。它们需要新的科学输入或理论，不能靠模拟和改图标题补齐。
'''
    (out/'结果解读.md').write_text(report,encoding='utf-8')
    return out/'结果解读.md'
