"""Run the frozen independent experiment suite from any working directory."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from atlas_new import experiments, manylabs, report

ROOT=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['smoke','full'],default='full')
    parser.add_argument('--skip-real',action='store_true',help='Explicitly mark real-data module not run')
    args=parser.parse_args();cfg=json.loads((ROOT/'configs'/f'{args.profile}.json').read_text())
    output_name=args.profile+('_synthetic_only' if args.skip_real else '')
    out=ROOT/'results'/output_name;out.mkdir(parents=True,exist_ok=True)
    data=ROOT/'data';data.mkdir(exist_ok=True)
    source_files=[p for p in ROOT.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.md','.txt']
                  and not any(x in p.relative_to(ROOT).parts for x in ['results','data','__pycache__'])]
    manifest=dict(started_utc=datetime.now(timezone.utc).isoformat(),command=sys.argv,
        python=sys.version,platform=platform.platform(),config=cfg,status='running',
        source_sha256={str(p.relative_to(ROOT)):digest(p) for p in source_files},
        packages={x:importlib.metadata.version(x) for x in ['numpy','scipy','pandas','matplotlib']},
        blocks={},scope='Independent implementation; not a claim of bitwise manuscript reproduction')
    manifest_path=out/'run_manifest.json'
    if manifest_path.exists():
        history=ROOT/'results'/'run_history';history.mkdir(exist_ok=True)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
        (history/f'{output_name}_{stamp}.json').write_bytes(manifest_path.read_bytes())
    def checkpoint():manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    checkpoint()
    try:
        # Statistical assertions and solver tests are essential to this numerical implementation.
        test=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],cwd=ROOT,
                            capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/'test_log.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
        if test.returncode:raise RuntimeError('Unit tests failed; see test_log.txt')
        for name,fun in [('hidden',experiments.hidden),('selection',experiments.selection),
                         ('minimax',experiments.minimax),('joint_calibration',experiments.joint_calibration),
                         ('operational',experiments.operational),('sharp_pi',experiments.pi_audit),('bridges',experiments.bridges)]:
            print(f'START {name}',flush=True);start=time.perf_counter();fun(cfg,out)
            manifest['blocks'][name]=dict(status='complete',seconds=time.perf_counter()-start);checkpoint()
            print(f'DONE {name} {manifest["blocks"][name]["seconds"]:.2f}s',flush=True)
        if not args.skip_real:
            print('START manylabs',flush=True);start=time.perf_counter();manylabs.run(cfg,out,data)
            manifest['blocks']['manylabs']=dict(status='complete',seconds=time.perf_counter()-start,
                                               sha256=manylabs.SHA256);checkpoint()
        else:manifest['blocks']['manylabs']=dict(status='not_run',reason='Explicit --skip-real')
        checks=report.validate_results(out)
        report.figures(out);report.write_report(cfg,out)
        manifest['status']='complete';manifest['validation_checks_passed']=len(checks)
    except Exception as error:
        manifest['status']='failed';manifest['error']=repr(error);checkpoint();raise
    finally:
        manifest['finished_utc']=datetime.now(timezone.utc).isoformat()
        manifest['artifacts']={str(p.relative_to(ROOT)):dict(sha256=digest(p),bytes=p.stat().st_size)
            for p in out.rglob('*') if p.is_file() and p!=manifest_path}
        checkpoint()
    print(f'COMPLETE {out}',flush=True)


if __name__=='__main__':main()
