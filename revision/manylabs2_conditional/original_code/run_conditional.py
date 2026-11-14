"""Frozen, assumption-conditional numerics. This program never opens target outcomes."""
from pathlib import Path
import sys, json, hashlib, csv, argparse, math
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor'))
import numpy as np
import pandas as pd
import scipy.sparse as sp
from scipy.stats import norm, t as student_t
import clarabel

L = math.sqrt(8 / 3)
ZETA2 = .025 / (17 * 4)
C2 = math.sqrt(2 * math.log(2 / ZETA2))
CINF = math.sqrt(2 * math.log(2 * 40 / .025))
POLICIES = ['uniform', 'design_inverse_variance', 'optimized_R2', 'optimized_Rinf', 'fixed_effect', 'random_effects']
DESIGN = POLICIES[:4]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def profile(frame):
    n = len(frame)
    known = np.array([(frame.sex == k).sum() for k in (1, 2, 3)], float)
    unknown = n - known.sum()
    assert n and unknown >= 0
    assert frame.sex.dropna().isin([1, 2, 3, 4]).all()
    return known / n, unknown / n

def arm_profile(frame, treatment):
    part = frame[frame['T'] == treatment]
    return profile(part)

def imbalance(frame):
    l1, r1 = arm_profile(frame, 1)
    l0, r0 = arm_profile(frame, 0)
    return max(.5 * np.abs(l1 + r1 * np.eye(3)[b] - l0 - r0 * np.eye(3)[c]).sum()
               for b in range(3) for c in range(3))

def mismatch(alpha, target_l, target_r, source_l, source_r):
    center = target_l - alpha @ source_l
    r = float(alpha @ source_r)
    values = [L * np.linalg.norm(center + target_r * np.eye(3)[b] - r * np.eye(3)[c])
              for b in range(3) for c in range(3)]
    return float(max(values)), int(np.argmax(values))

def solve_weights(target_l, target_r, source_l, source_r, beta, s, family, target):
    """Primal-dual SOCP: nonnegative simplex, nine profile cones, optional noise cone."""
    m = len(beta)
    nvar = m + 1 + (family == 'R2')
    ti = m
    ni = m + 1
    q = np.zeros(nvar)
    q[:m] = beta + (CINF * s if family == 'Rinf' else 0)
    q[ti] = 1
    if family == 'R2':
        q[ni] = C2
    matrices, rhs, cones = [], [], []
    row = np.zeros((1, nvar)); row[0, :m] = 1
    matrices.append(row); rhs.append(np.ones(1)); cones.append(clarabel.ZeroConeT(1))
    row = np.zeros((m, nvar)); row[:, :m] = -np.eye(m)
    matrices.append(row); rhs.append(np.zeros(m)); cones.append(clarabel.NonnegativeConeT(m))
    for b in range(3):
        for c in range(3):
            row = np.zeros((4, nvar)); row[0, ti] = -1 / L
            row[1:, :m] = (source_l + source_r[:, None] * np.eye(3)[c]).T
            matrices.append(row); rhs.append(np.r_[0, target_l + target_r * np.eye(3)[b]])
            cones.append(clarabel.SecondOrderConeT(4))
    if family == 'R2':
        row = np.zeros((m + 1, nvar)); row[0, ni] = -1
        row[1:, :m] = -np.diag(s)
        matrices.append(row); rhs.append(np.zeros(m + 1)); cones.append(clarabel.SecondOrderConeT(m + 1))
    A = sp.csc_matrix(np.vstack(matrices)); b = np.concatenate(rhs)
    settings = clarabel.DefaultSettings()
    settings.verbose = False; settings.max_iter = 500
    attempts = []
    for requested_tolerance in [1e-10, 1e-9, 1e-8]:
        settings.tol_gap_abs = requested_tolerance
        settings.tol_gap_rel = requested_tolerance
        settings.tol_feas = requested_tolerance
        solution = clarabel.DefaultSolver(sp.csc_matrix((nvar, nvar)), q, A, b, cones, settings).solve()
        attempts.append(dict(requested_tolerance=requested_tolerance,status=str(solution.status),
                             gap=float(solution.obj_val-solution.obj_val_dual),
                             primal_residual=float(solution.r_prim),dual_residual=float(solution.r_dual)))
        if str(solution.status) == 'Solved':
            break
    alpha_raw = np.asarray(solution.x[:m])
    alpha = np.maximum(alpha_raw, 0); alpha /= alpha.sum()
    bu, active = mismatch(alpha, target_l, target_r, source_l, source_r)
    noise = C2 * np.linalg.norm(s * alpha) if family == 'R2' else CINF * (alpha @ s)
    actual = bu + alpha @ beta + noise
    dual = float(solution.obj_val_dual)
    gap = actual - dual
    audit = dict(target=target, family=family, solver='Clarabel', solver_version=clarabel.__version__,
                 status=str(solution.status), iterations=solution.iterations,
                 requested_tolerance=requested_tolerance,solver_attempt_count=len(attempts),solver_attempts=json.dumps(attempts),
                 primal_solver_objective=float(solution.obj_val), primal_recomputed=float(actual),
                 dual_objective=dual, primal_dual_gap=float(gap), primal_residual=float(solution.r_prim),
                 dual_residual=float(solution.r_dual), raw_min_weight=float(alpha_raw.min()),
                 raw_simplex_error=float(abs(alpha_raw.sum()-1)), repaired_l1=float(np.abs(alpha-alpha_raw).sum()),
                 active_profile_vertex_b=active//3, active_profile_vertex_c=active%3)
    audit['numerically_optimal'] = bool(str(solution.status) == 'Solved' and gap >= -1e-7 and gap < 1e-7
                                         and solution.r_prim < 1e-7 and solution.r_dual < 1e-7)
    if not audit['numerically_optimal']:
        raise RuntimeError('Optimization failed audit: ' + json.dumps(audit))
    return alpha, audit

def dump_csv(path, rows):
    pd.DataFrame(rows).to_csv(path, index=False, float_format='%.17g')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true', help='Only alphabetically first target; uses unchanged full 17-target inference budget.')
    args = parser.parse_args()
    data, out = ROOT / 'data', ROOT / 'results'
    out.mkdir(exist_ok=True)
    design = pd.read_csv(data / 'all_design.csv')
    split = pd.read_csv(data / 'frozen_site_split.csv')
    profile_audit = pd.read_csv(data / 'sex_profile_set_audit.csv')
    assert 'Y' not in design.columns
    sources = sorted(split.loc[split.role != 'sealed_target', 'source'])
    all_targets = sorted(split.loc[split.role == 'sealed_target', 'source'])
    assert len(sources) == 40 and len(all_targets) == 17
    targets = all_targets[:1] if args.smoke else all_targets
    groups = {site: design[design.source == site] for site in sources + all_targets}
    assert len(design) == sum(len(f) for f in groups.values())
    # Mandatory independent count comparison: the profile audit contains no response outcomes.
    for site, frame in groups.items():
        a = profile_audit.set_index('source').loc[site]
        counts = [(frame.sex == k).sum() for k in (1,2,3)]
        assert counts == [a.male_n, a.female_n, a.other_n], site
        assert len(frame) == a.canonical_cohort_n
        assert len(frame)-sum(counts) == a.unknown_substantive_category_n
    source_l, source_r = map(np.array, zip(*(profile(groups[z]) for z in sources)))
    beta = np.array([imbalance(groups[z]) for z in sources])
    n1 = np.array([(groups[z]['T'] == 1).sum() for z in sources])
    n0 = np.array([(groups[z]['T'] == 0).sum() for z in sources])
    assert np.all(n1 > 1) and np.all(n0 > 1)
    s = .5 * np.sqrt(1/n1 + 1/n0)
    frozen, opt_audits, source_inputs = {}, [], []
    # All design policies are calculated before reading even the source response file.
    for target in targets:
        tl, tr = profile(groups[target])
        inv = 1/s**2; inv /= inv.sum()
        policies = dict(uniform=np.ones(40)/40, design_inverse_variance=inv)
        for family in ['R2','Rinf']:
            alpha, audit = solve_weights(tl,tr,source_l,source_r,beta,s,family,target)
            policies['optimized_'+family] = alpha; opt_audits.append(audit)
        frozen[target] = policies
        for i, site in enumerate(sources):
            source_inputs.append(dict(target=target, source=site, n=int(n1[i]+n0[i]), n1=int(n1[i]), n0=int(n0[i]),
                                      male_lower=source_l[i,0],female_lower=source_l[i,1],other_lower=source_l[i,2],unknown_mass=source_r[i],
                                      beta_imbalance=beta[i],s=s[i],target_male_lower=tl[0],target_female_lower=tl[1],
                                      target_other_lower=tl[2],target_unknown_mass=tr,
                                      profile_eta=0,conditional_accurate_observed_labels=True))
    frozen_payload = {z:{p:a.tolist() for p,a in ps.items()} for z,ps in frozen.items()}
    frozen_hash = hashlib.sha256(json.dumps(frozen_payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    # Only now read source outcomes. This path contains no sealed-target rows.
    source = pd.read_csv(data / 'source_only.csv')
    assert sorted(source.source.unique()) == sources
    assert len(source) == 4365 and source.Y.isin([0,1]).all()
    assert set(zip(source.source, source.uID)) == set(zip(design[design.source.isin(sources)].source, design[design.source.isin(sources)].uID))
    effects, variances, source_results = [], [], []
    for i, site in enumerate(sources):
        f = source[source.source == site]
        p1, p0 = f.loc[f['T']==1,'Y'].mean(), f.loc[f['T']==0,'Y'].mean()
        assert (f['T']==1).sum() == n1[i] and (f['T']==0).sum() == n0[i]
        theta = p1-p0
        rawv = p1*(1-p1)/(n1[i]-1) + p0*(1-p0)/(n0[i]-1)
        v = rawv if rawv > 0 else s[i]**2
        effects.append(theta); variances.append(v)
        source_results.append(dict(source=site,n1=int(n1[i]),n0=int(n0[i]),p1=p1,p0=p0,estimate=theta,
                                   estimated_variance_raw=rawv,estimated_variance_used=v,zero_variance_countproxy_fallback=rawv<=0))
    effects, variances = np.array(effects), np.array(variances)
    wfe = 1/variances; afe = wfe/wfe.sum(); mu_fe = afe@effects
    Q = float(wfe@((effects-mu_fe)**2)); df = len(sources)-1
    denom = wfe.sum() - (wfe@wfe)/wfe.sum()
    tau2 = max(0, (Q-df)/denom)
    wre = 1/(variances+tau2); are = wre/wre.sum()
    native_fe = norm.ppf(.975)/math.sqrt(wfe.sum())
    native_re = student_t.ppf(.975,df)*math.sqrt(tau2+1/wre.sum())
    rows, weight_rows, sensitivity = [], [], []
    for target in targets:
        tl,tr = profile(groups[target])
        policies = dict(frozen[target],fixed_effect=afe,random_effects=are)
        for policy,alpha in policies.items():
            bu,active = mismatch(alpha,tl,tr,source_l,source_r)
            bb = float(alpha@beta); noise2=float(C2*np.linalg.norm(alpha*s)); noiseinf=float(CINF*(alpha@s))
            r2, ri = bu+bb+noise2, bu+bb+noiseinf
            admissible2 = policy in DESIGN
            chosen = 'R2' if policy in POLICIES[:3] else 'Rinf'
            radius = r2 if chosen=='R2' else ri
            estimate = float(alpha@effects)
            native = native_fe if policy=='fixed_effect' else native_re if policy=='random_effects' else float('nan')
            row = dict(target=target,policy=policy,numerical_status='computed_conditional',qualification_status='assumption_conditional_only',
                       estimate=estimate,geometry_G_U=bu,B_U=bu+bb,beta_imbalance=bb,extra_source_bias=0,residual_rho_source=0,residual_rho_target=0,
                       noise_R2=noise2,noise_Rinf=noiseinf,R2=r2,Rinf=ri,R2_admissible=admissible2,
                       R2_role='valid_design_only' if admissible2 else 'diagnostic_only_outcome_adaptive_weights',
                       Rinf_admissible=True,selected_family=chosen,selected_radius=radius,
                       lower_unclipped=estimate-radius,upper_unclipped=estimate+radius,
                       lower=max(-1,estimate-radius),upper=min(1,estimate+radius),
                       release_delta_015=radius<=.15,release_delta_010=radius<=.10,release_delta_020=radius<=.20,release_delta_030=radius<=.30,
                       native_halfwidth=native,native_lower=estimate-native,native_upper=estimate+native,
                       native_interval_kind='approximate_FE_common_parameter_CI' if policy=='fixed_effect' else 'approximate_DL_new_study_PI' if policy=='random_effects' else 'not_applicable',
                       native_release_delta_015=(native<=.15) if np.isfinite(native) else None,
                       native_release_delta_010=(native<=.10) if np.isfinite(native) else None,
                       native_release_delta_020=(native<=.20) if np.isfinite(native) else None,
                       native_release_delta_030=(native<=.30) if np.isfinite(native) else None,
                       active_profile_vertex_b=active//3,active_profile_vertex_c=active%3,
                       effective_source_count=1/float(alpha@alpha),source_count=40,target_n=len(groups[target]),
                       zeta2=ZETA2,zetaInf=.025,conditional_joint_failure_budget=.05,
                       design_policy_freeze_sha256=frozen_hash)
            rows.append(row)
            for i,site in enumerate(sources):
                weight_rows.append(dict(target=target,policy=policy,source=site,weight=alpha[i],source_estimate=effects[i],
                                        source_estimated_variance=variances[i],s=s[i],beta=beta[i],outcome_adaptive=policy not in DESIGN))
            for kind, values in [('extra_source_bias',[.025,.05,.10]),('uniform_source_target_residual_rho',[.025,.05,.10]),('noise_variance_factor',[1,2,4])]:
                for value in values:
                    add = value if kind=='extra_source_bias' else 2*value if kind=='uniform_source_target_residual_rho' else 0
                    factor = math.sqrt(value) if kind=='noise_variance_factor' else 1
                    sr2,sri = bu+bb+add+noise2*factor,bu+bb+add+noiseinf*factor
                    rr=sr2 if chosen=='R2' else sri
                    sensitivity.append(dict(target=target,policy=policy,sensitivity_kind=kind,value=value,
                                            weights_fixed=True,reoptimized=False,estimate=estimate,geometry_G_U=bu,B_U=bu+bb+add,beta_imbalance=bb,
                                            extra_radius=add,noise_multiplier=factor,R2=sr2,Rinf=sri,R2_admissible=admissible2,
                                            selected_family=chosen,selected_radius=rr,lower=max(-1,estimate-rr),upper=min(1,estimate+rr),
                                            release_delta_010=rr<=.10,release_delta_015=rr<=.15,release_delta_020=rr<=.20,release_delta_030=rr<=.30))
    suffix = '_smoke' if args.smoke else ''
    dump_csv(out / ('predictions_pre_reveal'+suffix+'.csv'),rows)
    dump_csv(out / ('source_estimates_pre_reveal'+suffix+'.csv'),source_results)
    if not args.smoke:
        dump_csv(out/'source_inputs.csv',source_inputs); dump_csv(out/'weights.csv',weight_rows)
        dump_csv(out/'optimization_audit.csv',opt_audits); dump_csv(out/'sensitivity.csv',sensitivity)
    else:
        dump_csv(out/'optimization_audit_pre_reveal_smoke.csv',opt_audits)
        dump_csv(out/'weights_pre_reveal_smoke.csv',weight_rows)
        dump_csv(out/'source_inputs_pre_reveal_smoke.csv',source_inputs)
    summary = dict(numerical_status='computed_conditional',qualification_status='assumption_conditional_only',
                   causal_guarantee='Conditional on response law, common CATE, accurate observed labels, and additional noninformative selection/reporting assumptions; no unconditional causal guarantee.',
                   target_estimand='Expected ATE in retained finite canonical valid-response cohort, conditional on category, assignment and missingness mask.',
                   source_estimand='Unadjusted Cheap minus Expensive binary response difference using all retained participants.',
                   target_outcomes_read=False,source_n=len(source),source_sites=40,target_sites=len(targets),targets=targets,
                   policy_count=6,prediction_rows=len(rows),L=L,C2=C2,CInf=CINF,zeta2=ZETA2,zetaInf=.025,
                   joint_failure_budget=.05,profile_eta=0,main_extra_source_bias=0,main_residual_rho=0,
                   frozen_design_policy_sha256=frozen_hash,optimized_all_pass=all(a['numerically_optimal'] for a in opt_audits),
                   maximum_optimization_gap=max(a['primal_dual_gap'] for a in opt_audits),
                   FE_Q=Q,FE_df=df,DL_tau_squared=tau2,DL_denominator=float(denom),
                   FE_native_halfwidth=float(native_fe),DL_native_target_PI_halfwidth=float(native_re),
                   zero_variance_fallback_count=int(sum(r['zero_variance_countproxy_fallback'] for r in source_results)),
                   release_counts={p:sum(r['release_delta_015'] for r in rows if r['policy']==p) for p in POLICIES},
                   run_utc=datetime.now(timezone.utc).isoformat(),smoke=args.smoke,
                   input_sha256={name:digest(data/name) for name in ['all_design.csv','source_only.csv','frozen_site_split.csv','sex_profile_set_audit.csv']},
                   code_sha256=digest(Path(__file__)),clarabel_version=clarabel.__version__)
    (out/('numerical_summary_pre_reveal_smoke.json' if args.smoke else 'numerical_summary.json')).write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main()

