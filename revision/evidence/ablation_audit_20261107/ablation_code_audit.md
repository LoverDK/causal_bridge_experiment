# 已有消融与局部机制对照：代码和结果审计

审计日期：2026-11-07。只读已有源码/输出；没有生成新的模拟样本，没有修改旧结果。本文负责实现身份和数值，原稿 claims 与审稿意见的逐项对应由主代理另作整理。

仓库根目录：`C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild`。下列源码和证据路径若未写绝对路径，均相对于此根目录。

## 结论先行

已有**两组完整流程匹配消融**（权重；几何界），另有若干局部机制对照（去机制偏差项、单点机制集、去曲率、选择后保护、联合校准、拒绝、固定证书保留、训练来源数匹配）。不能把所有敏感性、baseline、压力测试都称作消融，也不能说此前只做过两项消融。

1. 权重优化在旧 `U/L/H + simplex` 完整流程的 bridgeable 菜单上确实有效；几何界中 barycentric 比单独 Lipschitz 更有用，但 `min(Bbar, BLip)` 相比 Bbar 没有发布或成本增益。这是可报告的零增益结果，不是需要“修出好结果”的故障。
2. 已有删除 U/曲率的局部实验，但它们没有运行采集—停止流程，所以不能替代完整成本—精度归因。
3. 旧 NSW 的“无拒绝”对照同时缩小机制误差项，并不纯粹只删除拒绝；合成分支的同名对照则确实保留原权重/区间。需要分别标明实现。
4. 找到两处报告/标签问题和一处解释混杂：小样本校准表硬编码 `finite`；operational 的 `assumption_valid` 只描述场景而未描述方法条件；污染噪声方差为 1.63，不能把覆盖下降纯归因于非高斯尾部。前两项只需修表格/元数据及验证，不要求重跑所有 Monte Carlo。
5. 当前新矩阵 moment / target-next-W 选桥分支没有 simplex、Bbar、BLip 这些模块。旧消融不能冒充新定理的组件消融，也不应机械移植这些并不存在的模块；可继承的是同设计、同信息、同目标精度下比较选桥规则的原则。

## 审计范围和数值可追溯性

本次重新读取并聚合：

- `ablations_full/records.csv`：345,600 条 stopped 记录；`plans.jsonl.gz`：172,800 条计划状态；独立实验单位只有 1,800 个 world。
- `full/joint_calibration_records.csv`：36,000 条；`full/operational_records.csv`：9,600 条。
- `full_plus/plus_calibration_sensitivity_records.csv`：72,000 条；optimizer audit 120 条。
- `real_supplement/holdouts.csv`：570 条；`matched_archive_size.csv`：5,700 条（57 个目标，每目标 100 个子集，非 5,700 个独立目标）。
- `legacy_audits/results/nsw_method_error_records.csv`：每方法 1,680 条；synthetic baseline raw CSV：四场景每方法 300 条。
- `current_method/exatlas/stress_records.csv`：七条件每条件 200 条。

原始 CSV/JSON 不含单次抽样结果的 panel A/B、selection、correlation、heavy-tail 和 11-entity calibration，只能核对已保存聚合数值、分母、代码和公式；本审计没有伪称独立恢复这些未存储的 draws。

可重复聚合脚本：

- `C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/ablation_audit_recompute.py`
- `C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/ablation_local_recompute.py`

衍生数据目录：`C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/ablation_audit_data/`。其中 `audit_summary.json` 和 `local_summary.json` 给审计总量、精确数值及元数据核验；其它 CSV 是从旧原始记录重算的摘要。

## 1. 完整流程权重消融：真实且有用，但作用有条件

**身份**：`current_method/atlas_new/ablations.py:11–23,87–110`，调用 `atlas_new/workflow.py` 的 `objective_parts/certificate/optimize`。这是后期的通用 U/L/H 证书实现，不是 legacy prototype，也不是现在的新 moment 矩阵方法。

**改变**：optimized、uniform、inverse-noise-variance、nearest-proxy-source 四种权重；都使用 `min(Bbar,BLip)`。IVW 使用已知 DGP noise variance，不是从目标结果估计。

**保持不变**：同一 world 的校准、proxy noise、每来源试验随机流、来源前缀、证书和阈值；桥接次序事先固定为 random 或 nearest。不会让每种权重各自重新选择桥。因此真正隔离的是“在同一批数据上的权重”，不是“各算法重新获取不同数据”的效果。

**设计**：三函数 linear/quadratic/sinusoidal × 三菜单 supported/bridgeable/unreachable × 每格 200 world；4 个旧来源各 800 人，6 候选，最多采 3 桥，每桥 96 人，199 校准 archives，eta=zeta=.05；threshold 为半径 .2/.3。协议明确是复用 workflow_full DGP/seed 的 post-review attribution，不是独立预注册确认。

以下为 bridgeable + random，三函数等权合并，共 600 world；成本是实际新增人数均值，最大 288。

| 证书/阈值 | 权重 | 发布率 | 成本 |
|---|---|---:|---:|
| R2 / .2 | optimized | 38.50% | 261.44 |
| R2 / .2 | uniform | 1.33% | 288.00 |
| R2 / .2 | IVW / nearest source | 0% / 0% | 288 / 288 |
| R2 / .3 | optimized | 100% | 159.68 |
| R2 / .3 | uniform | 20.33% | 283.52 |
| R2 / .3 | IVW / nearest source | 0% / 0% | 288 / 288 |
| Rinf / .2 | 四规则 | 全部 0% | 全部 288 |
| Rinf / .3 | optimized | 31.83% | 244.96 |
| Rinf / .3 | 其余三规则 | 全部 0% | 全部 288 |

在共同最终预算 288 下，R2 的全目标 MAE / **证书全宽**：optimized .033389/.422440；uniform .140518/.706055；IVW .361693/1.109683；nearest .130703/1.020809。注意这里是固定预算的证书宽度；stopped CSV 的 width 在拒绝时会转为 outer refusal region，不能混为一列比较。

已有 paired bootstrap（本次读取未重抽 bootstrap）给 R2/.3 optimized−uniform：发布差 +.796667，95% 区间 [.7700,.823333]；成本差 −123.84，区间 [−128.32,−119.36]。这些是世界配对、按函数分层的探索性 individual CI，不是多重比较后“全面优越”声明。

**负面/边界结果**：nearest bridge order 的 R2/.3 optimized 发布 100%、成本 241.60，而其他权重 0%；.2 时所有权重都拒绝。supported/random/R2/.3 中 optimized、uniform、IVW 全部无新增成本即发布，但 uniform/IVW MAE .014865，小于 optimized .015302。unreachable 菜单全部变体不发布。Rinf 比 R2 更保守；两者有效条件不同，不能只当同一个无条件界的优劣排名。

**支持**：旧 DGP 中，在同数据前缀下优化证书目标有明显发布/成本收益。**不支持**：任意函数/菜单上点估计都最好、桥接必然比直接目标试验便宜、新 moment 算法各组件有效。

**重跑建议**：无需因 already-supported MAE 略差而重跑；保留负结果。若未来主稿仍依赖这个通用分支，可在独立冻结 DGP 验证可迁移性；不能用调函数得到更好结果替代原结论。

证据：`current_method/results/ablations_full/{records.csv,plans.jsonl.gz,paired_differences.csv,run_manifest.json}`；`current_method/docs/ablation_protocol.md`；本次 `stopped_recomputed.csv`、`fixed_recomputed.csv`。

## 2. 完整流程几何界消融：Bbar 有用，min 的增益基本为零

**改变**：分别优化 Bbar、BLip 和 min(Bbar,BLip)。其余设计、随机流、共同来源前缀、统计罚项和阈值与上一项相同。另在 min 选择的**同一组权重**上同时计算三个界，以区别界的紧性与重新优化权重的效果。SLSQP 无全局最优保证；保存的全部计划均 `global_optimum_certified=False`，solver failures 总和为 0。

bridgeable/random/R2 中，min 与 Bbar 的结果完全相同：阈值 .2 发布 38.5%、成本261.44；.3 发布100%、成本159.68。BLip 在两个阈值均发布0%、成本288。共同最终预算288的证书宽度：min/Bbar .422440，BLip .903001。

跨所有函数、菜单、次序、证书、阈值和 reporting budgets，min 与 Bbar 的 **57,600 对 stopped 状态，发布差异 0、成本差异 0**。其中4,676对半径有数值差别，最大绝对半径差 .0118036。计划状态按 cell 计算的最终预算平均全宽改善最大是 sinusoidal/unreachable/random/R2 的 **.0091162**；全部stage最大平均全宽改善 .0097727。不要误写成完全每个区间相同。

同权重诊断：BLip 更紧的状态比例，在 sinusoidal/unreachable 为42.5%，quadratic/unreachable为26.34%；但改进很小且菜单仍不能发布。linear各菜单0%，supported所有函数0%。这解释了“理论上取最小值合理，但本 DGP 中决策收益几乎没有”。

**支持**：此 DGP 对 barycentric 几何的贡献有归因证据；组合界可偶尔微调半径。**不支持**：组合界显著提升发布率或节约成本。

**重跑建议**：不为取得正结果重跑。保留/缩小 min 的经验 claim 即可；若研究问题专门要求它的实质收益，应事前解释现实中哪些几何会让两个界互补，另设独立实验，而非事后挑场景。

证据同上；本次 `min_vs_barycentric_width.csv`、`same_weight_recomputed.csv`、`audit_summary.json`。原稿 `01.tex:1655–1697` 已如实报告这项零收益。

## 3. 局部删除机制误差项：原稿 Figure 2A 的真正消融

**源码**：`paper_original/run_operational_experiments.py:145–199` 的 `simulate_panel_a`。保留相同 Gaussian noise 和中心估计，仅从全宽 `2(.3+1.96×.1)` 删除机制偏差项 .3，成为 `2(1.96×.1)`；扫描隐藏 shift h∈[0,.5]。每 h 为20,000次，邻近 h 共用随机数。

在 h=.30：semantic sampling-only 覆盖 **.151**，保留项覆盖 **.97415**；全宽分别 .3919928、.9919928。在 h=.50（超出宣称 U=[−.3,.3]）即便保留项也只覆盖 .48755；这是假设失效边界，不是定理失败。h=0 时 sampling-only .9488，保留项1，体现额外宽度成本。

**支持**：隐藏偏差存在且有有效上界时，删除偏差预算会欠覆盖。**不支持**：真实机制集能被校准、完整桥接策略节约成本、一般高维最优性。

**建议**：已有局部对照有效；不因界外低覆盖重跑。若展示 full workflow 缺哪个模块，应另说明该图不含采集和停止。

证据：`paper_original/recorded/summaries/operational_panel_a_hidden_shift.csv`。原稿01.tex:1196–1202明确叫 semantic ablation。

## 4. 局部 singleton U / H=0：已有删除模块，但不是完整流程成本归因

**源码**：`current_method/atlas_new/experiments.py:112–195`，尤其149–152。固定四来源、一维二次响应 `tau=.6m+.3m²`、共同world/采样误差；singleton_U 把校准 box 压成 proxy 点；no_curvature 把 H 改成0，再各自优化权重。另有 nominal/extrapolation/proxy_shift/understated_LH/high_noise/bounded_nuisance_bias 六场景、每场景200世界。没有桥接 acquisition。

从9,600 raw记录重算的局部例子：

| 场景/方法 | 覆盖 | 平均全宽 | MAE |
|---|---:|---:|---:|
| nominal robust_Rinf | 1.000 | 1.431711 | .111511 |
| nominal singleton_U | .985 | .687670 | .111105 |
| nominal no_curvature | 1.000 | 1.391057 | .116610 |
| proxy_shift robust_Rinf | 1.000 | 1.472060 | .154990 |
| proxy_shift singleton_U | .870 | .745846 | .155687 |
| understated_LH robust_Rinf | .635 | .434538 | .214170 |
| understated_LH singleton_U | .555 | .360133 | .214202 |

**解释**：去掉不确定性可能让区间显著变窄；nominal 中尚未严重破坏经验覆盖并不能证明此模块不必要，二次函数和宽余量可能掩盖误设。低估 L/H 场景的欠覆盖是有效前提失效。H=0 对真实二次响应不是有效曲率上界，但本例其它项仍可保守覆盖。

**标签问题**：源码174行 `assumption_valid=scenario not in ['proxy_shift','understated_LH']` 仅按场景写值；因而 `adaptive_R2_invalid`、`singleton_U`、`no_curvature` 每方法800条也被标True。该列不可读作“这个方法的所有定理条件均满足”。应改成 scenario_assumptions_valid 并另列 method_assumptions_valid，或明确元数据语义；不需要为了改标签重跑数值。

**建议**：保留为局部负控制，不夸大为完整成本精度实验；若通用U/L/H方法仍是稿件核心，后续可对同一完整流程删模块并报告成本—精度，不能把新 moment 分支硬加这些模块。

证据：`current_method/results/full/{operational_records.csv,operational_frontier.csv,operational_audits.csv}`；本次 `operational_recomputed.csv`。

## 5. 选择后保护：原稿 panel B 和 supplementary selection

这是对统计保护机制的局部控制，不是完整算法 baseline。固定真值0、零机制误差、相同Gaussian source errors，改变 pointwise / simultaneous bound；max-selection 或softmax权重依赖看到的误差。源码 `paper_original/run_operational_experiments.py:202+` 及 `current_method/atlas_new/experiments.py:44–73`。

K128、每规则50,000次：pointwise-after-max coverage **.00158**、全宽3.919928；Gaussian Bonferroni **.95260**、7.092676；theorem Rinf **.99586**、8.266032。softmax温度.25：合法Rinf .99652/8.266032，对照非法design-R2 .49174/3.070642；温度1：Rinf1/8.266032，非法R2 .79786/.643682。

**支持**：任意看到结果后选择权重时，同步保护必要，并有明显宽度代价。**不支持**：所有 design-only R2 都无效；新 moment设计规则是设计可测，不能把此处的非法R2直接当它的失败。

**建议**：无需重跑使负控制好看；保留宽度代价，并给合法固定权重参照避免稻草人解释。

证据：`paper_original/recorded/summaries/operational_panel_b_post_selection.csv`、`current_method/results/full/selection.csv`，原稿1590后的supp-selection。

## 6. 联合校准：两项不同实验，不能混成同一个

### 6a. 旧 source-count grid（真正控制 joint vs marginal）

源码 `atlas_new/experiments.py:88–110`。每rep重新生成199条校准archive；k=4/16/64个来源加1目标，一维绝对Gaussian误差；joint_max、marginal-only、Gaussian union在相同draw比较；测试误差尺度1或**2**。36,000原始记录已重新聚合，每格2000个test。

| k | joint nominal | marginal nominal | Gaussian union nominal | joint ×2 shift |
|---:|---:|---:|---:|---:|
| 4 | .9565 | .7895 | .9585 | .3425 |
| 16 | .9525 | .4295 | .9530 | .0780 |
| 64 | .9510 | .0585 | .9515 | .0005 |

支持联合校准的重要性和交换性边界；不建立真实 U 的校准。证据 `full/joint_calibration_records.csv`；本次 `joint_recomputed.csv`。

### 6b. 11实体、二维 mechanism calibration（后续独立局部审核）

源码 `run_mechanism_calibration.py:34–60`，seed2026092401；固定199×11×2误差一次校准，欧氏范数，2000测试档案；shift为**1.5**。nominal joint=.951、marginal joint=.544；shift joint=.348、marginal joint=.0275。只存summary/calibrator，本次未重抽样。

原稿1618明确说旧 source-count grid 是 separate diagnostic，因此数值并不矛盾。但紧接的 `tab:supp-joint` caption 未明确其shift=2，容易被上一段×1.5误导；建议在caption写旧一维、k+1实体、×2。无需重跑。

证据：`current_method/results/mechanism_calibration/{summary.csv,calibrator.json,run_manifest.json}`。

## 7. full_plus：以敏感性/假设边界/数值审计为主，非完整消融

源码实际是 `current_method/atlas_new/audit_plus.py`，配置 `configs/full_plus.json`。本次搜索当前01.tex，未见full_plus、小校准标签或污染/t3数值直接入稿；不要把仓库补充诊断问题写成已进入论文主结果的错误。

| 项目 | 改变与对照 | 真实结果 | 可支持/限制 | 重跑判断 |
|---|---|---|---|---|
| 相关性边界 | 固定k8、sd=.06… .14，rho0/.3/.7；equal/max/softmax权重；Rinf、diag R2、cov R2 | rho.7固定equal：diag覆盖.749367/半径.099270，cov .993067/.233668，Rinf1/.339656；各n30000 | 错用对角噪声会欠覆盖；结果后自适应时cov R2仍不自动有效 | 无需重跑预期负控制 |
| 尾部形状 | Gaussian vs t3/sqrt3 vs1% N(0,8²)污染；max-abs自适应 | 原Gaussian Rinf覆盖 .994233、t3 .9239、污染.9436；n30000 | t3是等方差尾部对照；污染不是等方差 | 若需纯tail-shape归因，未来另冻结标准化污染；当前保留为scale+tail误设，不自动开新压力实验 |
| 历史残差校准 | 同一distribution半样本校准maxscore/半样本评估 | coverage Gaussian .988333、t3 .979867、污染 .9654；测试n15000 | 经验改善；不是通用非Gaussian定理 | 不可用它替代新moment定理 |
| 校准样本数 | ncal5/9/19/49/99/199/499/999 × k4/16/64；各3000 | n5/9全部inf、覆盖1；n19范围 .944667–.949；n49 .959333–.966；n999 .947–.95 | 小样本可给空洞保证；有限rank导致覆盖非严格单调 | 无需重跑使曲线单调 |
| optimizer诊断 | 120个随机1D/k5 box目标，SLSQP对8000Dirichlet随机权重 | mean(SLSQP−random-best)=−.06798254；最大差−.01193444；随机优胜0；solver失败0 | 优于有限随机搜索；不证明全局最优，更不验证新目标 | 无条件不重跑；新objective需要自己的数值验证 |

**必须修的报告问题**：`audit_plus.py:135` 调用 `calibrated_quantile(np.arange(10),.05)` 后硬编码 `observed='finite'`。本次直接调用纯函数确认inf；`core.py:92–97` 算 rank=ceil(11×.95)=11>10，正确返回inf。`results/full_plus/plus_assumption_boundaries.csv:5` 的finite为生成表错误；其validation_checks的“tiny calibration returns infinite radius”passed却与错误表不一致。改为读取返回值并验证生成的表即可。

**污染方差证明**：源码61行 `.99 N(0,1)+.01 N(0,8²)`，零均值但 Var=.99+.01×64=**1.63**；后续依旧按原sd构造Gaussian界。故低覆盖混合了尾形变化和方差低估。是解释范围问题，不把负结果自动判成实现错误。

证据：`results/full_plus/{plus_correlated_noise.csv,plus_heavy_tails.csv,plus_calibration_sensitivity_records.csv,plus_optimizer_audit.csv,plus_assumption_boundaries.csv,validation_checks.json}`；本次 `calibration_recomputed.csv` 和两个audit summary JSON。

## 8. 旧 no-rejection：两个实现身份，必须分别讲

### 8a. 合成 archive prototype：纯删除拒绝

`legacy_audits/src/causal_atlas_sim/methods.py:419–440` 调原fit后保留 weights、raw prediction、certificate和interval，仅强制发布。故 all-target point MAE应完全一样；这是代码定义，不是“拒绝无效”的实验证据。

从 `legacy_audits/results/extensions/synthetic_baselines_records.csv` 重算，每场景每方法300：

| 场景 | atlas / no-rejection共同MAE | atlas发布率 | no-rejection发布率 |
|---|---:|---:|---:|
| nominal | .138699 | 46.33% | 100% |
| moderate | .230578 | 28.33% | 100% |
| severe | .707439 | 1.33% | 100% |
| high_noise | .162400 | 5.00% | 100% |

正确指标应是发布率—选择后误差/误发布风险，不能期望只删除拒绝降低全目标MAE。无需为相同MAE重跑。

### 8b. NSW reconstruction：同名却混入区间缩小

源码 `legacy_audits/src/causal_atlas_sim/nsw_experiment.py:486–499,554–558`：相同权重、点估计，但无拒绝组还将 representation_term 乘默认 **.75**。因此它同时删拒绝和降低机制误差预算。

raw每方法1680条，重算 atlas vs no-rejection：点预测逐目标最大绝对差0；MAE都 .8615027；acceptance .767857 vs1；reference inclusion .974405 vs .969643；平均全宽5.630257 vs5.274930。不能将覆盖/宽度差纯归因于拒绝。若未来需要真正拒绝消融，保留同一区间仅切gate；可从既有输出重评分，是否需重新拟合取决于新增指标，不必重采集原数据。

这只是同一NSW试验内、heldout local contrast为有噪声参考的重构，非真实跨干预因果真值。

### 8c. 有代码但未见输出的选项

`legacy_audits/src/causal_atlas_sim/formal_experiment.py:107–109` 有 `atlas_no_variance_penalty`（lambda_sigma=0）、`atlas_top4_candidates`（max_candidates=4）。本次在可见CSV/JSON/Markdown输出中未找到这些标识，也未找到formal_records/formal_summary成品。准确措辞是**代码有选项但未见运行证据**，不能断言历史上从未跑过，也不能将其列为已完成消融。

若旧prototype不再是论文算法，不建议为“补齐清单”跑这些旧选项；应先确认对应模块是否还在最终实现中。

## 9. 旧固定证书保留：局部机制对照，不是新的选桥保障

`legacy_audits/src/causal_atlas_sim/extension_bridge.py` 在同一六候选库枚举64子集，共24档案（moderate/severe各12）；固定同一采样law、128 planning draws与2048 reference draws。对照为原 operational weight-family PI 与保留固定原/单点证书、固定Bonferroni allocation的 diagnostic。

旧保存汇总：operational 在24/24档案非单调；moderate平均41.1667条负单步边，severe24.6667；retained在24/24单调，经验gamma约1，72预算检查全eligible/nonvacuous/passed。并不证明原Algorithm1或其adaptive保证；诊断刻意保持nestedness而已。

证据 `legacy_audits/results/extensions/{bridge_set_values.csv,bridge_checks.csv,bridge_summary.csv,bridge_empty_intersections.csv}` 和 `docs/paper/extension_protocol_v2.md`。本次读取已有汇总/代码，未重新draw；建议保留为旧历史理论诊断，不携带成新moment主实验的结论。

## 10. Many Labs训练数量匹配：合理控制但不是ATLAS组件消融

`current_method/run_real_supplement.py:25–84`：相同57来源、同一framing干预和目标参考；比较LOSO、LOCO；为区分移除同国来源与训练量下降，对每目标从LOSO库随机抽与LOCO相同大小的100个子集。seed2026091607，子集选择独立于目标outcomes。

从5700 raw子集记录先按目标平均再总体平均：fixed matched-size MAE **.0799865333**，LOSO **.080043**，LOCO **.080428**；差很小。LOSO median .079357 优于fixed .080043；LOCO median .081980反而不如fixed .080428。不能宣称meta模型普遍优于简单稳健聚合，也不能将5700次计作独立目标来缩置信区间。

支持此数据上的来源组成/训练数量敏感性检查；不支持真实跨干预机制集校准、桥接收益或新moment模块。无需为了扩大差异重跑。

证据 `current_method/results/real_supplement/{holdouts.csv,matched_archive_size.csv,matched_comparison.csv,leakage_checks.csv}`；本次 `manylabs_recomputed.csv`、`local_summary.json`。

## 11. Baseline和压力测试：保留真实负结果，不能冒称完整消融

- **strong synthetic baselines**：旧prototype对ridge/kernel/IVW等。原始重算nominal kernel ridge MAE .119750 < atlas .138699；moderate kernel .181218 < atlas .230578；severe ridge meta .327909 < atlas .707439。high_noise atlas .162400则低于kernel .177187和ridge .172449。说明点准确率非普遍占优；这些baseline不带相同证书，不能以较小MAE推导它们有相同有效发布。应保留、解释指标差异；若换新算法比较必须重做公平接口，不把旧优势或劣势直接沿用。
- **ExAtlas-style composition-only stress**：`current_method/exatlas/run_exatlas_stress.py` 实际导入 `current_method/src/causal_atlas_sim` 的旧prototype。不是 `atlas_new` 新证书，更不是完整ExAtlas（无LLM enrichment/reconciliation/bridge generation）。原始每条件200重算：in-support Ex composable82.5%、released MAE .131370，atlas release41%、released MAE .115830；hidden_shift.75 Ex10%/.215653，atlas11.5%/.202719；observable_shift.75 Ex0.5%/.244227（仅1例），atlas2%/.246829（仅4例）。条件误差基于不同release集合，不能直接宣布谁胜。对应原稿1324明确composition-only。应保留有限范围；若review要完整baseline，需要单独实现和匹配信息而非改名。
- **logdet greedy/exhaustive/random（原panel D；full bridge）**：是策略baseline比较与Gaussian structured theorem核验，不是组件删除；原200个p6/n12/预算4设计，最多枚举495子集。`paper_original/recorded/summaries/operational_panel_d_bridge_design.csv` 与 `current_method/results/full/bridge_records.csv` 是不同实现保存的结果，不应直接混数。新moment theorem正在用原设计库做新的比较，旧logdet信息增益成绩不能替代新目标宽度/成本成绩。
- **anisotropy/complementarity/minimax**：是反例/理论边界/公式相图，不是完整算法消融。`full/bridge_anisotropy.csv` 已给logdet所选target radius .619806反而高于另一候选 .590962；应保留“信息增益不等于目标收缩”的限制，不重跑反例使其消失。
- **NSW real / semi-synthetic / proxy truth**：属于不同truth可用性、不同baseline的benchmark及校准审计；不能因同一目录有no-rejection名称就把整套都叫组件消融。尤其真实参考包含率与半合成已知真值覆盖率必须分开。

## 12. 什么需要改，什么无需重跑

| 分类 | 项目 | 下一步 |
|---|---|---|
| 可直接保留的正证据 | 旧匹配权重；Bbar相对BLip；joint-vs-marginal；选择保护；机制偏差项 | 如实保留并限定实现/DGP/分母 |
| 可直接保留的零/负结果 | min相对Bbar无决策收益；supported简单权重点误差更好；强baseline某些场景更优；unreachable预算用尽；非法条件欠覆盖 | 改claim范围，不按好坏决定重跑 |
| 修报告/标签即可 | small_calibration硬编码finite；assumption_valid含义；joint表caption ×2 vs段落×1.5 | 修生成逻辑、元数据、文字并做确定性检查；本审计未修改 |
| 归因设计需要修正才适合重做 | NSW no-rejection同时缩bias；污染noise方差不匹配 | 若最终论文还需要对应因果归因，再冻结匹配对照；保留旧结果 |
| 尚无运行证据 | no_variance/top4选项 | 先确认最终方法是否仍含该模块，避免补旧算法 |
| 新实现需要新对应证据 | 新矩阵moment target-next-W、非Gaussian有限方差证书 | 采用该实现本身的规则比较；不搬simplex/Bbar/BLip消融 |

“差”至少分三类：方法在该条件下确实不占优、理论前提被故意破坏、实验/报告自身混杂或错误。只有第三类直接要求修实验/报告；前两类是研究结果。

## 核对的源码哈希和限制

`ablations_full/run_manifest.json` 中以下8个source_sha256均与当前文件完全一致：

1. `current_method/run_ablations.py`
2. `current_method/atlas_new/ablations.py`
3. `current_method/atlas_new/ablation_report.py`
4. `current_method/atlas_new/workflow.py`
5. `current_method/atlas_new/core.py`
6. `current_method/configs/workflow_full.json`
7. `current_method/tests/test_ablations.py`
8. `current_method/docs/ablation_protocol.md`

对应布尔结果在本次 `audit_summary.json:source_sha256`。本次没有重新做所有既有文件的全量delivery哈希审计，也没有再次运行完整simulation/Lean；不得据此声称整库已重新验证。

旧 `ablations_full/independent_audit.json` 已存全计划/停止路径数值复建审核，但那是此前审核证据；本次独立完成的是原始文件聚合、匹配状态比较、源码核对和上述8个source hashes。
