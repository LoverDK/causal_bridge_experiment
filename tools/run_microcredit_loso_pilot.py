"""Fail-closed descriptive Meager microcredit LOSO pilot runner.

The input in this repository is exploratory.  Common design eligibility is a
separate gate from variance and design-coordinate gates.  Consequently a
traceable range baseline may run while variance-based methods and ATLAS are
recorded as not qualified.  No real calibration claim is made.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, t

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data/microcredit_loso_pilot_input.csv"
PROTOCOL_PATHS = [
    ROOT / "MICROCREDIT_LOSO_PILOT_PROTOCOL_20260925.md",
    ROOT / "MICROCREDIT_INVITATION_ITT_PROTOCOL_20260925.md",
]
DESIGN_COLUMNS = ["individual_rand", "target_women", "apr", "market",
                  "promotion", "collateral", "loan_share"]
OUTCOME_COLUMNS = ["study_id", "effect", "se"]
REQUIRED_COLUMNS = ["study_id", "effect", "se", *DESIGN_COLUMNS,
                    "status", "variance_status", "design_vector_status"]
METHODS = ["fixed_effect", "random_effects", "design_meta_regression",
           "robust_training_range", "atlas_descriptive"]
THRESHOLDS = [0.10, 0.20, 0.40, 0.80]
PRIMARY_DELTA = 0.20
SCALE = np.array([1.0, 1.0, 100.0, 3.0, 1.0, 1.0, 120.0])
VERIFIED_VARIANCE_STATUS = "verified_assignment_level_se"
VERIFIED_DESIGN_STATUS = "verified_design_coordinates"
VERIFIED_COMMON_STATUS = "verified_common_estimand"
VERIFIED_SOURCE_STATUS = "verified_source"
UNVERIFIED_LOCATORS = {"pending", "unverified", "unknown", "none", "n/a"}
COMMON_SOURCE_FIELDS = {
    "assignment_status": "assignment_source_locator",
    "outcome_status": "outcome_source_locator",
    "stratum_status": "stratum_source_locator",
    "target_population_status": "target_population_source_locator",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_metadata() -> dict[str, object]:
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        lines = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"head": None, "dirty": None, "status_lines": [str(exc)]}
    return {"head": head, "dirty": bool(lines), "status_lines": lines}


def dependency_metadata() -> dict[str, str]:
    return {"python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "scipy": __import__("scipy").__version__}


def protocol_hashes() -> dict[str, str | None]:
    return {str(p.relative_to(ROOT)).replace("\\", "/"): (sha256(p) if p.exists() else None)
            for p in PROTOCOL_PATHS}


def interval(row: pd.Series) -> tuple[float, float]:
    return float(row.effect - 1.96 * row.se), float(row.effect + 1.96 * row.se)


def reference_relation(lo: float, hi: float, rlo: float, rhi: float) -> str:
    if lo <= rlo and hi >= rhi:
        return "contains_full"
    if hi < rlo or lo > rhi:
        return "disjoint"
    return "partial_overlap"


def fixed_effect(train: pd.DataFrame) -> tuple[float, float]:
    w = 1.0 / np.square(train.se.to_numpy(float))
    mu = float(np.dot(w, train.effect) / w.sum())
    return mu, float(norm.ppf(.975) * np.sqrt(1.0 / w.sum()))


def random_effects(train: pd.DataFrame) -> tuple[float, float] | None:
    # The frozen rule uses df=n_train-2; with two studies this rule is unavailable.
    if len(train) <= 2:
        return None
    y = train.effect.to_numpy(float); v = np.square(train.se.to_numpy(float))
    w = 1.0 / v; mu = float(np.dot(w, y) / w.sum())
    q = float(np.dot(w, np.square(y - mu)))
    c = float(w.sum() - np.dot(w, w) / w.sum())
    tau2 = max(0.0, (q - (len(train) - 1)) / c) if c > 0 else 0.0
    wr = 1.0 / (v + tau2); mu = float(np.dot(wr, y) / wr.sum())
    rad = float(t.ppf(.975, len(train) - 2) * np.sqrt(1.0 / wr.sum() + tau2))
    return mu, rad


def robust_range(train: pd.DataFrame) -> tuple[float, float]:
    lo, hi = float(train.effect.min()), float(train.effect.max())
    return (lo + hi) / 2.0, (hi - lo) / 2.0


def design_atlas(train: pd.DataFrame, target_design: pd.Series) -> tuple[float, float]:
    x = train[DESIGN_COLUMNS].to_numpy(float) / SCALE
    z = target_design[DESIGN_COLUMNS].to_numpy(float) / SCALE
    dist = np.linalg.norm(x - z, axis=1)
    w = 1.0 / np.maximum(dist, 1e-6); w /= w.sum()
    mu = float(np.dot(w, train.effect))
    radius = float(np.max(dist) + 1.96 * np.sqrt(np.dot(w ** 2, train.se ** 2)))
    return mu, radius


def predict(method: str, train: pd.DataFrame, target_design: pd.Series) -> tuple[float, float] | None:
    if method == "fixed_effect": return fixed_effect(train)
    if method == "random_effects": return random_effects(train)
    if method == "design_meta_regression":
        x = np.column_stack([np.ones(len(train)), train[DESIGN_COLUMNS].to_numpy(float) / SCALE])
        z = np.r_[1.0, target_design[DESIGN_COLUMNS].to_numpy(float) / SCALE]
        if len(train) < max(4, x.shape[1] + 1) or np.linalg.matrix_rank(x) < x.shape[1]:
            return None
        y = train.effect.to_numpy(float)
        beta = np.linalg.lstsq(x, y, rcond=None)[0]
        residual = y - x @ beta
        df = len(train) - x.shape[1]
        scale = float(np.dot(residual, residual) / df)
        leverage = float(z @ np.linalg.inv(x.T @ x) @ z)
        return float(z @ beta), float(t.ppf(.975, df) * np.sqrt(scale * (1 + leverage)))
    if method == "robust_training_range": return robust_range(train)
    if method == "atlas_descriptive": return design_atlas(train, target_design)
    raise ValueError(method)


def validate_schema(studies: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in studies.columns]
    if missing: raise ValueError(f"input is missing required columns: {missing}")
    if studies.empty or studies.study_id.duplicated().any():
        raise ValueError("input must be non-empty with unique study_id")


def qualification_audit(studies: pd.DataFrame) -> pd.DataFrame:
    records = []
    for _, row in studies.iterrows():
        common_reasons = []
        variance_reasons = []
        design_reasons = []
        if row.status != VERIFIED_COMMON_STATUS:
            common_reasons.append("common_estimand_status_not_verified")
        for status_col, source_col in COMMON_SOURCE_FIELDS.items():
            if status_col not in row.index or row[status_col] != VERIFIED_SOURCE_STATUS:
                common_reasons.append(f"{status_col}_not_verified")
            locator = row.get(source_col, None)
            if (not isinstance(locator, str) or not locator.strip()
                    or locator.strip().lower() in UNVERIFIED_LOCATORS):
                common_reasons.append(f"{source_col}_missing")
        if "target_population" not in row.index or not isinstance(row.target_population, str) or not row.target_population.strip():
            common_reasons.append("target_population_missing")
        if not np.isfinite(float(row.effect)): common_reasons.append("effect_not_finite")
        if not np.isfinite(float(row.se)) or float(row.se) <= 0: variance_reasons.append("se_not_positive_finite")
        if row.variance_status != VERIFIED_VARIANCE_STATUS:
            variance_reasons.append("variance_status_not_verified")
        for c in DESIGN_COLUMNS:
            if not np.isfinite(float(row[c])): design_reasons.append(f"design_{c}_not_finite")
        if row.design_vector_status != VERIFIED_DESIGN_STATUS:
            design_reasons.append("design_vector_status_not_verified")
        records.append({
            "study_id": row.study_id,
            "common_qualified": not common_reasons,
            "variance_qualified": not common_reasons and not variance_reasons,
            "design_qualified": not common_reasons and not design_reasons,
            "reasons": ";".join(common_reasons + variance_reasons + design_reasons),
            "common_reasons": ";".join(common_reasons),
            "variance_reasons": ";".join(variance_reasons),
            "design_reasons": ";".join(design_reasons),
            "variance_status": row.variance_status,
            "design_vector_status": row.design_vector_status,
            "target_population": row.get("target_population", None),
            **{col: row.get(col, None) for col in COMMON_SOURCE_FIELDS},
            **{col: row.get(col, None) for col in COMMON_SOURCE_FIELDS.values()},
        })
    return pd.DataFrame(records)


def method_gate(qualification: pd.DataFrame, method: str) -> tuple[bool, str]:
    if method == "robust_training_range":
        ok = bool(qualification.common_qualified.all())
        return ok, "common_gate" if ok else "common_gate_failed"
    if method in {"fixed_effect", "random_effects"}:
        ok = bool(qualification.variance_qualified.all())
        return ok, "variance_gate" if ok else "variance_gate_failed"
    if method == "design_meta_regression":
        ok = bool(qualification.variance_qualified.all() and qualification.design_qualified.all())
        return ok, "variance_and_design_gate" if ok else "variance_or_design_gate_failed"
    if method == "atlas_descriptive":
        ok = bool(qualification.variance_qualified.all() and qualification.design_qualified.all())
        return ok, "variance_and_design_gate" if ok else "variance_or_design_gate_failed"
    raise ValueError(method)


def prediction_for_target(target_id: str, designs: pd.DataFrame, train_outcomes: pd.DataFrame,
                          gates: dict[str, tuple[bool, str]]) -> pd.DataFrame:
    target_design = designs.loc[designs.study_id == target_id].iloc[0]
    train = train_outcomes.copy()
    train = train.merge(designs, on="study_id", how="left", validate="one_to_one")
    if target_id in set(train.study_id): raise AssertionError("target outcome leaked into training")
    rows = []
    for method in METHODS:
        gate_ok, gate_reason = gates[method]
        if not gate_ok:
            rows.append({"target": target_id, "method": method, "n_train": len(train),
                         "status": "not_qualified", "qualification_reason": gate_reason,
                         "estimate": np.nan, "lower": np.nan, "upper": np.nan,
                         "radius": np.nan, "width": np.inf, "released": False})
            continue
        if not len(train):
            rows.append({"target": target_id, "method": method, "n_train": 0,
                         "status": "not_identified", "qualification_reason": "no_training_studies",
                         "estimate": np.nan, "lower": np.nan, "upper": np.nan,
                         "radius": np.nan, "width": np.inf, "released": False})
            continue
        if method == "robust_training_range" and len(train) < 2:
            result = None
            reason = "at_least_two_training_studies_required"
        else:
            result = predict(method, train, target_design[DESIGN_COLUMNS])
            reason = "frozen_df_rule_unavailable" if method == "random_effects" else "design_regression_not_identified"
        if result is None:
            rows.append({"target": target_id, "method": method, "n_train": len(train),
                         "status": "not_identified", "qualification_reason": reason,
                         "estimate": np.nan, "lower": np.nan, "upper": np.nan,
                         "radius": np.nan, "width": np.inf, "released": False})
        else:
            estimate, radius = result
            rows.append({"target": target_id, "method": method, "n_train": len(train),
                         "status": "computed", "qualification_reason": gate_reason,
                         "estimate": estimate, "lower": estimate - radius, "upper": estimate + radius,
                         "radius": radius, "width": 2 * radius,
                         "released": bool(radius <= PRIMARY_DELTA)})
    return pd.DataFrame(rows)


def score_predictions(predictions: pd.DataFrame, outcomes: pd.DataFrame,
                      qualification: pd.DataFrame) -> pd.DataFrame:
    outcome_by_id = outcomes.set_index("study_id")
    variance_by_id = qualification.set_index("study_id")["variance_qualified"]
    rows = predictions.copy()
    rows["reference_lower"] = np.nan
    rows["reference_upper"] = np.nan
    rows["point_error"] = np.nan
    rows["sign_error"] = pd.Series([None] * len(rows), dtype=object)
    rows["released_error_beyond_delta"] = pd.Series([None] * len(rows), dtype=object)
    rows["reference_relation"] = "not_run"
    for i, row in rows.iterrows():
        target = outcome_by_id.loc[row.target]
        if not bool(variance_by_id.loc[row.target]) or not np.isfinite(float(target.se)) or float(target.se) <= 0:
            rows.loc[i, "reference_relation"] = "reference_unavailable"
            if row.status == "computed":
                rows.loc[i, "point_error"] = abs(float(row.estimate) - float(target.effect))
            continue
        rlo, rhi = interval(target)
        rows.loc[i, "reference_lower"] = rlo; rows.loc[i, "reference_upper"] = rhi
        if row.status != "computed": continue
        estimate = float(row.estimate); radius = float(row.radius)
        rows.loc[i, "point_error"] = abs(estimate - float(target.effect))
        rows.loc[i, "sign_error"] = bool(np.sign(estimate) != np.sign(float(target.effect))) if estimate and target.effect else False
        rows.loc[i, "released_error_beyond_delta"] = bool(row.released and abs(estimate - float(target.effect)) > PRIMARY_DELTA)
        rows.loc[i, "reference_relation"] = reference_relation(estimate-radius, estimate+radius, rlo, rhi)
    return rows


def write_manifest(out: Path, input_path: Path, qualification: pd.DataFrame,
                   gates: dict[str, tuple[bool, str]], status: str, output_files: list[str]) -> None:
    missing_outputs = [name for name in output_files if not (out / name).is_file()]
    if missing_outputs:
        raise FileNotFoundError(f"missing expected outputs: {missing_outputs}")
    manifest = {
        "status": status, "run_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": (str(input_path.resolve().relative_to(ROOT)).replace("\\", "/") if input_path.resolve().is_relative_to(ROOT) else "external:" + input_path.name),
        "input_sha256": sha256(input_path),
        "runner_path": "tools/run_microcredit_loso_pilot.py", "runner_sha256": sha256(Path(__file__).resolve()),
        "protocol_hashes": protocol_hashes(), "git": git_metadata(),
        "dependencies": dependency_metadata(), "n_input_studies": int(len(qualification)),
        "n_qualified_studies": int(qualification.common_qualified.sum()),
        "qualification": qualification.to_dict(orient="records"),
        "method_gates": {m: {"qualified": bool(ok), "reason": reason} for m, (ok, reason) in gates.items()},
        "thresholds": THRESHOLDS, "primary_threshold": PRIMARY_DELTA,
        "calibration_claim": False, "raw_records_committed": False,
        "interpretation": "noisy-reference descriptive pilot only; no real calibration claim",
        "output_sha256": {name: sha256(out / name) for name in output_files},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run(out: Path, input_path: Path = INPUT_PATH) -> None:
    out = Path(out); input_path = Path(input_path)
    if out.exists(): raise FileExistsError(f"refusing to overwrite existing output directory: {out}")
    if not input_path.is_file(): raise FileNotFoundError(input_path)
    missing_protocols = [str(p) for p in PROTOCOL_PATHS if not p.is_file()]
    if missing_protocols: raise FileNotFoundError(f"missing protocols: {missing_protocols}")
    start_hashes = {"input": sha256(input_path), **protocol_hashes()}
    out.mkdir(parents=True, exist_ok=True)
    studies = pd.read_csv(input_path); validate_schema(studies)
    qualification = qualification_audit(studies)
    qualification.to_csv(out / "qualification_audit.csv", index=False)
    gates = {m: method_gate(qualification, m) for m in METHODS}
    if not qualification.common_qualified.all():
        if {"input": sha256(input_path), **protocol_hashes()} != start_hashes:
            raise RuntimeError("input or protocol changed during audit")
        write_manifest(out, input_path, qualification, gates, "audit_only", ["qualification_audit.csv"])
        return
    designs = studies[["study_id", *DESIGN_COLUMNS]].copy()
    outcomes = studies[OUTCOME_COLUMNS].copy()
    # Prediction phase: no target effect/SE is passed to prediction_for_target.
    prediction = pd.concat([
        prediction_for_target(t, designs, outcomes.loc[outcomes.study_id != t], gates)
        for t in studies.study_id
    ], ignore_index=True)
    prediction.to_csv(out / "predictions_before_scoring.csv", index=False)
    # Actual saved-path leakage audit. Change only each held-out target per split.
    leakage_parts = []
    altered_targets = {}
    for target_id in studies.study_id:
        altered = outcomes.copy()
        original_effect = float(outcomes.loc[outcomes.study_id == target_id, "effect"].iloc[0])
        sentinel_effect = -original_effect if original_effect != 0 else 1.0
        altered.loc[altered.study_id == target_id, "effect"] = sentinel_effect
        altered.loc[altered.study_id == target_id, "se"] = altered.loc[altered.study_id == target_id, "se"] * 3 + 1
        altered_targets[target_id] = altered.loc[altered.study_id == target_id].iloc[0].copy()
        leakage_parts.append(prediction_for_target(
            target_id, designs, altered.loc[altered.study_id != target_id], gates
        ))
    altered_prediction = pd.concat(leakage_parts, ignore_index=True)
    altered_prediction.to_csv(out / "leakage_predictions_before_scoring.csv", index=False)
    saved = pd.read_csv(out / "predictions_before_scoring.csv")
    altered_saved = pd.read_csv(out / "leakage_predictions_before_scoring.csv")
    compare = ["target", "method", "status", "qualification_reason", "estimate", "lower", "upper", "radius", "width", "released"]
    leakage = []
    for target_id in studies.study_id:
        left = saved.loc[saved.target == target_id].reset_index(drop=True)
        right = altered_saved.loc[altered_saved.target == target_id].reset_index(drop=True)
        diffs = []
        for col in ["estimate", "lower", "upper", "radius"]:
            a, b = left[col].to_numpy(float), right[col].to_numpy(float)
            mask = np.isfinite(a) & np.isfinite(b)
            diffs.extend(np.abs(a[mask] - b[mask]).tolist())
        original_target = outcomes.loc[outcomes.study_id == target_id].iloc[0]
        altered_target = altered_targets[target_id]
        leakage.append({"target": target_id,
                        "target_effect_changed": bool(original_target.effect != altered_target.effect),
                        "effect_perturbation": "sign_flip" if float(original_target.effect) != 0 else "nonzero_sentinel",
                        "target_se_changed": bool(original_target.se != altered_target.se),
                        "predictions_unchanged": bool(left[compare].equals(right[compare])),
                        "width_unchanged": bool(left.width.equals(right.width)),
                        "release_unchanged": bool(left.released.equals(right.released)),
                        "max_prediction_change": max(diffs or [0.0])})
    pd.DataFrame(leakage).to_csv(out / "leakage_audit.csv", index=False)
    # Scoring phase begins after prediction file is persisted and reopened.
    result = score_predictions(saved, outcomes, qualification)
    result.to_csv(out / "loso_results.csv", index=False)
    frontier = []
    for delta in THRESHOLDS:
        for method, group in result.groupby("method", sort=True):
            computed = group[group.status == "computed"]; released = computed[computed.radius <= delta]
            frontier.append({"delta": delta, "method": method, "n_targets": len(group), "n_computed": len(computed),
                             "n_released": len(released), "release_rate": len(released)/len(computed) if len(computed) else np.nan,
                             "mean_width": computed.width.replace(np.inf, np.nan).mean() if len(computed) else np.nan,
                             "released_mean_point_error": released.point_error.mean() if len(released) else np.nan})
    pd.DataFrame(frontier).to_csv(out / "release_frontier.csv", index=False)
    summary = []
    for method, group in result.groupby("method", sort=True):
        computed = group[group.status == "computed"]
        summary.append({"method": method, "n_targets": len(group), "n_computed": len(computed),
                        "n_released": int(computed.released.sum()) if len(computed) else 0,
                        "release_rate": computed.released.mean() if len(computed) else np.nan,
                        "mean_width": computed.width.replace(np.inf, np.nan).mean() if len(computed) else np.nan,
                        "mean_point_error": computed.point_error.mean() if len(computed) else np.nan,
                        "sign_errors": int(computed.sign_error.sum()) if len(computed) else 0,
                        "released_target_errors": int(computed.released_error_beyond_delta.sum()) if len(computed) else 0,
                        "released_target_risk": (computed.released_error_beyond_delta.sum()/computed.released.sum()) if len(computed) and computed.released.sum() else np.nan,
                        "contains_full": int((computed.reference_relation == "contains_full").sum()) if len(computed) else 0,
                        "disjoint": int((computed.reference_relation == "disjoint").sum()) if len(computed) else 0,
                        "partial_overlap": int((computed.reference_relation == "partial_overlap").sum()) if len(computed) else 0})
    pd.DataFrame(summary).to_csv(out / "loso_summary.csv", index=False)
    studies.to_csv(out / "pilot_input_design_and_reference.csv", index=False)
    if {"input": sha256(input_path), **protocol_hashes()} != start_hashes:
        raise RuntimeError("input or protocol changed during run")
    write_manifest(out, input_path, qualification, gates, "numeric_descriptive_pilot",
                   ["qualification_audit.csv", "predictions_before_scoring.csv", "leakage_predictions_before_scoring.csv",
                    "leakage_audit.csv", "loso_results.csv", "release_frontier.csv", "loso_summary.csv",
                    "pilot_input_design_and_reference.csv"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    args = parser.parse_args()
    run(args.output, args.input)
