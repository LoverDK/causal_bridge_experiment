from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "exatlas"))

from run_exatlas_stress import run


class ExAtlasStressTests(unittest.TestCase):
    def test_shift_protocol_is_deterministic_and_has_all_scenarios(self) -> None:
        first = run(repetitions=8, base_seed=20260922)
        second = run(repetitions=8, base_seed=20260922)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 7)
        self.assertEqual({row["scenario"] for row in first}, {"in_support", "observable_shift", "hidden_shift"})
        self.assertTrue(all(0.0 <= row["exatlas_composable_rate"] <= 1.0 for row in first))
        self.assertTrue(
            all(
                row["exatlas_composable_rate_lo"] <= row["exatlas_composable_rate"] <= row["exatlas_composable_rate_hi"]
                for row in first
            )
        )
        self.assertTrue(
            all(
                row["atlas_release_rate_lo"] <= row["atlas_release_rate"] <= row["atlas_release_rate_hi"]
                for row in first
            )
        )


if __name__ == "__main__":
    unittest.main()
