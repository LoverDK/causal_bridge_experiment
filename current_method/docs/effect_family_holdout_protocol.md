# Many Labs 2 跨 effect family 留出协议

日期：2026-09-25。该协议在读取目标效应评分前固定。

## 目的与边界

这套实验使用 Many Labs 2 官方仓库发布的 study-level `ML2_OriginalEffects.csv`，检验在不同心理学 effect family 之间迁移时，预测区间、拒绝规则和几个基线的行为。它是现实数据的跨 effect family 外部有效性压力测试，不是现实机制集合校准：该公开汇总没有 `U_i`、`L`、`H` 的独立审计标签，也没有无噪声的目标因果真值。

## 输入与固定留出

- 上游仓库：`ManyLabsOpenScience/ManyLabs2`，commit `acef63fc397b8dce7f0b00f863bcea78d324bea8`。
- 输入：`OSFdata/!!RawData/ML2_OriginalEffects.csv`，SHA-256 `78b3432bebb798595ebb08ee10fb68d3f6f59cd5e0ab49606cfb6835eb226406`。
- 只纳入 `ESCI.d` 非缺失、`ESCI.var.d > 0` 且 `N > 1` 的记录；固定纳入规则后，共 32 条中的 28 条有效记录。
- 目标 family 固定为 `Hauser`、`Huang`、`Miyamoto`、`Ross`、`Savani`，共 10 个 study-level targets。每次留出一个完整 family；该 family 的所有 study 不进入训练池。
- 目标参考 `ESCI.d` 只在最后评分读取。目标 `N` 与 `study.analysis.ori` 中的 WEIRD/NONWEIRD 标签属于预先可见的设计/元数据。

## 预测方法与阈值

1. `fixed_effects`：训练 study 的逆方差固定效应。
2. `random_effects`：DerSimonian--Laird 随机效应及 t 型预测半径。
3. `context_fixed_effects`：同一 WEIRD/NONWEIRD 元数据上下文至少有 3 条训练记录时做固定效应，否则回退到全训练池。
4. `robust_training_range`：训练效应的最小--最大范围，外扩 `1.96 * sqrt(4/N_target)`；这是保守范围基线，不是因果证书。
5. `family_split_conformal`：训练池内部按完整 family 留一，基于 family 均值残差的 95% split-conformal 半径，再加目标 N-only 采样 allowance。

所有方法的预设释放半径阈值为 `0.20, 0.40, 0.60, 0.80, 1.00`（Cohen's d 单位）。记录全体与已释放目标的 coverage、release/refusal rate、interval width、绝对误差和 sign error。held-out `ESCI.d` 是有噪声的评分参考，不应解释为真实因果参数覆盖率。

## 泄漏审计与产物

将所有目标 family 的 `ESCI.d` 翻转后重新运行，预测和半径必须保持不变；否则运行失败。结果目录保存 predictions、summary、included/excluded studies、leakage audit、report 和带输入/源码哈希的 manifest。

## 完成后的判断

本实验满足“真实跨 effect family 外部有效性、目标盲预测、拒绝率/宽度/误差/符号错误和多基线”的补充证据要求。它仍不满足最强要求中的现实 `U_i` 构造、独立现实校准档案、跨干预机制标签和真实因果真值。下一步应在预注册或新采集的跨干预档案中，从 study design metadata 冻结机制代理和校准划分，再复用本协议的 family holdout 与 baseline 面板。
