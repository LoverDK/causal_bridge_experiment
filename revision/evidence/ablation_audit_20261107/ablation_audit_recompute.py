import gzip,json,hashlib
from pathlib import Path
import numpy as np,pandas as pd
R=Path(r'C:\Users\Qiutian\Documents\Codex\2026-11-07\wo\outputs\experiment-rebuild')
O=Path(__file__).resolve().parent/'ablation_audit_data';O.mkdir(exist_ok=True)
A=R/'current_method/results/ablations_full'
f=pd.read_csv(A/'records.csv'); final=f[f.budget==3]
cols=['surface','scenario','replicate','schedule','mode','method','weight_rule','bound','stage','radius','error','certificate_covered','minimum_radius','barycentric_radius','lipschitz_radius','solver_failures','solver_successes','global_optimum_certified']
with gzip.open(A/'plans.jsonl.gz','rt',encoding='utf-8') as stream:
 p=pd.DataFrame([{k:d[k] for k in cols} for d in map(json.loads,stream)])
summary=final.groupby(['scenario','schedule','mode','tolerance','method']).agg(n=('released','size'),release=('released','mean'),cost=('new_n','mean'),mae=('error','mean'),width=('width','mean'),coverage=('covered','mean'),path_coverage=('path_covered','mean'),bad=('bad_release','mean')).reset_index()
summary.to_csv(O/'stopped_recomputed.csv',index=False)
fixed=p[p.stage==3].groupby(['scenario','schedule','mode','method']).agg(n=('radius','size'),radius=('radius','mean'),mae=('error','mean'),coverage=('certificate_covered','mean')).reset_index();fixed['certificate_width']=2*fixed.radius
fixed.to_csv(O/'fixed_recomputed.csv',index=False)
keys=['surface','scenario','replicate','schedule','mode','tolerance','budget']
mn=f[f.method=='optimized__minimum'].set_index(keys);bar=f[f.method=='optimized__barycentric'].set_index(keys)
assert mn.index.equals(bar.index)
minbar=dict(states=len(mn),release_disagreements=int((mn.released!=bar.released).sum()),cost_disagreements=int((mn.new_n!=bar.new_n).sum()),radius_disagreements=int((abs(mn.radius-bar.radius)>1e-10).sum()),max_absolute_radius_diff=float(abs(mn.radius-bar.radius).max()))
pk=['surface','scenario','replicate','schedule','mode','stage'];pm=p[p.method=='optimized__minimum'].set_index(pk);pb=p[p.method=='optimized__barycentric'].set_index(pk)
delta=(2*(pb.radius-pm.radius)).rename('width_improvement').reset_index()
cell=delta.groupby(['surface','scenario','schedule','mode','stage']).width_improvement.mean().reset_index();cell.to_csv(O/'min_vs_barycentric_width.csv',index=False)
same=pm.reset_index();same['lip_stricter']=same.lipschitz_radius<same.barycentric_radius-1e-10;same['bar_to_min']=same.barycentric_radius-same.minimum_radius
same.groupby(['surface','scenario']).agg(states=('radius','size'),lip_stricter_fraction=('lip_stricter','mean'),mean_radius_improvement=('bar_to_min','mean'),max_radius_improvement=('bar_to_min','max')).reset_index().to_csv(O/'same_weight_recomputed.csv',index=False)
cal=pd.read_csv(R/'current_method/results/full_plus/plus_calibration_sensitivity_records.csv')
cal.groupby(['n_cal','k']).agg(n=('covered','size'),coverage=('covered','mean'),infinite_fraction=('is_infinite','mean')).reset_index().to_csv(O/'calibration_recomputed.csv',index=False)
opt=pd.read_csv(R/'current_method/results/full_plus/plus_optimizer_audit.csv')
nsw=pd.read_csv(R/'legacy_audits/results/nsw_method_error_records.csv')
nsw['interval_width']=nsw.interval_upper-nsw.interval_lower
nsw.groupby('method').agg(n=('accepted','size'),mae=('absolute_reconstruction_error','mean'),acceptance=('accepted','mean'),coverage=('interval_includes_reference','mean'),width=('interval_width','mean')).reset_index().to_csv(O/'legacy_nsw_recomputed.csv',index=False)
nkey=['seed_batch','replicate','split_seed','target_object_id'];n1=nsw[nsw.method=='atlas'].set_index(nkey);n2=nsw[nsw.method=='atlas_no_rejection'].set_index(nkey)
synt=pd.read_csv(R/'legacy_audits/results/extensions/synthetic_baselines_records.csv')
synt.groupby(['scenario','method']).agg(n=('released','size'),mae=('absolute_error','mean'),release=('released','mean')).reset_index().to_csv(O/'legacy_synthetic_recomputed.csv',index=False)
meta=dict(stopped_rows=len(f),planned_rows=len(p),worlds=len(f[['surface','scenario','replicate']].drop_duplicates()),
 minbar=minbar,max_cell_width_improvement=cell.loc[cell.width_improvement.idxmax()].to_dict(),
 min_cell_width_improvement=cell.loc[cell.width_improvement.idxmin()].to_dict(),
 all_coverage=float(f.covered.mean()),all_bad_releases=int(f.bad_release.sum()),
 solver_failures=int(p.solver_failures.sum()),global_claims=int(p.global_optimum_certified.sum()),
 optimizer_audit=dict(n=len(opt),mean_gap=float(opt.gap.mean()),median_relative_gap=float(opt.relative_gap.median()),max_gap=float(opt.gap.max()),times_random_better=int((opt.gap>1e-10).sum()),failures=int(opt.solver_failures.sum()),global_claims=int(opt.global_optimum_certified.sum())),
 legacy_nsw_identical_estimate_max_abs=float(abs(n1.reconstructed_contrast-n2.reconstructed_contrast).max()),
 source_hashes={})
for name in ['source_sha256','artifact_sha256']:
 manifest=json.loads((A/'run_manifest.json').read_text())
 if name in manifest:
  match={}
  for k,v in manifest[name].items():
   path=(R/'current_method'/k.replace('\\','/')) if name=='source_sha256' else (A/k.replace('\\','/'))
   match[k]=hashlib.sha256(path.read_bytes()).hexdigest()==v if path.exists() else 'missing'
  meta[name]=match
(O/'audit_summary.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(meta,ensure_ascii=False,indent=2))
print(summary[(summary.scenario=='bridgeable')&(summary.schedule=='random')].to_string(index=False))
print(fixed[(fixed.scenario=='bridgeable')&(fixed.schedule=='random')&(fixed['mode']=='r2')].to_string(index=False))
print(pd.read_csv(O/'same_weight_recomputed.csv').to_string(index=False))
