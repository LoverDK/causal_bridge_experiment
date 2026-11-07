"""Analyze saved cost/precision runs without calling the simulator."""
import os
for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[variable]='1'
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import time

from atlas_new.cost_precision_report import analyze,ANALYSIS_SEED

ROOT=Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    source=args.input.resolve();out=(args.output or source/'analysis').resolve()
    if out.exists():raise FileExistsError(f'Choose a new analysis directory: {out}')
    raw_manifest=json.loads((source/'run_manifest.json').read_text(encoding='utf-8'))
    if raw_manifest.get('status')!='complete':raise ValueError('Raw run is not complete')
    out.mkdir(parents=True)
    files=[Path(__file__),ROOT/'atlas_new/cost_precision_report.py']
    start=time.perf_counter()
    manifest={'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),
        'command':sys.argv,'input_directory':str(source),'analysis_seed':ANALYSIS_SEED,
        'config':raw_manifest['config'],'scope':'Saved-data analysis; no new simulation; pointwise paired bootstrap CIs, not familywise claims',
        'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in files},
        'input_sha256':{p.name:digest(p) for p in [source/'prefix_records.csv',source/'stopped_records.csv',source/'run_manifest.json']},
        'packages':{n:importlib.metadata.version(n) for n in ['numpy','pandas','matplotlib']}}
    try:
        manifest['git_revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except (OSError,subprocess.CalledProcessError):manifest['git_revision']=None
    path=out/'analysis_manifest.json'
    path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    try:
        manifest['counts']=analyze(raw_manifest['config'],source,out)
        manifest['status']='complete'
    except Exception as exc:
        manifest['status']='failed';manifest['error']=repr(exc)
        raise
    finally:
        manifest['finished_utc']=datetime.now(timezone.utc).isoformat()
        manifest['elapsed_seconds']=time.perf_counter()-start
        manifest['artifacts']={str(p.relative_to(out)):{'sha256':digest(p),'bytes':p.stat().st_size}
            for p in out.rglob('*') if p.is_file() and p!=path}
        path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('COMPLETE',out,flush=True)


if __name__=='__main__':main()
