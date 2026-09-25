"""Run outcome-blind real-covariate calibration and NSW semisynthetic truth audits."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
DATA_PATH = ROOT / "data" / "nsw_dw.dta"
DEFAULT_OUT = ROOT / "results" / "extensions" / "nsw_real_proxy_truth"
PROTOCOL = ROOT / "docs" / "paper" / "nsw_real_proxy_truth_protocol.md"
BASE_SEED = 2026092501
ALPHA = 0.10
ENTITY_SIZE = 8
NSW_SOURCE_SHA256 = "d1bd2680a1c6f799f1c6d2455bf29633fdf19be01cb19490621c20a560b4e072"


def load_baseline_data():
    import pandas as pd

    digest = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
    if digest != NSW_SOURCE_SHA256:
        raise ValueError(f"NSW hash mismatch: {digest}")
    frame = pd.read_stata(DATA_PATH, columns=[
        "age", "education", "black", "hispanic", "married", "nodegree",
        "re74", "re75", "treat",
    ])
    x = frame[[
        "age", "education", "black", "hispanic", "married", "nodegree",
        "re74", "re75",
    ]].to_numpy(float)
    treatment = frame["treat"].to_numpy(int)
    return x, treatment


def split_participants(treatment, seed=BASE_SEED):
    rng = np.random.default_rng(seed)
    pools = {name: [] for name in ("development", "calibration", "validation")}
    for arm in (0, 1):
        ids = rng.permutation(np.flatnonzero(treatment == arm))
        fit_end = int(round(0.40 * len(ids)))
        calibration_end = int(round(0.70 * len(ids)))
        pools["development"].extend(ids[:fit_end].tolist())
        pools["calibration"].extend(ids[fit_end:calibration_end].tolist())
        pools["validation"].extend(ids[calibration_end:].tolist())
    result = {name: np.asarray(sorted(ids), dtype=int) for name, ids in pools.items()}
    if any(set(result[a]) & set(result[b]) for a, b in (
        ("development", "calibration"), ("development", "validation"),
        ("calibration", "validation"),
    )):
        raise AssertionError("participant split overlap")
    return result


def _entity_profiles(x, treatment, pool, rng, label):
    by_arm = {arm: rng.permutation(pool[treatment[pool] == arm]) for arm in (0, 1)}
    groups_per_arm = min(len(by_arm[0]), len(by_arm[1])) // (ENTITY_SIZE // 2)
    rows = []
    for group in range(groups_per_arm):
        chosen = np.concatenate([
            by_arm[arm][group * (ENTITY_SIZE // 2):(group + 1) * (ENTITY_SIZE // 2)]
            for arm in (0, 1)
        ])
        proxy_ids = np.concatenate([
            rng.choice(by_arm[arm][group * 4:(group + 1) * 4], size=2, replace=False)
            for arm in (0, 1)
        ])
        rows.append((f"{label}-{group:02d}", chosen, proxy_ids))
    return rows


def _quantile_order_statistic(scores, alpha):
    if not scores:
        raise ValueError("at least one calibration entity is required")
    rank = math.ceil((len(scores) + 1) * (1 - alpha))
    if rank > len(scores):
        return float("inf")
    return float(np.sort(np.asarray(scores, dtype=float))[rank - 1])


def real_proxy_audit(x, treatment, seed=BASE_SEED):
    pools = split_participants(treatment, seed)
    development = pools["development"]
    center = x[development].mean(axis=0)
    scale = x[development].std(axis=0, ddof=1)
    scale = np.where(scale > 1e-10, scale, 1.0)
    z = (x - center) / scale
    records = []
    entity_ids = {}
    for label in ("calibration", "validation"):
        rng = np.random.default_rng(seed + (1 if label == "calibration" else 2))
        profiles = _entity_profiles(z, treatment, pools[label], rng, label)
        entity_ids[label] = {name: ids.tolist() for name, ids, _ in profiles}
        for name, ids, proxy_ids in profiles:
            proxy = z[proxy_ids].mean(axis=0)
            reference = z[ids].mean(axis=0)
            error = float(np.max(np.abs(proxy - reference)))
            records.append(dict(
                split=label,
                entity=name,
                entity_unit_ids=";".join(map(str, ids.tolist())),
                proxy_unit_ids=";".join(map(str, proxy_ids.tolist())),
                n_treated=int(treatment[ids].sum()),
                n_control=int(len(ids) - treatment[ids].sum()),
                max_coordinate_error=error,
                truth_type="observed_pretreatment_covariate_group_mean",
                outcomes_read=False,
            ))
    calibration_scores = [r["max_coordinate_error"] for r in records if r["split"] == "calibration"]
    q = _quantile_order_statistic(calibration_scores, ALPHA)
    validation = [r for r in records if r["split"] == "validation"]
    covered = [r["max_coordinate_error"] <= q for r in validation]
    summary = [dict(
        calibration_entities=len(calibration_scores),
        validation_entities=len(validation),
        nominal_miscoverage=ALPHA,
        calibrated_supnorm_radius=q,
        validation_joint_profile_coverage=float(np.mean(covered)) if covered else float("nan"),
        validation_mean_supnorm_error=float(np.mean([r["max_coordinate_error"] for r in validation])) if validation else float("nan"),
        development_units=len(pools["development"]),
        calibration_units=len(pools["calibration"]),
        validation_units=len(pools["validation"]),
        development_calibration_overlap=False,
        development_validation_overlap=False,
        calibration_validation_overlap=False,
        outcomes_read=False,
        scope="within_trial_observed_covariate_proxy_only",
        not_latent_mechanism_truth=True,
        not_independent_study_archive=True,
    )]
    split_manifest = {
        "participant_pools": {name: ids.tolist() for name, ids in pools.items()},
        "entity_units": entity_ids,
    }
    return records, summary, split_manifest


def _potential_outcomes(x, noise, surface):
    if surface == "constant":
        tau = np.full(len(x), 2.0)
    elif surface == "smooth":
        tau = 2 + 0.8 * np.tanh(x[:, 0]) + 1.2 * np.tanh(x[:, 7])
    elif surface == "interaction":
        tau = 1 + 2 * np.tanh(x[:, 0] * x[:, 7]) + 0.8 * (x[:, 5] > 0)
    else:
        raise ValueError(surface)
    mu = 3 + 0.7 * x[:, 0] + 1.5 * np.tanh(x[:, 6]) + 0.5 * x[:, 1] ** 2
    y0 = mu + noise
    y1 = mu + tau + noise
    return y0, y1, tau


def _prediction_signature(rows):
    return {
        (row["method"], row["target"]): (
            row["estimate"], row["released"], row["lower"], row["upper"]
        ) for row in rows
    }


def _same_signature(left, right):
    if left.keys() != right.keys():
        return False
    for key in left:
        for a, b in zip(left[key], right[key]):
            if a is None or b is None:
                if a is not b:
                    return False
            elif not np.isclose(a, b, atol=1e-12, rtol=0):
                return False
    return True


def semisynthetic_truth_audit(x, treatment, repetitions=100):
    from dataclasses import replace
    from causal_atlas_sim.extension_nsw import fixed_design, make_objects, predictions

    design = fixed_design(x, treatment)
    source_pool, target_pool, source_anchors, target_anchors = design
    if set(source_pool) & set(target_pool):
        raise AssertionError("source and target participants overlap")
    rows = []
    leak_checks = []
    for surface, base_seed in zip(
        ("constant", "smooth", "interaction"),
        (2026092511, 2026092512, 2026092513),
    ):
        seeds = np.random.SeedSequence(base_seed).spawn(repetitions)
        for replicate, child in enumerate(seeds):
            rng = np.random.default_rng(child)
            noise = rng.normal(0, 3, len(x))
            y0, y1, tau = _potential_outcomes(x, noise, surface)
            y = np.where(treatment == 1, y1, y0)
            sources = make_objects(x, treatment, y, source_pool, source_anchors)
            targets = make_objects(x, treatment, y, target_pool, target_anchors)
            predicted, _ = predictions(x, treatment, y, source_pool, sources, targets)
            flipped = [
                replace(target, estimated_effect=-target.estimated_effect, standard_error=17 * target.standard_error)
                for target in targets
            ]
            flipped_predicted, _ = predictions(x, treatment, y, source_pool, sources, flipped)
            invariant = _same_signature(_prediction_signature(predicted), _prediction_signature(flipped_predicted))
            if not invariant:
                raise AssertionError("target-effect flip changed a prediction or interval")
            leak_checks.append(dict(surface=surface, replicate=replicate, target_effect_flip_invariant=invariant))
            for row in predicted:
                target = targets[row["target"]]
                truth = float(np.mean(tau[np.asarray(target.neighborhood_rows, dtype=int)]))
                has_interval = row["lower"] is not None and row["upper"] is not None
                covered = bool(row["lower"] <= truth <= row["upper"]) if has_interval else None
                rows.append(dict(
                    surface=surface,
                    replicate=replicate,
                    seed=int(child.generate_state(1, dtype=np.uint32)[0]),
                    method=row["method"],
                    target=row["target"],
                    estimate=row["estimate"],
                    released=row["released"],
                    lower=row["lower"],
                    upper=row["upper"],
                    truth=truth,
                    absolute_error=abs(row["estimate"] - truth),
                    causal_truth_covered=covered,
                    interval_width=(row["upper"] - row["lower"]) if has_interval else None,
                    real_nsw_covariates=True,
                    original_nsw_assignment=True,
                    known_truth="finite_neighborhood_mean_of_frozen_tau_x",
                    target_outcomes_used_for_prediction=False,
                ))
            if (replicate + 1) % 25 == 0:
                print(f"NSW semisynthetic truth {surface}: {replicate + 1}/{repetitions}", flush=True)
    return rows, leak_checks, design


def summarize_truth(records):
    groups = defaultdict(list)
    for row in records:
        groups[(row["surface"], row["method"])].append(row)
    result = []
    for (surface, method), rows in sorted(groups.items()):
        errors = np.asarray([r["absolute_error"] for r in rows], dtype=float)
        replicate_means = np.asarray([
            np.mean([r["absolute_error"] for r in rows if r["replicate"] == replicate])
            for replicate in sorted({r["replicate"] for r in rows})
        ], dtype=float)
        intervals = [r for r in rows if r["causal_truth_covered"] is not None]
        result.append(dict(
            surface=surface,
            method=method,
            target_evaluations=len(rows),
            replicates=len({r["replicate"] for r in rows}),
            mae=float(errors.mean()),
            mae_mcse=float(replicate_means.std(ddof=1) / math.sqrt(len(replicate_means))) if len(replicate_means) > 1 else 0.0,
            release_rate=float(np.mean([bool(r["released"]) for r in rows])),
            interval_evaluations=len(intervals),
            causal_truth_coverage=(float(np.mean([r["causal_truth_covered"] for r in intervals])) if intervals else None),
            mean_interval_width=(float(np.mean([r["interval_width"] for r in intervals])) if intervals else None),
            target_outcomes_used_for_prediction=False,
            truth_scope="semisynthetic_exact_finite_population_truth",
        ))
    return result


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=100)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    if args.repetitions < 1:
        raise ValueError("repetitions must be positive")
    out = args.output if args.output.is_absolute() else ROOT / args.output
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"Refusing to overwrite existing NSW audit: {out}")
    out.mkdir(parents=True, exist_ok=True)
    global OUT
    OUT = out
    x, treatment = load_baseline_data()
    proxy_records, proxy_summary, split_manifest = real_proxy_audit(x, treatment)
    truth_records, leak_checks, design = semisynthetic_truth_audit(x, treatment, args.repetitions)
    _write_csv(OUT / "real_covariate_proxy_records.csv", proxy_records)
    _write_csv(OUT / "real_covariate_proxy_summary.csv", proxy_summary)
    _write_csv(OUT / "semisynthetic_truth_records.csv", truth_records)
    _write_csv(OUT / "semisynthetic_truth_summary.csv", summarize_truth(truth_records))
    _write_csv(OUT / "target_effect_flip_audit.csv", leak_checks)
    (OUT / "split_manifest.json").write_text(json.dumps(split_manifest, indent=2) + "\n", encoding="utf-8")
    (OUT / "causal_truth_design.json").write_text(json.dumps({
        "source_units": design[0].tolist(),
        "target_units": design[1].tolist(),
        "source_anchors": design[2].tolist(),
        "target_anchors": design[3].tolist(),
        "source_target_overlap": False,
        "assignment_source": "original_nsw_randomized_assignment",
    }, indent=2) + "\n", encoding="utf-8")
    source_paths = [DATA_PATH, PROTOCOL, Path(__file__), ROOT / "src" / "causal_atlas_sim" / "extension_nsw.py", ROOT / "src" / "causal_atlas_sim" / "extension_baselines.py"]
    manifest = {
        "command": ["python", "legacy_audits/scripts/run/run_nsw_real_proxy_truth.py", "--repetitions", str(args.repetitions), "--output", str(out)],
        "seed": BASE_SEED,
        "settings": {"repetitions": args.repetitions, "alpha": ALPHA, "entity_size": ENTITY_SIZE},
        "python": platform.python_version(),
        "numpy": np.__version__,
        "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "sources": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name != "manifest.json"},
        "scope": {
            "real_covariate_proxy": "within-trial observed baseline profile only; not latent mechanism truth",
            "calibration_archive": "participant-disjoint split from one randomized trial; not independent study-level archive",
            "causal_truth": "exact semisynthetic finite-neighborhood truth on real NSW covariates and original assignment",
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"proxy": proxy_summary, "truth_summary": summarize_truth(truth_records), "outputs": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
