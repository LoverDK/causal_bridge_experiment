"""Independent comparison against original precomputed surface-cell tables."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
W=Path(__file__).resolve().parent
cfg=json.loads((W/'protocol.json').read_text())
P=Path(cfg['source_root'])/'current_method/results/ablations_full'
ours=pd.read_csv(W/'metrics_all_caps.csv')
key=['surface','scenario','schedule','mode','method','tolerance','budget']
mapping={'release':'released','participants':'new_n','all_target_mae':'error',
         'released_mae':'released_mae','certificate_coverage':'certificate_covered',
         'bad_release':'bad_release','selective_risk':'released_bad_rate'}
result=[]
for regime,name,widthname in [('first_release_stopped','stopped_cells.csv','returned_output_width'),
                              ('complete_prefix','fixed_budget_cells.csv','certificate_width')]:
 saved=pd.read_csv(P/name)
 saved=saved[saved.method.isin(cfg['methods'])]
 z=ours[(ours.regime==regime)&(ours.surface!='pooled')].merge(saved,on=key,suffixes=('_ours','_saved'),validate='one_to_one')
 assert len(z)==1152
 diffs={}
 for a,b in mapping.items():
  x=z[a+'_ours'] if a in saved.columns else z[a]
  y=z[b+'_saved'] if b in ours.columns else z[b]
  assert x.isna().equals(y.isna()),(name,a)
  diffs[a]=float(np.max(abs(x.fillna(0)-y.fillna(0))))
  assert diffs[a]<1e-10,(name,a,diffs[a])
 diffs['width']=float(np.max(abs(z[widthname]-z.width)))
 assert diffs['width']<1e-10
 if regime=='first_release_stopped':
  assert np.allclose(z.path_coverage,z.path_covered)
 result.append(dict(regime=regime,rows=len(z),maximum_absolute_differences=diffs,
                    saved_summary_sha256=hashlib.sha256((P/name).read_bytes()).hexdigest()))
raw=pd.read_csv(P/'records.csv')
paired=raw[raw.method.isin(['optimized__minimum','optimized__barycentric'])].pivot(
 index=['surface','scenario','replicate','schedule','mode','tolerance','budget'],columns='method',values=['released','new_n'])
geom={m:int((paired[(m,'optimized__minimum')]!=paired[(m,'optimized__barycentric')]).sum()) for m in ['released','new_n']}
assert max(geom.values())==0
source_manifest=json.loads((P/'run_manifest.json').read_text())
source_checks={name:hashlib.sha256((Path(cfg['source_root'])/'current_method'/name).read_bytes()).hexdigest()==digest
               for name,digest in source_manifest['source_sha256'].items()}
assert all(source_checks.values())
out=dict(summary_comparisons=result,minimum_vs_barycentric_stopped_mismatches=geom,source_hash_matches=source_checks,
         statement='Saved independent cell summaries agree; this checks arithmetic and attribution, not new scientific validity.')
(W/'independent_summary_checks.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
