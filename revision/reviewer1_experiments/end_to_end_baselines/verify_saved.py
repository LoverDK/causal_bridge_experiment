"""Independent pandas denominator checks; never imports the analysis implementation."""
from pathlib import Path
import pandas as pd
import numpy as np
import json,hashlib
O=Path(__file__).resolve().parent
E=Path('C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild/current_method/results')
l=pd.read_csv(E/'workflow_full/workflow_records.csv')
p=pd.read_csv(E/'ablations_full/records.csv')
truth=l[['surface','scenario','replicate','truth']].drop_duplicates()
assert len(truth)==1800
p=p.merge(truth,on=['surface','scenario','replicate'],validate='many_to_one')
p=p[(p['bound']=='minimum')&~((p.weight_rule=='optimized')&(p['mode']=='r2'))].copy()
p['method']=p['mode']+'_'+p.schedule+'_'+p.weight_rule
raw=pd.concat([l,p],ignore_index=True)
out=pd.read_csv(O/'surface_cap_metrics.csv')
assert len(out)==1920
maxerr=0.; checks=0
for r in out.itertuples(index=False):
 a=raw[(raw.scenario==r.scenario)&(raw.tolerance==r.tolerance)&(raw.budget==r.budget_cap//96)&(raw.method==r.method)]
 if r.surface!='ALL': a=a[a.surface==r.surface]
 assert len(a)==r.n_worlds
 b=a[a.released]
 expect={'conditional_release_coverage':b.covered.mean(),'conditional_first_release_cost':b.new_n.mean(),
  'released_mae':b.error.mean(),'sign_error_among_released':(b[b.truth!=0].estimate*b[b.truth!=0].truth<0).mean(),
  'exhaustion_without_release':((~a.released)&(a.new_n>=r.budget_cap)&(r.budget_cap>0)).mean(),
  'joint_bad_release':a.bad_release.mean()}
 for k,v in expect.items():
  saved=getattr(r,k)
  if pd.isna(v):assert pd.isna(saved)
  else:
   err=abs(v-saved); assert err<1e-12,(r.surface,r.method,k,v,saved); maxerr=max(maxerr,err)
  checks+=1
z=out[out.n_released==0]
assert z[['released_mae','conditional_release_coverage','conditional_first_release_cost','conditional_bad_release_risk','sign_error_among_released']].isna().all().all()
direct0=out[(out.method=='target_only')&(out.budget_cap==0)]
assert np.isposinf(direct0[['output_width','output_width_lo','output_width_hi','certificate_width','certificate_width_lo','certificate_width_hi']]).all().all()
x=out[(out.surface=='ALL')&(out.scenario=='bridgeable')&(out.method=='target_only')&(out.budget_cap==288)]
assert int(x[x.tolerance==.3].n_bad_release.iloc[0])==1
assert x[x.tolerance==.2].output_coverage.iloc[0]==1
assert abs(x[x.tolerance==.2].path_coverage.iloc[0]-599/600)<1e-12
status=json.loads((O/'concern_statuses.json').read_text(encoding='utf-8'))
assert len(status)==12 and all(r['before']==r['after'] for r in status)
result={'passed':True,'independent_conditional_checks':checks,'maximum_absolute_difference':maxerr,
 'zero_release_NA_checked_rows':len(z),'unbounded_direct_zero_cap_rows':len(direct0),
 'direct_bad_release_and_path_events_preserved':True,'concern_statuses_unchanged':12}
(O/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
files=[f for f in sorted(O.iterdir()) if f.is_file() and f.name!='artifact_hashes.json']
(O/'artifact_hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in files},indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
