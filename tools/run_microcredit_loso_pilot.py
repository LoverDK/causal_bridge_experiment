"""Run the frozen, descriptive Meager microcredit LOSO pilot.

Only study-level summaries copied from the authorized package's
``data/import_organise_data_v7.R`` are used.  No individual record is written
or shipped.  The three-row compatible set is intentionally small: this script
must refuse methods that require more independent training studies.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, t


STUDIES = pd.DataFrame(
    [
        # effect and se are the package's reported profit coefficients (lines
        # 749--750), converted by the package's own factors (741--753).
        dict(study_id="angelucci_mexico", effect=0.0, se=4.003322634607566,
             apr=100.0, target_women=1.0, market=2.0, promotion=1.0,
             collateral=0.0, loan_share=6.0, individual_rand=0.0,
             source="data/import_organise_data_v7.R:741-753,854-865",
             effect_source="reported_coefficients_profit[1], reported_coefficients_profit_sds[1]",
             reference_source="authorized OpenICPSR V1 package; study paper and import script",
             status="compatible_pilot"),
        dict(study_id="banerjee_india_endline1", effect=15.341039717051054,
             se=13.607588901565059, apr=24.0, target_women=1.0, market=3.0,
             promotion=0.0, collateral=0.0, loan_share=22.0,
             individual_rand=0.0,
             source="data/import_organise_data_v7.R:415-474,741-753",
             effect_source="reported_coefficients_profit[4], reported_coefficients_profit_sds[4]",
             reference_source="authorized OpenICPSR V1 package; endline 1 design and do-files",
             status="compatible_pilot"),
        dict(study_id="crepon_morocco", effect=17.892200606817777,
             se=10.797786899875067, apr=13.5, target_women=0.0, market=0.0,
             promotion=1.0, collateral=0.0, loan_share=21.0,
             individual_rand=0.0,
             source="data/import_organise_data_v7.R:489-560,741-753",
             effect_source="reported_coefficients_profit[5], reported_coefficients_profit_sds[5]",
             reference_source="authorized OpenICPSR V1 package; endline outcome construction and pair-clustered do-file",
             status="compatible_pilot"),
    ]
)

DESIGN_COLUMNS = ["individual_rand", "target_women", "apr", "market",
                  "promotion", "collateral", "loan_share"]
SCALE = np.array([1.0, 1.0, 100.0, 3.0, 1.0, 1.0, 120.0])


def _interval(row: pd.Series) -> tuple[float, float]:
    return float(row.effect - 1.96 * row.se), float(row.effect + 1.96 * row.se)


def _reference_relation(lo: float, hi: float, rlo: float, rhi: float) -> str:
    if lo <= rlo and hi >= rhi:
        return "contains_full"
    if hi < rlo or lo > rhi:
        return "disjoint"
    return "partial_overlap"


def fixed_effect(train: pd.DataFrame, target_se: float) -> tuple[float, float]:
    w = 1.0 / np.square(train.se.to_numpy())
    mu = float(np.dot(w, train.effect) / w.sum())
    rad = float(norm.ppf(.975) * np.sqrt(1.0 / w.sum() + target_se**2))
    return mu, rad


def random_effects(train: pd.DataFrame, target_se: float) -> tuple[float, float] | None:
    # The frozen protocol requires a t predictive radius with df=n_train-2.
    # With two training studies df=0; returning None is a deliberate refusal.
    if len(train) <= 2:
        return None
    y = train.effect.to_numpy(); v = np.square(train.se.to_numpy())
    w = 1.0 / v; mu = float(np.dot(w, y) / w.sum())
    q = float(np.dot(w, np.square(y - mu)))
    c = float(w.sum() - np.dot(w, w) / w.sum())
    tau2 = max(0.0, (q - (len(train) - 1)) / c) if c > 0 else 0.0
    wr = 1.0 / (v + tau2)
    mu = float(np.dot(wr, y) / wr.sum())
    df = len(train) - 2
    rad = float(t.ppf(.975, df) * np.sqrt(1.0 / wr.sum() + tau2 + target_se**2))
    return mu, rad


def robust_range(train: pd.DataFrame, target_se: float) -> tuple[float, float]:
    lo, hi = float(train.effect.min()), float(train.effect.max())
    extra = 1.96 * target_se
    return (lo + hi) / 2.0, (hi - lo) / 2.0 + extra


def design_atlas(train: pd.DataFrame, target: pd.Series) -> tuple[float, float]:
    x = train[DESIGN_COLUMNS].to_numpy(float) / SCALE
    z = target[DESIGN_COLUMNS].to_numpy(float) / SCALE
    dist = np.linalg.norm(x - z, axis=1)
    # Fixed inverse-distance weights and an uncalibrated descriptive envelope.
    w = 1.0 / np.maximum(dist, 1e-6)
    w /= w.sum()
    mu = float(np.dot(w, train.effect))
    radius = float(np.max(dist) + 1.96 * np.sqrt(np.dot(w**2, train.se**2)))
    return mu, radius


def predict(method: str, train: pd.DataFrame, target: pd.Series) -> tuple[float, float] | None:
    if method == "fixed_effect":
        return fixed_effect(train, float(target.se))
    if method == "random_effects":
        return random_effects(train, float(target.se))
    if method == "robust_training_range":
        return robust_range(train, float(target.se))
    if method == "atlas_descriptive":
        return design_atlas(train, target)
    if method == "design_meta_regression":
        # The three-row compatible set leaves only two training rows. A full
        # seven-coordinate regression is therefore not identified.
        return None
    raise ValueError(method)


def run(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    methods = ["fixed_effect", "random_effects", "design_meta_regression",
               "robust_training_range", "atlas_descriptive"]
    rows: list[dict[str, object]] = []
    leakage: list[dict[str, object]] = []
    for target_id in STUDIES.study_id:
        target = STUDIES[STUDIES.study_id == target_id].iloc[0]
        train = STUDIES[STUDIES.study_id != target_id].copy()
        rlo, rhi = _interval(target)
        for method in methods:
            result = predict(method, train, target)
            if result is None:
                rows.append(dict(target=target_id, method=method,
                                 n_train=len(train), status="not_identified",
                                 reference_lower=rlo, reference_upper=rhi,
                                 estimate=np.nan, lower=np.nan, upper=np.nan,
                                 width=np.inf, released=False,
                                 point_error=np.nan, reference_relation="not_run"))
                continue
            estimate, radius = result
            rows.append(dict(target=target_id, method=method,
                             n_train=len(train), status="computed",
                             reference_lower=rlo, reference_upper=rhi,
                             estimate=estimate, lower=estimate-radius,
                             upper=estimate+radius, width=2*radius,
                             radius=radius, released=radius <= .20,
                             point_error=abs(estimate-target.effect),
                             reference_relation=_reference_relation(
                                 estimate-radius, estimate+radius, rlo, rhi)))
        # Target effect is not passed to prediction. Replacing it leaves every
        # serialized prediction/release decision unchanged.
        changed = target.copy(); changed.effect = -float(changed.effect)
        changed_rows = []
        for method in methods:
            result = predict(method, train, changed)
            changed_rows.append(None if result is None else tuple(float(x) for x in result))
        original_rows = []
        for method in methods:
            result = predict(method, train, target)
            original_rows.append(None if result is None else tuple(float(x) for x in result))
        leakage.append(dict(target=target_id,
                            target_effect_flipped=True,
                            predictions_unchanged=changed_rows == original_rows,
                            max_prediction_change=max(
                                [max(abs(a-b) for a,b in zip(x,y))
                                 for x,y in zip(original_rows,changed_rows)
                                 if x is not None and y is not None] or [0.0])))

    result = pd.DataFrame(rows)
    result.to_csv(out / "loso_results.csv", index=False)
    frontier = []
    for delta in [0.10, 0.20, 0.40, 0.80]:
        for method, group in result.groupby("method", sort=True):
            computed = group[group.status == "computed"]
            released = computed[computed.radius <= delta] if len(computed) else computed
            frontier.append(dict(delta=delta, method=method,
                                n_targets=len(group), n_computed=len(computed),
                                n_released=len(released),
                                release_rate=float(len(released)/len(computed)) if len(computed) else np.nan,
                                mean_width=float(computed.width.replace(np.inf, np.nan).mean()) if len(computed) else np.nan,
                                released_mean_point_error=float(released.point_error.mean()) if len(released) else np.nan))
    pd.DataFrame(frontier).to_csv(out / "release_frontier.csv", index=False)
    pd.DataFrame(leakage).to_csv(out / "leakage_audit.csv", index=False)
    STUDIES.to_csv(out / "pilot_input_design_and_reference.csv", index=False)
    summary = []
    for method, g in result.groupby("method", sort=True):
        computed = g[g.status == "computed"]
        summary.append(dict(method=method, n_targets=len(g), n_computed=len(computed),
                            n_released=int(computed.released.sum()) if len(computed) else 0,
                            release_rate=float(computed.released.mean()) if len(computed) else np.nan,
                            mean_width=float(computed.width.replace(np.inf, np.nan).mean()) if len(computed) else np.nan,
                            mean_point_error=float(computed.point_error.mean()) if len(computed) else np.nan,
                            contains_full=int((computed.reference_relation == "contains_full").sum()) if len(computed) else 0,
                            disjoint=int((computed.reference_relation == "disjoint").sum()) if len(computed) else 0,
                            partial_overlap=int((computed.reference_relation == "partial_overlap").sum()) if len(computed) else 0))
    pd.DataFrame(summary).to_csv(out / "loso_summary.csv", index=False)
    (out / "run_manifest.json").write_text(json.dumps({
        "protocol": "MICROCREDIT_LOSO_PILOT_PROTOCOL_20260925.md",
        "estimand_protocol": "MICROCREDIT_INVITATION_ITT_PROTOCOL_20260925.md",
        "n_compatible_studies": int(len(STUDIES)),
        "studies": STUDIES.study_id.tolist(),
        "thresholds": [0.10, 0.20, 0.40, 0.80],
        "primary_threshold": 0.20,
        "calibration_claim": False,
        "raw_records_committed": False,
        "interpretation": "noisy-reference descriptive pilot; overlapping LOSO fits; no bootstrap"
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("results/microcredit_loso_pilot"))
    run(parser.parse_args().output)
