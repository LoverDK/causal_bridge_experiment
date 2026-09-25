import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pilot_reproducible_and_leakage_free():
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "pilot"
        subprocess.run([sys.executable, str(ROOT / "tools/run_microcredit_loso_pilot.py"),
                        "--output", str(out)], check=True)
        rows = list(csv.DictReader((out / "loso_results.csv").open(encoding="utf-8")))
        assert len(rows) == 15
        assert {r["target"] for r in rows} == {
            "angelucci_mexico", "banerjee_india_endline1", "crepon_morocco"
        }
        assert all(r["released"] == "False" for r in rows)
        assert {"sign_error", "released_error_beyond_delta"}.issubset(rows[0])
        leaks = list(csv.DictReader((out / "leakage_audit.csv").open(encoding="utf-8")))
        assert len(leaks) == 3
        assert all(r["predictions_unchanged"] == "True" and r["max_prediction_change"] == "0.0"
                   for r in leaks)
        manifest = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
        assert manifest["calibration_claim"] is False
        assert manifest["n_compatible_studies"] == 3
