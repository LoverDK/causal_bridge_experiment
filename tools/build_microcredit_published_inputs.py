"""Convert explicitly selected published table cells into versioned pilot inputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/microcredit_published_sources_v1.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(source: Path, output: Path) -> None:
    if output.exists():
        raise FileExistsError("Choose a new output directory")
    source_bytes = source.read_bytes()
    spec = json.loads(source_bytes)
    rows = []
    for item in spec["studies"]:
        factor = (1.0 / item["ppp_divisor"] * (100.0 / item["cpi_index"]) *
                  item["period_numerator"] / item["period_denominator"])
        row = {"study_id": item["study_id"], "effect": item["published_effect"] * factor,
               "se": item["published_se"] * factor, **item["exploratory_design"],
               "status": "verified_common_estimand",
               "assignment_status": "verified_source",
               "assignment_source_locator": item["assignment_source_locator"],
               "outcome_status": "verified_source",
               "outcome_source_locator": item["outcome_source_locator"],
               "stratum_status": "verified_source",
               "stratum_source_locator": item["stratum_source_locator"],
               "target_population_status": "verified_source",
               "target_population_source_locator": item["target_population_source_locator"],
               "target_population": item["target_population"],
               "variance_status": "verified_assignment_level_se",
               "design_vector_status": "exploratory_author_coded_coordinates_unverified",
               "published_effect": item["published_effect"], "published_se": item["published_se"],
               "conversion_factor": factor, "reference_n": item["n"],
               "reference_source": item["table_locator"], "source_pdf_sha256": item["pdf_sha256"],
               "sampling_and_variance": item["sampling_and_variance"],
               "source_spec_sha256": sha(source_bytes),
               "analysis_role": item["analysis_role"],
               "interpretation": "operational descriptive profit/access stratum; construct equivalence not established"}
        rows.append(row)
    output.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for filename, selected in [
        ("primary.csv", [r for r in rows if r["analysis_role"] == "primary"]),
        ("population_sensitivity.csv", rows),
    ]:
        path = output / filename
        with path.open("x", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader(); writer.writerows(selected)
        hashes[filename] = sha(path.read_bytes())
    manifest = {"source_spec_sha256": sha(source_bytes), "builder_sha256": sha(Path(__file__).read_bytes()),
                "outputs": hashes, "scope": "Published rounded summaries only; no microdata reconstruction"}
    (output / "input_build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)
