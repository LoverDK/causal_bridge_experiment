"""Independent saved-record audit of declared smoothness; never simulates."""
import os
for _name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[_name]='1'
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
import pandas as pd

VARIANTS=('baseline','L_half','L_double','H_zero','H_double')
FACTORS={'baseline':(1,1),'L_half':(.5,1),'L_double':(2,1),'H_zero':(1,0),'H_double':(1,2)}
WORLD=('surface','scenario','replicate')
IDENT=WORLD+('variant','mode')
MODES=('r2','rinf')
COLORS=dict(baseline='#0F4D92',L_half='#B64342',L_double='#42949E',H_zero='#D38339',H_double='#767676')
LABELS=dict(baseline='Original L, H',L_half='L / 2 (understated)',L_double='2L (conservative)',H_zero='H = 0 (omission)',H_double='2H (conservative)')

def read_json(p):return json.loads(p.read_text(encoding='utf-8'))
def read_jsonl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_json(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
def save_csv(p,f):f.to_csv(p,index=False,float_format='%.17g',lineterminator='\n')
def key(row,names):return tuple(row[n] for n in names)
def arr(v):return np.asarray(json.loads(v) if isinstance(v,str) else v)

def parts(d,ids,a,mode):
    """Literal independent expansion; does not import the experimental code."""
    a=np.asarray(a,float);ids=np.asarray(ids,int);c=np.asarray(d['centers'])[ids]
    r=np.asarray(d['radii'])[ids];t=np.asarray(d['target_center']);s=np.asarray(d['noise_sd'])[ids]
    L,H,rt=d['L'],d['H'],d['target_radius'];ns=len(d['centers'])
    q=math.sqrt(2*math.log(2*ns/d['zeta'])) if mode=='rinf' else math.sqrt(2*math.log(2*(d['budget']+1)/(d['zeta']/2)))
    cq=math.sqrt(2*math.log(2*ns/(d['zeta'] if mode=='rinf' else d['zeta']/2)))
    offset=L*np.linalg.norm(np.sum(a[:,None]*c,axis=0)-t);radial=L*(rt+np.dot(a,r))
    center_curv=0.;curv=0.
    for i in range(len(a)):
        for j in range(len(a)):
            if i!=j:
                dist=np.linalg.norm(c[i]-c[j]);coef=H*a[i]*a[j]/4
                center_curv+=coef*dist**2;curv+=coef*(dist+r[i]+r[j])**2
    lip_center=L*np.dot(a,np.linalg.norm(c-t,axis=1));bar=offset+radial+curv;lip=lip_center+radial
    noise=q*(np.dot(a,s) if mode=='rinf' else np.sqrt(np.dot(a*a,s*s)))
    return dict(barycentric_center_offset=float(offset),linear_set_radius=float(radial),center_curvature=float(center_curv),
        set_radius_curvature_inflation=float(curv-center_curv),total_curvature=float(curv),lipschitz_center_distance=float(lip_center),
        Bbar=float(bar),BLip=float(lip),geometry_min=float(min(bar,lip)),noise=float(noise),radius=float(min(bar,lip)+noise),coordinate_multiplier=cq)

def audit(raw):
    manifest=read_json(raw/'run_manifest.json');assert manifest['status']=='complete';cfg=manifest['config']
    assert all(manifest['checks'].values())
    for n,h in manifest['source_sha256'].items():assert digest(raw/'source_snapshot'/n)==h,n
    for n,h in manifest['artifact_sha256'].items():assert digest(raw/n)==h,n
    worlds=read_jsonl(raw/'world_audits.jsonl');designs=read_jsonl(raw/'variant_designs.jsonl');plans=read_jsonl(raw/'design_plans.jsonl')
    def csv(n):return pd.read_csv(raw/n,float_precision='round_trip')
    fixed=csv('fixed_certificate_records.csv');stopped=csv('stopped_output_records.csv')
    same=csv('same_weight_diagnostics.csv');observations=csv('common_observations.csv')
    nw=9*cfg['repetitions_per_cell']
    assert len(worlds)==nw and len(fixed)==nw*40 and len(stopped)==nw*80 and len(same)==nw*40 and len(observations)==nw*7
    assert not fixed.duplicated(list(IDENT)+['stage']).any() and not stopped.duplicated(list(IDENT)+['tolerance','budget']).any()
    wd={key(w,WORLD):w for w in worlds};dd={key(d,WORLD+('variant',)):d for d in designs}
    pp={key(p,IDENT+('stage',)):p for p in plans};ff={key(r,IDENT+('stage',)):r for r in fixed.to_dict('records')}
    oo={key(o,WORLD+('source_id',)):o for o in observations.to_dict('records')}
    assert len(dd)==nw*5 and len(pp)==nw*40 and len(wd)==nw
    diffs=dict(geometry=0.,estimate=0.,refusal=0.,stopped=0.,same_weight=0.,error_decomposition=0.)
    cal=[];same_scoring=[];conditional_checks=0

    def labels(row,d):
        lv=d['L']>=d['reference_L'];hv=d['H']>=d['reference_H'];valid=lv and hv
        for n,v in [('declared_L_valid',lv),('declared_H_valid',hv),('smoothness_declaration_valid',valid),
                    ('barycentric_assumptions_valid',valid),('lipschitz_assumptions_valid',lv),('refusal_bound_valid',lv),('guarantee_applicable',valid)]:
            assert row[n]==v,(n,row)
        nominal=row['nominal_path_failure_bound']
        assert (nominal==.1) if valid else (nominal is None or pd.isna(nominal))
        assert row['mechanism_event_holds']==d['mechanism_event_holds']

    def branch(row,d):
        valid=[]
        if d['declared_L_valid'] and d['declared_H_valid']:valid.append(row['Bbar'])
        if d['declared_L_valid']:valid.append(row['BLip'])
        strict=any(x<=row['geometry_min'] for x in valid)
        near=any(x<=row['geometry_min']+cfg['branch_tie_tolerance'] for x in valid)
        assert row['selected_bound_valid']==strict and row['valid_branch_near_min']==near
        assert row['active_branch']==('barycentric' if row['Bbar']<=row['BLip'] else 'lipschitz')

    def scoring(row,d,w,ids,a):
        mu=np.asarray(w['truth']);y=np.array([oo[key(w,WORLD)+(sid,)]['effect'] for sid in ids])
        causal=float(np.dot(a,mu[ids])-mu[-1]);sampling=float(np.dot(a,y-mu[ids]));total=float(np.dot(a,y)-mu[-1])
        for n,v in [('causal_error',causal),('sampling_error',sampling),('error',total)]:
            diffs['error_decomposition']=max(diffs['error_decomposition'],abs(row[n]-v))
        assert abs(total-causal-sampling)<1e-12
        excess=abs(causal)-row['geometry_min']
        assert row['causal_exceeds_declared_geometry']==(excess>0)
        assert row['causal_exceeds_declared_geometry_tolerant']==(excess>row['causal_check_tolerance'])
        assert np.isclose(row['causal_absolute_error'],abs(causal),rtol=0,atol=1e-12)
        assert np.isclose(row['sampling_absolute_error'],abs(sampling),rtol=0,atol=1e-12)
        assert row['truth']==mu[-1]
        if d['smoothness_declaration_valid'] and d['mechanism_event_holds']:
            assert excess<=row['causal_check_tolerance']
        return causal,sampling

    for wk,w in wd.items():
        scores=np.sort(w['calibration_scores']);rank=math.ceil((len(scores)+1)*(1-cfg['eta']))
        assert len(scores)==199 and scores[rank-1]==w['calibration_q'] and scores[-1]==w['calibration_max']
        order=np.random.default_rng(np.random.SeedSequence([cfg['seed'],w['surface_id'],w['scenario_id'],w['replicate'],20])).permutation(np.arange(4,10)).tolist()
        assert order==w['common_random_order']
        true=np.asarray(w['true_locations']);x,y=true.T;assert np.all(np.abs(true)<=1)
        if w['surface']=='linear':mu=.55*x+.3*y;L=math.hypot(.55,.3);H=0.
        elif w['surface']=='quadratic':mu=.5*x+.2*y+.06*(x*x+y*y);L=math.hypot(.62,.32);H=.12
        else:mu=.45*x+.2*y+.08*np.sin(2*x);L=math.hypot(.61,.2);H=.32
        assert np.allclose(mu,w['truth'],rtol=0,atol=1e-14)
        base=dd[wk+('baseline',)];assert base['L']==L and base['H']==H
        assert np.all(np.asarray(base['radii'])==cfg['proxy_scale']*w['calibration_q'])
        assert base['target_radius']==cfg['proxy_scale']*w['calibration_q']
        covered=bool(np.all(np.linalg.norm(np.asarray(base['centers'])-true[:-1],axis=1)<=np.asarray(base['radii'])+1e-14) and np.linalg.norm(np.asarray(base['target_center'])-true[-1])<=base['target_radius']+1e-14)
        assert covered==w['joint_set_covered']
        cal.append(dict(zip(WORLD,wk),joint_set_covered=covered,calibration_q=w['calibration_q'],radius=base['target_radius']))
        for sid in list(range(4))+order[:3]:
            o=oo[wk+(sid,)];assert o['n']==(800 if sid<4 else 96)
            assert abs(o['effect']-(o['treated_mean']-o['control_mean']))<1e-14
            assert abs(o['noise_sd']-1/math.sqrt(o['n']))<1e-14
        for variant in VARIANTS:
            d=dd[wk+(variant,)];ls,hs=FACTORS[variant]
            assert d['L']==L*ls and d['H']==H*hs and d['reference_L']==L and d['reference_H']==H
            for n in ['centers','radii','target_center','target_radius','noise_sd']:assert np.array_equal(d[n],base[n]),n
            labels(d,d);assert d['mechanism_event_holds']==covered
            for mode in MODES:
                previous=np.inf
                path_valid=all(ff[wk+(variant,mode,s)]['selected_bound_valid'] for s in range(4))
                for stage in range(4):
                    k=wk+(variant,mode,stage);p=pp[k];f=ff[k];a=np.asarray(p['weights']);ids=list(range(4))+order[:stage]
                    assert p['ids']==ids and np.array_equal(arr(f['weights']),a) and np.array_equal(arr(f['source_ids']),ids)
                    assert a.min()>=0 and abs(a.sum()-1)<1e-8
                    g=parts(d,ids,a,mode)
                    for n,v in g.items():
                        if n!='coordinate_multiplier':diffs['geometry']=max(diffs['geometry'],abs(v-f[n]),abs(v-p['geometry_parts'][n]))
                    assert g['radius']<=previous+1e-8;previous=g['radius']
                    effects=np.array([oo[wk+(sid,)]['effect'] for sid in ids]);estimate=float(a@effects)
                    dist=np.linalg.norm(np.asarray(d['centers'])[ids]-d['target_center'],axis=1)+np.asarray(d['radii'])[ids]+d['target_radius']
                    half=g['coordinate_multiplier']*np.asarray(d['noise_sd'])[ids]+d['L']*dist
                    low=float(np.max(effects-half));high=float(np.min(effects+half))
                    diffs['estimate']=max(diffs['estimate'],abs(estimate-f['estimate']))
                    diffs['refusal']=max(diffs['refusal'],abs(low-f['refusal_lower']),abs(high-f['refusal_upper']))
                    assert f['refusal_status']==('finite' if low<=high else 'inconsistent')
                    assert f['new_n']==stage*96 and f['historical_n']==3200 and f['path_all_selected_bounds_valid']==path_valid
                    labels(f,d);branch(f,d);scoring(f,d,w,ids,a)
                    assert abs(f['certificate_width']-2*g['radius'])<1e-10
                    assert abs(f['certificate_lower']-(estimate-g['radius']))<1e-10 and abs(f['certificate_upper']-(estimate+g['radius']))<1e-10
                    assert f['certificate_covered']==(f['certificate_lower']<=w['truth'][-1]<=f['certificate_upper'])
                    assert abs(f['absolute_error']-abs(estimate-w['truth'][-1]))<1e-12
                    if variant in ('H_zero','H_double'):
                        b=ff[wk+('baseline',mode,stage)]
                        assert f['refusal_lower']==b['refusal_lower'] and f['refusal_upper']==b['refusal_upper']
                        if w['surface']=='linear':
                            assert np.array_equal(a,arr(b['weights'])) and f['radius']==b['radius'] and f['estimate']==b['estimate']
                    conditional_checks+=int(d['smoothness_declaration_valid'] and covered)
    ss={key(r,IDENT+('stage',)):r for r in same.to_dict('records')}
    for k,row in ss.items():
        wk=k[:3];variant,mode,stage=k[3:];d=dd[wk+(variant,)];ref=pp[wk+('baseline',mode,stage)]
        assert np.array_equal(arr(row['weights']),ref['weights']) and np.array_equal(arr(row['source_ids']),ref['ids'])
        g=parts(d,ref['ids'],ref['weights'],mode);b=ss[wk+('baseline',mode,stage)]
        for n,v in g.items():
            if n!='coordinate_multiplier':diffs['same_weight']=max(diffs['same_weight'],abs(v-row[n]))
        assert abs(row['noise']-b['noise'])<1e-12;branch(row,d);labels(row,d)
        if variant in ('L_double','H_double'):assert row['radius']>=b['radius']-1e-11
        if variant in ('L_half','H_zero'):assert row['radius']<=b['radius']+1e-11
        if variant in ('H_zero','H_double'):assert row['BLip']==b['BLip']
        mu=np.asarray(wd[wk]['truth']);bias=abs(np.dot(ref['weights'],mu[ref['ids']])-mu[-1])
        same_scoring.append(dict(zip(IDENT+('stage',),k),causal_absolute_error=float(bias),causal_geometry_violation=bool(bias>row['geometry_min']+1e-10)))
    same=same.merge(pd.DataFrame(same_scoring),on=list(IDENT)+['stage'],validate='one_to_one')
    for r in stopped.to_dict('records'):
        ident=key(r,IDENT);d=dd[ident[:4]];radii=[ff[ident+(s,)]['radius'] for s in range(4)]
        hits=[s for s in range(4) if radii[s]<=r['tolerance']];first=hits[0] if hits else 3
        actual=min(r['budget'],first);f=ff[ident+(actual,)];release=f['radius']<=r['tolerance']
        low=f['certificate_lower'] if release else f['refusal_lower'];high=f['certificate_upper'] if release else f['refusal_upper']
        assert r['actual_stage']==actual and r['actual_new_n']==actual*96 and r['released']==release
        assert r['carried_after_stop']==(bool(hits) and r['budget']>first)
        assert np.array_equal(arr(r['acquired_bridge_ids']),wd[ident[:3]]['common_random_order'][:actual])
        assert np.array_equal(arr(r['weights']),arr(f['weights'])) and np.array_equal(arr(r['source_ids']),arr(f['source_ids']))
        diffs['stopped']=max(diffs['stopped'],abs(low-r['lower']),abs(high-r['upper']),abs(f['estimate']-r['estimate']))
        assert r['returned_output_bound_valid']==(f['selected_bound_valid'] if release else d['refusal_bound_valid'])
        assert r['covered']==(low<=r['truth']<=high) and r['bad_release']==(release and abs(r['estimate']-r['truth'])>r['tolerance'])
        assert r['interval_status']==('finite' if low<=high else 'inconsistent') and r['certificate_covered']==f['certificate_covered']
        scoring(r,d,wd[ident[:3]],arr(r['source_ids']).astype(int),arr(r['weights']))
    for _,g in stopped.groupby(list(IDENT)+['tolerance']):
        g=g.sort_values('budget')
        assert np.array_equal(g.path_covered,np.logical_and.accumulate(g.covered))
        assert np.array_equal(g.certificate_path_covered,np.logical_and.accumulate(g.certificate_covered))
        assert np.array_equal(g.path_all_output_bound_assumptions_satisfied,np.logical_and.accumulate(g.returned_output_bound_valid))
    assert max(diffs.values())<1e-9,diffs
    evidence=dict(status='passed',worlds=nw,fixed_states=len(fixed),stopped_rows=len(stopped),same_weight_states=len(same),
        valid_declaration_and_covered_mechanism_geometry_checks=conditional_checks,max_absolute_differences=diffs,
        sampling_performed=False,optimization_repeated=False,
        scope=['No simulator/optimizer import; explicit independent formulas and actual saved observations.',
               'All source/artifact hashes and calibration-score quantiles checked; no global-optimum claim.',
               'Policy declaration validity, selected branch and returned refusal validity remain separate.',
               'True effects used only to score saved plans; no new real-data analysis.'])
    return manifest,fixed,stopped,same,pd.DataFrame(cal),observations,evidence

def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,float(center-half)),min(1.,float(center+half))

def summaries(fixed,stopped,same,cal):
    fixed=fixed.copy();base=fixed[fixed.variant=='baseline'].set_index(list(WORLD)+['mode','stage'])
    index=pd.MultiIndex.from_frame(fixed[list(WORLD)+['mode','stage']])
    fixed['width_minus_baseline']=fixed.certificate_width.to_numpy()-base.certificate_width.reindex(index).to_numpy()
    fixed['absolute_error_minus_baseline']=fixed.absolute_error.to_numpy()-base.absolute_error.reindex(index).to_numpy()
    initial=fixed[fixed.stage==0].set_index(list(IDENT)).certificate_width
    fixed['initial_width']=initial.reindex(pd.MultiIndex.from_frame(fixed[list(IDENT)])).to_numpy()
    fixed['width_reduction']=fixed.initial_width-fixed.certificate_width
    fixed['relative_width_reduction']=fixed.width_reduction/fixed.initial_width
    tables={}
    for scope,groups in [('cells',['surface','scenario','variant','mode','stage']),('scenarios',['scenario','variant','mode','stage'])]:
        rows=[]
        for values,g in fixed.groupby(groups):
            n=len(g);k=int(g.certificate_covered.sum());ci=wilson(k,n) if scope=='cells' else (None,None)
            rows.append(dict(zip(groups,values),n_worlds=n,new_participants=int(g.new_n.iloc[0]),
                mean_width=float(g.certificate_width.mean()),median_width=float(g.certificate_width.median()),
                width_q10=float(g.certificate_width.quantile(.1)),width_q90=float(g.certificate_width.quantile(.9)),
                mean_width_minus_baseline=float(g.width_minus_baseline.mean()),mean_relative_width_reduction=float(g.relative_width_reduction.mean()),
                mae=float(g.absolute_error.mean()),mse=float(g.squared_error.mean()),covered_count=k,coverage=k/n,
                coverage_wilson_low=ci[0],coverage_wilson_high=ci[1],
                causal_mae=float(g.causal_absolute_error.mean()),sampling_mae=float(g.sampling_absolute_error.mean()),
                causal_geometry_violation_count=int(g.causal_exceeds_declared_geometry_tolerant.sum()),
                causal_geometry_violation_strict_count=int(g.causal_exceeds_declared_geometry.sum()),
                mean_geometry=float(g.geometry_min.mean()),mean_noise=float(g.noise.mean()),
                mean_center_curvature=float(g.center_curvature.mean()),mean_set_curvature_inflation=float(g.set_radius_curvature_inflation.mean()),
                mean_total_curvature=float(g.total_curvature.mean()),mean_Bbar=float(g.Bbar.mean()),mean_BLip=float(g.BLip.mean()),
                selected_bound_valid_count=int(g.selected_bound_valid.sum()),near_valid_bound_count=int(g.valid_branch_near_min.sum()),
                guarantee_applicable_count=int(g.guarantee_applicable.sum()),
                lipschitz_active_count=int(g.active_branch.eq('lipschitz').sum()),
                refusal_inconsistent_count=int(g.refusal_status.eq('inconsistent').sum()),solver_failure_count=int(g.solver_failures.sum())))
        tables['fixed_summary_'+scope]=pd.DataFrame(rows)
        tables['primary_summary_'+scope]=tables['fixed_summary_'+scope].query("mode == 'r2' and stage == 3").copy()
    terminal=stopped[stopped.budget==3]
    for scope,groups in [('cells',['surface','scenario','variant','mode','tolerance']),('scenarios',['scenario','variant','mode','tolerance'])]:
        rows=[]
        for values,g in terminal.groupby(groups):
            release=g[g.released];finite=g[g.interval_status=='finite'];n=len(g)
            rows.append(dict(zip(groups,values),n_worlds=n,release_count=len(release),release_rate=len(release)/n,
                mean_stopped_new_n=float(g.actual_new_n.mean()),bad_release_count=int(g.bad_release.sum()),
                bad_release_rate=float(g.bad_release.mean()),conditional_bad_release_rate=float(release.bad_release.mean()) if len(release) else np.nan,
                released_mae=float(release.absolute_error.mean()) if len(release) else np.nan,
                returned_covered_count=int(g.covered.sum()),returned_coverage=float(g.covered.mean()),
                returned_path_coverage=float(g.path_covered.mean()),certificate_path_coverage=float(g.certificate_path_covered.mean()),
                returned_valid_bound_count=int(g.returned_output_bound_valid.sum()),
                finite_count=len(finite),inconsistent_count=int(g.interval_status.eq('inconsistent').sum()),
                mean_returned_width_among_finite=float(finite.width.mean()) if len(finite) else np.nan))
        tables['stopped_summary_'+scope]=pd.DataFrame(rows)
    b=same[same.variant=='baseline'].set_index(list(WORLD)+['mode','stage'])
    same=same.copy();idx=pd.MultiIndex.from_frame(same[list(WORLD)+['mode','stage']])
    for metric in ['geometry_min','noise','radius','Bbar','BLip','total_curvature']:
        same[metric+'_minus_baseline']=same[metric].to_numpy()-b[metric].reindex(idx).to_numpy()
    rows=[]
    for values,g in same.groupby(['surface','scenario','variant','mode','stage']):
        row=dict(zip(['surface','scenario','variant','mode','stage'],values),n_worlds=len(g))
        row.update({('mean_'+m+'_minus_baseline'):float(g[m+'_minus_baseline'].mean()) for m in ['geometry_min','noise','radius','Bbar','BLip','total_curvature']})
        row.update(causal_geometry_violation_count=int(g.causal_geometry_violation.sum()),
            exact_same_geometry_count=int(g.geometry_min_minus_baseline.eq(0).sum()),
            near_same_geometry_count=int(g.geometry_min_minus_baseline.abs().le(1e-10).sum()))
        rows.append(row)
    tables['same_weight_summary_cells']=pd.DataFrame(rows)
    tables['same_weight_world_contrasts']=same[[*IDENT,'stage','causal_absolute_error','causal_geometry_violation',
        'geometry_min','Bbar','BLip','noise','radius','geometry_min_minus_baseline','noise_minus_baseline','radius_minus_baseline',
        'Bbar_minus_baseline','BLip_minus_baseline','total_curvature_minus_baseline','selected_bound_valid']]
    rows=[]
    for values,g in cal.groupby(['surface','scenario']):
        k=int(g.joint_set_covered.sum());lo,hi=wilson(k,len(g))
        rows.append(dict(zip(['surface','scenario'],values),n_worlds=len(g),joint_covered_count=k,joint_coverage=k/len(g),
            wilson_low=lo,wilson_high=hi,mean_radius=float(g.radius.mean())))
    tables['calibration_summary']=pd.DataFrame(rows)
    return tables,fixed

def paired_bootstrap(fixed,cfg):
    primary=fixed[(fixed['mode']==cfg['primary_mode'])&(fixed.stage==cfg['primary_stage'])]
    metrics=['certificate_width','absolute_error','squared_error','certificate_covered','causal_absolute_error','causal_exceeds_declared_geometry_tolerant','geometry_min','noise']
    B=cfg['bootstrap_repetitions'];rows=[];bycell={}
    for si,surface in enumerate(cfg['surfaces']):
        for gi,scenario in enumerate(cfg['scenarios']):
            g=primary[(primary.surface==surface)&(primary.scenario==scenario)]
            base=g[g.variant=='baseline'].sort_values('replicate').set_index('replicate')
            for vi,v in enumerate(VARIANTS[1:]):
                alt=g[g.variant==v].sort_values('replicate').set_index('replicate');assert base.index.equals(alt.index)
                diff=alt[metrics].astype(float).to_numpy()-base[metrics].astype(float).to_numpy()
                rng=np.random.default_rng(np.random.SeedSequence([cfg['bootstrap_seed'],si,gi,vi]))
                draws=rng.integers(0,len(diff),size=(B,len(diff)));boot=diff[draws].mean(axis=1)
                bycell[surface,scenario,v]=(diff.mean(axis=0),boot)
                for j,m in enumerate(metrics):
                    lo,hi=np.quantile(boot[:,j],[.025,.975])
                    rows.append(dict(surface=surface,scenario=scenario,variant=v,metric=m,n_worlds=len(diff),
                        mean_variant_minus_baseline=float(diff[:,j].mean()),exploratory_ci_low=float(lo),exploratory_ci_high=float(hi),bootstrap_repetitions=B))
    for scenario in cfg['scenarios']:
        for v in VARIANTS[1:]:
            avg=np.mean([bycell[s,scenario,v][0] for s in cfg['surfaces']],axis=0)
            boot=np.mean([bycell[s,scenario,v][1] for s in cfg['surfaces']],axis=0)
            for j,m in enumerate(metrics):
                lo,hi=np.quantile(boot[:,j],[.025,.975])
                rows.append(dict(surface='equal_surface_pool',scenario=scenario,variant=v,metric=m,n_worlds=3*cfg['repetitions_per_cell'],
                    mean_variant_minus_baseline=float(avg[j]),exploratory_ci_low=float(lo),exploratory_ci_high=float(hi),bootstrap_repetitions=B))
    return pd.DataFrame(rows)

def mdtable(frame,formats=None):
    formats=formats or {};cols=list(frame.columns)
    def cell(n,v):
        if pd.isna(v):return '—'
        if n in formats:return formats[n](v)
        if isinstance(v,(float,np.floating)):return f'{v:.6g}'
        return str(v)
    return '\n'.join(['| '+' | '.join(cols)+' |','| '+' | '.join('---' for _ in cols)+' |']+
        ['| '+' | '.join(cell(n,r[n]) for n in cols)+' |' for _,r in frame.iterrows()])

def figures(out,tables,cfg):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':9,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.facecolor':'white'})
    data=tables['fixed_summary_scenarios'].query("mode == 'r2'")
    fig,axs=plt.subplots(2,3,figsize=(12.5,6.5),layout='constrained');handles=[]
    for j,scenario in enumerate(cfg['scenarios']):
        for v in VARIANTS:
            g=data[(data.scenario==scenario)&(data.variant==v)].sort_values('stage')
            style='--' if v in ('L_half','H_zero') else '-'
            line=axs[0,j].plot(g.new_participants,g.mean_width,color=COLORS[v],ls=style,marker='o',ms=3,label=LABELS[v])[0]
            axs[1,j].plot(g.new_participants,g.coverage,color=COLORS[v],ls=style,marker='o',ms=3)
            if j==0:handles.append(line)
        axs[0,j].set(title=scenario,xlabel='New participants',ylabel='Mean certificate full width' if j==0 else '')
        axs[1,j].axhline(.90,color='#999999',ls=':',lw=1)
        axs[1,j].set(xlabel='New participants',ylabel='Empirical certificate coverage' if j==0 else '',ylim=(min(.86,float(data.coverage.min())-.025),1.012))
        for ax in axs[:,j]:ax.set_xticks([0,96,192,288])
    fig.legend(handles=handles,labels=[LABELS[v] for v in VARIANTS],loc='outside lower center',ncols=3,frameon=False)
    fig.savefig(out/'smoothness_declaration_results.png',dpi=300,bbox_inches='tight')
    fig.savefig(out/'smoothness_declaration_results.pdf',bbox_inches='tight');plt.close(fig)

def report(out,manifest,fixed,stopped,tables,evidence):
    cfg=manifest['config'];p=tables['primary_summary_scenarios'];cells=tables['primary_summary_cells']
    p=pd.concat([p[(p.scenario==s)&(p.variant==v)] for s in cfg['scenarios'] for v in VARIANTS])
    primary=fixed.query("mode == 'r2' and stage == 3")
    stop=tables['stopped_summary_scenarios'].query("mode == 'r2'")
    br=p[p.scenario=='bridgeable'].set_index('variant');ur=p[p.scenario=='unreachable'].set_index('variant')
    bs=stop[(stop.scenario=='bridgeable')&(stop.tolerance==.3)].set_index('variant')
    bs2=stop[(stop.scenario=='bridgeable')&(stop.tolerance==.2)].set_index('variant')
    hz=primary[primary.variant=='H_zero'];hzu=hz[(hz.surface!='linear')&(hz.scenario=='unreachable')]
    hzu_legal=hzu[hzu.selected_bound_valid];hzu_active=int(hzu_legal.active_branch.eq('lipschitz').sum())
    mainshow=p[['scenario','variant','n_worlds','mean_width','mae','covered_count','causal_geometry_violation_count']]
    geometry=cells.pivot(index=['surface','scenario'],columns='variant',values='causal_geometry_violation_count').reset_index()
    cov=cells.pivot(index=['surface','scenario'],columns='variant',values='covered_count').reset_index()
    geometry=geometry[['surface','scenario',*VARIANTS]];cov=cov[['surface','scenario',*VARIANTS]]
    sshow=stop[stop.scenario=='bridgeable'][['variant','tolerance','release_count','n_worlds','mean_stopped_new_n','bad_release_count','released_mae']]
    sshow=pd.concat([sshow[(sshow.tolerance==t)&(sshow.variant==v)] for t in cfg['tolerances'] for v in VARIANTS])
    pc=tables['paired_bootstrap'].query("surface == 'equal_surface_pool' and metric == 'certificate_width'")
    sw=tables['same_weight_summary_cells'].query("mode == 'r2' and stage == 3 and variant in ['H_zero', 'H_double']")
    trace=cfg['trace'];sample=primary[(primary.surface==trace['surface'])&(primary.scenario==trace['scenario'])&(primary.replicate==trace['replicate'])]
    sample=sample[['variant','declared_L','declared_H','Bbar','BLip','noise','radius','causal_error','sampling_error']]
    summary=primary.groupby('variant').agg(n_worlds=('certificate_covered','size'),covered=('certificate_covered','sum'),
        causal_violations=('causal_exceeds_declared_geometry_tolerant','sum'),legal_selected_bound=('selected_bound_valid','sum'))
    summary=summary.reindex(VARIANTS).reset_index()
    nzero=int(stop.release_count.eq(0).sum())
    text=rf'''# 声明 L/H 与曲率组件消融

本轮在原一般 **U/L/H、simplex 权重、min(Bbar,BLip)** 流程中，只改变声明的平滑性界。完成3种函数×3种菜单×每格{cfg['repetitions_per_cell']}世界，共{9*cfg['repetitions_per_cell']:,}个独立世界；主结果为 **R2、288新增参与者**。相同世界的五组共享校准集合、实际研究观测和随机3桥前缀，随后各自重新优化设计型权重。所有预设场景、0/96/192/288预算和Rinf补充均保留。

本次最重要的发现是 **低估L可能使策略过早、自信地发布**：bridgeable中L/2在采满288人后覆盖{int(br.loc['L_half','covered_count'])}/{int(br.loc['L_half','n_worlds'])}，但按δ=.3首次停止时有{int(bs.loc['L_half','bad_release_count'])}/{int(bs.loc['L_half','n_worlds'])}次错误发布；平均只用{bs.loc['L_half','mean_stopped_new_n']:.2f}人，baseline为{bs.loc['baseline','mean_stopped_new_n']:.2f}人、错误发布{int(bs.loc['baseline','bad_release_count'])}次。unreachable中L/2的主预算覆盖为{int(ur.loc['L_half','covered_count'])}/{int(ur.loc['L_half','n_worlds'])}，几何违例{int(ur.loc['L_half','causal_geometry_violation_count'])}个。缩短区间和减少成本在此伴随可靠性丧失。

保守声明有明确代价：bridgeable的主预算平均全宽由baseline的{br.loc['baseline','mean_width']:.6f}增加到2L的{br.loc['L_double','mean_width']:.6f}、2H的{br.loc['H_double','mean_width']:.6f}。**删除H的负结果也保留**：H0的主预算共{len(hz)}世界，几何违例{int(hz.causal_exceeds_declared_geometry_tolerant.sum())}次、漏盖{int((~hz.certificate_covered).sum())}次，本轮不能声称已实证展示删除曲率会失败；这也不为非线性H0补上统一保证。

这是参数声明的敏感性与组件归因，未改变真实函数，未依据上一轮proxy高覆盖调大噪声或更换阈值。模拟仍使用原两臂高斯观测；它不是新非高斯线性W选桥定理实验。

| 组 | 声明 | 保证身份 |
| --- | --- | --- |
| baseline | 原解析 L,H | 合法，合成条件下单policy完整路径失败概率至多0.10 |
| L_half | L/2,H | 三个函数上都低估真实域内L；负控制，无统一名义保证 |
| L_double | 2L,H | 合法但更保守 |
| H_zero | L,0 | linear与baseline完全相同；两个非线性函数上遗漏曲率，Bbar条件不足，BLip及拒绝外区间仍可合法 |
| H_double | L,2H | 合法但更保守；linear与baseline完全相同 |

解析界对应机制域 **[-1,1]²**，并非声称quadratic在整个欧氏空间具有有限L。校准球与该域相交，程序使用球的距离外包作保守计算。真实机制和凸包均在域内。半L低于解析梯度上确界；不能凭有限样本恰好覆盖就认证为有效L。

## 主预算：宽度、真实误差与两层覆盖

每行等量汇总三个函数，共{3*cfg['repetitions_per_cell']}世界。全宽是固定预算证书宽度，不是拒绝外区间；MAE以全部目标为分母。`covered_count`指证书包含真实目标，`causal_geometry_violation_count`指真实加权迁移偏差超过声明几何界（容差1e-10），二者是不同事件。

{mdtable(mainshow)}

按变体汇总主预算计数：

{mdtable(summary)}

负控制更窄或发布更多，不能称为同有效性条件下的改进。负控制若没有经验失败，也不能因此补上理论保证。原声明和加倍声明的覆盖是本DGP证据，不是对未知真实平滑性的认证。全部九格的真实目标覆盖计数（每格分母{cfg['repetitions_per_cell']}）：

{mdtable(cov)}

![声明平滑性消融](smoothness_declaration_results.png)

上排为平均证书全宽，下排为真实目标覆盖；虚线90%表示合法完整声明的保守路径保证水平，不给L_half或非线性H_zero授予名义保证。H_zero汇总混合了合法的linear与两种遗漏曲率的非线性面，必须结合各格CSV解释。每时点是同一世界的重复记录，不额外计样本。

## 曲率或 L 的影响在哪一层

记代理中心c、集合半径r、目标c*、r*，真实来源效果μᵢ与真实目标μ*。程序计算：

$$\overline B=L\left(\left\|\sum_i a_ic_i-c_*\right\|+r_*+\sum_i a_ir_i\right)+\frac H4\sum_{{i\ne j}}a_i a_j(\|c_i-c_j\|+r_i+r_j)^2,$$

$$B_{{Lip}}=L\sum_i a_i(\|c_i-c_*\|+r_i+r_*),\quad R=\min(\overline B,B_{{Lip}})+N(a).$$

$$\widehat\mu-\mu_* = \underbrace{{\sum_i a_i\mu_i-\mu_*}}_{{\text{{causal error}}}}+\underbrace{{\sum_i a_i(\widehat\mu_i-\mu_i)}}_{{\text{{sampling error}}}}.$$

真实μ只用于事后评分，不输入优化、选桥或停止。检查绝对causal error是否被几何项覆盖，有助区分几何声明与噪声余量；并不要求每个错设声明在有限组合中必然违例。以下为同一主预算、每格{cfg['repetitions_per_cell']}世界的几何违例数：

{mdtable(geometry)}

`fixed_summary_cells.csv`同时保存causal MAE、sampling MAE、几何和噪声均值；两种绝对误差的均值不能直接相加得到总MAE。严格“>0”的几何违例与容差1e-10版本分别保存，报告使用后者以免数值舍入当成数学反例。

单独归因使用 **baseline实际权重**：same_weight表不重新优化，噪声与点估计相同。增加L使Bbar和BLip均不减；增加H只增加Bbar，而BLip不变，取最小值后影响可能被另一分支挡住。重新优化后的变化还包含权重调整；多起点SLSQP没有全局最优保证，未强加跨组最优值排序。linear的H_zero/H_double与baseline输入、权重、点估计和半径相同，独立核验通过。

主预算、固定baseline权重下，H变化的各格平均半径变化见 `same_weight_summary_cells.csv`；完整{len(sw)}行保留。它与主表各自优化的效应不同，不能把两者混作曲率项的纯直接贡献。

## 发布与成本：按真实停点评价

下表列bridgeable两种预定半宽门槛。固定预算实验已采满共同前缀，停止表从同一批观测重建“首次R≤δ停止”，不是第二批独立数据。停止输出只用此前观测，后续行carry。

{mdtable(sshow)}

这里L/2、δ=.3的{int(bs.loc['L_half','bad_release_count'])}次错误发布与主预算{int(br.loc['L_half','covered_count'])}/{int(br.loc['L_half','n_worlds'])}覆盖并不矛盾：前者在首次达到被低估的半径门槛时停止，后者继续采集到288人再评价。同一批完整前缀重建的两个任务不能互换结论。该停止组的实际区间覆盖为{int(bs.loc['L_half','returned_covered_count'])}/{int(bs.loc['L_half','n_worlds'])}，较严格的区间漏盖事件与“误差超过δ”事件也不相同。δ=.2时L/2错误发布{int(bs2.loc['L_half','bad_release_count'])}次，其最终返回区间覆盖{int(bs2.loc['L_half','returned_covered_count'])}/{int(bs2.loc['L_half','n_worlds'])}，其中{int(bs2.loc['L_half','inconsistent_count'])}个返回外区间不一致；拒绝并不自动等于返回了有效区间。

其余supported/unreachable以及Rinf的全部结果见 `stopped_summary_cells.csv` / `stopped_summary_scenarios.csv`。零发布的R2组有{nzero}行，条件MAE与条件错误率均记缺失，不填0。不同变体的发布子集及停点可能不同，条件MAE不能直接排名估计器准确性；主预算全目标MAE提供共同评价分母。`bad_release_count`指发布且真实误差超过δ，其无条件分母是全部世界。

成本仅计新增试验参与者；4×800历史人数共用并单列，校准、机制编码、部署成本未计。固定预算每世界成本固定288；停止成本可能更少，二者不混用。

拒绝时返回各组声明L计算的outer envelope，不是sharp PI。同前缀baseline/H_zero/H_double的拒绝端点必须相同，因为H不进入该式；它们若在不同前缀停止，最终输出可不同。空/不一致保留状态，不算零宽成功。若H_zero的某一步由合法BLip达到最小值，该数值界可以有合法依据；近似tie仅作诊断，不能把整个非线性H_zero策略重新标为有统一名义保证。声明合法性、单步选中界、实际返回界和机制集合覆盖事件分别记录。

H0在主预算的非线性unreachable两格中，共{len(hzu_legal)}/{len(hzu)}个状态有严格合法BLip支持，其中{hzu_active}个默认active branch为Lipschitz、{len(hzu_legal)-hzu_active}个是精确并列。其余非线性状态不能仅凭经验覆盖就标为声明合法；linear的{len(hz[hz.surface=='linear'])}个世界则本来就有H=0。这个区别已逐行审计。

## 配对差异、固定例和核验

主预算平均全宽变化（变体减baseline），探索性95%配对区间：

{mdtable(pc[['scenario','variant','n_worlds','mean_variant_minus_baseline','exploratory_ci_low','exploratory_ci_high']])}

bootstrap按每函数×菜单内world配对重采，共{cfg['bootstrap_repetitions']}次、seed={cfg['bootstrap_seed']}，再等权汇总三个函数。未做多重比较校正；方法、时点及阈值不成为独立样本。MAE、覆盖、真实causal偏差及几何违例的配对结果完整保存在 `paired_bootstrap.csv`。

预先指定 {trace['surface']} / {trace['scenario']} / replicate {trace['replicate']} 的主预算分解：

{mdtable(sample)}

全部阶段权重见 `single_world_fixed_states.csv`，真实两臂观测均值见 `single_world_observations.csv`。所有九格的校准事件计数见 `calibration_summary.csv`。独立审核直接排序保存的199个校准分数并重建每项公式，没有重新生成数据或重新优化。

原运行commit `{manifest['git_revision']}`，实际{manifest['elapsed_seconds']:.2f}秒；10项实现测试、{len(manifest['checks'])}项运行检查通过。最初预估smoke5–20秒、full2–5分钟；smoke实测5.080秒并通过独立重建后，根代理在full启动前向作者更新为2–6分钟、4CPU。独立分析事前预估30–90秒，实际耗时与哈希见 `analysis_manifest.json`。

独立核验{evidence['fixed_states']:,}个固定权重状态、{evidence['stopped_rows']:,}个停止输出和{evidence['same_weight_states']:,}个同权重状态；最大重建差：`{json.dumps(evidence['max_absolute_differences'])}`。所有源码/原始产物哈希、来源共享、实际成本、有效性标签、真实误差分解及停止端点已检查。不声称验证全局优化，也未运行任何真实数据。

## 审稿范围

| 问题 | 本轮能提供的证据与仍缺部分 |
| --- | --- |
| REV-01 | 非线性固定例与分解解释术语；不代替正文可读性审阅 |
| REV-02 | Rinf仅设计型补充，未验证结果适应选择的实际用途 |
| REV-03 | 新数字对应一般证书及声明敏感性，不自动替换摘要 |
| REV-04 / KoBT.W1、WGDN.W2a | 回答合成L/H保守或低估时的敏感性；真实U/L/H来源仍open |
| REV-05 | 无真实证书案例或微贷资格修复 |
| REV-06 | 未处理ManyLabs目标参考噪声 |
| REV-07 | 内部组件的匹配比较；无ExAtlas、sample splitting或direct优势证据 |
| REV-08 | 消融不解决已有工作、定理继承及新颖性归属 |
| REV-09 | 仍为simplex类，不证明它充分或优于合法signed/regression替代类 |
| REV-10 | 固定random桥前缀，不重新验证新W或旧logdet定理 |
| REV-11 | 新协议/源码/产物与旧分支分开；全稿归属核对仍未完成 |
| REV-12 | 声明、选中分支、拒绝输出、停止与条件分母分开，真实验收仍缺 |

没有审稿问题因消融成功运行而自动标为resolved。旧审计元数据修复由独立记录承载，不改变本轮模拟数据或既有论文数值。
'''
    (out/'RESULTS.md').write_text(text,encoding='utf-8',newline='\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--output',type=Path)
    args=parser.parse_args();start=time.perf_counter();raw=args.raw.resolve()
    manifest,fixed,stopped,same,cal,observations,evidence=audit(raw)
    if args.output is None:print(json.dumps(evidence,ensure_ascii=False));return
    out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a fresh report directory.')
    tables,fixed=summaries(fixed,stopped,same,cal);tables['paired_bootstrap']=paired_bootstrap(fixed,manifest['config'])
    out.mkdir(parents=True)
    for n,f in tables.items():save_csv(out/(n+'.csv'),f)
    trace=manifest['config']['trace'];mask=(fixed.surface==trace['surface'])&(fixed.scenario==trace['scenario'])&(fixed.replicate==trace['replicate'])
    save_csv(out/'single_world_fixed_states.csv',fixed[mask])
    save_csv(out/'single_world_observations.csv',observations[(observations.surface==trace['surface'])&(observations.scenario==trace['scenario'])&(observations.replicate==trace['replicate'])])
    save_json(out/'independent_audit.json',evidence);figures(out,tables,manifest['config'])
    report(out,manifest,fixed,stopped,tables,evidence)
    save_json(out/'analysis_manifest.json',dict(raw_directory=str(raw),raw_manifest_sha256=digest(raw/'run_manifest.json'),analysis_script_sha256=digest(Path(__file__)),
        analysis_elapsed_seconds=time.perf_counter()-start,sampling_performed=False,output_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    print(json.dumps(dict(audit=evidence,analysis_elapsed_seconds=time.perf_counter()-start,primary=tables['primary_summary_scenarios'].to_dict('records')),ensure_ascii=False))

if __name__=='__main__':main()
