"""Run the frozen main-theorem workflow on unchanged archived designs."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[name]='1'
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
import pandas as pd
from atlas_new.main_theorem_workflow import METHODS,make_plans,public_state,sample_design_worlds

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def git(*args):
    p=subprocess.run(['git',*args],cwd=REPO,capture_output=True,text=True,encoding='utf-8',errors='replace')
    return p.stdout.strip() if p.returncode==0 else None
def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,float(mid-half)),min(1.,float(mid+half))

class CSVStreams:
    def __init__(self,out):self.out=out;self.streams={};self.counts={}
    def write(self,name,rows):
        if not rows:return
        if name not in self.streams:
            h=(self.out/name).open('w',newline='',encoding='utf-8');w=csv.DictWriter(h,fieldnames=list(rows[0]))
            w.writeheader();self.streams[name]=(h,w);self.counts[name]=0
        h,w=self.streams[name]
        for row in rows:
            w.writerow({k:json.dumps(v,separators=(',',':')) if isinstance(v,(list,dict)) else
                        format(v,'.17g') if isinstance(v,float) else v for k,v in row.items()})
        h.flush();self.counts[name]+=len(rows)
    def close(self):
        for h,w in self.streams.values():h.close()

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,required=True)
    ap.add_argument('--profile',choices=['smoke','full'],required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();cfg=json.loads(args.config.read_text(encoding='utf-8'))
    source=REPO/cfg['archive_path'];archive=json.loads(source.read_text(encoding='utf-8'))
    if digest(source)!=cfg['archive_sha256']:raise AssertionError('Archived designs differ from frozen protocol')
    profile=cfg['profiles'][args.profile];indices=profile['design_indices']
    chosen=[archive[i] for i in indices]
    if any(d['replicate']!=i for d,i in zip(chosen,indices)):raise AssertionError('Archive design identifiers changed')
    out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a fresh output directory; preserve prior results')
    out.mkdir(parents=True)
    sources=[Path(__file__),ROOT/'atlas_new/main_theorem_workflow.py',ROOT/'tests/test_main_theorem_workflow.py',
             args.config.resolve(),args.config.resolve().with_suffix('.md'),source]
    for p in sources:
        q=out/'source_snapshot'/p.relative_to(REPO);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    manifest=dict(status='running',experiment_id=cfg['experiment_id'],profile=args.profile,
        started_utc=datetime.now(timezone.utc).isoformat(),command=[sys.executable,*sys.argv],
        git_revision=git('rev-parse','HEAD'),git_status=git('status','--short'),config=cfg,
        source_sha256={p.relative_to(REPO).as_posix():digest(p) for p in sources},
        coverage_scope='Marginal over random beta and independent errors; pointwise at the design-only terminal step. No conditional posterior, fixed-beta, or whole-path simultaneous claim.',
        cost_scope='Study-level observations with archived sigma=.5, not participant counts or monetary costs.',
        model_scope='Fixed linear model, exact archived prior moments and designs; standardized Student-t5 parameter primitives and errors. No selected stress geometries.',
        sampling_scope='Same type and visit paired across methods; different visits and parameter/noise streams independent. One actual t5 noise draw per study-level observation.')
    save(out/'run_manifest.json',manifest);save(out/'archive_designs_used.json',chosen)
    streams=CSVStreams(out);start=time.perf_counter();endpoint_rows=[];design_summary=[];check_rows=[]
    try:
        tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_main_theorem_workflow.py','-v'],
            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/'test_log.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
        if tests.returncode:raise AssertionError('Main workflow implementation tests failed')
        for index,design in enumerate(chosen,1):
            plans,scores=make_plans(design,cfg);identifier=design['replicate']
            save(out/f'design_{identifier:03d}_plans.json',
                {m:dict(stop_stage=p['stop_stage'],attained=p['attained'],random_order=p['random_order'],
                        path=[public_state(s) for s in p['path']]) for m,p in plans.items()})
            streams.write('candidate_scores.csv',scores)
            for method,plan in plans.items():
                path=plan['path'];end=path[-1]
                streams.write('design_trajectory.csv',[dict(design_id=identifier,method=method,**{
                    k:v for k,v in public_state(s).items() if k not in ['weights']}) for s in path])
                design_summary.append(dict(design_id=identifier,method=method,study_observations=plan['stop_stage'],
                    attained=plan['attained'],width=end['width'],radius=end['radius'],W=end['W'],
                    before_stop_width=path[-2]['width'] if len(path)>1 else None))
                check_rows.append(dict(design_id=identifier,method=method,
                    first_hit=not plan['attained'] or all(s['radius']>cfg['scientific_halfwidth'] for s in path[:-1]),
                    nonincreasing=all(b['W']<=a['W']+1e-11 for a,b in zip(path,path[1:])),
                    observations_count=all(sum(s['counts'])==s['stage'] for s in path)))
            rows,stats,traces,ledger=sample_design_worlds(design,cfg,plans,profile['seed'],profile['worlds_per_design'])
            streams.write('terminal_records.csv',rows);streams.write('final_type_stats.csv',stats)
            streams.write('single_world_trace.csv',traces);streams.write('single_world_observations.csv',ledger)
            endpoint_rows.extend(rows)
            print(f'Designs {index}/{len(chosen)}; worlds {index*profile["worlds_per_design"]}; elapsed {time.perf_counter()-start:.1f}s',flush=True)
        streams.close()
        frame=pd.DataFrame(endpoint_rows);summary=[]
        for (design_id,method),group in frame.groupby(['design_id','method']):
            row=dict(design_id=int(design_id),method=method,n_worlds=len(group),
                study_observations=int(group.study_observations.iloc[0]),width=float(group.width.iloc[0]),
                attained=bool(group.attained.iloc[0]),mae=float(group.absolute_error.mean()),rmse=float(np.sqrt(group.squared_error.mean())))
            for event in ['covered','interval_miss_on_release','bad_release_scientific']:
                k=int(group[event].sum());row[event+'_count']=k;row[event+'_rate']=k/len(group)
                row[event+'_wilson_low'],row[event+'_wilson_high']=wilson(k,len(group))
            summary.append(row)
        pd.DataFrame(summary).to_csv(out/'per_design_summary.csv',index=False,float_format='%.17g')
        pd.DataFrame(design_summary).to_csv(out/'design_stop_summary.csv',index=False,float_format='%.17g')
        pd.DataFrame(check_rows).to_csv(out/'design_checks.csv',index=False)
        checks=dict(endpoint_count=len(frame)==len(chosen)*profile['worlds_per_design']*len(METHODS),
            no_duplicate_endpoints=not frame.duplicated(['design_id','replicate','method']).any(),
            finite_outputs=bool(np.isfinite(frame[['estimate','truth','W','radius','width']]).all().all()),
            primitive_W_equals_q=bool(np.allclose(frame.W,frame.q,atol=1e-12,rtol=1e-9)),
            radius_budget=bool(np.allclose(frame.radius**2*cfg['failure_probability'],frame.W)),
            coverage_event=bool(frame.covered.eq(frame.truth.between(frame.lower,frame.upper)).all()),
            scientific_event=bool(frame.bad_release_scientific.eq(frame.attained & frame.absolute_error.gt(cfg['scientific_halfwidth'])).all()),
            same_design_cost_for_all_worlds=bool(frame.groupby(['design_id','method']).study_observations.nunique().eq(1).all()),
            all_design_checks=all(all(r[k] for k in ['first_hit','nonincreasing','observations_count']) for r in check_rows),
            archive_unchanged=digest(source)==cfg['archive_sha256'])
        if not all(checks.values()):raise AssertionError(checks)
        manifest.update(status='complete',checks=checks,counts=dict(designs=len(chosen),
            worlds=len(chosen)*profile['worlds_per_design'],endpoints=len(frame),file_rows=streams.counts),
            all_plans_attained=bool(frame.attained.all()))
    except Exception as exc:manifest.update(status='failed',error=repr(exc));raise
    finally:
        streams.close();manifest.update(elapsed_seconds=time.perf_counter()-start,finished_utc=datetime.now(timezone.utc).isoformat(),
            artifact_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='run_manifest.json'})
        save(out/'run_manifest.json',manifest)

if __name__=='__main__':main()
