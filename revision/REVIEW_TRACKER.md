# 审稿问题跟踪

更新：2026-11-07（Asia/Shanghai）。基线：`7e5841d3f3f22f892233582b9509aad656f3d266`；分支：`codex/reviewer-guided-rebuild`。

本次仅初始化 tracker；尚未运行本轮新实验。已有记录、只读审计与新实验必须区分，没有问题被标完成。 机器可读版本为 `review_tracker.json`，两份同步维护。

## 每轮固定要求

- 每次实验推进前、后回顾全部 review 和 12 个问题。
- 不能用已运行代替已解决；状态由验收证据决定，保留未覆盖问题与负结果。
- 实验重建使用本地Git分支；未经明确安排不向公开实验仓库发布修订记录。

推进前：读全部 review 映射与 12 项现状，记录假设、信息、对照、预算、指标、预期及能/不能回答的问题。

推进后：记录版本、配置、种子、产物和结果，逐项回顾全部问题。将前/后记录分别写入 JSON 的 `round_review_protocol.entries`。未检查的意见沿用状态，负结果保留。

本轮执行协议：[FIRST_WORKFLOW.md](FIRST_WORKFLOW.md)。尚未启动新实验；先 smoke 和单世界轨迹，再检查三类预设情形，理解后才 full。

状态：`open` = 关键修复证据仍缺；`partial_evidence` = 有限证据不足验收；`pending_source` = 写作待最新源；`writing_in_progress` = 最新源已取得、副本改写进行中。本轮不设 resolved。

## 12 个问题

### REV-01 · 引言、首现定义与解释顺序

优先级：P1；状态：`writing_in_progress`。映射：nrhq.W1、nrhq.W2、nrhq.Q1。

已知证据：已有 PDF 及改写候选；nrhq 指出 decision layer、certificate、bridge 等定义前使用。 用户已在本机完成Overleaf克隆。原稿位于 causal_lab_proposal_subpapers_tex_iclr2027/01.tex；基线29e4c0db4a17e72e04d9a1c9b330e81b166c604a，原稿SHA256为ef261e308e3463eb8e54d5de3c0fded1879f58777222f0115a0c5a5f79eaab73。子代理正在同目录创建01_humanized.tex，原稿保留。

缺口：尚无基于最新源文件的修订、语义审查及编译验证；不能标完成。

验收证据：

- 最新源与 prose-only diff；先解释目标、输入、假设和输出，再用术语；贯穿例子和图 1 可独立读懂。
- 数学、引用、数值和限定条件保持准确，编译与逐项阅读通过。

下一步：核查同目录副本的语义、公式、引用、数值及编译结果；通过后提交并同步。

首轮能回答：为方法直觉提供一个可检查的流程例子。

首轮不能回答：最新 Overleaf 已修改完成；一次运行自动修复写作。

依据：`用户 PDF 第 1–2 页`；`nrhq review`。

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

### REV-03 · 摘要数字与证书结果归因

优先级：P0；状态：`open`。映射：WGDN.W1b、nrhq.Q1、nrhq.Q2。

已知证据：95.3% / 0.2% 对应 Gaussian Bonferroni 与未校正区间，不是完整证书效用；Table 15 另列 theorem simultaneous。

缺口：尚无摘要、贡献、图表到具体 bound/policy/code/result 的完整归属及修订。

验收证据：

- headline 数字逐项对应实际方法和设置；Bonferroni 动机例子与完整方法结果分开。
- 摘要实用结论由相应方法直接支持，负结果与范围保留。

下一步：追踪现有数字来源，后续修改摘要及贡献归因。

首轮能回答：本轮实际使用哪个 bound、policy 和评价事件。

首轮不能回答：复现 textbook 选择偏差即证明本方法新增贡献。

依据：`用户 PDF 摘要、Figure 2B、Table 15`；`paper_original/run_operational_experiments.py`。

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

### REV-06 · Many Labs 目标噪声与迁移证据

优先级：P0；状态：`partial_evidence`。映射：WGDN.W2c、WGDN.W2b、nrhq.Q2。

已知证据：halfwidth 含 target_design_variance，属于 noisy reference 的预测噪声；这不等于发现 outcome leakage。 已有 57 目标 CSV 的只读诊断：fixed 目标噪声占总方差中位 98.8774%，random 98.0202%。 δ=.15 时仅留目标噪声，fixed 10/57 的发布决定不变；random 原 6/57 变 7/57。

缺口：缺等目标 n / 固定参考噪声、多 effect families 诊断；当前结果不认证 archive 兼容性。

验收证据：

- 分开 target estimand 与 noisy reference，拆分 archive、transport、target validation 不确定性。
- 完成控制目标噪声的诊断与多效应族评估，基线预测与主证书分别报告。

下一步：首轮保持问题开放；另立 Many Labs 评价口径与目标噪声控制实验。

首轮能回答：合成流程中的证书与评价噪声如何区分。

首轮不能回答：首轮 smoke 解决 Many Labs 目标样本量问题或证明真实迁移。

依据：`paper_original/run_manylabs2_framing.py`；`current_method/atlas_new/manylabs.py`；`current_method/results/full/manylabs_holdouts.csv`；`本会话对已有 CSV 的只读半径分解；非新方法实验`。

### REV-07 · 可行基线、权重收益与完整成本

优先级：P0；状态：`partial_evidence`。映射：nrhq.W4、nrhq.Q2、WGDN.W1a、WGDN.Q1。

已知证据：已有 Appendix P 在共同 random bridge path 下支持部分合成场景的 design-only R2 权重收益，不能归为 R∞ 收益或超越最近前作。 已有汇总中直接 target trial 在若干设置更有利；审计/部署成本未纳入；尚无完整 ExAtlas matched-information 对照。

缺口：缺统一信息、假设、预算、置信水平和停止规则的强基线对照及全部成本。

验收证据：

- 与适用设计权重、稳健聚合、样本拆分、最近前作和直接 trial 比较，明确不可比条件。
- 报告 coverage、错误发布、发布率、宽度、目标误差与成本；保留全部预设场景及负结果。

下一步：首轮先理解已有策略身份和成本；强基线及总成本另立协议。

首轮能回答：单世界中各策略做了什么、花费多少参与者。

首轮不能回答：smoke 证明优越性；弱基线已覆盖 ExAtlas；参与者成本等于现实总成本。

依据：`current_method/results/ablations_full/report.md`；`current_method/results/ablations_full/stopped_summary.csv`；`current_method/results/workflow_full/pooled_summary.csv`。

### REV-08 · I&K、Manski、ExAtlas 与新增贡献

优先级：P0；状态：`open`。映射：nrhq.W3、nrhq.Q1、WGDN.W2d、WGDN.Q3。

已知证据：根代理核实 I&K 已有 pairwise bounded-variation / Lipschitz 参数空间与 target projection；Manski 已有目标集合汇总。 根代理核实 ExAtlas 已有同型重心误差分解、凸组合、阈值拒绝和 bridge 流程。

缺口：缺逐命题符号映射、贡献归属修订、主文比较与匹配近邻实验。

验收证据：

- 按 estimand、信息、假设、目标、采样误差、机制集合和选择规则列已有、推论与新增命题。
- 区分 Theorem 5.3 的 finite-metric sharp 特例与一般 outer region；新增主张有证明或直接实验，并补引用。

下一步：先完成文献/数学映射，再确定贡献与近邻实验。

首轮能回答：提供本实现的具体接口与信息边界供后续比较。

首轮不能回答：流程跑通证明新颖性；优于弱基线等于超越近邻。

依据：`https://arxiv.org/html/2108.06473v4`；`https://doi.org/10.1097/EDE.0000000000001178`；`https://arxiv.org/html/2605.27153v1`；`用户 PDF Theorem 5.3、Eq. 4.1、Appendix C`。

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

### REV-10 · bridge 定理与实际一步 heuristic

优先级：P1；状态：`open`。映射：KoBT.W4、KoBT.Q1、nrhq.Q1。

已知证据：Theorem 5.6 为非自适应 linear-Gaussian logdet 保证，target radius 控制另需 posterior condition-number 条件。 workflow targeted R2 最小化 prospective radius，是一步 heuristic；并非上述 theorem-backed policy。

缺口：缺两种 policy 明确分离及匹配对照；缺非线性/非高斯/异方差/错设下证据。

验收证据：

- 每个 policy 标注目标、信息、假设和适用定理；不把 heuristic 结果当 logdet 保证。
- 定理域内验证，域外另列经验 stress test；共同预算比较 random、radius policy、logdet 等。

下一步：首轮保持实际代码身份；后续 theorem policy 另立实现与实验协议。

首轮能回答：当前一步规则如何选 bridge、更新半径和停止。

首轮不能回答：heuristic 运行验证 logdet 定理；保证扩展到一般非线性因果模型。

依据：`current_method/atlas_new/workflow.py`；`用户 PDF Theorem 5.6、Appendix L.3`。

### REV-11 · 方法命名、旧 prototype 与结果版本

优先级：P1；状态：`open`。映射：WGDN.W3、KoBT.W3、KoBT.Q1、nrhq.W1。

已知证据：主文/附录 ATLAS 命名和旧 prototype 归属存在混淆；仓库已有 current_method、paper_original、legacy_audits 分区。

缺口：尚无全稿图表到实现、policy、bound、保证的完整清单；最新 Overleaf 源未取得。

验收证据：

- 名称统一并首现介绍；图表和摘要结果有 source commit、method_id、bound_id、适用范围。
- 旧 prototype 明确标记，不能支持当前定理的真实有效性。

下一步：首轮记录代码/配置/输出身份；论文图表映射待源文件到位。

首轮能回答：新输出可追溯到哪份代码、配置和方法。

首轮不能回答：旧图表自动属于当前算法；最新 Overleaf 已同步。

依据：`CURRENT_ARTIFACTS.md`；`README.md`；`legacy_audits/`；`用户 PDF 附录和 NSW 叙述`。

### REV-12 · 拒绝对象、停止状态与统计验收

优先级：P1；状态：`partial_evidence`。映射：WGDN.Q2、WGDN.Q3、WGDN.W2b、KoBT.W3、KoBT.Q1、nrhq.Q2。

已知证据：已有 sharp_lipschitz / outer-region 工具和 workflow；有限已知位置的 sharp region 不等于一般机制集合的 sharp region。 联合事件 P(release 且 bad error) 控制不等于给定 release 的条件覆盖。 现有 unreachable 菜单可耗尽预算仍拒绝；提前判无效/转直接 target 仍缺。

缺口：需统一资格失败、已算拒绝、发布、预算停止及空/无界/有限区域记录；统计口径与停止策略仍需核对。

验收证据：

- 每次运行保存输入审计、半径分解、区域类型和停止原因；空集合不误作成功，outer/exact 分开。
- 指标注明分母、eta/zeta 和 joint/conditional 事件；零发布条件风险 undefined；策略切换先定义后评估。
- 每轮前后回顾全部 review，用产物逐项验收，运行成功不直接关闭问题。

下一步：按 FIRST_WORKFLOW.md 先 smoke 和单世界轨迹，核对状态与信息流，再考虑 full。

首轮能回答：工程闭环、状态、信息边界、统计口径和实际停止行为。

首轮不能回答：运行即解决 review；联合错误等于条件覆盖；真实输入可信性、新颖性或普遍优势。

依据：`current_method/atlas_new/core.py`；`current_method/atlas_new/workflow.py`；`用户 PDF Eq. 4.3、Theorem 5.3、Appendix F.7`。

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

