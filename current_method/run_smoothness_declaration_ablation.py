"""Run five frozen smoothness declarations on shared general-workflow data."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[name]='1'
import argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import importlib.metadata
from itertools import product
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import numpy as np
import pandas as pd
from atlas_new.smoothness_declaration_ablation import run_world,VARIANTS,MODES,FACTORS
from run_mechanism_uncertainty_ablation import Streams,digest,save,git

ROOT=Path(__file__).resolve().parent;REPO=ROOT.parent

def validate_world(cfg,result):
    fixed,stopped,same,plans,designs,observations,audit=result
    f=pd.DataFrame(fixed);s=pd.DataFrame(stopped);samef=pd.DataFrame(same)
    checks=dict(counts=len(f)==40 and len(s)==80 and len(same)==40 and len(plans)==40 and len(observations)==7,
        fixed_unique=not f.duplicated(['variant','mode','stage']).any(),
        stopped_unique=not s.duplicated(['variant','mode','tolerance','budget']).any(),
        finite_certificates=bool(np.isfinite(f[['radius','estimate','causal_error','sampling_error']]).all().all()),
        component_sum=bool(np.allclose(f.radius,f.geometry_min+f.noise,atol=1e-11)),
        error_decomposition=bool(np.allclose(f.error,f.causal_error+f.sampling_error,atol=cfg.get('causal_check_tolerance',1e-10))),
        fixed_coverage=bool(f.certificate_covered.eq(f.truth.between(f.certificate_lower,f.certificate_upper)).all()),
        stopped_coverage=bool(s.covered.eq(s.truth.between(s.lower,s.upper)).all()),
        bad_release=bool(s.bad_release.eq(s.released & s.absolute_error.gt(s.tolerance)).all()),
        declaration_validity=bool(f.guarantee_applicable.eq(f.declared_L_valid & f.declared_H_valid).all()),
        nominal_labels=bool(f.loc[f.guarantee_applicable,'nominal_path_failure_bound'].eq(.1).all() and
                            f.loc[~f.guarantee_applicable,'nominal_path_failure_bound'].isna().all()),
        refusal_needs_L_only=bool(f.refusal_bound_valid.eq(f.declared_L_valid).all()),
        returned_validity=bool(s.returned_output_bound_valid.eq(np.where(s.released,s.selected_bound_valid,s.refusal_bound_valid)).all()),
        valid_geometry_covers_causal=bool((~f.loc[f.smoothness_declaration_valid & f.mechanism_event_holds,'causal_exceeds_declared_geometry_tolerant']).all()),
        simplex=all(min(p['weights'])>=0 and abs(sum(p['weights'])-1)<1e-8 for p in plans),
        shared_prefixes=all(len({tuple(p['ids']) for p in plans if p['stage']==stage})==1 for stage in range(4)),
        common_cost=sorted(o['n'] for o in observations)==sorted([800]*4+[96]*3),
        stopped_cost=bool(s.actual_new_n.eq(s.actual_stage*96).all()))
    for mode in MODES:
        for stage in range(4):
            rows={r['variant']:r for r in same if r['mode']==mode and r['stage']==stage}
            baseline=rows['baseline']
            checks['same_weight_identity']=checks.get('same_weight_identity',True) and all(
                r['weights']==baseline['weights'] and r['source_ids']==baseline['source_ids'] and r['noise']==baseline['noise'] for r in rows.values())
            for component in ['Bbar','BLip','geometry_min']:
                checks['same_weight_L_monotonicity']=checks.get('same_weight_L_monotonicity',True) and (
                    rows['L_half'][component]<=baseline[component]+1e-11 and baseline[component]<=rows['L_double'][component]+1e-11)
            for component in ['Bbar','geometry_min']:
                checks['same_weight_H_monotonicity']=checks.get('same_weight_H_monotonicity',True) and (
                    rows['H_zero'][component]<=baseline[component]+1e-11 and baseline[component]<=rows['H_double'][component]+1e-11)
            checks['H_does_not_enter_BLip']=checks.get('H_does_not_enter_BLip',True) and (
                rows['H_zero']['BLip']==baseline['BLip']==rows['H_double']['BLip'])
            ff=f[(f['mode']==mode)&(f.stage==stage)].set_index('variant')
            checks['H_does_not_enter_refusal']=checks.get('H_does_not_enter_refusal',True) and all(
                ff.loc['baseline',key]==ff.loc['H_zero',key]==ff.loc['H_double',key] for key in ['refusal_lower','refusal_upper'])
        for variant in VARIANTS:
            ff=f[(f.variant==variant)&(f['mode']==mode)].sort_values('stage')
            checks['monotone_radius']=checks.get('monotone_radius',True) and bool(np.all(np.diff(ff.radius)<=1e-8))
            for tolerance in cfg['tolerances']:
                ss=s[(s.variant==variant)&(s['mode']==mode)&(s.tolerance==tolerance)]
                hits=ff[ff.radius<=tolerance];stop=int(hits.stage.iloc[0]) if len(hits) else 3
                checks['first_release_and_carry']=checks.get('first_release_and_carry',True) and all(
                    r.actual_stage==min(r.budget,stop) for r in ss.itertuples())
    if not all(checks.values()):raise AssertionError(checks)
    return checks

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True);parser.add_argument('--profile',choices=['smoke','full'],required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    protocol=json.loads(args.config.read_text(encoding='utf-8'));cfg=dict(protocol,**protocol['profiles'][args.profile])
    if tuple(cfg['variants'])!=VARIANTS or tuple(cfg['bound_modes'])!=MODES:raise AssertionError('Frozen groups changed')
    assert cfg['max_bridges']==3 and cfg['archive_participants']==800 and cfg['participants_per_bridge']==96
    out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a fresh directory; preserve previous results')
    out.mkdir(parents=True)
    sources=[Path(__file__),ROOT/'atlas_new/smoothness_declaration_ablation.py',ROOT/'tests/test_smoothness_declaration_ablation.py',
        ROOT/'run_mechanism_uncertainty_ablation.py',ROOT/'atlas_new/mechanism_uncertainty_ablation.py',
        ROOT/'atlas_new/workflow.py',ROOT/'atlas_new/core.py',ROOT/'configs/workflow_full.json',
        args.config.resolve(),args.config.resolve().with_suffix('.md')]
    for p in sources:
        dest=out/'source_snapshot'/p.relative_to(REPO);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    manifest=dict(status='running',experiment_id=cfg['experiment_id'],profile=args.profile,config=cfg,
        command=[sys.executable,*sys.argv],git_revision=git('rev-parse','HEAD'),git_status=git('status','--short'),
        python=sys.version,platform=platform.platform(),packages={n:importlib.metadata.version(n) for n in ['numpy','scipy','pandas']},
        started_utc=datetime.now(timezone.utc).isoformat(),source_sha256={p.relative_to(REPO).as_posix():digest(p) for p in sources},
        scope='Five one-factor L/H declarations on original general U/L/H workflow, shared calibrated sets, fixed random prefixes and actual observations. No new linear-W theorem or real-data fitting.',
        coverage_scope='Nominal policy guarantee only for globally valid declared L and H. Branch-specific strict validity and numerical near-ties are diagnostic; no conditional-on-release guarantee.',
        output_scope='Fixed-budget certificates separate from stopped-policy outputs reconstructed from common observed prefixes. Refusal uses declared L; H is absent.',
        truth_scope='True source and target effects used only in post-plan error decomposition/scoring; never supplied to weight optimizer.',
        optimization_scope='Unchanged original multi-start feasible SLSQP; no global reoptimized ordering asserted.')
    save(out/'run_manifest.json',manifest);streams=Streams(out);started=time.perf_counter();checks={};completed=0
    try:
        test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_smoothness_declaration_ablation.py','-v'],
            cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (out/'test_log.txt').write_text(test.stdout+test.stderr,encoding='utf-8')
        if test.returncode:raise AssertionError('Smoothness ablation tests failed')
        tasks=[(cfg,s,g,r) for s,g,r in product(range(len(cfg['surfaces'])),range(len(cfg['scenarios'])),range(cfg['repetitions_per_cell']))]
        with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:
            futures=[pool.submit(run_world,t) for t in tasks]
            for future in as_completed(futures):
                result=future.result();local=validate_world(cfg,result)
                for k,v in local.items():checks[k]=checks.get(k,True) and v
                fixed,stopped,same,plans,designs,obs,audit=result
                for name,rows in [('fixed_certificate_records.csv',fixed),('stopped_output_records.csv',stopped),
                                  ('same_weight_diagnostics.csv',same),('common_observations.csv',obs)]:streams.rows(name,rows)
                for name,rows in [('design_plans.jsonl',plans),('variant_designs.jsonl',designs),('world_audits.jsonl',[audit])]:streams.objects(name,rows)
                completed+=1
                if completed%25==0 or completed==len(tasks):print(f'Worlds {completed}/{len(tasks)}; elapsed {time.perf_counter()-started:.1f}s',flush=True)
        checks['source_files_unchanged']=all(digest(p)==manifest['source_sha256'][p.relative_to(REPO).as_posix()] for p in sources)
        if not all(checks.values()):raise AssertionError(checks)
        manifest.update(status='complete',checks=checks,counts=dict(worlds=completed,file_rows=streams.counts))
    except Exception as exc:manifest.update(status='failed',error=repr(exc));raise
    finally:
        streams.close();manifest.update(finished_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-started,
            artifact_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='run_manifest.json'})
        save(out/'run_manifest.json',manifest)

if __name__=='__main__':main()
