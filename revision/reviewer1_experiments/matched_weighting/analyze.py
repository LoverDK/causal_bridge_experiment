"""Read-only Appendix P extension. No experimental imports, fitting or simulation."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
from pathlib import Path
import gzip, hashlib, json, time, platform
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parent
CFG=json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
ROOT=Path(CFG['source_root']); P=ROOT/'current_method/results/ablations_full'
START=time.perf_counter()
METHODS=CFG['methods']; SURFACES=CFG['surfaces']
KEY=['surface','scenario','replicate','schedule','mode','method']
BASE=['scenario','schedule','mode','tolerance','budget','method','regime']
METRICS=['release','participants','first_release_cost_conditional','all_target_mae','released_mae',
         'certificate_width','returned_output_width','certificate_coverage','output_coverage',
         'path_coverage','bad_release','selective_risk']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=[P/'records.csv',P/'plans.jsonl.gz',P/'run_manifest.json',P/'paired_differences.csv',
        ROOT/'current_method/atlas_new/ablations.py',ROOT/'current_method/atlas_new/workflow.py',
        ROOT/'current_method/docs/ablation_protocol.md',ROOT/'revision/review_tracker.json',
        ROOT/'revision/REVIEW_TRACKER.md',ROOT/'revision/FIRST_WORKFLOW.md',ROOT/'AGENTS.md']
input_hashes={str(p):sha(p) for p in inputs}
tracker=json.loads((ROOT/'revision/review_tracker.json').read_text(encoding='utf-8'))
issues=tracker.get('issues',tracker.get('concerns',[]))
assert len(issues)==12, tracker.keys()
review=[]
for phase in ['before','after']:
 for i in issues:
  relevant=i['id'] in CFG['review_scope']
  review.append(dict(phase=phase,id=i['id'],title=i['title'],status_before=i['status'],status_after=i['status'],
      evidence='REPORT.md; metrics_all_caps.csv; paired_intervals_cap288.csv' if relevant else 'No new evidence for this concern.',
      scope=('Saved synthetic weighting/certificate/order audit only; no external or adaptive validity established.' if relevant
             else 'Not investigated; original status preserved.'),resolved=False))
(OUT/'review_status_before_after.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')

df=pd.read_csv(P/'records.csv')
assert len(df)==345600 and not df.duplicated(KEY+['tolerance','budget']).any()
source_manifest=json.loads((P/'run_manifest.json').read_text())
assert sha(P/'records.csv')==source_manifest['artifacts']['records.csv']['sha256']
df=df[df.method.isin(METHODS)].copy()
df['regime']='first_release_stopped'
df['certificate_width']=2*df.radius
df['output_width']=df.width
df['path_coverage']=df.path_covered
df['output_coverage']=df.covered
df['participants']=df.new_n

plans=[]; prefixes={}; prefix_mismatches=0; simplex_failures=0; plan_count=0
decompressed=hashlib.sha256()
with gzip.open(P/'plans.jsonl.gz','rb') as f:
 for raw in f:
  decompressed.update(raw); p=json.loads(raw); plan_count+=1
  key=tuple(p[k] for k in ['surface','scenario','replicate','schedule','stage'])
  ids=tuple(p['ids'])
  if key in prefixes and prefixes[key]!=ids: prefix_mismatches+=1
  prefixes[key]=ids
  if min(p['weights']) < -1e-10 or abs(sum(p['weights'])-1)>1e-8: simplex_failures+=1
  if p['method'] in METHODS:
   plans.append({k:p[k] for k in KEY+['stage','radius','error','estimate','truth','certificate_covered']})
assert plan_count==172800 and prefix_mismatches==simplex_failures==0
assert decompressed.hexdigest()==source_manifest['artifacts']['plans.jsonl']['sha256']
fixed=pd.DataFrame(plans).rename(columns={'stage':'budget'})
fixed=fixed.sort_values(KEY+['budget'])
fixed['path_coverage']=fixed.groupby(KEY,sort=False).certificate_covered.cummin()
fixed['participants']=96*fixed.budget
fixed['certificate_width']=2*fixed.radius
fixed['output_width']=np.nan
fixed['output_coverage']=np.nan
fixed['regime']='complete_prefix'
fixed=pd.concat([fixed.assign(tolerance=t,released=fixed.radius.le(t),bad_release=fixed.radius.le(t)&fixed.error.gt(t))
                 for t in CFG['tolerances']],ignore_index=True)
all_rows=pd.concat([df,fixed],ignore_index=True)
assert len(all_rows)==460800

def metric_data(g):
 # Numerators and release denominator permit paired ratio bootstrap without changing target cohorts.
 r=g.released.to_numpy(float); e=g.error.to_numpy(float); c=g.participants.to_numpy(float)
 vals=np.column_stack([r,c,c*r,e,e*r,g.certificate_width,g.output_width,
                       g.certificate_covered,g.output_coverage,g.path_coverage,g.bad_release,
                       g.bad_release])
 if g.regime.iloc[0]!='first_release_stopped': vals[:,2]=np.nan
 return vals

def normalize(v):
 v=np.array(v,copy=True,dtype=float)
 with np.errstate(invalid='ignore',divide='ignore'):
  for j in [2,4,11]: v[...,j]=np.divide(v[...,j],v[...,0],out=np.full_like(v[...,j],np.nan),where=v[...,0]>0)
 return v

point=[]
for key,g in all_rows.groupby(BASE+['surface'],sort=True):
 v=normalize(metric_data(g).mean(axis=0))
 point.append(dict(zip(BASE+['surface'],key))|dict(n_worlds=len(g),n_released=int(g.released.sum()),
   **dict(zip(METRICS,v))))
for key,g in all_rows.groupby(BASE,sort=True):
 assert len(g)==600
 v=normalize(metric_data(g).mean(axis=0))
 point.append(dict(zip(BASE,key))|dict(surface='pooled',n_worlds=len(g),n_released=int(g.released.sum()),
   **dict(zip(METRICS,v))))
points=pd.DataFrame(point)
points['budget_participants']=96*points.budget
points.to_csv(OUT/'metrics_all_caps.csv',index=False)
print('Descriptive metrics complete:',len(points),'rows; seconds',round(time.perf_counter()-START,2),flush=True)

terminal=all_rows[all_rows.budget.eq(3)]
cols=['regime','schedule','mode','tolerance','method']
rng=np.random.default_rng(CFG['bootstrap']['seed'])
B=CFG['bootstrap']['repetitions']
cis=[]; paired=[]

def interval(v):
 if not np.isfinite(v).any(): return np.nan,np.nan,0
 good=v[np.isfinite(v)]
 lo,hi=np.quantile(good,[.025,.975]);return float(lo),float(hi),len(good)

def write_intervals(scenario,surface,grps,means,draws):
 # Each draw uses the same whole-world resample for every method/metric/budget regime.
 norm=normalize(draws)
 pm=normalize(means)
 for j,key in enumerate(grps):
  tag=dict(zip(cols,key))|dict(scenario=scenario,surface=surface,budget=3,budget_participants=288)
  for m,name in enumerate(METRICS):
   lo,hi,nvalid=interval(norm[:,j,m])
   cis.append(tag|dict(metric=name,estimate=pm[j,m],lower=lo,upper=hi,valid_draws=nvalid))
  if key[-1]!='optimized__minimum':continue
  for method in METHODS[1:]:
   other=grps.index(key[:-1]+(method,))
   diff=norm[:,j,:]-norm[:,other,:]
   for m,name in enumerate(METRICS):
    lo,hi,nvalid=interval(diff[:,m])
    paired.append(tag|dict(comparator=method,metric=name,difference=pm[j,m]-pm[other,m],lower=lo,upper=hi,valid_draws=nvalid))

for scenario in CFG['geometries']:
 sdraw=[]; smeans=[]; groupkeys=None
 for surface in SURFACES:
  g=terminal[terminal.scenario.eq(scenario)&terminal.surface.eq(surface)]
  groups=list(g.groupby(cols,sort=True))
  groupkeys=[tuple(k) for k,_ in groups]
  mat=np.stack([metric_data(h.sort_values('replicate')) for _,h in groups],axis=1)
  assert mat.shape==(200,64,12),mat.shape
  counts=rng.multinomial(200,np.full(200,1/200),size=B).astype(float)/200
  draws=(counts @ mat.reshape(200,-1)).reshape(B,64,12)
  means=mat.mean(axis=0)
  sdraw.append(draws);smeans.append(means)
  write_intervals(scenario,surface,groupkeys,means,draws)
 write_intervals(scenario,'pooled',groupkeys,np.mean(smeans,axis=0),np.mean(sdraw,axis=0))
 print('Bootstrap complete:',scenario,'seconds',round(time.perf_counter()-START,2),flush=True)
pd.DataFrame(cis).to_csv(OUT/'metric_intervals_cap288.csv',index=False)
paired=pd.DataFrame(paired)
paired.to_csv(OUT/'paired_intervals_cap288.csv',index=False)

# A separate legacy ledger preserves exact original published-seed paired intervals.
legacy=pd.read_csv(P/'paired_differences.csv')
legacy=legacy[legacy.comparator.isin(METHODS[1:])]
legacy.to_csv(OUT/'original_seed_paired_intervals.csv',index=False)

# Verify shared workflow records against independent saved run (not just matching labels).
wpath=ROOT/'current_method/results/workflow_full/workflow_records.csv'
w=pd.read_csv(wpath); input_hashes[str(wpath)]=sha(wpath)
overlaps=[]
for order,name in [('random','r2_random'),('nearest','r2_nearest')]:
 a=df[df.schedule.eq(order)&df['mode'].eq('r2')&df.method.eq('optimized__minimum')]
 b=w[w.method.eq(name)]
 j=a.merge(b,on=['surface','scenario','replicate','tolerance','budget'],validate='one_to_one',suffixes=('_p','_l'))
 differences={k:float(np.max(abs(j[k+'_p'].astype(float)-j[k+'_l'].astype(float))))
              for k in ['new_n','radius','estimate','error','released','bad_release','width','path_covered']}
 assert len(j)==14400 and max(differences.values())<1e-10
 overlaps.append(dict(schedule=order,n=len(j),max_absolute_differences=differences))

def select(regime,method,tol=.3,surface='pooled',order='random',mode='r2',scenario='bridgeable'):
 return points[(points.regime==regime)&(points.method==method)&(points.tolerance==tol)&(points.surface==surface)&
               (points.schedule==order)&(points['mode']==mode)&(points.scenario==scenario)&(points.budget==3)].iloc[0]
headlines=[]
for method in METHODS:
 for regime in CFG['regimes']:
  row=select(regime,method)
  headlines.append(row.to_dict())
pd.DataFrame(headlines).to_csv(OUT/'headline_regime_audit.csv',index=False)
assert int(select('first_release_stopped','uniform__minimum').n_released)==122
assert int(select('complete_prefix','uniform__minimum').n_released)==120
negative=points[(points.scenario=='bridgeable')&(points.schedule=='nearest')&(points.tolerance==.2)&(points['mode']=='r2')]
assert negative.release.eq(0).all()
checks=dict(source_record_rows=345600,retained_stopped_rows=len(df),plan_rows=plan_count,
 complete_prefix_rows=len(fixed),independent_worlds=1800,worlds_per_geometry=600,worlds_per_surface_geometry=200,
 shared_prefix_keys=len(prefixes),shared_prefix_failures=prefix_mismatches,simplex_failures=simplex_failures,
 decompressed_plan_hash=decompressed.hexdigest(),workflow_overlap=overlaps,
 stopped_all_bad_release_count=int(df.bad_release.sum()),stopped_all_path_covered=bool(df.path_covered.all()),
 fixed_all_certificate_covered=bool(fixed.certificate_covered.all()),stopped_uniform_release=122/600,
 complete_prefix_uniform_release=120/600,nearest_r2_bridgeable_delta02_all_refuse=True)
(OUT/'audit_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
elapsed=time.perf_counter()-START
manifest=dict(analysis_id=CFG['analysis_id'],analysis_type='saved-output arithmetic; no simulation or fitting',
 input_sha256=input_hashes,source_manifest_sha256=sha(P/'run_manifest.json'),
 code_sha256=sha(Path(__file__)),protocol_sha256=sha(OUT/'protocol.json'),
 output_sha256={p.name:sha(p) for p in OUT.glob('*') if p.is_file() and p.name not in ['manifest.json','REPORT.md']},
 elapsed_seconds=elapsed,forecast_seconds=CFG['forecast']['wall_seconds'],
 python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,
 bootstrap_seed=CFG['bootstrap']['seed'],bootstrap_repetitions=B,
 caveat='Fresh Monte Carlo bootstrap of existing worlds; not independent new simulation; ratio CIs undefined when no releases. Individual intervals do not adjust for multiplicity.')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(json.dumps(dict(elapsed_seconds=elapsed,point_rows=len(points),metric_ci_rows=len(cis),paired_ci_rows=len(paired),checks=checks),indent=2))
