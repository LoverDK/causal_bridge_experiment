"""Frozen-design binomial Monte Carlo. Never reads target outcomes.

The saturated-cell probability MLE is computed analytically. Finite logistic
coefficient existence and extended probability-MLE existence are distinct.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy import stats

Z90 = stats.norm.ppf(.95)
Z95 = stats.norm.ppf(.975)
QUANTILES = np.array([.025,.05,.25,.5,.75,.95,.975])


def hamilton(values: np.ndarray, total: int) -> np.ndarray:
    """Largest remainders; equal remainders resolve by category order."""
    a = np.floor(values).astype(int)
    remaining = int(total - a.sum())
    order = np.lexsort((np.arange(len(a)), -(values-a)))
    a[order[:remaining]] += 1
    assert a.sum() == total and np.all(a >= 0)
    return a


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scalar_posterior(x, v, m0, V0, subset):
    """Fixed-noise scalar Gaussian update, with affine data weights."""
    ids = np.asarray(subset, int)
    if not len(ids):
        return m0.copy(), V0.copy(), np.zeros((3, len(x)))
    xs = x[ids]
    precision = np.linalg.inv(V0) + (xs.T / v[ids]) @ xs
    V = np.linalg.inv(precision)
    W = np.zeros((3, len(x)))
    W[:, ids] = V @ (xs.T / v[ids])
    intercept = V @ np.linalg.solve(V0, m0)
    return intercept, V, W


def loggain(x, v, V0, subset):
    _, V, _ = scalar_posterior(x, v, np.zeros(3), V0, subset)
    return .5*(np.linalg.slogdet(V0)[1]-np.linalg.slogdet(V)[1])


def normal_decoder_metrics(bias,sampling_variance,posterior_variance):
    sd=np.sqrt(sampling_variance)
    standardized=np.divide(bias,sd,out=np.zeros_like(bias),where=sd>0)
    mae=sd*np.sqrt(2/np.pi)*np.exp(-.5*standardized**2)+bias*(2*stats.norm.cdf(standardized)-1)
    width=Z95*np.sqrt(posterior_variance)
    coverage=stats.norm.cdf((width-bias)/sd)-stats.norm.cdf((-width-bias)/sd)
    return dict(gaussian_matched_mae=float(mae.mean()),gaussian_matched_coverage95=float(coverage.mean()),
                mean_sampling_variance=float(sampling_variance.mean()),mean_working_posterior_variance=float(posterior_variance.mean()),
                mean_absolute_decoder_bias=float(np.abs(bias).mean()))


def design_library(x, v, source_working_variance, source_truth, targets, truth_bridge, truth_target, actual_v,costs):
    """All combinations, and policies frozen without simulated observations."""
    if not np.all(np.isfinite(v)&(v>0)) or not np.all(np.isfinite(actual_v)&(actual_v>0)):
        raise ValueError('Candidate menu contains an unidentified or zero-variance design; no silent NaN argmin permitted.')
    source_precision=1/source_working_variance
    V0=np.diag(1/(1+source_precision))
    m0=np.zeros(3)
    library = {}
    for budget in [1, 2, 4]:
        combos = list(itertools.combinations(range(len(x)), budget))
        records, intercepts, weights, variances, source_weights = [], [], [], [], []
        for sub in combos:
            a, V, W = scalar_posterior(x, v, m0, V0, sub)
            a_t, W_t = targets @ a, targets @ W
            H_source=(targets@V)*source_precision[None,:]
            mean = H_source@source_truth['mean'] + W_t @ truth_bridge
            sampling_var=(W_t**2)@actual_v+(H_source**2)@source_truth['variance']
            risk = np.mean((mean-truth_target)**2 + sampling_var)
            postvar=np.einsum('ij,jk,ik->i',targets,V,targets)
            records.append(dict(subset=sub, information_gain=loggain(x,v,V0,sub),
                                target_variance=np.mean(postvar),exact_bernoulli_mse=risk,
                                posterior_condition_number=float(np.linalg.cond(V)),
                                posterior_minimum_eigenvalue=float(np.linalg.eigvalsh(V).min()),
                                posterior_logdet=float(np.linalg.slogdet(V)[1]),
                                participant_cost=int(costs[list(sub)].sum()),
                                **normal_decoder_metrics(mean-truth_target,sampling_var,postvar)))
            intercepts.append(a_t)
            weights.append(W_t)
            source_weights.append(H_source)
            variances.append(postvar)
        gains = np.array([r['information_gain'] for r in records])
        risks = np.array([r['exact_bernoulli_mse'] for r in records])
        loggreedy, tvgreedy = [], []
        for j in range(budget):
            left = [k for k in range(len(x)) if k not in loggreedy]
            values = [loggain(x,v,V0,loggreedy+[k]) for k in left]
            loggreedy.append(left[int(np.argmax(values))])
            left = [k for k in range(len(x)) if k not in tvgreedy]
            values = []
            for k in left:
                _,V,_=scalar_posterior(x,v,m0,V0,tvgreedy+[k])
                values.append(np.mean(np.einsum('ij,jk,ik->i',targets,V,targets)))
            tvgreedy.append(left[int(np.argmin(values))])
        # Nearness uses only target/profile Euclidean geometry, and creates a
        # nested fixed menu with mean squared distance to the nearest bridge.
        near=[]
        dist=((targets[:,None,:]-x[None,:,:])**2).sum(axis=2)
        for j in range(budget):
            left=[k for k in range(len(x)) if k not in near]
            vals=[np.mean(dist[:,near+[k]].min(axis=1)) for k in left]
            near.append(left[int(np.argmin(vals))])
        idx={tuple(r['subset']):j for j,r in enumerate(records)}
        policies={
            'logdet_greedy':idx[tuple(sorted(loggreedy))],
            'logdet_exhaustive':int(np.argmax(gains)),
            'target_variance_greedy':idx[tuple(sorted(tvgreedy))],
            'nearest_profile':idx[tuple(sorted(near))],
            'bernoulli_exhaustive_oracle':int(np.argmin(risks)),
        }
        library[budget]=dict(records=records,intercept=np.array(intercepts),
                             weights=np.array(weights),variances=np.array(variances),
                             source_weights=np.array(source_weights),
                             V0=V0,source_working_variance=source_working_variance,
                             policies=policies)
    return library


def source_truth_and_working(counts,q,qp,source_indices):
    """Pooled independent-cell summary, retaining every source site."""
    n=counts[source_indices]
    qs=q[source_indices]
    totals=n.sum(axis=0)
    if np.any(totals<=0):
        raise ValueError('Pooled source category-arm is empty; no source Gaussian summary identified.')
    meanq=(n*qs).sum(axis=0)/totals
    truev=(n*qs*(1-qs)).sum(axis=0)/(totals**2)
    plan=qp*(1-qp)/totals
    return dict(mean=meanq[1]-meanq[0],variance=truev.sum(axis=0),
                planning_variance=plan.sum(axis=0),oracle_variance=truev.sum(axis=0),
                totals=totals,mean_q=meanq)


def simulate_source(rng,counts,q,source_indices,reps):
    n=counts[source_indices]
    totals=n.sum(axis=0)
    draws=rng.binomial(n[None],q[source_indices][None],size=(reps,)+n.shape)
    pooled=draws.sum(axis=1)
    qhat=pooled/totals[None]
    finite=((pooled>0)&(pooled<totals[None])).all(axis=(1,2))
    return dict(z=qhat[:,1]-qhat[:,0],strict=finite,extended=np.ones(reps,bool),
                source_total_n=int(n.sum()),pooled_totals=totals)


def safe_moments(a):
    a=np.asarray(a,float)
    a=a[np.isfinite(a)]
    if len(a)<2:
        return dict(n=len(a),mean=np.nan,variance=np.nan,skewness=np.nan,excess_kurtosis=np.nan,
                    qq_max_abs=np.nan,ks_distance=np.nan,q025=np.nan,q975=np.nan)
    quant=np.quantile(a,QUANTILES)
    return dict(n=len(a),mean=float(a.mean()),variance=float(a.var(ddof=1)),
                skewness=float(stats.skew(a,bias=False)),excess_kurtosis=float(stats.kurtosis(a,bias=False)),
                qq_max_abs=float(np.max(np.abs(quant-stats.norm.ppf(QUANTILES)))),
                ks_distance=float(stats.kstest(a,'norm').statistic),q025=float(np.quantile(a,.025)),
                q975=float(np.quantile(a,.975)))


def simulate_cells(rng, counts, q, p, reps):
    """counts [S,2,3]; q [S,2,3]; p [S,3]."""
    draws=rng.binomial(counts[None,:,:,:],q[None,:,:,:],size=(reps,)+counts.shape)
    qhat=np.divide(draws,counts[None,:,:,:],out=np.zeros(draws.shape,float),where=counts[None,:,:,:]>0)
    required=p>0
    empty=(counts==0)&required[:,None,:]
    identified=~empty.any(axis=(1,2))
    # A nonexistent irrelevant cell is not fitted; any observed cell must have
    # interior response probability for all finite saturated coefficients.
    boundary=((draws==0)|(draws==counts[None,:,:,:]))&(counts[None,:,:,:]>0)&required[None,:,None,:]
    strict=(~boundary.any(axis=(2,3)))&identified[None,:]
    extended=np.broadcast_to(identified,(reps,len(p))).copy()
    tau=np.sum(p[None,:,:]*(qhat[:,:,1,:]-qhat[:,:,0,:]),axis=2)
    plug_terms=np.divide(qhat*(1-qhat),counts[None,:,:,:],out=np.zeros(qhat.shape),where=counts[None,:,:,:]>0)
    plug=np.sum(p[None,:,:]**2 * plug_terms.sum(axis=2),axis=2)
    oracle_terms=np.divide(q*(1-q),counts,out=np.zeros(q.shape),where=counts>0)
    oracle=np.sum(p**2*oracle_terms.sum(axis=1),axis=1)
    truth=np.sum(p*(q[:,1,:]-q[:,0,:]),axis=1)
    tau[:,~identified]=np.nan
    plug[:,~identified]=np.nan
    oracle[~identified]=np.nan
    return dict(draws=draws,tau=tau,plug=plug,oracle=oracle,truth=truth,
                strict=strict,extended=extended,empty=empty,boundary=boundary,
                identified=identified,qhat=qhat)


def site_diagnostics(sim, sites, roles, scenario, dgp, scale, counts, p):
    rows=[]
    reps=len(sim['tau'])
    for j,site in enumerate(sites):
        error=sim['tau'][:,j]-sim['truth'][j]
        empirical=np.nanvar(error,ddof=1) if sim['identified'][j] else np.nan
        for estimator in ['strict_finite_logistic_mle','extended_probability_mle']:
            ok=sim['strict'][:,j] if estimator.startswith('strict') else sim['extended'][:,j]
            for variance in ['oracle','plugin']:
                v=np.full(reps,sim['oracle'][j]) if variance=='oracle' else sim['plug'][:,j]
                se=np.sqrt(v)
                valid=ok&np.isfinite(se)&(se>0)
                z=np.divide(error,se,out=np.full(reps,np.nan),where=valid)
                moment=safe_moments(z)
                covered90=valid&(np.abs(error)<=Z90*se)
                covered95=valid&(np.abs(error)<=Z95*se)
                r=dict(scenario=scenario,dgp=dgp,scale=scale,site=site,role=roles[j],
                       estimator=estimator,variance=variance,replications=reps,n=int(counts[j].sum()),
                       male_profile=p[j,0],female_profile=p[j,1],other_profile=p[j,2],
                       minimum_required_cell=int(counts[j][np.broadcast_to(p[j]>0,(2,3))].min()),
                       required_empty_cells=int(sim['empty'][j].sum()),identified=bool(sim['identified'][j]),
                       finite_beta_rate=float(sim['strict'][:,j].mean()),
                       separation_rate=float(sim['boundary'][:,j].any(axis=(1,2)).mean()),
                       extended_probability_mle_rate=float(sim['extended'][:,j].mean()),
                       optimizer_nonconvergence_rate=0.0,optimizer_note='analytic cell MLE; no iterative optimizer',
                       invalid_se_rate=float((ok&~valid).mean()),valid_rate=float(valid.mean()),
                       bias=float(error[ok].mean()) if ok.any() else np.nan,
                       empirical_variance=empirical,empirical_variance_scope='unconditional extended MLE (when identified)',
                       conditional_empirical_variance=float(error[ok].var(ddof=1)) if ok.sum()>1 else np.nan,
                       mean_delta_variance=float(v[ok].mean()) if ok.any() else np.nan,
                       empirical_to_delta_variance_ratio=float(empirical/v[ok].mean()) if ok.any() and v[ok].mean()>0 else np.nan,
                       variance_ratio_scope='unconditional extended empirical / estimator-valid mean delta',
                       conditional_empirical_to_delta_variance_ratio=float(error[ok].var(ddof=1)/v[ok].mean()) if ok.sum()>1 and v[ok].mean()>0 else np.nan,
                       coverage90_unconditional=float(covered90.mean()),coverage95_unconditional=float(covered95.mean()),
                       coverage90_conditional=float(covered90[valid].mean()) if valid.any() else np.nan,
                       coverage95_conditional=float(covered95[valid].mean()) if valid.any() else np.nan,
                       truth=sim['truth'][j])
                r.update({'z_'+k:v for k,v in moment.items()})
                # Frozen per-site adequacy; failures count against adequacy.
                r['finite_logistic_gate']=bool(r['finite_beta_rate']>=.99)
                r['adequate']=bool(r['valid_rate']>=.99 and .935<=r['coverage95_unconditional']<=.965
                                   and .885<=r['coverage90_unconditional']<=.915
                                   and .9<=r['empirical_to_delta_variance_ratio']<=1.1
                                   and abs(r['z_mean'])<=.1 and abs(r['z_skewness'])<=.3
                                   and abs(r['z_excess_kurtosis'])<=.5 and r['z_qq_max_abs']<=.2)
                r['adequacy_scope']='functional extended probability MLE' if estimator.startswith('extended') else 'strict finite logistic MLE including validity gate'
                rows.append(r)
    return rows


def joint_diagnostics(sim, candidates, scenario,dgp,scale):
    out=[]
    for estimator in ['strict_finite_logistic_mle','extended_probability_mle']:
        ok=(sim['strict'] if estimator.startswith('strict') else sim['extended'])[:,candidates].all(axis=1)
        for variance in ['oracle','plugin']:
            err=sim['tau'][:,candidates]-sim['truth'][candidates]
            v=np.broadcast_to(sim['oracle'][candidates],err.shape) if variance=='oracle' else sim['plug'][:,candidates]
            okv=ok&(np.isfinite(v)&(v>0)).all(axis=1)
            zz=err[okv]/np.sqrt(v[okv])
            if len(zz)>2:
                cov=np.cov(zz,rowvar=False)
                off=cov-np.diag(np.diag(cov))
                radial=(zz**2).sum(axis=1)
                cov95=float((radial<=stats.chi2.ppf(.95,len(candidates))).mean())
                rectangle_threshold=stats.norm.ppf((1+.95**(1/len(candidates)))/2)
                rectangle95=float((np.max(np.abs(zz),axis=1)<=rectangle_threshold).mean())
                maxcorr=float(np.max(np.abs(off)))
                cor=np.corrcoef(zz,rowvar=False)
                maxcorrelation=float(np.max(np.abs(cor-np.diag(np.diag(cor)))))
                radial_ks=float(stats.kstest(radial,'chi2',args=(len(candidates),)).statistic)
            else: cov95=maxcorr=maxcorrelation=radial_ks=rectangle95=np.nan
            out.append(dict(scenario=scenario,dgp=dgp,scale=scale,estimator=estimator,variance=variance,
                            candidate_count=len(candidates),joint_valid_rate=float(okv.mean()),
                            chi2_95_coverage_conditional=cov95,
                            chi2_95_coverage_unconditional=float(okv.mean())*cov95 if np.isfinite(cov95) else 0.,
                            rectangle_95_coverage_conditional=rectangle95,
                            rectangle_95_coverage_unconditional=float(okv.mean())*rectangle95 if np.isfinite(rectangle95) else 0.,
                            max_absolute_offdiagonal_covariance=maxcorr,
                            max_absolute_offdiagonal_correlation=maxcorrelation,radial_chi2_ks=radial_ks,
                            adequate=bool(okv.mean()>=.99 and np.isfinite(rectangle95)
                                          and abs(okv.mean()*rectangle95-.95)<=.02 and maxcorrelation<=.05)))
    return out


def weighted_metrics(weight,weighted_loss,weighted_absolute,weighted_coverage):
    denominator=weight.mean()
    if denominator<=0:
        return dict(valid_rate=0.,mse=np.nan,mse_mc_se=np.nan,mae=np.nan,
                    coverage95_conditional=np.nan,coverage95_unconditional=0.)
    mse=weighted_loss.mean()/denominator
    influence=(weighted_loss-mse*weight)/denominator
    return dict(valid_rate=float(denominator),mse=float(mse),
                mse_mc_se=float(influence.std(ddof=1)/np.sqrt(len(weight))),
                mae=float(weighted_absolute.mean()/denominator),
                coverage95_conditional=float(weighted_coverage.mean()/denominator),
                coverage95_unconditional=float(weighted_coverage.mean()))


def evaluate_designs(sim,source,pilot_sim,pilot_source,candidates,target_p,target_truth,library,
                     site_names,scenario,dgp,scale,noise_model):
    """All-subset evaluation; MC oracle trained on independent pilot draws."""
    comparisons=[]; exhaustive=[]
    y=sim['tau'][:,candidates]
    py=pilot_sim['tau'][:,candidates]
    reps=len(y)
    for budget,lib in library.items():
        records=lib['records']; W=lib['weights']; H=lib['source_weights']; vv=lib['variances']
        count=len(records)
        loss=np.zeros((count,reps)); absolute=np.zeros_like(loss); cover=np.zeros_like(loss)
        strict=np.zeros((count,reps),bool); extended=np.zeros((count,reps),bool)
        training_risk=np.zeros(count)
        for k,rec in enumerate(records):
            sub=list(rec['subset'])
            pred=source['z']@H[k].T + y[:,sub]@W[k,:,sub]
            error=pred-target_truth
            loss[k]=(error**2).mean(axis=1)
            absolute[k]=np.abs(error).mean(axis=1)
            cover[k]=(np.abs(error)<=Z95*np.sqrt(vv[k])).mean(axis=1)
            strict[k]=source['strict']&sim['strict'][:,np.asarray(candidates)[sub]].all(axis=1)
            extended[k]=source['extended']&sim['extended'][:,np.asarray(candidates)[sub]].all(axis=1)
            train_pred=pilot_source['z']@H[k].T + py[:,sub]@W[k,:,sub]
            training_risk[k]=((train_pred-target_truth)**2).mean()
            estmetrics={}
            for est,ok in [('strict_finite_logistic_mle',strict[k]),('extended_probability_mle',extended[k])]:
                estmetrics[est]=weighted_metrics(ok.astype(float),loss[k]*ok,absolute[k]*ok,cover[k]*ok)
            exhaustive.append(dict(scenario=scenario,dgp=dgp,scale=scale,noise_model=noise_model,budget=budget,
                                   subset='|'.join(site_names[np.asarray(candidates)[sub]]),
                                   **{a:b for a,b in rec.items() if a!='subset'},
                                   pilot_mc_mse=training_risk[k],pilot_replications=len(py),
                                   extended_mc_mse=estmetrics['extended_probability_mle']['mse'],
                                   extended_mc_mse_se=estmetrics['extended_probability_mle']['mse_mc_se'],
                                   strict_mc_mse=estmetrics['strict_finite_logistic_mle']['mse'],
                                   strict_valid_rate=estmetrics['strict_finite_logistic_mle']['valid_rate']))
        policies=dict(lib['policies'])
        policies['bernoulli_mc_exhaustive_oracle']=int(np.argmin(training_risk))
        exact_best=policies['bernoulli_exhaustive_oracle']
        mc_best=policies['bernoulli_mc_exhaustive_oracle']
        logopt=policies['logdet_exhaustive']
        greedy=policies['logdet_greedy']
        kappa_max=max(r['posterior_condition_number'] for r in records)
        greedy_factor=1-(1-1/budget)**budget
        bound_logdet=(1-greedy_factor)*np.linalg.slogdet(lib['V0'])[1]+greedy_factor*records[logopt]['posterior_logdet']
        radius_bound=Z95*np.linalg.norm(target_p,axis=1)*np.sqrt(kappa_max)*np.exp(bound_logdet/6)
        greedy_actual_radius=Z95*np.sqrt(vv[greedy])
        for policy,k in list(policies.items())+[('random_uniform_expectation',None)]:
            rec=records[k] if k is not None else None
            exact=rec['exact_bernoulli_mse'] if rec else np.mean([r['exact_bernoulli_mse'] for r in records])
            info=rec['information_gain'] if rec else np.mean([r['information_gain'] for r in records])
            gaussian={key:(rec[key] if rec else np.mean([r[key] for r in records]))
                      for key in ['gaussian_matched_mae','gaussian_matched_coverage95','mean_sampling_variance',
                                  'mean_working_posterior_variance','mean_absolute_decoder_bias',
                                  'posterior_condition_number','participant_cost']}
            for est,validity in [('strict_finite_logistic_mle',strict),('extended_probability_mle',extended)]:
                if k is None:
                    weight=validity.mean(axis=0)
                    weighted_loss=(loss*validity).mean(axis=0)
                    weighted_abs=(absolute*validity).mean(axis=0)
                    weighted_cov=(cover*validity).mean(axis=0)
                    paired_validity=validity&validity[mc_best][None]
                    paired_weight=paired_validity.mean(axis=0)
                    paired_weighted_difference=((loss-loss[mc_best][None])*paired_validity).mean(axis=0)
                else:
                    weight=validity[k].astype(float)
                    weighted_loss=loss[k]*weight;weighted_abs=absolute[k]*weight;weighted_cov=cover[k]*weight
                    paired_weight=(validity[k]&validity[mc_best]).astype(float)
                    paired_weighted_difference=(loss[k]-loss[mc_best])*paired_weight
                mt=weighted_metrics(weight,weighted_loss,weighted_abs,weighted_cov)
                paired_denominator=paired_weight.mean()
                if paired_denominator>0:
                    regret=paired_weighted_difference.mean()/paired_denominator
                    influence=(paired_weighted_difference-regret*paired_weight)/paired_denominator
                    regretse=influence.std(ddof=1)/np.sqrt(reps)
                else: regret=regretse=np.nan
                comparisons.append(dict(scenario=scenario,dgp=dgp,scale=scale,noise_model=noise_model,budget=budget,
                                         policy=policy,estimator=est,replications=reps,
                                         selected_sites='|'.join(site_names[np.asarray(candidates)[list(rec['subset'])]]) if rec else 'exact uniform subset expectation',
                                         **mt,exact_bernoulli_mse=exact,
                                         **gaussian,
                                         mc_mse_minus_exact=mt['mse']-exact,
                                         mc_mae_minus_gaussian=mt['mae']-gaussian['gaussian_matched_mae'],
                                         mc_coverage95_minus_gaussian=mt['coverage95_unconditional']-gaussian['gaussian_matched_coverage95'],
                                         empirical_error_scope='conditional on estimator availability; consult valid_rate',
                                         exact_bernoulli_risk_scope='unconditional extended-probability decoder, including repeated source',
                                         exact_mse_regret=exact-records[exact_best]['exact_bernoulli_mse'],
                                         relative_exact_mse_regret=exact/records[exact_best]['exact_bernoulli_mse']-1,
                                         paired_mc_mse_regret=float(regret),paired_mc_mse_regret_se=float(regretse),
                                         paired_valid_rate=float(paired_denominator),
                                         paired_regret_reference='independent-pilot-selected MC exhaustive oracle; fresh evaluation draws',
                                         oracle_pilot_replications=len(py),
                                         oracle_pilot_minimum_mse=float(training_risk[mc_best]),
                                         information_gain=info,information_gain_ratio=info/records[logopt]['information_gain'],
                                         cardinality_greedy_factor=greedy_factor,
                                         logdet_greedy_guarantee_verified=bool(records[greedy]['information_gain']+1e-12>=greedy_factor*records[logopt]['information_gain']),
                                         posterior_kappa_max_all_subsets=kappa_max,
                                         corollary_greedy_mean_radius_bound=float(radius_bound.mean()),
                                         greedy_mean_actual_radius=float(greedy_actual_radius.mean()),
                                         corollary_bound_to_actual_radius=float(radius_bound.mean()/greedy_actual_radius.mean()),
                                         agrees_logdet_exhaustive=bool(k==logopt) if k is not None else np.nan,
                                         agrees_bernoulli_oracle=bool(k==exact_best) if k is not None else np.nan,
                                         agrees_mc_oracle=bool(k==mc_best) if k is not None else np.nan,
                                         interval_note='Working Gaussian posterior intervals; repeated-source and independent-bridge frequentist coverage'))
    return comparisons,exhaustive


def source_only_comparisons(source,source_truth,source_working,target_p,target_truth,scenario,dgp,scale,noise_model):
    precision=1/source_working
    V0=np.diag(1/(1+precision))
    H=(target_p@V0)*precision[None,:]
    prediction=source['z']@H.T
    error=prediction-target_truth
    loss=(error**2).mean(axis=1)
    absolute=np.abs(error).mean(axis=1)
    postvar=np.einsum('ij,jk,ik->i',target_p,V0,target_p)
    coverage=(np.abs(error)<=Z95*np.sqrt(postvar)).mean(axis=1)
    mean=H@source_truth['mean']
    samplingvar=(H**2)@source_truth['variance']
    exact=float(np.mean((mean-target_truth)**2+samplingvar))
    normal=normal_decoder_metrics(mean-target_truth,samplingvar,postvar)
    result=[]
    for estimator,valid in [('strict_finite_logistic_mle',source['strict']),('extended_probability_mle',source['extended'])]:
        weight=valid.astype(float)
        metrics=weighted_metrics(weight,loss*weight,absolute*weight,coverage*weight)
        result.append(dict(scenario=scenario,dgp=dgp,scale=scale,noise_model=noise_model,budget=0,
                           policy='source_only_no_bridge',estimator=estimator,replications=len(loss),
                           selected_sites='',available=True,**metrics,exact_bernoulli_mse=exact,**normal,
                           mc_mse_minus_exact=metrics['mse']-exact,
                           mc_mae_minus_gaussian=metrics['mae']-normal['gaussian_matched_mae'],
                           mc_coverage95_minus_gaussian=metrics['coverage95_unconditional']-normal['gaussian_matched_coverage95'],
                           participant_cost=0,information_gain=0,
                           posterior_condition_number=float(np.linalg.cond(V0)),
                           interval_note='Working Gaussian source-only posterior interval; repeated source frequentist coverage'))
    return result


def run_protocol(protocol_path: Path, outdir: Path, pilot=False):
    protocol=json.loads(protocol_path.read_text(encoding='utf-8-sig'))
    outdir.mkdir(parents=True,exist_ok=True)
    sites=np.asarray(protocol['sites'])
    roles=protocol['roles']
    candidates=np.asarray(protocol['candidate_indices'],int)
    targets=np.asarray(protocol['target_indices'],int)
    source_indices=np.asarray(protocol['source_indices'],int)
    qp=np.asarray(protocol['q_planning'],float)
    assert len(sites)==57 and len(set(sites))==57
    assert len(targets)==17 and len(candidates)==12
    assert len(set(candidates))==12
    assert len(source_indices)==40 and len(set(source_indices)&set(targets))==0
    assert np.all((qp>0)&(qp<1))
    scenarios=protocol['scenarios'][:1] if pilot else protocol['scenarios']
    scales=protocol['scales'][:1] if pilot else protocol['scales']
    rows=[]; comparisons=[]; exhaustive=[]; joint=[]; elapsed=[]; schedules=[]; source_rows=[]; geometry=[]
    start=time.perf_counter()
    sequence=np.random.SeedSequence(protocol['seed'])
    children=sequence.spawn(sum(len(s['q_by_dgp'])*len(s.get('scales',scales)) for s in scenarios))
    condition=0
    for scenario in scenarios:
        p=np.asarray(scenario['profile'],float)
        assert p.shape==(57,3) and np.allclose(p.sum(axis=1),1)
        assert np.all(p>=0)
        reps=protocol['replications_main'] if scenario.get('main',False) else protocol['replications_sensitivity']
        if pilot: reps=min(reps,200)
        oracle_pilot_reps=min(protocol['replications_oracle_pilot'],200) if pilot else protocol['replications_oracle_pilot']
        for dgp,qvalues in scenario['q_by_dgp'].items():
            q=np.asarray(qvalues,float)
            assert q.shape==(57,2,3) and np.all((q>0)&(q<1))
            for scale in (scales if pilot else scenario.get('scales',scales)):
                t0=time.perf_counter()
                seedseq=children[condition]
                simulation_seeds=seedseq.spawn(4)
                condition+=1
                counts=np.asarray(scenario['counts_by_scale'][str(scale)],int)
                assert counts.shape==(57,2,3) and np.all(counts>=0)
                sim=simulate_cells(np.random.default_rng(simulation_seeds[0]),counts,q,p,reps)
                source=simulate_source(np.random.default_rng(simulation_seeds[1]),counts,q,source_indices,reps)
                pilot_sim=simulate_cells(np.random.default_rng(simulation_seeds[2]),counts,q,p,oracle_pilot_reps)
                pilot_source=simulate_source(np.random.default_rng(simulation_seeds[3]),counts,q,source_indices,oracle_pilot_reps)
                source_truth=source_truth_and_working(counts,q,qp,source_indices)
                singular=np.linalg.svd(p[source_indices],compute_uv=False)
                for noise_model in ['source_fitted_planning','oracle']:
                    source_working=source_truth['planning_variance'] if noise_model=='source_fitted_planning' else source_truth['oracle_variance']
                    V0=np.diag(1/(1+1/source_working))
                    geometry.append(dict(scenario=scenario['name'],dgp=dgp,scale=scale,noise_model=noise_model,
                                         source_profile_rank=int(np.linalg.matrix_rank(p[source_indices])),
                                         source_profile_singular_values='|'.join(map(str,singular)),
                                         source_profile_condition_number=float(np.linalg.cond(p[source_indices])),
                                         scalar_source_identity_design_rank=3,
                                         V0_eigenvalues='|'.join(map(str,np.linalg.eigvalsh(V0))),
                                         V0_condition_number=float(np.linalg.cond(V0)),
                                         source_participants=source['source_total_n']))
                    comparisons.extend(source_only_comparisons(source,source_truth,source_working,p[targets],
                                                               sim['truth'][targets],scenario['name'],dgp,scale,noise_model))
                for cat in range(3):
                    source_rows.append(dict(scenario=scenario['name'],dgp=dgp,scale=scale,category=cat+1,
                                            n_t0=int(source_truth['totals'][0,cat]),n_t1=int(source_truth['totals'][1,cat]),
                                            true_mean=source_truth['mean'][cat],true_variance=source_truth['variance'][cat],
                                            planning_variance=source_truth['planning_variance'][cat],
                                            empirical_mean=source['z'][:,cat].mean(),empirical_variance=source['z'][:,cat].var(ddof=1),
                                            finite_source_logistic_rate=source['strict'].mean(),
                                            all_40_source_sites_retained=True))
                rows.extend(site_diagnostics(sim,sites,roles,scenario['name'],dgp,scale,counts,p))
                joint.extend(joint_diagnostics(sim,candidates,scenario['name'],dgp,scale))
                for j,site in enumerate(sites):
                    for t in [0,1]:
                        for c in range(3):
                            schedules.append(dict(scenario=scenario['name'],dgp=dgp,scale=scale,site=site,
                                                  treatment=t,category=c+1,n=int(counts[j,t,c]),
                                                  profile=p[j,c],q=q[j,t,c]))
                # A fixed source-fitted planning noise, and an oracle-noise
                # benchmark. Neither uses future outcomes for selection.
                pv=np.sum(p[candidates]**2*np.divide(qp*(1-qp),counts[candidates],
                                                   out=np.zeros_like(counts[candidates],dtype=float),
                                                   where=counts[candidates]>0).sum(axis=1),axis=1)
                if not sim['identified'][candidates].all():
                    # Keep the menu and denominators; the unavailable whole-
                    # menu policy comparison cannot be rescued by deleting a
                    # difficult candidate after inspection.
                    bad='|'.join(sites[candidates[~sim['identified'][candidates]]])
                    for noise_model in ['source_fitted_planning','oracle']:
                        for budget in [1,2,4]:
                            for policy in ['logdet_greedy','logdet_exhaustive','target_variance_greedy',
                                           'nearest_profile','bernoulli_exhaustive_oracle',
                                           'bernoulli_mc_exhaustive_oracle','random_uniform_expectation']:
                                for estimator in ['strict_finite_logistic_mle','extended_probability_mle']:
                                    comparisons.append(dict(scenario=scenario['name'],dgp=dgp,scale=scale,
                                                             noise_model=noise_model,budget=budget,policy=policy,
                                                             estimator=estimator,replications=reps,available=False,
                                                             unavailable_reason='active empty cells in frozen menu: '+bad,
                                                             valid_rate=0.,mse=np.nan,mae=np.nan,
                                                             coverage95_unconditional=0.))
                else:
                    for noise_model,v in [('source_fitted_planning',pv),('oracle',sim['oracle'][candidates])]:
                        source_working=source_truth['planning_variance'] if noise_model=='source_fitted_planning' else source_truth['oracle_variance']
                        library=design_library(p[candidates],v,source_working,source_truth,p[targets],sim['truth'][candidates],
                                               sim['truth'][targets],sim['oracle'][candidates],counts[candidates].sum(axis=(1,2)))
                        a,b=evaluate_designs(sim,source,pilot_sim,pilot_source,candidates,p[targets],sim['truth'][targets],library,
                                             sites,scenario['name'],dgp,scale,noise_model)
                        for record in a: record['available']=True
                        comparisons.extend(a);exhaustive.extend(b)
                elapsed.append(dict(scenario=scenario['name'],dgp=dgp,scale=scale,replications=reps,
                                    seed_entropy=seedseq.entropy,seed_spawn_key=list(seedseq.spawn_key),
                                    elapsed_seconds=time.perf_counter()-t0))
                print(json.dumps(elapsed[-1]),flush=True)
                # Atomic per-condition checkpoints are useful for long runs.
                pd.DataFrame(rows).to_csv(outdir/'gaussian_approximation_results.csv',index=False)
                pd.DataFrame(comparisons).to_csv(outdir/'bridge_design_comparison.csv',index=False)
                pd.DataFrame(exhaustive).to_csv(outdir/'bernoulli_monte_carlo_results.csv',index=False)
                pd.DataFrame(joint).to_csv(outdir/'joint_gaussian_diagnostics.csv',index=False)
                pd.DataFrame(source_rows).to_csv(outdir/'source_summary_diagnostics.csv',index=False)
                pd.DataFrame(geometry).to_csv(outdir/'source_design_conditioning.csv',index=False)
    result=pd.DataFrame(rows)
    result['coverage95_absolute_error']=abs(result['coverage95_unconditional']-.95)
    result['in_candidate_menu']=result['site'].isin(sites[candidates])
    scoped=pd.concat([result.assign(scope='all_57_sites'),result[result.in_candidate_menu].assign(scope='fixed_12_menu')])
    summary=scoped.groupby(['scenario','dgp','scale','estimator','variance','scope'],sort=False).agg(
        site_count=('site','size'),identified_site_count=('identified','sum'),
        adequate_site_count=('adequate','sum'),mean_finite_beta_rate=('finite_beta_rate','mean'),
        finite_logistic_gate_site_count=('finite_logistic_gate','sum'),
        minimum_finite_beta_rate=('finite_beta_rate','min'),mean_valid_rate=('valid_rate','mean'),
        mean_coverage95_unconditional=('coverage95_unconditional','mean'),
        max_coverage95_absolute_error=('coverage95_absolute_error','max'),
        mean_coverage95_conditional_identified=('coverage95_conditional','mean'),
        mean_qq_max_abs_identified=('z_qq_max_abs','mean'),
        max_qq_max_abs_identified=('z_qq_max_abs','max')).reset_index()
    summary['all_sites_in_scope_adequate']=summary['adequate_site_count']==summary['site_count']
    summary['all_finite_logistic_gates_in_scope']=summary['finite_logistic_gate_site_count']==summary['site_count']
    summary.to_csv(outdir/'sample_size_scaling.csv',index=False)
    result.to_csv(outdir/'gaussian_approximation_results.csv',index=False)
    menu=summary[summary.scope=='fixed_12_menu'][['scenario','dgp','scale','estimator','variance','all_sites_in_scope_adequate']]
    joint_result=pd.DataFrame(joint).merge(menu,on=['scenario','dgp','scale','estimator','variance'],how='left')
    joint_result=joint_result.rename(columns={'all_sites_in_scope_adequate':'all_12_marginal_sites_adequate'})
    joint_result['joint_and_all12_adequate']=joint_result['adequate']&joint_result['all_12_marginal_sites_adequate']
    joint_result.to_csv(outdir/'joint_gaussian_diagnostics.csv',index=False)
    pd.DataFrame(schedules).to_csv(outdir/'simulation_cell_counts.csv',index=False)
    manifest=dict(protocol_path=str(protocol_path.resolve()),protocol_sha256=sha256(protocol_path),
                  code_sha256=sha256(Path(__file__)),seed=protocol['seed'],
                  run_type='timing_pilot' if pilot else 'full',condition_runs=elapsed,
                  elapsed_seconds=time.perf_counter()-start,numpy=np.__version__,pandas=pd.__version__,
                  scipy=__import__('scipy').__version__,
                  source_summary='fresh pooled category contrasts from all40 source sites; independent future bridge outcomes; zero-mean identity prior',
                  oracle='exact Bernoulli first-two-moment risk minimizer plus independent-pilot2000 selected MC exhaustive oracle evaluated on fresh main draws',
                  mle='analytic saturated cell binomial MLE, strict finite coefficients and extended probability boundary estimates separate',
                  outputs={p.name:sha256(p) for p in outdir.glob('*.csv')})
    (outdir/'monte_carlo_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--outdir',type=Path,required=True)
    parser.add_argument('--pilot',action='store_true')
    args=parser.parse_args()
    print(json.dumps(run_protocol(args.protocol,args.outdir,args.pilot),indent=2),flush=True)

