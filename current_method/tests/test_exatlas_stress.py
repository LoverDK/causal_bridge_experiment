from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "exatlas"))

from run_exatlas_stress import run


class ExAtlasStressTests(unittest.TestCase):
    def test_cli_runs_from_unrelated_cwd_and_refuses_overwrite(self) -> None:
        script = PROJECT_ROOT / "exatlas" / "run_exatlas_stress.py"
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            output = parent / "new-run"
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            command = [sys.executable, "-B", str(script), "--output", str(output),
                       "--repetitions", "2"]
            first = subprocess.run(command, cwd=parent, env=env,
                                   text=True, capture_output=True, check=True)
            self.assertEqual(json.loads(first.stdout)["rows"], 7)
            for name in ("stress_summary.csv", "stress_records.csv", "stress_metadata.json"):
                self.assertTrue((output / name).is_file())
            summary_before = (output / "stress_summary.csv").read_bytes()
            second = subprocess.run(command, cwd=parent, env=env,
                                    text=True, capture_output=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already exists", second.stderr)
            self.assertEqual((output / "stress_summary.csv").read_bytes(), summary_before)

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
