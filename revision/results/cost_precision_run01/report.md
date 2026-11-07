# 成本与精度共同评价：新独立模拟结果

模拟种子 `2026110702`；1800 个独立世界；每单元 200 世界。分析重采样种子 `2026110799`。

本报告比较完整采集前缀；原首次发布停止策略单独保存在 summary.csv 的 mode=stopped。每个世界的方法、阈值和预算重复行不算独立样本。

## 阅读规则

- 成本是实际新增参与者，不含历史档案、校准、审计和部署成本。静态档案一直是零成本参照。
- 精度为实际返回区间半宽，包含拒绝后的外区间；它不一定是原加权点估计的误差半径。
- release_tolerance 决定返回发布区间还是拒绝外区间；precision_target 决定首次达标任务。本轮两者数值相同，但属于不同概念；两个阈值对应两种输出规则。
- 窄区间必须与覆盖一起解读。无界半宽保留 infinity；不一致区间不记为零宽，相关总体均值记 undefined。finite 条件统计仅作明确标注的辅助项。
- certificate 达标沿用原点发布标准；returned_interval 达标按有限非空区间半宽，是另一项预声明任务。区间中点误差只作为该任务诊断，不能改写为原估计器表现。
- 达标成本为首次命中；未达标者保留且标为右删失。平均实际支出包括失败者；mean_hit_cost_given_attained 仅为条件诊断，不可单独比较成本。
- 方法差异使用世界配对、曲面内分层 bootstrap 的点态 95% 区间，未作全家族多重校正；避免据多个有利区间声称普遍优越。

## 全场景最终前缀精度与可靠性

| scenario | method | tolerance | mean_actual_cost | mean_halfwidth | path_covered | path_covered_lower | released |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bridgeable | r2_nearest | 0.2000 | 288.0000 | 0.3035 | 1.0000 | 0.9936 | 0.0000 |
| bridgeable | r2_nearest | 0.3000 | 288.0000 | 0.2526 | 1.0000 | 0.9936 | 1.0000 |
| bridgeable | r2_random | 0.2000 | 288.0000 | 0.2666 | 1.0000 | 0.9936 | 0.3867 |
| bridgeable | r2_random | 0.3000 | 288.0000 | 0.2110 | 1.0000 | 0.9936 | 1.0000 |
| bridgeable | r2_static | 0.2000 | 0.0000 | 0.5583 | 1.0000 | 0.9936 | 0.0000 |
| bridgeable | r2_static | 0.3000 | 0.0000 | 0.5583 | 1.0000 | 0.9936 | 0.0000 |
| bridgeable | r2_targeted | 0.2000 | 288.0000 | 0.2071 | 1.0000 | 0.9936 | 0.6667 |
| bridgeable | r2_targeted | 0.3000 | 288.0000 | 0.1929 | 1.0000 | 0.9936 | 1.0000 |
| bridgeable | rinf_targeted | 0.2000 | 288.0000 | 0.2973 | 1.0000 | 0.9936 | 0.0000 |
| bridgeable | rinf_targeted | 0.3000 | 288.0000 | 0.3003 | 1.0000 | 0.9936 | 0.3450 |
| bridgeable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9833 | 0.9696 | 1.0000 |
| bridgeable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9833 | 0.9696 | 1.0000 |
| supported | r2_nearest | 0.2000 | 288.0000 | 0.1144 | 1.0000 | 0.9936 | 1.0000 |
| supported | r2_nearest | 0.3000 | 288.0000 | 0.1144 | 1.0000 | 0.9936 | 1.0000 |
| supported | r2_random | 0.2000 | 288.0000 | 0.1149 | 1.0000 | 0.9936 | 1.0000 |
| supported | r2_random | 0.3000 | 288.0000 | 0.1149 | 1.0000 | 0.9936 | 1.0000 |
| supported | r2_static | 0.2000 | 0.0000 | 0.1169 | 1.0000 | 0.9936 | 1.0000 |
| supported | r2_static | 0.3000 | 0.0000 | 0.1169 | 1.0000 | 0.9936 | 1.0000 |
| supported | r2_targeted | 0.2000 | 288.0000 | 0.1141 | 1.0000 | 0.9936 | 1.0000 |
| supported | r2_targeted | 0.3000 | 288.0000 | 0.1141 | 1.0000 | 0.9936 | 1.0000 |
| supported | rinf_targeted | 0.2000 | 288.0000 | 0.1769 | 1.0000 | 0.9936 | 1.0000 |
| supported | rinf_targeted | 0.3000 | 288.0000 | 0.1769 | 1.0000 | 0.9936 | 1.0000 |
| supported | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9883 | 0.9761 | 1.0000 |
| supported | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9883 | 0.9761 | 1.0000 |
| unreachable | r2_nearest | 0.2000 | 288.0000 | 1.2367 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | r2_nearest | 0.3000 | 288.0000 | 1.2367 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | r2_random | 0.2000 | 288.0000 | 1.2945 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | r2_random | 0.3000 | 288.0000 | 1.2945 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | r2_static | 0.2000 | 0.0000 | 1.4417 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | r2_static | 0.3000 | 0.0000 | 1.4417 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | r2_targeted | 0.2000 | 288.0000 | 1.2367 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | r2_targeted | 0.3000 | 288.0000 | 1.2367 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | rinf_targeted | 0.2000 | 288.0000 | 1.2283 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | rinf_targeted | 0.3000 | 288.0000 | 1.2283 | 1.0000 | 0.9936 | 0.0000 |
| unreachable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9933 | 0.9830 | 1.0000 |
| unreachable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9933 | 0.9830 | 1.0000 |

## 分曲面结果：不由合并平均掩盖差异

| surface | scenario | method | tolerance | mean_actual_cost | mean_halfwidth | path_covered |
| --- | --- | --- | --- | --- | --- | --- |
| linear | bridgeable | r2_targeted | 0.2000 | 288.0000 | 0.1493 | 1.0000 |
| linear | bridgeable | r2_targeted | 0.3000 | 288.0000 | 0.1493 | 1.0000 |
| linear | bridgeable | rinf_targeted | 0.2000 | 288.0000 | 0.2491 | 1.0000 |
| linear | bridgeable | rinf_targeted | 0.3000 | 288.0000 | 0.2607 | 1.0000 |
| linear | bridgeable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9900 |
| linear | bridgeable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9900 |
| linear | supported | r2_targeted | 0.2000 | 288.0000 | 0.1080 | 1.0000 |
| linear | supported | r2_targeted | 0.3000 | 288.0000 | 0.1080 | 1.0000 |
| linear | supported | rinf_targeted | 0.2000 | 288.0000 | 0.1719 | 1.0000 |
| linear | supported | rinf_targeted | 0.3000 | 288.0000 | 0.1719 | 1.0000 |
| linear | supported | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9850 |
| linear | supported | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9850 |
| linear | unreachable | r2_targeted | 0.2000 | 288.0000 | 1.1518 | 1.0000 |
| linear | unreachable | r2_targeted | 0.3000 | 288.0000 | 1.1518 | 1.0000 |
| linear | unreachable | rinf_targeted | 0.2000 | 288.0000 | 1.1428 | 1.0000 |
| linear | unreachable | rinf_targeted | 0.3000 | 288.0000 | 1.1428 | 1.0000 |
| linear | unreachable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9950 |
| linear | unreachable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9950 |
| quadratic | bridgeable | r2_targeted | 0.2000 | 288.0000 | 0.1926 | 1.0000 |
| quadratic | bridgeable | r2_targeted | 0.3000 | 288.0000 | 0.1926 | 1.0000 |
| quadratic | bridgeable | rinf_targeted | 0.2000 | 288.0000 | 0.3615 | 1.0000 |
| quadratic | bridgeable | rinf_targeted | 0.3000 | 288.0000 | 0.3588 | 1.0000 |
| quadratic | bridgeable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9800 |
| quadratic | bridgeable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9800 |
| quadratic | supported | r2_targeted | 0.2000 | 288.0000 | 0.1165 | 1.0000 |
| quadratic | supported | r2_targeted | 0.3000 | 288.0000 | 0.1165 | 1.0000 |
| quadratic | supported | rinf_targeted | 0.2000 | 288.0000 | 0.1797 | 1.0000 |
| quadratic | supported | rinf_targeted | 0.3000 | 288.0000 | 0.1797 | 1.0000 |
| quadratic | supported | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9850 |
| quadratic | supported | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9850 |
| quadratic | unreachable | r2_targeted | 0.2000 | 288.0000 | 1.3428 | 1.0000 |
| quadratic | unreachable | r2_targeted | 0.3000 | 288.0000 | 1.3428 | 1.0000 |
| quadratic | unreachable | rinf_targeted | 0.2000 | 288.0000 | 1.3357 | 1.0000 |
| quadratic | unreachable | rinf_targeted | 0.3000 | 288.0000 | 1.3357 | 1.0000 |
| quadratic | unreachable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9950 |
| quadratic | unreachable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9950 |
| sinusoidal | bridgeable | r2_targeted | 0.2000 | 288.0000 | 0.2795 | 1.0000 |
| sinusoidal | bridgeable | r2_targeted | 0.3000 | 288.0000 | 0.2367 | 1.0000 |
| sinusoidal | bridgeable | rinf_targeted | 0.2000 | 288.0000 | 0.2813 | 1.0000 |
| sinusoidal | bridgeable | rinf_targeted | 0.3000 | 288.0000 | 0.2813 | 1.0000 |
| sinusoidal | bridgeable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9800 |
| sinusoidal | bridgeable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9800 |
| sinusoidal | supported | r2_targeted | 0.2000 | 288.0000 | 0.1177 | 1.0000 |
| sinusoidal | supported | r2_targeted | 0.3000 | 288.0000 | 0.1177 | 1.0000 |
| sinusoidal | supported | rinf_targeted | 0.2000 | 288.0000 | 0.1791 | 1.0000 |
| sinusoidal | supported | rinf_targeted | 0.3000 | 288.0000 | 0.1791 | 1.0000 |
| sinusoidal | supported | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9950 |
| sinusoidal | supported | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9950 |
| sinusoidal | unreachable | r2_targeted | 0.2000 | 288.0000 | 1.2155 | 1.0000 |
| sinusoidal | unreachable | r2_targeted | 0.3000 | 288.0000 | 1.2155 | 1.0000 |
| sinusoidal | unreachable | rinf_targeted | 0.2000 | 288.0000 | 1.2062 | 1.0000 |
| sinusoidal | unreachable | rinf_targeted | 0.3000 | 288.0000 | 1.2062 | 1.0000 |
| sinusoidal | unreachable | target_only | 0.2000 | 288.0000 | 0.1686 | 0.9900 |
| sinusoidal | unreachable | target_only | 0.3000 | 288.0000 | 0.1686 | 0.9900 |

## 达到指定精度的概率与实际支出

| scenario | method | tolerance | criterion | attainment_rate | mean_spent_until_hit_or_budget | n_not_attained |
| --- | --- | --- | --- | --- | --- | --- |
| bridgeable | r2_nearest | 0.2000 | certificate | 0.0000 | 288.0000 | 600 |
| bridgeable | r2_nearest | 0.2000 | returned_interval | 0.0300 | 283.5200 | 582 |
| bridgeable | r2_nearest | 0.3000 | certificate | 1.0000 | 238.8800 | 0 |
| bridgeable | r2_nearest | 0.3000 | returned_interval | 1.0000 | 196.4800 | 0 |
| bridgeable | r2_random | 0.2000 | certificate | 0.3867 | 265.2800 | 368 |
| bridgeable | r2_random | 0.2000 | returned_interval | 0.3967 | 263.3600 | 362 |
| bridgeable | r2_random | 0.3000 | certificate | 1.0000 | 162.2400 | 0 |
| bridgeable | r2_random | 0.3000 | returned_interval | 1.0000 | 147.0400 | 0 |
| bridgeable | r2_static | 0.2000 | certificate | 0.0000 | 0.0000 | 600 |
| bridgeable | r2_static | 0.2000 | returned_interval | 0.0000 | 0.0000 | 600 |
| bridgeable | r2_static | 0.3000 | certificate | 0.0000 | 0.0000 | 600 |
| bridgeable | r2_static | 0.3000 | returned_interval | 0.0000 | 0.0000 | 600 |
| bridgeable | r2_targeted | 0.2000 | certificate | 0.6667 | 226.5600 | 200 |
| bridgeable | r2_targeted | 0.2000 | returned_interval | 0.6750 | 226.0800 | 195 |
| bridgeable | r2_targeted | 0.3000 | certificate | 1.0000 | 120.0000 | 0 |
| bridgeable | r2_targeted | 0.3000 | returned_interval | 1.0000 | 112.8000 | 0 |
| bridgeable | rinf_targeted | 0.2000 | certificate | 0.0000 | 288.0000 | 600 |
| bridgeable | rinf_targeted | 0.2000 | returned_interval | 0.0567 | 280.0000 | 566 |
| bridgeable | rinf_targeted | 0.3000 | certificate | 0.3450 | 221.7600 | 393 |
| bridgeable | rinf_targeted | 0.3000 | returned_interval | 0.5883 | 193.4400 | 247 |
| bridgeable | target_only | 0.2000 | certificate | 1.0000 | 288.0000 | 0 |
| bridgeable | target_only | 0.2000 | returned_interval | 1.0000 | 288.0000 | 0 |
| bridgeable | target_only | 0.3000 | certificate | 1.0000 | 96.0000 | 0 |
| bridgeable | target_only | 0.3000 | returned_interval | 1.0000 | 96.0000 | 0 |
| supported | r2_nearest | 0.2000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_nearest | 0.2000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | r2_nearest | 0.3000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_nearest | 0.3000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | r2_random | 0.2000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_random | 0.2000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | r2_random | 0.3000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_random | 0.3000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | r2_static | 0.2000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_static | 0.2000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | r2_static | 0.3000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_static | 0.3000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | r2_targeted | 0.2000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_targeted | 0.2000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | r2_targeted | 0.3000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | r2_targeted | 0.3000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | rinf_targeted | 0.2000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | rinf_targeted | 0.2000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | rinf_targeted | 0.3000 | certificate | 1.0000 | 0.0000 | 0 |
| supported | rinf_targeted | 0.3000 | returned_interval | 1.0000 | 0.0000 | 0 |
| supported | target_only | 0.2000 | certificate | 1.0000 | 288.0000 | 0 |
| supported | target_only | 0.2000 | returned_interval | 1.0000 | 288.0000 | 0 |
| supported | target_only | 0.3000 | certificate | 1.0000 | 96.0000 | 0 |
| supported | target_only | 0.3000 | returned_interval | 1.0000 | 96.0000 | 0 |
| unreachable | r2_nearest | 0.2000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | r2_nearest | 0.2000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | r2_nearest | 0.3000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | r2_nearest | 0.3000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | r2_random | 0.2000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | r2_random | 0.2000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | r2_random | 0.3000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | r2_random | 0.3000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | r2_static | 0.2000 | certificate | 0.0000 | 0.0000 | 600 |
| unreachable | r2_static | 0.2000 | returned_interval | 0.0000 | 0.0000 | 600 |
| unreachable | r2_static | 0.3000 | certificate | 0.0000 | 0.0000 | 600 |
| unreachable | r2_static | 0.3000 | returned_interval | 0.0000 | 0.0000 | 600 |
| unreachable | r2_targeted | 0.2000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | r2_targeted | 0.2000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | r2_targeted | 0.3000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | r2_targeted | 0.3000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | rinf_targeted | 0.2000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | rinf_targeted | 0.2000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | rinf_targeted | 0.3000 | certificate | 0.0000 | 288.0000 | 600 |
| unreachable | rinf_targeted | 0.3000 | returned_interval | 0.0000 | 288.0000 | 600 |
| unreachable | target_only | 0.2000 | certificate | 1.0000 | 288.0000 | 0 |
| unreachable | target_only | 0.2000 | returned_interval | 1.0000 | 288.0000 | 0 |
| unreachable | target_only | 0.3000 | certificate | 1.0000 | 96.0000 | 0 |
| unreachable | target_only | 0.3000 | returned_interval | 1.0000 | 96.0000 | 0 |

## 定向 R2 的配对精度差异

下表差值为定向 R2 减去对照；负半宽差表示返回区间更窄。比较静态方法时实际成本不同，不属于等成本优势。

| scenario | tolerance | comparator | matched_actual_cost | targeted_minus_comparator | lower | upper |
| --- | --- | --- | --- | --- | --- | --- |
| bridgeable | 0.2000 | rinf_targeted | True | -0.0902 | -0.0936 | -0.0867 |
| bridgeable | 0.2000 | r2_random | True | -0.0594 | -0.0639 | -0.0549 |
| bridgeable | 0.2000 | r2_nearest | True | -0.0964 | -0.0997 | -0.0930 |
| bridgeable | 0.2000 | r2_static | False | -0.3512 | -0.3539 | -0.3485 |
| bridgeable | 0.2000 | target_only | True | 0.0385 | 0.0367 | 0.0404 |
| bridgeable | 0.3000 | rinf_targeted | True | -0.1074 | -0.1105 | -0.1045 |
| bridgeable | 0.3000 | r2_random | True | -0.0181 | -0.0194 | -0.0169 |
| bridgeable | 0.3000 | r2_nearest | True | -0.0598 | -0.0604 | -0.0592 |
| bridgeable | 0.3000 | r2_static | False | -0.3654 | -0.3676 | -0.3632 |
| bridgeable | 0.3000 | target_only | True | 0.0242 | 0.0240 | 0.0245 |
| supported | 0.2000 | rinf_targeted | True | -0.0629 | -0.0630 | -0.0627 |
| supported | 0.2000 | r2_random | True | -0.0008 | -0.0009 | -0.0008 |
| supported | 0.2000 | r2_nearest | True | -0.0004 | -0.0004 | -0.0003 |
| supported | 0.2000 | r2_static | False | -0.0029 | -0.0030 | -0.0028 |
| supported | 0.2000 | target_only | True | -0.0546 | -0.0547 | -0.0544 |
| supported | 0.3000 | rinf_targeted | True | -0.0629 | -0.0630 | -0.0627 |
| supported | 0.3000 | r2_random | True | -0.0008 | -0.0009 | -0.0008 |
| supported | 0.3000 | r2_nearest | True | -0.0004 | -0.0004 | -0.0003 |
| supported | 0.3000 | r2_static | False | -0.0029 | -0.0030 | -0.0028 |
| supported | 0.3000 | target_only | True | -0.0546 | -0.0547 | -0.0544 |
| unreachable | 0.2000 | rinf_targeted | True | 0.0084 | 0.0071 | 0.0098 |
| unreachable | 0.2000 | r2_random | True | -0.0578 | -0.0640 | -0.0518 |
| unreachable | 0.2000 | r2_nearest | True | 0.0000 | 0.0000 | 0.0000 |
| unreachable | 0.2000 | r2_static | False | -0.2050 | -0.2093 | -0.2009 |
| unreachable | 0.2000 | target_only | True | 1.0681 | 1.0638 | 1.0722 |
| unreachable | 0.3000 | rinf_targeted | True | 0.0084 | 0.0071 | 0.0097 |
| unreachable | 0.3000 | r2_random | True | -0.0578 | -0.0640 | -0.0521 |
| unreachable | 0.3000 | r2_nearest | True | 0.0000 | 0.0000 | 0.0000 |
| unreachable | 0.3000 | r2_static | False | -0.2050 | -0.2094 | -0.2009 |
| unreachable | 0.3000 | target_only | True | 1.0681 | 1.0642 | 1.0721 |

## 能回答和不能回答的审稿问题

本轮为 nrhq 的替代方法比较（REV-07）增加在共同模拟条件下的成本、精度和可靠性证据；为拒绝输出及停止口径（REV-12）提供完整记录。应根据逐场景结果决定支持范围，不能仅因运行完成而认定审稿意见解决。

本轮仍是设计驱动权重与一步半径桥接启发式。它没有验证结果自适应选择的实际收益，不能据此关闭 WGDN 的选择安全效用质疑；也没有补齐真实机制集合、真实应用或近邻新颖性。

## 图表与机器记录

- `summary.csv`：逐单元与等权汇总，prefix/stopped 分开，包含全分母状态与覆盖区间。
- `attainment.csv` / `attainment_summary.csv`：每世界首次命中、未命中状态及成本。
- `paired_comparisons.csv` / `paired_attainment.csv`：配对点态区间。
- `figures/`：成本—半宽、路径覆盖、两种达标任务，均导出 PDF 与 PNG。
- `analysis_validation.json` / `analysis_manifest.json`：分析校验、哈希、版本与口径。
