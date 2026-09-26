import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/run_microcredit_loso_pilot.py"


def fixture(path: Path, qualified: bool, n: int = 3) -> None:
    rows = []
    for i, (effect, se) in enumerate([(1.0, 0.5), (2.0, 0.6), (3.0, 0.7)][:n]):
        rows.append({"study_id": f"fixture_{i}", "effect": effect, "se": se,
                     "apr": 10 + i, "target_women": 1, "market": i,
                     "promotion": 1, "collateral": 0, "loan_share": 20 + i,
                     "individual_rand": 0,
                     "status": "verified_common_estimand" if qualified else "compatible_pilot",
                     "assignment_status": "verified_source" if qualified else "pending",
                     "assignment_source_locator": "fixture_design.md:10" if qualified else "pending",
                     "outcome_status": "verified_source" if qualified else "pending",
                     "outcome_source_locator": "fixture_design.md:20" if qualified else "pending",
                     "stratum_status": "verified_source" if qualified else "pending",
                     "stratum_source_locator": "fixture_design.md:30" if qualified else "pending",
                     "target_population_status": "verified_source" if qualified else "pending",
                     "target_population_source_locator": "fixture_design.md:40" if qualified else "pending",
                     "target_population": "synthetic fixture population" if qualified else "",
                     "variance_status": "verified_assignment_level_se" if qualified else "pending",
                     "design_vector_status": "verified_design_coordinates" if qualified else "exploratory"})
    pd.DataFrame(rows).to_csv(path, index=False)


class MicrocreditPilotTests(unittest.TestCase):
    def run_runner(self, input_path: Path, output: Path) -> None:
        subprocess.run([sys.executable, "-B", str(RUNNER), "--input", str(input_path), "--output", str(output)], check=True)

    def test_current_input_is_method_level_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "unsafe"
            self.run_runner(ROOT / "data/microcredit_loso_pilot_input.csv", out)
            manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "audit_only")
            self.assertEqual(manifest["n_qualified_studies"], 0)
            self.assertTrue(all(not gate["qualified"] for gate in manifest["method_gates"].values()))
            self.assertFalse((out / "loso_results.csv").exists())
            self.assertFalse((out / "predictions_before_scoring.csv").exists())
            self.assertFalse((out / "leakage_predictions_before_scoring.csv").exists())
            audit = pd.read_csv(out / "qualification_audit.csv")
            self.assertTrue(audit.common_reasons.str.contains("common_estimand_status_not_verified").all())
            self.assertTrue(audit.variance_reasons.str.contains("variance_status_not_verified").all())
            self.assertTrue(audit.design_reasons.str.contains("design_vector_status_not_verified").all())

    def test_qualified_fixture_delays_scoring_and_audits_saved_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); input_path = root / "fixture.csv"; out = root / "pilot"
            fixture(input_path, qualified=True); self.run_runner(input_path, out)
            manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "numeric_descriptive_pilot")
            self.assertIn("predictions_before_scoring.csv", manifest["output_sha256"])
            for filename, expected_hash in manifest["output_sha256"].items():
                self.assertEqual(hashlib.sha256((out / filename).read_bytes()).hexdigest(), expected_hash)
            predictions = pd.read_csv(out / "predictions_before_scoring.csv")
            self.assertFalse({"effect", "se", "reference_lower", "point_error"}.intersection(predictions.columns))
            self.assertEqual(len(predictions), 15)
            results = pd.read_csv(out / "loso_results.csv")
            self.assertIn("reference_lower", results.columns)
            leaks = pd.read_csv(out / "leakage_audit.csv")
            self.assertTrue(leaks.predictions_unchanged.all())
            self.assertTrue(leaks.width_unchanged.all())
            self.assertTrue(leaks.release_unchanged.all())
            self.assertTrue(leaks.target_effect_changed.all())
            self.assertTrue(leaks.target_se_changed.all())
            self.assertTrue((leaks.max_prediction_change == 0.0).all())

    def test_existing_output_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            input_path = root / "fixture.csv"
            out = root / "existing"
            fixture(input_path, qualified=False)
            out.mkdir()
            sentinel = out / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, "-B", str(RUNNER), "--input", str(input_path), "--output", str(out)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_one_study_has_no_training_prediction(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            input_path, out = root / "one.csv", root / "out"
            fixture(input_path, qualified=True, n=1)
            self.run_runner(input_path, out)
            result = pd.read_csv(out / "loso_results.csv")
            self.assertTrue((result.status == "not_identified").all())
            self.assertTrue((result.n_train == 0).all())
            self.assertTrue((result.qualification_reason == "no_training_studies").all())

    def test_two_studies_do_not_release_one_point_range(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            input_path, out = root / "two.csv", root / "out"
            fixture(input_path, qualified=True, n=2)
            self.run_runner(input_path, out)
            result = pd.read_csv(out / "loso_results.csv")
            ranges = result[result.method == "robust_training_range"]
            self.assertTrue((ranges.status == "not_identified").all())
            self.assertTrue((ranges.qualification_reason == "at_least_two_training_studies_required").all())
            self.assertFalse(ranges.released.any())

    def test_missing_target_se_does_not_fabricate_reference(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            input_path, out = root / "missing_se.csv", root / "out"
            fixture(input_path, qualified=True)
            data = pd.read_csv(input_path)
            data.loc[0, "se"] = float("nan")
            data.loc[0, "variance_status"] = "pending"
            data.to_csv(input_path, index=False)
            self.run_runner(input_path, out)
            result = pd.read_csv(out / "loso_results.csv")
            target = result[(result.target == "fixture_0") &
                            (result.method == "robust_training_range")].iloc[0]
            self.assertEqual(target.status, "computed")
            self.assertEqual(target.reference_relation, "reference_unavailable")
            self.assertTrue(pd.isna(target.reference_lower))

    def test_positive_unverified_target_se_does_not_fabricate_reference(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            input_path, out = root / "unverified_se.csv", root / "out"
            fixture(input_path, qualified=True)
            data = pd.read_csv(input_path)
            data.loc[0, "variance_status"] = "source_pending"
            data.to_csv(input_path, index=False)
            self.run_runner(input_path, out)
            result = pd.read_csv(out / "loso_results.csv")
            target = result[(result.target == "fixture_0") &
                            (result.method == "robust_training_range")].iloc[0]
            self.assertEqual(target.status, "computed")
            self.assertEqual(target.reference_relation, "reference_unavailable")
            self.assertTrue(pd.isna(target.reference_lower))
            self.assertTrue(pd.isna(target.reference_upper))

    def test_common_status_without_source_locators_is_audit_only(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            input_path, out = root / "missing_sources.csv", root / "out"
            fixture(input_path, qualified=True)
            data = pd.read_csv(input_path)
            data.loc[0, "target_population_source_locator"] = "pending"
            data.to_csv(input_path, index=False)
            self.run_runner(input_path, out)
            manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "audit_only")
            self.assertIn("target_population_source_locator_missing",
                          manifest["qualification"][0]["common_reasons"])
            self.assertFalse((out / "predictions_before_scoring.csv").exists())

    def test_missing_input_fails_before_creating_output(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            out = root / "out"
            completed = subprocess.run(
                [sys.executable, "-B", str(RUNNER), "--input", str(root / "missing.csv"), "--output", str(out)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(out.exists())



if __name__ == "__main__":
    unittest.main(verbosity=2)
