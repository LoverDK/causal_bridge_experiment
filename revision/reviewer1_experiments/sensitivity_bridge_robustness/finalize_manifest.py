from pathlib import Path
import csv
import hashlib
import json

root=Path(__file__).resolve().parent
out=root/"deterministic_reanalysis01"
reuse_manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
reuse_manifest["outputs"]=[r for r in reuse_manifest["outputs"] if Path(r["path"]).name!="REPORT.md"]
reuse_manifest["scope_note"]="Initial existing-CSV arithmetic provenance. Combined REPORT.md later gained an authorized deterministic stage and is hashed by delivery_manifest.json."
(root/"manifest.json").write_text(json.dumps(reuse_manifest,indent=2),encoding="utf-8")
with (out/"summary.csv").open(newline="",encoding="utf-8") as f:
    appendix=[{"row_id":"B"+r["budget"]+"_"+r["method"],**r} for r in csv.DictReader(f) if r["condition_stratum"]=="all"]
with (out/"appendix_table_rows.csv").open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=list(appendix[0]));writer.writeheader();writer.writerows(appendix)
with (out/"paired_comparisons.csv").open(newline="",encoding="utf-8") as f:
    pairs=list(csv.DictReader(f))
protocol=json.loads((root/"deterministic_protocol.json").read_text())
source_hash=hashlib.sha256(Path(protocol["input_designs"]).read_bytes()).hexdigest()
copy_hash=hashlib.sha256((out/"input_designs.json").read_bytes()).hexdigest()
assert source_hash==copy_hash==protocol["input_designs_sha256"]
facts={
    "scope":"Deterministic reanalysis of all200 original Gaussian linear designs; no outcomes or new designs",
    "source_design_sha256":source_hash,"copied_design_sha256":copy_hash,"hashes_match":True,
    "table_source":"deterministic_reanalysis01/appendix_table_rows.csv",
    "table_row_ids":[r["row_id"] for r in appendix],
    "primary_fact":{"claim_id":"E_B4_TARGET_GREEDY_GLOBAL_GAP","row_id":"B4_target_variance_greedy","n_designs":200,"radius_ratio_mean":1.0296872454963566,"radius_ratio_median":1.0000000000000002,"radius_ratio_q90":1.0927377625126307,"radius_ratio_max":1.6236897982624388,"target_optimal_count":118,"suboptimal_count":82,"definition":"target-greedy target radius divided by exhaustive target-optimal radius at the same budget"},
    "budget_rows":appendix,"paired_comparisons":pairs,
    "adverse_facts":[{"claim_id":"E_NO_DOMINANCE_LOGDET","budget":4,"target_greedy_wider_than_logdet_greedy":2,"n_designs":200,"max_radius_ratio":1.0260722121210508},{"claim_id":"E_WORST_GLOBAL_GAP","design_id":178,"budget":4,"selection":"post hoc worst case across all200; exploratory diagnostic","radius_ratio":1.6236897982624388,"variance_ratio":2.636368560981519}],
    "condition_strata_source":"deterministic_reanalysis01/summary.csv; condition_stratum not all; descriptive fixed bins0,25,50,100,infinity on maximum feasible-subset posterior condition",
    "verification":"deterministic_reanalysis01/independent_audit.json",
    "claim_limits":["No general greedy approximation theorem","No coverage inference from deterministic matrix arithmetic","No nonlinear or outcome-adaptive acquisition evidence","No new U/L/H calibration or direct-target superiority evidence"],
    "review_status_changed":False
}
(root/"claim_facts.json").write_text(json.dumps(facts,indent=2),encoding="utf-8")
files=[]
for p in sorted(root.rglob("*")):
    if p.is_file() and p.name!="delivery_manifest.json":
        files.append({"path":str(p.relative_to(root)),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
manifest={"delivery":"E smoothness reuse audit and authorized deterministic saved-design reanalysis", "source_design_sha256":source_hash,"copied_design_sha256":copy_hash,"hashes_match":True,"new_monte_carlo":False,"new_dgp":False,"source_archive_modified":False,"tex_or_git_modified":False,"files":files}
(root/"delivery_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({"file_count":len(files),"manifest":str(root/"delivery_manifest.json")}))
