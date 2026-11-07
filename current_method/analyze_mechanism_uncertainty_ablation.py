"""Independent audit/analysis of matched mechanism information; never simulates."""
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

VARIANTS=('calibrated_U','proxy_point','oracle_true_point')
MODES=('r2','rinf')
WORLD=('surface','scenario','replicate')
IDENT=WORLD+('variant','mode')
COLORS=dict(calibrated_U='#0F4D92',proxy_point='#B64342',oracle_true_point='#42949E')
LABELS=dict(calibrated_U='Calibrated sets',proxy_point='Proxy points (uncertified)',oracle_true_point='True locations (oracle)')

def read_json(p):return json.loads(p.read_text(encoding='utf-8'))
def read_jsonl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_json(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
def save_csv(p,frame):frame.to_csv(p,index=False,float_format='%.17g',lineterminator='\n')
def key(row,names):return tuple(row[n] for n in names)
def arr(value):return np.asarray(json.loads(value) if isinstance(value,str) else value)


def independent_parts(d,ids,a,mode):
    """Direct expansion of the two geometry bounds, independently of workflow."""
    a=np.asarray(a,float);ids=np.asarray(ids,int);c=np.asarray(d['centers'])[ids]
    r=np.asarray(d['radii'])[ids];target=np.asarray(d['target_center']);s=np.asarray(d['noise_sd'])[ids]
    rt=d['target_radius'];L=d['L'];H=d['H'];ns=len(d['centers'])
    q=math.sqrt(2*math.log(2*ns/d['zeta'])) if mode=='rinf' else math.sqrt(2*math.log(2*(d['budget']+1)/(d['zeta']/2)))
    cq=math.sqrt(2*math.log(2*ns/(d['zeta'] if mode=='rinf' else d['zeta']/2)))
    center=L*np.linalg.norm(np.sum(a[:,None]*c,axis=0)-target)
    radial=L*(rt+np.dot(a,r));curv=0.;center_curv=0.
    for i in range(len(a)):
        for j in range(len(a)):
            if i!=j:
                distance=np.linalg.norm(c[i]-c[j]);coef=H*a[i]*a[j]/4
                center_curv+=coef*distance**2;curv+=coef*(distance+r[i]+r[j])**2
    lip_center=L*np.dot(a,np.linalg.norm(c-target,axis=1))
    Bbar=center+radial+curv;BLip=lip_center+radial
    noise=q*(np.dot(a,s) if mode=='rinf' else np.sqrt(np.dot(a*a,s*s)))
    return dict(barycentric_center_offset=float(center),linear_set_radius=float(radial),center_curvature=float(center_curv),
        set_radius_curvature_inflation=float(curv-center_curv),total_curvature=float(curv),lipschitz_center_distance=float(lip_center),
        Bbar=float(Bbar),BLip=float(BLip),geometry_min=float(min(Bbar,BLip)),noise=float(noise),radius=float(min(Bbar,BLip)+noise),
        active_branch='barycentric' if Bbar<=BLip else 'lipschitz',coordinate_multiplier=cq)


def audit(raw):
    manifest=read_json(raw/'run_manifest.json');assert manifest['status']=='complete';cfg=manifest['config']
    for name,h in manifest['source_sha256'].items():assert digest(raw/'source_snapshot'/name)==h,name
    for name,h in manifest['artifact_sha256'].items():assert digest(raw/name)==h,name
    worlds=read_jsonl(raw/'world_audits.jsonl');designs=read_jsonl(raw/'variant_designs.jsonl');plans=read_jsonl(raw/'design_plans.jsonl')
    fixed=pd.read_csv(raw/'fixed_certificate_records.csv',float_precision='round_trip');stopped=pd.read_csv(raw/'stopped_output_records.csv',float_precision='round_trip')
    same=pd.read_csv(raw/'same_weight_diagnostics.csv',float_precision='round_trip');observations=pd.read_csv(raw/'common_observations.csv',float_precision='round_trip')
    nw=9*cfg['repetitions_per_cell'];assert len(worlds)==nw and len(fixed)==nw*24 and len(stopped)==nw*48 and len(same)==nw*24
    assert len(observations)==nw*7
    assert not fixed.duplicated(list(IDENT)+['stage']).any() and not stopped.duplicated(list(IDENT)+['tolerance','budget']).any()
    wd={key(w,WORLD):w for w in worlds};dd={key(d,WORLD+('variant',)):d for d in designs}
    pp={key(p,IDENT+('stage',)):p for p in plans}
    ff={key(r,IDENT+('stage',)):r for r in fixed.to_dict('records')}
    oo={key(r,WORLD+('source_id',)):r for r in observations.to_dict('records')}
    assert len(wd)==nw and len(dd)==nw*3 and len(pp)==nw*24
    differences=dict(geometry_components=0.,estimate=0.,refusal_endpoints=0.,stopped_endpoints=0.,same_weight_components=0.)
    cal_rows=[];same_checks=0
    for world_key,w in wd.items():
        scores=np.sort(w['calibration_scores']);rank=math.ceil((len(scores)+1)*(1-cfg['eta']))
        assert len(scores)==199 and scores[rank-1]==w['calibration_q'] and scores[-1]==w['calibration_max']
        order=np.random.default_rng(np.random.SeedSequence([cfg['seed'],w['surface_id'],w['scenario_id'],w['replicate'],20])).permutation(np.arange(4,10)).tolist()
        assert order==w['common_random_order']
        true=np.asarray(w['true_locations']);cal=dd[world_key+('calibrated_U',)]
        xx,yy=true.T
        if w['surface']=='linear':mu=.55*xx+.3*yy;expected_L=math.hypot(.55,.3);expected_H=0.
        elif w['surface']=='quadratic':mu=.5*xx+.2*yy+.06*(xx*xx+yy*yy);expected_L=math.hypot(.62,.32);expected_H=.12
        else:mu=.45*xx+.2*yy+.08*np.sin(2*xx);expected_L=math.hypot(.61,.2);expected_H=.32
        assert np.allclose(mu,w['truth'],atol=1e-14,rtol=0) and np.all(np.abs(true)<=1)
        assert cal['L']==expected_L and cal['H']==expected_H
        proxy=dd[world_key+('proxy_point',)];oracle=dd[world_key+('oracle_true_point',)]
        assert np.array_equal(cal['centers'],proxy['centers']) and np.array_equal(cal['target_center'],proxy['target_center'])
        assert np.all(np.asarray(cal['radii'])==cfg['proxy_scale']*w['calibration_q'])
        assert cal['target_radius']==cfg['proxy_scale']*w['calibration_q']
        assert not np.any(proxy['radii']) and proxy['target_radius']==0
        assert np.array_equal(oracle['centers'],true[:-1]) and np.array_equal(oracle['target_center'],true[-1])
        assert not np.any(oracle['radii']) and oracle['target_radius']==0
        for v,d in [('calibrated_U',cal),('proxy_point',proxy),('oracle_true_point',oracle)]:
            covered=bool(np.all(np.linalg.norm(np.asarray(d['centers'])-true[:-1],axis=1)<=np.asarray(d['radii'])+1e-14) and np.linalg.norm(np.asarray(d['target_center'])-true[-1])<=d['target_radius']+1e-14)
            assert covered==d['mechanism_event_holds'] and d['guarantee_applicable']==(v!='proxy_point')
            assert d['nominal_path_failure_bound']==(None if v=='proxy_point' else .1 if v=='calibrated_U' else .05)
            assert d['L']==cal['L'] and d['H']==cal['H'] and np.array_equal(d['noise_sd'],cal['noise_sd'])
        assert cal['mechanism_event_holds']==w['joint_set_covered']
        cal_rows.append(dict(zip(WORLD,world_key),joint_set_covered=w['joint_set_covered'],calibration_q=w['calibration_q'],radius=cal['target_radius']))
        for sid in list(range(4))+order[:3]:
            o=oo[world_key+(sid,)];assert o['n']==(800 if sid<4 else 96)
            assert np.isclose(o['effect'],o['treated_mean']-o['control_mean'],atol=1e-14)
            assert np.isclose(o['noise_sd'],1/np.sqrt(o['n']),atol=1e-14)
        for variant in VARIANTS:
            d=dd[world_key+(variant,)]
            for mode in MODES:
                last=np.inf
                for stage in range(4):
                    k=world_key+(variant,mode,stage);p=pp[k];f=ff[k];ids=list(range(4))+order[:stage];a=np.asarray(p['weights'])
                    assert p['ids']==ids and np.array_equal(arr(f['source_ids']),ids) and np.array_equal(arr(f['weights']),a)
                    assert np.min(a)>=0 and abs(a.sum()-1)<1e-8
                    g=independent_parts(d,ids,a,mode)
                    for name,value in g.items():
                        if name in ('coordinate_multiplier','active_branch'):continue
                        differences['geometry_components']=max(differences['geometry_components'],abs(value-f[name]),abs(value-p['geometry_parts'][name]))
                    assert abs(p['radius']-g['radius'])<1e-10 and g['radius']<=last+1e-8;last=g['radius']
                    effects=np.array([oo[world_key+(sid,)]['effect'] for sid in ids]);estimate=float(a@effects)
                    distances=np.linalg.norm(np.asarray(d['centers'])[ids]-d['target_center'],axis=1)+np.asarray(d['radii'])[ids]+d['target_radius']
                    half=g['coordinate_multiplier']*np.asarray(d['noise_sd'])[ids]+d['L']*distances
                    lower=float(np.max(effects-half));upper=float(np.min(effects+half))
                    differences['estimate']=max(differences['estimate'],abs(estimate-f['estimate']))
                    differences['refusal_endpoints']=max(differences['refusal_endpoints'],abs(lower-f['refusal_lower']),abs(upper-f['refusal_upper']))
                    assert f['refusal_status']==('finite' if lower<=upper else 'inconsistent')
                    assert f['new_n']==stage*96 and f['historical_n']==3200
                    assert f['truth']==w['truth'][-1]
                    assert f['guarantee_applicable']==d['guarantee_applicable'] and f['mechanism_event_holds']==d['mechanism_event_holds']
                    assert pd.isna(f['nominal_path_failure_bound']) if variant=='proxy_point' else f['nominal_path_failure_bound']==d['nominal_path_failure_bound']
                    assert np.isclose(f['absolute_error'],abs(estimate-f['truth'])) and np.isclose(f['squared_error'],(estimate-f['truth'])**2)
                    assert np.isclose(f['certificate_width'],2*g['radius']) and np.isclose(f['certificate_lower'],estimate-g['radius']) and np.isclose(f['certificate_upper'],estimate+g['radius'])
                    assert f['certificate_covered']==(estimate-g['radius']<=f['truth']<=estimate+g['radius'])
    ss={key(r,IDENT+('stage',)):r for r in same.to_dict('records')}
    for k,row in ss.items():
        world_key=k[:3];variant,mode,stage=k[3:];reference=pp[world_key+('calibrated_U',mode,stage)]
        assert np.array_equal(arr(row['weights']),reference['weights']) and np.array_equal(arr(row['source_ids']),reference['ids'])
        g=independent_parts(dd[world_key+(variant,)],reference['ids'],reference['weights'],mode)
        for name,value in g.items():
            if name not in ('coordinate_multiplier','active_branch'):differences['same_weight_components']=max(differences['same_weight_components'],abs(value-row[name]))
        cal=ss[world_key+('calibrated_U',mode,stage)]
        assert abs(row['noise']-cal['noise'])<1e-12
        if variant=='proxy_point' or (variant=='oracle_true_point' and wd[world_key]['joint_set_covered']):
            assert row['geometry_min']<=cal['geometry_min']+1e-11;same_checks+=1
    for row in stopped.to_dict('records'):
        ident=key(row,IDENT);radius=[ff[ident+(s,)]['radius'] for s in range(4)]
        hits=[s for s in range(4) if radius[s]<=row['tolerance']];first=hits[0] if hits else 3
        actual=min(row['budget'],first);f=ff[ident+(actual,)];released=f['radius']<=row['tolerance']
        lower=f['certificate_lower'] if released else f['refusal_lower'];upper=f['certificate_upper'] if released else f['refusal_upper']
        assert row['actual_stage']==actual and row['actual_new_n']==actual*96 and row['released']==released
        assert row['carried_after_stop']==(bool(hits) and row['budget']>first)
        assert row['new_observation']==(row['budget']>0 and not row['carried_after_stop'])
        assert np.array_equal(arr(row['acquired_bridge_ids']),wd[ident[:3]]['common_random_order'][:actual])
        assert np.array_equal(arr(row['source_ids']),arr(f['source_ids'])) and np.array_equal(arr(row['weights']),arr(f['weights']))
        differences['stopped_endpoints']=max(differences['stopped_endpoints'],abs(lower-row['lower']),abs(upper-row['upper']),abs(f['estimate']-row['estimate']))
        assert row['covered']==(lower<=row['truth']<=upper)
        assert row['bad_release']==(released and abs(row['estimate']-row['truth'])>row['tolerance'])
        assert row['interval_status']==('finite' if lower<=upper else 'inconsistent')
        assert row['certificate_covered']==f['certificate_covered']
    for _,group in stopped.groupby(list(IDENT)+['tolerance']):
        ordered=group.sort_values('budget')
        assert np.array_equal(ordered.path_covered,np.logical_and.accumulate(ordered.covered))
        assert np.array_equal(ordered.certificate_path_covered,np.logical_and.accumulate(ordered.certificate_covered))
    assert max(differences.values())<1e-9,differences
    evidence=dict(status='passed',profile=manifest['profile'],worlds=nw,fixed_states=len(fixed),stopped_rows=len(stopped),
        same_weight_comparisons=same_checks,max_absolute_differences=differences,
        sampling_performed=False,optimization_repeated=False,
        scope=['Independent explicit geometry/noise formulas; original simulator/optimizer not imported.',
               'Saved calibration scores sorted without regenerating random observations.',
               'Each variant uses its own refusal geometry; stopped outputs use only the acquired prefix.',
               'No verification of global optimization or real mechanism calibration.'])
    return manifest,fixed,stopped,same,pd.DataFrame(cal_rows),observations,evidence


def wilson(k,n):
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,float(center-half)),min(1.,float(center+half))


def summaries(fixed,stopped,same,calibration):
    fixed=fixed.copy()
    initial=fixed[fixed.stage==0].set_index(list(IDENT)).certificate_width
    fixed['initial_certificate_width']=[initial[tuple(r)] for r in fixed[list(IDENT)].itertuples(index=False,name=None)]
    fixed['width_reduction']=fixed.initial_certificate_width-fixed.certificate_width
    fixed['relative_width_reduction']=fixed.width_reduction/fixed.initial_certificate_width
    tables={}
    for aggregation,groups in [('cells',['surface','scenario','variant','mode','stage']),('scenarios',['scenario','variant','mode','stage'])]:
        rows=[]
        for values,g in fixed.groupby(groups):
            k=int(g.certificate_covered.sum());ci=wilson(k,len(g)) if aggregation=='cells' else (None,None)
            row=dict(zip(groups,values),n_worlds=len(g),new_participants=int(g.new_n.iloc[0]),
                mean_width=float(g.certificate_width.mean()),median_width=float(g.certificate_width.median()),q10_width=float(g.certificate_width.quantile(.1)),q90_width=float(g.certificate_width.quantile(.9)),
                mean_width_reduction=float(g.width_reduction.mean()),mean_relative_width_reduction=float(g.relative_width_reduction.mean()),
                mae=float(g.absolute_error.mean()),mse=float(g.squared_error.mean()),covered_count=k,coverage=k/len(g),coverage_wilson_low=ci[0],coverage_wilson_high=ci[1],
                mean_geometry=float(g.geometry_min.mean()),mean_noise=float(g.noise.mean()),
                mean_linear_set_radius=float(g.linear_set_radius.mean()),mean_center_curvature=float(g.center_curvature.mean()),
                mean_set_curvature_inflation=float(g.set_radius_curvature_inflation.mean()),
                refusal_inconsistent_count=int(g.refusal_status.eq('inconsistent').sum()),solver_failure_count=int(g.solver_failures.sum()))
            rows.append(row)
        tables['fixed_summary_'+aggregation]=pd.DataFrame(rows)
    terminal=stopped[stopped.budget==3]
    for aggregation,groups in [('cells',['surface','scenario','variant','mode','tolerance']),('scenarios',['scenario','variant','mode','tolerance'])]:
        rows=[]
        for values,g in terminal.groupby(groups):
            release=g[g.released];finite=g[g.interval_status=='finite']
            rows.append(dict(zip(groups,values),n_worlds=len(g),release_count=len(release),release_rate=len(release)/len(g),
                bad_release_count=int(g.bad_release.sum()),bad_release_rate=float(g.bad_release.mean()),
                conditional_bad_release_rate=float(release.bad_release.mean()) if len(release) else np.nan,
                released_mae=float(release.absolute_error.mean()) if len(release) else np.nan,
                mean_stopped_new_n=float(g.actual_new_n.mean()),median_stopped_new_n=float(g.actual_new_n.median()),
                returned_covered_count=int(g.covered.sum()),returned_coverage=float(g.covered.mean()),
                returned_path_covered_count=int(g.path_covered.sum()),returned_path_coverage=float(g.path_covered.mean()),
                certificate_path_covered_count=int(g.certificate_path_covered.sum()),certificate_path_coverage=float(g.certificate_path_covered.mean()),
                finite_returned_count=len(finite),inconsistent_count=int(g.interval_status.eq('inconsistent').sum()),
                mean_returned_width_among_finite=float(finite.width.mean()) if len(finite) else np.nan))
        tables['stopped_summary_'+aggregation]=pd.DataFrame(rows)
    pairs=[]
    cols=list(WORLD)+['mode','stage']
    reference=same[same.variant=='calibrated_U'].set_index(cols)
    for variant in VARIANTS[1:]:
        other=same[same.variant==variant].set_index(cols)
        pair=reference[['geometry_min','noise','radius','linear_set_radius','set_radius_curvature_inflation','mechanism_event_holds']].join(
            other[['geometry_min','noise','radius']],lsuffix='_cal',rsuffix='_other')
        pair['comparison']=variant
        pair['geometry_difference']=pair.geometry_min_cal-pair.geometry_min_other
        pair['noise_difference']=pair.noise_cal-pair.noise_other
        pair['radius_difference']=pair.radius_cal-pair.radius_other
        pairs.append(pair.reset_index())
    same_pairs=pd.concat(pairs,ignore_index=True)
    tables['same_weight_world_contrasts']=same_pairs
    rows=[]
    for values,g in same_pairs.groupby(['surface','scenario','comparison','mode','stage']):
        rows.append(dict(zip(['surface','scenario','comparison','mode','stage'],values),n_worlds=len(g),mean_geometry_difference=float(g.geometry_difference.mean()),
            median_geometry_difference=float(g.geometry_difference.median()),min_geometry_difference=float(g.geometry_difference.min()),max_absolute_noise_difference=float(g.noise_difference.abs().max()),
            mean_direct_set_radius=float(g.linear_set_radius.mean()),mean_set_curvature_inflation=float(g.set_radius_curvature_inflation.mean()),
            oracle_exceeds_cal_count=int(g.geometry_difference.lt(-1e-11).sum()),oracle_exceeds_on_covered_count=int((g.geometry_difference.lt(-1e-11)&g.mechanism_event_holds).sum())))
    tables['same_weight_summary_cells']=pd.DataFrame(rows)
    rows=[]
    for values,g in calibration.groupby(['surface','scenario']):
        k=int(g.joint_set_covered.sum());lo,hi=wilson(k,len(g))
        rows.append(dict(zip(['surface','scenario'],values),n_worlds=len(g),joint_covered_count=k,joint_coverage=k/len(g),wilson_low=lo,wilson_high=hi,mean_radius=float(g.radius.mean()),mean_calibration_q=float(g.calibration_q.mean())))
    tables['calibration_summary']=pd.DataFrame(rows)
    for scope in ['cells','scenarios']:
        f=tables['fixed_summary_'+scope]
        tables['primary_summary_'+scope]=f[(f['mode']=='r2')&(f.stage==3)].copy()
    return tables,fixed


def paired_bootstrap(fixed,cfg):
    """Prespecified paired resampling of worlds inside each original stratum."""
    primary=fixed[(fixed['mode']==cfg['primary_mode'])&(fixed.stage==cfg['primary_stage'])]
    metrics=['certificate_width','absolute_error','squared_error','certificate_covered','geometry_min','noise']
    B=cfg['bootstrap_repetitions'];rows=[];boot_by_cell={}
    for si,surface in enumerate(cfg['surfaces']):
        for gi,scenario in enumerate(cfg['scenarios']):
            group=primary[(primary.surface==surface)&(primary.scenario==scenario)]
            ref=group[group.variant=='calibrated_U'].sort_values('replicate').set_index('replicate')
            for vi,variant in enumerate(VARIANTS[1:]):
                alt=group[group.variant==variant].sort_values('replicate').set_index('replicate')
                assert ref.index.equals(alt.index)
                diff=ref[metrics].astype(float).to_numpy()-alt[metrics].astype(float).to_numpy()
                rng=np.random.default_rng(np.random.SeedSequence([cfg['bootstrap_seed'],si,gi,vi]))
                draws=rng.integers(0,len(diff),size=(B,len(diff)))
                boot=diff[draws].mean(axis=1);boot_by_cell[surface,scenario,variant]=(diff.mean(axis=0),boot)
                for j,metric in enumerate(metrics):
                    lo,hi=np.quantile(boot[:,j],[.025,.975])
                    rows.append(dict(surface=surface,scenario=scenario,comparison=variant,metric=metric,n_worlds=len(diff),
                        paired_mean_cal_minus_comparator=float(diff[:,j].mean()),exploratory_ci_low=float(lo),exploratory_ci_high=float(hi),bootstrap_repetitions=B))
    for scenario in cfg['scenarios']:
        for variant in VARIANTS[1:]:
            average=np.mean([boot_by_cell[s,scenario,variant][0] for s in cfg['surfaces']],axis=0)
            boot=np.mean([boot_by_cell[s,scenario,variant][1] for s in cfg['surfaces']],axis=0)
            for j,metric in enumerate(metrics):
                lo,hi=np.quantile(boot[:,j],[.025,.975])
                rows.append(dict(surface='equal_surface_pool',scenario=scenario,comparison=variant,metric=metric,n_worlds=3*cfg['repetitions_per_cell'],
                    paired_mean_cal_minus_comparator=float(average[j]),exploratory_ci_low=float(lo),exploratory_ci_high=float(hi),bootstrap_repetitions=B))
    return pd.DataFrame(rows)


def figures(out,tables,cfg):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],'font.size':9,
        'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'savefig.facecolor':'white'})
    data=tables['fixed_summary_scenarios'];data=data[data['mode']=='r2']
    fig,axs=plt.subplots(2,3,figsize=(12.5,6.4),layout='constrained')
    handles=[]
    for j,scenario in enumerate(cfg['scenarios']):
        for variant in VARIANTS:
            g=data[(data.scenario==scenario)&(data.variant==variant)].sort_values('stage')
            line=axs[0,j].plot(g.new_participants,g.mean_width,color=COLORS[variant],marker='o',ms=3,label=LABELS[variant])[0]
            axs[1,j].plot(g.new_participants,g.coverage,color=COLORS[variant],marker='o',ms=3)
            if j==0:handles.append(line)
        axs[0,j].set(title=scenario,xlabel='New participants',ylabel='Mean certificate width' if j==0 else '')
        axs[1,j].axhline(.90,color=COLORS['calibrated_U'],ls='--',lw=.8,alpha=.65)
        axs[1,j].axhline(.95,color=COLORS['oracle_true_point'],ls=':',lw=.8,alpha=.65)
        axs[1,j].set(xlabel='New participants',ylabel='Empirical certificate coverage' if j==0 else '',ylim=(min(.86,float(data.coverage.min())-.025),1.007))
        for ax in axs[:,j]:ax.set_xticks([0,96,192,288])
    fig.legend(handles=handles,labels=[LABELS[v] for v in VARIANTS],loc='outside lower center',ncols=3,frameon=False)
    fig.savefig(out/'mechanism_uncertainty_results.png',dpi=300,bbox_inches='tight')
    fig.savefig(out/'mechanism_uncertainty_results.pdf',bbox_inches='tight');plt.close(fig)


def mdtable(frame,formats=None):
    formats=formats or {};cols=list(frame.columns)
    def cell(name,v):
        if pd.isna(v):return '—'
        if name in formats:return formats[name](v)
        if isinstance(v,(float,np.floating)):return f'{v:.4g}'
        return str(v)
    return '\n'.join(['| '+' | '.join(cols)+' |','| '+' | '.join('---' for _ in cols)+' |']+['| '+' | '.join(cell(k,r[k]) for k in cols)+' |' for _,r in frame.iterrows()])


def report(out,manifest,fixed,stopped,same,calibration,observations,tables,evidence):
    cfg=manifest['config'];primary=tables['primary_summary_scenarios'];cell=tables['primary_summary_cells']
    release=tables['stopped_summary_scenarios'];release=release[release['mode']=='r2']
    paired=tables['paired_bootstrap'];pc=paired[(paired.surface=='equal_surface_pool')&paired.metric.eq('certificate_width')]
    trace=cfg['trace'];trace_fixed=fixed[(fixed.surface==trace['surface'])&(fixed.scenario==trace['scenario'])&(fixed.replicate==trace['replicate'])]
    shown=trace_fixed[(trace_fixed['mode']=='r2')&trace_fixed.stage.isin([0,3])][['variant','stage','Bbar','BLip','geometry_min','noise','radius']]
    wide=cell.pivot(index=['surface','scenario'],columns='variant',values='mean_width').reset_index()
    coverage=cell.pivot(index=['surface','scenario'],columns='variant',values='coverage').reset_index()
    minimum_proxy=cell[cell.variant=='proxy_point'].coverage.min()
    compact=primary[['scenario','variant','n_worlds','mean_width','mae','coverage','mean_geometry','mean_noise']]
    stopped_show=release[['scenario','variant','tolerance','release_count','n_worlds','mean_stopped_new_n','bad_release_count','released_mae','inconsistent_count']]
    no_release=release[release.release_count==0]
    text=rf'''# 机制集合不确定性消融

本轮完成 {len(calibration):,} 个独立世界：3种函数×3种机制菜单×每格{cfg['repetitions_per_cell']}世界。主比较为 **R2、固定288新增参与者**，Rinf及新增0、96、192人的预算点为预先规定的补充。所有方法共享4项历史研究、相同3桥随机前缀、同一批实际观察结果、L/H和噪声；只改变机制输入及据此优化的权重。

这检验的是原一般 **U/L/H、simplex权重、min(Bbar,BLip)** 计算证书；不是非高斯线性W选桥定理。当前采集顺序固定随机，没有检验定向选桥。三种输入不能被视作具有相同可用信息和理论保证的普通算法：

- `calibrated_U`：代理中心加联合校准球；在声明的合成条件下，每个policy的完整路径覆盖至少90%。
- `proxy_point`：同一代理中心但把半径设为0；忽略代理误差的负控制，**没有名义覆盖保证**。
- `oracle_true_point`：知道真实机制位置的理想参照；具有额外信息，使用相同噪声乘子时路径覆盖至少95%，不是可实施方法。

## 主结果：宽度、误差、覆盖一起看

以下按菜单汇总，每行包含三个函数等量的{3*cfg['repetitions_per_cell']}世界。宽度是固定预算下的**证书全宽**，不是拒绝外区间宽度；MAE使用全部目标，不筛选发布者。

本轮主要观察到保留集合不确定性带来的区间加宽与更谨慎的发布；calibrated_U和proxy_point的点估计误差非常接近。当前小代理误差设置没有出现严重的经验覆盖崩塌，不能据此声称已经实证证明忽略机制集合必然造成大量错误发布。

{mdtable(compact,{'coverage':lambda x:f'{x:.6f}'})}

proxy_point的九个格子中最低经验覆盖为 {minimum_proxy:.4%}。是否观察到漏盖，必须按这些实际结果解释；负控制在这个小代理噪声、保守统计项的设置中仍可能覆盖很好。没有因此为其补上理论保证，也没有增大噪声或调整阈值来制造失败。oracle与proxy表现接近也不说明代理已经等于真实机制。

![机制集合消融](mechanism_uncertainty_results.png)

上排为固定预算平均证书宽度，下排为对应真实目标经验覆盖，每菜单等权汇总三函数。虚线90%和点线95%分别标明calibrated与oracle的保守路径保证水平；proxy没有名义线。这些线不是每个格子经验覆盖必须达到的确定下限。经验覆盖并非条件于发布，也不把多个时点当独立重复。

所有九格的主预算平均宽度：

{mdtable(wide)}

对应证书覆盖：

{mdtable(coverage,{v:lambda x:f'{x:.6f}' for v in VARIANTS})}

各格MAE、MSE、分位数、误差项和每格覆盖Wilson区间见 `primary_summary_cells.csv`；所有预算和Rinf见 `fixed_summary_cells.csv`。菜单汇总只是描述，不将跨函数观测误当成同一条件下的重复实验。

## 不确定性具体加在什么地方

对实际单纯形权重a，记代理中心c、集合半径r、目标中心c*及目标半径r*：

$$\overline B=L\left(\left\|\sum_i a_ic_i-c_*\right\|+r_*+\sum_i a_ir_i\right)+\frac H4\sum_{{i\ne j}}a_i a_j(\|c_i-c_j\|+r_i+r_j)^2,$$

$$B_{{Lip}}=L\sum_i a_i(\|c_i-c_*\|+r_i+r_*),\qquad R=\min(\overline B,B_{{Lip}})+N(a).$$

半径r同时进入线性集合项和曲率中的距离膨胀；不能只删去 $L(r_*+\sum_i a_ir_i)$ 就声称完成集合消融。记录将中心曲率与半径引起的额外曲率分开。这里计算的是有效上界，未证明对一般机制集合取得精确最坏配置。

`same_weight_world_contrasts.csv` 在每world、mode、stage固定 **calibrated_U的实际权重**，再分别代入三种geometry；不会重新优化。该比较的噪声项一致。calibrated几何不小于proxy几何总是成立；对oracle仅在本次联合机制覆盖事件发生时保证该排序。独立审计检查了这两个不同的条件。原表中重新优化后的差异还包含权重改变，不能全部归为直接半径惩罚；SLSQP也没有全局最优保证。

主预算配对平均全宽差（calibrated减对照）及探索性95%区间：

{mdtable(pc[['scenario','comparison','n_worlds','paired_mean_cal_minus_comparator','exploratory_ci_low','exploratory_ci_high']])}

bootstrap使用预定seed={cfg['bootstrap_seed']}、{cfg['bootstrap_repetitions']}次，在每函数×菜单内部成对重采world，再对三个函数等权汇总。方法、阈值和阶段不另计样本。区间未作多重比较校正，不支持自动宣称所有对比显著优越。MAE/MSE、覆盖、几何和噪声的完整配对结果在 `paired_bootstrap.csv`。

## 发布与停止：与固定预算分开

这里从同一份已实际采集的完整前缀重建“首次R≤δ停止”的策略；它不是第二批独立实验。每个停止输出只使用该停点之前的Y，之后行标为carry，不能称为又采了96人。未发布时返回各自geometry计算的outer refusal envelope，不是sharp PI；发布时返回中心±证书半径。

{mdtable(stopped_show,{'released_mae':lambda x:f'{x:.5g}'})}

上表的成本是停止策略新增参与者平均值，完整预算的成本始终是stage×96。历史4×800人单列为共享既有资料。`bad_release_count` 是发布且真实误差超过δ的次数，分母为全部world；它不同于发布条件风险。零发布的组有 {len(no_release)} 行，其条件MAE保留缺失值“—”，不写0。

不同变体可能在不同世界、不同预算发布，因此条件MAE不能直接用来判断哪个估计器更准确；主表的全目标固定预算MAE才保持了共同评价分母。

停止后实际返回区间的覆盖、路径覆盖、有限区间宽度及不一致数见 `stopped_summary_cells.csv` / `stopped_summary_scenarios.csv`。有限宽度均值明确以有限区间为分母，空/不一致不能计为零宽成功。固定预算证书覆盖与停止时实际输出覆盖不能互相替代。

## 固定讲解例与校准检查

预先指定例为 {trace['surface']} / {trace['scenario']} / replicate {trace['replicate']}。stage0与stage3的实际权重对应半径分解：

{mdtable(shown)}

完整权重、各步来源及输出见 `single_world_fixed_states.csv`，实际两臂观察均值与效果见 `single_world_observations.csv`。同一bridge的Y只生成一次后供所有变体使用，oracle只额外获得机制位置，未读取效果真值优化。

{mdtable(tables['calibration_summary'][['surface','scenario','n_worlds','joint_covered_count','joint_coverage','mean_radius']],{'joint_coverage':lambda x:f'{x:.6f}'})}

校准每world使用199份独立合成archive、每份覆盖全部11个实体的最大误差分数。独立分析直接对保存的199个分数排序核对秩分位数，没有重新生成校准数据。实际某world的机制集合漏盖与是否具备校准论证是不同字段；不可把calibrated的偶发漏盖改成“前提从未成立”，也不可把proxy的经验成功改成“已经有保证”。真实机制集合来源及真实L/H仍未解决。

## 核验、时长与审稿范围

原运行 Git `{manifest['git_revision']}`，运行耗时 {manifest['elapsed_seconds']:.2f}秒，10项实现测试和{len(manifest['checks'])}项运行检查通过。初估full3–8分钟；smoke实测3.093秒后，根代理在运行前告知修正为2–4分钟、4CPU。分析核验与作图耗时另记于 `analysis_manifest.json`。没有启动真实数据拟合。

独立核验不导入实验实现或重新优化，检查 {evidence['fixed_states']:,} 个实际权重/公式状态和 {evidence['stopped_rows']:,} 个停止输出，重建source加权估计、Bbar/BLip/噪声、每个变体的拒绝端点与停止成本。最大绝对差为 `{json.dumps(evidence['max_absolute_differences'])}`；全部源与产物哈希已核对。统计事件的全路径预算沿用原4时点/10来源分配，不因oracle省下eta就额外缩小它的噪声项。

| 问题 | 本轮证据与限制 |
| --- | --- |
| REV-01 | 固定例与完整分解可帮助解释；不代替作者对文字的审阅 |
| REV-02 | 全部权重设计型；Rinf secondary不证明结果适应选择效用 |
| REV-03 | 数字明确归属一般U/L/H计算证书，不自动替换其他分支摘要 |
| REV-04 / KoBT.W1、WGDN.W2a | 隔离集合不确定性的宽度、误差与发布影响；合成校准不能回答真实U来源，保持open |
| REV-05 | 没有真实案例或微贷资格修复 |
| REV-06 | 不涉及Many Labs目标参考噪声 |
| REV-07 | 相同数据、路径和新增成本的组件对照；不证明相对direct或ExAtlas优势 |
| REV-08 | 不解决相关工作或新颖性归属 |
| REV-09 | 保留simplex；不证明它优于所有替代估计器 |
| REV-10 | 固定随机桥前缀，不检验新W或旧logdet选桥定理 |
| REV-11 | negative control、oracle与实际主方法身份明确；不完成全稿命名修复 |
| REV-12 | 固定证书、拒绝outer、停止风险、空区间和零发布分母分开 |

这些结果只构成相应问题的限定证据，没有自动将任何审稿问题标为resolved。
'''
    (out/'RESULTS.md').write_text(text,encoding='utf-8',newline='\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--raw',type=Path,required=True);parser.add_argument('--output',type=Path)
    args=parser.parse_args();raw=args.raw.resolve();start=time.perf_counter()
    manifest,fixed,stopped,same,calibration,observations,evidence=audit(raw)
    if args.output is None:print(json.dumps(evidence,ensure_ascii=False));return
    out=args.output.resolve()
    if out.exists():raise FileExistsError('Use a fresh report directory.')
    tables,fixed=summaries(fixed,stopped,same,calibration)
    tables['paired_bootstrap']=paired_bootstrap(fixed,manifest['config'])
    out.mkdir(parents=True)
    for name,frame in tables.items():save_csv(out/(name+'.csv'),frame)
    trace=manifest['config']['trace'];mask=(fixed.surface==trace['surface'])&(fixed.scenario==trace['scenario'])&(fixed.replicate==trace['replicate'])
    save_csv(out/'single_world_fixed_states.csv',fixed[mask])
    save_csv(out/'single_world_observations.csv',observations[(observations.surface==trace['surface'])&(observations.scenario==trace['scenario'])&(observations.replicate==trace['replicate'])])
    save_json(out/'independent_audit.json',evidence)
    figures(out,tables,manifest['config']);report(out,manifest,fixed,stopped,same,calibration,observations,tables,evidence)
    save_json(out/'analysis_manifest.json',dict(raw_directory=str(raw),raw_manifest_sha256=digest(raw/'run_manifest.json'),analysis_script_sha256=digest(Path(__file__)),
        analysis_elapsed_seconds=time.perf_counter()-start,sampling_performed=False,output_sha256={p.name:digest(p) for p in out.iterdir() if p.is_file()}))
    print(json.dumps(dict(audit=evidence,primary=tables['primary_summary_scenarios'].to_dict('records'),analysis_elapsed_seconds=time.perf_counter()-start),ensure_ascii=False))

if __name__=='__main__':main()
