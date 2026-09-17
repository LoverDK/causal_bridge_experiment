"""Rebuild visualization/text only; preserve the executed simulation manifest."""
import argparse
from datetime import datetime,timezone
import json
from atlas_new import report
from run_all import ROOT,digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['smoke','full'],default='full')
    args=parser.parse_args();out=ROOT/'results'/args.profile
    mp=out/'run_manifest.json';manifest=json.loads(mp.read_text(encoding='utf-8'))
    if manifest['status']!='complete':raise RuntimeError('Only complete runs may be postprocessed')
    # Formula-implementing modules must match the actual executed version.
    for name in ['core.py','experiments.py','manylabs.py']:
        path=ROOT/'atlas_new'/name
        key=str(path.relative_to(ROOT))
        if digest(path)!=manifest['source_sha256'][key]:
            raise RuntimeError(f'Experiment source changed: {name}; rerun experiments instead')
    report.validate_results(out);report.figures(out);report.write_report(manifest['config'],out)
    manifest.setdefault('postprocessing',[]).append(dict(
        utc=datetime.now(timezone.utc).isoformat(),reason='Report text and visual labeling update; no simulation resampling',
        source_sha256={'atlas_new/report.py':digest(ROOT/'atlas_new'/'report.py'),'refresh_report.py':digest(ROOT/'refresh_report.py')}))
    manifest['artifacts']={str(p.relative_to(ROOT)):dict(sha256=digest(p),bytes=p.stat().st_size)
        for p in out.rglob('*') if p.is_file() and p!=mp}
    mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    print('Postprocessing complete:',out)


if __name__=='__main__':main()
