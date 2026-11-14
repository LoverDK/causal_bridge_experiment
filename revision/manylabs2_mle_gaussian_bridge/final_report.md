# Bernoulli 实验、MLE/Delta 高斯近似与选桥：最终报告

完成日期：2026-11-09。主种子：2026110901。本报告只总结本轮冻结方案的模拟与审计；未修改论文、PDF、Overleaf 或 GitHub。

## 研究结论

**这条连接在限定的实验设计和 Common-CATE 模型下有实用价值，但不能把原始 Many Labs 2 的全部站点直接宣布为满足线性高斯定理。** 原始规模下，57 个站点中只有 29 个能定义本轮要求的饱和分层风险差估计；另外 28 个存在正权重类别的空单元。对于预先按设计支持条件选出的 12 个候选，扩展概率 MLE 的标量风险差在 oracle 方差标准化下已经通过预设边际及联合近似门槛。这个较窄的成功结论不能推广为 57 站点有限 logistic MLE 均成功。

在测试规模 {1,2,5,10,20} 中，全 57 站点的扩展风险差首次全部通过 oracle 方差门槛是 **5 倍规模**，使用每次模拟样本估计的 plug-in 方差则是 **10 倍规模**。如果坚持要求有限 logistic 参数 MLE 的存在率至少 99%，全站点到 20 倍仍不通过；固定 12 个候选的严格边际与联合门槛在 20 倍才通过。这些是所设 DGP、未来分层设计和有限网格的观察结果，并非普适样本量定理。

Common-CATE 成立时，logdet greedy 在本轮主条件中达到穷举 logdet 最优，选桥后的实际 Bernoulli 目标 MSE 也接近目标风险最优；B=4 的相对精确 MSE regret 约 **0.48%**。然而，中等站点异质性下，4 桥的名义 95% 区间平均覆盖率从原始规模的 **52.32%** 降至 20 倍规模的 **10.79%**。矩匹配 Gaussian 给出几乎相同的覆盖率。因此，主要问题是共同均值结构失配，而非误差分布不够高斯。

## 1. 实际执行了什么

三名独立子代理均使用用户指定的 `gpt-6.1-sol / high`：数学代理推导 MLE、Delta 方法、标量定理映射并构建输入；计算代理实现并运行 Bernoulli Monte Carlo；审计代理独立重算概率、方差、穷举最优及逐目标汇总。主代理冻结方案、核对解释边界、整合结果并校验保留状态。

原始设计保持为 57 站点、7,228 名参与者；40 source sites 共 4,365 人，17 target sites 共 2,863 人。DGP 拟合仅使用 source 结局。真实 target 结局没有用于拟合、调参、菜单选择或高斯近似校准；历史 target profiles 仅作回顾性设计点。此前研究已接触过 target 结果，因此这不是前瞻注册或对研究者历史知情状态的保证。完整性检查对旧文件只作字节哈希比较，不把旧 target 结果输入本轮模型。

完成 **46 个条件**：A/B × 5 个规模的 10 个主条件，各 5,000 次评估；3 个未知类别极端补全及 9 个 Other 概率组合，在规模 1、5、20 下共 36 个次条件，各 2,000 次评估。每条件另生成独立的 2,000 次 oracle 选择 pilot；不可识别的菜单不作选桥排名。总共生成 122,000 个评估世界和 92,000 个 pilot 世界，每个世界包含来源和独立未来实验的向量化二项计数；这些数不是新增真实参与者。

正式模拟耗时 **90.17 秒**；逐目标重放导出另耗时 **33.57 秒**。正式运行前的计时 pilot 为 1.15 秒，给用户的更新预测为 2–5 分钟 CPU。此次不需要 GPU。

## 2. DGP、未知类别与稀疏 Other

每个原有 observed-profile set 写为 U_s = l_s + r_s Δ₃。主场景采用其重心；敏感性使用把所有未知质量分别分配给 Male、Female、Other 的三个极端点。真实未知标签保持未知，没有把个体随意改成某一类别。

源数据记录为 Other 的参与者仅 12 人（控制 7 人、成功 4；处理 5 人、成功 1），还有 47 个未知类别；全样本记录为 Other 的参与者为 29 人、未知为 90 人。所有 4,365 个 source 结局都进入拟合：已知类别采用对应 Bernoulli likelihood，未知类别采用预先固定的均匀潜在类别混合 likelihood。该混合是假设，不能解释为真实缺失机制已被识别。

用于生成 DGP 的 q 加入半次成功、半次失败的正则项；这仅用于生成概率，**没有修补模拟中失败的 MLE**，也不应称为 Jeffreys 后验众数。控制组 q 为 (0.297029, 0.329102, 0.496486)，处理组为 (0.492982, 0.511767, 0.307273)。未经正则化的 source 拟合另供冻结的规划方差使用。Other 概率敏感性为 (q₀, q₁)∈{0.2,0.5,0.8}²，全数报告。

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

| 规模 c | 可定义 RD 的站点数 | A oracle 通过 | A plug-in 通过 | B oracle 通过 | B plug-in 通过 | A 有限 MLE 存在率≥99% | B 有限 MLE 存在率≥99% |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 29 | 29/57 | 18/57 | 29/57 | 15/57 | 7/57 | 7/57 |
| 2 | 38 | 38/57 | 35/57 | 38/57 | 33/57 | 14/57 | 14/57 |
| 5 | 57 | 57/57 | 55/57 | 57/57 | 56/57 | 14/57 | 14/57 |
| 10 | 57 | 57/57 | 57/57 | 57/57 | 57/57 | 17/57 | 18/57 |
| 20 | 57 | 57/57 | 57/57 | 57/57 | 57/57 | 28/57 | 27/57 |

表中 oracle/plug-in 列是扩展概率风险差通过全部功能门槛的数量；最后两列仅统计有限 MLE 存在率门槛。A 在 c=20 时最差站点的有限 MLE 存在率仍为 46.54%，B 为 43.60%。原因是 Other 单元稀疏，而该类别在风险差中的权重可以很小：参数 MLE 经常分离，并不必然使整个加权风险差偏离正态。

固定 12 桥菜单的 oracle 扩展功能边际及联合近似从 c=1 起通过；每个模拟样本 plug-in 标准误的对应门槛从 c=5 起通过；严格有限 logistic MLE 的对应门槛从 c=20 起通过，联合可用率为 A 99.32%、B 99.12%。这 12 个设计预先从 29 个非空支持合格站点中按最远点规则选择。所有 57 个诊断站点仍保留，该菜单限制构成结论适用范围的一部分。

需要区分两种“plug-in”：上述诊断使用每次未来样本的 q̂ 估计 SE；下面选桥使用一次真实 source 拟合得到并冻结的规划方差。后者并未通过每次未来桥结局重估方差或改变候选菜单，其误差也不因只扩张模拟未来人数而自动消失。

## 5. 高斯选桥在实际 Bernoulli 数据流上的表现

每次重复重新生成全部 40 个 source 实验，按类别汇总为三个标量 source 观测 z_c，使用明确的工作先验 N(0,I₃)。它是 pooled category contrast 模型，不是声称 40 个站点的饱和 MLE 都成功。未来桥与 source 独立生成，即使复用同一历史 profile 身份。候选为 armstrong、radboud、tanzania、ouhk、kwazulu、osnabruck、umich、ulatina、tilburg、pascal、padua、queensland2。

桥观测为一个标量 τ̂_b≈N(p_bᵀγ,v_b)，因此 x_b=p_b，与 Theorem 5.6 的 scalar observation 形式相符，无需把桥改成向量观测定理。V_S=(V₀⁻¹+Σ_b p_bp_bᵀ/v_b)⁻¹；所有方法共用来源、先验、解码器、菜单、噪声流和实验个数预算。预算 B=1、2、4 对应 12、66、495 个穷举子集。另有不增加桥的 source-only 基准。

以下主表使用冻结 source 拟合规划方差及扩展概率 MLE，覆盖是 17 个目标的平均边际覆盖。列出的区间是工作 Gaussian posterior 的名义 95% 区间；固定真值下不自动具有频率学 95% 保证。

| DGP | c | 不加桥的精确 MSE | 4 桥精确 MSE | 4 桥 MC MSE | 4 桥 MC MAE | Bernoulli 覆盖 | 矩匹配 Gaussian 覆盖 | 相对最优 MSE regret | 模拟新增人数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 1 | 0.0002316475 | 0.0002064282 | 0.0002119231 | 0.011551 | 94.61% | 95.00% | 0.481% | 582 |
| A | 5 | 4.629501e-05 | 4.124445e-05 | 4.202006e-05 | 0.005174 | 94.71% | 95.00% | 0.480% | 2910 |
| A | 20 | 1.158144e-05 | 1.031798e-05 | 1.065556e-05 | 0.002605 | 94.58% | 94.99% | 0.480% | 11640 |
| B | 1 | 0.001184967 | 0.001174301 | 0.001178155 | 0.028741 | 52.32% | 52.42% | 5.862% | 582 |
| B | 5 | 0.001000431 | 0.00100983 | 0.001008399 | 0.027031 | 25.20% | 25.27% | 7.663% | 2910 |
| B | 20 | 0.0009659073 | 0.0009791043 | 0.0009793766 | 0.026757 | 10.79% | 10.76% | 8.079% | 11640 |

| 策略（A，c=1，B=4） | 精确目标 MSE | MC MSE ± MC SE | 平均新增人数 | 信息增益 | 精确 MSE regret |
| --- | --- | --- | --- | --- | --- |
| logdet_greedy | 0.0002064282 | 0.0002119231 ± 3.9e-06 | 582.00 | 0.072145 | 0.481% |
| logdet_exhaustive | 0.0002064282 | 0.0002119231 ± 3.9e-06 | 582.00 | 0.072145 | 0.481% |
| target_variance_greedy | 0.0002054391 | 0.0002111285 ± 3.9e-06 | 617.00 | 0.071923 | 0.000% |
| nearest_profile | 0.0002090339 | 0.0002152647 ± 4e-06 | 524.00 | 0.059594 | 1.750% |
| random_uniform_expectation | 0.0002140479 | 0.0002207174 ± 3.9e-06 | 395.33 | 0.047847 | 4.190% |
| bernoulli_exhaustive_oracle | 0.0002054391 | 0.0002111285 ± 3.9e-06 | 617.00 | 0.071923 | 0.000% |
| bernoulli_mc_exhaustive_oracle | 0.0002059334 | 0.0002127761 ± 4e-06 | 601.00 | 0.070224 | 0.241% |

在 A、c=1、B=4 下，greedy 相对不加桥的精确 MSE 降低 **10.89%**；选中 tanzania、ulatina、pascal、queensland2，需 582 个模拟新增参与者。在 A 主场景中，预算 B=1、2 的精确 MSE regret 为零，B=4 约 0.48%。所有主条件的 greedy 与穷举 logdet 在信息目标上相等，但这不是 logdet 一般能最优或目标 MSE 一般受该定理保证的证明。

这些策略预算相同的是**实验个数**，并非参与者数；例如 random 的 B=4 平均人数更少。不能据此声称等参与者成本最优，也没有在本轮比较直接目标实验。random 行为对全部同预算子集等概率取平均；两个 Bernoulli oracle 分别按精确模拟真风险、独立 2,000 次 pilot 风险选取，均不是现实可实施策略。pilot oracle 在独立评估流上可能被其他设计偶然超过，保留有符号 regret。

固定线性解码器的 MSE 只取决于均值、协方差和偏差，因此 Bernoulli 与矩匹配 Gaussian 的 MSE **在代数上精确相同**。这项数值一致性不能单独验证高斯尾部；MAE、QQ、联合诊断和覆盖对比才提供额外的分布证据。代码包含重复来源噪声、先验收缩偏差以及 B 的结构偏差，没有把工作 posterior covariance 直接当作真实采样协方差。

## 6. 异质性、逐目标结果和敏感性

B 的个体实验可以在自身真实均值附近近似正态，但不同站点已不共享同一个 γ。选桥和来源汇总仍用共同均值，样本增加会缩小方差而保留运输偏差。A/B 的 centered normality 门槛相似，目标覆盖却完全不同；这正是需要区分的两个问题。

| DGP | c | 17 个目标各自覆盖率的最小值 | 最大值 |
| --- | --- | --- | --- |
| A | 1 | 94.36% | 94.88% |
| A | 20 | 94.26% | 95.00% |
| B | 1 | 3.60% | 94.42% |
| B | 20 | 0.00% | 94.90% |

全体 17 个目标的 MSE、MAE、可用率及两种覆盖统计已存于 `target_level_metrics.csv`（68,816 行）。不能只用平均覆盖掩盖 B 下部分目标的零覆盖。20 倍规模下，即使选择模拟真风险最优的 4 桥组合，平均覆盖也约 10.43%，oracle 方差或更优选桥并不修复错误的共同效应假设。

三个未知类别极端补全全部纳入：all-Male/all-Female 在 c=1 时使冻结菜单出现活跃空单元，整条件选桥比较保留为 unavailable，没有更换菜单或填补 MLE；其全部 57 站点诊断仍输出。其余规模可计算。Other 的 9 个概率组合、3 个规模共 27 个敏感性条件中，source-planned 4 桥 greedy 的覆盖范围为 **94.22%–95.72%**，相对精确 MSE regret 约 0.48%；这说明本轮结果在此有限敏感性网格中稳定，不意味着所有稀有类别概率或真实缺失机制都得到验证。

来源 profile 设计矩阵秩为 3、条件数约 95.02；实际 pooled source 标量设计为三个坐标方向，V₀ 的特征值和条件数另外逐条件报告。主场景全部可行子集的最大 posterior 条件数在 **103.43–136.06** 之间。定理推论给出的 greedy 绝对目标半径上界约为实际平均边际半径的 **22.38–27.33 倍**，较松。信息目标很接近最优，不代表该绝对半径上界数值上紧。

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

代码、协议、输入的 10 个冻结哈希及逐目标导出所关联的 9 个主结果哈希均一致。论文仓库仍为 `b58f4339c1bf4be6b2dfe477eba0e41fdef0ccf6`，分支 `revision/manylabs2-conditional-20261109`，工作区 clean；原稿、附录和 PDF 的 3 个保护哈希不变，前一轮 48 个研究文件不变。没有执行 push 或修改远端。

关键文件：`dgp_specification.md`、`mle_delta_derivation.md`、`theorem_5_6_compatibility.md`、全部结果 CSV、`monte_carlo_manifest.json`、`target_metrics_export_manifest.json`、`audit/final_independent_audit.md`、`audit/final_preservation_check.json`、`artifact_manifest.json`。

已冻结输入与代码可复现。为避免覆盖现有证据，在项目目录执行以下 PowerShell 命令，将复现实验写入新目录（预计本机约 2–5 分钟）：

```powershell
$studyRoot = 'D:\study\zzh科研\phase1\manylabs2_mle_gaussian_bridge'
$replayDir = Join-Path $studyRoot ('replay_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
& 'D:\python\python.exe' -B -X utf8 (Join-Path $studyRoot 'code\bernoulli_mc.py') --protocol (Join-Path $studyRoot 'protocol\execution.json') --outdir $replayDir
& 'D:\python\python.exe' -B -X utf8 (Join-Path $studyRoot 'code\export_target_metrics.py') --protocol (Join-Path $studyRoot 'protocol\execution.json') --outdir $replayDir
```

环境：NumPy 2.5.2，pandas 3.0.5，SciPy 1.18.1。`code/build_inputs.py` 记录输入和参数生成逻辑；正式复现优先使用冻结的 `protocol/execution.json`，不重新拟合或覆盖已冻结输入。
