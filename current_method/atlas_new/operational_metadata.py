"""Scientific-condition labels for the original 1-D operational experiment.

These are method/input conditions, not a claim that a realized interval covers.
They describe experiments.operational only, whose certificate is the exact
box-supremum barycentric bound (not the later min(Bbar, BLip) workflow).
No labels from this module may be inferred for an unknown method or scenario.
"""

SCENARIOS = frozenset(('nominal', 'extrapolation', 'proxy_shift',
                      'understated_LH', 'high_noise', 'bounded_nuisance_bias'))
CERTIFICATE_METHODS = frozenset(('robust_Rinf', 'design_R2', 'adaptive_Rinf',
                               'adaptive_R2_invalid', 'singleton_U', 'no_curvature'))
POINT_METHODS = frozenset(('ridge_source_only', 'archive_mean'))


def operational_condition_labels(scenario, method, eta, zeta):
    """Return sufficient-condition metadata without outcomes or effect truth.

    The original operational DGP is mu(m)=.6m+.3m^2 on [-1,1], with
    correct bounds L=1.2, H=.6. Its no_curvature method uses H=0 in Bbar;
    it has no BLip fallback. All rows also contain a separately computed
    L-only outer envelope using the ORIGINAL calibrated boxes, even when
    the method's certificate uses proxy singletons or no certificate exists.
    """
    if scenario not in SCENARIOS or method not in CERTIFICATE_METHODS | POINT_METHODS:
        raise ValueError(f'Unknown operational metadata input: {scenario}/{method}')
    if not 0 < eta < 1 or not 0 < zeta < 1:
        raise ValueError('Failure budgets must be in (0,1)')
    has_certificate = method in CERTIFICATE_METHODS
    exchangeable = scenario != 'proxy_shift'
    valid_l = scenario != 'understated_LH'
    valid_h = scenario != 'understated_LH' and method != 'no_curvature'
    valid_sets = exchangeable and method != 'singleton_U'
    valid_selection = method != 'adaptive_R2_invalid'
    reasons = []
    if has_certificate:
        if not exchangeable:
            reasons.append('proxy_error_scale_differs_from_calibration')
        if method == 'singleton_U':
            reasons.append('proxy_singletons_omit_calibrated_location_error')
        if not valid_l:
            reasons.append('declared_L_below_domain_gradient_supremum')
        if not valid_h:
            reasons.append('declared_H_below_domain_Hessian_supremum')
        if not valid_selection:
            reasons.append('design_R2_used_with_outcome_adaptive_weights')
    valid_certificate = has_certificate and valid_sets and valid_l and valid_h and valid_selection
    valid_outer = exchangeable and valid_l
    return {
        'metadata_schema_version': '2',
        'certificate_status': ('not_applicable_point_only' if not has_certificate else
                               'conditions_satisfied' if valid_certificate else 'unsupported_conditions'),
        'certificate_object': 'box_supremum_barycentric' if has_certificate else 'none',
        'certificate_set_role': ('none' if not has_certificate else
                                 'uncertified_proxy_singletons' if method == 'singleton_U' else 'calibrated_boxes'),
        'calibration_exchangeability_assumed_valid': exchangeable,
        'certificate_set_guarantee_applicable': valid_sets if has_certificate else None,
        'declared_L_valid_on_domain': valid_l if has_certificate else None,
        'declared_H_valid_on_domain': valid_h if has_certificate else None,
        'weight_selection_condition_satisfied': valid_selection if has_certificate else None,
        'sampling_and_nuisance_conditions_satisfied': True,
        'assumption_valid': valid_certificate if has_certificate else None,
        'certificate_guarantee_applicable': valid_certificate,
        'nominal_certificate_failure_bound': eta + zeta if valid_certificate else None,
        'certificate_unsupported_reasons': ';'.join(reasons),
        'outer_inputs_role': 'original_calibrated_boxes_and_declared_L',
        'outer_guarantee_applicable': valid_outer,
        'nominal_outer_failure_bound': eta + zeta if valid_outer else None,
        'guarantee_scope': 'unconditional_single_evaluated_output_not_conditional_on_release',
        'joint_set_covered_scope': 'realized_event_for_original_calibrated_boxes_not_method_assumptions',
    }
