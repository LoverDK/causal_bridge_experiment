"""Deterministic evidence exporter; frozen choices and same MC outcomes.

Does not refit parameters, select designs, or modify primary result files.
The primary per-condition SeedSequence child streams 0 and 1 are replayed.
"""
from __future__ import annotations
import argparse
import itertools
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd
import bernoulli_mc as core


def target_metrics(weight,loss,absolute,coverage):
    """Inputs are weighted numerators; supports exact uniform subset average."""
    denominator=weight.mean()
    n=loss.shape[1]
    if denominator<=0:
        return [dict(valid_rate=0.,mse=np.nan,mse_mc_se=np.nan,mae=np.nan,
                     coverage95_conditional=np.nan,coverage95_unconditional=0.) for _ in range(n)]
    mse=loss.mean(axis=0)/denominator
    influence=(loss-weight[:,None]*mse[None,:])/denominator
    se=influence.std(axis=0,ddof=1)/np.sqrt(len(weight))
    mae=absolute.mean(axis=0)/denominator
    cu=coverage.mean(axis=0)
    cc=cu/denominator
    return [dict(valid_rate=float(denominator),mse=float(mse[j]),mse_mc_se=float(se[j]),mae=float(mae[j]),
                 coverage95_conditional=float(cc[j]),coverage95_unconditional=float(cu[j])) for j in range(n)]


def export(protocol_path,outdir):
    started=time.perf_counter()
    primary_names=['bernoulli_monte_carlo_results.csv','bridge_design_comparison.csv',
                   'gaussian_approximation_results.csv','joint_gaussian_diagnostics.csv','sample_size_scaling.csv',
                   'simulation_cell_counts.csv','source_design_conditioning.csv','source_summary_diagnostics.csv',
                   'monte_carlo_manifest.json']
    before={n:core.sha256(outdir/n) for n in primary_names}
    protocol=json.loads(protocol_path.read_text(encoding='utf-8-sig'))
    manifest=json.loads((outdir/'monte_carlo_manifest.json').read_text(encoding='utf-8'))
    assert core.sha256(protocol_path)==manifest['protocol_sha256']
    assert core.sha256(Path(core.__file__))==manifest['code_sha256']
    compared=pd.read_csv(outdir/'bridge_design_comparison.csv')
    sites=np.asarray(protocol['sites']); targets=np.asarray(protocol['target_indices'])
    sourceids=np.asarray(protocol['source_indices']); candidates=np.asarray(protocol['candidate_indices'])
    site_to_candidate={site:i for i,site in enumerate(sites[candidates])}
    qp=np.asarray(protocol['q_planning'])
    allrows=[]; timings=[]
    def append_rows(condition,noise,budget,policy,estimator,values,available):
        for j,value in enumerate(values):
            allrows.append(dict(scenario=condition['scenario'],dgp=condition['dgp'],scale=condition['scale'],
                                noise_model=noise,budget=budget,policy=policy,estimator=estimator,
                                target_site=sites[targets[j]],available=available,
                                replications=condition['replications'],**value))
    for condition in manifest['condition_runs']:
        t0=time.perf_counter()
        name=condition['scenario']; dgp=condition['dgp']; scale=condition['scale']; reps=condition['replications']
        scenario=next(s for s in protocol['scenarios'] if s['name']==name)
        p=np.asarray(scenario['profile']); counts=np.asarray(scenario['counts_by_scale'][str(scale)],int)
        q=np.asarray(scenario['q_by_dgp'][dgp])
        seed=np.random.SeedSequence(condition['seed_entropy'],spawn_key=tuple(condition['seed_spawn_key']))
        children=seed.spawn(4)
        sim=core.simulate_cells(np.random.default_rng(children[0]),counts,q,p,reps)
        source=core.simulate_source(np.random.default_rng(children[1]),counts,q,sourceids,reps)
        source_truth=core.source_truth_and_working(counts,q,qp,sourceids)
        group=compared[(compared.scenario==name)&(compared.dgp==dgp)&(compared.scale==scale)]
        for noise,noise_group in group.groupby('noise_model',sort=False):
            source_working=source_truth['planning_variance'] if noise=='source_fitted_planning' else source_truth['oracle_variance']
            precision=1/source_working
            V0=np.diag(1/(1+precision))
            targetp=p[targets]; truth=sim['truth'][targets]
            H=(targetp@V0)*precision[None,:]
            postvar=np.einsum('ij,jk,ik->i',targetp,V0,targetp)
            pred=source['z']@H.T
            error=pred-truth
            for estimator,valid in [('strict_finite_logistic_mle',source['strict']),('extended_probability_mle',source['extended'])]:
                values=target_metrics(valid.astype(float),error**2*valid[:,None],
                                      np.abs(error)*valid[:,None],
                                      (np.abs(error)<=core.Z95*np.sqrt(postvar))*valid[:,None])
                append_rows(condition,noise,0,'source_only_no_bridge',estimator,values,True)
            plans=np.sum(p[candidates]**2*np.divide(qp*(1-qp),counts[candidates],
                                                   out=np.zeros_like(counts[candidates],float),
                                                   where=counts[candidates]>0).sum(axis=1),axis=1)
            v=plans if noise=='source_fitted_planning' else sim['oracle'][candidates]
            y=sim['tau'][:,candidates]
            for budget,budget_group in noise_group[noise_group.budget>0].groupby('budget',sort=False):
                budget=int(budget)
                if not bool(budget_group.available.all()):
                    for row in budget_group.itertuples():
                        values=[dict(valid_rate=0.,mse=np.nan,mse_mc_se=np.nan,mae=np.nan,
                                     coverage95_conditional=np.nan,coverage95_unconditional=0.) for _ in targets]
                        append_rows(condition,noise,budget,row.policy,row.estimator,values,False)
                    continue
                selected={}
                for row in budget_group.itertuples():
                    if row.policy=='random_uniform_expectation': continue
                    sub=tuple(sorted(site_to_candidate[n] for n in row.selected_sites.split('|')))
                    selected.setdefault(sub,[]).append((row.policy,row.estimator))
                random_acc={est:dict(weight=np.zeros(reps),loss=np.zeros((reps,17)),
                                     absolute=np.zeros((reps,17)),coverage=np.zeros((reps,17)))
                            for est in ['strict_finite_logistic_mle','extended_probability_mle']}
                combinations=list(itertools.combinations(range(len(candidates)),budget))
                for sub in combinations:
                    ids=np.asarray(sub)
                    x=p[candidates[ids]]
                    V=np.linalg.inv(np.eye(3)+np.diag(precision)+(x.T/v[ids])@x)
                    H=(targetp@V)*precision[None,:]
                    W=(targetp@V)@(x.T/v[ids])
                    pred=source['z']@H.T+y[:,ids]@W.T
                    error=pred-truth
                    loss=error**2; absolute=np.abs(error)
                    postvar=np.einsum('ij,jk,ik->i',targetp,V,targetp)
                    coverage=absolute<=core.Z95*np.sqrt(postvar)
                    for est,valid in [('strict_finite_logistic_mle',source['strict']&sim['strict'][:,candidates[ids]].all(axis=1)),
                                      ('extended_probability_mle',source['extended']&sim['extended'][:,candidates[ids]].all(axis=1))]:
                        a=random_acc[est]
                        weight=valid.astype(float)
                        l=loss*valid[:,None]; ab=absolute*valid[:,None]; co=coverage*valid[:,None]
                        a['weight']+=weight; a['loss']+=l; a['absolute']+=ab;a['coverage']+=co
                        if sub in selected:
                            matches=[policy for policy,estimator in selected[sub] if estimator==est]
                            if matches:
                                values=target_metrics(weight,l,ab,co)
                                for policy in matches:
                                    append_rows(condition,noise,budget,policy,est,values,True)
                for est,a in random_acc.items():
                    count=len(combinations)
                    values=target_metrics(a['weight']/count,a['loss']/count,a['absolute']/count,a['coverage']/count)
                    append_rows(condition,noise,budget,'random_uniform_expectation',est,values,True)
        timings.append(dict(scenario=name,dgp=dgp,scale=scale,elapsed_seconds=time.perf_counter()-t0))
        print(json.dumps({'completed':len(timings),'total':len(manifest['condition_runs']),'seconds':timings[-1]['elapsed_seconds']}),flush=True)
    result=pd.DataFrame(allrows)
    result.to_csv(outdir/'target_level_metrics.csv',index=False)
    keys=['scenario','dgp','scale','noise_model','budget','policy','estimator']
    aggregate=result.groupby(keys,sort=False).agg(target_count=('target_site','size'),
                                                  valid_rate=('valid_rate','mean'),mse=('mse','mean'),
                                                  mae=('mae','mean'),coverage95_conditional=('coverage95_conditional','mean'),
                                                  coverage95_unconditional=('coverage95_unconditional','mean')).reset_index()
    check=aggregate.merge(compared,on=keys,suffixes=('_replay','_primary'),validate='one_to_one')
    differences={}
    for metric in ['valid_rate','mse','mae','coverage95_conditional','coverage95_unconditional']:
        left=check[metric+'_replay'].to_numpy();right=check[metric+'_primary'].to_numpy()
        assert np.array_equal(np.isnan(left),np.isnan(right)),metric+' missingness mismatch'
        differences[metric]=float(np.nanmax(np.abs(left-right)))
        assert np.allclose(left,right,atol=1e-12,rtol=1e-10,equal_nan=True),metric+' replay mismatch'
    assert (aggregate.target_count==17).all() and len(check)==len(compared)
    after={n:core.sha256(outdir/n) for n in primary_names}
    assert before==after,'Primary evidence changed during export'
    output=dict(exporter_sha256=core.sha256(Path(__file__)),primary_hashes=before,
                protocol_sha256=core.sha256(protocol_path),rows=len(result),policy_condition_groups=len(aggregate),
                target_count=17,maximum_absolute_replay_differences=differences,
                elapsed_seconds=time.perf_counter()-started,condition_timings=timings,
                target_metrics_sha256=core.sha256(outdir/'target_level_metrics.csv'),
                provenance='Same recorded primary evaluation seeds; policies read from frozen primary outputs, no selection or refitting')
    (outdir/'target_metrics_export_manifest.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in output.items() if k not in ['primary_hashes','condition_timings']},indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--protocol',required=True,type=Path)
    parser.add_argument('--outdir',required=True,type=Path)
    args=parser.parse_args()
    export(args.protocol,args.outdir)
