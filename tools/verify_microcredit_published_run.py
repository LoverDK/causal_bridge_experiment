"""Independently check published-input conversion, saved LOSO arithmetic and provenance."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def verify(run: Path, source: Path) -> dict:
    manifest = json.loads((run / "run_manifest.json").read_text())
    for name, wanted in manifest["output_sha256"].items():
        assert digest(run / name) == wanted, name
    assert digest(ROOT / manifest["input_path"]) == manifest["input_sha256"]
    assert digest(ROOT / manifest["runner_path"]) == manifest["runner_sha256"]
    for name, wanted in manifest["protocol_hashes"].items():
        assert digest(ROOT / name) == wanted, name
    input_rows = rows(ROOT / manifest["input_path"])
    data = {row["study_id"]: row for row in input_rows}
    spec = {item["study_id"]: item for item in json.loads(source.read_text())["studies"]}
    errors = []
    def close(actual: str | float, expected: float) -> None:
        a = float(actual); errors.append(abs(a - expected))
        assert math.isclose(a, expected, rel_tol=1e-12, abs_tol=1e-12), (a, expected)
    for name, row in data.items():
        item = spec[name]
        with localcontext() as context:
            context.prec = 40
            d = lambda key: Decimal(str(item[key]))
            factor = Decimal(100) * d("period_numerator") / (d("ppp_divisor") * d("cpi_index") * d("period_denominator"))
            close(row["effect"], float(d("published_effect") * factor))
            close(row["se"], float(d("published_se") * factor))
        assert row["source_spec_sha256"] == digest(source)
        assert row["source_pdf_sha256"] == item["pdf_sha256"]
    results = rows(run / "loso_results.csv")
    assert len(results) == 5 * len(data)
    by_method = {}
    for row in results:
        method = row["method"]; target = data[row["target"]]
        train = [r for name, r in data.items() if name != row["target"]]
        assert int(row["n_train"]) == len(train)
        by_method.setdefault(method, []).append(row)
        if method in {"atlas_descriptive", "design_meta_regression"}:
            assert row["status"] == "not_qualified"
        elif method == "random_effects" or (method == "robust_training_range" and len(train) < 2):
            assert row["status"] == "not_identified"
        else:
            assert row["status"] == "computed"
            if method == "fixed_effect":
                precision = [1 / float(t["se"]) ** 2 for t in train]
                mean = math.fsum(w * float(t["effect"]) for w, t in zip(precision, train)) / math.fsum(precision)
                radius = NormalDist().inv_cdf(.975) / math.sqrt(math.fsum(precision))
            else:
                values = [float(t["effect"]) for t in train]
                mean = (min(values) + max(values)) / 2
                radius = (max(values) - min(values)) / 2
            for key, value in [("estimate", mean), ("radius", radius), ("lower", mean-radius), ("upper", mean+radius), ("width", 2*radius)]:
                close(row[key], value)
            assert (row["released"] == "True") == (radius <= .20)
            close(row["point_error"], abs(mean-float(target["effect"])))
            lo = float(target["effect"]) - 1.96*float(target["se"])
            hi = float(target["effect"]) + 1.96*float(target["se"])
            close(row["reference_lower"], lo); close(row["reference_upper"], hi)
            relation = "contains_full" if mean-radius <= lo and mean+radius >= hi else ("disjoint" if mean+radius < lo or mean-radius > hi else "partial_overlap")
            assert row["reference_relation"] == relation
    for row in rows(run / "loso_summary.csv"):
        group = [x for x in by_method[row["method"]] if x["status"] == "computed"]
        released = [x for x in group if x["released"] == "True"]
        assert int(row["n_computed"]) == len(group)
        assert int(row["n_released"]) == len(released)
        if not released: assert row["released_target_risk"] == ""
        for relation in ["contains_full", "disjoint", "partial_overlap"]:
            assert int(row[relation]) == sum(x["reference_relation"] == relation for x in group)
    for row in rows(run / "leakage_audit.csv"):
        for name in ["target_effect_changed", "target_se_changed", "predictions_unchanged", "width_unchanged", "release_unchanged"]:
            assert row[name] == "True"
        assert float(row["max_prediction_change"]) == 0
    assert (run / "predictions_before_scoring.csv").read_bytes() == (run / "leakage_predictions_before_scoring.csv").read_bytes()
    return {"status": "passed", "run": run.name, "input_sha256": manifest["input_sha256"],
            "run_manifest_sha256": digest(run / "run_manifest.json"), "source_sha256": digest(source),
            "n_studies": len(data), "n_method_rows": len(results), "max_numeric_error": max(errors),
            "scope": "Decimal unit conversion, stdlib independent arithmetic, saved-table counts, conditional target perturbation and hash checks; not raw-data or measurement-equivalence verification"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ROOT / "data/microcredit_published_sources_v1.json")
    args = parser.parse_args()
    print(json.dumps(verify(args.run, args.source), indent=2))
