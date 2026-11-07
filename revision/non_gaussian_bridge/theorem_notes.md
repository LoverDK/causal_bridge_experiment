# 直接选择让目标区间最短的桥

主目标已改为：**在给定可行候选中，让指定目标的下一步认证区间最短。**logdet 只保留为历史代理对照，移到英文稿附录，不再作为主选桥规则。配套文件 theorem_draft.tex 给出完整纸面证明；未修改 Overleaf。

先固定同一个失败概率 $\alpha$。对每个可行候选 $b$，计算加入它并更新估计权重后的半径，再选

$$
b^*\in\arg\min_b R(S\cup\{b\},\alpha).
$$

区间总长度是 $2R$，所以这就直接最大化下一步区间的缩短量。候选菜单、权重规则、机制设计和矩信息都必须预先确定，不利用本轮效果观测。

对保留的矩阵估计器，令

$$
V_S=\left(V_0^{-1}+\sum_{i\in S}x_ix_i^\top/\sigma_i^2\right)^{-1},
\qquad q_S=t^\top V_St.
$$

其认证半径为 $R(S,\alpha)=\sqrt{q_S/\alpha}$。Sherman–Morrison 公式给出

$$
q_{S\cup\{b\}}=q_S-
\underbrace{\frac{(t^\top V_Sx_b)^2}
{\sigma_b^2+x_b^\top V_Sx_b}}_{H(b\mid S)}.
$$

因此，**最大化 $H(b\mid S)$ 与最小化下一步目标区间长度完全等价**。公式显式使用目标方向 $t$；无须绕经 logdet 或条件数界。英文稿通过矩阵相乘验证逆更新，再推出上述恒等式，包括分母为正及更新后半径非负。

这只保证**一步最优**。反复选当前最好的一步，不能据此声称整个 $B$ 步预算后仍全局最优。若候选数较小，可枚举所有 $|T|\le B$ 的可行集合，直接最小化 $R(S\cup T,\alpha)$，从而获得声明的有限设计族内的全局最优。成本不同时，用真实成本约束筛选菜单；“得分除以成本”没有由此得到相同最优性保证。达到指定精度的最低成本，也可在有限菜单中另行枚举。

区间的统计依据仍是**线性、已知矩信息、有限方差**模型。随机参数 $\beta$ 有已知均值 $m_0$、完整协方差 $V_0$；噪声中心化、独立，并与参数独立，有已知方差上界。参数坐标允许相关。任取预先固定的线性权重，定义

$$
d=\sum_i a_ix_i-t,\qquad
W=d^\top V_0d+\sum_i a_i^2v_i,\qquad R=\sqrt{W/\alpha}.
$$

这个 $W$ 形式无须矩阵求逆恒等式即可证明覆盖率，不需要已知参数范数。概率针对参数与噪声的联合分布，不能说成给定观测后的后验概率，也不是针对每个固定真实参数的统一保证。非线性、未知设计位置或未经证明的矩信息估计，不在本次结论内。

**Lean 已验证的核心**是原文 $m_0=0$ 模型下的实际观测误差概率界，以及非空有限系数菜单确有最小半径成员且该成员具有覆盖保证。原模块审计采用警告即错误，并检查了标准公理依赖。

新增目标更新模块也已通过：它实际证明逆矩阵更新，再推出 $q_{\rm new}=q-H$，最后证明有限候选中存在下一步矩阵半宽最小者。其明确假设是 $AV=I$、$V$ 对称、$r\ne0$、$r+x^\top Vx\ne0$，以及共同 $\alpha>0$。它不是只假定 $q-H$ 公式后做大小比较。

仍需区分：从具体正定设计推出这些假设、候选到权重的映射、完整 $W=q$ 连接及概率覆盖，尚未合成一个完整的矩阵选桥定理。新增模块自身不证明二次型非负或覆盖率；数学正文用正定设计条件保证这些性质。不能把分模块验证写成整条矩阵应用均已完成。详见 [验证范围](README.md) 与 [已有审计](lean_verification.json)。

$\alpha$ 是失败概率，$\delta_{\mathrm{sci}}$ 是要求的误差精度。半径不超过后者才发布认证的点估计，否则返回区间并拒绝认证该精度。全路径覆盖需预先分配各步 $\alpha_t$，总和不超过 $\alpha$；每一步比较候选仍须使用相同的 $\alpha_t$。固定参数 ridge 和精确目标匹配作为不同模型的备选留在附录。

这里证明的是有限菜单内的认证区间优化；它不证明普遍低于直接目标采样的成本，也不把经典二阶矩方法或逆矩阵公式作为新颖性贡献。

## 已核实的引用与 BibTeX

以下两条分别支持基本概率不等式和历史 logdet 对照所用的经典贪心因子。新目标得分的逆更新在稿中直接证明，不依赖外部定理的省略推导。元数据及引用范围已独立核查：[Duchi 讲义](https://web.stanford.edu/class/stats311/lecture-notes.pdf)、[Nemhauser 等原论文](https://doi.org/10.1007/BF01588971)。

```bibtex
@misc{duchi2023notes,
  author       = {Duchi, John},
  title        = {Lecture Notes on Statistics and Information Theory},
  year         = {2023},
  month        = dec,
  howpublished = {Stanford University lecture notes},
  note         = {Version dated December 6, 2023; Section 4.1},
  url          = {https://web.stanford.edu/class/stats311/lecture-notes.pdf}
}

@article{nemhauser1978analysis,
  author  = {Nemhauser, G. L. and Wolsey, L. A. and Fisher, M. L.},
  title   = {An Analysis of Approximations for Maximizing
             Submodular Set Functions---{I}},
  journal = {Mathematical Programming},
  volume  = {14},
  pages   = {265--294},
  year    = {1978},
  doi     = {10.1007/BF01588971},
  url     = {https://doi.org/10.1007/BF01588971}
}
```
