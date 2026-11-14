"""Post-run arithmetic timing audit on saved inputs, no simulated draws."""
from pathlib import Path
import csv, json, time
import numpy as np

ROOT=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'config.json').read_text())
designs=json.loads((ROOT/'full'/'designs.json').read_text())
clock=time.perf_counter
load_start=clock()
data=[]
for d in designs:
    with np.load(ROOT/'full'/'raw'/f"cell_{d['cell']:03d}.npz") as z:
        data.append({name:z[name].copy() for name in ['half1','half2','x','s','l','h','u','a0','estimate','radius']})
load_seconds=clock()-load_start
def compute(z,rho,mi):
    half1=z['half1'];half2=z['half2'];x=z['x'];s=z['s'];a0=z['a0'];n,k=half1.shape
    y=(half1+half2)/2
    if mi in [0,2,3]:
        idx=np.argmax(abs(half1 if mi==2 else y)/s,axis=1)
        w=np.broadcast_to((1-rho)*a0,(n,k)).copy();w[np.arange(n),idx]+=rho
    else:
        w=[None,a0,None,None,np.full(k,1/k),s**-2/sum(s**-2)][mi]
    est=np.sum(w*(half2 if mi==2 else y),axis=1)
    b=float(z['l'])*(abs(w@x)+2*float(z['u']))+float(z['h'])/2*(w@(abs(x)+2*float(z['u']))**2)
    if mi==0:
        rad=b+np.sqrt(2*np.log(2*k/cfg['alpha']))*(w@s)
    else:
        rad=b+np.sqrt(2*np.log(2/cfg['alpha']))*np.sqrt((w*w)@(s*s))*(np.sqrt(2) if mi==2 else 1)
    return est,np.broadcast_to(rad,n)
rows=[]
for repetition in range(3):
    for mi,method in enumerate(cfg['methods']):
        elapsed=0.
        for z in data:
            for ri,rho in enumerate(cfg['rho']):
                start=clock();e,r=compute(z,rho,mi);elapsed+=clock()-start
                assert np.allclose(e,z['estimate'][ri,mi],atol=2e-12,rtol=0)
                assert np.allclose(r,z['radius'][ri,mi],atol=2e-12,rtol=0)
        rows.append(dict(repetition=repetition,method=method,world_evaluations=720000,
                         policy_arithmetic_seconds=elapsed,microseconds_per_world=elapsed/720000*1e6))
with (ROOT/'timing.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
result=dict(repetitions=3,raw_load_seconds=load_seconds,
            shared_design_optimization_seconds=sum(d['seconds'] for d in designs),
            max_design_optimization_seconds=max(d['seconds'] for d in designs),
            per_method_seconds={m:[r['policy_arithmetic_seconds'] for r in rows if r['method']==m] for m in cfg['methods']},
            note='Standalone arithmetic measured from saved data, repeated rho/world evaluations; excludes raw loading, scoring, compression, and shared design optimization. Not operational deployment cost. All arithmetic checked against saved outputs.')
(ROOT/'timing.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
