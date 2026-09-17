"""Fixed-protocol simulations; exported records include negative results."""
from itertools import combinations
from time import perf_counter
import json
import numpy as np
import pandas as pd
from scipy.special import softmax
from scipy.stats import norm
from .core import (box_vertices, radius, optimize_radius, calibrated_quantile,
                   sharp_lipschitz, posterior, information, logdet_greedy, complementarity)


def save(out, name, rows):
    df = pd.DataFrame(rows)
    df.to_csv(out/f'{name}.csv', index=False, float_format='%.12g')
    return df


def wilson(success, total):
    if total == 0: return np.nan, np.nan
    p, z = success/total, norm.ppf(.975)
    den = 1+z*z/total
    mid = (p+z*z/(2*total))/den
    half = z*np.sqrt(p*(1-p)/total+z*z/(4*total*total))/den
    return max(0., mid-half), min(1., mid+half)


def hidden(cfg, out):
    rng = np.random.default_rng(cfg['seed_hidden']); n = cfg['hidden_draws']
    error = rng.normal(0, .1, n); rows = []
    for h in np.linspace(0, .5, 26):
        for method, rad in [('semantic_gaussian', norm.ppf(.975)*.1),
                            ('paper_gaussian_set', .3+norm.ppf(.975)*.1),
                            ('theorem_Rinf', .3+np.sqrt(2*np.log(8/.05))*.2)]:
            hits = int(np.count_nonzero(abs(error-h) <= rad))
            lo, hi = wilson(hits, n)
            rows.append(dict(shift=h, method=method, radius=rad, n=n, coverage=hits/n,
                             mc_lower=lo, mc_upper=hi,
                             analytic=norm.cdf((h+rad)/.1)-norm.cdf((h-rad)/.1),
                             set_valid=h<=.3+1e-12))
    return save(out, 'hidden_shift', rows)


def selection(cfg, out):
    rng = np.random.default_rng(cfg['seed_selection']); n = cfg['selection_draws']
    rows = []
    for k in [1, 2, 4, 8, 16, 32, 64, 128]:
        z = rng.normal(size=(n, k)); maxima = abs(z).max(axis=1)
        for method, threshold, exact in [
            ('pointwise_after_max', norm.ppf(.975), .95**k),
            ('gaussian_bonferroni', norm.ppf(1-.05/(2*k)), (1-.05/k)**k),
            ('theorem_Rinf_max', np.sqrt(2*np.log(2*k/.05)),
             (2*norm.cdf(np.sqrt(2*np.log(2*k/.05)))-1)**k)]:
            hits = int((maxima<=threshold).sum()); lo, hi = wilson(hits,n)
            rows.append(dict(k=k,method=method,n=n,coverage=hits/n,analytic=exact,
                             mc_lower=lo,mc_upper=hi,mean_width=2*threshold))
        for temperature in [.25, 1.0]:
            a = softmax(abs(z)/temperature, axis=1); estimate = (a*z).sum(axis=1)
            for method, rad in [
                ('continuous_Rinf', np.full(n,np.sqrt(2*np.log(2*k/.05)))),
                ('continuous_R2_invalid', np.sqrt(2*np.log(2/.05))*np.linalg.norm(a,axis=1))]:
                hits=int((abs(estimate)<=rad).sum()); lo,hi=wilson(hits,n)
                rows.append(dict(k=k,method=method,temperature=temperature,n=n,coverage=hits/n,
                                 mc_lower=lo,mc_upper=hi,mean_width=2*np.mean(rad)))
        # Truly continuous data-dependent mixing, distinct from simplex-vertex selection.
        j=np.argmax(abs(z),axis=1); mixing=1/(1+np.exp(-maxima))
        estimate=(1-mixing)*z.mean(axis=1)+mixing*z[np.arange(n),j]
        rad=np.sqrt(2*np.log(2*k/.05))
        hits=int((abs(estimate)<=rad).sum());lo,hi=wilson(hits,n)
        rows.append(dict(k=k,method='continuous_mixture_Rinf',n=n,coverage=hits/n,
                         mc_lower=lo,mc_upper=hi,mean_width=2*rad))
    return save(out,'selection',rows)


def minimax(cfg,out):
    rng=np.random.default_rng(cfg['seed_minimax']);z=rng.normal(size=cfg['minimax_draws'])
    rows=[]
    for a in np.geomspace(.01,1,cfg['minimax_grid']):
        for sigma in np.geomspace(.01,1,cfg['minimax_grid']):
            losses=abs(sigma*z-a); analytic=sigma*np.sqrt(2/np.pi)*np.exp(-.5*(a/sigma)**2)+a*(2*norm.cdf(a/sigma)-1)
            rows.append(dict(ambiguity=a,sigma=sigma,n=len(z),risk=losses.mean(),
                             risk_mcse=losses.std(ddof=1)/np.sqrt(len(z)),analytic_risk=analytic,
                             risk_over_rate=losses.mean()/max(a,sigma),
                             minimax_lower=max(a,sigma/8),upper=a+sigma*np.sqrt(2/np.pi)))
    return save(out,'minimax',rows)


def joint_calibration(cfg,out):
    rows=[]; rng=np.random.default_rng(cfg['seed_calibration'])
    for k in [4,16,64]:
        for rep in range(cfg['joint_calibration_repetitions']):
            residual=abs(rng.normal(size=(cfg['calibration_archives'],k+1)))
            qjoint=calibrated_quantile(residual.max(axis=1),cfg['eta'])
            qsingle=calibrated_quantile(residual[:,0],cfg['eta'])
            oracle=norm.ppf(1-cfg['eta']/(2*(k+1)))
            test=abs(rng.normal(size=k+1))
            for shift in [1.,2.]:
                for name,q in [('joint_max',qjoint),('marginal_only_invalid',qsingle),('gaussian_union',oracle)]:
                    rows.append(dict(k=k,replicate=rep,test_scale=shift,method=name,radius=q,
                                     joint_covered=bool(np.all(test*shift<=q)),
                                     marginal_fraction=float(np.mean(test*shift<=q))))
    df=save(out,'joint_calibration_records',rows)
    summary=[]
    for keys,g in df.groupby(['k','test_scale','method']):
        lo,hi=wilson(int(g.joint_covered.sum()),len(g))
        summary.append(dict(zip(['k','test_scale','method'],keys))|dict(n=len(g),
            joint_coverage=g.joint_covered.mean(),mc_lower=lo,mc_upper=hi,
            marginal_coverage=g.marginal_fraction.mean(),mean_radius=g.radius.mean()))
    return save(out,'joint_calibration_summary',summary)


def operational(cfg,out):
    rows=[]; audits=[]; k=4; scale=.06; L,H=1.2,.6
    scenarios=['nominal','extrapolation','proxy_shift','understated_LH','high_noise','bounded_nuisance_bias']
    for rep in range(cfg['operational_repetitions']):
        # Paired random streams across scenarios and methods; independent across replications.
        rng=np.random.default_rng(np.random.SeedSequence([cfg['seed_operational'],rep]))
        m=rng.uniform(-.8,.8,k+1); proxy_error=rng.normal(size=k+1); noise=rng.normal(size=k)
        cal=abs(rng.normal(size=(cfg['calibration_archives'],k+1))).max(axis=1)
        q=calibrated_quantile(cal,cfg['eta']); audit_radius=q*scale
        for scenario in scenarios:
            true_m=m.copy()
            if scenario=='extrapolation': true_m[:-1]=-.7+.15*np.arange(k);true_m[-1]=.95
            r=np.clip(true_m+scale*proxy_error*(3 if scenario=='proxy_shift' else 1),-1,1)
            boxes=np.column_stack((np.maximum(-1,r-audit_radius),np.minimum(1,r+audit_radius)))
            joint=bool(np.all((true_m>=boxes[:,0])&(true_m<=boxes[:,1])))
            tau=.6*true_m+.3*true_m**2
            s=np.linspace(.04,.10,k)*(3 if scenario=='high_noise' else 1)
            beta=np.full(k,.06 if scenario=='bounded_nuisance_bias' else 0.)
            bias=beta*np.array([-1,1,-1,1])
            effects=tau[:-1]+s*noise+bias
            l,h=(.12,.06) if scenario=='understated_LH' else (L,H)
            starts=perf_counter()
            if np.any(boxes[:,0]>boxes[:,1]):
                audits.append(dict(scenario=scenario,replicate=rep,status='empty_audited_set',joint_set_covered=False))
                continue
            a,rad,diag=optimize_radius(boxes,l,h,s,beta,cfg['zeta'])
            vertices=box_vertices(boxes)
            candidates=[('robust_Rinf',a,rad,diag),
                        ('design_R2',a,radius(a,vertices,l,h,s,beta,cfg['zeta'],'fixed'),diag)]
            # Outcome-adaptive stress rule (not the release-radius minimizer).
            # All weights remain strictly inside the simplex. Select temperature
            # AFTER seeing effects; selection-safe validity must survive this.
            adaptive_candidates=[softmax(abs(effects)/temp) for temp in [.02,.08,.3,1.]]
            adaptive=max(adaptive_candidates,key=lambda w: abs(w@effects))
            candidates.extend([
                ('adaptive_Rinf',adaptive,radius(adaptive,vertices,l,h,s,beta,cfg['zeta']),{}),
                ('adaptive_R2_invalid',adaptive,radius(adaptive,vertices,l,h,s,beta,cfg['zeta'],'fixed'),{})])
            for name,ab_boxes,ab_h in [
                ('singleton_U',np.column_stack((np.clip(r,-1,1),np.clip(r,-1,1))),h),
                ('no_curvature',boxes,0.)]:
                aw,rw,dd=optimize_radius(ab_boxes,l,ab_h,s,beta,cfg['zeta']);candidates.append((name,aw,rw,dd))
            elapsed=perf_counter()-starts
            design=np.column_stack((np.ones(k),r[:-1])); reg=np.diag([0.,.1])
            prediction=float(np.array([1,r[-1]])@np.linalg.solve(design.T@design+reg,design.T@effects))
            candidates.extend([('ridge_source_only',None,np.nan,{}),('archive_mean',np.full(k,1/k),np.nan,{})])
            audits.append(dict(scenario=scenario,replicate=rep,status='evaluated',q=q,
                joint_set_covered=joint,mechanisms=json.dumps(true_m.tolist()),proxies=json.dumps(r.tolist()),
                boxes=json.dumps(boxes.tolist()),effects=json.dumps(effects.tolist()),noise_sd=json.dumps(s.tolist()),
                beta=json.dumps(beta.tolist()),L=l,H=h,optimization_seconds=elapsed))
            for name,weights,bound,dd in candidates:
                estimate=prediction if weights is None else float(weights@effects)
                error=abs(estimate-tau[-1]); lo=estimate-bound;hi=estimate+bound
                # Verified outer envelope from singleton Lipschitz constraints, for general boxes.
                distances=np.maximum(abs(boxes[-1,0]-boxes[:-1,1]),abs(boxes[-1,1]-boxes[:-1,0]))
                source_radius=beta+np.sqrt(2*np.log(2*k/cfg['zeta']))*s
                outer_lo=np.max(effects-source_radius-l*distances)
                outer_hi=np.min(effects+source_radius+l*distances)
                rows.append(dict(scenario=scenario,replicate=rep,method=name,truth=tau[-1],estimate=estimate,
                    error=error,radius=bound,width=2*bound,covered=bool(lo<=tau[-1]<=hi) if np.isfinite(bound) else np.nan,
                    joint_set_covered=joint,weights=json.dumps(weights.tolist()) if weights is not None else '',
                    outer_status='nonempty' if outer_lo<=outer_hi else 'inconsistent',
                    outer_lower=outer_lo,outer_upper=outer_hi,outer_covered=outer_lo<=tau[-1]<=outer_hi,
                    assumption_valid=scenario not in ['proxy_shift','understated_LH'],**dd))
        if (rep+1)%25==0: print(f'  operational {rep+1}/{cfg["operational_repetitions"]}',flush=True)
    df=save(out,'operational_records',rows);save(out,'operational_audits',audits)
    summaries=[];frontier=[]
    for (scenario,method),g in df.groupby(['scenario','method']):
        coverage_lo,coverage_hi=wilson(int(g.covered.fillna(False).sum()),int(g.covered.notna().sum()))
        summaries.append(dict(scenario=scenario,method=method,n=len(g),mae=g.error.mean(),
            mae_mcse=g.error.std(ddof=1)/np.sqrt(len(g)),coverage=g.covered.mean(),mean_width=g.width.mean(),
            coverage_mc_lower=coverage_lo,coverage_mc_upper=coverage_hi,
            joint_set_coverage=g.joint_set_covered.mean(),outer_coverage=g.outer_covered.mean(),
            solver_failures=g.solver_failures.sum()))
        if not g.radius.notna().all(): continue
        for tol in cfg['tolerances']:
            release=g.radius<=tol; wrong=release & (g.error>tol);nrel=int(release.sum())
            elo,ehi=wilson(int(wrong.sum()),len(g))
            frontier.append(dict(scenario=scenario,method=method,tolerance=tol,n=len(g),n_released=nrel,
                release_rate=release.mean(),released_mae=g.loc[release,'error'].mean(),
                released_coverage=g.loc[release,'covered'].mean(),
                unconditional_bad_release=wrong.mean(),bad_release_mc_lower=elo,bad_release_mc_upper=ehi,
                conditional_bad_release=float(wrong.sum()/nrel) if nrel else np.nan,
                bound_if_valid=cfg['eta']+cfg['zeta']))
    save(out,'operational_summary',summaries);save(out,'operational_frontier',frontier)
    return df


def pi_audit(cfg,out):
    rng=np.random.default_rng(cfg['seed_pi']);rows=[];witnesses=[];k=5;L=1.2
    for rep in range(cfg['pi_repetitions']):
        x=np.sort(rng.uniform(-1,1,k));target=rng.uniform(-1,1);tau=.6*x+.3*x*x;truth=.6*target+.3*target*target
        sd=np.full(k,.06);obs=tau+rng.normal(size=k)*sd
        delta=np.sqrt(2*np.log(2*k/cfg['zeta']))*sd
        for mode,lower,upper in [('exact_sources',tau,tau),('noisy_sources',obs-delta,obs+delta)]:
            res=sharp_lipschitz(x,target,lower,upper,L)
            row=dict(replicate=rep,mode=mode,target=target,truth=truth,status=res['status'],
                     lower=res['lower'],upper=res['upper'],width=res['width'],
                     covered=res['lower']<=truth<=res['upper'],
                     best_singleton_width=float(np.min(upper-lower+2*L*abs(x-target))))
            if mode=='exact_sources':
                closed_lo=np.max(tau-L*abs(x-target));closed_hi=np.min(tau+L*abs(x-target))
                row['closed_form_error']=max(abs(res['lower']-closed_lo),abs(res['upper']-closed_hi))
            rows.append(row)
            witnesses.append(dict(replicate=rep,mode=mode,x=x.tolist(),target=target,
                                  source_lower=lower.tolist(),source_upper=upper.tolist(),**res))
    save(out,'pi_records',rows)
    cases={'inconsistent_sources':sharp_lipschitz([0,.1],.05,[0,1],[0,1],1),
           'unanchored':sharp_lipschitz([],0,[],[],1),
           'hull_interior':sharp_lipschitz([-1,1],0,[0,0],[0,0],1)}
    for witness in witnesses:
        for key,value in list(witness.items()):
            if isinstance(value,float) and not np.isfinite(value):witness[key]=None
    (out/'pi_witnesses.json').write_text(json.dumps(witnesses,indent=2,allow_nan=False),encoding='utf-8')
    # JSON-safe representation: status carries the meaning of unavailable endpoints.
    cases={k:{a:(None if isinstance(v,float) and not np.isfinite(v) else v) for a,v in d.items()} for k,d in cases.items()}
    (out/'pi_boundary_cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
    return pd.DataFrame(rows)


def bridges(cfg,out):
    rng=np.random.default_rng(cfg['seed_bridge']);rows=[];p=6;n=12;budget=4
    subsets=list(combinations(range(n),budget));designs=[]
    for rep in range(cfg['bridge_instances']):
        q,_=np.linalg.qr(rng.normal(size=(p,p)))
        prior=q@np.diag(np.exp(rng.uniform(np.log(.35),np.log(3),p)))@q.T
        x=rng.normal(size=(n,p));x/=np.linalg.norm(x,axis=1)[:,None];x*=rng.lognormal(0,.5,n)[:,None]
        sigma=np.full(n,.5);target=rng.normal(size=p);target/=np.linalg.norm(target)
        start=perf_counter();covs=[posterior(prior,x,sigma,s) for s in subsets]
        values=np.array([information(prior,v) for v in covs]);radii=np.array([1.96*np.sqrt(target@v@target) for v in covs])
        conditions=np.array([np.linalg.cond(v) for v in covs]);exhaustive_seconds=perf_counter()-start
        start=perf_counter();greedy=logdet_greedy(prior,x,sigma,budget);greedy_seconds=perf_counter()-start
        gi=subsets.index(tuple(sorted(greedy)));best=int(np.argmax(values));targetbest=int(np.argmin(radii))
        random_ids=rng.integers(0,len(subsets),cfg['bridge_random_subsets'])
        kappa=float(conditions.max()) # verifies the condition for ALL feasible budget-B sets in this instance.
        for method,idxs in [('greedy',[gi]),('logdet_optimum',[best]),('target_optimum',[targetbest]),('random',random_ids)]:
            for trial,idx in enumerate(idxs):
                v=covs[idx];det=np.linalg.det(v)
                bound=1.96*np.linalg.norm(target)*np.sqrt(kappa)*det**(1/(2*p))
                rows.append(dict(replicate=rep,method=method,trial=trial,selected=str(subsets[idx]),
                    information=values[idx],information_ratio=values[idx]/values[best],
                    target_radius=radii[idx],target_radius_ratio=radii[idx]/radii[targetbest],
                    condition=conditions[idx],all_subset_kappa=kappa,target_radius_bound=bound,
                    greedy_seconds=greedy_seconds if method=='greedy' else np.nan,
                    exhaustive_seconds=exhaustive_seconds if method=='logdet_optimum' else np.nan))
        designs.append(dict(replicate=rep,prior=prior.tolist(),design=x.tolist(),sigma=sigma.tolist(),target=target.tolist()))
    df=save(out,'bridge_records',rows);save(out,'bridge_complementarity',complementarity())
    (out/'bridge_designs.json').write_text(json.dumps(designs,indent=2),encoding='utf-8')
    # Global logdet favors the first high-variance coordinate, but target is the second.
    prior=np.diag([100.,.1]);x=np.eye(2);sigma=np.ones(2);target=np.array([0.,1.]);greedy=logdet_greedy(prior,x,sigma,1)
    anis=[]
    for i in range(2):
        v=posterior(prior,x,sigma,[i]);anis.append(dict(candidate=i,chosen_by_logdet=i in greedy,
            information=information(prior,v),target_radius=1.96*np.sqrt(target@v@target),condition=np.linalg.cond(v)))
    save(out,'bridge_anisotropy',anis)
    return df
