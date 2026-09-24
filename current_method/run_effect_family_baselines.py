"""Unified baseline panel for the pinned Many Labs 2 family holdout.

All methods use the same five complete-family holdouts as the external
validity audit.  Target effects are read only for final scoring.  This file
names the comparison classes used in the PDF assessment explicitly:
transportability, hierarchical meta-analysis, robust partial identification,
and conformal/selective prediction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

from run_effect_family_holdout import (
    ALPHA,
    DATA_SHA256,
    DATA_URL,
    ELIGIBLE_FAMILIES,
    COMMIT,
    _design_se,
    load_data,
)


ROOT = Path(__file__).resolve().parent
RELEASE_THRESHOLDS = (0.20, 0.40, 0.60, 0.80, 1.00)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixed_fit(train: pd.DataFrame) -> tuple[float, float]:
    y = train.effect.to_numpy(float)
    v = train.variance.to_numpy(float)
    w = 1.0 / v
    return float(np.sum(w * y) / np.sum(w)), float(1.0 / np.sum(w))


def _hierarchical_fit(train: pd.DataFrame) -> tuple[float, float, float, int]:
    """Normal-Normal random-effects meta-analysis fit."""
    mean, fixed_var = _fixed_fit(train)
    y = train.effect.to_numpy(float)
    v = train.variance.to_numpy(float)
    w = 1.0 / v
    q = float(np.sum(w * (y - mean) ** 2))
    c = float(np.sum(w) - np.sum(w * w) / np.sum(w))
    tau2 = max(0.0, (q - (len(y) - 1)) / c) if c > 0 else 0.0
    rw = 1.0 / (v + tau2)
    posterior_mean = float(np.sum(rw * y) / np.sum(rw))
    posterior_var = float(1.0 / np.sum(rw))
    return posterior_mean, posterior_var, float(tau2), max(len(y) - 2, 1)


def _transport_fit(train: pd.DataFrame, target: pd.Series) -> tuple[float, float, int]:
    """Weighted context meta-regression with a design-only target allowance."""
    x = (train.context == "NONWEIRD").astype(float).to_numpy()
    X = np.column_stack([np.ones(len(train)), x])
    y = train.effect.to_numpy(float)
    v = train.variance.to_numpy(float)
    W = np.diag(1.0 / v)
    xtwx = X.T @ W @ X
    if np.linalg.matrix_rank(xtwx) < 2:
        X = X[:, :1]
    xtwx_inv = np.linalg.pinv(X.T @ W @ X)
    beta = xtwx_inv @ X.T @ W @ y
    target_x = np.array([1.0, float(target.context == "NONWEIRD")])[: X.shape[1]]
    estimate = float(target_x @ beta)
    residual = y - X @ beta
    df = max(len(train) - X.shape[1], 1)
    heterogeneity = max(0.0, float(np.sum((residual**2) / v) - df) / max(np.sum(1.0 / v), 1e-12))
    coefficient_var = float(target_x @ xtwx_inv[: X.shape[1], : X.shape[1]] @ target_x)
    target_se = _design_se(target.N)
    predictive_var = max(0.0, coefficient_var + heterogeneity + target_se**2)
    return estimate, predictive_var, df


def _conformal_radius(train: pd.DataFrame, target: pd.Series, unit: str) -> tuple[float, float]:
    """Return all-training center and a leave-unit-out absolute-residual radius."""
    center, _ = _fixed_fit(train)
    residuals: list[float] = []
    groups = train.groupby(unit, sort=True)
    for _, group in groups:
        other = train.drop(index=group.index)
        if len(other) < 3:
            continue
        prediction, _ = _fixed_fit(other)
        group_center, _ = _fixed_fit(group)
        residuals.append(abs(group_center - prediction))
    if len(residuals) < 2:
        raise RuntimeError(f"Need at least two conformal calibration units for {unit}")
    ordered = np.sort(np.asarray(residuals, float))
    rank = min(len(ordered) - 1, int(math.ceil((len(ordered) + 1) * (1 - ALPHA))) - 1)
    radius = float(ordered[rank] + 1.96 * _design_se(target.N))
    return center, radius


def _predict(train: pd.DataFrame, target: pd.Series) -> list[dict[str, float | str]]:
    target_se = _design_se(target.N)
    z = 1.96
    transport, transport_var, transport_df = _transport_fit(train, target)
    hierarchical, posterior_var, tau2, hierarchical_df = _hierarchical_fit(train)
    # Predictive interval for a transported study-level standardized effect.
    hierarchical_radius = float(t.ppf(1 - ALPHA / 2, hierarchical_df) * math.sqrt(
        posterior_var + tau2 + target_se**2
    ))
    transport_radius = float(t.ppf(1 - ALPHA / 2, transport_df) * math.sqrt(transport_var))
    lo = float(train.effect.min() - z * target_se)
    hi = float(train.effect.max() + z * target_se)
    robust_center = (lo + hi) / 2.0
    robust_radius = (hi - lo) / 2.0
    study_center, study_radius = _conformal_radius(train, target, "study.name")
    family_center, family_radius = _conformal_radius(train, target, "family")
    return [
        {"method": "transport_meta_regression", "estimate": transport, "radius": transport_radius},
        {"method": "hierarchical_meta_analysis", "estimate": hierarchical, "radius": hierarchical_radius},
        {"method": "robust_partial_identification", "estimate": robust_center, "radius": robust_radius},
        {"method": "study_split_conformal", "estimate": study_center, "radius": study_radius},
        {"method": "family_split_conformal", "estimate": family_center, "radius": family_radius},
    ]


def analyze(frame: pd.DataFrame) -> pd.DataFrame:
    usable = frame[frame.valid_d].copy()
    usable["effect"] = usable["ESCI.d"].astype(float)
    usable["variance"] = usable["ESCI.var.d"].astype(float)
    rows: list[dict[str, object]] = []
    for family in ELIGIBLE_FAMILIES:
        target_rows = usable[usable.family.eq(family)]
        train = usable[~usable.family.eq(family)]
        for _, target in target_rows.iterrows():
            for prediction in _predict(train, target):
                estimate = float(prediction["estimate"])
                radius = float(prediction["radius"])
                observed = float(target.effect)
                rows.append({
                    "target_family": family,
                    "target_study": target["study.analysis"],
                    "target_context": target.context,
                    "target_N": int(target.N),
                    "method": prediction["method"],
                    "estimate": estimate,
                    "radius": radius,
                    "width": 2 * radius,
                    "observed_effect": observed,
                    "absolute_error": abs(estimate - observed),
                    "sign_error": int(np.sign(estimate) != np.sign(observed) and observed != 0),
                    "covered": int(abs(estimate - observed) <= radius),
                    "train_n": len(train),
                })
    return pd.DataFrame(rows)


def summarize(predictions: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for method, group in predictions.groupby("method", sort=True):
        for threshold in RELEASE_THRESHOLDS:
            released = group.radius <= threshold
            selected = group[released]
            rows.append({
                "method": method,
                "threshold": threshold,
                "n_targets": len(group),
                "n_released": int(released.sum()),
                "release_rate": float(released.mean()),
                "refusal_rate": float(1 - released.mean()),
                "coverage_all": float(group.covered.mean()),
                "coverage_released": float(selected.covered.mean()) if len(selected) else float("nan"),
                "mae_all": float(group.absolute_error.mean()),
                "mae_released": float(selected.absolute_error.mean()) if len(selected) else float("nan"),
                "sign_error_all": float(group.sign_error.mean()),
                "sign_error_released": float(selected.sign_error.mean()) if len(selected) else float("nan"),
                "mean_width_released": float(selected.width.mean()) if len(selected) else float("nan"),
            })
    return pd.DataFrame(rows)


def leakage_audit(frame: pd.DataFrame, original: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for family in ELIGIBLE_FAMILIES:
        flipped = frame.copy()
        mask = flipped.family.eq(family)
        flipped.loc[mask, "ESCI.d"] = -flipped.loc[mask, "ESCI.d"]
        changed = analyze(flipped)
        left = original[original.target_family.eq(family)]
        right = changed[changed.target_family.eq(family)]
        merged = left.merge(right, on=["target_family", "target_study", "method"], suffixes=("", "_flipped"))
        rows.append(pd.DataFrame({
            "target_family": merged.target_family,
            "target_study": merged.target_study,
            "method": merged.method,
            "prediction_change": (merged.estimate - merged.estimate_flipped).abs(),
            "radius_change": (merged.radius - merged.radius_flipped).abs(),
        }))
    return pd.concat(rows, ignore_index=True)


def write_report(predictions: pd.DataFrame, summary: pd.DataFrame, leakage: pd.DataFrame) -> str:
    lines = [
        "# Many Labs 2 baseline panel under cross-effect-family holdout",
        "",
        f"The panel uses the pinned Many Labs 2 summary at commit `{COMMIT}` (SHA-256 `{DATA_SHA256}`), with the same five complete-family holdouts and ten targets as the external-validity audit.",
        "",
        "## Baselines",
        "",
        "- `transport_meta_regression`: weighted context meta-regression using the pre-existing WEIRD/NONWEIRD design metadata.",
        "- `hierarchical_meta_analysis`: Normal-Normal random-effects predictive interval with DerSimonian--Laird heterogeneity.",
        "- `robust_partial_identification`: training effect envelope plus an N-only sampling allowance.",
        "- `study_split_conformal`: leave-one-study-out absolute residual calibration.",
        "- `family_split_conformal`: leave-one-family-out residual calibration, the stricter family-level comparison.",
        "",
        "## Results",
        "",
        "| Method | threshold | release | coverage all | coverage released | MAE released | sign error released | width released |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        def fmt(x): return "NA" if pd.isna(x) else f"{x:.3f}"
        lines.append(f"| {row.method} | {row.threshold:.2f} | {row.release_rate:.3f} | {row.coverage_all:.3f} | {fmt(row.coverage_released)} | {fmt(row.mae_released)} | {fmt(row.sign_error_released)} | {fmt(row.mean_width_released)} |")
    lines += [
        "",
        f"Target-effect flip audit: maximum prediction change `{leakage.prediction_change.max():.3g}`, maximum radius change `{leakage.radius_change.max():.3g}`.",
        "",
        "## Interpretation and next step",
        "",
        "This panel closes the naming and implementation gap in the prior audit: transportability, hierarchical meta-analysis, robust partial identification, and conformal/selective baselines are now run under the same frozen family-level split. The ten targets are too few for a definitive method ranking, and held-out standardized effects remain noisy references. The central missing evidence is unchanged: no real mechanism sets U_i, independent real calibration archive, or causal target truth is available. The next feasible experiment is a pre-registered cross-intervention archive with design metadata frozen into mechanism proxies and a separate calibration split before target outcomes are read.",
    ]
    return "\n".join(lines) + "\n"


def run(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    frame = load_data()
    predictions = analyze(frame)
    summary = summarize(predictions)
    leakage = leakage_audit(frame, predictions)
    if float(leakage[["prediction_change", "radius_change"]].to_numpy().max()) > 1e-12:
        raise AssertionError("Target-effect leakage detected")
    predictions.to_csv(output / "predictions.csv", index=False, float_format="%.15g")
    summary.to_csv(output / "summary.csv", index=False, float_format="%.15g")
    leakage.to_csv(output / "leakage_audit.csv", index=False, float_format="%.15g")
    report = write_report(predictions, summary, leakage)
    (output / "report.md").write_text(report, encoding="utf-8")
    manifest = {
        "status": "complete",
        "commit": COMMIT,
        "data_url": DATA_URL,
        "data_sha256": DATA_SHA256,
        "eligible_target_families": list(ELIGIBLE_FAMILIES),
        "release_thresholds": list(RELEASE_THRESHOLDS),
        "n_target_studies": int(predictions.target_study.nunique()),
        "methods": sorted(predictions.method.unique()),
        "scope": "Baseline comparison under real Many Labs 2 cross-effect-family holdout; no mechanism labels",
        "target_outcome_fields_used_only_for_scoring": ["ESCI.d"],
        "target_effect_variance_used_only_for_eligibility": ["ESCI.var.d"],
        "source_sha256": {Path(__file__).name: sha256(Path(__file__))},
        "python": sys.version,
        "platform": platform.platform(),
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": {},
    }
    for path in output.iterdir():
        if path.is_file():
            manifest["artifacts"][path.name] = {"sha256": sha256(path), "bytes": path.stat().st_size}
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "effect_family_baselines")
    args = parser.parse_args()
    run(args.output)
    print(f"COMPLETE {args.output}")


if __name__ == "__main__":
    main()
