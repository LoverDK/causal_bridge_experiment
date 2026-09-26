"""Stress-test ExAtlas-style composability under controlled target shifts."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.dgp import SimulationConfig, generate_minimal_archive
from causal_atlas_sim.exatlas_baseline import ExAtlasConfig, fit_exatlas_style
from causal_atlas_sim.methods import AtlasConfig, fit_causal_atlas


def _wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """Return a fixed 95% Wilson interval for a binomial release rate."""
    if trials <= 0:
        raise ValueError("trials must be positive")
    fraction = successes / trials
    denominator = 1.0 + z * z / trials
    center = (fraction + z * z / (2.0 * trials)) / denominator
    half_width = z * math.sqrt(
        fraction * (1.0 - fraction) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _run(
    repetitions: int = 200, base_seed: int = 20260922
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    scenarios = (
        ("in_support", "none", 0.0),
        ("observable_shift", "target_shift_fraction", 0.25),
        ("observable_shift", "target_shift_fraction", 0.50),
        ("observable_shift", "target_shift_fraction", 0.75),
        ("hidden_shift", "target_hidden_shift_fraction", 0.25),
        ("hidden_shift", "target_hidden_shift_fraction", 0.50),
        ("hidden_shift", "target_hidden_shift_fraction", 0.75),
    )
    ex_config = ExAtlasConfig(residual_threshold=0.10)
    atlas_config = AtlasConfig()
    base_sequences = np.random.SeedSequence(base_seed).spawn(len(scenarios))
    rows: list[dict[str, object]] = []
    raw_records: list[dict[str, object]] = []
    for scenario_index, ((scenario, parameter, level), scenario_seed) in enumerate(
        zip(scenarios, base_sequences, strict=True)
    ):
        sequences = scenario_seed.spawn(repetitions)
        records: list[dict[str, object]] = []
        for sequence in sequences:
            seed = int(sequence.generate_state(1, dtype=np.uint32)[0])
            kwargs = {parameter: level} if parameter != "none" else {}
            generated = generate_minimal_archive(SimulationConfig(**kwargs), seed=seed)
            exatlas = fit_exatlas_style(generated.archive, generated.target, ex_config)
            atlas = fit_causal_atlas(generated.archive, generated.target, atlas_config)
            records.append(
                {
                    "scenario": scenario,
                    "parameter": parameter,
                    "level": level,
                    "seed": seed,
                    "true": generated.target.true_effect,
                    "ex_composable": exatlas.composable,
                    "ex_residual": exatlas.normalized_residual,
                    "ex_abs_error": abs(exatlas.raw_point_estimate - generated.target.true_effect),
                    "atlas_accepted": atlas.accepted,
                    "atlas_abs_error": (
                        abs(atlas.point_estimate - generated.target.true_effect)
                        if atlas.point_estimate is not None
                        else float("nan")
                    ),
                }
            )
        raw_records.extend(records)
        ex_selected = [record for record in records if record["ex_composable"]]
        atlas_selected = [record for record in records if record["atlas_accepted"]]
        ex_ci = _wilson_interval(len(ex_selected), repetitions)
        atlas_ci = _wilson_interval(len(atlas_selected), repetitions)
        rows.append(
            {
                "scenario": scenario,
                "parameter": parameter,
                "level": level,
                "repetitions": repetitions,
                "exatlas_composable_rate": len(ex_selected) / repetitions,
                "exatlas_composable_rate_lo": ex_ci[0],
                "exatlas_composable_rate_hi": ex_ci[1],
                "exatlas_mean_residual": float(np.mean([record["ex_residual"] for record in records])),
                "exatlas_conditional_mae": (
                    float(np.mean([record["ex_abs_error"] for record in ex_selected]))
                    if ex_selected else None
                ),
                "exatlas_all_target_raw_mae": float(np.mean([record["ex_abs_error"] for record in records])),
                "atlas_release_rate": len(atlas_selected) / repetitions,
                "atlas_release_rate_lo": atlas_ci[0],
                "atlas_release_rate_hi": atlas_ci[1],
                "atlas_conditional_mae": (
                    float(np.nanmean([record["atlas_abs_error"] for record in atlas_selected]))
                    if atlas_selected else None
                ),
            }
        )
    return rows, raw_records


def run(repetitions: int = 200, base_seed: int = 20260922) -> list[dict[str, object]]:
    """Run the stress audit and return one summary row per scenario."""
    rows, _ = _run(repetitions=repetitions, base_seed=base_seed)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="New directory for this run; existing paths are refused")
    parser.add_argument("--repetitions", type=int, default=200)
    parser.add_argument("--base-seed", type=int, default=20260922)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    output = args.output.resolve()
    if output.exists():
        parser.error(f"output path already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    rows, raw_records = _run(repetitions=args.repetitions, base_seed=args.base_seed)
    with (output / "stress_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (output / "stress_records.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(raw_records[0]))
        writer.writeheader()
        writer.writerows(raw_records)
    metadata = {
        "repetitions_per_scenario": args.repetitions,
        "base_seed": args.base_seed,
        "exatlas_variant": "composition-only; no LLM enrichment, reconciliation, or bridge generation",
        "exatlas_residual_threshold": 0.10,
        "purpose": "controlled observable and hidden target-shift audit of composability and refusal",
        "target_outcomes_used_for_fit": False,
    }
    (output / "stress_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(rows), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()

