"""Execute the frozen matched mechanism-information ablation in fresh outputs."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[name]='1'
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import csv
from datetime import datetime,timezone
import hashlib
import importlib.metadata
from itertools import product
import json
from pathlib import Path
import shutil
import platform
import subprocess
import sys
import time
import numpy as np
import pandas as pd
from atlas_new.mechanism_uncertainty_ablation import run_world,VARIANTS,MODES

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def git(*args):
    p=subprocess.run(['git',*args],cwd=REPO,capture_output=True,text=True,encoding='utf-8',errors='replace')
    return p.stdout.strip() if p.returncode==0 else None

class Streams:
    def __init__(self,out):self.out=out;self.csv={};self.json={};self.counts={}
    def rows(self,name,rows):
        if not rows:return
        if name not in self.csv:
            f=(self.out/name).open('w',encoding='utf-8',newline='');writer=csv.DictWriter(f,fieldnames=list(rows[0]))
            writer.writeheader();self.csv[name]=(f,writer);self.counts[name]=0
        f,writer=self.csv[name]
        for row in rows:
            writer.writerow({k:json.dumps(v,separators=(',',':')) if isinstance(v,(list,dict)) else
                format(v,'.17g') if isinstance(v,float) else v for k,v in row.items()})
        f.flush();self.counts[name]+=len(rows)
    def objects(self,name,rows):
        if name not in self.json:self.json[name]=(self.out/name).open('w',encoding='utf-8');self.counts[name]=0
        for row in rows:self.json[name].write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')
        self.json[name].flush();self.counts[name]+=len(rows)
    def close(self):
        for f,w in self.csv.values():f.close()
        for f in self.json.values():f.close()

def validate_world(cfg,result):
    fixed,stopped,same,plans,designs,observations,audit=result
    f=pd.DataFrame(fixed);s=pd.DataFrame(stopped)
    group=['variant','mode'];negative=f.variant.eq('proxy_point')
    checks=dict(
        counts=len(f)==24 and len(s)==48 and len(plans)==24 and len(same)==24 and len(observations)==7,
        fixed_unique=not f.duplicated(group+['stage']).any(),
        stopped_unique=not s.duplicated(group+['tolerance','budget']).any(),
        finite_certificates=bool(np.isfinite(f[['radius','estimate','certificate_lower','certificate_upper']]).all().all()),
        component_sum=bool(np.allclose(f.radius,f.geometry_min+f.noise,atol=1e-11,rtol=1e-10)),
        fixed_coverage=bool(f.certificate_covered.eq(f.truth.between(f.certificate_lower,f.certificate_upper)).all()),
        stopped_coverage=bool(s.covered.eq(s.truth.between(s.lower,s.upper)).all()),
        bad_release=bool(s.bad_release.eq(s.released & s.absolute_error.gt(s.tolerance)).all()),
        invalid_labels=bool((~f.loc[negative,'guarantee_applicable']).all() and f.loc[negative,'nominal_path_failure_bound'].isna().all()),
        valid_labels=bool(f.loc[~negative,'guarantee_applicable'].all()),
        nonnegative_simplex=all(min(p['weights'])>=0 and abs(sum(p['weights'])-1)<1e-8 for p in plans),
        shared_prefixes=all(len({tuple(p['ids']) for p in plans if p['stage']==stage})==1 for stage in range(4)),
        common_observation_cost=sorted(o['n'] for o in observations)==sorted([800]*4+[96]*3),
        stopped_cost=bool(s.actual_new_n.eq(s.actual_stage*cfg['participants_per_bridge']).all()),
        refusal_status=bool(f.refusal_status.eq(np.where(f.refusal_lower<=f.refusal_upper,'finite','inconsistent')).all()))
    for variant in VARIANTS:
        for mode in MODES:
            ff=f[(f.variant==variant)&(f['mode']==mode)].sort_values('stage')
            checks['monotone_radius']=checks.get('monotone_radius',True) and bool(np.all(np.diff(ff.radius)<=1e-8))
            for tolerance in cfg['tolerances']:
                ss=s[(s.variant==variant)&(s['mode']==mode)&(s.tolerance==tolerance)].sort_values('budget')
                hits=ff[ff.radius<=tolerance]
                stop=int(hits.stage.iloc[0]) if len(hits) else cfg['max_bridges']
                checks['first_release_and_carry']=checks.get('first_release_and_carry',True) and all(
                    r.actual_stage==min(r.budget,stop) for r in ss.itertuples())
    if not all(checks.values()):raise AssertionError(checks)
    return checks

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--profile',choices=['smoke','full'],required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    protocol=json.loads(args.config.read_text(encoding='utf-8'));cfg=dict(protocol,**protocol['profiles'][args.profile])
    if tuple(cfg['variants'])!=VARIANTS or tuple(cfg['bound_modes'])!=MODES:raise AssertionError('Frozen variants/modes changed')
    assert cfg['max_bridges']==3 and cfg['archive_participants']==800 and cfg['participants_per_bridge']==96
    out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a new directory; preserve prior results')
    out.mkdir(parents=True)
    sources=[Path(__file__),ROOT/'atlas_new/mechanism_uncertainty_ablation.py',ROOT/'tests/test_mechanism_uncertainty_ablation.py',
        ROOT/'atlas_new/workflow.py',ROOT/'atlas_new/core.py',ROOT/'configs/workflow_full.json',
        args.config.resolve(),args.config.resolve().with_suffix('.md')]
    for p in sources:
        dest=out/'source_snapshot'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    manifest=dict(status='running',experiment_id=cfg['experiment_id'],profile=args.profile,config=cfg,
        command=[sys.executable,*sys.argv],git_revision=git('rev-parse','HEAD'),git_status=git('status','--short'),
        python=sys.version,platform=platform.platform(),
        packages={name:importlib.metadata.version(name) for name in ['numpy','scipy','pandas']},
        started_utc=datetime.now(timezone.utc).isoformat(),source_sha256={p.relative_to(REPO).as_posix():digest(p) for p in sources},
        scope='Original general U/L/H simulator. Matched fixed random source prefix, common actual Gaussian two-arm observations, unchanged L/H.',
        information_scope='Proxy points are an invalid negative control; oracle exact locations are extra information. No true locations enter calibrated/proxy planning.',
        output_scope='Fixed-budget certificate/refusal endpoints are separate from stopped-policy outputs reconstructed from the same sampled prefixes, without resampling or using post-stop observations.',
        coverage_scope='Original finite-horizon multipliers retained. Calibrated sets have eta+zeta path failure budget; oracle zeta with same multipliers; proxy has no nominal guarantee.',
        optimization_scope='Original multi-start feasible SLSQP, not certified global optimization.')
    save(out/'run_manifest.json',manifest);streams=Streams(out);started=time.perf_counter();checks={};completed=0
    try:
        test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_mechanism_uncertainty_ablation.py','-v'],
            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/'test_log.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
        if test.returncode:raise AssertionError('Mechanism ablation tests failed')
        tasks=[(cfg,s,g,r) for s,g,r in product(range(len(cfg['surfaces'])),range(len(cfg['scenarios'])),range(cfg['repetitions_per_cell']))]
        with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:
            pending=[pool.submit(run_world,t) for t in tasks]
            for future in as_completed(pending):
                result=future.result();local=validate_world(cfg,result)
                for k,v in local.items():checks[k]=checks.get(k,True) and v
                fixed,stopped,same,plans,designs,observations,audit=result
                streams.rows('fixed_certificate_records.csv',fixed);streams.rows('stopped_output_records.csv',stopped)
                streams.rows('same_weight_diagnostics.csv',same);streams.rows('common_observations.csv',observations)
                streams.objects('design_plans.jsonl',plans);streams.objects('variant_designs.jsonl',designs)
                streams.objects('world_audits.jsonl',[audit]);completed+=1
                if completed%25==0 or completed==len(tasks):
                    print(f'Worlds {completed}/{len(tasks)}; elapsed {time.perf_counter()-started:.1f}s',flush=True)
        checks['source_files_unchanged']=all(digest(p)==manifest['source_sha256'][p.relative_to(REPO).as_posix()] for p in sources)
        if not all(checks.values()):raise AssertionError(checks)
        manifest.update(status='complete',checks=checks,counts=dict(worlds=completed,file_rows=streams.counts))
    except Exception as exc:manifest.update(status='failed',error=repr(exc));raise
    finally:
        streams.close();manifest.update(finished_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-started,
            artifact_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='run_manifest.json'})
        save(out/'run_manifest.json',manifest)

if __name__=='__main__':main()
