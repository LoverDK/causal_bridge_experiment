"""Read-only replay of frozen certificates from aggregate inputs and saved weights.

This verifies arithmetic, decision rules and reported reference metrics. It does
not re-estimate weights, reopen individual outcomes or validate model assumptions.
"""
from pathlib import Path
import hashlib,json,math
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
def read(name):return pd.read_csv(ROOT/name)
def main():
    m=json.loads((ROOT/'package_manifest.json').read_text(encoding='utf-8'))
    for name,h in m['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
    counts=read('aggregate_inputs/profile_counts.csv')
    source=read('results/source_estimates_pre_reveal.csv').set_index('source')
    inputs=read('results/source_inputs.csv')
    weights=read('results/weights.csv')
    pred=read('results/predictions_pre_reveal.csv')
    assert len(pred)==102 and pred.target.nunique()==17 and len(weights)==4080
    def pr(site,arm):
        row=counts[(counts.source==site)&(counts.arm==arm)].iloc[0]
        return np.array([row.male,row.female,row.other])/row.n,row.unknown/row.n,int(row.n)
    def tv(site):
        a,ar,n1=pr(site,1);b,br,n0=pr(site,0)
        vertices1=a+ar*np.eye(3);vertices0=b+br*np.eye(3)
        return np.max(.5*np.abs(vertices1[:,None,:]-vertices0[None,:,:]).sum(2))
    c2=math.sqrt(2*math.log(2/(.025/68)))
    ci=math.sqrt(2*math.log(2*40/.025))
    L=math.sqrt(8/3)
    residuals=[]
    def eq(a,b):
        discrepancy=float(np.max(np.abs(np.asarray(a)-np.asarray(b))))
        residuals.append(discrepancy)
        assert discrepancy<1e-11,(a,b,discrepancy)
    for x in inputs.itertuples():
        lo,unknown,n=pr(x.source,-1)
        tl,tr,tn=pr(x.target,-1)
        eq(lo,[x.male_lower,x.female_lower,x.other_lower]);eq(unknown,x.unknown_mass)
        eq(tl,[x.target_male_lower,x.target_female_lower,x.target_other_lower]);eq(tr,x.target_unknown_mass)
        eq(tv(x.source),x.beta_imbalance)
        eq(math.sqrt(.25*(1/pr(x.source,1)[2]+1/pr(x.source,0)[2])),x.s)
    computed=[]
    for x in pred.itertuples():
        w=weights[(weights.target==x.target)&(weights.policy==x.policy)].sort_values('source')
        a=w.weight.to_numpy();assert np.min(a)>=0;eq(a.sum(),1)
        lo=np.array([pr(k,-1)[0] for k in w.source]);ur=np.array([pr(k,-1)[1] for k in w.source])
        tl,tr,n=pr(x.target,-1)
        g=L*max(np.linalg.norm(tl+tr*np.eye(3)[b]-a@lo-(a@ur)*np.eye(3)[c]) for b in range(3) for c in range(3))
        beta=a@np.array([tv(k) for k in w.source]);noise2=c2*np.linalg.norm(a*w.s.to_numpy());noiseinf=ci*(a@w.s.to_numpy())
        est=a@source.loc[w.source,'estimate'].to_numpy()
        for got,wanted in [(g,x.geometry_G_U),(beta,x.beta_imbalance),(g+beta,x.B_U),(noise2,x.noise_R2),(noiseinf,x.noise_Rinf),(g+beta+noise2,x.R2),(g+beta+noiseinf,x.Rinf),(est,x.estimate)]:eq(got,wanted)
        rad=g+beta+(noise2 if x.selected_family=='R2' else noiseinf);eq(rad,x.selected_radius)
        for key,d in [('010',.10),('015',.15),('020',.20),('030',.30)]:assert bool(getattr(x,'release_delta_'+key))==(rad<=d)
        assert bool(x.R2_admissible)==(x.policy not in ['fixed_effect','random_effects'])
        computed.append((x.target,x.policy,est,rad))
    sens=read('results/sensitivity.csv');assert len(sens)==918
    indexed=pred.set_index(['target','policy'])
    for x in sens.itertuples():
        base=indexed.loc[(x.target,x.policy)]
        add=x.value if x.sensitivity_kind=='extra_source_bias' else 2*x.value if x.sensitivity_kind=='uniform_source_target_residual_rho' else 0
        mult=math.sqrt(x.value) if x.sensitivity_kind=='noise_variance_factor' else 1
        rad=base.B_U+add+mult*(base.noise_R2 if base.selected_family=='R2' else base.noise_Rinf)
        eq(rad,x.selected_radius);assert bool(x.release_delta_015)==(rad<=.15)
    # Reference outcomes enter only after all frozen source predictions are reconstructed.
    refs=read('results/target_references.csv').set_index('target')
    for site,x in refs.iterrows():
        eq(x.yes1/x.n1-x.yes0/x.n0,x.reference_RD)
        eq(tv(site),x.reference_beta)
        eq(tv(site)+math.sqrt(2*math.log(2*17/.05)) * math.sqrt(.25*(1/x.n1+1/x.n0)),x.reference_radius)
    summary=read('results/policy_comparison.csv').set_index('policy')
    replay=pd.DataFrame(computed,columns=['target','policy','estimate','radius'])
    replay['reference']=replay.target.map(refs.reference_RD)
    for policy,g in replay.groupby('policy'):
        expected=summary.loc[policy]
        eq((g.estimate-g.reference).abs().mean(),expected.reference_MAE)
        eq(2*g.radius.mean(),expected.mean_raw_width)
        assert int((g.radius<=.15).sum())==expected.release_count
    print(json.dumps({'passed':True,'certificate_rows':102,'weights':4080,'sensitivity_rows':918,'targets':17,
                      'maximum_arithmetic_discrepancy':max(residuals),'optimization_rerun':False,
                      'individual_outcomes_opened':False,'scientific_assumptions_validated':False},indent=2))
if __name__=='__main__':main()
