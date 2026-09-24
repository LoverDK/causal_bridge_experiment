"""Expanded sensitivity panel holding out every eligible Many Labs 2 family.

This keeps the original five-family panel unchanged and asks whether its
release/coverage pattern depends on selecting only families with two studies.
The eligibility rule is fixed by the pinned author summary; all 23 eligible
families and all 28 valid study-level effects are targets in turn.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from run_effect_family_baselines import (
    RELEASE_THRESHOLDS,
    _predict,
    load_data,
)
from run_effect_family_holdout import COMMIT, DATA_SHA256, DATA_URL


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    usable = frame[frame.valid_d].copy()
    usable["effect"] = usable["ESCI.d"].astype(float)
    usable["variance"] = usable["ESCI.var.d"].astype(float)
    return usable


def analyze_all(frame: pd.DataFrame) -> pd.DataFrame:
    usable = prepare(frame)
    target_families = tuple(sorted(usable.family.unique()))
    rows: list[dict[str, object]] = []
    for family in target_families:
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
                "n_target_families": group.target_family.nunique(),
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
    audits = []
    families = sorted(prepare(frame).family.unique())
    for family in families:
        flipped = frame.copy()
        mask = flipped.family.eq(family)
        flipped.loc[mask, "ESCI.d"] = -flipped.loc[mask, "ESCI.d"]
        changed = analyze_all(flipped)
        left = original[original.target_family.eq(family)]
        right = changed[changed.target_family.eq(family)]
        merged = left.merge(right, on=["target_family", "target_study", "method"], suffixes=("", "_flipped"))
        audits.append(pd.DataFrame({
            "target_family": merged.target_family,
            "target_study": merged.target_study,
            "method": merged.method,
            "prediction_change": (merged.estimate - merged.estimate_flipped).abs(),
            "radius_change": (merged.radius - merged.radius_flipped).abs(),
        }))
    return pd.concat(audits, ignore_index=True)


def write_report(predictions: pd.DataFrame, summary: pd.DataFrame, leakage: pd.DataFrame) -> str:
    lines = [
        "# All-family sensitivity panel under Many Labs 2 holdout",
        "",
        f"The panel uses the pinned author summary at commit `{COMMIT}` (SHA-256 `{DATA_SHA256}`), with every eligible family held out in turn.",
        f"There are {predictions.target_family.nunique()} target families and {predictions.target_study.nunique()} target studies; all 28 valid Cohen's d records are scored once.",
        "",
        "This is a sensitivity analysis for the five-family panel. It is not a causal mechanism certificate: the references are noisy study-level standardized effects and the source contains no U_i labels or causal truth.",
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
        "## Interpretation",
        "",
        "The all-family panel tests whether the original five-family conclusions are driven by target selection. It remains an external-validity stress test only. The next evidence step is a pre-registered cross-intervention archive with design-metadata mechanism proxies and an independent calibration split frozen before target outcomes.",
    ]
    return "\n".join(lines) + "\n"


def run(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    frame = load_data()
    predictions = analyze_all(frame)
    summary = summarize(predictions)
    leakage = leakage_audit(frame, predictions)
    if float(leakage[["prediction_change", "radius_change"]].to_numpy().max()) > 1e-12:
        raise AssertionError("Target-effect leakage detected")
    predictions.to_csv(output / "predictions.csv", index=False, float_format="%.15g")
    summary.to_csv(output / "summary.csv", index=False, float_format="%.15g")
    leakage.to_csv(output / "leakage_audit.csv", index=False, float_format="%.15g")
    (output / "report.md").write_text(write_report(predictions, summary, leakage), encoding="utf-8")
    manifest = {
        "status": "complete",
        "commit": COMMIT,
        "data_url": DATA_URL,
        "data_sha256": DATA_SHA256,
        "target_families": sorted(prepare(frame).family.unique()),
        "n_target_families": int(predictions.target_family.nunique()),
        "n_target_studies": int(predictions.target_study.nunique()),
        "methods": sorted(predictions.method.unique()),
        "release_thresholds": list(RELEASE_THRESHOLDS),
        "scope": "All eligible-family external-validity sensitivity; no mechanism labels",
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
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "effect_family_baselines_all")
    args = parser.parse_args()
    run(args.output)
    print(f"COMPLETE {args.output}")


if __name__ == "__main__":
    main()
