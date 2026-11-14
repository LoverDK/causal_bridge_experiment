"""Frozen paired-world benchmark. Python run.py --profile smoke|full.

No execution without root authorization. Every artifact stays alongside this file.
"""
from __future__ import annotations
import argparse, csv, hashlib, itertools, json, math, os, platform, sys, time
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import minimize, minimize_scalar

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / 'config.json').read_text(encoding='utf-8'))
METHODS = CFG['methods']

def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False), encoding='utf-8')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def cells():
    for i, v in enumerate(itertools.product(CFG['geometry'], CFG['precision'], CFG['surfaces'], CFG['K'], CFG['ambiguity'])):
        yield dict(cell=i, geometry=v[0], precision=v[1], surface=v[2], K=v[3], u=v[4])

def design(cell):
    k = cell['K']
    if cell['geometry'] == 'balanced_near':
        x = np.linspace(-.12, .12, k)
    elif cell['geometry'] == 'one_distant':
        x = np.r_[.75, np.linspace(-.1, .1, k-1)]
    else:
        x = np.linspace(.55, .85, k)
    s = np.full(k, .1) if cell['precision'] == 'equal' else np.linspace(.06, .14, k)
    if cell['precision'] == 'heterogeneous' and cell['geometry'] == 'one_distant':
        s[0] = .025
    l, h = {'flat': (0.,0.), 'linear': (.3,0.), 'curved': (1.1,.8)}[cell['surface']]
    return x, s, l, h

def surface(x, name):
    return np.zeros_like(x) if name == 'flat' else .3*x + (.4*x*x if name == 'curved' else 0.)

def geometry(a, x, l, h, u):
    return l*(np.abs(a @ x)+2*u) + .5*h*(a @ ((np.abs(x)+2*u)**2))

def radius(a, x, s, l, h, u, mode='r2'):
    q = np.sqrt(2*np.log(2/CFG['alpha']))
    qk = np.sqrt(2*np.log(2*len(x)/CFG['alpha']))
    noise = qk*(a @ s) if mode == 'rinf' else q*np.sqrt((a*a) @ (s*s))
    return geometry(a,x,l,h,u) + noise

def optimize(x,s,l,h,u):
    """Convex primal plus independent supporting-hyperplane dual certificate."""
    t0 = time.perf_counter()
    k = len(x); q = np.sqrt(2*np.log(2/CFG['alpha']))
    c = .5*h*(np.abs(x)+2*u)**2
    def fun(v):
        a=v[:k]
        return 2*l*u+c@a+l*v[-1]+q*np.linalg.norm(s*a)
    def jac(v):
        a=v[:k]; norm=np.linalg.norm(s*a)
        return np.r_[c+q*s*s*a/norm,l]
    cons=[{'type':'eq','fun':lambda v:v[:k].sum()-1,'jac':lambda v:np.r_[np.ones(k),0.]},
          {'type':'ineq','fun':lambda v:v[-1]-x@v[:k],'jac':lambda v:np.r_[-x,1.]},
          {'type':'ineq','fun':lambda v:v[-1]+x@v[:k],'jac':lambda v:np.r_[x,1.]}]
    candidates=[]
    for astart in [np.ones(k)/k, s**-2/np.sum(s**-2)]:
        out=minimize(fun,np.r_[astart,abs(x@astart)],jac=jac,method='SLSQP',
                     bounds=[(0,1)]*k+[(0,None)],constraints=cons,
                     options={'ftol':1e-12,'maxiter':1000})
        a=np.maximum(out.x[:k],0); a/=a.sum()
        candidates.append((float(radius(a,x,s,l,h,u)),a,out.success))
    val,a,success=min(candidates,key=lambda z:z[0])
    # b=q diag(s)a/||diag(s)a|| is feasible for dual Euclidean ball.
    b=q*s*a/np.linalg.norm(s*a)
    coeff=c+b*s
    # Maximizing min_i(coeff_i+v*x_i), |v|<=L is a one-dimensional LP.
    # Enumerate intersections to avoid local optimizer and certify finite optimum.
    trial=[-l,l]
    for i in range(k):
        for j in range(i):
            if abs(x[i]-x[j])>1e-15:
                z=(coeff[j]-coeff[i])/(x[i]-x[j])
                if -l<=z<=l: trial.append(z)
    lower=max(2*l*u+float(np.min(coeff+v*x)) for v in trial)
    gap=val-lower
    if gap < -1e-9 or gap>CFG['optimizer_dual_gap_tolerance']:
        raise AssertionError(f'Convex optimization dual gap {gap}')
    return a,dict(primal=val,dual_lower=lower,dual_gap=gap,success=bool(success),seconds=time.perf_counter()-t0)

def select(y,s):
    return np.argmax(np.abs(y)/s,axis=1)

def policy(half1,half2,x,s,l,h,u,a0,rho):
    """No target truth or true source/target mechanisms are accepted."""
    n,k=half1.shape
    y=(half1+half2)/2
    idx=select(y,s); splitidx=select(half1,np.sqrt(2)*s)
    a=np.broadcast_to((1-rho)*a0,(n,k)).copy(); a[np.arange(n),idx]+=rho
    ah=np.broadcast_to((1-rho)*a0,(n,k)).copy(); ah[np.arange(n),splitidx]+=rho
    uniform=np.full(k,1/k); iv=s**-2/np.sum(s**-2)
    est=np.stack([np.sum(a*y,axis=1),y@a0,np.sum(ah*half2,axis=1),np.sum(a*y,axis=1),y@uniform,y@iv])
    rad=np.stack([radius(a,x,s,l,h,u,'rinf'),np.full(n,radius(a0,x,s,l,h,u)),
                  radius(ah,x,np.sqrt(2)*s,l,h,u),radius(a,x,s,l,h,u),
                  np.full(n,radius(uniform,x,s,l,h,u)),np.full(n,radius(iv,x,s,l,h,u))])
    return est,rad,idx,splitidx

def wilson(success,n):
    if n==0: return (None,None,None)
    p=float(success/n); z=1.959963984540054; d=1+z*z/n
    mid=(p+z*z/(2*n))/d
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (p,max(0.,float(mid-half)),min(1.,float(mid+half)))

def mean_se(x):
    return (None,None) if len(x)==0 else (float(np.mean(x)),float(np.std(x,ddof=1)/np.sqrt(len(x))) if len(x)>1 else None)

def summarize(cell,rho,est,rad,truth):
    rows=[]
    for j,m in enumerate(METHODS):
        err=np.abs(est[j]-truth); cov=err<=rad[j]
        for delta in CFG['tolerances']:
            release=rad[j]<=delta; bad=release&(err>delta); nr=int(release.sum())
            row={**cell,'rho':rho,'method':m,'delta':delta,'worlds':len(truth),'releases':nr,
                 'bad_releases':int(bad.sum()),'coverage_n':int(cov.sum()),
                 'conditional_coverage_n':int(cov[release].sum()),'guarantee_applicable':m!='naive_postselection_R2'}
            for name,v,n in [('coverage',int(cov.sum()),len(truth)),('release',nr,len(truth)),
                             ('refusal',len(truth)-nr,len(truth)),('bad_release_probability',int(bad.sum()),len(truth)),
                             ('selective_risk',int(bad.sum()),nr),('conditional_coverage',int(cov[release].sum()),nr)]:
                p,lo,hi=wilson(v,n); row[name]=p; row[name+'_lo']=lo;row[name+'_hi']=hi
            for name,v in [('width',2*rad[j]),('all_MAE',err),('released_MAE',err[release])]:
                row[name],row[name+'_mc_se']=mean_se(v)
            rows.append(row)
    return rows

def paired(cell,rho,est,rad,truth):
    rows=[]; err=np.abs(est-truth)
    for j in range(1,len(METHODS)):
        for delta in CFG['tolerances']:
            r0=rad[0]<=delta; rj=rad[j]<=delta
            row={**cell,'rho':rho,'delta':delta,'left':METHODS[0],'right':METHODS[j],
                 'left_release_right_refuse':int(np.sum(r0&~rj)),
                 'right_release_left_refuse':int(np.sum(rj&~r0))}
            for name,diff in [('release',r0.astype(float)-rj),('coverage',(err[0]<=rad[0]).astype(float)-(err[j]<=rad[j])),
                              ('width',2*(rad[0]-rad[j])),('MAE',err[0]-err[j])]:
                mu,se=mean_se(diff); row[name+'_difference']=mu;row[name+'_mc_se']=se
                row[name+'_lo']=mu-1.96*se;row[name+'_hi']=mu+1.96*se
            rows.append(row)
    return rows

def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def isolation_checks(x,s,l,h,u,a0):
    # Deterministic inputs: not a Monte Carlo experiment.
    h1=np.vstack([np.linspace(-.3,.4,len(x)),np.linspace(.2,-.1,len(x))]);h2=-.7*h1
    p=policy(h1,h2,x,s,l,h,u,a0,.2)
    for fake_truth in [-1000.,1000.]:
        _scoring_error=np.abs(p[0]-fake_truth)
        fresh=policy(h1,h2,x,s,l,h,u,a0,.2)
        assert all(np.array_equal(a,b) for a,b in zip(p,fresh))
    altered=policy(h1,h2+10,x,s,l,h,u,a0,.2)
    assert np.array_equal(p[3],altered[3]),'split selector read evaluation half'
    assert np.allclose(p[2],select((h1+h2)/2,s))
    assert np.allclose(p[1][3],radius((1-.2)*a0+.2*np.eye(len(x))[p[2]],x,s,l,h,u))
    return {'target_scorer_flip':True,'split_selection_half2_isolation':True,'full_mean_is_half_average':True}

def run(profile):
    started=time.perf_counter();out=ROOT/profile
    if out.exists(): raise RuntimeError(f'Refusing to overwrite {out}')
    out.mkdir();(out/'raw').mkdir()
    n=CFG[profile+'_worlds_per_cell'];seed=CFG[profile+'_seed']
    allrows=[];allpairs=[];designs=[];checks=[]
    for cell in cells():
        x,s,l,h=design(cell);u=cell['u'];a0,opt=optimize(x,s,l,h,u)
        check=isolation_checks(x,s,l,h,u,a0)
        rng=np.random.default_rng(np.random.SeedSequence([seed,cell['cell']]))
        actual=x+rng.uniform(-u,u,size=(n,len(x)));target=rng.uniform(-u,u,size=n)
        tau=surface(actual,cell['surface']);truth=surface(target,cell['surface'])
        half1=tau+np.sqrt(2)*s*rng.standard_normal(tau.shape)
        half2=tau+np.sqrt(2)*s*rng.standard_normal(tau.shape)
        ests=[];rads=[];indices=[];splitindices=[];policytimes=[]
        for rho in CFG['rho']:
            t0=time.perf_counter();est,rad,idx,hidx=policy(half1,half2,x,s,l,h,u,a0,rho)
            policytimes.append(time.perf_counter()-t0)
            assert np.all(rad[3]<=rad[0]+1e-12),'same-weight R2 > Rinf'
            assert np.all(rad[1]<=rad[3]+CFG['optimizer_dual_gap_tolerance']),'global optimum ordering'
            assert np.all(rad[1]<=rad[0]+CFG['optimizer_dual_gap_tolerance'])
            assert np.all(np.abs((1-rho)*(tau@a0)+rho*tau[np.arange(n),idx]-truth)
                          <= geometry((1-rho)*a0+rho*np.eye(len(x))[idx],x,l,h,u)+1e-12),'invalid geometry'
            allrows+=summarize(cell,rho,est,rad,truth);allpairs+=paired(cell,rho,est,rad,truth)
            ests.append(est);rads.append(rad);indices.append(idx);splitindices.append(hidx)
        np.savez_compressed(out/'raw'/f"cell_{cell['cell']:03d}.npz",half1=half1,half2=half2,
                            actual_source=actual,actual_target=target,target_truth=truth,
                            estimate=np.stack(ests),radius=np.stack(rads),selected=np.stack(indices),
                            split_selected=np.stack(splitindices),a0=a0,x=x,s=s,l=l,h=h,u=u)
        designs.append({**cell,'x':x.tolist(),'s':s.tolist(),'L':l,'H':h,'a0':a0.tolist(),**opt,'policy_seconds_by_rho':policytimes})
        checks.append({**cell,**check,'same_weight_order':True,'global_order':True,'geometry_valid':True})
        if (cell['cell']+1)%12==0: print(f"{profile}: {cell['cell']+1}/72 cells; {time.perf_counter()-started:.2f}s",flush=True)
    write_csv(out/'summary.csv',allrows);write_csv(out/'paired.csv',allpairs)
    write_json(out/'designs.json',designs);write_json(out/'checks.json',checks)
    write_json(out/'config.json',CFG)
    files=[p for p in out.rglob('*') if p.is_file()]
    meta=dict(profile=profile,worlds_per_cell=n,cells=72,independent_worlds=72*n,
              total_seconds=time.perf_counter()-started,seed=seed,command=sys.argv,
              python=sys.version,numpy=np.__version__,scipy=scipy.__version__,platform=platform.platform(),
              code_hashes={p.name:sha(p) for p in [ROOT/'run.py',ROOT/'verify.py',ROOT/'config.json',ROOT/'PROTOCOL.md']},
              artifact_hashes={str(p.relative_to(out)):sha(p) for p in files})
    write_json(out/'manifest.json',meta)
    print(json.dumps({k:meta[k] for k in ['profile','independent_worlds','total_seconds']}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--profile',choices=['smoke','full'],required=True)
    run(parser.parse_args().profile)
