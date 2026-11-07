"""Archived-design complete workflow for the non-Gaussian target certificate.

All design decisions precede outcome generation. One observation is one
study-level measurement with the archived sigma, not a participant cohort.
"""
from __future__ import annotations
import math
import numpy as np

METHODS=('target_radius','logdet','frozen_random','direct_target')

def standardized_t5(rng,size):
    return rng.standard_t(5,size=size)*math.sqrt(3/5)

def inputs(design,config):
    prior=np.asarray(design['prior'],float);target=np.asarray(design['target'],float)
    x=np.vstack([np.asarray(design['design'],float),target])
    variance=np.r_[np.asarray(design['sigma'],float)**2,config['direct_noise_sd']**2]
    np.linalg.cholesky(prior)
    if not np.allclose(prior,prior.T,atol=1e-12) or np.any(variance<=0):
        raise ValueError('Invalid archived covariance or noise scales')
    return prior,np.linalg.inv(prior),target,x,variance

def states_for_counts(prior,prior_inverse,target,x,variance,counts,alpha):
    """Batch exact W calculations for arbitrary fixed candidate allocations."""
    counts=np.atleast_2d(np.asarray(counts,int))
    precision=prior_inverse+np.einsum('bi,ij,ik->bjk',counts/variance,x,x)
    V=np.linalg.inv(precision)
    u=np.einsum('bij,j->bi',V,target)
    weights=(u@x.T)/variance
    residual=(counts*weights)@x-target
    parameter=np.einsum('bi,ij,bj->b',residual,prior,residual)
    noise=(counts*weights**2*variance).sum(axis=1)
    W=parameter+noise;q=u@target
    if not np.allclose(W,q,rtol=1e-9,atol=1e-12):
        raise AssertionError('Primitive moment W differs from inverse-design quadratic')
    return [dict(counts=c.tolist(),weights=a.tolist(),V=v,W=float(w),q=float(qq),
                 parameter_component=float(p),noise_component=float(n),radius=float(np.sqrt(w/alpha)),
                 width=float(2*np.sqrt(w/alpha)))
            for c,a,v,w,qq,p,n in zip(counts,weights,V,W,q,parameter,noise)]

def make_plans(design,config):
    prior,pinv,t,x,var=inputs(design,config);n=len(x)-1
    rng=np.random.default_rng(np.random.SeedSequence([config['random_path_seed'],design['replicate']]))
    random_order=rng.permutation(n).tolist()
    plans={};all_scores=[]
    for method in METHODS:
        counts=np.zeros(n+1,int)
        first=states_for_counts(prior,pinv,t,x,var,counts,config['failure_probability'])[0]
        first.update(stage=0,selected=None,visit=None,study_observations=0)
        path=[first]
        for stage in range(1,config['max_study_observations']+1):
            if path[-1]['radius']<=config['scientific_halfwidth']:break
            if method=='direct_target':
                kind=n;trial=counts.copy();trial[kind]+=1
                chosen=states_for_counts(prior,pinv,t,x,var,trial,config['failure_probability'])[0]
            else:
                # By default every type may be selected again as a fresh measurement.
                available=list(range(n))
                no_repeat=config.get('initial_without_replacement',0)
                if stage<=no_repeat: available=[i for i in available if counts[i]==0]
                candidate_counts=np.tile(counts,(len(available),1))
                candidate_counts[np.arange(len(available)),available]+=1
                candidates=states_for_counts(prior,pinv,t,x,var,candidate_counts,config['failure_probability'])
                V=path[-1]['V'];gain=[];logdet=[]
                for i,state in zip(available,candidates):
                    d=var[i]+float(x[i]@V@x[i])
                    h=float(t@V@x[i])**2/d
                    if not np.isclose(path[-1]['W']-state['W'],h,atol=1e-11,rtol=1e-7):
                        raise AssertionError('Actual candidate W disagrees with rank-one target score')
                    gain.append(h);logdet.append(.5*math.log1p(float(x[i]@V@x[i])/var[i]))
                if method=='target_radius':j=min(range(len(available)),key=lambda j:(candidates[j]['W'],available[j]))
                elif method=='logdet':j=min(range(len(available)),key=lambda j:(-logdet[j],available[j]))
                else:
                    expected=random_order[(stage-1)%n]
                    if expected not in available:raise AssertionError('Random path incompatible with replacement rule')
                    j=available.index(expected)
                kind=available[j];chosen=candidates[j]
                for i,state,h,f in zip(available,candidates,gain,logdet):
                    all_scores.append(dict(design_id=design['replicate'],method=method,stage=stage,
                        candidate=i,selected=i==kind,W_before=path[-1]['W'],W_after=state['W'],
                        target_gain=h,logdet_gain=f))
            visit=int(counts[kind]);counts[kind]+=1
            chosen.update(stage=stage,selected=kind,visit=visit,study_observations=stage)
            path.append(chosen)
        attained=path[-1]['radius']<=config['scientific_halfwidth']
        plans[method]=dict(path=path,stop_stage=len(path)-1,attained=attained,
                           random_order=random_order if method=='frozen_random' else None)
    return plans,all_scores

def public_state(state):
    return {k:v for k,v in state.items() if k!='V'}

def sample_design_worlds(design,config,plans,seed,worlds):
    """Draw actual t5 random parameters and independent per-visit t5 errors.

    Same type and visit are paired across policies; no effect is given to the
    precomputed planner. The function returns sufficient statistics to audit
    every endpoint and a complete trace for the preselected world.
    """
    prior,_,t,x,var=inputs(design,config);design_id=design['replicate'];p=len(t)
    maximum=np.max([z['path'][-1]['counts'] for z in plans.values()],axis=0)
    rows=[];stats=[];ledger=[];traces=[]
    for replicate in range(worlds):
        key=[seed,design_id,replicate]
        rng=np.random.default_rng(np.random.SeedSequence(key+[100]))
        beta=np.linalg.cholesky(prior)@standardized_t5(rng,p)
        observations={};cumulative={}
        for kind,count in enumerate(maximum):
            rng=np.random.default_rng(np.random.SeedSequence(key+[200,kind]))
            noise=np.sqrt(var[kind])*standardized_t5(rng,int(count))
            ys=float(x[kind]@beta)+noise
            observations[kind]=ys;cumulative[kind]=np.r_[0.,np.cumsum(ys)]
        truth=float(t@beta)  # scoring only, after all sampling and planning
        for method,plan in plans.items():
            final=plan['path'][-1]
            sums=np.array([cumulative[k][c] for k,c in enumerate(final['counts'])])
            estimate=float(np.dot(final['weights'],sums));error=estimate-truth
            row=dict(design_id=design_id,replicate=replicate,method=method,
                study_observations=plan['stop_stage'],attained=plan['attained'],
                estimate=estimate,truth=truth,error=error,absolute_error=abs(error),squared_error=error**2,
                W=final['W'],q=final['q'],parameter_component=final['parameter_component'],
                noise_component=final['noise_component'],radius=final['radius'],width=final['width'],
                lower=estimate-final['radius'],upper=estimate+final['radius'],covered=abs(error)<=final['radius'],
                interval_miss_on_release=plan['attained'] and abs(error)>final['radius'],
                bad_release_scientific=plan['attained'] and abs(error)>config['scientific_halfwidth'])
            rows.append(row)
            for kind,count in enumerate(final['counts']):
                if count:stats.append(dict(design_id=design_id,replicate=replicate,method=method,
                    candidate_type=kind,observations=count,sum_y=sums[kind],weight_per_observation=final['weights'][kind]))
            if design_id==config['trace_design_id'] and replicate==config['trace_world']:
                for state in plan['path']:
                    ss=np.array([cumulative[k][c] for k,c in enumerate(state['counts'])])
                    e=float(np.dot(state['weights'],ss));r=state['radius']
                    traces.append(dict(design_id=design_id,replicate=replicate,method=method,
                        stage=state['stage'],selected=state['selected'],visit=state['visit'],
                        estimate=e,truth=truth,error=e-truth,lower=e-r,upper=e+r,radius=r,width=2*r,
                        W=state['W'],parameter_component=state['parameter_component'],noise_component=state['noise_component'],
                        released=r<=config['scientific_halfwidth'],weights=state['weights'],counts=state['counts']))
                    if state['stage']:
                        kind,visit=state['selected'],state['visit']
                        ledger.append(dict(design_id=design_id,replicate=replicate,method=method,stage=state['stage'],
                            candidate_type=kind,visit=visit,observed_y=float(observations[kind][visit]),noise_sd=float(np.sqrt(var[kind]))))
    return rows,stats,traces,ledger
