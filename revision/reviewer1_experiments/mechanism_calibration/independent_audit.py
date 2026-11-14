"""Independent full-sort regeneration/checks; does not import runner helpers."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import time
import numpy as np


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_rank(n, alpha):
    return int((Decimal(n+1)*(Decimal(1)-alpha)).to_integral_value(rounding=ROUND_CEILING))


def independent_errors(rng, rows, c, missing, unreliable, cfg):
    n_entity, n_coordinate = c['K']+c['bridges']+1,c['p']
    a = rng.standard_normal(size=(rows,1,n_coordinate))
    z = rng.standard_normal(size=(rows,n_entity,n_coordinate))
    e = np.sqrt(c['rho'])*a+np.sqrt(1.0-c['rho'])*z
    mask1 = rng.random(size=e.shape)<missing
    perturb1 = rng.standard_normal(size=e.shape)
    e = e+float(cfg['missing_noise_sd'])*mask1*perturb1
    mask2 = rng.random(size=e.shape)<unreliable
    perturb2 = rng.standard_normal(size=e.shape)
    e = e+float(cfg['unreliable_noise_sd'])*mask2*perturb2
    # Explicit sum-of-squares instead of the runner's norm helper.
    norms = np.sqrt((e*e).sum(axis=2))
    return norms,int(mask1.sum()),int(mask2.sum())


def agreement(x,y):
    assert np.array_equal(np.isposinf(x),np.isposinf(y))
    assert np.array_equal(np.isnan(x),np.isnan(y))
    finite=np.isfinite(x)&np.isfinite(y)
    difference=float(np.max(np.abs(x[finite]-y[finite]))) if finite.any() else 0.0
    assert np.allclose(x[finite],y[finite],rtol=1e-13,atol=1e-13),difference
    return difference


def independent_wilson(values):
    count=len(values); mean=float(np.sum(values))/count
    z=1.959963984540054
    center=(mean+z*z/(2*count))/(1+z*z/count)
    margin=z/(1+z*z/count)*math.sqrt(mean*(1-mean)/count+z*z/(4*count*count))
    return max(0,center-margin),min(1,center+margin)


def independent_bootstrap(values, repeats, seed):
    """Count-weight arithmetic instead of runner's sampled-row mean."""
    rng=np.random.default_rng(seed)
    answer=np.empty((repeats,)+values.shape[1:])
    missing=np.isnan(values).all(axis=0)
    flat=np.nan_to_num(values.reshape(len(values),-1),nan=0.0)
    for first in range(0,repeats,50):
        last=min(first+50,repeats)
        indices=rng.integers(0,len(values),size=(last-first,len(values)))
        counts=np.array([np.bincount(row,minlength=len(values)) for row in indices])
        means=np.einsum('bn,nc->bc',counts,flat,optimize=False)/len(values)
        answer[first:last]=means.reshape((-1,)+values.shape[1:])
    answer[:,missing]=np.nan
    return answer


def audit(directory):
    start=time.perf_counter()
    cfg=json.loads((directory/'frozen_config.json').read_text(encoding='utf-8'))
    run=json.loads((directory/'run_manifest.json').read_text(encoding='utf-8'))
    profile=cfg['profiles'][run['profile']]
    eta=Decimal(cfg['eta'])
    assert len(cfg['cells'])==26
    assert exact_rank(18,eta)==19 and exact_rank(19,eta)==19
    assert exact_rank(199,eta/Decimal(11))>199
    assert exact_rank(199,eta/Decimal(5))<=199
    # Minimum independent complete-archive sample sizes, not entity rows.
    assert exact_rank(7,eta)>7
    assert exact_rank(218,eta/Decimal(11))>218
    assert exact_rank(219,eta/Decimal(11))<=219
    summary=list(csv.DictReader((directory/'summary.csv').open(encoding='utf-8',newline='')))
    entity_summary=list(csv.DictReader((directory/'entity_summary.csv').open(encoding='utf-8',newline='')))
    paired=list(csv.DictReader((directory/'paired_world_contrasts.csv').open(encoding='utf-8',newline='')))
    rows=[];max_diff=0.0
    methods=['joint_max','entitywise_marginal','entitywise_bonferroni']
    for ci,c in enumerate(cfg['cells']):
        raw_path=directory/'raw'/f'{ci:02d}_{c["cell_id"]}.npz'
        with np.load(raw_path,allow_pickle=False) as compressed:
            # Cache each member once; NpzFile indexing otherwise decompresses it
            # again at every world, changing verification I/O from O(W) to O(W²).
            raw={key:compressed[key] for key in compressed.files}
            n,m=c['n_cal'],c['M']
            r=[exact_rank(n,eta),exact_rank(n,eta),exact_rank(n,eta/Decimal(m))]
            assert np.array_equal(raw['ranks'],r)
            metric=[]
            for wi in range(profile['worlds_per_cell']):
                rng=np.random.Generator(np.random.PCG64(np.random.SeedSequence([profile['seed'],ci,wi])))
                calibration,cm,cu=independent_errors(rng,n,c,c['missing_cal'],c['unreliable_cal'],cfg)
                test,tm,tu=independent_errors(rng,1,c,c['missing_test'],c['unreliable_test'],cfg)
                # Norm scales linearly because the frozen multiplier is positive.
                test=test[0]*c['scale_test']
                max_diff=max(max_diff,agreement(test,raw['test_norms'][wi]))
                ordered_joint=np.sort(np.max(calibration,axis=1))
                ordered_slot=np.sort(calibration,axis=0)
                expected=np.full((3,m),np.inf)
                if r[0]<=n: expected[0,:]=ordered_joint[r[0]-1]
                if r[1]<=n: expected[1,:]=ordered_slot[r[1]-1,:]
                if r[2]<=n: expected[2,:]=ordered_slot[r[2]-1,:]
                max_diff=max(max_diff,agreement(expected,raw['radii'][wi]))
                max_diff=max(max_diff,agreement(np.array(ordered_joint[-1]),np.array(raw['calibration_max'][wi])))
                max_diff=max(max_diff,agreement(expected[0,0],np.array(raw['joint_order_statistic'][wi])))
                assert np.array_equal([cm,cu,tm,tu],raw['perturbation_counts'][wi])
                hit=np.less_equal(test[None,:],expected)
                assert np.array_equal(hit,raw['hits'][wi])
                values=np.stack([hit.min(axis=1),hit.sum(axis=1)/m,
                                 hit[:,:c['K']].sum(axis=1)/c['K'],
                                 hit[:,c['K']:m-1].sum(axis=1)/c['bridges'] if c['bridges'] else np.full(3,np.nan),
                                 hit[:,-1]],axis=-1)
                max_diff=max(max_diff,agreement(values,raw['metrics'][wi]))
                metric.append(values)
            metric=np.array(metric)
            boot=independent_bootstrap(metric,profile['bootstrap_repetitions'],
                                      np.random.SeedSequence([cfg['bootstrap_seed'],profile['seed'],ci]))
            for mi,method in enumerate(methods):
                saved=next(s for s in summary if s['cell_id']==c['cell_id'] and s['rule']==method)
                for ri,role in enumerate(['joint','entity','source','bridge','target']):
                    expected_mean=metric[:,mi,ri].mean()
                    actual=saved[role+'_coverage']
                    if np.isnan(expected_mean):
                        assert actual==''
                        assert saved[role+'_lower']==saved[role+'_upper']==''
                    else:
                        assert abs(float(actual)-expected_mean)<1e-13
                        if ri in (0,4): lo,hi=independent_wilson(metric[:,mi,ri])
                        else: lo,hi=np.quantile(boot[:,mi,ri],[.025,.975])
                        assert abs(float(saved[role+'_lower'])-lo)<1e-12
                        assert abs(float(saved[role+'_upper'])-hi)<1e-12
                inf=float(np.isinf(raw['radii'][:,mi,:]).mean())
                assert abs(float(saved['infinite_radius_fraction'])-inf)<1e-13
                for slot in range(m):
                    entity=next(s for s in entity_summary if s['cell_id']==c['cell_id'] and s['rule']==method and int(s['entity_slot'])==slot)
                    value=raw['hits'][:,mi,slot]
                    lo,hi=independent_wilson(value)
                    assert abs(float(entity['coverage'])-value.mean())<1e-13
                    assert abs(float(entity['lower'])-lo)<1e-12
                    assert abs(float(entity['upper'])-hi)<1e-12
            for left,right in [(0,1),(0,2),(2,1)]:
                for ri,role in enumerate(['joint','entity']):
                    pair=next(s for s in paired if s['cell_id']==c['cell_id'] and s['left']==methods[left] and s['right']==methods[right] and s['metric']==role)
                    expected=(metric[:,left,ri]-metric[:,right,ri]).mean()
                    lo,hi=np.quantile(boot[:,left,ri]-boot[:,right,ri],[.025,.975])
                    assert abs(float(pair['difference'])-expected)<1e-13
                    assert abs(float(pair['lower'])-lo)<1e-12
                    assert abs(float(pair['upper'])-hi)<1e-12
            if not c['bridges']:
                assert np.isnan(raw['metrics'][:,:,3]).all()
            if c['exchangeability_assumption_holds']:
                effective_coverage=min(r[0]/(n+1),1.0)
                bonf_entity=min(r[2]/(n+1),1.0)
                joint_lower=max(0.0,1-m*(1-bonf_entity))
            else:
                effective_coverage=None; joint_lower=None
            rows.append(dict(cell_id=c['cell_id'],worlds=profile['worlds_per_cell'],
                             rank_joint=r[0],rank_bonferroni=r[2],n_cal=n,M=m,
                             joint_max_unconditional_coverage_if_exchangeable=effective_coverage,
                             bonferroni_joint_lower_bound_if_exchangeable=joint_lower,
                             all_raw_worlds_regenerated=True))
    for rel,metadata in run['artifacts'].items():
        assert checksum(directory/rel)==metadata['sha256'],rel
    # An analytic impossibility/infinity result is not a performance win.
    output=dict(status='passed',profile=run['profile'],worlds_regenerated=len(cfg['cells'])*profile['worlds_per_cell'],
                all_26_cells_retained=True,maximum_absolute_reconstruction_difference=max_diff,
                elapsed_seconds=time.perf_counter()-start,
                checks=['independent Decimal rank arithmetic','explicit full-sort calibration reconstruction',
                        'every smoke/full world regenerated independently','infinity retained and scored',
                        'entity marginal fractions use world unit','full menu joint AND including unused bridges',
                        'all role means recomputed','Wilson and world-bootstrap intervals independently recomputed',
                        'paired method differences and intervals independently recomputed',
                        'all original run-artifact hashes verified'],
                statistical_success_not_required=True,real_data_execution=False,
                interpretation='Code audit only; no real mechanism labels, outcomes or empirical-coverage pass threshold.',
                analytic_cell_reference=rows,source_sha256={Path(__file__).name:checksum(Path(__file__))})
    (directory/'independent_audit.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in output.items() if k!='analytic_cell_reference'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path)
    audit(p.parse_args().directory)
