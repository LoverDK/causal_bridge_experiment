"""Post-hoc real-data robustness audit with source/country outcome isolation."""
from pathlib import Path
import hashlib, json, platform, sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from atlas_new.manylabs import fetch, summarize, predict, SHA256

ROOT=Path(__file__).resolve().parent
SEED=2026091607
THRESHOLDS=[.10,.15,.20,.25,.30]

def estimates(archive,counts):
    y=archive.effect.to_numpy(); ordered=np.sort(y); trim=int(.1*len(y))
    model=predict(y,archive.variance,counts)
    point={k:v[0] for k,v in model.items() if k!='diagnostics'}
    point.update(unweighted=float(np.mean(y)),median=float(np.median(y)),
                 trimmed=float(np.mean(ordered[trim:len(y)-trim])))
    return point,{k:model[k][1] for k in ['fixed','random']}

def source_table(raw):
    assert raw.groupby('source').Country.nunique().eq(1).all()
    return summarize(raw).merge(raw.groupby('source').Country.first().rename('country'),on='source',validate='one_to_one')

def run():
    out=ROOT/'results'/'real_supplement'
    if out.exists(): raise FileExistsError('Preserve existing real_supplement; use an explicit new output name for reruns.')
    out.mkdir(parents=True)
    raw=fetch(ROOT/'data'); sources=source_table(raw)
    assert len(raw)==7228 and len(sources)==57 and sources.country.nunique()==26
    sources.to_csv(out/'sources.csv',index=False)
    rows=[]; leakage=[]; matched=[]; rng=np.random.default_rng(SEED)
    for protocol in ['LOSO','LOCO']:
        for target in sources.itertuples(index=False):
            held=sources.source.eq(target.source) if protocol=='LOSO' else sources.country.eq(target.country)
            train=sources.loc[~held].copy(); counts=(target.n_cheap,target.n_expensive)
            point,radii=estimates(train,counts)
            # Integration audit alters every held-out raw response, rebuilds source summaries and refits.
            changed=raw.copy(); mask=changed.source.isin(sources.loc[held,'source'])
            changed.loc[mask,'variable']=np.where(changed.loc[mask,'variable'].eq('Yes'),'No','Yes')
            rebuilt=source_table(changed); rebuilt=rebuilt[rebuilt.source.isin(train.source)]
            pp,rr=estimates(rebuilt,counts)
            difference=max([abs(point[k]-pp[k]) for k in point]+[abs(radii[k]-rr[k]) for k in radii])
            assert difference<1e-14 and not set(train.source)&set(sources.loc[held,'source'])
            leakage.append(dict(protocol=protocol,source=target.source,heldout_sources=int(held.sum()),max_change=difference))
            influence={k:0. for k in point}
            for removed in train.source:
                minus,_=estimates(train[train.source.ne(removed)],counts)
                influence={k:max(influence[k],abs(point[k]-minus[k])) for k in point}
            for method,value in point.items():
                radius=radii.get(method,np.nan); error=abs(value-target.effect)
                rows.append(dict(protocol=protocol,source=target.source,country=target.country,method=method,
                    n_train=len(train),estimate=value,radius=radius,width=2*radius,reference=target.effect,
                    error=error,included=(float(error<=radius) if np.isfinite(radius) else np.nan),
                    max_delete_source_change=influence[method],train_sources='|'.join(train.source)))
            if protocol=='LOCO':
                pool=sources[sources.source.ne(target.source)]
                for rep in range(100):
                    subset=pool.iloc[rng.choice(len(pool),len(train),replace=False)]
                    v=estimates(subset,counts)[0]['fixed']
                    matched.append(dict(source=target.source,country=target.country,rep=rep,n_train=len(train),
                        estimate=v,error=abs(v-target.effect),train_sources='|'.join(subset.source)))
    records=pd.DataFrame(rows); records.to_csv(out/'holdouts.csv',index=False)
    pd.DataFrame(leakage).to_csv(out/'leakage_checks.csv',index=False)
    pd.DataFrame(matched).to_csv(out/'matched_archive_size.csv',index=False)
    summaries=[]; frontiers=[]
    for (protocol,method),g in records.groupby(['protocol','method']):
        country=g.groupby('country').error.mean()
        summaries.append(dict(protocol=protocol,method=method,sites=len(g),countries=len(country),
            site_mae=g.error.mean(),country_mae=country.mean(),max_error=g.error.max(),
            inclusion=g.included.mean(),mean_width=g.width.mean(),
            max_delete_source_change=g.max_delete_source_change.max()))
        if method in ['fixed','random']:
            for delta in THRESHOLDS:
                sel=g[g.radius<=delta]
                frontiers.append(dict(protocol=protocol,method=method,delta=delta,n_released=len(sel),
                    release_rate=len(sel)/len(g),released_mae=sel.error.mean(),
                    released_inclusion=sel.included.mean(),mean_released_width=sel.width.mean()))
    summary=pd.DataFrame(summaries); summary.to_csv(out/'summary.csv',index=False)
    pd.DataFrame(frontiers).to_csv(out/'frontier.csv',index=False)
    fixed=records[records.method.eq('fixed')].pivot(index='source',columns='protocol',values='error')
    fixed['matched_size']=pd.DataFrame(matched).groupby('source').error.mean()
    fixed=fixed.join(sources.set_index('source').country)
    fixed.to_csv(out/'matched_comparison.csv')
    validation=dict(raw_participants=len(raw),sites=len(sources),countries=sources.country.nunique(),
        method_holdouts=len(records),integration_perturbation_checks=len(leakage),
        max_heldout_outcome_effect=max(x['max_change'] for x in leakage),
        all_estimates_finite=bool(np.isfinite(records.estimate).all()),
        no_interval_for_unmodelled_robust_methods=bool(records[~records.method.isin(['fixed','random'])].radius.isna().all()),
        matched_size_repeats=100,seed=SEED)
    assert validation['all_estimates_finite'] and validation['no_interval_for_unmodelled_robust_methods']
    (out/'validation_checks.json').write_text(json.dumps(validation,indent=2),encoding='utf8')
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    inputs=[Path(__file__),ROOT/'atlas_new/manylabs.py',ROOT/'docs/真实数据补充协议.md',ROOT/'data/manylabs2_framing.csv']
    manifest=dict(completed_utc=datetime.now(timezone.utc).isoformat(),python=sys.version,platform=platform.platform(),
        data_sha256=SHA256,seed=SEED,thresholds=THRESHOLDS,
        inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()},status='complete',
        scope='Post-hoc noisy-reference benchmark; no real calibrated mechanism sets or new intervention acquisition')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(summary.to_string(index=False)); print('\nMatched means:',fixed[['LOSO','LOCO','matched_size']].mean().to_dict())
    print(json.dumps(validation))

if __name__=='__main__':run()
