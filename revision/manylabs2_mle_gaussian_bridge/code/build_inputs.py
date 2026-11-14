"""Build outcome-blind designs and source-only Bernoulli calibration; never reads target Y."""
from __future__ import annotations
import csv
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
SEED = 2026110901
SCALES = [1, 2, 5, 10, 20]
CATEGORIES = ["Male", "Female", "Other"]


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def hamilton(total, profile):
    expected = total * profile
    result = np.floor(expected).astype(int)
    remainder = int(total - result.sum())
    order = sorted(range(3), key=lambda j: (-float(expected[j]-result[j]), j))
    for j in order[:remainder]:
        result[j] += 1
    assert result.sum() == total and np.all(result >= 0)
    return result


def calibrate(source_rows):
    """Unknown-label likelihood is Bernoulli(mean_c q_tc), with fixed uniform weights."""
    known_n = np.zeros((2, 3), dtype=int)
    known_k = np.zeros((2, 3), dtype=int)
    unknown_n = np.zeros(2, dtype=int)
    unknown_k = np.zeros(2, dtype=int)
    for row in source_rows:
        t, y = int(row["T"]), int(row["Y"])
        if row["sex"] in ("1", "2", "3"):
            c = int(row["sex"])-1
            known_n[t, c] += 1
            known_k[t, c] += y
        else:
            assert row["sex"] in ("", "4")
            unknown_n[t] += 1
            unknown_k[t] += y
    fits = {}
    for half_count, label in [(0., "raw"), (.5, "smooth")]:
        q_fit, arm_diagnostics = [], []
        for t in (0, 1):
            n, k = known_n[t], known_k[t]
            un, uk = unknown_n[t], unknown_k[t]

            def objective(q):
                qm = q.mean()
                loglik = np.sum((k+half_count)*np.log(q)
                                +(n-k+half_count)*np.log1p(-q))
                loglik += uk*np.log(qm)+(un-uk)*np.log1p(-qm)
                grad = (k+half_count)/q-(n-k+half_count)/(1-q)
                grad += (uk/qm-(un-uk)/(1-qm))/3
                return -float(loglik), -grad

            start = (k+.5)/(n+1)
            fit = minimize(objective, start, jac=True, method="L-BFGS-B",
                           bounds=[(1e-12, 1-1e-12)]*3,
                           options={"ftol": 1e-14, "gtol": 1e-9, "maxiter": 10000})
            q = fit.x
            # Convex objective: independent deterministic starts check the global optimum.
            checks = [minimize(objective, np.full(3, x), jac=True, method="L-BFGS-B",
                               bounds=[(1e-12, 1-1e-12)]*3,
                               options={"ftol": 1e-14, "gtol": 1e-9, "maxiter": 10000})
                      for x in (.25, .5, .75)]
            all_fits = [fit]+checks
            fit = min(all_fits, key=lambda v: v.fun)
            q = fit.x
            gradient = float(np.max(np.abs(objective(q)[1])))
            assert gradient < 1e-3, (label, t, gradient)
            assert max(v.fun for v in all_fits)-min(v.fun for v in all_fits) < 1e-7
            q_fit.append(q.tolist())
            arm_diagnostics.append({"arm": t, "success": bool(fit.success),
                                    "message": str(fit.message), "negative_objective": float(fit.fun),
                                    "max_abs_gradient": gradient,
                                    "boundary": bool(np.any((q<1e-8)|(q>1-1e-8))),
                                    "finite_logit": bool(np.all((q>1e-8)&(q<1-1e-8)))})
        fits[label] = {"q": q_fit, "arms": arm_diagnostics}
    return fits, known_n, known_k, unknown_n, unknown_k


def main():
    started = time.perf_counter()
    design_path, source_path = ROOT/"data/all_design.csv", ROOT/"data/source_only.csv"
    design, source = read_rows(design_path), read_rows(source_path)
    assert "Y" not in design[0]
    assert len(design) == 7228 and len(source) == 4365
    sites = sorted({row["source"] for row in design})
    assert len(sites) == 57
    index = {s: j for j, s in enumerate(sites)}
    source_sites = {row["source"] for row in source}
    source_indices = [j for j, s in enumerate(sites) if s in source_sites]
    target_indices = [j for j, s in enumerate(sites) if s not in source_sites]
    assert len(source_indices) == 40 and len(target_indices) == 17
    assert sum(row["source"] in source_sites for row in design) == 4365
    assert {row["uID"] for row in source} == {row["uID"] for row in design if row["source"] in source_sites}
    arm_n = np.zeros((57, 2), dtype=int)
    known_n = np.zeros((57, 3), dtype=int)
    unknown_n = np.zeros(57, dtype=int)
    for row in design:
        j, t = index[row["source"]], int(row["T"])
        arm_n[j, t] += 1
        if row["sex"] in ("1", "2", "3"):
            known_n[j, int(row["sex"])-1] += 1
        else:
            assert row["sex"] in ("", "4")
            unknown_n[j] += 1
    site_n = arm_n.sum(axis=1)
    assert np.all(arm_n > 0)
    lower, uncertainty = known_n/site_n[:, None], unknown_n/site_n
    profiles = {"barycenter": lower+uncertainty[:, None]/3}
    for c, name in enumerate(CATEGORIES):
        profile = lower.copy()
        profile[:, c] += uncertainty
        profiles["unknown_all_"+name] = profile
    for profile in profiles.values():
        assert np.allclose(profile.sum(axis=1), 1) and np.all(profile >= lower-1e-14)
    counts = {}
    for name, profile in profiles.items():
        counts[name] = {}
        for scale in SCALES:
            counts[name][str(scale)] = np.asarray([[hamilton(scale*arm_n[j,t], profile[j])
                                                   for t in (0,1)] for j in range(57)])

    bary = profiles["barycenter"]
    eligible = [j for j in range(57) if all(
        np.all((counts["barycenter"][str(scale)][j] > 0) | (bary[j][None,:] == 0))
        for scale in SCALES)]
    assert len(eligible) >= 12, "Insufficient active-cell-supported candidate profiles"
    menu = [eligible[0]]
    while len(menu) < 12:
        remaining = [j for j in eligible if j not in menu
                     and all(not np.array_equal(bary[j], bary[k]) for k in menu)]
        assert remaining
        score = {j: min(float(np.linalg.norm(bary[j]-bary[k])) for k in menu) for j in remaining}
        menu.append(min(remaining, key=lambda j: (-score[j], sites[j])))

    fits, calibration_n, calibration_k, missing_n, missing_k = calibrate(source)
    q_raw, q_smooth = np.array(fits["raw"]["q"]), np.array(fits["smooth"]["q"])
    qa = np.broadcast_to(q_smooth, (57,2,3)).copy()
    rng = np.random.default_rng(SEED)
    z = rng.uniform(-1, 1, 57)
    z -= z.mean()
    z /= np.max(np.abs(z))
    h = min(.05, .5*float(np.minimum(q_smooth[1],1-q_smooth[1]).min()))
    qb = qa.copy()
    qb[:,1,:] += h*z[:,None]
    assert np.all((qb>0)&(qb<1)) and abs(z.mean()) < 1e-14

    def scenario(name, profile_name, is_main, q_by_dgp):
        sc = SCALES if is_main else [1,5,20]
        return {"name": name, "main": is_main, "scales": sc,
                "profile": profiles[profile_name].tolist(),
                "profile_name": profile_name,
                "counts_by_scale": {str(s): counts[profile_name][str(s)].tolist() for s in sc},
                "q_by_dgp": {k: v.tolist() for k,v in q_by_dgp.items()}}

    scenarios = [scenario("barycenter", "barycenter", True, {"A": qa,"B": qb})]
    for name in profiles:
        if name != "barycenter":
            scenarios.append(scenario(name, name, False, {"A": qa}))
    for q0 in (.2,.5,.8):
        for q1 in (.2,.5,.8):
            qs = qa.copy()
            qs[:,0,2], qs[:,1,2] = q0,q1
            scenarios.append(scenario(f"other_q0_{q0:.1f}_q1_{q1:.1f}", "barycenter", False, {"A":qs}))
    assert sum(len(v["scales"])*len(v["q_by_dgp"]) for v in scenarios) == 46
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [design_path, source_path]}
    out = {"seed":SEED,"replications_main":5000,"replications_sensitivity":2000,
           "replications_oracle_pilot":2000,"scales":SCALES,"categories":CATEGORIES,
           "sites":sites,"roles":["source" if j in source_indices else "target" for j in range(57)],
           "source_indices":source_indices,"target_indices":target_indices,
           "candidate_indices":menu,"q_planning":q_raw.tolist(),"q_smooth":q_smooth.tolist(),
           "scenarios":scenarios,"arm_sizes":arm_n.tolist(),"site_sizes":site_n.tolist(),
           "profile_lower":lower.tolist(),"unknown_fraction":uncertainty.tolist(),
           "base_prior_mean":[0.,0.,0.],"base_prior_covariance":np.eye(3).tolist(),
           "noise_plans":["source_plugin","oracle"],
           "calibration": {"fits":fits,"known_n":calibration_n.tolist(),"known_k":calibration_k.tolist(),
                           "unknown_n":missing_n.tolist(),"unknown_k":missing_k.tolist(),
                           "unknown_membership_weights":[1/3]*3,
                           "unknown_likelihood":"Bernoulli(mean_c q_tc); all 47 source unknown outcomes used",
                           "regularization":"half-count log penalty .5 sum_tc(log q_tc+log(1-q_tc)); DGP generation only"},
           "heterogeneity":{"seed":SEED,"z":z.tolist(),"h":h,
                            "law":"q_s1c=q_smooth_1c+h*z_s; q_s0c=q_smooth_0c; no clipping",
                            "mean_z":float(z.mean())},
           "candidate_menu":{"selection":"lexicographic first eligible, then farthest-first Euclidean p; ties lexicographic",
                             "support_constraint":"all active barycenter cells positive at every main scale",
                             "eligible_indices":eligible,"eligible_count":len(eligible),
                             "candidate_ids":[sites[j] for j in menu],
                             "eligible_ids":[sites[j] for j in eligible],
                             "excluded_ids":[sites[j] for j in range(57) if j not in eligible],
                             "fixed_across_sensitivities":True,
                             "all_57_site_diagnostics_required":True},
           "input_sha256":hashes,
           "builder_seconds":time.perf_counter()-started}
    (ROOT/"protocol").mkdir(exist_ok=True)
    (ROOT/"protocol/execution.json").write_text(json.dumps(out,indent=2,allow_nan=False),encoding="utf-8")
    with (ROOT/"protocol/design_cell_inventory.csv").open("w",encoding="utf-8",newline="") as stream:
        fields=["profile","scale","site","role","n0","n1","p_Male","p_Female","p_Other",
                "n0_Male","n0_Female","n0_Other","n1_Male","n1_Female","n1_Other",
                "active_empty_cells","structural_zero_cells","max_abs_rounding_error","menu_candidate"]
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        for name,profile in profiles.items():
            for scale in SCALES:
                for j,s in enumerate(sites):
                    ct=counts[name][str(scale)][j]
                    active=profile[j]>0
                    row={"profile":name,"scale":scale,"site":s,"role":out["roles"][j],
                         "n0":int(scale*arm_n[j,0]),"n1":int(scale*arm_n[j,1]),
                         "active_empty_cells":int(((ct==0)&active[None,:]).sum()),
                         "structural_zero_cells":int((~active).sum()*2),
                         "max_abs_rounding_error":float(np.max(np.abs(ct-scale*arm_n[j,:,None]*profile[j]))),
                         "menu_candidate":j in menu}
                    for c,cat in enumerate(CATEGORIES):
                        row["p_"+cat]=float(profile[j,c])
                        for t in (0,1):row[f"n{t}_{cat}"]=int(ct[t,c])
                    writer.writerow(row)
    summary={"source_n":len(source),"sites":57,"target_n":2863,
             "q_raw":q_raw.tolist(),"q_smooth":q_smooth.tolist(),"h":h,
             "eligible_count":len(eligible),"candidate_ids":[sites[j] for j in menu],
             "calibration_diagnostics":fits,"conditions":46,"scenarios":len(scenarios),
             "output":str(ROOT/"protocol/execution.json")}
    (ROOT/"protocol/calibration_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))


if __name__ == "__main__":
    main()
