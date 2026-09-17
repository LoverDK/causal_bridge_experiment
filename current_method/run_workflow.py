"""Run the frozen finite-horizon workflow experiment without touching old results."""
import os
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[variable]='1'
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import pandas as pd
from atlas_new.workflow import run_world, tasks
from atlas_new.workflow_report import validate, summarize, figures, report

ROOT=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',choices=['workflow_smoke','workflow_full'],default='workflow_full')
    parser.add_argument('--workers',type=int,default=None)
    args=parser.parse_args()
    cfg=json.loads((ROOT/'configs'/f'{args.profile}.json').read_text(encoding='utf-8'))
    if args.workers is not None:cfg['workers']=args.workers
    assert cfg['dimension']==2 and cfg['initial_sources']==4 and cfg['candidate_bridges']==6
    assert cfg['workers']>=1 and 0<cfg['max_bridges']<=6
    out=ROOT/'results'/args.profile
    if out.exists() and (out/'run_manifest.json').exists():
        raise FileExistsError('Preserve previous run: move its exact directory to a versioned archive before rerunning.')
    out.mkdir(parents=True,exist_ok=True)
    files=[ROOT/'run_workflow.py',ROOT/'atlas_new'/'workflow.py',ROOT/'atlas_new'/'workflow_report.py',
           ROOT/'atlas_new'/'core.py',ROOT/'atlas_new'/'experiments.py',ROOT/'atlas_new'/'report.py',
           ROOT/'configs'/f'{args.profile}.json',ROOT/'docs'/'完整流程实验协议.md',ROOT/'tests'/'test_workflow.py']
    manifest=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),command=sys.argv,
        config=cfg,python=sys.version,platform=platform.platform(),
        packages={name:importlib.metadata.version(name) for name in ['numpy','scipy','pandas','matplotlib']},
        source_sha256={str(p.relative_to(ROOT)):digest(p) for p in files},
        scope='Synthetic complete workflow; not real mechanism-set calibration; no superiority hard-coded.')
    manifest_path=out/'run_manifest.json'
    manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    started=time.perf_counter()
    try:
        test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_workflow.py','-v'],
                            cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace')
        (out/'test_log.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
        if test.returncode:raise AssertionError('Workflow regression tests failed; see test_log.txt')
        jobs=tasks(cfg);rows=[];events=[];plans=[];choices=[];audits=[]
        with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:
            futures=[pool.submit(run_world,job) for job in jobs]
            for n,future in enumerate(as_completed(futures),1):
                a,b,c,d,e=future.result();rows.extend(a);events.extend(b);plans.extend(c);choices.extend(d);audits.append(e)
                if n%25==0 or n==len(jobs):
                    print(f'Worlds {n}/{len(jobs)}; elapsed {time.perf_counter()-started:.1f}s',flush=True)
        order=['surface','scenario','replicate','method','tolerance','budget']
        pd.DataFrame(rows).sort_values(order).to_csv(out/'workflow_records.csv',index=False,float_format='%.15g')
        pd.DataFrame(events).sort_values(order[:-1]+['stage']).to_csv(out/'acquisitions.csv',index=False,float_format='%.15g')
        pd.DataFrame(choices).sort_values(order[:4]+['stage','candidate']).to_csv(out/'candidate_scores.csv',index=False,float_format='%.15g')
        plans.sort(key=lambda p:tuple(p[k] for k in order[:4])+ (p['stage'],))
        audits.sort(key=lambda p:tuple(p[k] for k in order[:3]))
        for filename,records in [('plans.jsonl',plans),('world_audits.jsonl',audits)]:
            (out/filename).write_text(''.join(json.dumps(r,ensure_ascii=False,allow_nan=False)+'\n' for r in records),encoding='utf-8')
        checks=validate(cfg,out);manifest['checks']=checks
        failed=[c['name'] for c in checks if not c['passed']]
        if failed:raise AssertionError('; '.join(failed))
        summarize(cfg,out);figures(cfg,out);report(cfg,out)
        manifest['counts']=dict(independent_worlds=len(audits),policy_budget_records=len(rows),
                                acquisitions_logged=len(events),planned_states=len(plans))
        manifest['status']='complete'
    except Exception as exc:
        manifest['status']='failed';manifest['error']=repr(exc)
        raise
    finally:
        manifest['finished_utc']=datetime.now(timezone.utc).isoformat()
        manifest['elapsed_seconds']=time.perf_counter()-started
        manifest['artifacts']={str(p.relative_to(out)):dict(sha256=digest(p),bytes=p.stat().st_size)
                               for p in out.rglob('*') if p.is_file() and p!=manifest_path}
        manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print('COMPLETE',out,flush=True)


if __name__=='__main__':main()
