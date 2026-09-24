"""Run the independent, outcome-blind mechanism-set calibration audit."""
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

from atlas_new.mechanism_calibration import coverage, fit_joint_calibrator

ROOT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(hits: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        return float("nan"), float("nan")
    p = hits / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(mid - half), float(mid + half)


def run(output: Path, *, seed: int = 2026092401, repetitions: int = 2000,
        calibration_archives: int = 199, entities: int = 11,
        dimension: int = 2, eta: float = .05) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    output.mkdir(parents=True)
    rng = np.random.default_rng(seed)
    calibration = rng.normal(size=(calibration_archives, entities, dimension))
    calibrator = fit_joint_calibrator(calibration, eta)
    rows = []
    # Test archives are independent of calibration and contain the full choice
    # universe.  No effect outcome or target result enters this audit.
    for setting, multiplier in [("nominal", 1.0), ("proxy_shift", 1.5)]:
        test = rng.normal(size=(repetitions, entities, dimension)) * multiplier
        norms = np.linalg.norm(test, axis=2)
        for rule, radius in [("joint", calibrator["joint_radius"]),
                             ("marginal", calibrator["marginal_radius"])]:
            hit = coverage(test, radius, joint=rule == "joint")
            joint_hit = np.all(norms <= radius, axis=1)
            lo, hi = wilson(int(joint_hit.sum()), len(joint_hit))
            rows.append({"setting": setting, "rule": rule,
                         "n_test": repetitions, "n_entities": entities,
                         "dimension": dimension, "radius": float(radius),
                         "joint_coverage": float(np.mean(joint_hit)),
                         "entity_coverage": float(np.mean(norms <= radius)),
                         "mc_lower": lo, "mc_upper": hi,
                         "assumption_valid": setting == "nominal"})
    summary = pd.DataFrame(rows)
    summary.to_csv(output / "summary.csv", index=False, float_format="%.15g")
    (output / "calibrator.json").write_text(
        json.dumps(calibrator, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = {
        "status": "complete", "seed": seed, "repetitions": repetitions,
        "calibration_archives": calibration_archives, "entities": entities,
        "dimension": dimension, "eta": eta,
        "scope": "Independent proxy-error calibration audit; no outcomes or target effects",
        "source_sha256": {
            "run_mechanism_calibration.py": digest(Path(__file__)),
            "atlas_new/mechanism_calibration.py": digest(ROOT / "atlas_new" / "mechanism_calibration.py"),
        },
        "python": sys.version, "platform": platform.platform(),
        "completed_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": {},
    }
    manifest["artifacts"] = {
        p.name: {"sha256": digest(p), "bytes": p.stat().st_size}
        for p in output.iterdir() if p.is_file()
    }
    (output / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results" / "mechanism_calibration")
    args = parser.parse_args()
    run(args.output)
    print(f"COMPLETE {args.output}")


if __name__ == "__main__":
    main()
