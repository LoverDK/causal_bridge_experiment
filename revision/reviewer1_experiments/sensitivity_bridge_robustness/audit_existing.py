"""Existing-CSV arithmetic only. Never imports or executes experiment code."""
from pathlib import Path
import csv
import hashlib
import json
import time

BASE = Path("C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild")
OUT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(rel):
    with (BASE / rel).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def number(row, key):
    return float(row[key])

def copy_csv(rel, name):
    (OUT / name).write_bytes((BASE / rel).read_bytes())

def main():
    start = time.perf_counter()
    source_files = [
        "AGENTS.md", "revision/FIRST_WORKFLOW.md", "revision/REVIEW_TRACKER.md",
        "revision/review_tracker.json", "revision/REVIEW_ABLATION_CONTINUATION02.md",
        "revision/REVIEW_ABLATION_CONTINUATION02.json", "revision/MECHANISM_UNCERTAINTY_ABLATION01.md",
        "revision/MECHANISM_UNCERTAINTY_ABLATION01.json", "revision/HISTORICAL_BRIDGE_WORKFLOW01.md",
        "revision/ABLATION_AUDIT_20261107.md", "current_method/atlas_new/experiments.py",
        "current_method/results/full/bridge_records.csv", "current_method/results/full/bridge_anisotropy.csv",
        "current_method/results/full/bridge_designs.json", "current_method/results/full/operational_summary.csv",
        "revision/results/ablation_continuation02/primary_summary_scenarios.csv",
        "revision/results/ablation_continuation02/stopped_summary_scenarios.csv",
        "revision/results/ablation_continuation02/primary_summary_cells.csv",
        "revision/results/ablation_continuation02/same_weight_summary_cells.csv",
        "revision/results/ablation_continuation02/RESULTS.md",
        "revision/results/ablation_continuation02/analysis_manifest.json",
        "revision/results/ablation_continuation02/independent_audit.json",
        "revision/results/mechanism_uncertainty_ablation01/primary_summary_scenarios.csv",
        "revision/results/mechanism_uncertainty_ablation01/stopped_summary_scenarios.csv",
        "revision/results/mechanism_uncertainty_ablation01/RESULTS.md",
        "revision/results/mechanism_uncertainty_ablation01/analysis_manifest.json",
        "revision/results/historical_bridge_workflow01/RESULTS.md",
        "revision/results/non_gaussian_target_run01/RESULTS.md",
        "revision/results/main_theorem_workflow01/RESULTS.md",
    ]
    fixed = rows("revision/results/ablation_continuation02/primary_summary_scenarios.csv")
    assert len(fixed) == 15 and all(r["mode"] == "r2" and int(r["stage"]) == 3 for r in fixed)
    totals = {}
    for variant in ["baseline", "L_half", "L_double", "H_zero", "H_double"]:
        selected = [r for r in fixed if r["variant"] == variant]
        assert len(selected) == 3 and sum(int(r["n_worlds"]) for r in selected) == 1800
        totals[variant] = {key: sum(int(r[key]) for r in selected) for key in
                           ["n_worlds", "covered_count", "causal_geometry_violation_count", "selected_bound_valid_count"]}
    stopped = rows("revision/results/ablation_continuation02/stopped_summary_scenarios.csv")
    bridge_stop = [r for r in stopped if r["mode"] == "r2" and r["scenario"] == "bridgeable"]
    assert len(bridge_stop) == 10
    bridge = rows("current_method/results/full/bridge_records.csv")
    greedy = [r for r in bridge if r["method"] == "greedy"]
    assert len(greedy) == 200
    ratios = sorted(number(r, "information_ratio") for r in greedy)
    target_ratios = sorted(number(r, "target_radius_ratio") for r in greedy)
    kappa = sorted(number(r, "all_subset_kappa") for r in greedy)
    bound_ratios = sorted(number(r, "target_radius_bound") / number(r, "target_radius") for r in greedy)
    med = lambda a: (a[len(a)//2-1] + a[len(a)//2])/2
    bridge_summary = {
        "designs": len(greedy), "budget": 4, "method": "logdet_greedy",
        "information_ratio_min": min(ratios), "information_ratio_median": med(ratios), "information_ratio_mean": sum(ratios)/len(ratios),
        "target_radius_ratio_mean": sum(target_ratios)/len(target_ratios), "target_radius_ratio_max": max(target_ratios),
        "all_subset_kappa_min": min(kappa), "all_subset_kappa_median": med(kappa), "all_subset_kappa_max": max(kappa),
        "bound_over_actual_radius_min": min(bound_ratios), "bound_over_actual_radius_median": med(bound_ratios), "bound_over_actual_radius_max": max(bound_ratios),
        "warning": "200 design summaries; 250 random subsets per design are nested comparisons, not independent designs. No target-greedy run added."
    }
    checks = []
    for folder in ["ablation_continuation02", "mechanism_uncertainty_ablation01"]:
        rel = f"revision/results/{folder}"
        manifest = json.loads((BASE / rel / "analysis_manifest.json").read_text(encoding="utf-8"))
        for name in ["primary_summary_scenarios.csv", "stopped_summary_scenarios.csv", "RESULTS.md"]:
            expected = manifest["output_sha256"][name]
            actual = digest(BASE / rel / name)
            checks.append({"path": str(BASE / rel / name), "expected_sha256": expected, "actual_sha256": actual, "match": actual == expected})
    assert all(c["match"] for c in checks)
    (OUT / "existing_csv_arithmetic.json").write_text(json.dumps({"smoothness_totals": totals, "bridgeable_stopped_rows": bridge_stop, "bridge_original_summary": bridge_summary, "archive_hash_checks": checks}, indent=2), encoding="utf-8")
    for rel, name in [
        ("revision/results/ablation_continuation02/primary_summary_scenarios.csv", "reused_LH_primary.csv"),
        ("revision/results/ablation_continuation02/stopped_summary_scenarios.csv", "reused_LH_stopped.csv"),
        ("revision/results/ablation_continuation02/primary_summary_cells.csv", "reused_LH_cells.csv"),
        ("revision/results/mechanism_uncertainty_ablation01/primary_summary_scenarios.csv", "reused_U_primary.csv"),
        ("current_method/results/full/bridge_anisotropy.csv", "reused_bridge_anisotropy.csv")]:
        copy_csv(rel, name)
    latest = Path("D:/study/zzh科研/reviewer1-sprint/causal_lab_proposal_subpapers_tex_iclr2027/01_reviewer1_baselines.tex")
    manifest = {
        "operation": "Existing archived CSV arithmetic and selected hash verification only",
        "new_sampling": False, "new_optimization": False, "archive_modified": False,
        "command": "python audit_existing.py", "elapsed_seconds": time.perf_counter() - start,
        "protocol_sha256": digest(OUT / "reuse_protocol.json"), "code_sha256": digest(Path(__file__)),
        "source_files": [{"path": str(BASE / rel), "sha256": digest(BASE / rel)} for rel in source_files],
        "latest_paper": {"path": str(latest), "sha256": digest(latest)},
        "outputs": [{"path": str(p), "sha256": digest(p)} for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "manifest.json"],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"elapsed_seconds": manifest["elapsed_seconds"], "smoothness_totals": totals, "bridge_summary": bridge_summary, "hash_checks_passed": len(checks)}, indent=2))

if __name__ == "__main__":
    main()
