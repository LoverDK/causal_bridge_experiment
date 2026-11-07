# 主实验的模型与任务忠实性审计

日期：2026-11-07。此审计只读原论文、定理草稿、原存档、冻结协议和既有结果；没有修改实验、生成新世界或更换有利参数。数值交叉检查只重算已有分配的矩阵和解析下界。

## 结论

当前程序正确实现了新非高斯定理草稿中的**已知矩、随机参数、线性观测、设计型选桥**模型。原论文 Panel D 的 200 个设计也确实原样保留。没有发现能够解释结果差距的公式、索引或成本累计错误。

但这不是一般 ATLAS 的“有历史研究 → 校准机制集合 → 组合历史效果 → 发布/拒绝 → 桥接”的完整任务。它从随机生成的先验二阶矩开始，没有真实历史研究结果。新加入的 direct 基线假定目标实验随时可做、噪声与桥接相同、每次研究成本相同。在这些明确假设下，原设计里的桥接通常更贵；这一结果不能用来否定一般的历史证据复用，也不能用“原设计原样保留”把它称为已经检验了历史复用的经济优势。

独立全局下界检查进一步表明：198/200 个设计中，**即使改成全局最优桥接分配，在当前候选、单位研究成本和 W 证书下也无法比 direct 更省**。因此当前主要问题不是贪心算法没有找好，而是所检验的任务和费用假设与作者希望表达的优势之间存在缺口。

## 逐项对应

| 项目 | 原论文 / 草稿 | 当前实现 | 审计判断 |
| --- | --- | --- | --- |
| 线性观测 | 原 01.tex 已有 Y_b=x_bᵀβ+ε_b | 相同 | 线性不是这次偷偷增加的条件 |
| 初始 P | 原 structured repair 的 V0 是 β~N(0,V0) 的先验协方差 | 从原档案读取 prior，β=Cholesky(P)z | 原二阶矩忠实保留；没有证据把 P 解释为从历史结果推导的后验 |
| 非高斯形状 | 新草稿只要求已知矩、有限方差与必要的零交叉协方差 | β 基础坐标及每次 ε 均为真实标准化 t5 | 是新草稿的合法实例；不能恢复 Gaussian 条件后验解释 |
| 初始历史观测 | 原 Panel D 未产生或读取历史 Y | stage0 所有观测次数为0，估计均值0 | 对原 Panel D 忠实，对一般 archive 复用任务不完整 |
| 估计权重 | 草稿为线性矩估计器的 a_i | 按 V、x、v 计算，可为负、和不必为1 | 不是论文一般主算法的 simplex 权重 |
| 误差界 | 草稿 W=dᵀPd+Σa_i²v_i，R=√(W/α) | 显式计算两项，并核对 W=tᵀVt | 公式实现正确；不同于原 B_U+噪声的 R∞/R2 |
| 选桥 | 新草稿直接最小化下一步目标区间 | 枚举12个候选的新W并最小化 | 单步精确，不是整个停止预算的全局最优定理 |
| 原预算 | 原 Panel D 从12种候选选4个不同元素 | 从第一步就允许同类型的新独立重复，直到阈值 | 明确任务扩展，不是原4元素子集实验的严格复现 |
| 随机对照 | 原代码随机取4元素子集 | 预先固定一个随机排列并循环 | 第一轮前4个组成均匀随机子集；后续是平衡循环分配，不是每步独立随机抽类型 |
| direct | 原 Panel D 没有这个方法 | 新增 x=t、σ=.5，每次成本1、可重复 | 自然的新增对照；其可行性、噪声和经济成本相同是新协议假设，不是从论文验证得到 |
| 停止 | 草稿允许冻结半径决定停止，并明确覆盖范围 | 首次R≤.30，所有路径提前由设计确定 | 合法设计型终点；不支持全路径同时覆盖或结果驱动可选停止 |
| 机制校准 | 一般ATLAS需要 U、L、H、兼容性、来源噪声等 | 直接给定准确x、P、v，没有U校准 | 不能称为一般ATLAS完整理论流程验证 |

来源：

- [原 01.tex：一般 archive 与机制输入](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/overleaf-paper/causal_lab_proposal_subpapers_tex_iclr2027/01.tex:125)，[一般权重与半径](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/overleaf-paper/causal_lab_proposal_subpapers_tex_iclr2027/01.tex:168)，[理想算法](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/overleaf-paper/causal_lab_proposal_subpapers_tex_iclr2027/01.tex:198)。
- [原 structured repair](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/overleaf-paper/causal_lab_proposal_subpapers_tex_iclr2027/01.tex:675)，[Panel D 的原设置](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/overleaf-paper/causal_lab_proposal_subpapers_tex_iclr2027/01.tex:1231)。
- [原存档生成器](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/current_method/atlas_new/experiments.py:231)。
- [新定理：矩与覆盖范围](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/revision/non_gaussian_bridge/theorem_draft.tex:31)，[矩阵估计器](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/revision/non_gaussian_bridge/theorem_draft.tex:117)，[单步选桥](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/revision/non_gaussian_bridge/theorem_draft.tex:141)，[停止与保证边界](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/revision/non_gaussian_bridge/theorem_draft.tex:185)。
- [当前实现](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/current_method/atlas_new/main_theorem_workflow.py:15)，[冻结协议](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/revision/MAIN_THEOREM_WORKFLOW01.md)。

关于重复观测：可把每次访问写成不同索引 (候选类型, 访问序号)，相同设计向量配新的独立噪声。冻结上限使这些索引仍可放进有限菜单，因此重复类型不违反新草稿的有限观测模型；它改变的是原12元素、无放回、预算4的实验任务。当前代码确实生成了新噪声，没有重复使用旧Y。

## P 是否已经代表历史信息？

只能称为假定已知的初始参数不确定性，不能据现有材料称为“已使用历史数据之后的不确定性”。原生成器先抽随机正交矩阵，再抽范围 [.35,3] 内的特征值构造 P；随后独立生成候选向量与目标。存档只有 prior、design、sigma、target 和设计编号。没有历史研究的 x_H、Y_H、噪声或来源，亦没有历史更新过程。

在 Gaussian 共轭模型中，合法的历史后验均值和协方差可以作为新的初态；但这需要说明如何从历史数据得到它们。去掉 Gaussian 后，矩阵逆更新一般不再等于条件后验协方差。不能把目前随机生成的 P 重新命名成历史后验，也不能只把历史数据压成一个 P 而遗漏非零中心、矩估计的不确定性及条件化论证。

如果后续任务确实要评价历史复用，应单独规定历史观测及其可用信息、初始中心、已经支出的成本如何计算、两类方法是否共享历史信息，并使用与相应保证相符的更新。这是需要确定的任务输入，不是本次审计替作者选择的有利设置。加入历史本身也不保证桥接必然胜过同样可利用历史的 direct。

## direct 为什么大约只需56次？

这不是程序把直接实验的区间计算得更乐观。它使用同一个 P、同一个 α=.05 和同一种 W 界。设 q0=tᵀPt、直接研究方差 v_d=.25，则重复 N 次直接观测目标后：

$$q_{\rm direct}(N)=\left(q_0^{-1}+N/v_d\right)^{-1}.$$

要求完整宽度≤.60等价于 q≤q_req=.05×.30²=.0045。因此

$$N_{\rm direct}=\max\left\{0,\left\lceil v_d\left(q_{req}^{-1}-q_0^{-1}\right)\right\rceil\right\}.$$

原档案 q0 范围为 .4369110042–2.5756430474，由此独立重算得到199个设计需要56次、1个需要55次，与主实验完全一致。direct 每次直接测想要的标量，没有把观测资源分配给不相关参数方向的需要。桥接需要利用候选方向识别同一目标；是否更省取决于候选方向、噪声和真实费用等条件。

这里的“一次研究级效果观测”不是一名参与者，也不是货币。原论文只给桥接研究的 σ=.5；它没有证明 direct 也能以相同经济成本取得相同 σ。把两者设成一致是一个透明的比较任务，不能据此断言现实桥接无价值，也不能反过来无依据地抬高 direct 成本。

## 一般机制流程为何尚未闭合

一般算法的目标是 μ(m*)，源研究机制未知，只给集合 U_i；其点估计是 simplex 组合，误差预算包括支持偏移、曲率、nuisance 与来源噪声，拒绝输出还涉及 Θ_U。当前子模型直接知道线性 x_i 与 t，参数按 P 随机生成，使用可有负系数的线性估计器，剩余参数误差按其二阶矩计入 W。

尤其是 t5 噪声没有原一般主定理要求的 sub-Gaussian 指数矩条件；它由新的有限方差定理覆盖，不能直接套用原 R∞/R2 定理。当前“返回区间并拒绝精度”是 W 证书语义，也不是计算了原一般 sharp partial-identification region。

因此适当名称是“原存档设计上的非高斯结构化选桥流程”。它可以支撑关于非高斯矩界、实际选桥、更新和设计型停止的限定结论；不能自动回答真实机制集合校准、一般非线性 μ、历史复用省钱或真实应用完整闭环。

## 全局成本下界：独立证明

固定当前12种桥接候选、P≻0、已知v_k>0。允许任意非负连续分配 n_k（因此也覆盖所有非负整数分配），令

$$A(n)=P^{-1}+\sum_k n_k x_kx_k^\top/v_k,\qquad q(n)=t^\top A(n)^{-1}t,\qquad N=\sum_k n_k.$$

取任意非零向量 z，记

$$D(z)=\max_k (x_k^\top z)^2/v_k.$$

由 A 内积下的 Cauchy–Schwarz：

$$ (t^\top z)^2\le(t^\top A^{-1}t)(z^\top Az). $$

若该分配满足 q(n)≤q_req，则

$$\frac{(t^\top z)^2}{q_{req}}\le z^\top P^{-1}z+\sum_k n_k\frac{(x_k^\top z)^2}{v_k}\le z^\top P^{-1}z+ND(z).$$

当 D(z)>0，任何可行分配都必须满足

$$N\ge L(z):=\max\left\{0,\frac{(t^\top z)^2/q_{req}-z^\top P^{-1}z}{D(z)}\right\}.$$

这个结论对任意 z 都成立，所以数值优化器是否成功退出不影响某个已经给出的 z 的下界资格。无需声称已经找到全局最优 z 或依赖优化器的“成功”标签。D=0 时需另行处理：分子为正意味着沿该方向无有限可行成本；分子非正不提供正下界。

对整数成本，L>N_direct−1 足以排除严格省钱；L>N_direct 则足以证明严格更贵。必须审计不等式的边界余量，不能直接对有浮点误差的 L 做 ceil 就宣称形式化证书。

该结论属于当前 q/W 证书与候选模型。因 q 是给定分配下线性最小均方误差，对任意线性权重使用同一二阶矩证书的达标也给出必要条件。它不排除利用完整 t5 分布的其他区间、非线性估计器、新的候选、不同费用或一般机制模型；也不构成对所有统计方法的下界。

## 独立数值核对

对实现代理输出的全部200个 z、连续分配和整数分配，从未修改的原档案重新计算 P^{-1}、D、L、q 与成本。连续与整数分配均非负，整数分配各坐标为整数，全部满足 q≤.0045。没有生成任何效果观测。

| 核对项 | 结果 |
| --- | --- |
| 独立 L 与保存 L 的最大差 | 0（当前双精度计算） |
| 整数可行 q 的最大重算差 | 1.56×10^-17 |
| 连续 q 的最大重算差 | 2.86×10^-17 |
| 扣除 10^-6·max(1,L) 后，L仍大于direct成本 | 198/200 |
| 其中最小正余量 | 2.14017549（design48；保守下界58.14017549，direct56） |
| 两个更便宜的整数可行分配 | design2：55；design62：46；各自direct均56 |
| 独立重算用时 | 0.0453秒，CPU矩阵核算 |

实现代理报告的连续可行上界与解析下界间最大绝对间隙约0.00053744，相对间隙最大6.56×10^-7；greedy成本/下界的中位数约1.00435、最大约1.05063。这些是现有设计下 greedy 已接近全局成本极限的证据。即使不用这些接近性数字，198个解析下界与direct之间的正余量已经排除了“只换一个全局规划器即可普遍省钱”的解释。

数值证据使用float64并向下扣除安全余量，不是区间算术或Lean验证的机器严格证书。最接近direct者仍有2.14次观测的余量，因此当前比较不依赖接近整数边界的舍入。这里的下界在更宽松的 q_req=.0045 门槛下都已高于direct；要求桥接与direct实际终点同样窄只会收紧条件，不能逆转这198例的判定。

原证书：[allocation_certificates.json](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/work/main_optimality_audit/full200/allocation_certificates.json)；独立重算：[independent_recomputed_certificates.csv](C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/work/main_optimality_audit/full200/independent_recomputed_certificates.csv)。

## 对后续决策的含义

1. 目前没有依据为了结果好看修改候选幅度、direct费用或阈值。原结果应保留，并按受限结构化模型解释。
2. 若论文主张只是“在给定桥接菜单中更有效地选实验”，新规则相对logdet/random的结果有直接对应的证据。
3. 若论文主张是“利用历史研究，在相同目标精度下比重新直接实验更省”，应先把历史信息、目标实验可行性和实际成本来源定义清楚。当前实验没有充分实例化这个任务，不能仅通过增加采样量补上。
4. 若继续检验一般机制校准与运输主算法，需要保留 U、L、H、来源效果及其保证的接口，说明桥接子模型怎样接入。不能把本次已知矩的线性流程换名当成全模型验证。

本审计不替作者决定新的科学任务，不建议挑选能够让桥接获胜的参数。它区分了公式实现正确、结构化模型内的负结果、以及尚未被实验覆盖的论文任务。
