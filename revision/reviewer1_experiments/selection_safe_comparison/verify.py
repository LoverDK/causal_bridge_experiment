"""Independent raw-data reconstruction; intentionally does not import run.py."""
from pathlib import Path
import csv, hashlib, json, math, sys, time
import numpy as np

ROOT=Path(__file__).resolve().parent

def close(a,b,tol=2e-10):
    if a is None or b is None:
        assert a is b
    else:
        assert abs(float(a)-float(b))<=tol, (a,b)

def main(profile):
    started=time.perf_counter();out=ROOT/profile
    cfg=json.loads((out/'config.json').read_text())
    designs=json.loads((out/'designs.json').read_text())
    manifest=json.loads((out/'manifest.json').read_text())
    for name,expected in manifest['artifact_hashes'].items():
        assert hashlib.sha256((out/name).read_bytes()).hexdigest()==expected,name
    summaries=list(csv.DictReader((out/'summary.csv').open(encoding='utf-8')))
    pairrows=list(csv.DictReader((out/'paired.csv').open(encoding='utf-8')))
    summarymap={(int(r['cell']),float(r['rho']),r['method'],float(r['delta'])):r for r in summaries}
    pairmap={(int(r['cell']),float(r['rho']),r['right'],float(r['delta'])):r for r in pairrows}
    maxdiff=0.;count=0;impossible=0;all_geometry=0.;analytic=[]
    for d in designs:
        z=np.load(out/'raw'/f"cell_{d['cell']:03d}.npz")
        x=z['x'];s=z['s'];a0=z['a0'];k=len(x);n=len(z['target_truth'])
        l,h,u=[float(z[v]) for v in ['l','h','u']]
        half1,half2=z['half1'],z['half2'];y=.5*half1+.5*half2
        q=math.sqrt(2*math.log(2/cfg['alpha']));qk=math.sqrt(2*math.log(2*k/cfg['alpha']))
        def f(t):
            return t*0 if d['surface']=='flat' else .3*t+(.4*t*t if d['surface']=='curved' else 0)
        assert np.array_equal(f(z['actual_target']),z['target_truth'])
        assert np.all(abs(z['actual_source']-x)<=u+1e-14)
        assert np.all(abs(z['actual_target'])<=u+1e-14)
        truth=z['target_truth']
        for ri,rho in enumerate(cfg['rho']):
            selected=np.array([max(range(k),key=lambda j:abs(row[j])/s[j]) for row in y])
            split_selected=np.array([max(range(k),key=lambda j:abs(row[j])/(math.sqrt(2)*s[j])) for row in half1])
            assert np.array_equal(selected,z['selected'][ri])
            assert np.array_equal(split_selected,z['split_selected'][ri])
            a=np.tile((1-rho)*a0,(n,1));a[np.arange(n),selected]+=rho
            ah=np.tile((1-rho)*a0,(n,1));ah[np.arange(n),split_selected]+=rho
            weights=[a,np.tile(a0,(n,1)),ah,a,np.full((n,k),1/k),np.tile((1/s**2)/sum(1/s**2),(n,1))]
            re=[];rr=[]
            for mi,w in enumerate(weights):
                assert np.all(w>=-1e-15) and np.allclose(w.sum(axis=1),1)
                est=np.sum(w*(half2 if mi==2 else y),axis=1)
                g=l*(np.abs(np.sum(w*x,axis=1))+2*u)+h/2*np.sum(w*(np.abs(x)+2*u)**2,axis=1)
                noise=qk*np.sum(w*s,axis=1) if mi==0 else q*np.sqrt(np.sum((w*s)**2,axis=1))*(math.sqrt(2) if mi==2 else 1)
                rad=g+noise
                maxdiff=max(maxdiff,float(np.max(abs(est-z['estimate'][ri,mi]))),float(np.max(abs(rad-z['radius'][ri,mi]))))
                assert np.allclose(est,z['estimate'][ri,mi],rtol=0,atol=2e-12)
                assert np.allclose(rad,z['radius'][ri,mi],rtol=0,atol=2e-12)
                source_true=f(z['actual_source'])
                geom_violation=np.abs(np.sum(w*source_true,axis=1)-truth)-g
                all_geometry=max(all_geometry,float(geom_violation.max()))
                assert np.all(geom_violation<=1e-12)
                err=abs(est-truth);cov=err<=rad
                for delta in cfg['tolerances']:
                    r=summarymap[(d['cell'],rho,cfg['methods'][mi],delta)]
                    release=rad<=delta;nr=int(release.sum());bad=release&(err>delta)
                    assert nr==int(r['releases']) and int(cov.sum())==int(r['coverage_n'])
                    assert int(bad.sum())==int(r['bad_releases'])
                    assert int(cov[release].sum())==int(r['conditional_coverage_n'])
                    for name,v in [('coverage',cov),('release',release),('refusal',~release),('bad_release_probability',bad)]:
                        close(r[name],np.mean(v))
                    close(r['width'],np.mean(rad*2));close(r['all_MAE'],err.mean())
                    if nr:
                        close(r['selective_risk'],bad.sum()/nr)
                        close(r['conditional_coverage'],cov[release].mean())
                        close(r['released_MAE'],err[release].mean())
                    else:
                        assert r['selective_risk']==r['conditional_coverage']==r['released_MAE']==''
                    for name,v in [('width',rad*2),('all_MAE',err),('released_MAE',err[release])]:
                        if len(v)>1: close(r[name+'_mc_se'],np.std(v,ddof=1)/math.sqrt(len(v)))
                    count+=1
                re.append(est);rr.append(rad)
            re=np.array(re);rr=np.array(rr);err=abs(re-truth)
            for mi in range(1,6):
                for delta in cfg['tolerances']:
                    r=pairmap[(d['cell'],rho,cfg['methods'][mi],delta)]
                    a_release=rr[0]<=delta;b_release=rr[mi]<=delta
                    leftonly=int(np.sum(a_release&~b_release));rightonly=int(np.sum(b_release&~a_release))
                    assert leftonly==int(r['left_release_right_refuse'])
                    assert rightonly==int(r['right_release_left_refuse'])
                    if mi==1: impossible+=leftonly
                    for name,diff in [('release',a_release.astype(float)-b_release),
                                      ('coverage',(err[0]<=rr[0]).astype(float)-(err[mi]<=rr[mi])),
                                      ('width',2*(rr[0]-rr[mi])),('MAE',err[0]-err[mi])]:
                        close(r[name+'_difference'],diff.mean())
                        close(r[name+'_mc_se'],np.std(diff,ddof=1)/math.sqrt(n))
            if d['surface']=='flat' and d['precision']=='equal' and rho==1:
                # Exact null coverage for the max-absolute selected vertex.
                p_naive=math.erf(q/math.sqrt(2))**k
                p_simul=math.erf(qk/math.sqrt(2))**k
                analytic.append(dict(cell=d['cell'],K=k,naive_expected=p_naive,naive_observed=float(np.mean(err[3]<=rr[3])),
                                     simultaneous_expected=p_simul,simultaneous_observed=float(np.mean(err[0]<=rr[0]))))
        assert d['dual_gap']<=cfg['optimizer_dual_gap_tolerance']
    assert impossible==0
    result=dict(passed=True,independent_reconstruction=True,summary_rows_recomputed=count,
                max_formula_difference=maxdiff,max_geometry_violation=all_geometry,
                impossible_global_optimized_release_reversals=impossible,
                analytic_null_comparisons=analytic,seconds=time.perf_counter()-started)
    (out/'independent_verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='analytic_null_comparisons'}))

if __name__=='__main__': main(sys.argv[1])
