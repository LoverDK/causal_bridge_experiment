import unittest
from pathlib import Path

from run_effect_family_baselines_all import analyze_all, leakage_audit, load_data


class AllFamilySensitivityChecks(unittest.TestCase):
    def test_all_valid_families_are_held_out(self):
        frame = load_data(Path(__file__).parents[1] / "data" / "manylabs2_original_effects.csv")
        predictions = analyze_all(frame)
        self.assertEqual(predictions.target_family.nunique(), 23)
        self.assertEqual(predictions.target_study.nunique(), 28)
        self.assertEqual(predictions.method.nunique(), 5)

    def test_all_family_leakage_audit(self):
        frame = load_data(Path(__file__).parents[1] / "data" / "manylabs2_original_effects.csv")
        predictions = analyze_all(frame)
        audit = leakage_audit(frame, predictions)
        self.assertLessEqual(float(audit.prediction_change.max()), 1e-12)
        self.assertLessEqual(float(audit.radius_change.max()), 1e-12)


if __name__ == "__main__":
    unittest.main()
