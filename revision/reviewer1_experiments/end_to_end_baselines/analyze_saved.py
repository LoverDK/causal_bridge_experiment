"""Saved-record arithmetic only: no experiment imports, generation, or fitting."""
from pathlib import Path
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ[k]='1'
import json, hashlib, time, warnings
import numpy as np
import pandas as pd

T=time.perf_counter(); O=Path(__file__).resolve().parent
E=Path('C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild')
A=O.parents[1]/'reviewer1_baseline_revision'
LFILE=E/'current_method/results/workflow_full/workflow_records.csv'
PFILE=E/'current_method/results/ablations_full/records.csv'
TRACK=E/'revision/review_tracker.json'
tracker=json.loads(TRACK.read_text(encoding='utf-8'))
concerns=tracker.get('issues',tracker.get('concerns',[]))
assert len(concerns)==12
statuses=[dict(id=x['id'],title=x['title'],before=x['status'],after=x['status'],status_changed=False,
 evidence_scope=('saved synthetic comparison and statistical denominator extension' if x['id'] in ['REV-07','REV-12'] else 'no new acceptance evidence; prior status preserved')) for x in concerns]
(O/'concern_statuses.json').write_text(json.dumps(statuses,ensure_ascii=False,indent=2),encoding='utf-8')

l=pd.read_csv(LFILE); p=pd.read_csv(PFILE)
assert len(l)==86400 and len(p)==345600
K=['surface','scenario','replicate','tolerance','budget']
truth=l.drop_duplicates(K)[K+['truth']]
assert len(truth)==14400
p=p.merge(truth,on=K,validate='many_to_one')
overlap=[]
for order in ['random','nearest']:
 x=p[(p['method']=='optimized__minimum')&(p['mode']=='r2')&(p.schedule==order)].set_index(K).sort_index()
 y=l[l.method.eq('r2_'+order)].set_index(K).sort_index()
 assert x.index.equals(y.index)
 fields=['radius','estimate','error','width','new_n','released','bad_release','covered','path_covered','certificate_covered','joint_set_covered']
 for f in fields:
  err=float(np.max(np.abs(x[f].astype(float).to_numpy()-y[f].astype(float).to_numpy())))
  assert err==0,(order,f,err)
  overlap.append(dict(schedule=order,field=f,rows=len(x),maximum_difference=err))
pd.DataFrame(overlap).to_csv(O/'overlap_verification.csv',index=False)
p=p[p['bound'].eq('minimum')].copy()
p=p[~((p['weight_rule']=='optimized')&(p['mode']=='r2'))]
p['source']='P'; p['method']=p['mode']+'_'+p.schedule+'_'+p.weight_rule
l['source']='L'
cols=K+['method','source','new_n','radius','estimate','truth','error','released','bad_release','width','covered','path_covered']
d=pd.concat([l[cols],p[cols]],ignore_index=True)
assert not d.duplicated(K+['method']).any()
methods=sorted(d.method.unique()); assert len(methods)==20,len(methods)
metrics=['release','refusal','mae','released_mae','output_width','certificate_width','path_coverage','output_coverage','conditional_release_coverage','participants','conditional_first_release_cost','exhaustion_without_release','joint_bad_release','conditional_bad_release_risk','sign_error_among_released']
def evaluate(s):
 # last axis: release,error,error*release,width,2R,path,covered,covered*release,cost,cost*release,exhaust,bad,sign,nonzero_release
 out=np.stack([s[...,0],1-s[...,0],s[...,1],divide(s[...,2],s[...,0]),s[...,3],s[...,4],s[...,5],s[...,6],divide(s[...,7],s[...,0]),s[...,8],divide(s[...,9],s[...,0]),s[...,10],s[...,11],divide(s[...,11],s[...,0]),divide(s[...,12],s[...,13])],axis=-1)
 return out
def divide(a,b):
 return np.divide(a,b,out=np.full(np.broadcast_shapes(np.shape(a),np.shape(b)),np.nan),where=b>0)
def bounds(a):
 # Nearest empirical percentiles preserve +/-infinity without inf-inf interpolation.
 with warnings.catch_warnings():
  warnings.simplefilter('ignore',RuntimeWarning)
  return np.nanquantile(a,[.025,.975],axis=0,method='nearest')

rng=np.random.default_rng(2026110804); B=2000
rows=[]; pairs=[]; Bfact=[]
for (scenario,tol,budget),g in d.groupby(['scenario','tolerance','budget'],sort=True):
 surfaces=sorted(g.surface.unique()); central=[]; boots=[]; gstrata=[]
 for surface in surfaces:
  s=g[g.surface.eq(surface)].sort_values(['replicate','method'])
  assert len(s)==200*len(methods)
  assert s.method.to_list()==methods*200
  rel=s.released.to_numpy(float); err=s.error.to_numpy(); cost=s.new_n.to_numpy(); target=s.truth.to_numpy()
  nz=(target!=0); cap=budget*96
  exhausted=(~s.released.to_numpy())&(cost>=cap)&(cap>0)
  suff=np.stack([rel,err,err*rel,s.width,2*s.radius,s.path_covered,s.covered,s.covered.to_numpy()*rel,cost,cost*rel,exhausted,s.bad_release,(s.estimate.to_numpy()*target<0)*rel,nz*rel],axis=-1).astype(float).reshape(200,len(methods),14)
  central.append(suff.mean(axis=0))
  # One bootstrap multiplicity vector per world, shared across all methods.
  counts=rng.multinomial(200,np.full(200,1/200),size=B)
  flat=suff.reshape(200,-1)
  assert not np.isnan(flat).any()
  weighted=counts@np.where(np.isfinite(flat),flat,0)/200
  weighted[(counts@np.isposinf(flat).astype(float))>0]=np.inf
  weighted[(counts@np.isneginf(flat).astype(float))>0]=-np.inf
  boots.append(weighted.reshape(B,len(methods),14))
  gstrata.append(s)
 for i,surface in enumerate(surfaces+['ALL']):
  if surface=='ALL':
   c=evaluate(np.mean(central,axis=0)); bs=evaluate(np.mean(boots,axis=0)); actual=g; n=600
  else:
   c=evaluate(central[i]);bs=evaluate(boots[i]);actual=gstrata[i];n=200
  low,high=bounds(bs)
  for j,m in enumerate(methods):
   a=actual[actual.method.eq(m)]; nr=int(a.released.sum())
   row=dict(surface=surface,scenario=scenario,tolerance=tol,budget_cap=budget*96,method=m,source=a.source.iloc[0],regime='first-release stopped',n_worlds=n,n_released=nr,n_refused=n-nr,n_bad_release=int(a.bad_release.sum()),n_sign_errors=int(((a.estimate*a.truth<0)&a.released).sum()),n_zero_truth=int(a.truth.eq(0).sum()),n_exhausted=int(((~a.released)&(a.new_n>=budget*96)&(budget>0)).sum()))
   for q,metric in enumerate(metrics):
    row[metric]=c[j,q];row[metric+'_lo']=low[j,q];row[metric+'_hi']=high[j,q]
   row['conditional_boot_valid']=int(np.isfinite(bs[:,j,8]).sum())
   row['n_unbounded_width']=int(np.isinf(a.width).sum())
   row['n_nonfinite_width']=int((~np.isfinite(a.width)).sum())
   rows.append(row)
  j=methods.index('r2_targeted')
  for k,m in enumerate(methods):
   if k==j:continue
   dif=bs[:,j,:]-bs[:,k,:]
   lo,hi=bounds(dif)
   for q,metric in enumerate(metrics):
    pairs.append(dict(surface=surface,scenario=scenario,tolerance=tol,budget_cap=budget*96,comparator=m,metric=metric,n_pairs=n,targeted_minus_comparator=c[j,q]-c[k,q],lower=lo[q],upper=hi[q],valid_bootstrap=int((~np.isnan(dif[:,q])).sum())))
 print('complete',scenario,tol,budget,flush=True)

out=pd.DataFrame(rows); out.to_csv(O/'surface_cap_metrics.csv',index=False)
pd.DataFrame(pairs).to_csv(O/'paired_targeted_contrasts.csv',index=False)
old=pd.read_csv(A/'workflow_common_cap_metrics.csv')
join=out[(out.surface=='ALL')&(out.source=='L')].assign(budget=lambda z:z.budget_cap//96).merge(old,on=['scenario','tolerance','method','budget'],validate='one_to_one',suffixes=('','_old'))
assert len(join)==144
checks={}
for new,prior in [('release','release_old'),('participants','mean_new_n'),('mae','all_target_mae'),('output_width','mean_output_width'),('path_coverage','path_coverage_old'),('output_coverage','output_coverage_old')]:
 checks[new]=float(np.max(np.abs(join[new]-join[prior])));assert checks[new]<1e-12
facts=out[(out.surface=='ALL')&(out.scenario=='bridgeable')&(out.method.isin(['r2_targeted','r2_random','r2_nearest','target_only']))]
facts.to_csv(O/'claim_facts.csv',index=False)
manifest=dict(kind='saved-output reanalysis; no new worlds',seed=2026110804,bootstrap_repetitions=B,bootstrap_unit='world; paired across methods; surface-stratified pooled',independent_worlds=1800,raw_L_rows=len(l),raw_P_rows=345600,overlap_rows=28800,methods=methods,metric_rows=len(out),paired_contrast_rows=len(pairs),prior_metric_max_difference=checks,seconds=time.perf_counter()-T,inputs={})
inputs=[LFILE,PFILE,TRACK,E/'AGENTS.md',E/'revision/REVIEW_TRACKER.md',E/'revision/FIRST_WORKFLOW.md',E/'current_method/results/workflow_full/run_manifest.json',E/'current_method/results/ablations_full/run_manifest.json',A/'unified_stopped_metrics.csv',A/'workflow_common_cap_metrics.csv',A/'agent4_end_to_end_design.md',O/'PROTOCOL.md']
for f in inputs:manifest['inputs'][str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
(O/'analysis_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in manifest.items() if k!='inputs'},indent=2))
