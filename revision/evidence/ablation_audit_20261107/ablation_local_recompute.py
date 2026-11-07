from pathlib import Path
import pandas as pd
import numpy as np
import json, sys
R=Path(r'C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/outputs/experiment-rebuild')
O=Path(r'C:/Users/Qiutian/Documents/Codex/2026-11-07/wo/work/ablation_audit_data')
def read(f):return pd.read_csv(R/f)
oper=read('current_method/results/full/operational_records.csv')
oper['coverage_num']=pd.to_numeric(oper.covered.replace({'True':1,'False':0}),errors='coerce')
ops=oper.groupby(['scenario','method']).agg(n=('error','size'),mae=('error','mean'),coverage=('coverage_num','mean'),width=('width','mean')).reset_index()
ops.to_csv(O/'operational_recomputed.csv',index=False)
joint=read('current_method/results/full/joint_calibration_records.csv')
js=joint.groupby(['k','test_scale','method']).agg(n=('joint_covered','size'),coverage=('joint_covered','mean'),marginal=('marginal_fraction','mean'),radius=('radius','mean')).reset_index()
js.to_csv(O/'joint_recomputed.csv',index=False)
ml=read('current_method/results/real_supplement/holdouts.csv')
ms=ml.groupby(['protocol','method']).agg(n=('error','size'),mae=('error','mean'),width=('width','mean'),inclusion=('included','mean')).reset_index()
ms.to_csv(O/'manylabs_recomputed.csv',index=False)
matched=read('current_method/results/real_supplement/matched_archive_size.csv')
matchedmean=matched.groupby('source').error.mean().mean()
ex=read('current_method/exatlas/stress_records.csv')
xs=[]
for key,g in ex.groupby(['scenario','level']):
 xs.append(dict(scenario=key[0],level=key[1],n=len(g),ex_release=g.ex_composable.mean(),ex_all_mae=g.ex_abs_error.mean(),ex_released_mae=g[g.ex_composable].ex_abs_error.mean(),atlas_release=g.atlas_accepted.mean(),atlas_released_mae=g.atlas_abs_error.mean()))
pd.DataFrame(xs).to_csv(O/'exatlas_recomputed.csv',index=False)
sys.path.insert(0,str(R/'current_method'))
from atlas_new.core import calibrated_quantile
detail={'matched_size_rows':len(matched),'matched_size_targets':matched.source.nunique(),'matched_size_reps':sorted(matched.groupby('source').size().unique().tolist()),'matched_size_mae':matchedmean,'small_calibration_n10_isinf':bool(np.isinf(calibrated_quantile(np.arange(10),.05))),'contamination_variance':.99+.01*8**2,'operational_invalid_metadata_counts':oper[(oper.method.isin(['singleton_U','no_curvature','adaptive_R2_invalid'])) & (oper.assumption_valid)].groupby('method').size().to_dict()}
(O/'local_summary.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(detail,ensure_ascii=False,indent=2))
print(ops[ops.method.isin(['robust_Rinf','design_R2','singleton_U','no_curvature'])].to_string(index=False))
print(ms.to_string(index=False));print(pd.DataFrame(xs).to_string(index=False))
