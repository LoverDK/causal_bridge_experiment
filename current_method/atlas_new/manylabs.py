"""Pinned Many Labs 2 framing baseline audit; no calibrated mechanism claims."""
import hashlib
import io
import json
import urllib.parse
import urllib.request
import numpy as np
import pandas as pd
from scipy.stats import norm, t
from .experiments import save

COMMIT='acef63fc397b8dce7f0b00f863bcea78d324bea8'
SHA256='15898b5c241696adc7fd91a638839ba49a9f9be64c78da9151b39018d66bfbd3'
PATH='OSFdata/Framing (Tversky & Kahneman, 1981)/Tversky.1/Global/Data/Tversky_1_study_global_include_all_CLEAN_CASE.csv'
URL=f'https://raw.githubusercontent.com/ManyLabsOpenScience/ManyLabs2/{COMMIT}/'+urllib.parse.quote(PATH)


def fetch(data_dir):
    file=data_dir/'manylabs2_framing.csv'
    raw=file.read_bytes() if file.exists() else urllib.request.urlopen(URL,timeout=45).read()
    actual=hashlib.sha256(raw).hexdigest()
    if actual != SHA256: raise RuntimeError(f'Data checksum mismatch: {actual}')
    if not file.exists(): file.write_bytes(raw)
    (data_dir/'provenance.json').write_text(json.dumps(dict(url=URL,commit=COMMIT,sha256=actual,
        paper_source='Klein et al. (2018); OSF 8cd4r',bytes=len(raw)),indent=2),encoding='utf-8')
    df=pd.read_csv(io.BytesIO(raw))
    df=df[df['case.include'].astype(str).str.lower().eq('true') & df.factor.isin(['Cheap','Expensive'])
          & df.variable.isin(['Yes','No']) & df.source.notna()].copy()
    return df


def summarize(data):
    rows=[]
    for source,g in data.groupby('source',sort=True):
        a=g[g.factor.eq('Cheap')];b=g[g.factor.eq('Expensive')]
        if min(len(a),len(b))<2:continue
        pa=a.variable.eq('Yes').mean();pb=b.variable.eq('Yes').mean()
        rows.append(dict(source=source,n_cheap=len(a),n_expensive=len(b),effect=pa-pb,
            variance=pa*(1-pa)/(len(a)-1)+pb*(1-pb)/(len(b)-1)))
    return pd.DataFrame(rows)


def predict(source_effects,source_variances,target_counts):
    """Only source outcomes and target DESIGN counts accepted by this interface."""
    effects=np.asarray(source_effects,float);v=np.asarray(source_variances,float)
    if len(v)<3 or np.any(v<=0): raise ValueError('Need positive source variances and >=3 sources')
    n1,n0=target_counts
    if min(n1,n0)<2:raise ValueError('Insufficient target design size')
    w=1/v;fe=float(w@effects/w.sum());se2=float(1/w.sum())
    Q=float(np.sum(w*(effects-fe)**2));C=float(w.sum()-(w*w).sum()/w.sum())
    tau2=max(0.,(Q-(len(v)-1))/C);rw=1/(v+tau2);re=float(rw@effects/rw.sum())
    target_v=1/(4*n1)+1/(4*n0)
    return dict(fixed=(fe,float(norm.ppf(.975)*np.sqrt(se2+target_v))),
                random=(re,float(t.ppf(.975,len(v)-2)*np.sqrt(1/rw.sum()+tau2+target_v))),
                diagnostics=dict(Q=Q,I2=max(0.,(Q-(len(v)-1))/Q) if Q>0 else 0.,
                                 tau2=tau2,fixed_mean=fe,random_mean=re,fixed_se=np.sqrt(se2),
                                 random_pi_degrees_of_freedom=len(v)-2))


def run(cfg,out,data_dir):
    data=fetch(data_dir);summary=summarize(data)
    if len(data)!=7228 or len(summary)!=57:raise RuntimeError('Pinned sample count differs from paper')
    save(out,'manylabs_sources',summary);rows=[];leakage=[]
    for _,target in summary.iterrows():
        archive=summary[summary.source.ne(target.source)].copy()
        # Freeze predictions before reference is accessed.
        preds=predict(archive.effect,archive.variance,(target.n_cheap,target.n_expensive))
        for method in ['fixed','random']:
            estimate,rad=preds[method]
            rows.append(dict(source=target.source,method=method,estimate=estimate,radius=rad,width=2*rad,
                target_reference=target.effect,error=abs(estimate-target.effect),
                included=abs(estimate-target.effect)<=rad,released_at_015=rad<=.15,
                source_ids='|'.join(archive.source),n_cheap=target.n_cheap,n_expensive=target.n_expensive))
        # Strong integration test: change raw held-out responses, rebuild summaries, refit.
        changed=data.copy();mask=changed.source.eq(target.source)
        changed.loc[mask,'variable']=np.where(changed.loc[mask,'variable'].eq('Yes'),'No','Yes')
        perturbed=summarize(changed);src=perturbed[perturbed.source.ne(target.source)]
        check=predict(src.effect,src.variance,(target.n_cheap,target.n_expensive))
        difference=max(abs(a-b) for method in ['fixed','random'] for a,b in zip(preds[method],check[method]))
        leakage.append(dict(source=target.source,perturbation='flip_all_target_responses',maximum_prediction_change=difference,
                            no_target_source_in_training=target.source not in set(archive.source)))
        if difference>1e-14:raise RuntimeError('Target-outcome leakage detected')
    df=save(out,'manylabs_holdouts',rows);save(out,'manylabs_leakage_tests',leakage)
    frontier=[];summaries=[]
    for method,g in df.groupby('method'):
        for cutoff in np.r_[np.arange(.05,.505,.005)]:
            chosen=g[g.radius<=cutoff+1e-12]
            frontier.append(dict(method=method,threshold=cutoff,n_released=len(chosen),release_rate=len(chosen)/len(g),
                reference_mae=chosen.error.mean(),reference_inclusion=chosen.included.mean(),mean_width=chosen.width.mean()))
        chosen=g[g.released_at_015]
        summaries.append(dict(method=method,n=len(g),reference_mae=g.error.mean(),included_count=int(g.included.sum()),
            reference_inclusion=g.included.mean(),mean_width=g.width.mean(),n_released_015=len(chosen),
            released_mae_015=chosen.error.mean(),released_inclusion_015=chosen.included.mean(),released_width_015=chosen.width.mean()))
    save(out,'manylabs_frontier',frontier);save(out,'manylabs_summary',summaries)
    diag=predict(summary.effect,summary.variance,(100,100))['diagnostics']
    (out/'manylabs_diagnostics.json').write_text(json.dumps(diag,indent=2),encoding='utf-8')
    return df
