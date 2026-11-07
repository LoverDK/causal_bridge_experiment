"""Matched input-information ablation for the original U/L/H workflow.

Acquisition order and observations are shared. Only an explicitly labelled
oracle constructor accepts true locations. No planning function accepts Y or
effect truth. The original implementation remains unchanged.
"""
from dataclasses import replace
import json
import numpy as np
from .workflow import make_world, collect, optimize, certificate, multipliers, refusal_envelope
from .core import calibrated_quantile

VARIANTS=('calibrated_U','proxy_point','oracle_true_point')
MODES=('r2','rinf')

def variant_design(base,variant,oracle_locations=None):
    if variant=='calibrated_U':
        return replace(base,centers=base.centers.copy(),radii=base.radii.copy(),
                       target_center=base.target_center.copy(),noise_sd=base.noise_sd.copy())
    if variant=='proxy_point':
        return replace(base,centers=base.centers.copy(),radii=np.zeros_like(base.radii),
                       target_center=base.target_center.copy(),target_radius=0.,noise_sd=base.noise_sd.copy())
    if variant=='oracle_true_point':
        if oracle_locations is None:raise ValueError('Oracle branch requires explicitly provided true locations')
        m=np.asarray(oracle_locations,float)
        return replace(base,centers=m[:-1].copy(),radii=np.zeros_like(base.radii),
                       target_center=m[-1].copy(),target_radius=0.,noise_sd=base.noise_sd.copy())
    raise ValueError(variant)

def geometry_parts(design,ids,weights,mode):
    ids=list(ids);a=np.asarray(weights,float);c=design.centers[ids];r=design.radii[ids]
    pair=np.linalg.norm(c[:,None]-c[None,:],axis=2)
    inflated=pair+r[:,None]+r[None,:];np.fill_diagonal(inflated,0.)
    bary_offset=design.L*float(np.linalg.norm(a@c-design.target_center))
    radial=design.L*float(design.target_radius+a@r)
    center_curvature=design.H/4*float(a@(pair**2)@a)
    total_curvature=design.H/4*float(a@(inflated**2)@a)
    curvature_inflation=total_curvature-center_curvature
    lip_center=design.L*float(a@np.linalg.norm(c-design.target_center,axis=1))
    q,_=multipliers(design,mode)
    noise=q*(float(a@design.noise_sd[ids]) if mode=='rinf' else float(np.linalg.norm(a*design.noise_sd[ids])))
    bbar=bary_offset+radial+total_curvature;blip=lip_center+radial
    radius=min(bbar,blip)+noise
    expected=certificate(design,ids,a,mode)
    if not np.isclose(radius,expected,rtol=1e-11,atol=1e-12):raise AssertionError('Component sum differs from original certificate')
    return dict(barycentric_center_offset=bary_offset,linear_set_radius=radial,
        center_curvature=center_curvature,set_radius_curvature_inflation=curvature_inflation,
        total_curvature=total_curvature,lipschitz_center_distance=lip_center,
        Bbar=bbar,BLip=blip,geometry_min=min(bbar,blip),active_branch='barycentric' if bbar<=blip else 'lipschitz',
        noise=noise,radius=radius)

def fixed_prefix_plan(design,mode,order):
    """Same ordered source prefix for every information variant and bound."""
    path=[]
    for stage in range(design.budget+1):
        ids=list(range(design.initial))+[int(i) for i in order[:stage]]
        warm=None if not path else np.r_[path[-1]['weights'],0.]
        p=optimize(design,ids,mode,warm)
        p.update(stage=stage,chosen=None if stage==0 else int(order[stage-1]),
                 geometry_parts=geometry_parts(design,ids,p['weights'],mode))
        if path and p['radius']>path[-1]['radius']+1e-8:
            raise AssertionError('Adding a source worsened the feasible certificate')
        path.append(p)
    return path

def condition_labels(variant,design,true_locations):
    actual=np.asarray(true_locations,float)
    covered=bool(np.all(np.linalg.norm(design.centers-actual[:-1],axis=1)<=design.radii+1e-14)
                 and np.linalg.norm(design.target_center-actual[-1])<=design.target_radius+1e-14)
    return dict(input_role={'calibrated_U':'calibrated_mechanism_sets',
        'proxy_point':'invalid_negative_control_ignores_proxy_error',
        'oracle_true_point':'ideal_oracle_extra_mechanism_information'}[variant],
        guarantee_applicable=variant!='proxy_point',mechanism_event_holds=covered,
        sampling_assumptions_valid=True,smoothness_assumptions_valid=True,
        nominal_path_failure_bound=None if variant=='proxy_point' else
            design.zeta+(design.eta if variant=='calibrated_U' else 0.))

def evaluate_prefix(design,path,observations,mode):
    """No effect truth is accepted. Refusal uses this exact variant's geometry."""
    ids=path['ids'];weights=path['weights'];radius=path['radius']
    estimate=float(np.dot(weights,[observations[i]['effect'] for i in ids]))
    lo,hi=refusal_envelope(design,ids,observations,mode)
    return dict(stage=path['stage'],source_ids=ids,weights=weights,estimate=estimate,radius=radius,
        certificate_lower=estimate-radius,certificate_upper=estimate+radius,certificate_width=2*radius,
        refusal_lower=lo,refusal_upper=hi,refusal_width=hi-lo if lo<=hi else None,
        refusal_status='finite' if lo<=hi else 'inconsistent',
        solver_successes=path['solver_successes'],solver_failures=path['solver_failures'],
        **{k:v for k,v in path['geometry_parts'].items() if k!='radius'})

def stopped_outputs(fixed,order,tolerance,cfg):
    """Reconstruct stopped-policy outputs using only each acquired prefix.

    The full-budget paired trajectory is sampled separately. Carried states
    never use later observations and are not counted as new acquisitions.
    """
    stopped=None;rows=[]
    for budget,state in enumerate(fixed):
        if stopped is None:
            released=state['radius']<=tolerance;stage=state['stage']
            lo,hi=(state['certificate_lower'],state['certificate_upper']) if released else (state['refusal_lower'],state['refusal_upper'])
            current=dict(state,budget=budget,actual_stage=stage,actual_bridges=stage,
                actual_new_n=stage*cfg['participants_per_bridge'],acquired_bridge_ids=[int(i) for i in order[:stage]],
                released=released,lower=lo,upper=hi,width=hi-lo if lo<=hi else None,
                interval_status='finite' if lo<=hi else 'inconsistent',
                new_observation=stage>0,carried_after_stop=False,
                refusal_reason='released' if released else 'budget_exhausted' if budget==cfg['max_bridges'] else 'radius_above_tolerance')
            if released:stopped=current
        else:
            current=dict(stopped,budget=budget,new_observation=False,carried_after_stop=True)
        rows.append(current)
    return rows

def run_world(task):
    cfg,surface_id,scenario_id,replicate=task
    world=make_world(cfg,surface_id,scenario_id,replicate);base=world['design']
    meta={k:world[k] for k in ['surface','scenario','replicate']}
    rng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],surface_id,scenario_id,replicate,20]))
    order=rng.permutation(np.arange(base.initial,len(base.centers))).tolist()
    designs={v:variant_design(base,v,world['locations'] if v=='oracle_true_point' else None) for v in VARIANTS}
    # Complete all design-only optimization before acquiring observations.
    plans={(v,m):fixed_prefix_plan(designs[v],m,order) for v in VARIANTS for m in MODES}
    ids=list(range(base.initial))+order[:base.budget]
    observations={i:collect(world,i,cfg['archive_participants'] if i<base.initial else cfg['participants_per_bridge']) for i in ids}
    acquisition=[dict(**meta,stage=0 if i<base.initial else order.index(i)+1,
        role='history' if i<base.initial else 'fixed_budget_bridge',**observations[i]) for i in ids]
    plan_rows=[];fixed_rows=[];stopped_rows=[];same_rows=[];design_rows=[]
    truth=float(world['truth'][-1])  # Scoring only, after all plans and sampling.
    for variant,d in designs.items():
        labels=condition_labels(variant,d,world['locations'])
        design_rows.append(dict(**meta,variant=variant,centers=d.centers.tolist(),radii=d.radii.tolist(),
            target_center=d.target_center.tolist(),target_radius=d.target_radius,noise_sd=d.noise_sd.tolist(),
            L=d.L,H=d.H,initial=d.initial,budget=d.budget,eta=d.eta,zeta=d.zeta,**labels))
        for mode in MODES:
            identity=dict(**meta,variant=variant,mode=mode,method_id=f'{variant}_{mode}_fixed_random',**labels)
            path=plans[variant,mode]
            plan_rows.extend(dict(**identity,**p) for p in path)
            unscored=[evaluate_prefix(d,p,observations,mode) for p in path]
            for p,state in zip(path,unscored):
                error=state['estimate']-truth
                fixed_rows.append(dict(**identity,**state,new_n=p['stage']*cfg['participants_per_bridge'],
                    historical_n=base.initial*cfg['archive_participants'],truth=truth,error=error,
                    absolute_error=abs(error),squared_error=error**2,
                    certificate_covered=state['certificate_lower']<=truth<=state['certificate_upper'],
                    refusal_covered=state['refusal_lower']<=truth<=state['refusal_upper']))
                reference=plans['calibrated_U',mode][p['stage']]
                same_rows.append(dict(**identity,stage=p['stage'],weight_source='calibrated_U',
                    source_ids=reference['ids'],weights=reference['weights'],
                    **geometry_parts(d,reference['ids'],reference['weights'],mode)))
            for tolerance in cfg['tolerances']:
                path_covered=True;certificate_path_covered=True
                for state in stopped_outputs(unscored,order,tolerance,cfg):
                    error=state['estimate']-truth;covered=state['lower']<=truth<=state['upper']
                    certcovered=state['certificate_lower']<=truth<=state['certificate_upper']
                    path_covered=path_covered and covered;certificate_path_covered=certificate_path_covered and certcovered
                    stopped_rows.append(dict(**identity,tolerance=tolerance,**state,truth=truth,error=error,
                        absolute_error=abs(error),covered=covered,path_covered=path_covered,
                        certificate_covered=certcovered,certificate_path_covered=certificate_path_covered,
                        bad_release=bool(state['released'] and abs(error)>tolerance),
                        execution_scope='stopped_policy_reconstructed_from_shared_observed_prefix_no_resampling'))
    audit=dict(**meta,seed=cfg['seed'],surface_id=surface_id,scenario_id=scenario_id,
        common_random_order=order,true_locations=world['locations'].tolist(),truth=world['truth'].tolist(),
        calibration_q=world['calibration_q'],calibration_max=world['calibration_max'],
        max_standardized_proxy_error=world['max_standardized_proxy_error'],joint_set_covered=world['joint_set_covered'],
        calibration_archives=cfg['calibration_archives'],calibration_scores_source='exact replay of original make_world seed; no independent extra calibration worlds',
        proxy_scale=cfg['proxy_scale'],L=base.L,H=base.H)
    # Expose the original calibration draws without changing the old generator.
    calrng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],surface_id,scenario_id,replicate,0]))
    calrng.normal(0,.025,(len(base.centers),2))
    errors=calrng.normal(size=(cfg['calibration_archives'],len(base.centers)+1,2))
    scores=np.linalg.norm(errors,axis=2).max(axis=1)
    if calibrated_quantile(scores,cfg['eta'])!=world['calibration_q']:
        raise AssertionError('Calibration replay differs from original generator')
    audit['calibration_scores']=scores.tolist()
    return fixed_rows,stopped_rows,same_rows,plan_rows,design_rows,acquisition,audit
