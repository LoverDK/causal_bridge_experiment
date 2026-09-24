"""Cross-effect-family holdout audit for the public Many Labs 2 summary.

This is an external-validity stress test, not a real mechanism-set certificate:
the public summary supplies study-level standardized effects and variances, but
no independently audited mechanism labels.  The target family is frozen before
the target effect is read.  Only training-family effects, variances, sample
size, and the WEIRD metadata flag are used to form predictions and release
decisions.
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
from scipy.stats import norm, t


ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "manylabs2_original_effects.csv"
COMMIT = "acef63fc397b8dce7f0b00f863bcea78d324bea8"
DATA_SHA256 = "78b3432bebb798595ebb08ee10fb68d3f6f59cd5e0ab49606cfb6835eb226406"
DATA_URL = (
    "https://raw.githubusercontent.com/ManyLabsOpenScience/ManyLabs2/"
    f"{COMMIT}/OSFdata/!!RawData/ML2_OriginalEffects.csv"
)
ELIGIBLE_FAMILIES = ("Hauser", "Huang", "Miyamoto", "Ross", "Savani")
ALPHA = 0.05
RELEASE_THRESHOLDS = (0.20, 0.40, 0.60, 0.80, 1.00)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    if sha256(path) != DATA_SHA256:
        raise RuntimeError("The input is not the pinned Many Labs 2 summary file")
    frame = pd.read_csv(path)
    required = {"study.name", "study.analysis", "study.analysis.ori", "N", "ESCI.d", "ESCI.var.d"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    frame = frame.copy()
    frame["family"] = frame["study.name"].astype(str)
    frame["context"] = np.where(
        frame["study.analysis.ori"].astype(str).str.contains("NONWEIRD", case=False),
        "NONWEIRD", "WEIRD"
    )
    frame["valid_d"] = (
        pd.to_numeric(frame["ESCI.d"], errors="coerce").notna()
        & pd.to_numeric(frame["ESCI.var.d"], errors="coerce").notna()
        & (pd.to_numeric(frame["ESCI.var.d"], errors="coerce") > 0)
        & (pd.to_numeric(frame["N"], errors="coerce") > 1)
    )
    return frame


def _fit_fixed(train: pd.DataFrame) -> tuple[float, float]:
    y = train["effect"].to_numpy(float)
    v = train["variance"].to_numpy(float)
    w = 1.0 / v
    return float(np.sum(w * y) / np.sum(w)), float(1.0 / np.sum(w))


def _fit_random(train: pd.DataFrame) -> tuple[float, float, float]:
    y = train["effect"].to_numpy(float)
    v = train["variance"].to_numpy(float)
    mean, fixed_var = _fit_fixed(train)
    q = float(np.sum((y - mean) ** 2 / v))
    w = 1.0 / v
    c = float(np.sum(w) - np.sum(w * w) / np.sum(w))
    tau2 = max(0.0, (q - (len(y) - 1)) / c) if c > 0 else 0.0
    rw = 1.0 / (v + tau2)
    return float(np.sum(rw * y) / np.sum(rw)), float(1.0 / np.sum(rw)), float(tau2)


def _design_se(n: float) -> float:
    # Conservative outcome-blind scale for a standardized mean difference.
    # It uses only the target sample size, not the target effect or variance.
    return math.sqrt(4.0 / float(n))


def _prediction_rows(train: pd.DataFrame, target: pd.Series) -> list[dict]:
    z = float(norm.ppf(1 - ALPHA / 2))
    fixed, fixed_var = _fit_fixed(train)
    random, random_var, tau2 = _fit_random(train)
    target_se = _design_se(target["N"])
    fixed_radius = z * math.sqrt(fixed_var + target_se**2)
    random_radius = float(t.ppf(1 - ALPHA / 2, max(len(train) - 2, 1))) * math.sqrt(
        random_var + tau2 + target_se**2
    )
    # A conservative range baseline: it says only that the target is in the
    # observed training-family envelope up to a design-only sampling allowance.
    range_low = float(train.effect.min()) - z * target_se
    range_high = float(train.effect.max()) + z * target_se
    range_center = (range_low + range_high) / 2.0
    range_radius = (range_high - range_low) / 2.0
    # Context-stratified transport baseline, falling back to the full pool.
    same = train[train.context == target["context"]]
    context_train = same if len(same) >= 3 else train
    context_mean, context_var = _fit_fixed(context_train)
    context_radius = z * math.sqrt(context_var + target_se**2)
    # Family-level split conformal: calibrate on leave-one-family-out family
    # means inside the training pool, then fit the final point on all training.
    family_residuals = []
    for family, group in train.groupby("family", sort=True):
        other = train[train.family != family]
        if len(other) < 3:
            continue
        loo_mean, _ = _fit_fixed(other)
        group_mean, _ = _fit_fixed(group)
        family_residuals.append(abs(group_mean - loo_mean))
    if not family_residuals:
        raise RuntimeError("No family-level conformal calibration units")
    family_residuals = np.sort(np.asarray(family_residuals, float))
    rank = min(len(family_residuals) - 1, int(math.ceil((len(family_residuals) + 1) * (1 - ALPHA))) - 1)
    conformal_radius = float(family_residuals[rank] + z * target_se)
    return [
        {"method": "fixed_effects", "estimate": fixed, "radius": fixed_radius},
        {"method": "random_effects", "estimate": random, "radius": random_radius},
        {"method": "context_fixed_effects", "estimate": context_mean, "radius": context_radius},
        {"method": "robust_training_range", "estimate": range_center, "radius": range_radius},
        {"method": "family_split_conformal", "estimate": fixed, "radius": conformal_radius},
    ]


def analyze(frame: pd.DataFrame) -> pd.DataFrame:
    usable = frame[frame.valid_d].copy()
    usable["effect"] = usable["ESCI.d"].astype(float)
    usable["variance"] = usable["ESCI.var.d"].astype(float)
    rows = []
    for family in ELIGIBLE_FAMILIES:
        target_rows = usable[usable.family == family]
        train = usable[~usable.family.eq(family)]
        if len(target_rows) == 0 or len(train) < 3:
            raise RuntimeError(f"Invalid holdout split for {family}")
        for _, target in target_rows.iterrows():
            for prediction in _prediction_rows(train, target):
                estimate = float(prediction["estimate"])
                radius = float(prediction["radius"])
                observed = float(target["effect"])
                rows.append({
                    "target_family": family,
                    "target_study": target["study.analysis"],
                    "target_context": target["context"],
                    "target_N": int(target["N"]),
                    "method": prediction["method"],
                    "estimate": estimate,
                    "radius": radius,
                    "width": 2 * radius,
                    "lower": estimate - radius,
                    "upper": estimate + radius,
                    "observed_effect": observed,
                    "absolute_error": abs(estimate - observed),
                    "sign_error": int(np.sign(estimate) != np.sign(observed) and observed != 0),
                    "covered": int(abs(estimate - observed) <= radius),
                    "train_n": int(len(train)),
                    "train_families": "|".join(sorted(train.family.unique())),
                })
    return pd.DataFrame(rows)


def summarize(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
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
                "sign_error_all": float(group.sign_error.mean()),
                "mae_all": float(group.absolute_error.mean()),
                "coverage_released": float(selected.covered.mean()) if len(selected) else float("nan"),
                "sign_error_released": float(selected.sign_error.mean()) if len(selected) else float("nan"),
                "mae_released": float(selected.absolute_error.mean()) if len(selected) else float("nan"),
                "mean_width_released": float(selected.width.mean()) if len(selected) else float("nan"),
            })
    return pd.DataFrame(rows)


def leakage_audit(frame: pd.DataFrame, predictions: pd.DataFrame) -> pd.DataFrame:
    # Perturb one held-out family at a time.  Other eligible families remain
    # unchanged because they are valid members of the training pool for this
    # particular split.
    key = ["target_family", "target_study", "method"]
    audits = []
    for family in ELIGIBLE_FAMILIES:
        flipped = frame.copy()
        mask = flipped["family"].eq(family)
        flipped.loc[mask, "ESCI.d"] = -flipped.loc[mask, "ESCI.d"]
        changed = analyze(flipped)
        original = predictions[predictions.target_family.eq(family)]
        perturbed = changed[changed.target_family.eq(family)]
        merged = original.merge(perturbed, on=key, suffixes=("", "_flipped"))
        merged["prediction_change"] = (merged.estimate - merged.estimate_flipped).abs()
        merged["radius_change"] = (merged.radius - merged.radius_flipped).abs()
        audits.append(merged[key + ["prediction_change", "radius_change"]])
    return pd.concat(audits, ignore_index=True)


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
    usable = frame[frame.valid_d]
    exclusions = frame[~frame.valid_d][["study.analysis", "study.name", "ESCI.d", "ESCI.var.d"]].copy()
    predictions.to_csv(output / "predictions.csv", index=False, float_format="%.15g")
    summary.to_csv(output / "summary.csv", index=False, float_format="%.15g")
    leakage.to_csv(output / "leakage_audit.csv", index=False, float_format="%.15g")
    usable[["study.analysis", "family", "N", "context", "ESCI.d", "ESCI.var.d"]].to_csv(
        output / "included_studies.csv", index=False, float_format="%.15g"
    )
    exclusions.to_csv(output / "excluded_studies.csv", index=False)
    manifest = {
        "status": "complete",
        "commit": COMMIT,
        "data_url": DATA_URL,
        "data_sha256": DATA_SHA256,
        "eligible_target_families": list(ELIGIBLE_FAMILIES),
        "alpha": ALPHA,
        "release_thresholds": list(RELEASE_THRESHOLDS),
        "n_raw_rows": int(len(frame)),
        "n_included_rows": int(len(usable)),
        "n_excluded_rows": int(len(exclusions)),
        "n_target_studies": int(len(predictions) // 5),
        "scope": "Real Many Labs 2 cross-effect-family external-validity stress test; no mechanism labels",
        "outcome_blind_fields": ["N", "study.analysis.ori context", "training effects", "training variances"],
        "target_outcome_fields_used_only_for_scoring": ["ESCI.d"],
        "target_effect_variance_used_only_for_eligibility": ["ESCI.var.d"],
        "source_sha256": {Path(__file__).name: sha256(Path(__file__))},
        "python": sys.version,
        "platform": platform.platform(),
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": {},
    }
    for p in output.iterdir():
        if p.is_file():
            manifest["artifacts"][p.name] = {"sha256": sha256(p), "bytes": p.stat().st_size}
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = write_report(frame, predictions, summary, leakage)
    (output / "report.md").write_text(report, encoding="utf-8")
    manifest["artifacts"]["report.md"] = {"sha256": sha256(output / "report.md"), "bytes": (output / "report.md").stat().st_size}
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_report(frame: pd.DataFrame, predictions: pd.DataFrame, summary: pd.DataFrame, leakage: pd.DataFrame) -> str:
    lines = [
        "# Many Labs 2 cross-effect-family holdout audit",
        "",
        f"- Pinned source commit: `{COMMIT}`; SHA-256 `{DATA_SHA256}`.",
        f"- Eligible target families frozen before scoring: `{', '.join(ELIGIBLE_FAMILIES)}`.",
        f"- Included records: {int(frame.valid_d.sum())}/{len(frame)}; target studies: {predictions.target_study.nunique()}.",
        "- The target `ESCI.d` is read only for the final score. Predictions and release/refusal decisions use training records, target N, and the pre-existing WEIRD/NONWEIRD metadata flag.",
        "",
        "## Methods",
        "",
        "`fixed_effects` and `random_effects` are inverse-variance pooled and DerSimonian--Laird baselines. `context_fixed_effects` pools the same WEIRD context when at least three training records exist. `robust_training_range` reports the training effect envelope enlarged by a conservative N-only sampling allowance. `family_split_conformal` uses leave-one-family-out residuals within the training pool.",
        "",
        "## Results",
        "",
        "| Method | threshold | release | coverage all | coverage released | MAE released | sign error released | width released |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        def fmt(x): return "NA" if pd.isna(x) else f"{x:.3f}"
        lines.append(f"| {row['method']} | {row['threshold']:.2f} | {row['release_rate']:.3f} | {row['coverage_all']:.3f} | {fmt(row['coverage_released'])} | {fmt(row['mae_released'])} | {fmt(row['sign_error_released'])} | {fmt(row['mean_width_released'])} |")
    lines += [
        "",
        f"Leakage audit maximum prediction change after flipping all held-out target effects: `{leakage.prediction_change.max():.3g}`; maximum radius change: `{leakage.radius_change.max():.3g}`.",
        "",
        "## Boundary and next step",
        "",
        "This experiment adds real cross-effect-family external-validity evidence and tests refusal, interval width, noisy-reference coverage, absolute error, and sign error without target-outcome leakage. It does not satisfy the strongest original requirement: the public summary has no independently audited real mechanism sets U_i, no real calibration archive frozen before target outcomes, and no causal truth for the held-out effects. The next feasible experiment is a preregistered or newly collected cross-intervention archive with design metadata defining mechanism proxies before outcomes are read, an independent calibration split, and the same family-level holdout plus transportability, hierarchical, robust partial-identification, and conformal baselines.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "effect_family_holdout")
    args = parser.parse_args()
    run(args.output)
    print(f"COMPLETE {args.output}")


if __name__ == "__main__":
    main()
