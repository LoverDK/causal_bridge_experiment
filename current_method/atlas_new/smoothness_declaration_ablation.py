"""One-factor declarations of L and H on shared calibrated mechanism sets.

Declaration validity, the assumptions needed by a branch, and validity of an
actually returned bound are separate. Numerical near-ties never upgrade a
method's nominal policy guarantee.
"""
from dataclasses import replace
import numpy as np
from .workflow import make_world,collect
from .core import calibrated_quantile
from .mechanism_uncertainty_ablation import geometry_parts,fixed_prefix_plan,evaluate_prefix,stopped_outputs

VARIANTS=('baseline','L_half','L_double','H_zero','H_double')
MODES=('r2','rinf')
FACTORS={'baseline':(1.,1.),'L_half':(.5,1.),'L_double':(2.,1.),'H_zero':(1.,0.),'H_double':(1.,2.)}

def declared_design(base,variant):
    ls,hs=FACTORS[variant]
    return replace(base,L=base.L*ls,H=base.H*hs,centers=base.centers.copy(),radii=base.radii.copy(),
                   target_center=base.target_center.copy(),noise_sd=base.noise_sd.copy())

def declaration_labels(base,declared,variant,joint_event):
    lv=bool(declared.L>=base.L);hv=bool(declared.H>=base.H);valid=lv and hv
    return dict(reference_L=base.L,reference_H=base.H,declared_L=declared.L,declared_H=declared.H,
        L_factor=FACTORS[variant][0],H_factor=FACTORS[variant][1],declared_L_valid=lv,declared_H_valid=hv,
        smoothness_declaration_valid=valid,guarantee_applicable=valid,
        mechanism_event_holds=bool(joint_event),mechanism_calibration_valid=True,sampling_assumptions_valid=True,
        barycentric_assumptions_valid=valid,lipschitz_assumptions_valid=lv,refusal_bound_valid=lv,
        nominal_path_failure_bound=base.eta+base.zeta if valid else None,
        information_role='valid_declared_smoothness' if valid else 'underdeclared_smoothness_negative_control')

def branch_labels(parts,labels,tolerance):
    minimum=parts['geometry_min'];valid=[]
    if labels['barycentric_assumptions_valid']:valid.append(('barycentric',parts['Bbar']))
    if labels['lipschitz_assumptions_valid']:valid.append(('lipschitz',parts['BLip']))
    strict=[name for name,value in valid if value<=minimum]
    near=[name for name,value in valid if value<=minimum+tolerance]
    return dict(selected_bound_valid=bool(strict),valid_branches_attaining_min=strict,
        valid_branch_near_min=bool(near),valid_branches_near_min=near,numeric_tie_tolerance=tolerance,
        gap_to_valid_geometry=min(value for _,value in valid)-minimum if valid else None,
        validity_scope='strict float comparison for selected bound; near-tie diagnostic does not upgrade any policy guarantee')

def score_errors(state,truth,observations,tolerance):
    """Post-planning diagnostics only; this function never returns a decision."""
    ids=state['source_ids'];a=np.asarray(state['weights'])
    true_sources=np.asarray(truth)[ids]
    causal=float(a@true_sources-truth[-1])
    sampling=float(a@(np.array([observations[i]['effect'] for i in ids])-true_sources))
    error=float(state['estimate']-truth[-1]);excess=abs(causal)-state['geometry_min']
    if abs(error-causal-sampling)>tolerance:raise AssertionError('Signed error decomposition mismatch')
    return dict(truth=float(truth[-1]),error=error,absolute_error=abs(error),squared_error=error**2,
        causal_error=causal,sampling_error=sampling,causal_absolute_error=abs(causal),
        sampling_absolute_error=abs(sampling),causal_geometry_excess=excess,
        causal_exceeds_declared_geometry=excess>0,
        causal_exceeds_declared_geometry_tolerant=excess>tolerance,causal_check_tolerance=tolerance)

def run_world(task):
    cfg,surface_id,scenario_id,replicate=task
    world=make_world(cfg,surface_id,scenario_id,replicate);base=world['design']
    meta={k:world[k] for k in ['surface','scenario','replicate']}
    order=np.random.default_rng(np.random.SeedSequence([cfg['seed'],surface_id,scenario_id,replicate,20])).permutation(np.arange(4,10)).tolist()
    designs={v:declared_design(base,v) for v in VARIANTS}
    plans={(v,m):fixed_prefix_plan(designs[v],m,order) for v in VARIANTS for m in MODES}
    ids=list(range(4))+order[:3]
    obs={i:collect(world,i,cfg['archive_participants'] if i<4 else cfg['participants_per_bridge']) for i in ids}
    acquisitions=[dict(**meta,stage=0 if i<4 else order.index(i)+1,role='history' if i<4 else 'fixed_budget_bridge',**obs[i]) for i in ids]
    truth=float(world['truth'][-1])  # Scoring only, after every design plan.
    fixed=[];stopped=[];same=[];plan_rows=[];design_rows=[]
    for variant,d in designs.items():
        labels=declaration_labels(base,d,variant,world['joint_set_covered'])
        design_rows.append(dict(**meta,variant=variant,centers=d.centers.tolist(),radii=d.radii.tolist(),
            target_center=d.target_center.tolist(),target_radius=d.target_radius,noise_sd=d.noise_sd.tolist(),
            L=d.L,H=d.H,initial=d.initial,budget=d.budget,eta=d.eta,zeta=d.zeta,**labels))
        for mode in MODES:
            identity=dict(**meta,variant=variant,mode=mode,method_id=f'{variant}_{mode}_fixed_random',**labels)
            path=plans[variant,mode]
            states=[]
            for p in path:
                bl=branch_labels(p['geometry_parts'],labels,cfg['branch_tie_tolerance'])
                plan_rows.append(dict(**identity,**p,**bl))
                states.append(dict(evaluate_prefix(d,p,obs,mode),**bl))
            path_valid=all(s['selected_bound_valid'] for s in states)
            for p,state in zip(path,states):
                scored=score_errors(state,world['truth'],obs,cfg.get('causal_check_tolerance',1e-10))
                if labels['smoothness_declaration_valid'] and world['joint_set_covered'] and scored['causal_exceeds_declared_geometry_tolerant']:
                    raise AssertionError('Valid smoothness and covered mechanism sets failed causal geometry bound')
                fixed.append(dict(**identity,**state,path_all_selected_bounds_valid=path_valid,
                    new_n=p['stage']*cfg['participants_per_bridge'],historical_n=4*cfg['archive_participants'],
                    **scored,
                    certificate_covered=state['certificate_lower']<=truth<=state['certificate_upper'],
                    refusal_covered=state['refusal_lower']<=truth<=state['refusal_upper']))
                reference=plans['baseline',mode][p['stage']]
                parts=geometry_parts(d,reference['ids'],reference['weights'],mode)
                same.append(dict(**identity,stage=p['stage'],weight_source='baseline',source_ids=reference['ids'],
                    weights=reference['weights'],**parts,**branch_labels(parts,labels,cfg['branch_tie_tolerance'])))
            for tolerance in cfg['tolerances']:
                path_covered=True;cert_path_covered=True;output_path_valid=True
                for state in stopped_outputs(states,order,tolerance,cfg):
                    scored=score_errors(state,world['truth'],obs,cfg.get('causal_check_tolerance',1e-10))
                    covered=state['lower']<=truth<=state['upper']
                    cc=state['certificate_lower']<=truth<=state['certificate_upper']
                    path_covered=path_covered and covered;cert_path_covered=cert_path_covered and cc
                    output_valid=state['selected_bound_valid'] if state['released'] else labels['refusal_bound_valid']
                    output_path_valid=output_path_valid and output_valid
                    stopped.append(dict(**identity,tolerance=tolerance,**state,**scored,covered=covered,path_covered=path_covered,
                        certificate_covered=cc,certificate_path_covered=cert_path_covered,
                        returned_output_bound_valid=output_valid,
                        path_all_output_bound_assumptions_satisfied=output_path_valid,
                        returned_output_basis='selected_certificate' if state['released'] else 'L_only_refusal_envelope',
                        bad_release=bool(state['released'] and scored['absolute_error']>tolerance),
                        execution_scope='stopped_policy_reconstructed_from_shared_observed_prefix_no_resampling'))
    calrng=np.random.default_rng(np.random.SeedSequence([cfg['seed'],surface_id,scenario_id,replicate,0]))
    calrng.normal(0,.025,(10,2));errors=calrng.normal(size=(cfg['calibration_archives'],11,2))
    scores=np.linalg.norm(errors,axis=2).max(axis=1)
    if calibrated_quantile(scores,cfg['eta'])!=world['calibration_q']:raise AssertionError('Calibration replay changed')
    audit=dict(**meta,seed=cfg['seed'],surface_id=surface_id,scenario_id=scenario_id,common_random_order=order,
        true_locations=world['locations'].tolist(),truth=world['truth'].tolist(),reference_L=base.L,reference_H=base.H,
        calibration_q=world['calibration_q'],calibration_max=world['calibration_max'],calibration_scores=scores.tolist(),
        max_standardized_proxy_error=world['max_standardized_proxy_error'],joint_set_covered=world['joint_set_covered'],
        calibration_archives=cfg['calibration_archives'],proxy_scale=cfg['proxy_scale'])
    return fixed,stopped,same,plan_rows,design_rows,acquisitions,audit
