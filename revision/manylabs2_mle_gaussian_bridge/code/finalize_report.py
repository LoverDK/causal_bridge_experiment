"""Assemble a report from frozen outputs; no fitting or Monte Carlo execution."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / 'manylabs2_conditional_execution'
PAPER = ROOT.parents[1] / 'reviewer1-sprint'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def readj(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def main():
    baseline = readj(ROOT / 'audit/baseline_snapshot.json')
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    def git(*args):
        return subprocess.run(['git', '-C', str(PAPER), *args], check=True, capture_output=True,
                              text=True, encoding='utf-8', env=env).stdout
    commands = {'head': ('rev-parse', 'HEAD'), 'branch': ('branch', '--show-current'),
                'status': ('status', '--porcelain=v1'), 'remotes': ('remote', '-v'),
                'unstaged': ('diff', '--binary'), 'staged': ('diff', '--cached', '--binary')}
    current = {key: git(*args) for key, args in commands.items()}
    prior_check = {name: sha(OLD / name) == value for name, value in baseline['prior_study_files'].items()}
    paper_check = {name: sha(name) == value for name, value in baseline['protected_paper_files'].items()}
    inputs_check = {name: sha(ROOT / 'data' / name) == value for name, value in baseline['source_inputs'].items()}
    freeze = readj(ROOT / 'audit/full_run_freeze.json')
    freeze_check = {name: sha(ROOT / name) == value for name, value in freeze['files'].items()}
    preservation = {'checked_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'paper_before': baseline['paper'], 'paper_after': current,
                    'paper_git_state_identical': current == baseline['paper'],
                    'protected_paper_hashes_match': paper_check,
                    'prior_study_hashes_match': prior_check, 'input_hashes_match': inputs_check,
                    'frozen_hashes_match': freeze_check,
                    'target_outcome_integrity_note': 'Prior files are hashed as opaque bytes for preservation only; no real target outcomes enter fitting, selection or simulation diagnostics.',
                    'network_mutations': 'None: no push, Overleaf write, GitHub write or manuscript/PDF edit in this task.'}
    assert current == baseline['paper'], 'Paper git state differs from pre-task baseline'
    assert all(prior_check.values()) and all(paper_check.values()) and all(inputs_check.values()) and all(freeze_check.values())
    (ROOT / 'audit/final_preservation_check.json').write_text(json.dumps(preservation, ensure_ascii=False, indent=2), encoding='utf-8')

    scale = pd.read_csv(ROOT / 'sample_size_scaling.csv')
    design = pd.read_csv(ROOT / 'bridge_design_comparison.csv')
    target = pd.read_csv(ROOT / 'target_level_metrics.csv')
    diag = pd.read_csv(ROOT / 'gaussian_approximation_results.csv')
    manifest = readj(ROOT / 'monte_carlo_manifest.json')
    exporter = readj(ROOT / 'target_metrics_export_manifest.json')
    audit = readj(ROOT / 'audit/numerical_audit_summary.json')
    export_audit = readj(ROOT / 'audit/target_export_audit_summary.json')
    assert audit['findings'] == []
    full = scale[(scale.scenario == 'barycenter') & (scale.scope == 'all_57_sites') &
                 (scale.estimator == 'extended_probability_mle')]
    rows = []
    for c in [1, 2, 5, 10, 20]:
        a = full[(full.dgp == 'A') & (full.scale == c)].set_index('variance')
        b = full[(full.dgp == 'B') & (full.scale == c)].set_index('variance')
        rows.append([c, int(a.loc['oracle', 'identified_site_count']),
                     f"{int(a.loc['oracle', 'adequate_site_count'])}/57",
                     f"{int(a.loc['plugin', 'adequate_site_count'])}/57",
                     f"{int(b.loc['oracle', 'adequate_site_count'])}/57",
                     f"{int(b.loc['plugin', 'adequate_site_count'])}/57",
                     f"{int(a.loc['oracle', 'finite_logistic_gate_site_count'])}/57",
                     f"{int(b.loc['oracle', 'finite_logistic_gate_site_count'])}/57"])
    scaling_table = table(['规模 c', '可定义 RD 的站点数', 'A oracle 通过', 'A plug-in 通过', 'B oracle 通过', 'B plug-in 通过', 'A 有限 MLE 存在率≥99%', 'B 有限 MLE 存在率≥99%'], rows)
    main_design = design[(design.scenario == 'barycenter') &
                         (design.estimator == 'extended_probability_mle') &
                         (design.noise_model == 'source_fitted_planning')]
    selected = main_design[(main_design.policy == 'logdet_greedy') & (main_design.budget == 4)].copy()
    rows = []
    for dgp in ['A', 'B']:
        for c in [1, 5, 20]:
            g = selected[(selected.dgp == dgp) & (selected.scale == c)].iloc[0]
            no = main_design[(main_design.dgp == dgp) & (main_design.scale == c) & (main_design.policy == 'source_only_no_bridge')].iloc[0]
            rows.append([dgp, c, f"{no.exact_bernoulli_mse:.7g}", f"{g.exact_bernoulli_mse:.7g}",
                         f"{g.mse:.7g}", f"{g.mae:.6f}", f"{100*g.coverage95_unconditional:.2f}%",
                         f"{100*g.gaussian_matched_coverage95:.2f}%", f"{100*g.relative_exact_mse_regret:.3f}%",
                         int(g.participant_cost)])
    bridge_table = table(['DGP', 'c', '不加桥的精确 MSE', '4 桥精确 MSE', '4 桥 MC MSE', '4 桥 MC MAE', 'Bernoulli 覆盖', '矩匹配 Gaussian 覆盖', '相对最优 MSE regret', '模拟新增人数'], rows)
    policies = ['logdet_greedy', 'logdet_exhaustive', 'target_variance_greedy', 'nearest_profile',
                'random_uniform_expectation', 'bernoulli_exhaustive_oracle', 'bernoulli_mc_exhaustive_oracle']
    row_data = main_design[(main_design.dgp == 'A') & (main_design.scale == 1) & (main_design.budget == 4)].set_index('policy')
    policy_table = table(['策略（A，c=1，B=4）', '精确目标 MSE', 'MC MSE ± MC SE', '平均新增人数', '信息增益', '精确 MSE regret'],
                         [[p, f"{row_data.loc[p, 'exact_bernoulli_mse']:.7g}",
                           f"{row_data.loc[p, 'mse']:.7g} ± {row_data.loc[p, 'mse_mc_se']:.2g}",
                           f"{row_data.loc[p, 'participant_cost']:.2f}",
                           f"{row_data.loc[p, 'information_gain']:.6f}",
                           f"{100*row_data.loc[p, 'relative_exact_mse_regret']:.3f}%"] for p in policies])
    targets = target[(target.scenario == 'barycenter') & (target.estimator == 'extended_probability_mle') &
                     (target.noise_model == 'source_fitted_planning') & (target.policy == 'logdet_greedy') & (target.budget == 4)]
    target_table = table(['DGP', 'c', '17 个目标各自覆盖率的最小值', '最大值'],
                         [[dgp, c, f"{100*g.coverage95_unconditional.min():.2f}%", f"{100*g.coverage95_unconditional.max():.2f}%"]
                          for (dgp, c), g in targets[targets.scale.isin([1, 20])].groupby(['dgp', 'scale'])])
    greedy = design[(design.scenario == 'barycenter') & (design.estimator == 'extended_probability_mle') & (design.policy == 'logdet_greedy')]
    kappa_lo, kappa_hi = greedy.posterior_kappa_max_all_subsets.min(), greedy.posterior_kappa_max_all_subsets.max()
    bound_lo, bound_hi = greedy.corollary_bound_to_actual_radius.min(), greedy.corollary_bound_to_actual_radius.max()
    a0 = main_design[(main_design.dgp == 'A') & (main_design.scale == 1) & (main_design.policy == 'source_only_no_bridge')].iloc[0]
    a4 = selected[(selected.dgp == 'A') & (selected.scale == 1)].iloc[0]
    reduction = 100*(1-a4.exact_bernoulli_mse/a0.exact_bernoulli_mse)
    sensitivity = design[(design.scenario.str.startswith('other_q')) & (design.estimator == 'extended_probability_mle') &
                         (design.noise_model == 'source_fitted_planning') & (design.policy == 'logdet_greedy') & (design.budget == 4)]
    summary = {'main_B4_summary_rows': rows, 'A_c1_B4_exact_MSE_reduction_percent': reduction,
               'main_kappa_range': [kappa_lo, kappa_hi], 'corollary_to_actual_radius_range': [bound_lo, bound_hi],
               'main_conditions': len(manifest['condition_runs']), 'diagnostic_rows': len(diag),
               'target_metric_rows': len(target), 'seed': manifest['seed'],
               'simulation_seconds': manifest['elapsed_seconds'], 'export_seconds': exporter['elapsed_seconds']}
    (ROOT / 'results/report_numbers.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

    report = f'''# Bernoulli 实验、MLE/Delta 高斯近似与选桥：最终报告

完成日期：2026-11-09。主种子：{manifest['seed']}。本报告只总结本轮冻结方案的模拟与审计；未修改论文、PDF、Overleaf 或 GitHub。

## 研究结论

**这条连接在限定的实验设计和 Common-CATE 模型下有实用价值，但不能把原始 Many Labs 2 的全部站点直接宣布为满足线性高斯定理。** 原始规模下，57 个站点中只有 29 个能定义本轮要求的饱和分层风险差估计；另外 28 个存在正权重类别的空单元。对于预先按设计支持条件选出的 12 个候选，扩展概率 MLE 的标量风险差在 oracle 方差标准化下已经通过预设边际及联合近似门槛。这个较窄的成功结论不能推广为 57 站点有限 logistic MLE 均成功。

在测试规模 {{1,2,5,10,20}} 中，全 57 站点的扩展风险差首次全部通过 oracle 方差门槛是 **5 倍规模**，使用每次模拟样本估计的 plug-in 方差则是 **10 倍规模**。如果坚持要求有限 logistic 参数 MLE 的存在率至少 99%，全站点到 20 倍仍不通过；固定 12 个候选的严格边际与联合门槛在 20 倍才通过。这些是所设 DGP、未来分层设计和有限网格的观察结果，并非普适样本量定理。

Common-CATE 成立时，logdet greedy 在本轮主条件中达到穷举 logdet 最优，选桥后的实际 Bernoulli 目标 MSE 也接近目标风险最优；B=4 的相对精确 MSE regret 约 **0.48%**。然而，中等站点异质性下，4 桥的名义 95% 区间平均覆盖率从原始规模的 **52.32%** 降至 20 倍规模的 **10.79%**。矩匹配 Gaussian 给出几乎相同的覆盖率。因此，主要问题是共同均值结构失配，而非误差分布不够高斯。

## 1. 实际执行了什么

三名独立子代理均使用用户指定的 `gpt-6.1-sol / high`：数学代理推导 MLE、Delta 方法、标量定理映射并构建输入；计算代理实现并运行 Bernoulli Monte Carlo；审计代理独立重算概率、方差、穷举最优及逐目标汇总。主代理冻结方案、核对解释边界、整合结果并校验保留状态。

原始设计保持为 57 站点、7,228 名参与者；40 source sites 共 4,365 人，17 target sites 共 2,863 人。DGP 拟合仅使用 source 结局。真实 target 结局没有用于拟合、调参、菜单选择或高斯近似校准；历史 target profiles 仅作回顾性设计点。此前研究已接触过 target 结果，因此这不是前瞻注册或对研究者历史知情状态的保证。完整性检查对旧文件只作字节哈希比较，不把旧 target 结果输入本轮模型。

完成 **46 个条件**：A/B × 5 个规模的 10 个主条件，各 5,000 次评估；3 个未知类别极端补全及 9 个 Other 概率组合，在规模 1、5、20 下共 36 个次条件，各 2,000 次评估。每条件另生成独立的 2,000 次 oracle 选择 pilot；不可识别的菜单不作选桥排名。总共生成 122,000 个评估世界和 92,000 个 pilot 世界，每个世界包含来源和独立未来实验的向量化二项计数；这些数不是新增真实参与者。

正式模拟耗时 **{manifest['elapsed_seconds']:.2f} 秒**；逐目标重放导出另耗时 **{exporter['elapsed_seconds']:.2f} 秒**。正式运行前的计时 pilot 为 1.15 秒，给用户的更新预测为 2–5 分钟 CPU。此次不需要 GPU。

## 2. DGP、未知类别与稀疏 Other

每个原有 observed-profile set 写为 U_s = l_s + r_s Δ₃。主场景采用其重心；敏感性使用把所有未知质量分别分配给 Male、Female、Other 的三个极端点。真实未知标签保持未知，没有把个体随意改成某一类别。

源数据记录为 Other 的参与者仅 12 人（控制 7 人、成功 4；处理 5 人、成功 1），还有 47 个未知类别；全样本记录为 Other 的参与者为 29 人、未知为 90 人。所有 4,365 个 source 结局都进入拟合：已知类别采用对应 Bernoulli likelihood，未知类别采用预先固定的均匀潜在类别混合 likelihood。该混合是假设，不能解释为真实缺失机制已被识别。

用于生成 DGP 的 q 加入半次成功、半次失败的正则项；这仅用于生成概率，**没有修补模拟中失败的 MLE**，也不应称为 Jeffreys 后验众数。控制组 q 为 (0.297029, 0.329102, 0.496486)，处理组为 (0.492982, 0.511767, 0.307273)。未经正则化的 source 拟合另供冻结的规划方差使用。Other 概率敏感性为 (q₀, q₁)∈{{0.2,0.5,0.8}}²，全数报告。

DGP A 的 q 在站点间共享，γ_c=q₁c−q₀c，τ_s=p_sᵀγ 精确成立。DGP B 在处理概率上添加固定、站点间无权均值为零、幅度不超过 0.05 的扰动，无 clipping；其真实站点效应是 τ_s=p_sᵀγ+δ_s。无权均值为零不意味着选中的桥或目标加权偏差为零。

类别记录发生在任务之后。模拟把潜在类别稳定性和报告不受处理影响作为明确假设，没有用此实验验证该现实条件。每个 U_s 中固定一个代表 p_s，也没有获得对整个 U_s 同时有效的现实证书。

规模 c 下每个历史 treatment arm 的总人数精确乘 c，按固定 p_s 用 Hamilton 最大余数法安排未来分层实验的整数类别人数，保留 treatment ratio 和站点相对规模。人口标准化 profile 不变，整数类别比例有已记录的舍入误差。**这不是把历史 arm×category 单元机械乘 c**；若机械复制原本为零的单元，空单元会永远保持为零，不能得到这里的改善。

## 3. MLE、Delta 方法与失败的具体含义

对于正计数单元 K~Binomial(n,q)，有限 logistic MLE 为 β̂=log[K/(n−K)]，仅在 0<K<n 时存在。K=0 或 n 时，有限 β̂ 不存在，但闭区间 [0,1] 上的扩展概率 MLE q̂=K/n 仍有数学定义。正权重类别 n=0 则使所要求的饱和风险差不可识别，保留 NA，不能填值。

标准化风险差和方差为

τ̂_s = Σ_c p_sc(q̂_s1c−q̂_s0c)，

v_s = Σ_c p_sc² [q_s1c(1−q_s1c)/n_s1c + q_s0c(1−q_s0c)/n_s0c]。

非空单元下，此 oracle 方差对扩展概率估计是**精确有限样本方差**；近似的是标准化误差分布。各活跃单元比例保持正、概率远离 0/1、信息随规模增长以及实验独立时，MLE 正态极限和 Delta 方法给出 (τ̂−τ)/√v ⇒ N(0,1)。代入 q̂ 的方差还存在有限单元偏小：E[q̂(1−q̂)]=(1−1/n)q(1−q)。全部推导、稀疏项可忽略的条件及联合极限见 `mle_delta_derivation.md`。

本轮使用解析解，因此不存在迭代求解器不收敛；这不代表不存在分离或有限 MLE 失败。两种估计器分别保留。所有 57 个站点均报告，未定义区间计为无条件覆盖失败，另列可用性条件下的统计量。低可用率造成的“无条件覆盖低”不得误读为可定义区间本身同样差。

## 4. 原始规模及扩样结果

预设功能近似门槛包括可标准化率≥99%、|均值 Z|≤0.10、方差比在 [0.9,1.1]、|偏度|≤0.30、|超额峰度|≤0.50、7 个 QQ 分位点最大误差≤0.20 SD，以及 90%/95% 覆盖偏差各≤1.5 个百分点。严格有限 MLE 还要求其存在率≥99%。联合 12 维门槛额外检查有效率、95% 矩形覆盖及非对角相关。门槛在计时 pilot 前确定，10 个运行输入/代码文件在正式运行前锁定哈希；这是有限 Monte Carlo 决策规则，并非经多重检验校正的模型真实性判定。

{scaling_table}

表中 oracle/plug-in 列是扩展概率风险差通过全部功能门槛的数量；最后两列仅统计有限 MLE 存在率门槛。A 在 c=20 时最差站点的有限 MLE 存在率仍为 46.54%，B 为 43.60%。原因是 Other 单元稀疏，而该类别在风险差中的权重可以很小：参数 MLE 经常分离，并不必然使整个加权风险差偏离正态。

固定 12 桥菜单的 oracle 扩展功能边际及联合近似从 c=1 起通过；每个模拟样本 plug-in 标准误的对应门槛从 c=5 起通过；严格有限 logistic MLE 的对应门槛从 c=20 起通过，联合可用率为 A 99.32%、B 99.12%。这 12 个设计预先从 29 个非空支持合格站点中按最远点规则选择。所有 57 个诊断站点仍保留，该菜单限制构成结论适用范围的一部分。

需要区分两种“plug-in”：上述诊断使用每次未来样本的 q̂ 估计 SE；下面选桥使用一次真实 source 拟合得到并冻结的规划方差。后者并未通过每次未来桥结局重估方差或改变候选菜单，其误差也不因只扩张模拟未来人数而自动消失。

## 5. 高斯选桥在实际 Bernoulli 数据流上的表现

每次重复重新生成全部 40 个 source 实验，按类别汇总为三个标量 source 观测 z_c，使用明确的工作先验 N(0,I₃)。它是 pooled category contrast 模型，不是声称 40 个站点的饱和 MLE 都成功。未来桥与 source 独立生成，即使复用同一历史 profile 身份。候选为 armstrong、radboud、tanzania、ouhk、kwazulu、osnabruck、umich、ulatina、tilburg、pascal、padua、queensland2。

桥观测为一个标量 τ̂_b≈N(p_bᵀγ,v_b)，因此 x_b=p_b，与 Theorem 5.6 的 scalar observation 形式相符，无需把桥改成向量观测定理。V_S=(V₀⁻¹+Σ_b p_bp_bᵀ/v_b)⁻¹；所有方法共用来源、先验、解码器、菜单、噪声流和实验个数预算。预算 B=1、2、4 对应 12、66、495 个穷举子集。另有不增加桥的 source-only 基准。

以下主表使用冻结 source 拟合规划方差及扩展概率 MLE，覆盖是 17 个目标的平均边际覆盖。列出的区间是工作 Gaussian posterior 的名义 95% 区间；固定真值下不自动具有频率学 95% 保证。

{bridge_table}

{policy_table}

在 A、c=1、B=4 下，greedy 相对不加桥的精确 MSE 降低 **{reduction:.2f}%**；选中 tanzania、ulatina、pascal、queensland2，需 582 个模拟新增参与者。在 A 主场景中，预算 B=1、2 的精确 MSE regret 为零，B=4 约 0.48%。所有主条件的 greedy 与穷举 logdet 在信息目标上相等，但这不是 logdet 一般能最优或目标 MSE 一般受该定理保证的证明。

这些策略预算相同的是**实验个数**，并非参与者数；例如 random 的 B=4 平均人数更少。不能据此声称等参与者成本最优，也没有在本轮比较直接目标实验。random 行为对全部同预算子集等概率取平均；两个 Bernoulli oracle 分别按精确模拟真风险、独立 2,000 次 pilot 风险选取，均不是现实可实施策略。pilot oracle 在独立评估流上可能被其他设计偶然超过，保留有符号 regret。

固定线性解码器的 MSE 只取决于均值、协方差和偏差，因此 Bernoulli 与矩匹配 Gaussian 的 MSE **在代数上精确相同**。这项数值一致性不能单独验证高斯尾部；MAE、QQ、联合诊断和覆盖对比才提供额外的分布证据。代码包含重复来源噪声、先验收缩偏差以及 B 的结构偏差，没有把工作 posterior covariance 直接当作真实采样协方差。

## 6. 异质性、逐目标结果和敏感性

B 的个体实验可以在自身真实均值附近近似正态，但不同站点已不共享同一个 γ。选桥和来源汇总仍用共同均值，样本增加会缩小方差而保留运输偏差。A/B 的 centered normality 门槛相似，目标覆盖却完全不同；这正是需要区分的两个问题。

{target_table}

全体 17 个目标的 MSE、MAE、可用率及两种覆盖统计已存于 `target_level_metrics.csv`（68,816 行）。不能只用平均覆盖掩盖 B 下部分目标的零覆盖。20 倍规模下，即使选择模拟真风险最优的 4 桥组合，平均覆盖也约 10.43%，oracle 方差或更优选桥并不修复错误的共同效应假设。

三个未知类别极端补全全部纳入：all-Male/all-Female 在 c=1 时使冻结菜单出现活跃空单元，整条件选桥比较保留为 unavailable，没有更换菜单或填补 MLE；其全部 57 站点诊断仍输出。其余规模可计算。Other 的 9 个概率组合、3 个规模共 27 个敏感性条件中，source-planned 4 桥 greedy 的覆盖范围为 **{100*sensitivity.coverage95_unconditional.min():.2f}%–{100*sensitivity.coverage95_unconditional.max():.2f}%**，相对精确 MSE regret 约 0.48%；这说明本轮结果在此有限敏感性网格中稳定，不意味着所有稀有类别概率或真实缺失机制都得到验证。

来源 profile 设计矩阵秩为 3、条件数约 95.02；实际 pooled source 标量设计为三个坐标方向，V₀ 的特征值和条件数另外逐条件报告。主场景全部可行子集的最大 posterior 条件数在 **{kappa_lo:.2f}–{kappa_hi:.2f}** 之间。定理推论给出的 greedy 绝对目标半径上界约为实际平均边际半径的 **{bound_lo:.2f}–{bound_hi:.2f} 倍**，较松。信息目标很接近最优，不代表该绝对半径上界数值上紧。

## 7. Theorem 5.6 能说什么

1. 有限样本 Bernoulli 风险差是离散分布；解析概率 MLE 并不会使其精确 Gaussian。
2. 活跃单元信息增长、概率位于内部且独立时，MLE 与 Delta 方法给出局部标量近似。固定独立 12 候选满足各自条件时可得到联合极限；共享未知 nuisance 或共享参与者需额外处理。
3. 本轮桥确实使用标量 p_bᵀγ。三个 pooled source summary 是三个已有标量观测；工作 Gaussian 先验超出真实 γ∈[−1,1]³ 的支持范围，属于局部模型而非精确 Bernoulli 生成先验。
4. 固定 PSD 信息增量的 logdet 集函数，其单调次模性及 greedy 的 1−1/e 下界是精确矩阵代数结论。把该 logdet 解释为 mutual information、把其 covariance 解释为真实 Bernoulli posterior，则需要 Gaussian 模型或另行证明的近似。
5. source 拟合规划方差有参数误差，未来样本 plug-in SE 另有有限单元偏差。设计排序稳定还需要候选间一致误差控制、可控条件数及最优间隙；单个估计量 CLT 本身不足以保证 argmax 完全相同。
6. logdet guarantee 只属于其信息目标，不属于 target-variance greedy、nearest、random 或目标风险 oracle。主模拟的低 MSE regret 是额外经验结果。近似渐近解释还要求共同均值正确、噪声估计一致及相关误差均可控制。
7. 真正的有限样本 Bernoulli 扩展需要均匀分布近似/集中界、噪声与 profile 校准、设计选择误差传递及明确的区间保证；本次没有完成这样的新定理，也没有声称已有定理可无条件用于 Bernoulli。

详细推导、posterior 与 sandwich 采样协方差、近似 argmax regret 条件均见 `theorem_5_6_compatibility.md`。

## 8. 可用于 rebuttal 的结论及不能使用的说法

可引用的英文表述：

> We evaluated the scalar Gaussian design surrogate using independent Bernoulli trials calibrated from source outcomes and historical site profiles. In the prespecified common-CATE simulation, log-determinant greedy attained the exhaustive log-determinant optimum across the tested main conditions and incurred at most 0.49% relative target-MSE regret. This is a finite-menu simulation result, not an extension of the theorem to exact Bernoulli likelihoods. Sparse cells limited finite-logit MLE existence; the extended risk-difference functional met our all-site Gaussian-approximation criteria from fivefold sample sizes with oracle variances and tenfold sample sizes with sample plug-in variances. Prespecified site heterogeneity produced severe undercoverage despite accurate centered Gaussian approximations, identifying common-effect misspecification as a separate limitation.

这为 KoBT Weakness 4 增加了一条具体回应：高斯选桥准则可在明确的非高斯二元实验模拟中检验，其性能和失效边界都有量化证据。它不能完整消除“现实适用性”疑问。不能写成“57 个真实站点已验证高斯定理”“有限样本保证已推广到任意非高斯数据”“20 倍样本已真实采集”“真实 Common-CATE 已成立”，也不能把这个固定 profile 模拟叫作完整机制集合的真实因果覆盖验证。

下一步如果由作者决定写入论文，适合定位为 **Bernoulli simulation robustness / approximation audit**，同时保留 A 与 B、全 57 站点失败率及窄菜单范围。本轮没有自动修改正文或削弱定理条件。

## 9. 独立核验、复现与保留状态

审计覆盖全部 10,488 条站点诊断、5,244 个站点-arm 规模配置、50,424 条穷举子集风险及全部逐目标导出。独立二项方差核对最大相对差约 6.7×10⁻¹³；所有风险 MC 与精确值的最大标准化差为 3.03 个报告 MC SE；oracle 重建、greedy 界和随机子集平均风险均无不一致。逐目标均值和主输出最大差小于 7×10⁻¹⁴。所有门槛通过/不通过仍有 Monte Carlo 不确定性，不能解读为统计上精确的转折点。

代码、协议、输入的 10 个冻结哈希及逐目标导出所关联的 9 个主结果哈希均一致。论文仓库仍为 `{current['head'].strip()}`，分支 `{current['branch'].strip()}`，工作区 clean；原稿、附录和 PDF 的 3 个保护哈希不变，前一轮 48 个研究文件不变。没有执行 push 或修改远端。

关键文件：`dgp_specification.md`、`mle_delta_derivation.md`、`theorem_5_6_compatibility.md`、全部结果 CSV、`monte_carlo_manifest.json`、`target_metrics_export_manifest.json`、`audit/final_independent_audit.md`、`audit/final_preservation_check.json`、`artifact_manifest.json`。

已冻结输入与代码可复现。为避免覆盖现有证据，在项目目录执行以下 PowerShell 命令，将复现实验写入新目录（预计本机约 2–5 分钟）：

```powershell
$studyRoot = 'D:\\study\\zzh科研\\phase1\\manylabs2_mle_gaussian_bridge'
$replayDir = Join-Path $studyRoot ('replay_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
& 'D:\\python\\python.exe' -B -X utf8 (Join-Path $studyRoot 'code\\bernoulli_mc.py') --protocol (Join-Path $studyRoot 'protocol\\execution.json') --outdir $replayDir
& 'D:\\python\\python.exe' -B -X utf8 (Join-Path $studyRoot 'code\\export_target_metrics.py') --protocol (Join-Path $studyRoot 'protocol\\execution.json') --outdir $replayDir
```

环境：NumPy {manifest['numpy']}，pandas {manifest['pandas']}，SciPy {manifest['scipy']}。`code/build_inputs.py` 记录输入和参数生成逻辑；正式复现优先使用冻结的 `protocol/execution.json`，不重新拟合或覆盖已冻结输入。
'''
    (ROOT / 'final_report.md').write_text(report, encoding='utf-8')
    handoff = f'''请作为我的研究讨论伙伴，依据下面已经完成的实验，帮助决定如何回应 ICLR Reviewer KoBT 的 Weakness 4，以及是否值得把这一模拟放入论文。请区分已取得证据、尚未满足的条件和下一步选择，不要把模拟当成真实数据验证或直接命令改论文。

论文：When Can Experiments Be Reused? Certified Transport, Refusal, and Causal Bridging。
本轮任务：用 Many Labs 2 的设计和 source 结局校准 Bernoulli DGP，推导 saturated logistic MLE→Delta 风险差→标量 Gaussian bridge surrogate，并用真实 Bernoulli Monte Carlo 检验 Theorem 5.6 的 logdet 选桥准则。三代理均 gpt-6.1-sol/high，分别数学、实现、独立审计。

实际已完成：57 站点/7,228 人的历史设计，40 sources/4,365 人，17 targets/2,863 人；target 真实结局不用于拟合、调参、选桥、校准，profile 的使用明确为回顾性。全部 47 个 source 未知类别用预设 uniform latent-mixture likelihood 保留；DGP-only 半计数正则化，不修补模拟 MLE。主 profile 为各 U_s 重心，另有三个极端补全和 Other 概率 {{0.2,0.5,0.8}}²。未来分层模拟用 Hamilton allocation 保持各 arm 总数和固定人口 profile，不能误称机械复制历史类别格子。DGP A 共用 q，τ_s=p_sᵀγ；B 加入最大 0.05、站点均值为零的处理概率扰动。未知标签、post-task reporting、Common-CATE 都没有被真实数据验证。

46 条件：A/B×规模1/2/5/10/20，各5,000评估；36次敏感性各2,000；每条件独立2,000 oracle pilot。正式模拟90.17秒、逐目标导出33.57秒，seed2026110901。12个候选从29个非空支持设计中预先选择，所有57站点保留诊断；两种极端补全c1不支持固定菜单，保留unavailable。source在每次模拟重新生成并pool成三个category contrasts，工作先验N(0,I₃)，桥为独立新模拟；source-fitted planning variance与每次样本plug-in SE是两个概念。

数值结论：原始规模仅29/57的饱和RD可定义，28个active-empty。扩展概率MLE的全57站点功能正态性oracle最早5倍全部过门槛，sample plug-in最早10倍；严格有限logit MLE到20倍仍不过（A只有28/57达到99%存在率，最差46.54%）。预设12候选的扩展oracle边际+联合c1可过、sample plug-in c5可过、严格finite-MLE c20才可过。不能把扩展K/n边界估计说成有限logit MLE成功。

比较预算B=1/2/4，穷举12/66/495组合：logdet greedy/exhaustive、target-variance greedy、nearest、exact uniform random、精确Bernoulli目标MSE oracle、独立pilot MC oracle，另有source-only。均在实际Bernoulli draws评估。A主条件greedy达到logdet穷举最优，B1/2精确MSE regret为0，B4约0.48%。A c1 B4 source-planned：source-only精确MSE0.0002316475；greedy0.0002064282，改善{reduction:.2f}%；MC MSE0.0002119231、覆盖94.61%、新增582个模拟参与者。风险oracle0.0002054391、617人；random0.0002140479、平均395.33人。因此预算相同只指实验个数，不能声称同参与者成本最优；没有直接目标实验对照。

B c1 B4覆盖52.32%，c20仅10.79%，矩匹配Gaussian分别52.42%和10.76%；c20各目标覆盖0–94.9%。这表明高斯误差近似可好，但共同均值错误仍导致严重失效。A/B的functional normality类似，不能把B失败归因于非高斯或声称扩样能修复结构偏差。Other网格source-plannedB4覆盖约94.22%–95.72%。主场景posterior最大条件数103.43–136.06，半径推论上界是实际半径22.38–27.33倍，数值松。

理论判断：每桥是标量x_b=p_b，符合scalar surrogate。固定PSD增量的logdet次模性和greedy比例在矩阵目标上精确成立；其Gaussian互信息/后验解释对Bernoulli不是自动有效。对于固定affine decoder，Bernoulli与矩匹配Gaussian的MSE由矩决定而精确相同，不能用MSE一致单独证明尾部Gaussian；本轮另看QQ、联合分布、MAE和coverage。严格渐近传递需活跃cell信息增长、内部q、独立固定menu、方差一致性、conditioning和选择间隙控制。真实有限样本Bernoulli保证未证明；fixed truth下Gaussian posterior区间不是自动频率学95%区间。

交付：推导、DGP说明、协议/种子/代码、10,488诊断行、50,424穷举风险行、68,816逐目标行，独立审计全部通过（原冻结10hash、导出相关9hash不变）。final_report.md含详细数字、适用范围、可用英文rebuttal段落；gptchat_handoff_prompt.md为此交接稿。目录：D:\\study\\zzh科研\\phase1\\manylabs2_mle_gaussian_bridge。

保留状态：本轮没有改论文/PDF/Overleaf/GitHub；论文HEAD b58f4339c1bf4be6b2dfe477eba0e41fdef0ccf6，branch revision/manylabs2-conditional-20261109，clean。前轮48文件和3个论文/PDF保护文件hash不变。

请回答：这些结果能把KoBT意见回应到哪一步？该如何用准确的主句表述“高斯准则在二元实验中可有用”而不夸大？是否应把A的成功与B的失效成对展示？是否有必要再做实验，若有，请给出有限且能区分剩余问题的设计；不要为了改善数字修改已冻结DGP或隐去失败站点。若需要原始文件，请让我提供本报告或相关CSV，勿假装能直接访问我本机路径。
'''
    (ROOT / 'gptchat_handoff_prompt.md').write_text(handoff, encoding='utf-8')

    required = ['dgp_specification.md', 'mle_delta_derivation.md', 'gaussian_approximation_results.csv',
                'sample_size_scaling.csv', 'bridge_design_comparison.csv', 'bernoulli_monte_carlo_results.csv',
                'theorem_5_6_compatibility.md', 'final_report.md', 'gptchat_handoff_prompt.md']
    assert all((ROOT / p).is_file() and (ROOT / p).stat().st_size for p in required)
    files = {p.relative_to(ROOT).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
             for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name != 'artifact_manifest.json'
             and '__pycache__' not in p.parts and not any(part.startswith('replay_') for part in p.parts)}
    artifact = {'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'study': 'Bernoulli MLE Gaussian bridge simulation',
                'lead_report_review': {'mathematical_scope': 'mle_math approved; recorded-category wording clarified',
                                       'numerical_claims': 'mle_compute approved; DGP A budget-regret scope clarified',
                                       'independent_audit': 'mle_audit passed core and per-target export reconciliation'},
                'required_deliverables_present': required, 'primary_code_sha256': manifest['code_sha256'],
                'seed': manifest['seed'], 'simulation_seconds': manifest['elapsed_seconds'],
                'target_export_seconds': exporter['elapsed_seconds'], 'files': files}
    (ROOT / 'artifact_manifest.json').write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'report': str(ROOT / 'final_report.md'), 'artifact_file_count': len(files),
                      'preservation': 'passed', 'paper_head': current['head'].strip(),
                      'prior_files_unchanged': len(prior_check), 'required_deliverables': len(required),
                      'A_c1_B4_exact_MSE_reduction_percent': reduction}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
