"""Run the frozen historical-evidence bridge workflow without precision stopping."""
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
from atlas_new.historical_bridge_workflow import METHODS,REFERENCE,make_plans,public_state,sample_design_worlds

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

def summarize(frame):
    summary=[]
    for (did,method,budget),group in frame.groupby(['design_id','method','new_budget']):
        row=dict(design_id=int(did),method=method,new_budget=int(budget),n_worlds=len(group),
            role=group.role.iloc[0],history_observations=int(group.history_observations.iloc[0]),
            width=float(group.width.iloc[0]),history_width=float(group.history_width.iloc[0]),
            width_reduction_fraction=float(group.width_reduction_fraction.iloc[0]),
            mae=float(group.absolute_error.mean()),rmse=float(np.sqrt(group.squared_error.mean())),
            mean_absolute_point_difference=float(group.absolute_point_difference.mean()),
            rms_point_difference=float(np.sqrt(group.squared_point_difference.mean())))
        events=['covered','scientific_error','ci_decisive','ci_direction_wrong','within_reference_threshold',
                'ci_sign_agreement','reference_decisive','both_decisive','decisive_same_direction','decisive_opposite_direction']
        for event in events:
            k=int(group[event].sum());row[event+'_count']=k;row[event+'_rate']=k/len(group)
            row[event+'_wilson_low'],row[event+'_wilson_high']=wilson(k,len(group))
        summary.append(row)
    return summary

def frame_checks(frame,cfg,n_worlds):
    method=frame[frame.role=='fixed_budget_method'];ref=frame[frame.role=='reference']
    sign=np.where(frame.lower>0,1,np.where(frame.upper<0,-1,0))
    threshold=cfg['point_difference_threshold']
    return dict(
        endpoint_count=len(frame)==n_worlds*(len(METHODS)*len(cfg['budgets'])+1),
        no_duplicate_endpoints=not frame.duplicated(['design_id','replicate','method','new_budget']).any(),
        finite_outputs=bool(np.isfinite(frame[['estimate','truth','W','radius','width','reference_estimate']]).all().all()),
        primitive_W_equals_q=bool(np.allclose(frame.W,frame.q,atol=1e-12,rtol=1e-9)),
        radius_budget=bool(np.allclose(frame.radius**2*cfg['failure_probability'],frame.W)),
        coverage_event=bool(frame.covered.eq(frame.truth.between(frame.lower,frame.upper)).all()),
        scientific_event=bool(frame.scientific_error.eq(frame.absolute_error.gt(threshold)).all()),
        reference_difference=bool(np.allclose(frame.point_difference,frame.estimate-frame.reference_estimate)),
        reference_threshold=bool(frame.within_reference_threshold.eq(frame.absolute_point_difference.le(threshold)).all()),
        direction_rule=bool(np.array_equal(frame.ci_sign,sign)),
        direction_comparison=bool(frame.ci_sign_agreement.eq(frame.ci_sign.eq(frame.reference_ci_sign)).all()),
        reference_independent_stream=bool(ref.future_stream.eq('reference_future').all() and method.future_stream.eq('policy_future').all()),
        reference_width_bound=bool(ref.width.le(2*np.sqrt(cfg['direct_noise_sd']**2/(cfg['reference_direct_observations']*cfg['failure_probability']))+1e-11).all()),
        same_history_at_zero=bool(method[method.new_budget==0].groupby('replicate').estimate.nunique().eq(1).all()),
        fixed_budgets=sorted(method.new_budget.unique().tolist())==sorted(cfg['budgets']),
        reference_is_own_record=bool(len(ref)==n_worlds and ref.new_budget.eq(cfg['reference_direct_observations']).all()),
        costs_count_history_separately=bool(frame.total_observations.eq(frame.new_budget+cfg['history_studies']).all()))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,required=True)
    ap.add_argument('--profile',choices=['smoke','full'],required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();cfg=json.loads(args.config.read_text(encoding='utf-8'))
    if cfg['reference_noise_stream']!='independent_of_all_policy_future_observations':
        raise AssertionError('Frozen independent reference stream is required')
    if cfg['budgets'][0]!=0 or sorted(set(cfg['budgets']))!=cfg['budgets']:
        raise AssertionError('Budgets must be unique, increasing and begin at history-only zero')
    source=REPO/cfg['archive_path'];archive=json.loads(source.read_text(encoding='utf-8'))
    if digest(source)!=cfg['archive_sha256']:raise AssertionError('Archived inputs differ from frozen protocol')
    profile=cfg['profiles'][args.profile];indices=profile['design_indices'];chosen=[archive[i] for i in indices]
    if any(d['replicate']!=i for d,i in zip(chosen,indices)):raise AssertionError('Archive identifiers changed')
    out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a fresh output directory; preserve prior results')
    out.mkdir(parents=True)
    sources=[Path(__file__),ROOT/'atlas_new/historical_bridge_workflow.py',ROOT/'tests/test_historical_bridge_workflow.py',
             args.config.resolve(),args.config.resolve().with_suffix('.md'),source]
    for p in sources:
        q=out/'source_snapshot'/p.relative_to(REPO);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    manifest=dict(status='running',experiment_id=cfg['experiment_id'],profile=args.profile,
        started_utc=datetime.now(timezone.utc).isoformat(),command=[sys.executable,*sys.argv],
        git_revision=git('rev-parse','HEAD'),git_status=git('status','--short'),config=cfg,
        source_sha256={p.relative_to(REPO).as_posix():digest(p) for p in sources},
        coverage_scope='Pointwise at each fixed budget, jointly over beta and historical/future noise. No conditional posterior, fixed-beta, or whole-path simultaneous claim.',
        cost_scope='New study-level observations; four actual historical observations are separately recorded sunk costs. No participant or monetary conversion.',
        model_scope='Unchanged archived linear designs and known prior/noise moments. Independent standardized t5 primitives; history updates linear estimates, not a claimed non-Gaussian posterior.',
        sampling_scope='History stream shared across methods; policy future same-type/same-visit observations paired. Reference64 future observations independent of all policy future observations; same beta and history only.',
        stopping_scope='No width, direction or outcome stopping. All policy paths reach max frozen budget; reference reaches fixed64.')
    save(out/'run_manifest.json',manifest);save(out/'archive_designs_used.json',chosen)
    streams=CSVStreams(out);start=time.perf_counter();summaries=[];history_designs=[];design_rows=[];check_rows=[]
    aggregate_checks={};world_count=0;endpoint_count=0
    try:
        tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_historical_bridge_workflow.py','-v'],
            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/'test_log.txt').write_text(tests.stdout+tests.stderr,encoding='utf-8')
        if tests.returncode:raise AssertionError('Historical workflow tests failed')
        for index,design in enumerate(chosen,1):
            plans,scores=make_plans(design,cfg);did=design['replicate']
            save(out/f'design_{did:03d}_plans.json',{m:dict(horizon=p['horizon'],history_types=p['history_types'],
                history_counts=p['history_counts'],random_order=p['random_order'],path=[public_state(s) for s in p['path']])
                for m,p in plans.items()})
            h=plans[METHODS[0]]
            history_designs.append(dict(design_id=did,history_types=h['history_types'],history_counts=h['history_counts']))
            streams.write('candidate_scores.csv',scores)
            for method,plan in plans.items():
                path=plan['path']
                streams.write('design_trajectory.csv',[dict(design_id=did,method=method,**{
                    k:v for k,v in public_state(s).items() if k!='weights'}) for s in path])
                budgets=[cfg['reference_direct_observations']] if method==REFERENCE else cfg['budgets']
                for budget in budgets:
                    s=path[budget]
                    design_rows.append(dict(design_id=did,method=method,new_budget=budget,
                        history_observations=cfg['history_studies'],width=s['width'],W=s['W'],
                        history_width=path[0]['width'],width_ratio_to_history=s['width']/path[0]['width']))
                check_rows.append(dict(design_id=did,method=method,
                    fixed_horizon=len(path)==plan['horizon']+1,
                    nonincreasing=all(b['W']<=a['W']+1e-11 for a,b in zip(path,path[1:])),
                    observations_count=all(sum(s['future_counts'])==s['stage'] and
                        sum(s['total_counts'])==cfg['history_studies']+s['stage'] for s in path)))
            rows,stats,histories,traces,ledger=sample_design_worlds(design,cfg,plans,profile['seed'],profile['worlds_per_design'])
            streams.write('budget_records.csv',rows);streams.write('prefix_type_stats.csv',stats)
            streams.write('history_observations.csv',histories)
            streams.write('single_world_trace.csv',traces);streams.write('single_world_observations.csv',ledger)
            frame=pd.DataFrame(rows);checks=frame_checks(frame,cfg,profile['worlds_per_design'])
            if not all(checks.values()):raise AssertionError(dict(design_id=did,checks=checks))
            for k,v in checks.items():aggregate_checks[k]=aggregate_checks.get(k,True) and v
            summaries.extend(summarize(frame));world_count+=profile['worlds_per_design'];endpoint_count+=len(rows)
            if index%10==0 or index==len(chosen):
                print(f'Designs {index}/{len(chosen)}; worlds {world_count}; elapsed {time.perf_counter()-start:.1f}s',flush=True)
        streams.close();save(out/'history_designs.json',history_designs)
        pd.DataFrame(summaries).to_csv(out/'per_design_summary.csv',index=False,float_format='%.17g')
        pd.DataFrame(design_rows).to_csv(out/'design_budget_summary.csv',index=False,float_format='%.17g')
        pd.DataFrame(check_rows).to_csv(out/'design_checks.csv',index=False)
        aggregate_checks.update(all_design_checks=all(all(r[k] for k in ['fixed_horizon','nonincreasing','observations_count']) for r in check_rows),
            archive_unchanged=digest(source)==cfg['archive_sha256'])
        if not all(aggregate_checks.values()):raise AssertionError(aggregate_checks)
        manifest.update(status='complete',checks=aggregate_checks,counts=dict(designs=len(chosen),worlds=world_count,
            endpoints=endpoint_count,file_rows=streams.counts))
    except Exception as exc:manifest.update(status='failed',error=repr(exc));raise
    finally:
        streams.close();manifest.update(elapsed_seconds=time.perf_counter()-start,finished_utc=datetime.now(timezone.utc).isoformat(),
            artifact_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='run_manifest.json'})
        save(out/'run_manifest.json',manifest)

if __name__=='__main__':main()
