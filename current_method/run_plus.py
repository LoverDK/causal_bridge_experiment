"""Run the independent second-round robustness audits."""
import argparse, hashlib, importlib.metadata, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path
from atlas_new import audit_plus
ROOT=Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--profile',choices=['smoke_plus','full_plus'],default='full_plus');args=ap.parse_args()
    cfg=json.loads((ROOT/'configs'/f'{args.profile}.json').read_text(encoding='utf-8'));out=ROOT/'results'/args.profile;out.mkdir(parents=True,exist_ok=True)
    files=[p for p in ROOT.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.md','.txt'] and not any(x in p.relative_to(ROOT).parts for x in ['results','data','__pycache__'])]
    manifest=dict(started_utc=datetime.now(timezone.utc).isoformat(),command=sys.argv,python=sys.version,platform=platform.platform(),config=cfg,status='running',
        source_sha256={str(p.relative_to(ROOT)):digest(p) for p in files},packages={x:importlib.metadata.version(x) for x in ['numpy','scipy','pandas','matplotlib']},scope='Independent second-round audit; no old results imported')
    (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    try:
        audit_plus.run(cfg,out);manifest['status']='complete'
        import pandas as pd
        checks=[]
        corr=pd.read_csv(out/'plus_correlated_noise.csv');tails=pd.read_csv(out/'plus_heavy_tails.csv');opt=pd.read_csv(out/'plus_optimizer_audit.csv')
        cal=pd.read_csv(out/'plus_calibration_sensitivity_summary.csv')
        checks.append(dict(name='Rinf correlated coverage valid scenarios',passed=bool(corr[(corr.valid)&(corr.method=='Rinf_coordinate_union')].coverage.ge(.90).all())))
        checks.append(dict(name='negative controls labelled',passed=bool((~tails[tails.distribution!='gaussian'].assumption_valid).all())))
        checks.append(dict(name='optimizer does not claim global optimum',passed=bool((~opt.global_optimum_certified).all())))
        checks.append(dict(name='tiny calibration returns infinite radius',
                           passed=bool((cal[cal.n_cal < 19].infinite_fraction == 1).all())))
        checks.append(dict(name='diagonal R2 invalid under correlation or adaptation',
                           passed=bool((~corr[(corr.method=='R2_diagonal') & ((corr.rho > 0) | (corr.rule != 'fixed_equal'))].valid).all())))
        for c in checks:
            if not c['passed']:raise AssertionError(c['name'])
        (out/'validation_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8');manifest['checks']=checks
        manifest['status']='complete'
    except Exception as e:manifest['status']='failed';manifest['error']=repr(e);raise
    finally:
        manifest['finished_utc']=datetime.now(timezone.utc).isoformat();manifest['artifacts']={str(p.relative_to(ROOT)):dict(sha256=digest(p),bytes=p.stat().st_size) for p in out.rglob('*') if p.is_file() and p.name!='run_manifest.json'}
        (out/'run_manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print('COMPLETE',out)

if __name__=='__main__':main()
