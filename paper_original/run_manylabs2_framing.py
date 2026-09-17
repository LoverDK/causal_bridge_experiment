#!/usr/bin/env python3
"""Independent-site transport benchmark from Many Labs 2.

The benchmark uses the Tversky--Kahneman framing replication.  Treatment is
the randomized price context (Cheap versus Expensive), the outcome is the
binary decision to travel to another store, and each Many Labs 2 ``source`` is
held out as an independent target sample.  Target outcomes are never used to
fit a prediction or to decide whether to release it.

This script deliberately implements transparent meta-analytic baselines.  Its
random-effects predictive interval is a working-model baseline, not a finite-
sample causal certificate and not an implementation of the paper's proposed
mechanism uncertainty sets.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import os
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from scipy.stats import chi2, norm, t


COMMIT = "acef63fc397b8dce7f0b00f863bcea78d324bea8"
DATA_URL = (
    "https://raw.githubusercontent.com/ManyLabsOpenScience/ManyLabs2/"
    f"{COMMIT}/OSFdata/Framing%20%28Tversky%20%26%20Kahneman%2C%201981%29/"
    "Tversky.1/Global/Data/Tversky_1_study_global_include_all_CLEAN_CASE.csv"
)
DATA_SHA256 = "15898b5c241696adc7fd91a638839ba49a9f9be64c78da9151b39018d66bfbd3"
PRIMARY_DELTA = 0.15
ALPHA = 0.05

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
PURPLE = "#7A4EAB"
INK = "#273142"
MID = "#6B7280"
LIGHT = "#E8EDF3"


@dataclass(frozen=True)
class MetaFit:
    mean: float
    variance: float
    tau2: float
    q: float
    q_pvalue: float
    i2: float


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_verified(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        urllib.request.urlretrieve(DATA_URL, temporary)
        observed = sha256(temporary)
        if observed != DATA_SHA256:
            raise RuntimeError(
                f"Downloaded data checksum mismatch: expected {DATA_SHA256}, got {observed}"
            )
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_clean_data(path: Path, allow_download: bool) -> pd.DataFrame:
    if not path.exists():
        if not allow_download:
            raise FileNotFoundError(
                f"Missing {path}. Re-run with --download to obtain the commit-pinned public file."
            )
        download_verified(path)
    observed = sha256(path)
    if observed != DATA_SHA256:
        raise RuntimeError(
            f"Data checksum mismatch: expected {DATA_SHA256}, got {observed}. "
            "Refusing to analyze an unpinned version."
        )
    frame = pd.read_csv(path)
    required = {
        "source",
        "factor",
        "variable",
        "Country",
        "Language",
        "Weird",
        "Setting",
        "case.include",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Required columns missing: {sorted(missing)}")
    include = frame["case.include"].astype(str).str.lower().isin({"true", "1"})
    frame = frame.loc[include].copy()
    frame = frame.loc[
        frame["factor"].isin(["Cheap", "Expensive"])
        & frame["variable"].isin(["Yes", "No"])
        & frame["source"].notna()
    ].copy()
    frame["A"] = (frame["factor"] == "Cheap").astype(int)
    frame["Y"] = (frame["variable"] == "Yes").astype(int)
    return frame


def summarize_sites(frame: pd.DataFrame) -> pd.DataFrame:
    counts = (
        frame.groupby(["source", "factor"], observed=True)["Y"]
        .agg(events="sum", n="size")
        .reset_index()
    )
    wide = counts.pivot(index="source", columns="factor", values=["events", "n"])
    expected = [
        ("events", "Cheap"),
        ("events", "Expensive"),
        ("n", "Cheap"),
        ("n", "Expensive"),
    ]
    complete = wide.dropna(subset=expected).copy()
    if len(complete) != frame["source"].nunique():
        omitted = sorted(set(frame["source"].unique()).difference(complete.index))
        raise ValueError(f"Sites without both treatment arms: {omitted}")

    sites = pd.DataFrame(index=complete.index)
    sites["events_cheap"] = complete[("events", "Cheap")].astype(int)
    sites["n_cheap"] = complete[("n", "Cheap")].astype(int)
    sites["events_expensive"] = complete[("events", "Expensive")].astype(int)
    sites["n_expensive"] = complete[("n", "Expensive")].astype(int)
    if (sites[["n_cheap", "n_expensive"]] <= 1).any().any():
        raise ValueError("At least one arm has fewer than two observations.")

    sites["p_cheap"] = sites["events_cheap"] / sites["n_cheap"]
    sites["p_expensive"] = sites["events_expensive"] / sites["n_expensive"]
    sites["effect_rd"] = sites["p_cheap"] - sites["p_expensive"]
    # Unbiased plug-in variance for a difference of independent Bernoulli means.
    sites["variance_rd"] = (
        sites["p_cheap"] * (1.0 - sites["p_cheap"]) / (sites["n_cheap"] - 1)
        + sites["p_expensive"]
        * (1.0 - sites["p_expensive"])
        / (sites["n_expensive"] - 1)
    )
    if (sites["variance_rd"] <= 0).any():
        raise ValueError("A site has a zero risk-difference variance estimate.")
    sites["se_rd"] = np.sqrt(sites["variance_rd"])
    sites["ci_low"] = sites["effect_rd"] - norm.ppf(0.975) * sites["se_rd"]
    sites["ci_high"] = sites["effect_rd"] + norm.ppf(0.975) * sites["se_rd"]
    sites["n_total"] = sites["n_cheap"] + sites["n_expensive"]

    metadata_columns = ["Country", "Language", "Weird", "Setting"]
    metadata = frame.groupby("source", observed=True)[metadata_columns].first()
    sites = sites.join(metadata, how="left").reset_index()
    sites["Weird"] = pd.to_numeric(sites["Weird"], errors="coerce")
    sites["context"] = np.where(sites["Weird"] == 1, "WEIRD", "non-WEIRD")
    return sites.sort_values("source").reset_index(drop=True)


def fit_fixed(y: np.ndarray, v: np.ndarray) -> MetaFit:
    weights = 1.0 / v
    mean = float(np.sum(weights * y) / np.sum(weights))
    variance = float(1.0 / np.sum(weights))
    q = float(np.sum(weights * (y - mean) ** 2))
    df = len(y) - 1
    return MetaFit(
        mean=mean,
        variance=variance,
        tau2=0.0,
        q=q,
        q_pvalue=float(chi2.sf(q, df)),
        i2=float(max(0.0, (q - df) / q)) if q > 0 else 0.0,
    )


def fit_random_dl(y: np.ndarray, v: np.ndarray) -> MetaFit:
    fixed = fit_fixed(y, v)
    weights = 1.0 / v
    c_term = float(np.sum(weights) - np.sum(weights**2) / np.sum(weights))
    tau2 = float(max(0.0, (fixed.q - (len(y) - 1)) / c_term))
    random_weights = 1.0 / (v + tau2)
    mean = float(np.sum(random_weights * y) / np.sum(random_weights))
    variance = float(1.0 / np.sum(random_weights))
    return MetaFit(
        mean=mean,
        variance=variance,
        tau2=tau2,
        q=fixed.q,
        q_pvalue=fixed.q_pvalue,
        i2=fixed.i2,
    )


def leave_one_site_out(sites: pd.DataFrame, delta: float) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    zcrit = float(norm.ppf(1.0 - ALPHA / 2.0))
    for target_index, target in sites.iterrows():
        train = sites.drop(index=target_index)
        y_train = train["effect_rd"].to_numpy(float)
        v_train = train["variance_rd"].to_numpy(float)
        fixed = fit_fixed(y_train, v_train)
        random = fit_random_dl(y_train, v_train)

        # This worst-case Bernoulli variance uses target arm sizes but no outcomes.
        target_design_variance = (
            0.25 / float(target["n_cheap"]) + 0.25 / float(target["n_expensive"])
        )
        fixed_halfwidth = zcrit * math.sqrt(fixed.variance + target_design_variance)
        # Small-sample t critical value is used for the random-effects working model.
        random_crit = float(t.ppf(1.0 - ALPHA / 2.0, df=max(len(train) - 2, 1)))
        random_halfwidth = random_crit * math.sqrt(
            random.variance + random.tau2 + target_design_variance
        )
        observed = float(target["effect_rd"])
        records.append(
            {
                "source": target["source"],
                "Country": target["Country"],
                "Language": target["Language"],
                "context": target["context"],
                "n_cheap": int(target["n_cheap"]),
                "n_expensive": int(target["n_expensive"]),
                "observed_effect_rd": observed,
                "observed_se_rd": float(target["se_rd"]),
                "fixed_prediction": fixed.mean,
                "fixed_halfwidth": fixed_halfwidth,
                "fixed_abs_error": abs(observed - fixed.mean),
                "fixed_covered": abs(observed - fixed.mean) <= fixed_halfwidth,
                "random_prediction": random.mean,
                "random_tau2": random.tau2,
                "random_halfwidth": random_halfwidth,
                "random_abs_error": abs(observed - random.mean),
                "random_covered": abs(observed - random.mean) <= random_halfwidth,
                "released_delta": random_halfwidth <= delta,
                "delta": delta,
            }
        )
    return pd.DataFrame.from_records(records)


def method_metrics(
    loso: pd.DataFrame, prediction: str, halfwidth: str, released: pd.Series
) -> dict[str, float | int]:
    subset = loso.loc[released].copy()
    if subset.empty:
        return {
            "n_released": 0,
            "release_rate": 0.0,
            "mae": math.nan,
            "rmse": math.nan,
            "coverage": math.nan,
            "mean_interval_width": math.nan,
        }
    errors = subset["observed_effect_rd"] - subset[prediction]
    covered = errors.abs() <= subset[halfwidth]
    return {
        "n_released": int(len(subset)),
        "release_rate": float(len(subset) / len(loso)),
        "mae": float(errors.abs().mean()),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "coverage": float(covered.mean()),
        "mean_interval_width": float(2.0 * subset[halfwidth].mean()),
    }


def build_summary(loso: pd.DataFrame, delta: float) -> pd.DataFrame:
    all_sites = pd.Series(True, index=loso.index)
    released = loso["random_halfwidth"] <= delta
    rows = []
    for name, pred, width, mask in [
        ("fixed_effect_all", "fixed_prediction", "fixed_halfwidth", all_sites),
        ("random_effects_all", "random_prediction", "random_halfwidth", all_sites),
        (
            f"random_effects_abstain_delta_{delta:.2f}",
            "random_prediction",
            "random_halfwidth",
            released,
        ),
    ]:
        row: dict[str, object] = {"method": name, "delta": delta if "abstain" in name else np.nan}
        row.update(method_metrics(loso, pred, width, mask))
        rows.append(row)
    return pd.DataFrame(rows)


def selective_frontier(loso: pd.DataFrame) -> pd.DataFrame:
    lower = max(0.05, float(loso["random_halfwidth"].min()) - 0.01)
    upper = min(0.50, float(loso["random_halfwidth"].max()) + 0.01)
    deltas = np.unique(np.r_[np.linspace(lower, upper, 100), PRIMARY_DELTA])
    rows = []
    for delta in deltas:
        released = loso["random_halfwidth"] <= delta
        metrics = method_metrics(
            loso, "random_prediction", "random_halfwidth", released
        )
        rows.append({"delta": float(delta), **metrics})
    return pd.DataFrame(rows).sort_values("delta").reset_index(drop=True)


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.titlesize": 10.5,
            "axes.labelsize": 9,
            "axes.edgecolor": "#9AA4B2",
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.labelcolor": INK,
            "text.color": INK,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
        }
    )


def draw_figure(
    sites: pd.DataFrame,
    loso: pd.DataFrame,
    frontier: pd.DataFrame,
    fixed: MetaFit,
    random: MetaFit,
    delta: float,
    output_pdf: Path,
    output_png: Path,
) -> None:
    configure_plotting()
    fig = plt.figure(figsize=(11.5, 8.1), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=[1.12, 1.0], height_ratios=[1.15, 0.85])
    ax_a = fig.add_subplot(grid[:, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[1, 1])

    ordered = sites.sort_values("effect_rd").reset_index(drop=True)
    y_pos = np.arange(len(ordered))
    colors = np.where(ordered["context"].eq("WEIRD"), BLUE, ORANGE)
    ax_a.axvspan(
        random.mean - 1.96 * math.sqrt(random.variance + random.tau2),
        random.mean + 1.96 * math.sqrt(random.variance + random.tau2),
        color=GREEN,
        alpha=0.10,
        lw=0,
        label="RE predictive band for a true site effect",
    )
    ax_a.axvline(0, color="#AAB2BE", lw=0.9, ls=(0, (2, 2)))
    ax_a.axvline(fixed.mean, color=PURPLE, lw=1.3, ls=(0, (4, 2)))
    ax_a.axvline(random.mean, color=GREEN, lw=1.5)
    ax_a.hlines(y_pos, ordered["ci_low"], ordered["ci_high"], color=colors, alpha=0.42, lw=0.7)
    ax_a.scatter(
        ordered["effect_rd"],
        y_pos,
        c=colors,
        s=12 + 35 * np.sqrt(ordered["n_total"] / ordered["n_total"].max()),
        edgecolor="white",
        linewidth=0.35,
        zorder=3,
    )
    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels(ordered["source"], fontsize=5.7)
    ax_a.set_xlabel("Site risk difference: Pr(Yes | Cheap) − Pr(Yes | Expensive)")
    ax_a.set_ylabel("Independent Many Labs 2 source (sorted)")
    ax_a.set_title("A  Cross-site causal-effect variation", loc="left", fontweight="bold")
    ax_a.grid(axis="x", color=LIGHT, lw=0.6)
    ax_a.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=BLUE, markeredgecolor="white", label="WEIRD"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=ORANGE, markeredgecolor="white", label="non-WEIRD"),
            Line2D([0], [0], color=PURPLE, ls=(0, (4, 2)), label="fixed-effect mean"),
            Line2D([0], [0], color=GREEN, label="random-effects mean"),
        ],
        frameon=False,
        fontsize=7.2,
        ncol=2,
        loc="lower right",
    )

    released = loso["random_halfwidth"] <= delta
    covered = loso["random_covered"].astype(bool)
    point_colors = np.where(released, BLUE, ORANGE)
    point_edges = np.where(covered, "white", "#B91C1C")
    sizes = 22 + 80 * np.sqrt(
        (loso["n_cheap"] + loso["n_expensive"])
        / (loso["n_cheap"] + loso["n_expensive"]).max()
    )
    lim_low = float(
        min(loso["observed_effect_rd"].min(), loso["random_prediction"].min()) - 0.04
    )
    lim_high = float(
        max(loso["observed_effect_rd"].max(), loso["random_prediction"].max()) + 0.04
    )
    ax_b.plot([lim_low, lim_high], [lim_low, lim_high], color="#9AA4B2", lw=1.0, ls=(0, (3, 2)))
    ax_b.scatter(
        loso["observed_effect_rd"],
        loso["random_prediction"],
        s=sizes,
        c=point_colors,
        edgecolor=point_edges,
        linewidth=0.9,
        alpha=0.86,
    )
    ax_b.set_xlim(lim_low, lim_high)
    ax_b.set_ylim(lim_low, lim_high)
    ax_b.set_xlabel("Held-out site effect (revealed only for evaluation)")
    ax_b.set_ylabel("Archive-only random-effects prediction")
    ax_b.set_title("B  Strict leave-one-site-out transport", loc="left", fontweight="bold")
    ax_b.grid(color=LIGHT, lw=0.6)
    ax_b.text(
        0.02,
        0.97,
        f"release if PI half-width ≤ {delta:.2f}\nblue: released; orange: refused\nred rim: 95% PI miss",
        transform=ax_b.transAxes,
        ha="left",
        va="top",
        fontsize=7.2,
        bbox={"facecolor": "white", "edgecolor": LIGHT, "pad": 3.5, "alpha": 0.93},
    )

    finite = frontier.dropna(subset=["mae", "coverage"]).copy()
    normalization = Normalize(vmin=float(finite["coverage"].min()), vmax=1.0)
    scatter = ax_c.scatter(
        finite["release_rate"],
        finite["mae"],
        c=finite["coverage"],
        cmap="viridis",
        norm=normalization,
        s=22,
        alpha=0.85,
        linewidth=0,
    )
    ax_c.plot(finite["release_rate"], finite["mae"], color="#65758B", lw=0.75, alpha=0.55)
    primary_index = (finite["delta"] - delta).abs().idxmin()
    primary = finite.loc[primary_index]
    ax_c.scatter(
        [primary["release_rate"]],
        [primary["mae"]],
        s=95,
        facecolor="none",
        edgecolor=ORANGE,
        linewidth=1.8,
        zorder=5,
    )
    ax_c.annotate(
        f"δ={delta:.2f}\nrelease={primary['release_rate']:.0%}",
        (primary["release_rate"], primary["mae"]),
        xytext=(7, 7),
        textcoords="offset points",
        fontsize=7.2,
    )
    ax_c.set_xlabel("Fraction of target sites released")
    ax_c.set_ylabel("MAE among released sites")
    ax_c.set_title("C  Selective prediction frontier", loc="left", fontweight="bold")
    ax_c.grid(color=LIGHT, lw=0.6)
    colorbar = fig.colorbar(scatter, ax=ax_c, fraction=0.045, pad=0.02)
    colorbar.set_label("Empirical 95% PI coverage", fontsize=7.5)
    colorbar.ax.tick_params(labelsize=7)

    fig.suptitle(
        "Many Labs 2 framing effect: independent-source transport without target-outcome leakage",
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(output_pdf)
    fig.savefig(output_png, dpi=300)
    plt.close(fig)


def write_report(
    output: Path,
    sites: pd.DataFrame,
    fixed: MetaFit,
    random: MetaFit,
    summary: pd.DataFrame,
    delta: float,
) -> None:
    fixed_row = summary.loc[summary["method"] == "fixed_effect_all"].iloc[0]
    random_row = summary.loc[summary["method"] == "random_effects_all"].iloc[0]
    abstain_row = summary.loc[summary["method"].str.contains("abstain")].iloc[0]
    text = f"""# Many Labs 2 independent-source benchmark

## Audited design

- Public source: Many Labs 2 official OSF-linked GitHub repository, commit `{COMMIT}`.
- Experiment: Tversky--Kahneman framing replication (`Tversky.1`).
- Binary treatment: `Cheap` (A=1) versus `Expensive` (A=0) price context.
- Binary outcome: willingness to travel to another store (`Yes`=1, `No`=0).
- Independent unit for transport: the Many Labs 2 `source` sample.
- Estimand: source-specific risk difference Pr(Yes | Cheap) - Pr(Yes | Expensive).
- Split: strict leave-one-source-out; the held-out outcome and effect are not used for fitting or release/refusal.

The cleaned file contains {len(sites)} complete sources and {int(sites['n_total'].sum()):,} analyzed responses. The
commit-pinned input has SHA-256 `{DATA_SHA256}`.

## Aggregate estimates

- Fixed-effect mean risk difference: {fixed.mean:.4f} (SE {math.sqrt(fixed.variance):.4f}).
- DerSimonian--Laird random-effects mean: {random.mean:.4f} (SE {math.sqrt(random.variance):.4f}).
- Estimated between-source SD: {math.sqrt(random.tau2):.4f}; I-squared: {100.0 * random.i2:.1f}%;
  Cochran Q p-value: {random.q_pvalue:.4g}.

## Held-out prediction

| Method | Release rate | MAE | RMSE | 95% PI coverage | Mean PI width |
|---|---:|---:|---:|---:|---:|
| Fixed effects, always release | {fixed_row['release_rate']:.3f} | {fixed_row['mae']:.4f} | {fixed_row['rmse']:.4f} | {fixed_row['coverage']:.3f} | {fixed_row['mean_interval_width']:.4f} |
| Random effects, always release | {random_row['release_rate']:.3f} | {random_row['mae']:.4f} | {random_row['rmse']:.4f} | {random_row['coverage']:.3f} | {random_row['mean_interval_width']:.4f} |
| Random effects, release only if half-width <= {delta:.2f} | {abstain_row['release_rate']:.3f} | {abstain_row['mae']:.4f} | {abstain_row['rmse']:.4f} | {abstain_row['coverage']:.3f} | {abstain_row['mean_interval_width']:.4f} |

## Interpretation boundary

These are real independent-source predictions, but the random-effects interval is only a model-based baseline.
It is not a finite-sample-valid certificate, the tolerance was not learned from target outcomes, and the observed
held-out risk difference is itself noisy. This benchmark therefore supports claims about the need for selective
transport and provides a leakage-free test bed; it does not by itself validate calibrated mechanism uncertainty
sets or the paper's strongest coverage theorem.
"""
    output.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=Path(__file__).with_name("tversky_framing_clean.csv"),
        help="Path to the commit-pinned cleaned Many Labs 2 CSV.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory for tables, report, and figures.",
    )
    parser.add_argument(
        "--delta",
        type=float,
        default=PRIMARY_DELTA,
        help="Pre-outcome release tolerance on predictive-interval half-width.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download the public commit-pinned CSV when --data is missing.",
    )
    args = parser.parse_args()
    if not (0.0 < args.delta < 1.0):
        raise ValueError("--delta must lie in (0,1).")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    frame = load_clean_data(args.data, allow_download=args.download)
    sites = summarize_sites(frame)
    y = sites["effect_rd"].to_numpy(float)
    v = sites["variance_rd"].to_numpy(float)
    fixed = fit_fixed(y, v)
    random = fit_random_dl(y, v)
    loso = leave_one_site_out(sites, delta=args.delta)
    summary = build_summary(loso, delta=args.delta)
    frontier = selective_frontier(loso)

    global_summary = pd.DataFrame(
        [
            {
                "n_sites": len(sites),
                "n_responses": int(sites["n_total"].sum()),
                "fixed_mean": fixed.mean,
                "fixed_se": math.sqrt(fixed.variance),
                "random_mean": random.mean,
                "random_se": math.sqrt(random.variance),
                "tau2_dl": random.tau2,
                "tau_dl": math.sqrt(random.tau2),
                "cochran_q": random.q,
                "cochran_q_pvalue": random.q_pvalue,
                "i2": random.i2,
            }
        ]
    )

    sites.to_csv(args.out_dir / "site_effects.csv", index=False)
    loso.to_csv(args.out_dir / "loso_predictions.csv", index=False)
    summary.to_csv(args.out_dir / "benchmark_summary.csv", index=False)
    frontier.to_csv(args.out_dir / "selective_frontier.csv", index=False)
    global_summary.to_csv(args.out_dir / "global_meta_summary.csv", index=False)
    draw_figure(
        sites,
        loso,
        frontier,
        fixed,
        random,
        args.delta,
        args.out_dir / "manylabs2_framing_loso.pdf",
        args.out_dir / "manylabs2_framing_loso.png",
    )
    write_report(
        args.out_dir / "benchmark_results.md",
        sites,
        fixed,
        random,
        summary,
        args.delta,
    )

    print(global_summary.to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
