# 审稿问题跟踪

更新：2026-11-07（Asia/Shanghai）。基线：`7e5841d3f3f22f892233582b9509aad656f3d266`；分支：`codex/reviewer-guided-rebuild`。

作者已接受所测非高斯线性模型中有限新增桥接预算明显缩短历史区间的结论，本轮主实验收束。机制集合消融已按协议4528e20完成并独立审核；真实实验review与开跑条件已整理，适用准备完整后才开始。机器可读版本为 `review_tracker.json`，两份同步维护。

## 每轮固定要求

- 每次实验推进前、后回顾全部 review 和 12 个问题。
- 不能用已运行代替已解决；状态由验收证据决定，保留未覆盖问题与负结果。
- 实验重建使用本地Git分支；未经明确安排不向公开实验仓库发布修订记录。

推进前：读全部 review 映射与 12 项现状，记录假设、信息、对照、预算、指标、预期及能/不能回答的问题。

推进后：记录版本、配置、种子、产物和结果，逐项回顾全部问题。将前/后记录分别写入 JSON 的 `round_review_protocol.entries`。未检查的意见沿用状态，负结果保留。

本轮设计：[FIRST_WORKFLOW.md](FIRST_WORKFLOW.md)；运行前冻结协议：[COST_PRECISION_RUN01.md](COST_PRECISION_RUN01.md)。原复现和新smoke/full均完成，结果见[RUN01解读](results/cost_precision_run01/RESULTS.md)。作者理解仍待讨论；下方旧轮次记录按历史保留。

状态：`open` = 关键修复证据仍缺；`partial_evidence` = 有限证据不足验收；`pending_source` = 写作待最新源；`writing_in_progress` = 最新源已取得、副本改写进行中。本轮不设 resolved。

## 12 个问题

### REV-01 · 引言、首现定义与解释顺序

优先级：P1；状态：`partial_evidence`。映射：nrhq.W1、nrhq.W2、nrhq.Q1。

已知证据：已有 PDF 及改写候选；nrhq 指出 decision layer、certificate、bridge 等定义前使用。 用户已在本机完成Overleaf克隆。原稿位于 causal_lab_proposal_subpapers_tex_iclr2027/01.tex；基线29e4c0db4a17e72e04d9a1c9b330e81b166c604a，原稿SHA256为ef261e308e3463eb8e54d5de3c0fded1879f58777222f0115a0c5a5f79eaab73。同目录01_humanized.tex已创建并提交475b1ec，用户已推送，origin/main与推送reflog均已更新；原稿保留。

缺口：副本已通过语义审查和编译，正文10页；尚需作者审阅可读性。对照实验和新增贡献不由文字编辑解决。

验收证据：

- 最新源与 prose-only diff；先解释目标、输入、假设和输出，再用术语；贯穿例子和图 1 可独立读懂。
- 数学、引用、数值和限定条件保持准确，编译与逐项阅读通过。

下一步：作者审阅Overleaf副本；实验工作继续提供可理解的单世界运行轨迹。

首轮能回答：为方法直觉提供一个可检查的流程例子。

首轮不能回答：一次流程运行自动解决写作、实用收益或新增贡献问题。

依据：`用户 PDF 第 1–2 页`；`nrhq review`。

本轮更新（RUN01）：有可复核的完整流程、成本与精度例子；作者是否理解、正文是否足够清楚仍需讨论。 状态不变。

### REV-02 · R∞ 的代价与 R2 的实际用途

优先级：P0；状态：`partial_evidence`。映射：WGDN.W1a、WGDN.Q1、nrhq.Q1。

已知证据：当前 optimize_radius / plan 不接收 observed effects，主 workflow 是设计权重并实际使用 R2。 同一非负权重、偏差项、噪声及置信预算下 R∞≥R2；不能寻找同条件的反向发布例子。 已有 workflow 记录显示 R∞ 释放更少；这是原有结果，非本轮运行。

缺口：缺真实 outcome-adaptive 用途和与合法 sample splitting 的匹配对照；权重优化收益不能归为 selection safety。

验收证据：

- 逐 policy 标明信息、权重选择时机和合法 bound；明确半径关系及条件。
- 同目标/信息/预算下报告覆盖、发布、宽度和成本；直接回答有无适应性实用收益，必要时收窄主张。

下一步：首轮跟踪设计权重和 R2/R∞ 分解；后续单独定义适应性任务及对照。

首轮能回答：当前 planner 是否使用结果、半径来源与适用条件。

首轮不能回答：R∞ 普遍更优；完成 sample-split 或真实适应性效用比较。

依据：`current_method/atlas_new/core.py`；`current_method/atlas_new/workflow.py`；`current_method/results/workflow_full/pooled_summary.csv`。

本轮更新（RUN01）：补齐设计型 R2/R∞ 的成本、宽度和覆盖比较；未测试结果驱动选择或合法 sample splitting，不能据此宣称 selection-safe 收益。 状态不变。

### REV-03 · 摘要数字与证书结果归因

优先级：P0；状态：`partial_evidence`。映射：WGDN.W1b、nrhq.Q1、nrhq.Q2。

已知证据：95.3% / 0.2% 对应 Gaussian Bonferroni 与未校正区间，不是完整证书效用；Table 15 另列 theorem simultaneous。

缺口：摘要Bonferroni归因已澄清；主要贡献、全部图表到实际策略及保证的系统核对和完整方法效用证据仍需后续实验。

验收证据：

- headline 数字逐项对应实际方法和设置；Bonferroni 动机例子与完整方法结果分开。
- 摘要实用结论由相应方法直接支持，负结果与范围保留。

下一步：复核每个主要实验结论的实际方法与保证，决定摘要应呈现哪些完整方法结果。

首轮能回答：本轮实际使用哪个 bound、policy 和评价事件。

首轮不能回答：复现 textbook 选择偏差即证明本方法新增贡献。

依据：`用户 PDF 摘要、Figure 2B、Table 15`；`paper_original/run_operational_experiments.py`。

本轮更新（RUN01）：新数字明确绑定 R2/R∞、prefix/stopped 与输出任务；未把本轮数字自动写入摘要，其他实验归因仍待全篇核对。 状态不变。

### REV-04 · 真实机制集合与 L,H 的来源

优先级：P0；状态：`open`。映射：WGDN.W2a、WGDN.Q2、KoBT.W1、KoBT.Q1。

已知证据：现有 workflow 用合成机制标签与解析 L,H；joint calibration 在合成、声明条件下验证。 有限档案诊断不能证明遗漏机制不存在或认证全域平滑性上界。

缺口：缺真实、结果盲、可追溯的机制坐标、集合、L,H、联合覆盖依据及错设敏感性。

验收证据：

- 真实输入注明单位、来源、外部假设、未知项及集合扩大规则，在目标结果揭盲前固定。
- 说明独立校准依据，或明确条件证书/敏感性分析；扫描集合宽度与 L,H 错设。

下一步：首轮解释模拟输入来源；另立真实 archive 输入审计。

首轮能回答：模拟 U,L,H 如何获得、哪些真值只用于评价。

首轮不能回答：现实集合或 L,H 已有效；合成校准直接认证真实跨干预。

依据：`current_method/atlas_new/workflow.py`；`current_method/docs/mechanism_set_calibration_protocol.md`。

本轮更新（RUN01）：仅使用合成校准和已知解析 L,H；真实机制集合、错设与外部有效性没有新增证据。 状态不变。

### REV-05 · 真实闭环与微贷 not_qualified

优先级：P0；状态：`open`。映射：WGDN.W2b、WGDN.Q2、KoBT.W3、KoBT.Q1。

已知证据：微贷 ATLAS 为 not_qualified，n_computed=0；不是计算证书后全部拒绝。 published 主分析为 Mexico、India EL1 两项；NSW 是 within-trial reconstruction，不能作为跨干预机制保证验证。

缺口：尚无真实 audit→集合→半径→发布/拒绝→验证的完整证书案例。

验收证据：

- 至少一个真实 worked case 实际给出半径分解、目标区间与决策；全拒绝可以，但必须真正计算。
- 资格失败、计算后拒绝、发布单独计数；未计算宽度不填 0，零发布条件风险为 undefined。

下一步：结合 REV-04 建真实输入；先统一状态语义，再运行真实证书。

首轮能回答：用合成轨迹演示完整链路及状态记录。

首轮不能回答：用合成闭环替代真实闭环；not_qualified 等于成功拒绝。

依据：`MICROCREDIT_PUBLISHED_V1_REPORT_20260925.md`；`results/microcredit_primary_published_v1/loso_summary.csv`；`results/microcredit_primary_published_v1/qualification_audit.csv`。

本轮更新（RUN01）：完整合成闭环已实际重跑；真实微贷 not_qualified 和真实证书案例缺口不变。 状态不变。

### REV-06 · Many Labs 目标噪声与迁移证据

优先级：P0；状态：`partial_evidence`。映射：WGDN.W2c、WGDN.W2b、nrhq.Q2。

已知证据：halfwidth 含 target_design_variance，属于 noisy reference 的预测噪声；这不等于发现 outcome leakage。 已有 57 目标 CSV 的只读诊断：fixed 目标噪声占总方差中位 98.8774%，random 98.0202%。 δ=.15 时仅留目标噪声，fixed 10/57 的发布决定不变；random 原 6/57 变 7/57。

缺口：缺等目标 n / 固定参考噪声诊断；多效应族基线已有，仍不认证 archive 兼容性。

验收证据：

- 分开 target estimand 与 noisy reference，拆分 archive、transport、target validation 不确定性。
- 完成控制目标噪声的诊断与多效应族评估，基线预测与主证书分别报告。

下一步：首轮保持问题开放；另立 Many Labs 评价口径与目标噪声控制实验。

首轮能回答：合成流程中的证书与评价噪声如何区分。

首轮不能回答：首轮 smoke 解决 Many Labs 目标样本量问题或证明真实迁移。

依据：`paper_original/run_manylabs2_framing.py`；`current_method/atlas_new/manylabs.py`；`current_method/results/full/manylabs_holdouts.csv`；`本会话对已有 CSV 的只读半径分解；非新方法实验`。

本轮更新（RUN01）：没有运行 Many Labs；目标噪声主导的问题不由本轮修复。 状态不变。

### REV-07 · 可行基线、权重收益与完整成本

优先级：P0；状态：`partial_evidence`。映射：nrhq.W4、nrhq.Q2、WGDN.W1a、WGDN.Q1。

已知证据：已有 Appendix P 在共同 random bridge path 下支持部分合成场景的 design-only R2 权重收益，不能归为 R∞ 收益或超越最近前作。 已有汇总中直接 target trial 在若干设置更有利；审计/部署成本未纳入；尚无完整 ExAtlas matched-information 对照。

缺口：合成六策略已按统一评价比较；仍缺最近前作、样本拆分等强外部基线与审计部署总成本，以及真实输入下的对应证据。

验收证据：

- 与适用设计权重、稳健聚合、样本拆分、最近前作和直接 trial 比较，明确不可比条件。
- 报告 coverage、错误发布、发布率、宽度、目标误差与成本；保留全部预设场景及负结果。

下一步：作者讨论成本—精度交叉及失败场景；下一协议考虑可观测输入下桥接/目标切换，强外部基线和完整成本仍须独立补齐。

首轮能回答：单世界中各策略做了什么、花费多少参与者。

首轮不能回答：smoke 证明优越性；弱基线已覆盖 ExAtlas；参与者成本等于现实总成本。

依据：`current_method/results/ablations_full/report.md`；`current_method/results/ablations_full/stopped_summary.csv`；`current_method/results/workflow_full/pooled_summary.csv`。

本轮更新（RUN01）：在共同名义可靠性、明确新增成本下完成六策略和全部预设场景比较，直接推进 nrhq.W4/Q2；最近前作/样本拆分及审计部署总成本仍缺。 状态不变。

### REV-08 · I&K、Manski、ExAtlas 与新增贡献

优先级：P0；状态：`open`。映射：nrhq.W3、nrhq.Q1、WGDN.W2d、WGDN.Q3。

已知证据：根代理核实 I&K 已有 pairwise bounded-variation / Lipschitz 参数空间与 target projection；Manski 已有目标集合汇总。 根代理核实 ExAtlas 已有同型重心误差分解、凸组合、阈值拒绝和 bridge 流程。

缺口：缺逐命题符号映射、贡献归属修订、主文比较与匹配近邻实验。

验收证据：

- 按 estimand、信息、假设、目标、采样误差、机制集合和选择规则列已有、推论与新增命题。
- 区分 Theorem 5.3 的 finite-metric sharp 特例与一般 outer region；新增主张有证明或直接实验，并补引用。

下一步：依据原文完成Theorem 5.3继承关系与贡献边界改写；继续核对ExAtlas等近邻，不以任务名称不同替代数学比较。

首轮能回答：提供本实现的具体接口与信息边界供后续比较。

首轮不能回答：流程跑通证明新颖性；优于弱基线等于超越近邻。

依据：`https://arxiv.org/html/2108.06473v4`；`https://doi.org/10.1097/EDE.0000000000001178`；`https://arxiv.org/html/2605.27153v1`；`用户 PDF Theorem 5.3、Eq. 4.1、Appendix C`。

本轮更新（RUN01）：并行核查 I&K/Manski，明确 Theorem 5.3 的集合构造继承关系；未完成论文本体修改、全部近邻比较或贡献新颖性证明。 状态不变。

### REV-09 · 凸组合候选类的理由与边界

优先级：P1；状态：`open`。映射：KoBT.W2、KoBT.Q1。

已知证据：方法限制为非负和为一的 prior ATE 权重；现有定理不证明它在所有 transport 估计器中最优。 重心不必是可实施干预，机制凸包上的平滑性需要科学解释。

缺口：缺应用中选择该类的理由及负权重、外推、meta-regression / IPD 方法的信息条件对照。

验收证据：

- 说明 aggregate ATE 信息约束、稳定性/可解释性动机与限制，避免全局最优性表述。
- 给出适用和失效例子；合理替代类可用时公平比较，或说明额外信息需求。

下一步：首轮解释 simplex 权重；后续补候选类论证和 hull 外边界。

首轮能回答：凸组合类内如何计算、为什么当前保证适用。

首轮不能回答：该类在所有估计器中最优；真实机制插值天然合理。

依据：`current_method/atlas_new/core.py`；`用户 PDF Sections 3–4、Theorem 5.4`。

本轮更新（RUN01）：本轮维持 simplex 估计器类；没有负权重、回归或 IPD 对照，不能回答为何该候选类充分。 状态不变。

### REV-10 · bridge 定理与实际一步 heuristic

优先级：P1；状态：`partial_evidence`。映射：KoBT.W4、KoBT.Q1、nrhq.Q1。

已知证据：Theorem 5.6 为非自适应 linear-Gaussian logdet 保证，target radius 控制另需 posterior condition-number 条件。 workflow targeted R2 最小化 prospective radius，是一步 heuristic；并非上述 theorem-backed policy。

缺口：缺两种 policy 明确分离及匹配对照；缺非线性/非高斯/异方差/错设下证据。

验收证据：

- 每个 policy 标注目标、信息、假设和适用定理；不把 heuristic 结果当 logdet 保证。
- 定理域内验证，域外另列经验 stress test；共同预算比较 random、radius policy、logdet 等。

下一步：首轮保持实际代码身份；后续 theorem policy 另立实现与实验协议。

首轮能回答：当前一步规则如何选 bridge、更新半径和停止。

首轮不能回答：heuristic 运行验证 logdet 定理；保证扩展到一般非线性因果模型。

依据：`current_method/atlas_new/workflow.py`；`用户 PDF Theorem 5.6、Appendix L.3`。

本轮更新（RUN01）：验证的是 prospective-radius heuristic；随机与最近来源对照不能验证 logdet 定理，非高斯/异方差稳健性仍缺。 状态不变。

### REV-11 · 方法命名、旧 prototype 与结果版本

优先级：P1；状态：`open`。映射：WGDN.W3、KoBT.W3、KoBT.Q1、nrhq.W1。

已知证据：主文/附录 ATLAS 命名和旧 prototype 归属存在混淆；仓库已有 current_method、paper_original、legacy_audits 分区。

缺口：最新Overleaf源已取得，workflow已对应Appendix L / Tables 10–12 / Figure 5；全稿图表到实现、policy、bound、保证的完整清单尚未完成。

验收证据：

- 名称统一并首现介绍；图表和摘要结果有 source commit、method_id、bound_id、适用范围。
- 旧 prototype 明确标记，不能支持当前定理的真实有效性。

下一步：为首轮新输出记录代码、配置、方法与结果出处；继续核对其余论文图表。

首轮能回答：新输出可追溯到哪份代码、配置和方法。

首轮不能回答：旧prototype图表自动属于当前算法；一套workflow映射完成全稿归属检查。

依据：`CURRENT_ARTIFACTS.md`；`README.md`；`legacy_audits/`；`用户 PDF 附录和 NSW 叙述`。

本轮更新（RUN01）：新结果有冻结配置、独立种子、源快照和哈希；全篇 prototype 与当前方法的归属核对仍未完成。 状态不变。

### REV-12 · 拒绝对象、停止状态与统计验收

优先级：P1；状态：`partial_evidence`。映射：WGDN.Q2、WGDN.Q3、WGDN.W2b、KoBT.W3、KoBT.Q1、nrhq.Q2。

已知证据：已有 sharp_lipschitz / outer-region 工具和 workflow；有限已知位置的 sharp region 不等于一般机制集合的 sharp region。 联合事件 P(release 且 bad error) 控制不等于给定 release 的条件覆盖。 现有 unreachable 菜单可耗尽预算仍拒绝；提前判无效/转直接 target 仍缺。

缺口：本合成流程输出/停止/空无界/分母已核对；真实资格失败状态、sharp区域与外区间的全篇归属，以及提前无效停止/目标切换仍待处理。

验收证据：

- 每次运行保存输入审计、半径分解、区域类型和停止原因；空集合不误作成功，outer/exact 分开。
- 指标注明分母、eta/zeta 和 joint/conditional 事件；零发布条件风险 undefined；策略切换先定义后评估。
- 每轮前后回顾全部 review，用产物逐项验收，运行成功不直接关闭问题。

下一步：讨论完整前缀与首次半宽达标结果；下一协议明确提前无效停止与目标切换，真实资格状态另立审计。

首轮能回答：工程闭环、状态、信息边界、统计口径和实际停止行为。

首轮不能回答：运行即解决 review；联合错误等于条件覆盖；真实输入可信性、新颖性或普遍优势。

依据：`current_method/atlas_new/core.py`；`current_method/atlas_new/workflow.py`；`用户 PDF Eq. 4.3、Theorem 5.3、Appendix F.7`。

本轮更新（RUN01）：严格区分点发布、拒绝外区间、半宽达标、完整前缀和原停止；失败/无界保留，支持本合成流程统计口径。真实资格状态、提前无效停止和 sharp 区域使用仍待处理。 状态不变。

## 完整 review 映射

下列 W/Q 标识用于本地跟踪，非新增审稿意见。官方 review ID 与编号解释保存在 JSON。

### nrhq · 2JCfCkHDXh

W1–W4 为逻辑分段，原文弱点未编号。

- nrhq.W1（未编号写作段 1）：术语未定义，引言和图 1 难读 → REV-01、REV-11
- nrhq.W2（未编号写作段 2）：缺直觉与例子，叙述含糊及 AI 写作质量质疑 → REV-01
- nrhq.W3（未编号 related-work 段）：主文文献定位不足 → REV-08
- nrhq.W4（未编号比较段）：没有可行替代方法对比 → REV-07
- nrhq.Q1（第 1 问）：关键创新及选择、权重、发布的作用 → REV-01、REV-02、REV-03、REV-08、REV-10
- nrhq.Q2（第 2 问）：与替代方法的结果比较 → REV-03、REV-06、REV-07、REV-12

### WGDN · nB7TstUxYZ

W1a/b、W2a–d 拆分原 W1/W2；W3 为未编号 smaller point。

- WGDN.W1a（W1 前两段）：选择安全半径损失 pooling 精度和发布能力 → REV-02、REV-07
- WGDN.W1b（W1 摘要段）：95.3% / 0.2% 来自 Bonferroni，非完整证书 → REV-03
- WGDN.W2a（W2 机制集合段）：真实集合未构造，合成标签校准不够 → REV-04
- WGDN.W2b（W2 真实数据段）：真实数据未实际应用主证书 → REV-05、REV-06、REV-12
- WGDN.W2c（W2 framing / Figure 3 段）：发布可能主要由目标样本量决定 → REV-06
- WGDN.W2d（W2 标准工具段）：理论工具标准，需要明确贡献与实用证据 → REV-08
- WGDN.W3（未编号 smaller point）：ATLAS 命名与旧 prototype 混用 → REV-11
- WGDN.Q1（第 1 问）：选择安全是否优于合法设计权重或样本拆分；否则定理作用 → REV-02、REV-07
- WGDN.Q2（第 2 问）：无机制标签如何构造真实集合并计算证书；全拒绝亦可 → REV-04、REV-05、REV-12
- WGDN.Q3（第 3 问）：Theorem 5.3 与 I&K / Manski 的关系和新增内容 → REV-08、REV-12

### KoBT · tjD8lFbVSQ

Q1 仅回指 W1–W4。

- KoBT.W1（W1）：机制集合及 L,H 的取得与错设风险 → REV-04
- KoBT.W2（W2）：为什么采用 prior ATE 的凸组合 → REV-09
- KoBT.W3（W3）：NSW / 微贷不足以支持主要实用主张 → REV-05、REV-11、REV-12
- KoBT.W4（W4）：bridge 保证仅限线性高斯，现实适用性未知 → REV-10
- KoBT.Q1（Questions: see weaknesses）：回指 W1–W4，无独立新增问题 → REV-04、REV-05、REV-09、REV-10、REV-11、REV-12


## WRITING-01 回顾

已回顾全部12项，未运行本轮新实验。01_humanized.tex完成主文改写与独立检查：正文10页、全稿42页，正式数学内容、数据表和原稿均保留。REV-01和REV-03有部分文字证据；摘要明确95.3%来自Gaussian Bonferroni。相关工作扩展仅使用原附录内容，尚未完成最近邻工作的数学比较。其余问题继续保持此前状态。写作提交为475b1ec，用户已推送且本地origin/main的推送记录一致。


## AUDIT-WORKFLOW-01 回顾与首轮设计

已重读三份review并回顾全部12项，所有状态保留。原完整合成workflow已存在：1800独立世界、6策略、2阈值；9源文件和18产物哈希一致。从固定旧轨迹独立重算R2半径，最大差异约3.11e-15；这属于旧结果核查，尚未运行新模拟。

- REV-01：只读重建原linear/bridgeable/replicate 0轨迹，解释半径.583089→.205812→.168749及192人停止；作者理解情况尚待讨论。
- REV-02：核实原workflow在观察结果前预规划全部候选顺序、权重与半径；新结果更新估计和拒绝区间，不提供outcome-adaptive选择收益证据。
- REV-07：复核原bridgeable汇总：delta=.3定向R2与直接目标均发布100%，平均新增人数117.92与96；仍是旧结果，不是本轮新实验。
- REV-10：原targeted逐候选最小化prospective radius；初始完整路径按设计排定，没有执行logdet策略。
- REV-11：原workflow对应01.tex Appendix L、Tables 10–12及Figure 5；9个manifest源文件及18个产物哈希均一致。
- REV-12：只读重建三几何linear/replicate 0的R2半径，最大差异3.11e-15；确认发布后预算行沿用输出与成本，plans中未来状态不是实际采集。

具体方案见 [FIRST_WORKFLOW.md](FIRST_WORKFLOW.md)：27世界smoke和单世界讲解，然后原1800世界full复现。每阶段检查全部review；保存不利结果。真实输入、真实闭环、Many Labs、近邻新增贡献、候选类合理性和更一般桥接保证继续开放。机器证据见 `evidence/workflow_archive_audit.json`。

## AUDIT-OUTPUT-MODES-01：点发布与区间信息

用户要求澄清桥接可发布点估计或返回区间时，如何与直接目标试验比较。已回顾全部12项，状态均保留；本次仅重读原代码并分析旧CSV，没有新模拟。

两种策略都以 R≤delta 为原发布条件，发布时同时给出点估计与区间；未发布的桥接仍返回外区间。此前讨论集中于发布率和新增人数，未充分评价区间收紧收益。bridgeable 的600个世界中，R∞ targeted在delta=.3时原发布208个，另有149个未发布但返回有限非空区间宽度≤.6；R2 targeted在delta=.2时原发布399个，另有8个未发布但区间宽度≤.4。

这些数量是原停止轨迹的探索性再分析，不是新的发布率。以区间中点作为估计并按宽度停止，会改变估计器和策略，必须单独规定并评估；不能直接据此改写原成本。首轮应区分桥接的信息收益与达到原点估计精度的成本。对应REV-07/09/12，真实输入、选择安全收益和新颖性仍未解决。证据：`evidence/output_mode_audit.json`。

## DESIGN-COST-PRECISION-01：成本与精度共同作为重点

作者明确本轮结论必须同时考虑成本与精度。已更新FIRST_WORKFLOW.md：在共同可靠性要求下，评价同预算精度和同精度成本，包含拒绝后的有效区间；原发布率保留为一种任务指标。点估计实际误差、返回区间半宽及原证书半径分别记录。

旧linear/bridgeable/replicate 0、delta=.3、96人时，定向R2和直接目标均发布，但半宽分别是.205812与.292060，说明相同成本和相同发布状态仍可有不同精度。这是解释性单例，不是总体优势证据。

已回顾全部12项，状态不变。重点推进REV-07与REV-12的评价设计，仍无新模拟。原停止轨迹与新完整预算采集轨迹明确分开；后者尚未实现，需要独立版本与预先固定的新种子。覆盖、无界/空区间、未达标世界以及成本范围都必须共同报告。真实机制、真实应用、自适应用途、新颖性与理论范围缺口均继续保留。


## COST-PRECISION-RUN01：执行完成

原流程已完整复现；独立种子的成本—精度新实验与分析完成。全部12项意见已回顾，负结果保留，没有问题标为全部解决；I&K/Manski阅读核查已另存。

- REV-01：有可复核的完整流程、成本与精度例子；作者是否理解、正文是否足够清楚仍需讨论。
- REV-02：补齐设计型 R2/R∞ 的成本、宽度和覆盖比较；未测试结果驱动选择或合法 sample splitting，不能据此宣称 selection-safe 收益。
- REV-03：新数字明确绑定 R2/R∞、prefix/stopped 与输出任务；未把本轮数字自动写入摘要，其他实验归因仍待全篇核对。
- REV-04：仅使用合成校准和已知解析 L,H；真实机制集合、错设与外部有效性没有新增证据。
- REV-05：完整合成闭环已实际重跑；真实微贷 not_qualified 和真实证书案例缺口不变。
- REV-06：没有运行 Many Labs；目标噪声主导的问题不由本轮修复。
- REV-07：在共同名义可靠性、明确新增成本下完成六策略和全部预设场景比较，直接推进 nrhq.W4/Q2；最近前作/样本拆分及审计部署总成本仍缺。
- REV-08：并行核查 I&K/Manski，明确 Theorem 5.3 的集合构造继承关系；未完成论文本体修改、全部近邻比较或贡献新颖性证明。
- REV-09：本轮维持 simplex 估计器类；没有负权重、回归或 IPD 对照，不能回答为何该候选类充分。
- REV-10：验证的是 prospective-radius heuristic；随机与最近来源对照不能验证 logdet 定理，非高斯/异方差稳健性仍缺。
- REV-11：新结果有冻结配置、独立种子、源快照和哈希；全篇 prototype 与当前方法的归属核对仍未完成。
- REV-12：严格区分点发布、拒绝外区间、半宽达标、完整前缀和原停止；失败/无界保留，支持本合成流程统计口径。真实资格状态、提前无效停止和 sharp 区域使用仍待处理。

运行32项与分析18项核验全部通过。最直接支持nrhq.W4/Q2的合成对照与成本—精度解释，未关闭该意见。详见[结果解读](results/cost_precision_run01/RESULTS.md)和[核验记录](evidence/cost_precision_run01_complete.json)。

## RELATED-WORK-01：点名文献阅读完成

[阅读说明](RELATED_WORK_READING.md)核实I&K已有pairwise Lipschitz空间、目标投影与含噪置信矩形构造；Manski的集合交原则与本稿有直接关系。Manski细节来自2019作者前稿，未声称读取最终刊版全文。REV-08保持open；论文相关工作与贡献定位尚待改写。


## THEORY-NONGAUSSIAN-01 与新实验设计

非高斯W形式概率界、真实观测误差与有限菜单目标区间选择已通过Lean；详见[验证范围](non_gaussian_bridge/README.md)。REV-10由open改为partial_evidence，仅支持Gaussian限制和选择目标这一部分。条件后验、固定参数覆盖与joint marginal coverage分开；线性、已知二阶矩、机制输入及现实适用性仍未解决。其余11项状态不变，没有resolved。

用户要求直接缩短目标区间，故新主选择是逐候选最小化有效半径；logdet为对照。已冻结[NON-GAUSSIAN-TARGET-RUN01](NON_GAUSSIAN_TARGET_RUN01.md)，commit 7846f87。协议表逐项回顾12项意见；新模拟结果尚未报告。


## NON-GAUSSIAN-TARGET-RUN01 完成后回顾

完整运行5400个独立世界、216000条相关预算记录，代码793f7ae，11项测试与8项运行核验通过。[完整结果](results/non_gaussian_target_run01/RESULTS.md)保留所有27个预设单元。强桥与直接目标实验在完整width=0.532657214043时分别需新增64与256人；计入共同历史则总128与320人。优势由预设2倍target loading解释，weak桥接负结果保留。

- REV-01：新增预先指定单世界的观测、权重、方差分解和采集/停止轨迹；不代替作者理解或全稿编辑。
- REV-02：验证新moment分支的design-only选择，不是R∞结果适应性效用证据。
- REV-03：结果对应新主定理和明确method_id；未自动改摘要数字。
- REV-04：V0、噪声方差、机制向量均为synthetic_known；真实集合、L/H与二阶矩校准仍未解决。
- REV-05：完成合成新分支闭环，没有新的真实微贷证书。
- REV-06：本轮未运行Many Labs，目标噪声问题状态不变。
- REV-07：严格同宽0.532657214043时强桥64新人数、direct256；弱桥在256人仍不能达到width .6。优势来自声明的loading，非普遍省成本。
- REV-08：概率/矩阵/有限枚举为已有工具；本轮没有解决贡献新颖性及全部近邻比较。
- REV-09：新线性moment估计器可有signed weights，不证明原simplex类在所有方法中最优。
- REV-10：5400世界覆盖27个预设几何×参数分布×噪声分布；target规则实际枚举W并核对目标gain。去Gaussian部分得到理论与域内实现证据，线性和有效输入限制仍在。
- REV-11：新分支、冻结配置、代码793f7ae、源快照、哈希和报告单独保存；旧实验没有被覆盖。
- REV-12：独立记录pointwise/五前缀区间、actual stopped/full prefix，以及interval miss与scientific bad release；停止由设计决定，不能推广为任意outcome-adaptive停止。

所有状态维持前一理论里程碑，REV-10仍是partial_evidence；没有resolved。经验覆盖不代替概率定理，线性模型/已知输入/现实应用缺口保留。


## 2026-11-07 消融审计、结构化分支结果及主目标修正

已有消融完成只读核查；原设计非高斯分支运行及全局成本诊断完成，明确其缺实际历史数据。作者现将主目标改为有限新增预算缩短历史区间，并比较与高预算直接目标参考的点差和方向结论；HISTORICAL-BRIDGE-WORKFLOW01已冻结待执行。不再以同精度省钱验收，全部12项状态保留。

已回顾全部REV-01至REV-12，状态均未更改。详细证据见 [消融盘点](ABLATION_AUDIT_20261107.md)、[结构化分支报告](results/main_theorem_workflow01/RESULTS.md)、[成本与任务诊断](BRIDGE_COST_DIAGNOSIS_20261107.md)。权重与几何消融已有，局部诊断错误单列，负结果保留。原设计分支无实际历史Y，不能作为一般机制复用主实验；全局规划亦无法逆转当前198/200设计的同价direct成本差距。手设强弱载荷旧结果不再承担主实验结论，预算扩展仅smoke。

新目标由作者确认：有限新增预算缩短历史区间，同时报告与高预算直接目标参考的点差及方向结论。协议 [HISTORICAL-BRIDGE-WORKFLOW01](HISTORICAL_BRIDGE_WORKFLOW01.md) 已于cdc146b冻结；4次实际历史观测共享，主新增预算4，所有0/1/2/4/8预算保留，参考64次独立未来目标观测不是真值。当前未报告运行结果，不预设优势。

新固定要求：每次实验启动前预估耗时和资源，小规模测速后更新full估计，长任务留出租实例选择。本轮预告smoke5–15秒/full1–3分钟CPU，实际时长待记录。REV-02、04、05、06、08、09等仍不由该线性合成分支解决；原稿未自动更改。


## HISTORICAL-BRIDGE-WORKFLOW01 完成回顾

已再次回顾全部REV-01至REV-12，状态全部保留。协议cdc146b、实现ba7f3dc、报告b173f7d；200设计x200世界，840000端点，实际63.18秒（事前估60–120秒），10测试和19运行检查通过。独立重算最大误差6.75e-14。

主预算4时，target相对历史全宽缩短比例中位46.79%，random21.21%、logdet37.69%；target在200/200设计比random更窄、193/200比logdet更窄。支持所测合成线性已知矩模型中的有限预算信息增益，没有进行总体显著性检验。

与64次目标参考点差不超过.30占61.275%；参考定向的30658世界中，同向4841、仍不足25816、反向1，更强的方向结论接近目标未达到。同预算direct真实MAE .1817低于target .2930，所有对照保留。双方不足、全体有用同向、条件描述比例及真实覆盖分开报告。

详见[完整报告](results/historical_bridge_workflow01/RESULTS.md)。REV-01/07/10/12新增限定证据，其余缺口仍在。新主实验与原始消融审计已完成。后续理论优化需区分信息不足与置信界保守性，新增形式化范围另行说明，不修改阈值来制造成功。


## 消融讨论续接

作者已接受历史主实验的有限预算区间缩短结论，本轮收束。已有权重、几何与新选桥策略对照保留；下一组建议优先讨论机制集合不确定性如何影响区间与可靠性，尚未启动新实验。具体盘点和三组输入建议见[消融审计](ABLATION_AUDIT_20261107.md)。

REV-02新增理论判断：同一设计输入、候选simplex与失败预算下，min_a R2(a) <= R2(a(Y)) <= R∞(a(Y))；中间只是数值，最左全局设计最优才具相应合法保证。不能通过实验找到R∞发布而这一最优R2拒绝的同条件例子；某个较差固定权重或局部解不在此结论内。跨流程不同置信预算分配需重新核对。该解释不等于R∞实用角色已经解决，全部12项状态保持。


## MECHANISM-UNCERTAINTY-ABLATION01：执行与真实实验准备

用户已授权一般U/L/H流程的机制集合消融：calibrated_U、proxy_point负控制、oracle真坐标，共同数据和随机桥路径，R2主结果、Rinf次结果，同权重诊断与各自优化分开。协议4528e20、实现ca2056b；运行前已回顾全12项，smoke27世界3.093秒并通过10项测试、18项检查及独立重算。full事前预估由3–8分钟更新为2–4分钟/4CPU，告知用户后启动。结果及after回顾另记，不以已启动改变review状态。

真实实验当前只做准备，详见[审稿要求与开跑清单](REAL_EXPERIMENT_REVIEW_PREPARATION.md)和[机器状态](real_experiment_readiness.json)。目前NOT_READY_FOR_REAL_RUN：真实机制输入、有效条件、estimand/独立性/已见结果审计及新协议尚不完整。先准备真实输入到证书案例，再准备ManyLabs目标噪声诊断，最后在条件满足时准备候选实验揭示回放。没有运行新的真实效应估计、模型拟合或回放。

REV-04/05仍open：微贷ATLAS未获资格、n_computed=0，不能称为成功拒绝；条件worked case与真实校准保证分层。REV-06仍partial：原ManyLabs结果为有噪参考基线，控制目标噪声尚未新跑。REV-07/10/11/12分别保留比较、模型输入、版本和评价口径缺口；REV-01/02/03/08/09亦未关闭。全12状态保留。旧计划中的七研究、19校准单位及盲编码条件不能被当成已完成事实。


## MECHANISM-UNCERTAINTY-ABLATION01：完成后回顾

1800世界完整运行75.79秒（预告2–4分钟/4CPU）；10项测试、18项运行检查通过。独立重算43200权重/公式状态及86400停止输出，几何最大差6.66e-16，估计与端点差为0；根复核34个源码/原始结果/报告哈希并检查图像，另一个代理只读聚合结果相符。

主预算288人、R2：calibrated和oracle各1800/1800覆盖，proxy1798/1800；未显示明显欠覆盖，不因负控制结果好而换seed或改噪声。bridgeable三者平均全宽分别.421914/.309321/.310244；阈值.2时calibrated发布242/600，proxy566/600，oracle575/600。结果量化集合不确定性的精度和发布代价，不证明忽略集合一定实证失败，也不使proxy具有理论保证。

- REV-01：固定单世界输入、权重和半径分解已保存；不代替作者可读性审阅。
- REV-02：全部设计型权重；Rinf次结果没有提供结果适应选择用途。
- REV-03：数字明确归属一般U/L/H计算证书及三个输入身份；未改摘要。
- REV-04：合成集合消融量化宽度与发布代价；proxy在主预算仍覆盖1798/1800，未展示明显欠覆盖；真实U/LH来源继续open。
- REV-05：本轮不运行真实数据，微贷资格失败未改变；真实准备报告已列开跑要求。
- REV-06：本轮未运行ManyLabs目标噪声诊断；真实准备报告列为独立待冻结任务。
- REV-07：共用观测、桥路径和预算的组件比较已完成；不证明相对direct/ExAtlas优势，真实成本仍缺。
- REV-08：机制消融未解决相关工作与新颖性。
- REV-09：保留simplex；没有证明该估计器类普遍最优。
- REV-10：本轮固定random路径，不验证新W或旧logdet选桥定理；去高斯已有范围保持。
- REV-11：本轮区分主方法、proxy负控制、oracle及一般U/LH分支；全稿命名仍未修完。
- REV-12：固定证书、停止实际输出、拒绝outer、零发布NA、空区间与成本分母已独立核对；没有真实验证。

全部12项状态保持，没有resolved。详见[结果与范围](results/mechanism_uncertainty_ablation01/RESULTS.md)和[完成核验](evidence/mechanism_uncertainty_ablation01_complete.json)。真实实验仍处于[准备阶段](REAL_EXPERIMENT_REVIEW_PREPARATION.md)，没有新真实数据运行。
