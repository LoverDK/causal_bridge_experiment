"""Independently audit and report the frozen non-Gaussian target-bridge run.

This program reads completed artifacts only. It never imports the simulator,
chooses a new design, or draws samples. Width/cost quantities are deterministic;
Wilson intervals describe Monte Carlo uncertainty in world-level events only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
CELL = ["geometry", "beta_family", "noise_family", "method"]
WORLD = CELL + ["replicate"]
METHODS = ["target_radius", "logdet", "frozen_random", "direct_target"]
GEOMETRIES = ["target_informative", "distractor", "weak"]
FAMILIES = ["gaussian", "rademacher", "student_t5"]
COLORS = dict(zip(METHODS, ["#0F4D92", "#42949E", "#B64342", "#767676"]))
MARKERS = dict(zip(METHODS, ["o", "s", "^", "D"]))
LABELS = dict(zip(METHODS, ["Target radius", "Logdet", "Frozen random", "Direct target"]))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def wilson(successes, n):
    if not n:
        return np.nan, np.nan
    z = 1.959963984540054
    p = successes / n
    den = 1 + z*z/n
    mid = (p + z*z/(2*n))/den
    half = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return max(0.0, float(mid-half)), min(1.0, float(mid+half))


def event_summary(frame, keys, events):
    rows = []
    for key, group in frame.groupby(keys, sort=True, dropna=False):
        row = dict(zip(keys, key if isinstance(key, tuple) else (key,)))
        row["n_worlds"] = len(group)
        for event in events:
            count = int(group[event].sum())
            row[event+"_count"] = count
            row[event+"_rate"] = count / len(group)
            row[event+"_wilson_low"], row[event+"_wilson_high"] = wilson(count, len(group))
        if "width" in group:
            for col in ["width", "path_width", "new_participants", "W", "parameter_component", "noise_component"]:
                row[col] = float(group[col].iloc[0])
                row[col+"_range"] = float(group[col].max()-group[col].min())
            row["mae"] = float(group.absolute_error.mean())
            row["rmse"] = float(np.sqrt(group.squared_error.mean()))
            row["absolute_error_median"] = float(group.absolute_error.median())
            row["absolute_error_q90"] = float(group.absolute_error.quantile(.9))
            released = group[group.released]
            row["released_denominator"] = len(released)
            for event in ["interval_miss_on_release", "bad_release_scientific"]:
                row[event+"_conditional_rate"] = float(released[event].mean()) if len(released) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def audit(records, manifest, raw, cfg, scores, plans):
    checks = {}
    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)
    n = cfg["replicates"][manifest["profile"]]
    stages = cfg["new_batches"] + 1
    check("manifest_complete", manifest["status"] == "complete")
    check("all_raw_manifest_checks", all(manifest["checks"].values()))
    for name, expected in manifest["artifact_sha256"].items():
        check("sha256:"+name, digest(raw/name) == expected)
    for name, expected in manifest["source_sha256"].items():
        check("source_snapshot_sha256:"+name, digest(raw/"source_snapshot"/name) == expected)
    check("all_27_cells", len(records[CELL[:-1]].drop_duplicates()) == 27)
    check("all_four_methods", set(records.method) == set(METHODS))
    check("all_two_modes", set(records["mode"]) == {"prefix", "stopped"})
    check("record_count", len(records) == 27*n*4*2*stages)
    check("unique_record_keys", not records.duplicated(WORLD+["mode", "budget_stage"]).any())
    check("world_denominator_per_group", records.groupby(CELL+["mode", "budget_stage"]).size().eq(n).all())
    check("finite_numerical_outputs", np.isfinite(records[["width", "estimate", "W", "q", "lower", "upper"]]).all().all())
    check("nonnegative_width", records.width.ge(0).all())
    check("width_identity", np.allclose(records.width, 2*records.radius))
    check("cost_identity", records.new_participants.eq(records.actual_stage*cfg["batch_participants"]).all())
    check("common_history_cost", records.history_participants.eq(64).all())
    check("total_cost_identity", records.total_participants.eq(64+records.new_participants).all())
    check("primitive_moment_identity", np.allclose(records.W, records.parameter_component+records.noise_component, rtol=1e-10, atol=1e-13))
    check("W_equals_q", np.allclose(records.W, records.q, rtol=1e-10, atol=1e-13))
    check("pointwise_radius", np.allclose(records.radius**2*cfg["failure_probability"], records.W))
    check("joint_radius", np.allclose(records.path_radius, np.sqrt(stages)*records.radius))
    check("coverage_scoring", records.covered.eq(records.truth.between(records.lower, records.upper)).all())
    check("scientific_bad_release_scoring", records.bad_release_scientific.eq(records.released & records.absolute_error.gt(cfg["scientific_halfwidth"])).all())
    check("interval_miss_on_release_scoring", records.interval_miss_on_release.eq(records.released & ~records.covered).all())
    check("bad_release_subset_interval_miss", (~records.bad_release_scientific | records.interval_miss_on_release).all())
    check("release_rule", records.released.eq(records.radius.le(cfg["scientific_halfwidth"])).all())
    check("width_constant_across_worlds_and_distributions", records.groupby(["geometry", "method", "mode", "budget_stage"]).width.agg(lambda v: v.max()-v.min()).lt(1e-12).all())
    prefix = records[records["mode"].eq("prefix")].copy()
    stopped = records[records["mode"].eq("stopped")].copy()
    check("full_prefix_actual_cost", prefix.actual_stage.eq(prefix.budget_stage).all())
    check("width_never_increases", prefix.sort_values(WORLD+["budget_stage"]).groupby(WORLD).width.diff().dropna().le(1e-12).all())
    lookup = prefix.set_index(WORLD+["actual_stage"])
    restored = lookup.reindex(pd.MultiIndex.from_frame(stopped[WORLD+["actual_stage"]]))
    for col in ["estimate", "width", "W", "lower", "upper", "new_participants"]:
        check("stopped_frozen_"+col, np.allclose(stopped[col].to_numpy(), restored[col].to_numpy()))
    first = prefix[prefix.released].groupby(WORLD).budget_stage.min().rename("first_release")
    expected = stopped.join(first, on=WORLD)
    check("first_release_stopping", expected.actual_stage.eq(np.minimum(expected.budget_stage, expected.first_release.fillna(cfg["new_batches"]))).all())
    computed_path = prefix.groupby(WORLD)[["covered", "path_interval_covered"]].all()
    terminal = prefix[prefix.budget_stage.eq(cfg["new_batches"])].set_index(WORLD)
    check("all_pointwise_prefix_scoring", terminal.all_pointwise_prefix_covered.eq(computed_path.covered).all())
    check("all_joint_prefix_scoring", terminal.all_joint_prefix_covered.eq(computed_path.path_interval_covered).all())
    check("rank_one_score_identity", np.allclose(scores.exact_gain, scores.sherman_gain, rtol=1e-9, atol=1e-13))
    check("gain_is_W_decrease", np.allclose(scores.exact_gain, scores.W_before-scores.W_after))
    for key, group in scores.groupby(["geometry", "method", "stage"]):
        selected = group[group.selected]
        check("single_selected:"+str(key), len(selected) == 1)
        if key[1] == "target_radius":
            check("target_minimum:"+str(key), abs(float(selected.W_after.iloc[0])-float(group.W_after.min())) < 1e-12)
        elif key[1] == "logdet":
            check("logdet_maximum:"+str(key), abs(float(selected.logdet_gain.iloc[0])-float(group.logdet_gain.max())) < 1e-12)
    check("plans_complete", len(plans) == 12 and all(len(p) == stages for p in plans.values()))
    return checks


def attainment(prefix, cfg):
    rows = []
    for key, group in prefix.groupby(WORLD, sort=True):
        group = group.sort_values("budget_stage")
        for threshold in cfg["full_width_thresholds"]:
            hit = group[group.width.le(threshold)]
            ok = bool(len(hit))
            cost = int(hit.new_participants.iloc[0]) if ok else None
            rows.append(dict(zip(WORLD, key)) | dict(full_width_threshold=threshold,
                attained=ok, right_censored=not ok, first_cost=cost,
                actual_consumed_cost=cost if ok else int(group.new_participants.max()),
                cost_to_success=cost, final_available_width=float(group.width.iloc[-1])))
    individual = pd.DataFrame(rows)
    summaries = []
    for key, group in individual.groupby(CELL+["full_width_threshold"], sort=True):
        row = dict(zip(CELL+["full_width_threshold"], key))
        row.update(n_worlds=len(group), attained_count=int(group.attained.sum()),
                   failed_count=int((~group.attained).sum()), attained_rate=float(group.attained.mean()),
                   failed_rate=float((~group.attained).mean()),
                   first_cost=float(group.first_cost.iloc[0]) if group.attained.all() else np.nan,
                   actual_consumed_cost=float(group.actual_consumed_cost.iloc[0]),
                   final_available_width=float(group.final_available_width.iloc[0]),
                   deterministic_design_quantity=True)
        summaries.append(row)
    return individual, pd.DataFrame(summaries)


def md_table(frame, columns, decimals=4):
    def val(v):
        if pd.isna(v): return "未达标 / NA"
        if isinstance(v, (float, np.floating)): return f"{v:.{decimals}f}"
        return str(v)
    return "| " + " | ".join(columns) + " |\n| " + " | ".join(["---"]*len(columns)) + " |\n" + "\n".join(
        "| "+" | ".join(val(v) for v in row)+" |" for row in frame[columns].itertuples(index=False, name=None))


def figures(widths, summaries, stopped_summary, path_summary, out):
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 14, "axes.spines.right": False, "axes.spines.top": False,
        "axes.linewidth": 1.8, "legend.frameon": False, "pdf.fonttype": 42, "svg.fonttype": "none"})
    def save(fig, stem):
        fig.savefig(out/(stem+".pdf"), bbox_inches="tight", facecolor="white")
        fig.savefig(out/(stem+".png"), bbox_inches="tight", facecolor="white", dpi=300)
        plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.4), sharex=True, sharey=True)
    for ax, geometry in zip(axes, GEOMETRIES):
        for method in METHODS:
            d = widths[(widths.geometry == geometry) & (widths.method == method)].sort_values("budget_stage")
            ax.plot(d.new_participants, d.width, color=COLORS[method], marker=MARKERS[method],
                    lw=2.3, ms=6, label=LABELS[method], linestyle={"target_radius":"-", "logdet":"--", "frozen_random":":", "direct_target":"-."}[method])
        for threshold in [.4, .6, .8]:
            ax.axhline(threshold, color="#CFCECE", lw=.8, zorder=0)
        ax.set(title=geometry.replace("_", " ").title(), xlabel="New participants", xticks=[0,64,128,192,256], ylim=(0,1.85))
    axes[0].set_ylabel("Full interval width")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower center", ncol=4, bbox_to_anchor=(.5,-.02))
    fig.suptitle("Fixed-design cost–precision curves (no Monte Carlo error bars)", y=1.01)
    fig.tight_layout(pad=1.5, rect=(0,.06,1,1))
    save(fig, "cost_precision")
    combos = [(b,n) for b in FAMILIES for n in FAMILIES]
    combo_labels = [f"{b}/{n}" for b,n in [("G","G"),("G","R"),("G","T"),("R","G"),("R","R"),("R","T"),("T","G"),("T","R"),("T","T")]]
    terminal = summaries[(summaries["mode"] == "prefix") & (summaries.budget_stage == 4)]
    panels = [(terminal,"covered","Final full prefix"), (stopped_summary,"covered","Actual stopping point"),
              (path_summary,"all_joint_prefix_covered","All five adjusted intervals")]
    fig, axes = plt.subplots(3,3,figsize=(17,12),sharex=True,sharey=True)
    lowest = min(float(data[event+"_wilson_low"].min()) for data,event,_ in panels)
    for row,geometry in enumerate(GEOMETRIES):
        for col,(data,event,title) in enumerate(panels):
            ax=axes[row,col]
            for k,method in enumerate(METHODS):
                d=data[(data.geometry == geometry)&(data.method == method)].set_index(["beta_family","noise_family"]).loc[combos]
                rates=d[event+"_rate"].to_numpy()
                low=d[event+"_wilson_low"].to_numpy(); high=d[event+"_wilson_high"].to_numpy()
                ax.errorbar(np.arange(9)+(k-1.5)*.16,rates,yerr=np.array([rates-low,high-rates]),
                    fmt=MARKERS[method],color=COLORS[method],ms=4,capsize=2,lw=1,label=LABELS[method])
            ax.axhline(.95,color="#272727",ls=":",lw=1)
            ax.set(xticks=range(9),xticklabels=combo_labels,ylim=(min(.94,lowest-.005),1.003))
            ax.tick_params(axis="x",rotation=45,labelsize=10)
            if row == 0: ax.set_title(title)
            if col == 0: ax.set_ylabel(geometry.replace("_"," ")+"\nCoverage")
            if row == 2: ax.set_xlabel("Parameter / noise family")
    fig.legend(*axes[0,0].get_legend_handles_labels(),loc="lower center",ncol=4,bbox_to_anchor=(.5,-.005))
    fig.suptitle("World-level coverage with pointwise 95% Wilson intervals\nG: Gaussian; R: Rademacher; T: standardized Student-t5",y=1.01)
    fig.tight_layout(pad=1.5,rect=(0,.035,1,1))
    save(fig,"coverage")


def write_report(out, raw, manifest, cfg, summaries, stopped, paths, widths, attainment_summary, trajectory, trace, checks, matches):
    final_width=widths.pivot(index=["geometry","method"],columns="budget_stage",values="width").reset_index()
    final_width.columns=["geometry","method","n=0","n=64","n=128","n=192","n=256"]
    compact_attain=attainment_summary.drop_duplicates(["geometry","method","full_width_threshold"])
    compact_attain=compact_attain.pivot(index=["geometry","method"],columns="full_width_threshold",values="first_cost").reset_index()
    compact_attain.columns=["geometry","method","width≤0.4","width≤0.6","width≤0.8"]
    point=summaries[summaries["mode"].eq("prefix")]
    coverage_range=lambda d,e:f"{d[e+'_rate'].min():.2%}–{d[e+'_rate'].max():.2%}"
    misses=int(point.interval_miss_on_release_count.sum())
    bad=int(point.bad_release_scientific_count.sum())
    n=cfg["replicates"][manifest["profile"]]
    example=trajectory[(trajectory.method=='target_radius')&(trajectory['mode']=='prefix')].copy()
    example["selected"]=example.selected.fillna("仅历史")
    texts=["# 非高斯目标区间选桥：RUN01 结果\n",
        "**核心结果：在 target_informative 和 distractor 两个预设几何中，目标半径桥接用 64 名新增参与者，直接目标实验用 256 名，得到相同的完整区间宽度 0.532657214043。新增人数减少 75%。** 这来自事先给定的 x=(2,0,0) 桥接 loading；不是普遍性结论。weak 场景桥接采满 256 人后区间仍宽于 .60，直接目标实验可以达到该精度。这里是预算内未达到预设精度，不是定理失效或估计错误。\n",
        "本轮检验的是已知二阶矩、固定线性设计下的目标区间选桥。它把实际两臂观测、矩估计、区间、逐候选选择、采集与停止连接起来；不是原一般 U/L/H 工作流的重新验证。全部预设的 27 个几何×参数分布×噪声分布单元均保留。\n",
        f"输入：`{raw.relative_to(REPO).as_posix()}`；profile={manifest['profile']}，seed={cfg['seeds'][manifest['profile']]}，每单元 {n} 世界，共 {27*n:,} 世界，四方法、两种记录模式、五前缀，共 {27*n*40:,} 行。原始运行源提交 `{manifest['git_revision']}`；其源快照及原始产物哈希由分析程序核对。\n",
        "## 先解释一次实验\n",
        "一次世界先生成一个共享的随机参数 beta，再生成两项各 32 人的历史实验。每次新实验有处理/对照各 32 人；个体噪声标准差为 0.5，所以 ATE 差均值噪声方差是 1/64。四方法共享相同历史、先验矩和真参数；相同实验身份共享同一个配对观测。不同新实验使用独立参与者和噪声流。桥接向量与 V0 均为 synthetic_known。真参数只进入生成器及评分，不进入选桥器。\n",
        "主半径为 R=√(W/.05)，完整宽度为 2R；W=dᵀV0d+Σa²v。target_radius 枚举本轮剩余候选的更新 W，选最小者。权重、路径和宽度仅由设计决定，观测会改变点估计，但不会改变这条预先确定的路径。以下单世界固定为 distractor / Gaussian / Gaussian / replicate 0，未因结果好坏而挑选。\n",
        f"该世界真实目标效果（仅评分可见）为 **{trace['scoring_truth']['target']:.6f}**。完整逐步数值、已观察效果、权重和分解见 `single_world_trajectory.csv`；处理与对照均值、采集身份和样本量见 `single_world_observations.csv`。\n",
        md_table(example,
                 ["budget_stage","new_participants","selected","estimate","width","parameter_component","noise_component","released"]),"\n",
        "主停止规则第一次 R≤.30 即停止；stopped 后续预算行只是同一已停止输出的冻结视图。完整 prefix 会继续采满四批，专门用于同成本前沿；它不是已停止策略实际看过的数据。\n",
        "## 同成本完整区间宽度\n",
        "下表横轴是新增参与者，另有共同的 64 名历史参与者。费用只按人数计，不包括现实校准、审计、部署费用。所有分布组合和世界具有相同设计，因此同一几何/方法/预算的宽度完全相同：这里没有 Monte Carlo 成本或宽度置信区间，也不能把 200 次重复当作 200 次独立的设计优势证据。\n",
        md_table(final_width,list(final_width.columns)),"\n",
        "![成本与精度](cost_precision.png)\n",
        "### 严格相同宽度的成本对照\n",
        "除了同一阈值达标，本表直接比较原始 prefix：target_radius 第 1 批与 direct_target 第 4 批。两者历史和先验相同。前者新增精度矩阵为 (2t)(2t)ᵀ/(1/64)=256ttᵀ；后者四批合计 4ttᵀ/(1/64)=256ttᵀ。因此 W 和区间宽度相同，仅观测噪声实现、中心和端点不必相同。完整精度匹配数值及浮点差值见 `exact_width_cost_matches.csv`。\n",
        md_table(matches,["geometry","bridge_new_n","direct_new_n","bridge_width","direct_width","width_abs_difference","incremental_saving_fraction"],decimals=12),"\n",
        "75% 是新增参与者节约：(256−64)/256。若把共同 64 名历史参与者也计入，总人数是 128 对 320，节约 60%；两者都不包含现实校准等费用。两个几何共享同一个 b0=2t 设计，因此不是两份独立的普遍性证据，更不能把跨分布/世界重复当作独立发现。\n",
        "target_informative 与 distractor 的强桥接候选含 x=(2,0,0)，在同个体噪声与同人数下，观测对目标参数的 loading 是直接目标实验的两倍。因此首次桥接的优势有明确输入来源；不能据此声称任意桥接都优于直接目标实验。distractor 还含很大的非目标方向，logdet 会优先追求整体信息增量；本轮目标半径规则则直接追求目标精度。weak 菜单只有很弱的目标方向，用于检查候选信息不足时的行为。预算内未达到精度的结果必须与有利场景一起解释。\n",
        "## 同精度首次成本及未达标\n",
        "所有世界都保留在分母中。下表是完整区间宽度首次≤阈值所需的新增人数；未达标表示采满 256 人仍未达到，cost_to_success 为 NA，属于右删失，不能把 256 写作成功所需成本。该任务从完整 prefix 推导，和主 stopped 的 .60 阈值相同或不同均明确列出。由于路径固定，每个单元达标率只能是 0 或 1，不对此确定性比例构造抽样置信区间。逐世界与逐单元达标率/失败率及实际消耗见 attainment 表。\n",
        md_table(compact_attain,list(compact_attain.columns),decimals=0),"\n",
        "## 覆盖与错误发布\n",
        f"逐点主区间：540 个 cell×method×prefix 分组，经验覆盖范围 **{coverage_range(point,'covered')}**；实际停止点：108 个分组，范围 **{coverage_range(stopped,'covered')}**。每个分组分母为 {n} 个独立世界，不能把五前缀当五倍独立样本。\n",
        f"对五前缀另分配每步 .05/5 的失败预算，半径变成 √5 R；整条路径同时覆盖范围 **{coverage_range(paths,'all_joint_prefix_covered')}**。主单次半径的五前缀同时覆盖也单独保留（{coverage_range(paths,'all_pointwise_prefix_covered')}），只作诊断，不声称主半径有 95% 同时保证。\n",
        "![覆盖率与 Monte Carlo 区间](coverage.png)\n",
        f"完整 prefix 的 interval_miss_on_release 合计 {misses} 条、bad_release_scientific 合计 {bad} 条。这些是相关前缀记录计数，不是独立事件样本量。前者指发布且真值不在自身区间内；后者指发布且点误差超过科学半宽 .30。二者不可互换。逐点率与 Wilson 区间使用全世界分母；条件于发布的诊断另列，零发布时为 NA。\n",
        "Wilson 区间是逐格、未作全家族校正的 Monte Carlo 描述；全覆盖也不证明真实失败概率为零。Chebyshev 区间可能保守，本轮高经验覆盖不表示优于其它区间或精确达到名义覆盖。这里的概率针对随机参数与噪声的联合分布；不支持给定固定 beta 或给定结果后的条件覆盖。停止点由设计预先决定，因而仍为固定设计；不推到任意结果自适应停止。\n",
        "## 审稿意见能推进到哪里\n",
        "REV-10 / KoBT.W4：为取消 Gaussian 形状假设后的线性矩分支提供定理域内实现证据，并显示直接目标区间选择与 logdet 目标不同。仍依赖线性观测及可信的已知二阶矩，不回答现实输入和域外错设；不标 resolved。REV-07：提供共同信息、人数和可靠性口径下的四策略成本—精度对照；优势受几何 loading 限制，缺现实总成本和强外部基线。REV-12：区分完整前缀、实际停止、单次/路径区间和两种错误发布事件；不覆盖真实资格失败或任意适应性停止。\n",
        "全部 12 项回顾：REV-01 得到指定单世界轨迹，作者理解仍待讨论；REV-02 无 R∞ 结果自适应效用证据；REV-03 不自动改摘要数字；REV-04 二阶矩为已知合成输入，真实集合/L/H 未解；REV-05 未提供真实闭环；REV-06 未新增 Many Labs；REV-07 有局部对照；REV-08 未证新颖性；REV-09 线性矩权重可有负值，但未证原凸组合类普适性；REV-10 有域内非高斯实现；REV-11 新分支源与协议可追溯，未完成全稿归属；REV-12 有局部统计语义验收。保持 tracker 状态，本报告不关闭任何问题。\n",
        "## 验证与产物\n",
        f"独立分析的 {len(checks)} 项断言全部通过：包括原始产物哈希、完整分母、W 分解、W=q、单次/路径半径、rank-one 增益、每步目标最小值、成本、评分及停止后冻结。原运行测试记录位于 `test_log.txt`；这些实现检查和有限模拟都不能替代证明。\n",
        "- `cell_prefix_stopped_summary.csv`：所有 27 单元×4 方法×2 模式×5 前缀的误差、宽度、覆盖与 Wilson 区间。\n- `stopped_terminal_summary.csv`、`path_coverage_summary.csv`：实际停点与五前缀事件。\n- `deterministic_width_cost.csv`、`exact_width_cost_matches.csv`：无重复伪精度的设计曲线及严格同宽度成本。\n- `attainment_per_world.csv`、`attainment_summary.csv`：首次成本、失败分母及实际消耗。\n- `single_world_trajectory.csv`、`single_world_observations.csv`、`single_world_initial_candidates.csv`：预先指定世界、已采集观测和第一次各候选评分。\n- `analysis_checks.json`、`analysis_manifest.json`：核查、来源与分析版本。PDF 图与 PNG 图同名保存。\n"]
    (out/"RESULTS.md").write_text("\n".join(texts),encoding="utf-8")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,default=REPO/"reproduced/non_gaussian_target_run01/full")
    parser.add_argument("--output",type=Path,default=REPO/"revision/results/non_gaussian_target_run01")
    args=parser.parse_args()
    raw=args.input.resolve(); out=args.output.resolve()
    manifest=json.loads((raw/"run_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "complete": raise ValueError("Raw manifest must be complete before analysis")
    if out.exists(): raise FileExistsError(f"Use a fresh analysis output directory: {out}")
    out.mkdir(parents=True)
    analysis=dict(status="running",started_utc=datetime.now(timezone.utc).isoformat(),
        source_run=str(raw),raw_manifest_sha256=digest(raw/"run_manifest.json"),
        analysis_source_sha256=digest(Path(__file__)),command=[sys.executable,*sys.argv],
        scope="Descriptive fixed-design costs; world-level marginal events with pointwise Wilson 95% intervals; no family correction")
    save_json(out/"analysis_manifest.json",analysis)
    try:
        cfg=manifest["config"]
        records=pd.read_csv(raw/"records.csv")
        scores=pd.read_csv(raw/"candidate_scores.csv")
        plans=json.loads((raw/"design_plans.json").read_text(encoding="utf-8"))
        checks=audit(records,manifest,raw,cfg,scores,plans)
        prefix=records[records["mode"].eq("prefix")]
        events=["covered","path_interval_covered","released","interval_miss_on_release","bad_release_scientific"]
        summaries=event_summary(records,CELL+["mode","budget_stage"],events)
        stop_records=records[records["mode"].eq("stopped") & records.budget_stage.eq(cfg["new_batches"])]
        stopped=event_summary(stop_records,CELL,events)
        paths=event_summary(prefix[prefix.budget_stage.eq(cfg["new_batches"])],CELL,
                            ["all_pointwise_prefix_covered","all_joint_prefix_covered"])
        widths=prefix.drop_duplicates(["geometry","method","budget_stage"])[[
            "geometry","method","budget_stage","new_participants","history_participants","total_participants",
            "width","path_width","W","parameter_component","noise_component","selected"]].sort_values(["geometry","method","budget_stage"])
        matches=[]
        for geometry in ["target_informative","distractor"]:
            bridge=widths[(widths.geometry==geometry)&(widths.method=="target_radius")&(widths.budget_stage==1)].iloc[0]
            direct=widths[(widths.geometry==geometry)&(widths.method=="direct_target")&(widths.budget_stage==4)].iloc[0]
            matches.append(dict(geometry=geometry,bridge_new_n=int(bridge.new_participants),direct_new_n=int(direct.new_participants),
                bridge_W=float(bridge.W),direct_W=float(direct.W),W_abs_difference=float(abs(bridge.W-direct.W)),
                bridge_width=float(bridge.width),direct_width=float(direct.width),width_abs_difference=float(abs(bridge.width-direct.width)),
                incremental_saving_fraction=1-float(bridge.new_participants/direct.new_participants),
                bridge_total_n=int(bridge.total_participants),direct_total_n=int(direct.total_participants)))
        matches=pd.DataFrame(matches)
        checks["strict_equal_width_cost_match"]=bool(matches.width_abs_difference.lt(1e-12).all())
        if not checks["strict_equal_width_cost_match"]: raise AssertionError("Prespecified exact-width match failed")
        individual,attain=attainment(prefix,cfg)
        trace=None
        for line in (raw/"traces.jsonl").open(encoding="utf-8"):
            candidate=json.loads(line)
            if (candidate["geometry"],candidate["beta_family"],candidate["noise_family"],candidate["replicate"]) == ("distractor","gaussian","gaussian",0):
                trace=candidate;break
        if trace is None: raise AssertionError("Prespecified explanatory world missing")
        trajectory=records[(records.geometry=="distractor")&(records.beta_family=="gaussian")&
            (records.noise_family=="gaussian")&(records.replicate==0)].copy()
        trajectory["observed_source_ids"]=[json.dumps(plans[f"distractor/{row.method}"][row.actual_stage]["ids"]) for row in trajectory.itertuples()]
        trajectory["weights"]=[json.dumps(plans[f"distractor/{row.method}"][row.actual_stage]["weights"]) for row in trajectory.itertuples()]
        observation_lookup={o["id"]:o for o in trace["history"]+trace["acquisitions"]}
        trajectory["observed_effects"]=[json.dumps([observation_lookup[i]["observed_effect"] for i in json.loads(ids)]) for ids in trajectory.observed_source_ids]
        reconstructed=np.array([np.dot(json.loads(weights),json.loads(effects)) for weights,effects in zip(trajectory.weights,trajectory.observed_effects)])
        checks["single_world_estimator_reconstruction"]=bool(np.allclose(reconstructed,trajectory.estimate,atol=1e-13,rtol=1e-10))
        if not checks["single_world_estimator_reconstruction"]: raise AssertionError("Single-world estimator reconstruction failed")
        observations=pd.DataFrame(list(observation_lookup.values()))
        initial=scores[(scores.geometry=="distractor")&(scores.stage==1)]
        for name,frame in [("cell_prefix_stopped_summary",summaries),("stopped_terminal_summary",stopped),
            ("path_coverage_summary",paths),("deterministic_width_cost",widths),
            ("attainment_per_world",individual),("attainment_summary",attain),
            ("single_world_trajectory",trajectory),("single_world_initial_candidates",initial),
            ("single_world_observations",observations),("exact_width_cost_matches",matches)]:
            frame.to_csv(out/(name+".csv"),index=False,float_format="%.15g")
        save_json(out/"analysis_checks.json",checks)
        figures(widths,summaries,stopped,paths,out)
        write_report(out,raw,manifest,cfg,summaries,stopped,paths,widths,attain,trajectory,trace,checks,matches)
        analysis.update(status="complete",checks_passed=len(checks),worlds=int(records.world_id.nunique()),
                        records=len(records),summary_rows=len(summaries))
    except Exception as exc:
        analysis.update(status="failed",error=repr(exc));raise
    finally:
        analysis["finished_utc"]=datetime.now(timezone.utc).isoformat()
        analysis["artifact_sha256"]={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!="analysis_manifest.json"}
        save_json(out/"analysis_manifest.json",analysis)
    print(json.dumps({"status":"complete","output":str(out),"checks_passed":len(checks)},ensure_ascii=True))


if __name__ == "__main__":
    main()
