# 机制集合不确定性消融：运行前冻结协议

实验标识：`MECHANISM-UNCERTAINTY-ABLATION01`。日期：2026-11-07。参数以同名JSON为机器可读版本。本轮已获用户授权，但尚无运行结果；不以生成正面结果为验收条件。

## 要回答的问题与方法身份

保留机制集合的不确定性，会如何改变区间、真实误差、覆盖和发布成本？把代理坐标直接当真会付出什么可靠性代价？如果机制位置真的已知，可以省去多少不确定性？这些是本轮的三个相连问题。

本轮使用已有一般 **U/L/H、simplex权重、min(Bbar,BLip)计算证书**流程，源码为 `current_method/atlas_new/workflow.py`。这是机制不确定性组件的消融，不是刚完成的线性known-moment新选桥定理实验，也不是legacy prototype。候选桥的次序固定随机，不测试定向选桥或logdet。

主要对应 **KoBT.W1、WGDN.W2a** 中机制集合的作用与遗漏风险，以及 **nrhq.Q1/Q2** 对模块作用与可比较结果的要求。合成标签下的这一比较不能解决真实U的来源，不能把解析L/H变成真实世界认证。REV-04保持open。

## 数据、种子与规模

原 `configs/workflow_full.json` 的DGP不变：linear、quadratic、sinusoidal三函数，supported、bridgeable、unreachable三菜单；二维机制；4个历史来源，每来源800人；6个候选桥；最多新增3桥，每桥96人；候选不重复；199份独立合成校准archives；proxy_scale=.012；eta=zeta=.05。

机制真位置按原菜单加N(0,.025²)抖动并裁到[-1,1]²；目标位置固定。校准分数是每份archive内全部11实体（4历史、6未来候选、1目标）的二维Gaussian代理误差范数最大值，用原秩分位数得到共同球半径。机制集合可理解为该球与声明机制域的交集；代码的三角不等式距离表达是覆盖这些集合的计算上界，不声称求解精确最坏机制配置。

每次RCT仍为两臂各n/2人、单位噪声sd=.5，处理均值为该位置的真实响应，控制均值0；ATE标准差为1/sqrt(n)，无nuisance bias。L/H固定为原函数的解析值，不扫描平滑度、误差尺度或额外压力网格。

- smoke：每函数×菜单3世界，共27；seed **2026110751**。
- full：每格200世界，共1800；seed **2026110752**。
- bootstrap：full2000次，smoke100次；seed **2026110753**。
- 预设讲解例：linear / bridgeable / replicate0，不按结果更换。

新seed与已看过的旧1800世界独立；DGP并未变成新的现实分布。每个world是实验单位，方法、预算和阈值重复不是新样本。

## 三个输入版本

| variant | 中心 | 集合半径 | 身份与保证 |
|---|---|---|---|
| calibrated_U | 原proxy | 原共同校准半径 | 已声明合成联合校准条件下的主方法 |
| proxy_point | 完全相同proxy | 全部为0 | 把测量代理当真实位置的负控制；没有机制集合覆盖保证 |
| oracle_true_point | 真实来源和目标机制位置 | 全部为0 | 额外机制位置信息的oracle参照；不是可实施方法，不接触真实效果用于拟合 |

三版本共享同一校准archive、source trial noise、实际观察到的source ATE、L/H、样本量、统计乘子、阈值和每一步来源前缀。oracle只被允许知道机制位置；真响应和目标效应只供评分，不输入优化器。不能把它的权重拿回主方法当初始值。

分别记录 `guarantee_applicable` 与 `mechanism_event_holds`：前者是前提是否有校准论证，后者是模拟评分时这一次真位置是否在集合中。calibrated_U偶遇覆盖事件失败并不等于代码假设声明失效；proxy_point偶尔经验表现很好也不建立保证。

## 固定随机采集与权重拟合

唯一schedule为random：`default_rng(SeedSequence([seed,surface_id,scenario_id,replicate,20])).permutation(arange(4,10))`。三个版本、两种证书采用同一前3候选和相同数据前缀；不加nearest或定向选桥。这样隔离的是机制输入对权重和证书的作用，不是选择了不同数据的收益。

每个版本、mode、stage使用原 `workflow.optimize`：设计型多起点SLSQP、uniform/顶点和自身上一阶段权重补零作可行fallback。不得声称全局最优，也不跨版本共享优化权重。局部求解器可能让重新优化后的排序偏离全局最优的理想排序；保留并诊断，不据此修改数据或阈值。

主mode为 **R2**，Rinf是预先冻结secondary。所有权重与顺序都不读取评估结果，因此本轮不证明Rinf的结果适应选择收益。

## 置信预算和区间对象

沿用原有限时域统计分配：4个时点（stage0..3）和全部10个source。

- R2证书噪声为 `sqrt(2 log(2*4/(zeta/2))) * ||a*s||2`；拒绝外区间使用 `sqrt(2 log(2*10/(zeta/2)))` 的共同逐源事件。
- Rinf证书和拒绝使用 `sqrt(2 log(2*10/zeta))` 的逐源共同事件；证书噪声为该乘子乘 `sum(a*s)`。
- calibrated_U的完整输出路径保证至少 `.90=1−eta−zeta`。oracle位置准确，使用相同噪声分配时至少`.95=1−zeta`；不把省去的eta重新分配来进一步缩窄oracle。
- proxy_point的名义保证为缺失值，不标95%或90%覆盖。各组经验覆盖均按相同真实θ计算并报告。

这是每个policy自己的有限路径保证，不是所有方法同时覆盖，也不是条件于发布的95%/90%保证。R2/Rinf旧分配不同，不能只根据名字把它们当同一统计乘子的范数消融。

固定预算的主对象为**证书区间** `[estimate−radius, estimate+radius]`，全宽为2radius。stopped流程若未发布，则返回variant-specific的**outer refusal envelope**；它可能不以加权估计为中心，也不是一般U下的sharp PI集合。两类宽度和覆盖分栏。空/不一致不记为零宽成功，无界不删除。

## 主比较、分解与停止

主预算为stage3，即 **288新增人**；0/96/192/288全报。主表是R2、所有9格，以及每菜单按函数等权的600世界汇总。首先报告每组证书宽度、相对自身stage0的缩短、全目标真实MAE/MSE、证书覆盖及几何/噪声分解，再做world配对的calibrated−proxy和calibrated−oracle对照。

必须有两个视角：

1. **各自重新优化**：输入变化可能同时改变权重和几何证书，反映整体组件删除后的结果。
2. **同权重诊断**：固定calibrated_U在每个mode/stage实际选出的权重，使用完全相同ATE，分别计算三输入版本的几何和证书。此时估计、统计噪声项相同，变化只来自机制几何。

同权重分解至少保存：

- Bbar中心重心错位；`L*(r_target+sum(a*r_i))`直接集合项。
- Bbar中心位置曲率；集合半径扩大pair distance造成的**额外曲率项**。不能只记直接集合项而漏掉集合影响曲率。
- BLip中心距离、集合项、总BLip；Bbar总量；两者最小值与active branch；噪声、总radius。

确定性核对：同权重calibrated几何≥proxy-point几何应总成立；calibrated几何≥oracle几何只在joint set covered事件上要求。没有必要要求proxy_point在经验上一定欠覆盖；其它项的保守性可能掩盖省略的集合误差。

主fixed-budget视图真正采集共同前缀直到stage3，即使较早达到旧阈值仍继续；无需按两个阈值复制这些固定预算结果。另执行独立标记的stopped视图，沿用半径阈值 **.2/.3**，首次发布即停止或预算耗尽，记录真实采集成本、发布/拒绝输出和无条件bad release。stopped轨迹后续carry不是同预算全量采集。

零发布组的条件误差为NA，不填0。不只挑发布者比较点误差，不将较窄但未证明可靠的negative-control区间称为优势。

## 实现和独立审核要求

源码新增于独立模块，旧workflow及所有旧输出只读。结果使用新目录 `reproduced/mechanism_uncertainty_ablation01/{smoke,full}`，报告使用 `revision/results/mechanism_uncertainty_ablation01`，存在的目录不覆盖。run manifest记录协议、旧复用源码、新模块/runner/tests、依赖、Git状态、seeds、运行命令和实际耗时的哈希/版本。

需要验证：三输入版本的设计/观察配对；全半径分解与aᵀobserved-effect重算；oracle真坐标访问隔离；planner不接收outcomes；variant-specific refusal design而非误回用world.design；same-weight不等式及条件；预算计数；停止后未消费后续样本；空区间与NA分母；所有记录数、三函数三菜单完整。保留一个全来源输入—权重—界—区间—停止的预设world trace。

world内严格配对，以world为bootstrap单位、按函数/菜单分层。CI是探索性individual intervals，不作familywise superiority声明；不因负控制未失败或oracle收益小而重跑换seed、加错设网格、改阈值。

## 运行前全部12项review回顾

已读取 `REVIEW_TRACKER.md`、`review_tracker.json` 的全12项及完整review映射，并回看 `FIRST_WORKFLOW.md`。此处记录before范围，不修改tracker状态；根代理统一维护tracker。

| 问题 | 原状态 | 本轮能推进/不能解决 |
|---|---|---|
| REV-01 | partial_evidence | 单world解释集合与各误差项；不完成写作验收 |
| REV-02 | partial_evidence | 明确设计权重与R2/Rinf身份；不测试结果适应任务或sample splitting |
| REV-03 | partial_evidence | 新数字逐项绑定实现/输入/输出；不自动替换摘要 |
| REV-04 | open | KoBT.W1/WGDN.W2a的合成机制不确定性组件作用；不提供真实U来源，不认证真实L/H |
| REV-05 | open | 不运行真实数据，不改变microcredit资格失败 |
| REV-06 | partial_evidence | 不处理Many Labs目标噪声或跨family问题 |
| REV-07 | partial_evidence | nrhq.Q2的匹配组件、成本/精度对照；不是ExAtlas或direct superiority |
| REV-08 | open | 不解决I&K/Manski/ExAtlas贡献归属或新颖性 |
| REV-09 | open | 保留simplex，不证明它优于所有估计器 |
| REV-10 | partial_evidence | random固定路径；不验证新的moment或旧logdet选桥定理 |
| REV-11 | open | 明确general U/L/H、negative control、oracle身份；不完成全稿命名修改 |
| REV-12 | partial_evidence | 区分fixed/stopped、证书/outer、错误发布、空集合及分母；不提供真实案例 |

smoke后、full后继续回顾全部12项。运行成功只说明执行完成；结论由保存结果支持，不自动resolved。

## 耗时预估及执行门槛

根代理已向用户预告：smoke27世界 **10–30秒**，full1800世界 **3–8分钟**，4个CPU进程，SciPy SLSQP是主要瓶颈，不需要GPU。依据为同机旧cost-precision smoke8.483秒/full429.622秒；本轮每world24次optimize，省去目标候选枚举。历史ablations_full133.806秒来自另一历史环境，只作辅助参考。测试、报告和独立审核耗时另记。

本协议提交后实现代理可写/运行针对性tests及smoke。**full的放行条件**：smoke检查通过、报告代理独立核查、实现代理用实测更新full估计、根代理已将更新告知用户。用户已授权本轮，无需再次请批；这个门槛是保证冻结设计和准确告知运行成本，而非新增审批。若发现真实实现错误，修正并保留版本/日志后复核；不得通过改数据生成或科学阈值获取好结果。
