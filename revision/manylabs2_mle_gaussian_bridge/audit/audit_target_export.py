"""Independent target-export aggregation and provenance audit; no simulations."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((ROOT/'target_metrics_export_manifest.json').read_text(encoding='utf-8-sig'))
    primary_manifest = json.loads((ROOT/'monte_carlo_manifest.json').read_text(encoding='utf-8-sig'))
    protocol = json.loads((ROOT/'protocol/execution.json').read_text(encoding='utf-8-sig'))
    freeze = json.loads((ROOT/'audit/full_run_freeze.json').read_text(encoding='utf-8-sig'))
    targets = {protocol['sites'][j] for j in protocol['target_indices']}
    d = pd.read_csv(ROOT/'target_level_metrics.csv')
    p = pd.read_csv(ROOT/'bridge_design_comparison.csv')
    keys = ['scenario','dgp','scale','noise_model','budget','policy','estimator']
    groups = d.groupby(keys, sort=False, dropna=False)
    assert len(d) == 68816 and len(p) == 4048 and len(groups) == 4048
    assert (groups.size() == 17).all()
    assert groups['target_site'].apply(lambda x: len(x)==17 and set(x)==targets).all()
    assert not d.duplicated(keys+['target_site']).any()
    assert groups['available'].nunique().eq(1).all()
    assert groups['replications'].nunique().eq(1).all()
    grouped = groups[['valid_rate','mse','mae','coverage95_conditional','coverage95_unconditional']].mean().reset_index()
    joined = grouped.merge(p, on=keys, suffixes=('_targetmean','_primary'), validate='one_to_one')
    assert len(joined) == len(p)
    differences = {}
    for metric in ['valid_rate','mse','mae','coverage95_conditional','coverage95_unconditional']:
        a = joined[metric+'_targetmean'].to_numpy()
        b = joined[metric+'_primary'].to_numpy()
        assert np.array_equal(np.isnan(a), np.isnan(b)), metric
        assert np.allclose(a,b,atol=1e-12,rtol=1e-10,equal_nan=True), metric
        differences[metric] = float(np.nanmax(abs(a-b)))
    status = groups[['available','replications']].first().reset_index().merge(p[keys+['available','replications']], on=keys,
                                     suffixes=('_export','_primary'), validate='one_to_one')
    assert (status.available_export==status.available_primary).all()
    assert (status.replications_export==status.replications_primary).all()
    unavailable = d[~d.available]
    assert set(unavailable.scenario)=={'unknown_all_Male','unknown_all_Female'}
    assert (unavailable.scale==1).all() and (unavailable.budget>0).all()
    assert unavailable['mse'].isna().all() and unavailable['mae'].isna().all()
    assert unavailable['valid_rate'].eq(0).all() and unavailable.coverage95_unconditional.eq(0).all()
    source_only = d[d.policy=='source_only_no_bridge']
    assert len(source_only)==46*2*2*17 and source_only.available.all() and source_only.budget.eq(0).all()
    assert (d.loc[d.available,'mse_mc_se'].dropna()>=0).all()
    assert len(manifest['primary_hashes'])==9
    assert all(digest(ROOT/name)==value for name,value in manifest['primary_hashes'].items())
    assert all(digest(ROOT/name)==value for name,value in primary_manifest['outputs'].items())
    assert all(digest(ROOT/name)==value for name,value in freeze['files'].items())
    assert digest(ROOT/'target_level_metrics.csv')==manifest['target_metrics_sha256']
    assert digest(ROOT/'code/export_target_metrics.py')==manifest['exporter_sha256']
    assert digest(ROOT/'protocol/execution.json')==manifest['protocol_sha256']==primary_manifest['protocol_sha256']
    assert digest(ROOT/'code/bernoulli_mc.py')==primary_manifest['code_sha256']
    assert len(manifest['condition_timings'])==len(primary_manifest['condition_runs'])==46
    assert [(x['scenario'],x['dgp'],x['scale']) for x in manifest['condition_timings']]==[(x['scenario'],x['dgp'],x['scale']) for x in primary_manifest['condition_runs']]
    output = {'status':'passed','target_rows':len(d),'policy_condition_groups':len(groups),'targets_per_group':17,
              'primary_hashes_verified':9,'original_freeze_hashes_verified':10,
              'unavailable_target_rows':len(unavailable),'source_only_target_rows':len(source_only),
              'maximum_absolute_aggregate_differences':differences,
              'seed_provenance_review':'Exporter reconstructs each recorded evaluation SeedSequence child; source/bridge child streams 1/0 are unchanged; policy choices read from primary outputs; no refitting or reselection.',
              'exporter_sha256':manifest['exporter_sha256'],'findings':[]}
    (ROOT/'audit/target_export_audit_summary.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    summary_path=ROOT/'audit/numerical_audit_summary.json'
    summary=json.loads(summary_path.read_text(encoding='utf-8-sig'))
    summary['target_export_audit']=output
    summary_path.write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
