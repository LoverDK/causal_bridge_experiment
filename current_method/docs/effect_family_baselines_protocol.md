# 跨 effect family baseline panel 协议

日期：2026-09-25。该协议与目标效应揭盲前固定，复用 `effect_family_holdout` 的输入、五个完整目标 family 和十个 target study。

## 目的

上一套真实数据实验已验证跨 effect family 的目标盲留出、拒绝和泄漏控制，但 baseline 名称与原评价中的四类比较对象没有逐项对应。本实验在完全相同的留出和阈值下运行以下显式方法：transportability、hierarchical meta-analysis、robust partial-identification、conformal/selective prediction。

## 方法

1. `transport_meta_regression`：用 study-level Cohen's d 的逆方差拟合 WEIRD/NONWEIRD 上下文加权 meta-regression；目标上下文来自原始 study metadata，预测半径加入系数不确定性、异质性和仅由目标 `N` 得到的 sampling allowance。
2. `hierarchical_meta_analysis`：Normal-Normal random-effects 层级模型，DerSimonian--Laird 估计 between-study heterogeneity，输出 t 型 predictive radius。
3. `robust_partial_identification`：训练池 effect envelope 外扩 `1.96 * sqrt(4/N_target)`，作为保守部分识别区间；它不使用目标效应。
4. `study_split_conformal`：在训练池内按 study 留一，校准绝对残差，再加目标 N-only allowance。
5. `family_split_conformal`：在训练池内按完整 family 留一，校准 family-level 残差；这是比 study-level 更严格的跨 family selective baseline。

每个方法在半径阈值 `0.20, 0.40, 0.60, 0.80, 1.00` 下记录 release/refusal、all-target coverage、released-target coverage、MAE、sign error 和 interval width。目标 `ESCI.d` 只用于最后评分；目标 `ESCI.var.d` 只用于固定的 eligibility 检查。

## 审计与边界

逐目标 family 翻转 held-out `ESCI.d` 后重新运行，预测和 radius 必须不变。该面板提供了原评价要求的 baseline 对照和真实跨 family 压力测试，但不提供真实 `U_i`、独立现实 calibration archive 或无噪声 causal truth。十个 target 也不足以作稳定方法排名。下一步仍是预注册/新采集跨干预档案，并在 target outcome 揭盲前冻结机制代理和独立校准分割。
