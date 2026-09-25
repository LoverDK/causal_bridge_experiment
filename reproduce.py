"""Portable isolated reproduction; never overwrite the published result archive."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent


def restore(folder):
    compressed=folder/'results/ablations_full/plans.jsonl.gz'
    target=compressed.with_suffix('')
    if compressed.exists() and not target.exists():
        with gzip.open(compressed,'rb') as source,target.open('wb') as dest:
            shutil.copyfileobj(source,dest)


def run(cmd,cwd):
    subprocess.run([sys.executable,*map(str,cmd)],cwd=cwd,check=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite',choices=['verify','current','plus','workflow','ablations','audit-ablations','real','calibration','effect-family','effect-family-baselines','effect-family-baselines-corrected','effect-family-baselines-all','original','legacy-nsw','legacy-nsw-real-proxy-truth','legacy-extensions','figures'])
    parser.add_argument('--profile',choices=['smoke','full'],default='smoke')
    parser.add_argument('--output',type=Path,default=ROOT/'reproduced')
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if args.suite=='verify':
        data=json.loads((ROOT/'provenance/release_manifest.json').read_text(encoding='utf-8'))
        failures=[]
        for name,item in data['files'].items():
            p=ROOT/name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:
                failures.append(name)
        if failures:raise AssertionError(f'Hash mismatches: {failures}')
        print('Verified',len(data['files']),'release files')
        return
    out=args.output.resolve()
    if out.exists():
        raise FileExistsError('Choose a new --output directory to preserve previous runs: '+str(out))
    out.mkdir(parents=True)
    if args.suite in ['current','plus','workflow','ablations','real','calibration','effect-family','effect-family-baselines','effect-family-baselines-corrected','effect-family-baselines-all']:
        dest=out/'current_method'
        shutil.copytree(ROOT/'current_method',dest,ignore=shutil.ignore_patterns('results','__pycache__'))
        script={'current':'run_all.py','plus':'run_plus.py','workflow':'run_workflow.py','ablations':'run_ablations.py','real':'run_real_supplement.py','calibration':'run_mechanism_calibration.py','effect-family':'run_effect_family_holdout.py','effect-family-baselines':'run_effect_family_baselines.py','effect-family-baselines-corrected':'run_effect_family_baselines.py','effect-family-baselines-all':'run_effect_family_baselines_all.py'}[args.suite]
        cmd=[script]
        if args.suite not in ['real','calibration','effect-family','effect-family-baselines','effect-family-baselines-corrected','effect-family-baselines-all']:
            profile={'workflow':'workflow_'+args.profile,'plus':args.profile+'_plus'}.get(args.suite,args.profile)
            cmd+=['--profile',profile]
        if args.suite in ['workflow','ablations']:cmd+=['--workers',args.workers]
        if args.suite=='calibration':cmd+=['--output',Path('results')/'mechanism_calibration']
        if args.suite=='effect-family':cmd+=['--output',Path('results')/'effect_family_holdout']
        if args.suite=='effect-family-baselines':cmd+=['--output',Path('results')/'effect_family_baselines']
        if args.suite=='effect-family-baselines-corrected':cmd+=['--output',Path('results')/'effect_family_baselines_corrected']
        if args.suite=='effect-family-baselines-all':cmd+=['--output',Path('results')/'effect_family_baselines_all']
        run(cmd,dest)
    elif args.suite=='audit-ablations':
        dest=out/'current_method'
        shutil.copytree(ROOT/'current_method',dest,ignore=shutil.ignore_patterns('results','__pycache__'))
        for name in ['ablations_full','workflow_full']:
            shutil.copytree(ROOT/'current_method/results'/name,dest/'results'/name)
        restore(dest)
        run(['audit_ablations.py'],dest)
    elif args.suite=='original':
        dest=out/'paper_original'
        dest.mkdir()
        for p in (ROOT/'paper_original').glob('*.py'):shutil.copy2(p,dest/p.name)
        run(['run_operational_experiments.py'],dest)
        run(['run_manylabs2_framing.py','--data',ROOT/'current_method/data/manylabs2_framing.csv','--out-dir',dest/'manylabs'],dest)
    elif args.suite.startswith('legacy'):
        dest=out/'legacy_audits'
        shutil.copytree(ROOT/'legacy_audits',dest,ignore=shutil.ignore_patterns('__pycache__'))
        if args.suite=='legacy-nsw':
            run(['scripts/run/run_nsw_experiment.py'],dest)
        elif args.suite=='legacy-nsw-real-proxy-truth':
            run(['scripts/run/run_nsw_real_proxy_truth.py','--repetitions',100,
                 '--output',Path('results')/'extensions'/'nsw_real_proxy_truth_reproduction'],dest)
        else:
            # The original runner records a git revision; avoid inventing one in a scratch copy.
            script=dest/'scripts/run/run_requested_extensions.py'
            text=script.read_text(encoding='utf-8')
            old="subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()"
            assert old in text
            text=text.replace(old,"'isolated reproduction; see repository release commit'")
            script.write_text(text,encoding='utf-8')
            n=100 if args.profile=='full' else 2
            for block in ['synthetic','nsw','bridge']:
                run([script,block,'--repetitions',n,'--bootstrap',200 if args.profile=='full' else 5,
                     '--bridge-repetitions',12 if args.profile=='full' else 1],dest)
            if args.profile=='full':
                run(['scripts/build/build_extension_artifacts.py'],dest)
    else:
        run([ROOT/'paper_figures/render_appendix_figures.py','--output',out],ROOT)


if __name__=='__main__':main()
