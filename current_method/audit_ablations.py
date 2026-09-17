"""Independent post-run reconstruction of saved weights, intervals and costs."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from atlas_new.workflow import make_world, collect, multipliers

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/ablations_full'


def main():
    manifest=json.loads((OUT/'run_manifest.json').read_text())
    cfg=manifest['config']; worlds={}; observations={}
    for s,surface in enumerate(cfg['surfaces']):
        for g,scenario in enumerate(cfg['scenarios']):
            for r in range(cfg['repetitions_per_cell']):
                key=(surface,scenario,r)
                world=make_world(cfg,s,g,r);worlds[key]=world
                observations[key]={j:collect(world,j,cfg['archive_participants'] if j<4 else cfg['participants_per_bridge'])['effect'] for j in range(10)}
    max_radius_error=max_prediction_error=0.;n=0;lookup={}
    with (OUT/'plans.jsonl').open(encoding='utf-8') as f:
        for line in f:
            p=json.loads(line);key=tuple(p[k] for k in ['surface','scenario','replicate'])
            d=worlds[key]['design'];ids=p['ids'];a=np.array(p['weights'])
            c=d.centers[ids];rad=d.radii[ids];sd=d.noise_sd[ids]
            center=a@c
            # Direct pairwise sum, independent of objective_parts and certificate.
            pair_sum=sum(a[i]*a[j]*(np.linalg.norm(c[i]-c[j])+rad[i]+rad[j])**2
                         for i in range(len(ids)) for j in range(len(ids)) if i!=j)
            bar=d.L*(np.linalg.norm(center-d.target_center)+d.target_radius+a@rad)+d.H/4*pair_sum
            lip=d.L*sum(a[i]*(np.linalg.norm(c[i]-d.target_center)+d.target_radius+rad[i]) for i in range(len(ids)))
            q,_=multipliers(d,p['mode'])
            noise=q*(a@sd if p['mode']=='rinf' else np.sqrt(sum((a*sd)**2)))
            expected={'minimum':min(bar,lip),'barycentric':bar,'lipschitz':lip}[p['bound']]+noise
            estimate=sum(a[i]*observations[key][j] for i,j in enumerate(ids))
            max_radius_error=max(max_radius_error,abs(expected-p['radius']))
            max_prediction_error=max(max_prediction_error,abs(estimate-p['estimate']))
            lookup[key+tuple(p[k] for k in ['schedule','mode','method','stage'])]=(p['radius'],p['estimate'])
            n+=1
    df=pd.read_csv(OUT/'records.csv');keys=['surface','scenario','replicate','schedule','mode','method','tolerance']
    stop_error=0.;expected_cost=True
    for key,g in df.groupby(keys,sort=False):
        g=g.sort_values('budget');tolerance=key[-1];stop=None
        for row in g.itertuples(index=False):
            if stop is None:
                rad,estimate=lookup[key[:-1]+(row.budget,)]
                if rad<=tolerance:
                    stop=row.budget
            else:
                rad,estimate=lookup[key[:-1]+(stop,)]
            stop_error=max(stop_error,abs(rad-row.radius),abs(estimate-row.estimate))
            expected_cost &= row.new_n==(row.budget if stop is None else stop)*cfg['participants_per_bridge']
    old=pd.read_csv(ROOT/'results/workflow_full/workflow_records.csv')
    parity=[]
    for schedule,method in [('random','r2_random'),('nearest','r2_nearest')]:
        current=df[(df.schedule==schedule)&(df['mode']=='r2')&(df.method=='optimized__minimum')]
        ref=old[old.method==method]
        mergekeys=['surface','scenario','replicate','tolerance','budget']
        a=current.set_index(mergekeys).sort_index();b=ref.set_index(mergekeys).sort_index()
        cols=['radius','estimate','new_n','released','bad_release','path_covered']
        pd.testing.assert_frame_equal(a[cols],b[cols],check_exact=False,atol=1e-10,rtol=1e-9)
        parity.append(dict(schedule=schedule,rows=len(a),matched=True))
    assert max_radius_error<1e-9 and max_prediction_error<1e-9 and stop_error<1e-9 and expected_cost
    result=dict(independent_plans_checked=n,max_radius_error=max_radius_error,max_prediction_error=max_prediction_error,
                stopped_records_checked=len(df),max_stopped_reconstruction_error=stop_error,costs_match=bool(expected_cost),
                original_workflow_parity=parity)
    (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # A separate lossless archive stays below the GitHub individual-file limit.
    with (OUT/'plans.jsonl').open('rb') as source, gzip.open(OUT/'plans.jsonl.gz','wb',compresslevel=6) as dest:
        import shutil
        shutil.copyfileobj(source,dest)
    h=hashlib.sha256()
    with gzip.open(OUT/'plans.jsonl.gz','rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    assert h.hexdigest()==manifest['artifacts']['plans.jsonl']['sha256']
    result['compressed_plans_bytes']=(OUT/'plans.jsonl.gz').stat().st_size
    result['lossless_archive_verified']=True
    (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
