# 新版论文实验套件

面向 2026-09-16 *When Can Experiments Transfer? Operational Certificates and Active Causal Bridging*。
独立算法、独立配置、独立结果；不覆盖旧实验、不依赖旧 src。不只是方案：本目录提供运行器、数学内核、自动检查、真实数据校验及结果报告。

## 阅读顺序

1. [CURRENT_ARTIFACTS](../CURRENT_ARTIFACTS.md)：当前论文项目与实验产物的对应关系。
2. [完整实验结果解读](results/full/结果解读.md)：运行后生成的中文结论与表格。
3. `results/full/figures/`：PNG（预览）和 SVG（可编辑矢量）图。
4. `results/full/run_manifest.json`：配置、种子、软件环境、运行耗时、输入/源码/输出哈希。

已完成正式 full 运行：1,200 个完整流程场景档案（200 个配对随机重复 × 6 场景）、9,600 条方法记录、200 个 Gaussian 桥接设计、57 个真实来源留出。配对场景不是 1,200 个完全独立重复。测试日志与结果检查均保存在结果目录。

## 运行

从仓库根目录：

```powershell
python -m pip install -r current_method/requirements.txt
python current_method/run_all.py --profile smoke
python current_method/run_all.py --profile full
cd current_method
python -m unittest discover -s tests -v
```

自动运行器会设置正确工作目录并先执行测试。
不联网调试可加 `--skip-real`，输出另存于 `results/<profile>_synthetic_only`，报告会标注真实数据未运行。首次真实测试下载经过 commit 固定和 SHA-256 校验的数据，以后用本地缓存。
完整运行的统计配置事先写入 `configs/full.json`，轻量测试输出在 `results/smoke`，不能当作论文完整结果。

仅修改报告或图形时，可运行 `python current_method/refresh_report.py --profile full`，它检查实验核心源码哈希、使用已存 CSV，避免重新抽样。图形后处理版本另记入 manifest。

机制集合校准审计使用独立的 outcome-blind 入口：`python current_method/run_mechanism_calibration.py`，或从仓库根目录运行 `python reproduce.py calibration --output reproduced/calibration`。协议和边界见 `docs/mechanism_set_calibration_protocol.md`；它是带标签的控制审计，不是现实跨干预校准的替代品。

第二轮独立复核：

```powershell
python current_method/run_plus.py --profile smoke_plus
python current_method/run_plus.py --profile full_plus
```

`full_plus` 独立测试相关源噪声、Gaussian 前提失效、联合校准样本量和权重优化数值误差，结果在 `results/full_plus`；它不会修改 `results/full`。

## 文件组织

完整流程实验（独立输出，不覆盖以上两轮）：

```powershell
python current_method/run_workflow.py --profile workflow_smoke
python current_method/run_workflow.py --profile workflow_full
```

协议见 [完整流程实验协议](docs/完整流程实验协议.md)。包含二维联合机制校准、真实生成的两臂随机试验、拒绝后桥接采集、重新估计和首次发布后停止；比较直接优化 R2/R∞、随机桥接、最近桥接、无桥接与目标重做。正式配置是 1,800 个独立世界，每个世界 6 方法 × 2 阈值配对评估。代码会拒绝覆盖已有运行；复跑请先把对应结果目录移动到明确的带版本名目录保留。

入口结果：[完整流程报告](results/workflow_full/完整流程实验结果.md)、`workflow_records.csv`、`acquisitions.csv`、`paired_comparisons.csv`、`run_manifest.json`。`world_audits.jsonl` 在评分后公开机制真值用于审计；它不作为规划器输入。该实验仍是合成验证，不代表真实跨干预机制集合已经校准。

```text
atlas_new/core.py         集合最坏情形、R∞/R2、sharp LP、Gaussian桥接
atlas_new/experiments.py  六组合成与校准模块
atlas_new/manylabs.py     57-source framing holdout 与目标结果泄漏测试
atlas_new/report.py       CSV校验、图、中文报告
configs/                 冻结样本量、种子、预算、阈值
docs/                    理论对应和实验协议
tests/                   独立数学恒等式、反例、前提与接口检查
data/                    经校验的公开原始数据及provenance
results/full/            全量运行结果、端点见证、图、报告
```

## 三个必须保留的边界

- 模拟中的历史机制审计能获得机制标签；真实 Many Labs 数据没有这些标签，因此真实基准只执行固定/随机效应方法，不冒称已实现真实 U_i 校准。
- 箱子半径计算在本一维设定中精确；多起点权重优化只认证可行性，不认证全局最优。
- 联合事件给无条件错误发布控制；不能偷换成给定发布后仍保证 95% 条件覆盖。

## 与旧仓库的关系

Many Labs 数据来源为论文固定的公开仓库和 OSF 8cd4r；引用原研究 Klein et al. (2018)，数据适用原提供者条款。

## 审查后新增的两组贡献归因实验

2026-09-17 完成同一证书下的四种权重对照，以及三种几何误差界消融。
使用原工作流的 1,800 个配对世界，共享随机／最近机制桥接顺序，分别比较 R2 和 R∞。

```powershell
python current_method/run_ablations.py --profile smoke --workers 4
python current_method/run_ablations.py --profile full --workers 4
python current_method/audit_ablations.py
```

入口拒绝覆盖已有结果；复跑应在独立副本中进行。正式输出在 `results/ablations_full`。
协议见 [ablation_protocol.md](docs/ablation_protocol.md)，主要结果和负结果见
[ablation_results_zh.md](docs/ablation_results_zh.md)。
附录表格 15--16 已集成到当前论文；仓库保留其数值结果、审计记录和运行代码。

独立核验检查全部 172,800 个计划和 345,600 条停止记录，并确认与已有随机／最近 R2 工作流一致。
`plans.jsonl.gz` 是 `plans.jsonl` 的已验证无损压缩副本，发布仓库时可用前者避免单文件体积限制。
这些实验支持本 DGP 中优化权重及 barycentric 几何的作用；未观察到两种界取最小值比 Bbar 单独使用带来额外发布率或成本收益。
它们不构成 ExAtlas 对照，也不解决真实机制集合校准问题。
