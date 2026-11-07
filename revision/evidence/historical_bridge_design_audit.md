# HISTORICAL_BRIDGE_WORKFLOW01 独立设计审核

日期：2026-11-07。本审核只检查理论、设计公平性和报告方式；未运行新模拟、未抽取任何新outcomes。依据当前 `revision/non_gaussian_bridge/theorem_draft.tex`、`theorem_notes.md`、原200份structured design存档及主代理协议。收束时已核对冻结提交 `cdc146b` 的 `revision/HISTORICAL_BRIDGE_WORKFLOW01.json`，确认主预算4、独立reference噪声、全预算报告、200×200世界及pointwise联合边际范围与本审核一致。

## 审核结论与最终冻结决定

这个设计能回答：已有四项历史观测后，在有限新增预算内，按新定理选桥能缩短多少目标认证区间；相对随机/logdet/直接目标采样怎样；点估计与更高预算目标参考是否接近，方向结论是否有用且一致。

最终主预算为 **4**，对应原Panel D预算；**0、1、2、8全部报告，8为secondary**，不按结果挑主预算。参考为“共同历史 + 64次目标观测”，其64条未来噪声与所有policy未来噪声**独立**，仅共享历史观测和同一真实β。旧提议的嵌套small-direct参考已弃用，不应进入实现。

全部200个原p6/12候选设计保持原始V0、x、t和σ=.5；每设计按seed2026110740均匀不放回选4个历史类型，各产生一条实际模拟观测；历史选择固定在outcomes生成之前。所有方法共享这些历史数据。未来原12类型均可重复，每次是新独立观测。参数与噪声使用标准化t5，known mean0、known covariance/variance。每设计200个独立world，共40000world；这些是合成历史，不是真实校准archive。

α=.05给每个固定方法/预算的联合边际95%证书；不声称给定已观测历史后的后验覆盖，不声称固定β的统一覆盖，不声称全路径95%覆盖。点差阈值 .30 使用既定单位和尺度，不根据结果调整。成本单位为study-level effect observation，不能改称参与者。

## 1. 历史数据到估计与区间的完整公式

对某个固定设计，令V0为原存档正定协方差，目标为θ=tᵀβ，m0=0。历史索引H有4条观测；每条Y_i=x_iᵀβ+ε_i，v_i=σ_i²=.25。S表示历史和当前新增观测的**实例索引**并集，而不是去重的实验类型集合。

定义

\[
A_S=V_0^{-1}+\sum_{i\in S}x_ix_i^\top/v_i,\quad V_S=A_S^{-1},
\]
\[
\widehat\theta_S=t^\top V_S\sum_{i\in S}x_iY_i/v_i
=\sum_{i\in S}a_i(S)Y_i,\quad a_i(S)=t^\top V_Sx_i/v_i.
\]

原moment定理的实际误差系数必须从全部历史和新增观测展开：

\[
d_S=\sum_{i\in S}a_i(S)x_i-t,
\quad W_S=d_S^\top V_0d_S+\sum_{i\in S}a_i(S)^2v_i,
\]
\[
W_S=t^\top V_St=q_S,\qquad
I_S=[\widehat\theta_S-\sqrt{W_S/.05},\widehat\theta_S+\sqrt{W_S/.05}].
\]

历史基线正是S=H，所有方法budget0的估计、区间和实际观测必须逐项相同。

实现可以用递推：

\[
V_{new}=V_S-\frac{V_Sxx^\top V_S}{v+x^\top V_Sx},
\quad
\widehat\beta_{new}=\widehat\beta_S+
\frac{V_Sx}{v+x^\top V_Sx}(Y-x^\top\widehat\beta_S).
\]

但递推只是代数实现；应与全体观测重算的a、d、W校验。非Gaussian条件下，**不能把V_H当作条件于Y_H的后验协方差，重新假设β|Y_H服从已知协方差的prior**。所用概率界始终以原V0和全部观测误差为依据。V_S是该线性估计器的边际误差协方差，不必是后验协方差。

“实际历史证据区间”指中心确实用Y_H计算；在此known-moment模型中，宽度由历史设计和已知矩决定，不随Y_H数值改变。应公开这一点，不能暗示用历史数据学习出未知V0。

## 2. 选桥规则与重复观测

每一步在全部12种类型中选择：

\[
H(j\mid S)=\frac{(t^\top V_Sx_j)^2}{.25+x_j^\top V_Sx_j},
\quad q_{S+j}=q_S-H(j\mid S).
\]

target选择下一步实际W最小者，并核对其等价于最大H；logdet选择最大 `.5*log1p(xᵀVx/.25)`；random按独立于outcomes、事先冻结的随机类型次序；direct每次x=t且同σ=.5。固定tie-break，不能读真实β、θ、Y或参考结果选择类型。

重复实验类型并不违反有限菜单定理：将每个类型的第k次访问表示为不同实例(j,k)，噪声独立；在最大8步内可视作12×8个潜在实例，每步允许每类型下一个未用实例。历史实例与未来实例也必须分开。重复j时不得重新利用历史Y_j，或多次计数同一观测。

每步target是下一步最优，不保证4步或8步终值全局最优。logdet/random是同预算、同候选、同噪声的有效策略对照。完整direct在相同新增次数下使用相同历史；参考direct64不参与策略选择。

原候选x尺度是原生成器的一部分，某些类型单位观测信息较强。这是当前设计的性质，不能在结果出来后归一化/换候选，也不能将此场景优势概括成所有桥都优于direct。

## 3. 64次目标观测作为参考是否足够

设历史之后q_H=tᵀV_Ht>0。新增N条相互独立、方差.25的直接目标观测时，

\[
q_{H+direct(N)}=\frac{q_H}{1+Nq_H/.25}
=\left(q_H^{-1}+N/.25\right)^{-1}\le .25/N.
\]

因此N=64时，不需要知道真实β或观察结果，就有

\[
R_{ref}\le\sqrt{.25/(64\times.05)}=.2795085,
\quad width_{ref}\le .5590170<.60.
\]

64在原halfwidth .30尺度上确实“够用”；它不是无限精度真值，也不意味着所有参考区间都能排除0。可称“64次目标观测的高预算参考”或“满足预设证书精度的参考”，不能称ground truth。

未来reference noise与allpolicy future noise独立，避免small direct前缀和reference共享额外噪声而机械提高agreement。但所有方法和reference仍共享β、历史Y；比较是配对而非两个独立估计器。若要计算差值的理论二阶矩，应在观测union上补零后用a_policy−a_ref：

\[
\operatorname{Var}(\widehat\theta_{policy}-\widehat\theta_{ref})
= (X^\top c)^\top V_0(X^\top c)+\sum_i c_i^2v_i,
\quad c=a_{policy}-a_{ref}.
\]

不能简单相加W_policy+W_ref而忽略共享历史和β的协方差。现协议只需实证报告点差，不必额外提出一个未验证的difference证书。

## 4. 主指标及分母

### 区间缩短：先看历史基线，再比较同预算策略

每设计/方法/预算记录width、width/width_H、1−width/width_H、绝对缩短；主预算4分别与同预算random/logdet/direct做配对差。报告均值、median、分位数及胜/平/负设计比例；不要只报少数最有利design。

宽度在同一design的200world完全相同，所以其有效设计重复数是**200**，不是40000。不要通过重复world把width的标准误压小。若做总体CI，以design为聚类/外层重采样单位；点误差/方向等亦优先保持同design内方法、budget配对，分层或聚类方式事先声明。

### 与高预算参考接近：全目标点差

对全部40000world报 `abs(estimate_policy−estimate_ref)` 的mean/median/p90和 `≤.30` 比例；不先按参考显著、方法显著或结果大小筛选。并同时报对真实θ的MAE/RMSE、95%区间覆盖，以及参考自身的真误差/覆盖。这样不会把“两个估计碰巧接近”包装成正确。

`.30`近似比例是经验描述，不是统计等效性/非劣性检验。若桥接点差很小但其认证区间明显更宽，只能说点预测接近，不能说已经达到和direct64相同的认证精度。

### 三分类方向：必须保留“双方不足”

采用完全同一规则：lower>0为正，upper<0为负，其余不足；端点恰好为0归不足。

至少输出每预算、每方法对reference的3×3表。由此分开报告：

1. **有用同向/全部world**：双方同为正或同为负的数量除以40000；双方不足不算有用成功。
2. **双方不足/全部world**、明确反向/全部world，以及method决定率和reference决定率。
3. 在reference已明确的固定子集内，分别报同向、method不足、反向，给出该子集实际n；不能只报“双方已明确”后的同向率。
4. reference不足而method明确单列，不能自动称method错误；使用真实θ评估方向是否错，并明确这不是reference agreement。

主显示可并排放“点差≤.30”与“有用同向”，另报二者同时成立的比例；无需以未知结果修改阈值。全三分类一致率可以给，但不得把大批不足—不足主导的一致率作为研究结论。

95%边际覆盖只限制整体错误覆盖概率；不能解释成“被判正/负的子集只有5%错误”，那是不同的选择后条件风险。

## 5. 成本与公平性解释

历史4条观测是共同沉没成本。主budget4与reference64的新增成本是4对64；总观测数则8对68。两种口径都能列，主口径预先声明为新增study-effect observations，不能混用。

“花1/16新增预算”是预算设置，不是实验发现。只有在同时展示误差、认证width和有用方向结果后，才可讨论这种成本下降是否值得。若bridge4比direct4差，应保留；若bridge4接近reference点估计却区间很宽，也必须同时展示。

所有方法同H、Y_H、V0、t、noise方差、α和新增预算；同类型同次访问可以跨策略共享潜在观测以实现配对，但策略内部各次访问独立。reference使用专用独立stream。预算0输出需完全相同。

## 6. 实现检查和输出建议

实现建议：planner只接受设计、known moments、counts和seed；先冻结全部200设计的方法路径，再生成β/噪声。β=chol(V0)z，z各坐标为独立t5×sqrt(3/5)，不是逐样本标准化；noise也是同标准化t5乘.5，并与β独立。

必要确定性检查：

- history每设计恰4个不同类型、所有方法相同，输入archive hash一致。
- 初始估计/width逐world一致；每未来观测id只出现一次，reference streams与policyfuture disjoint。
- 所有历史+新增实际coeff生成的W与q数值相等；递推estimate与完整aᵀY相等。
- 每步W非增；target选择的W不高于该步所有12候选，和SM gain选择一致；固定tie-break可复建。
- direct64的R≤.2795085，不能在失败时跳过design或更换阈值。
- 修改scoring truth不改变已保存的plans/predictions；非观测型planner不读取Y/β。
- direction3×3计数和全分母闭合；参考未明确时条件比例无分母应为NA而非0/100%。

建议输出design_inputs/history_ids/path_counts/candidate_scores、per-world predictions+intervals、独立scoring表、按design聚合、方向3×3及全预算摘要；保存一个固定design/world的历史观测到最后区间的完整trace帮助作者理解。不要按结果挑“最成功示例”。

预算表是固定报告点，不按Y或方向结果选择停止。每点可称pointwise marginal95%；如果后来引入“第一个方向明确时停止”，必须另处理序贯有效性，不能沿用这次声明。

## 审核边界

本设计仍是线性观测、known moments、合成非Gaussian参数/噪声的structured实验。它能检验新定理如何指导已有证据上的目标收缩；不能自动解决真实机制集校准、非线性transport、真实干预成本、完整ExAtlas基线或一般最优性。Lean既有分模块验证范围应照原说明保留，不扩大成整条实验系统都已形式化证明。
