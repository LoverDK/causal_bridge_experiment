from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from causal_atlas_sim.dgp import generate_minimal_archive
from causal_atlas_sim.exatlas_baseline import ExAtlasConfig, exatlas_representation, fit_exatlas_style


class ExAtlasBaselineTests(unittest.TestCase):
    def test_representation_is_fixed_length_and_deterministic(self) -> None:
        generated = generate_minimal_archive(seed=12)
        first = exatlas_representation(generated.target)
        second = exatlas_representation(generated.target)
        self.assertEqual(first.shape, (6,))
        self.assertTrue((first == second).all())

    def test_fit_does_not_use_target_outcome_and_is_reproducible(self) -> None:
        generated = generate_minimal_archive(seed=13)
        config = ExAtlasConfig(residual_threshold=0.35)
        first = fit_exatlas_style(generated.archive, generated.target, config)
        altered = generated.target.__class__(
            **{**generated.target.__dict__, "observed_outcome": generated.target.observed_outcome[::-1].copy()}
        )
        second = fit_exatlas_style(generated.archive, altered, config)
        self.assertEqual(first.composable, second.composable)
        self.assertAlmostEqual(first.raw_point_estimate, second.raw_point_estimate)
        self.assertTrue((first.weights == second.weights).all())

    def test_threshold_controls_composability(self) -> None:
        generated = generate_minimal_archive(seed=14)
        loose = fit_exatlas_style(generated.archive, generated.target, ExAtlasConfig(residual_threshold=10.0))
        strict = fit_exatlas_style(generated.archive, generated.target, ExAtlasConfig(residual_threshold=0.0))
        self.assertTrue(loose.composable)
        self.assertLessEqual(int(strict.composable), int(loose.composable))


if __name__ == "__main__":
    unittest.main()
