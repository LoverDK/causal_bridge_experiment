"""Fixed-budget bridge acquisition after four actual historical observations.

Known prior moments are inputs, not calibrated from the historical outcomes.
The inverse information matrix describes linear mean-square error; under t5
sampling it is not asserted to be a conditional posterior covariance.
"""
from __future__ import annotations
import math
import numpy as np

METHODS=('target_radius','logdet','frozen_random','direct_target')
REFERENCE='direct_reference'

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
    counts=np.atleast_2d(np.asarray(counts,int))
    precision=prior_inverse+np.einsum('bi,ij,ik->bjk',counts/variance,x,x)
    V=np.linalg.inv(precision);u=np.einsum('bij,j->bi',V,target)
    weights=(u@x.T)/variance;residual=(counts*weights)@x-target
    parameter=np.einsum('bi,ij,bj->b',residual,prior,residual)
    noise=(counts*weights**2*variance).sum(axis=1);W=parameter+noise;q=u@target
    if not np.allclose(W,q,rtol=1e-9,atol=1e-12):
        raise AssertionError('Primitive W differs from inverse-information quadratic')
    return [dict(total_counts=c.tolist(),weights=a.tolist(),V=v,W=float(w),q=float(qq),
                 parameter_component=float(p),noise_component=float(n),radius=float(np.sqrt(w/alpha)),
                 width=float(2*np.sqrt(w/alpha)))
            for c,a,v,w,qq,p,n in zip(counts,weights,V,W,q,parameter,noise)]

def history_selection(design,config):
    n=len(design['design']);h=config['history_studies']
    if not 0<h<=n:raise ValueError('History must have distinct archived candidate types')
    rng=np.random.default_rng(np.random.SeedSequence([config['history_selection_seed'],design['replicate']]))
    order=rng.permutation(n)[:h].tolist();counts=np.zeros(n+1,int);counts[order]=1
    return order,counts

def make_plans(design,config):
    """Freeze every acquisition decision using design data, before outcomes."""
    prior,pinv,t,x,var=inputs(design,config);n=len(x)-1
    history_types,history=history_selection(design,config)
    rng=np.random.default_rng(np.random.SeedSequence([config['random_path_seed'],design['replicate']]))
    random_order=rng.permutation(n).tolist();plans={};scores=[]
    for method in (*METHODS,REFERENCE):
        future=np.zeros(n+1,int)
        first=states_for_counts(prior,pinv,t,x,var,history,config['failure_probability'])[0]
        first.update(stage=0,new_observations=0,selected=None,visit=None,future_counts=future.tolist())
        path=[first]
        horizon=config['reference_direct_observations'] if method==REFERENCE else max(config['budgets'])
        for stage in range(1,horizon+1):
            if method in ('direct_target',REFERENCE):
                kind=n;trial=history+future;trial[kind]+=1
                chosen=states_for_counts(prior,pinv,t,x,var,trial,config['failure_probability'])[0]
            else:
                trials=np.tile(history+future,(n,1));trials[np.arange(n),np.arange(n)]+=1
                candidates=states_for_counts(prior,pinv,t,x,var,trials,config['failure_probability'])
                V=path[-1]['V'];gain=[];logdet=[]
                for i,state in enumerate(candidates):
                    denominator=var[i]+float(x[i]@V@x[i])
                    h=float(t@V@x[i])**2/denominator
                    if not np.isclose(path[-1]['W']-state['W'],h,atol=1e-11,rtol=1e-7):
                        raise AssertionError('Actual next W disagrees with rank-one target score')
                    gain.append(h);logdet.append(.5*math.log1p(float(x[i]@V@x[i])/var[i]))
                if method=='target_radius':kind=min(range(n),key=lambda i:(candidates[i]['W'],i))
                elif method=='logdet':kind=min(range(n),key=lambda i:(-logdet[i],i))
                else:kind=random_order[(stage-1)%n]
                chosen=candidates[kind]
                for i,state,h,f in zip(range(n),candidates,gain,logdet):
                    scores.append(dict(design_id=design['replicate'],method=method,stage=stage,candidate=i,
                        selected=i==kind,W_before=path[-1]['W'],W_after=state['W'],target_gain=h,logdet_gain=f))
            visit=int(future[kind]);future[kind]+=1
            chosen.update(stage=stage,new_observations=stage,selected=kind,visit=visit,future_counts=future.tolist())
            path.append(chosen)
        plans[method]=dict(path=path,history_types=history_types,history_counts=history.tolist(),
            horizon=horizon,random_order=random_order if method=='frozen_random' else None)
    return plans,scores

def public_state(state):
    return {k:v for k,v in state.items() if k!='V'}

def ci_sign(lower,upper):
    return 1 if lower>0 else -1 if upper<0 else 0

def estimate_state(state,history_sums,cumulative):
    future_sums=np.array([cumulative[k][c] for k,c in enumerate(state['future_counts'])])
    return float(np.dot(state['weights'],history_sums+future_sums))

def sample_design_worlds(design,config,plans,seed,worlds):
    """Actual independent t5 history/future noise, paired by future type/visit."""
    prior,_,t,x,var=inputs(design,config);did=design['replicate'];p=len(t)
    history_types=plans[METHODS[0]]['history_types'];history_counts=plans[METHODS[0]]['history_counts']
    if config['reference_noise_stream']!='independent_of_all_policy_future_observations':
        raise ValueError('Reference future observations must be independent of policy future observations')
    maximum=np.max([plans[m]['path'][-1]['future_counts'] for m in METHODS],axis=0)
    needed={k:set() for k in range(len(x))}
    for method in METHODS:
        plan=plans[method]
        for budget in config['budgets']:
            for kind,count in enumerate(plan['path'][budget]['future_counts']):
                if count:needed[kind].add(count)
    rows=[];stats=[];histories=[];ledger=[];traces=[]
    for replicate in range(worlds):
        key=[seed,did,replicate]
        beta=np.linalg.cholesky(prior)@standardized_t5(np.random.default_rng(np.random.SeedSequence(key+[100])),p)
        history_sums=np.zeros(len(x))
        for position,kind in enumerate(history_types):
            rng=np.random.default_rng(np.random.SeedSequence(key+[150,kind]))
            y=float(x[kind]@beta+np.sqrt(var[kind])*standardized_t5(rng,1)[0])
            history_sums[kind]=y
            histories.append(dict(design_id=did,replicate=replicate,history_position=position,
                candidate_type=kind,observed_y=y,noise_sd=float(np.sqrt(var[kind]))))
        observations={};cumulative={}
        for kind,count in enumerate(maximum):
            rng=np.random.default_rng(np.random.SeedSequence(key+[200,kind]))
            ys=float(x[kind]@beta)+np.sqrt(var[kind])*standardized_t5(rng,int(count))
            observations[kind]=ys;cumulative[kind]=np.r_[0.,np.cumsum(ys)]
            for count in sorted(needed[kind]):
                stats.append(dict(design_id=did,replicate=replicate,candidate_type=kind,
                    stream='policy_future',future_observations=count,sum_future_y=float(cumulative[kind][count])))
        refcount=config['reference_direct_observations'];direct_kind=len(x)-1
        refrng=np.random.default_rng(np.random.SeedSequence(key+[300,direct_kind]))
        refobservations=float(x[direct_kind]@beta)+np.sqrt(var[direct_kind])*standardized_t5(refrng,refcount)
        refcumulative={k:np.array([0.]) for k in range(len(x))}
        refcumulative[direct_kind]=np.r_[0.,np.cumsum(refobservations)]
        stats.append(dict(design_id=did,replicate=replicate,candidate_type=direct_kind,
            stream='reference_future',future_observations=refcount,sum_future_y=float(refcumulative[direct_kind][-1])))
        truth=float(t@beta)  # Truth is available only to this generator/scorer.
        refstate=plans[REFERENCE]['path'][-1]
        refestimate=estimate_state(refstate,history_sums,refcumulative)
        refradius=refstate['radius'];refsign=ci_sign(refestimate-refradius,refestimate+refradius)
        history_width=plans[METHODS[0]]['path'][0]['width']
        for method,plan in plans.items():
            method_cumulative=refcumulative if method==REFERENCE else cumulative
            stream='reference_future' if method==REFERENCE else 'policy_future'
            budgets=[config['reference_direct_observations']] if method==REFERENCE else config['budgets']
            for budget in budgets:
                state=plan['path'][budget];estimate=estimate_state(state,history_sums,method_cumulative)
                error=estimate-truth;r=state['radius'];lower=estimate-r;upper=estimate+r
                sign=ci_sign(lower,upper);difference=estimate-refestimate
                rows.append(dict(design_id=did,replicate=replicate,method=method,
                    role='reference' if method==REFERENCE else 'fixed_budget_method',new_budget=budget,
                    future_stream=stream,
                    history_observations=len(history_types),total_observations=len(history_types)+budget,
                    estimate=estimate,truth=truth,error=error,absolute_error=abs(error),squared_error=error**2,
                    W=state['W'],q=state['q'],parameter_component=state['parameter_component'],
                    noise_component=state['noise_component'],radius=r,width=state['width'],lower=lower,upper=upper,
                    covered=abs(error)<=r,scientific_error=abs(error)>config['point_difference_threshold'],
                    history_width=history_width,width_ratio_to_history=state['width']/history_width,
                    width_reduction_fraction=1-state['width']/history_width,
                    ci_sign=sign,ci_decisive=sign!=0,ci_direction_wrong=sign!=0 and sign!=int(np.sign(truth)),
                    reference_new_observations=config['reference_direct_observations'],
                    reference_estimate=refestimate,reference_radius=refradius,reference_ci_sign=refsign,
                    point_difference=difference,absolute_point_difference=abs(difference),
                    squared_point_difference=difference**2,
                    within_reference_threshold=abs(difference)<=config['point_difference_threshold'],
                    ci_sign_agreement=sign==refsign,reference_decisive=refsign!=0,
                    both_decisive=sign!=0 and refsign!=0,
                    decisive_same_direction=sign!=0 and refsign!=0 and sign==refsign,
                    decisive_opposite_direction=sign!=0 and refsign!=0 and sign!=refsign))
            if did==config['trace_design_id'] and replicate==config['trace_world']:
                for state in plan['path']:
                    e=estimate_state(state,history_sums,method_cumulative);r=state['radius']
                    traces.append(dict(design_id=did,replicate=replicate,method=method,
                        stage=state['stage'],selected=state['selected'],visit=state['visit'],future_stream=stream,
                        new_observations=state['stage'],history_observations=len(history_types),
                        estimate=e,truth=truth,error=e-truth,lower=e-r,upper=e+r,radius=r,width=2*r,
                        W=state['W'],q=state['q'],parameter_component=state['parameter_component'],
                        noise_component=state['noise_component'],ci_sign=ci_sign(e-r,e+r),
                        reference_estimate=refestimate,point_difference=e-refestimate,
                        weights=state['weights'],total_counts=state['total_counts'],future_counts=state['future_counts']))
                    if state['stage']:
                        kind,visit=state['selected'],state['visit']
                        ledger.append(dict(design_id=did,replicate=replicate,method=method,stage=state['stage'],
                            candidate_type=kind,visit=visit,stream=stream,
                            observed_y=float(refobservations[visit] if method==REFERENCE else observations[kind][visit]),
                            noise_sd=float(np.sqrt(var[kind]))))
    return rows,stats,histories,traces,ledger
