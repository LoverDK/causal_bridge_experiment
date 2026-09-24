import unittest
from pathlib import Path

from run_effect_family_baselines import analyze, leakage_audit, load_data


class EffectFamilyBaselineChecks(unittest.TestCase):
    def test_panel_has_all_requested_baseline_classes(self):
        frame = load_data(Path(__file__).parents[1] / "data" / "manylabs2_original_effects.csv")
        predictions = analyze(frame)
        self.assertEqual(predictions.target_study.nunique(), 10)
        self.assertEqual(predictions.method.nunique(), 5)
        self.assertEqual(
            set(predictions.method),
            {
                "transport_meta_regression",
                "hierarchical_meta_analysis",
                "robust_partial_identification",
                "study_split_conformal",
                "family_split_conformal",
            },
        )

    def test_target_effect_flip_does_not_change_baseline_predictions(self):
        frame = load_data(Path(__file__).parents[1] / "data" / "manylabs2_original_effects.csv")
        predictions = analyze(frame)
        audit = leakage_audit(frame, predictions)
        self.assertLessEqual(float(audit.prediction_change.max()), 1e-12)
        self.assertLessEqual(float(audit.radius_change.max()), 1e-12)

    def test_study_and_family_units_are_not_silently_collapsed(self):
        frame = load_data(Path(__file__).parents[1] / "data" / "manylabs2_original_effects.csv")
        predictions = analyze(frame)
        study = predictions[predictions.method == "study_split_conformal"].set_index(["target_family", "target_study"])
        family = predictions[predictions.method == "family_split_conformal"].set_index(["target_family", "target_study"])
        self.assertGreater(float((study.radius - family.radius).abs().max()), 1e-12)


if __name__ == "__main__":
    unittest.main()
