import unittest
from pathlib import Path

import pandas as pd

from run_effect_family_holdout import analyze, leakage_audit, load_data


class EffectFamilyHoldoutChecks(unittest.TestCase):
    def test_pinned_input_and_frozen_target_families(self):
        frame = load_data(Path(__file__).parents[1] / "data" / "manylabs2_original_effects.csv")
        predictions = analyze(frame)
        self.assertEqual(predictions.target_family.nunique(), 5)
        self.assertEqual(predictions.target_study.nunique(), 10)
        self.assertEqual(predictions.method.nunique(), 5)

    def test_target_effect_flip_cannot_change_prediction(self):
        frame = load_data(Path(__file__).parents[1] / "data" / "manylabs2_original_effects.csv")
        predictions = analyze(frame)
        audit = leakage_audit(frame, predictions)
        self.assertLessEqual(audit.prediction_change.max(), 1e-12)
        self.assertLessEqual(audit.radius_change.max(), 1e-12)


if __name__ == "__main__":
    unittest.main()
