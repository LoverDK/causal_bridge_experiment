# 全部可纳入 family 的敏感性协议

日期：2026-09-25。该敏感性实验不修改已经发布的五-family baseline panel。

## 目的

上一套 panel 固定留出五个有两个 study 的 family，以便观察 family-level calibration。这个选择可能让读者担心 target 选择影响结论。因此本实验在同一输入和 eligibility rule 下，把 23 个可纳入 family、28 个有效 study-level Cohen's d 全部逐 family 留出。

## 固定规则

- 输入和 SHA-256 与前两套 Many Labs 2 实验相同。
- 目标 family 是通过 `finite ESCI.d`, `positive ESCI.var.d`, `N > 1` 后剩余的全部 23 个 family，不再根据 study 数量或结果选择。
- 每次留出一个完整 family，该 family 的所有 study 不进训练池；目标效应只用于最终评分。
- 使用同一五种 baseline 和相同的半径阈值 `0.20, 0.40, 0.60, 0.80, 1.00`；study-level conformal 按唯一 `study.analysis` 留一，family-level conformal 按 `family` 留一。

## 额外审计

逐 family 翻转 held-out `ESCI.d`，预测和半径必须保持不变。另对 study-level 与 family-level conformal 的校准分数进行解释：当前数据中 95% order statistic 经常落在最大残差，因此两个规则相同不等于两个设计完全等价；这反映的是 23 个 family、训练 family 数量和小样本 quantile 的限制。

## 解释边界

该敏感性分析提高 target family 的覆盖面，仍然是 noisy study-level 外部有效性压力测试，不提供现实机制集合 `U_i`、独立 calibration archive 或无噪声 causal truth。下一步仍是预注册/新采集跨干预资料，并在目标结果揭盲前冻结机制代理和 calibration split。
