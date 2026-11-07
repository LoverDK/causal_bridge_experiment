# 目标区间选桥：非高斯定理与验证范围

本轮目标是直接缩短指定目标的有效区间。原文 logdet 是另一种设计目标；它的经典近似因子不能转称为目标区间的近似因子。原稿和旧实验没有被覆盖修改。

## 已完成的主概率定理

保留原文的线性模型及随机参数解释：`Y_i = x_iᵀ β + ε_i`、目标 `θ = tᵀ β`。参数均值为零，真实协方差 K 已知；参数各坐标可以相关。噪声中心化、平方可积、两两独立，方差有已知上界 v_i；参数与噪声的交叉协方差为零。原文的相互独立条件足以满足这些前提。参数和噪声都不必高斯，也不必有次高斯尾部。

对于在看到评估结果之前固定的权重 a，设

\[
d=\sum_i a_i x_i-t,\qquad
W_a=d^\top Kd+\sum_i a_i^2v_i,\qquad R_a=\sqrt{W_a/\alpha}.
\]

Lean 已验证实际观测形成的估计量满足

\[
\Pr\left(\left|\sum_i a_iY_i-t^\top\beta\right|>R_a\right)\le\alpha.
\]

概率同时对参数和噪声取平均；它不是给定每个固定 β 的保证，也不是给定观测后的后验概率。K 和 v 必须有效，不能把同一数据估出的量直接代入后仍宣称该保证成立。

## 直接选最短目标区间

对每个候选下一步实验，提前给出其采集方案、估计权重和上式半径，在非空有限候选菜单内选择最小半径。`exists_best_moment_bridge` 已验证：这样的选择存在，其半径不大于菜单内任何比较方案，并且所选估计量仍满足上述实际误差概率保证。半径乘以二就是返回区间的长度。

这可以用于一个候选实验的比较，也可以用于全部预算可行实验组合的枚举。前者只有下一步最优性；后者才是在所枚举完整方案内最优。它不证明逐步贪心能达到多步全局最优，也不证明桥接一定比直接目标实验便宜。直接目标实验可以成为同一菜单中的候选。

Lean 中有限实数菜单的选择使用数学上的 `Classical.choose`，没有提取可执行优化器。半径由已知输入计算；实际程序仍须核对公式、数值比较和采样实现。对于有理输入，可以使用代数数比较或有误差证书的保守上界。

在原矩阵线性估计器下，纸面推导给出

\[
q_S=t^\top V_St,\quad R_S=\sqrt{q_S/\alpha},\quad
q_S-q_{S\cup\{b\}}=
\frac{(t^\top V_Sx_b)^2}{\sigma_b^2+x_b^\top V_Sx_b}.
\]

所以在同一步、相同失败概率和同一可行菜单中，最大化右侧得分等价于最小化更新后的目标区间。这是目标方向的得分，不是 logdet 得分。`NonGaussianTargetUpdate.lean` 已证明实际 rank-one inverse 更新、目标二次型减少量及有限菜单实际下一步半宽最优；它以旧逆矩阵关系、对称性和分母非零为前提，没有把更新公式当成假设。它还没有与具体正定设计构造、W=q 及概率界全部连成一条矩阵概率定理。

## 实际形式化范围

| 结论 | 状态及限制 |
| --- | --- |
| 实际 `Y` 到估计误差的代数分解 | 已验证 |
| 完整协方差二次型、交叉项、加权噪声方差 | 已验证；未假设参数坐标独立 |
| 正方差和零方差下的概率保证 | 已验证；没有把所需尾界当作假设 |
| 零均值随机参数的 W 形式定理 | 已验证，`moment_prior_bridge_coverage` |
| 有限菜单最小目标半径及其覆盖 | 已验证，`exists_best_moment_bridge` |
| 固定参数的 box 偏差界及覆盖 | 已验证，独立替代模型 |
| 精确目标匹配、无需参数上界的覆盖 | 已验证，独立替代模型 |
| Euclidean 偏差界 | 已验证辅助引理；不等于整条 ridge 推论 |
| 正定 V0、半正定 G 的逆矩阵 sandwich 恒等式 | 已验证；具体采集系数到 W=q 的完整连接尚未验证 |
| 实际 rank-one inverse 更新、目标二次型减少公式 | 已验证；前提为旧矩阵确为逆、对称性及分母非零 |
| 有限候选的实际下一步矩阵目标半宽最小 | 已验证，`exists_best_target_next`；不含多步全局最优 |
| 一般贪心 gap 递推到有限预算因子 | 已验证辅助引理；没有据此声称目标半径次模 |
| 非零先验均值、协方差上界、全路径联合事件与停止 | 有纸面说明，未完整形式化 |
| 实际 matrix logdet 次模性、谱界 | 有纸面证明，未完整形式化；不是当前主选桥目标 |

主定理及有限选择的实现在 [NonGaussianBridge.lean](../../LeanProofs/NonGaussianBridge.lean)。代码变量 `δ` 是失败概率，对应本文 α；不是科学误差阈值。

## 可重复核验

实际使用 Lean **4.34.0-rc1**；Mathlib commit **de5ce8a9a66a4aa68a9bdbb35b63a06d34d9ca11**。核验脚本先把缓存的 Git HEAD 与锁文件比较，再按依赖顺序构建模块，使用 `--error=warning`。源文件 SHA256、各模块退出状态和公理输出见 [JSON 记录](lean_verification.json) 与 [逐项输出](lean_verification.txt)。

已审计命题只依赖标准公理 `propext`、`Classical.choice`、`Quot.sound`。没有 `sorry`、`admit` 或新增公理。标准公理不是跳过本项目证明的占位符。

本机复核命令（从工作区根目录执行）：

```powershell
.\outputs\experiment-rebuild\LeanProofs\verify_non_gaussian.ps1 `
  -LeanBinary 'C:\Users\Qiutian\.elan\toolchains\leanprover--lean4---v4.34.0-rc1\bin\lean.exe' `
  -MathlibProject 'D:\study\zzh科研\output\causal_bridge_experiment_publish\LeanProofs'
```

脚本只读取已有依赖，构建产物写入本仓库 `.lake/non_gaussian`。使用新的标准 Lean 环境时，可按仓库锁文件取得依赖后运行 `lake build`；本轮实际执行的是上述固定缓存脚本。

理论直接推进 **KoBT.W4 / REV-10** 中的 Gaussian 限制，并使选桥目标明确。它没有消除线性模型、已知设计与有效二阶矩输入等限制，也不能代替非高斯实验、现实案例或贡献新颖性论证。标准方差不等式、有限枚举和经典次模结论不作为本论文的新基础定理。
