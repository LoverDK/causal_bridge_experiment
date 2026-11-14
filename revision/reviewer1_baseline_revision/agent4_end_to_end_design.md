# Agent 4：完整流程基线是否需要新增实验

日期：2026-11-08。只读评估；未修改 TeX/Git/实验仓库，未生成新 world、未拟合、未执行模拟。本文的新计算仅读取保存的 CSV、JSON 和 gzip，比较记录及校验哈希。

实验仓库 E = `C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild`。

## 决策

**本轮应先统一重分析 Appendix L 的 workflow_full 与 Appendix P 的 ablations_full，不应把新增模拟作为修订前提。** 两组证据确实来自相同世界和噪声，不只是形式上类似的协议。现有结果已回答两项限定问题：在相同数据前缀上，权重优化相对 uniform/IVW/nearest-source 是否有贡献；在相同优化权重实现下，targeted/random/nearest/static/direct 采集策略有何取舍。这足以支持具体组件归因及完整合成流程比较。

缺少“每种权重都按自己的半径重新定向采桥”的完整交叉矩阵，**不妨碍上述两项结论**。它只妨碍声称某个完整权重—采集组合全面胜出、交互效应已被识别、或 targeted 对每种权重都有效。应限制这些主张，而不是为找正结果调 DGP。真实基准现阶段评价的是替代预测估计器；不能把它们接在此处当作一般 ATLAS 已完成真实端到端验证。

如 root 确实需要新的归因行，最小可选工作是在**现存 optimized-targeted 冻结路径**上追加 uniform/IVW/nearest-source 的确定性重放；不增加独立世界、不调整目标、机制、阈值或预算。它仍是共同路径权重归因，不是每种权重自适应选桥算法的完整比较。此项是 helpful，不是 necessary。

## 已检查材料和可追溯性

- 当前稿 `D:/study/zzh科研/reviewer1-sprint/causal_lab_proposal_subpapers_tex_iclr2027/01_reviewer1_blue.tex`：完整 workflow 约 1410 行起，匹配权重约 1679 行起；主文约 355 行已限定组件贡献，并报告 direct 更便宜。
- 前审计 `D:/study/zzh科研/reviewer1-sprint/rebuttal_work/reviewer1_experimental_evidence_audit.md`：E02、E05–E12。
- E 的 `AGENTS.md`；`current_method/docs/ablation_protocol.md`；`current_method/atlas_new/workflow.py`、`ablations.py`、两个 runner、`audit_ablations.py`。
- `current_method/results/workflow_full/{run_manifest.json,workflow_records.csv,plans.jsonl,world_audits.jsonl}`。
- `current_method/results/ablations_full/{run_manifest.json,records.csv,plans.jsonl.gz,independent_audit.json}`；以及保存的 stopped/fixed-budget 汇总。
- `revision/evidence/ablation_audit_20261107/ablation_code_audit.md`。

## L/P 可统一：逐项核实

1. **实验单位和 seeds 完全一致。** 两个 manifest 都是 seed `2026091801`，linear/quadratic/sinusoidal × supported/bridgeable/unreachable × 每格200，共1,800个独立世界。P 只是 profile 和报告配置不同。不得把两组世界相加成3,600个样本。
2. **历史、菜单和机制信息一致。** 均4个历史来源、6个候选桥，2维机制；每历史来源800人；最多3桥、每桥96人；199个独立带机制标签的校准 archives；proxy scale .012；解析给定相同 L/H。`make_world` 使用 SeedSequence `[seed, surface_id, scenario_id, replicate, 0]`，故校准误差、机制抖动和测试proxy完全共用。
3. **结果流一致且规划看不到它们。** `collect` 使用 `[seed, surface_id, scenario_id, replicate, 10, token]`；同 source、同 world 给相同平衡双臂试验。random 顺序使用 token 20。L 的 `plan` 只接设计；P 的 `fit/common_order` 也只接设计。P 预生成全部候选的观测是 fixed-budget counterfactual 评分，代码没有把它传给 fit/order；stopped输出通过相同 `execute` 重建。direct 是独立 target batch token 100+batch，不能说与桥接使用相同个体或同噪声实现；其DGP、单位成本和随机实验尺度相同。
4. **预算、科学阈值、误差预算一致。** 报告预算0/96/192/288；delta .2/.3；eta=zeta=.05。R2 weighted multiplier 为 `sqrt(2 log(2*4/.025))`，refusal coordinate multiplier 为 `sqrt(2 log(2*10/.025))`；Rinf为 `sqrt(2 log(2*10/.05))`。P直接调用相同 `multipliers`，因此同certificate内可配对。direct无需机制预算，使用总.10跨3 looks的 multiplier；是共同每policy路径覆盖下界.90，而不是每个罚项都完全相同。
5. **证书及求解器版本一致。** 两个 manifest 的 `atlas_new/workflow.py` SHA都为 `4c9a2185beb2b47b6ef289498b15136966bb03fc2318214e013c50591782e327`，core SHA都为 `fe91cb77b425d48d435ef295973976449747182051d35aded01b1332e7fcd59b`。P minimum分支直接调用同 `optimize`：uniform/best vertex多起点，70次SLSQP，ftol 1e-8，可行fallback。没有全局最优证书。
6. **不是只靠manifest推断：重新检查了保存结果。** 本次新只读比较 P 的 optimized__minimum/R2/random、nearest 与 L 的 r2_random、r2_nearest，共28,800行（每顺序14,400）。按 world+tolerance+budget 配对；radius、estimate、error、width、new_n 的最大差全为0；release、bad_release、covered、path_covered、certificate_covered、joint_set_covered全为0个不一致。CSV只读比较耗时1.50秒。
7. **压缩计划完整。** P的原 `plans.jsonl`现为`plans.jsonl.gz`，不是丢失结果。本次解压流读取172,800行；SHA `32b94f7602476145fa60cd98a9ee025e7c127b15456291ca29a68ad80d5ab0e3`与manifest中原计划一致，耗时.31秒。保存的 independent_audit 已独立检查172,800计划、345,600停止状态；半径重算最大误差2.22e-16，停止重建5.11e-15，成本一致。

## 已有比较究竟识别什么

**匹配权重归因已充分。** P已包含4权重 × random/nearest两条共同路径 × R2/Rinf，且另有三个几何bound。共同prefix是控制变量，避免把权重改变和采到不同数据混在一起。bridgeable/random/R2/.3：optimized发布100%、159.68人；uniform20.33%、283.52人；IVW和nearest-source均0%、288人。同固定288预算的MAE分别.0334和.1405，证书全宽.4224和.7061。nearest顺序也有比较，故不是只挑一种顺序。supported的简单权重已能零新增成本发布、点MAE略好；unreachable全部拒绝，应同时保留。

**选桥归因也已充分，但限定于 optimized refit。** L在相同世界比较 targeted/random/nearest/static/direct。bridgeable/.3时targeted、random、nearest均100%发布，成本117.92/159.68/241.60；direct为96。`.2`时targeted只发布66.5%、成本227.04，direct100%、288，不能把较低花费称为同成功率节约。unreachable采满预算仍拒绝；static不采不发布。targeted是prospective-radius heuristic，不承接logdet greedy的理论近似因子。

**不能把两种归因拼成未经测量的交互结论。** L/P中optimized random/nearest重叠完全一致，可共用一个框架展示。不能从“optimized胜uniform on random”加“targeted胜random under optimized”推出“targeted+optimized相对uniform+自行targeted的差额”；更不能把两项成本差相加。若回答“优化权重和目标导向采集在所测共同世界里分别产生收益”，现有证据足够。

完整4×3矩阵只在以下新增主张出现时成为必要：要估计weight×policy交互；要宣称每种权重的自身targeted策略都输给ATLAS；要选最优完整算法组合。那时应另冻结每种weight对候选的prospective-radius scoring rule、tie-break、每轮重拟合、失败fallback。这个实验改变了不同算法看到的source prefix，回答的已是完整策略问题。

## R2、Rinf 与 selective release 的解释边界

- L和P所有实际权重和顺序都在看evaluation outcomes前由设计决定。因此它们是合法design-measurable R2应用；使用Rinf的行展示一种更保守证书，不展示outcome adaptivity净收益。
- 对同一候选类、同bias bound、同失败预算与乘子，全局设计最优R2不可能被仅仅改成Rinf后从拒绝变为发布。当前SLSQP不证明全局最优；不同模式的有限轮次分配也不同，不能未经核对直接作数值支配论证。
- 保护任意outcome-adaptive权重是定理能力，不能由此声称该完整workflow实际利用了结果适应性。Panel B是selection protection诊断，不是这里的端到端效用比较。
- 名义.90是**每policy有限路径的无条件覆盖下界**。不是在release条件下.90 coverage，也不是所有policies联合.90，也不是任意horizon。
- bad_release应报告 `P(release and |error|>delta)`。可另报告经验selective risk `bad_releases / releases`和released MAE，但没有额外论证就不是条件保证；0个release时二者undefined，不能写0。

## 建议统一重分析协议：不需要新样本

保留原archive和原结果，向新revision子目录写衍生结果；原始manifest、源哈希、配对索引和本次分析命令一并保存。只读L/P，去掉重叠行，标注行来自哪个既有研究、估计器、路径和证书。所有世界和完整9格设计都保留，不因不利结果删格。

第一层固定预算报告：budget0/96/192/288时所有目标的MAE、certificate coverage、**证书全宽2R**；共同prefix内成对比较不同weights。P的plans.gz已保存全部未停止counterfactual评分。L的计划保存了ids/weights/radius，但未保存所有未停止估计，不能把carry-forward stopped CSV误作未停止固定预算评分；如需要其未停止MAE，先检查所需来源观测是否在已有日志/计划中可恢复。

第二层真实停止报告：首次R<=delta或预算耗尽时的release/refusal、all-target MAE、released MAE、实际新增participants、unconditional bad-release、empirical selective risk及分母、整条实际output path coverage。拒绝时的width是Lipschitz outer region，须与2R分列；空集/不一致/无界不伪造为零宽，分别计数。配对单位是world；按surface分层bootstrap或保存的原individual探索性CI，不将86,400/345,600条状态当独立样本。无需重抽已有CI；如加新指标需标注为探索性重分析。

第三层bridge value：相对budget0 archive-only，在相同固定成本下的半径/宽度下降、MAE变化、发布增加；相对random/nearest在同目标阈值下的发布和实际成本联合变化。对direct同时列release、cost、width和risk。报告supported/unreachable负结果；不把带拒绝差异的平均支出当同服务水平的成本优势；成本仅新增participants，未计校准、机制编码和部署。

## 比较器的准入与不能承诺的实证

- optimized/uniform/已知noise-IVW/nearest-source：P中已有，同certificate、同prefix，最直接且公平。IVW忽视系统性transport bias是方法的实际差异；应明确比较的是相同认证框架中的权重规则，不能泛指整个meta-analysis领域。
- random/nearest/targeted/static/direct：L中已有，完整合成政策比较。必须区分nearest bridge policy与nearest-source weights。
- FE/RE：在共享目标estimand和可辩护common-effect或exchangeable random-effects target prediction条件下才是效应/区间公平比较。异质机制构造中普通FE置信区间是加权source平均的CI，并非自动成为target-effect预测区间。若额外施加现有几何证书，FE/known-variance IV权重已被P覆盖；不必重复命名成新baseline。RE若新拟合，应冻结tau²估计、预测target的噪声项与coverage对象；不能只对比一个source均值CI。
- robust PI：必须明确输入类和对象。现有`refusal_envelope`是共同source-compatible Lipschitz outer region；可以报告，不能称为一般sharp smooth-class PI。精确有限位置Lipschitz LP是另一个明确对象，需要同输入域、同不确定性处理、同noise预算；不能把真实Many Labs的training envelope改名成这种因果PI。未定义一般“robust PI baseline”前不启动拟合。
- Many Labs/NSW/microcredit：属于其他预测/重构/资格诊断。当前真实机制联合校准→certificate→桥接→release/refusal→验证尚未闭环；不能拿这些替代估计器benchmark给L/P赋予真实ATLAS验证地位。

## 如决定追加：最小、冻结且不调参的方案

**选项A（推荐备选）：相同targeted路径的权重重放。** 使用L保存的R2 optimized-targeted各world完整stage0–3 ids，追加uniform/known-noise IVW/nearest-source，沿同一路径重新计算既有证书和停止状态。保留两delta、三surface、三menu共1,800既存world；不按看到结果挑bridgeable子集作为唯一证据。将这些行与P/L共同分析，标签明确“fixed optimized-targeted path replay”。这不证明新规则自行选桥的性能。

只使用冻结的既有trial streams：优先从acquisitions和保存计划恢复已存在观测；若缺少某个未采集source结果，记录缺失，root决策后才可按原SeedSequence确定性重建同一source stream。不得另抽seed或新world充当reanalysis。target truth只进入scorer，不能进入权重、排序、threshold或模型选择。保留source、代码、input/output hashes。

smoke仅验证9个预指定world（每surface×menu rep0），不据结果调DGP或判是否值得full；再做全部既存1,800世界。指标完全沿用上一节。若新增基于targeted的uniform等路径，添加一个coordinate/set覆盖审计与同prefix重建检查；不能把旧P验证自动视为覆盖新增行。

**选项B（仅当需要交互主张）：各权重自己的targeted采集。** 4weights×3policies的R2主面板；random/nearest已有，optimized-targeted已有，只缺3种简单权重自身targeted。所有candidate scores用本权重规则、同min-bound和noise预算；先规划全路径再读取Y。额外Rinf只在有明确研究问题时另做，不能为了矩阵对称机械翻倍。继续使用全部冻结world和source streams，全面保留失败。此项新增的是策略计划/重放，仍非独立外部确认。

无必要新增SOTA标签、真实fit或新DGP；也不新增一个试图制造Rinf胜全局design-R2的任务。若审稿人要求外部效度，旧world上的扩矩阵不能满足，应明确把真实机制输入资格作为未完成工作。

## 运行时间与硬件

实际manifest：workflow_full在Windows、Python3.13、4个ProcessPool CPU workers上用153.120秒，包含测试、1,800world计划/采集、验证、2000次bootstrap、图表/写盘；ablations_full为133.806秒，172,800plans、345,600stopped rows，也含测试/报告。两runner把OMP/OpenBLAS/MKL线程设为1，以world为粒度多进程；核心是小矩阵NumPy、SciPy SLSQP和Python/JSON，不使用CUDA。

本机此次只读28,800 overlap配对用了1.50秒，8.65MB gzip解压哈希.31秒，验证了轻量reanalysis吞吐。完整统一聚合含两CSV（约96MB）及131.8MB解压plans，预计**30秒–3分钟**；若新算大量2000次bootstrap或做全计划重建，预计**1–5分钟**。这些是依据既有体量和历史总runtime的保守工程范围，不是已完成新重分析的实测值。

选项A的9-world smoke预计**2–15秒**；全部existing-world targeted固定prefix replay预计**10–90秒计算，含审计/汇总0.5–3分钟**。依据是只有3个简单权重、4stage×1,800world，权重无需SLSQP，显著少于已耗134秒的P工作量。选项B每world每权重最多6+5+4个candidate scores，无SLSQP新增拟合，预计**1–5分钟**含验证/报告；若顺带全重跑原优化workflow，按既有153秒基准给**2–8分钟**。环境、并发负载和Python包差异可能影响，必须先测smoke再更新，不把这些范围说成承诺。

CPU是主要收益点；合理4–8物理核、多world并行可缩短计算，bootstrap/JSON/CSV有串行和I/O部分，不能承诺线性加速。内存足够容纳几十万字典/表行有帮助，流式读gzip可降低峰值。当前代码GPU收益近乎零；不需要租GPU。鉴于已有运行是分钟级，本轮没有基于时间的租机必要。

## 可直接用于rebuttal的结论边界

我们将完整合成workflow与使用同一1,800世界的匹配权重比较统一呈现。相同random/nearest路径的重叠结果逐行一致，允许把weight贡献与acquisition-policy贡献放在一个共享实验框架中解释。优化权重和targeted acquisition各自在明确条件下有益；direct在部分设置成本更低，unreachable menus可耗尽预算仍拒绝，组合几何最小值未增加发布收益。结果支持这些限定的合成组件与政策结论；不支持结果适应性净收益、条件发布覆盖、真实机制校准或完整算法普遍优越。
