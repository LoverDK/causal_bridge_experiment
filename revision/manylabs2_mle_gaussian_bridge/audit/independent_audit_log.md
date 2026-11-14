# Independent audit log

## Scope and preservation

The audit opened the task attachment, the prior conditional branch's mathematical specification, outcome-free all_design.csv, the header of permitted source_only.csv, and new-branch code/math artifacts. It did not open real target responses, prior results/target CSV files, manuscripts, PDFs, Overleaf, or Git state. All audit writes stay under this audit directory.

## Outcome-free inventory

Confirmed 57 sites, 7,228 records, 40 sources/4,365 source records, and 17 targets/2,863 target design records. The known source category-arm counts are Male (686 control,654 treatment), Female (1,488,1,478), and Other (7,5). Forty-seven source labels are unknown (20 blank,27 refusal), retained in profile uncertainty sets. Other is absent among recorded labels at 43 of 57 sites and present in both arms at just three sites. Barycenter completion gives positive Other weight at 43 sites; the other 14 have structurally absent Other. These facts were calculated without outcomes or simulations.

## Initial code review before execution

Reviewed code/bernoulli_mc.py functions simulate_cells, site_diagnostics, joint_diagnostics, scalar_posterior, design_library, and evaluate_designs. The saturated binomial estimator, exact oracle variance, affine posterior mapping, exhaustive 12/66/495 subset enumeration, risk bias-variance formula, and invalid-interval-as-noncoverage convention are mathematically consistent.

Requested the following implementation changes before final audit: separate conditional finite-MLE empirical variance from unconditional extended-estimator variance; add per-policy and paired loss-difference Monte Carlo errors; explicitly handle unidentified candidate risk rather than allow NaN argmin to select a subset; and mask structurally irrelevant categories in boundary events even if current allocations make that distinction automatic.

The exact analytic Bernoulli squared-risk oracle is an acceptable stronger benchmark than an empirical-minimum MC oracle. It requires no training split because its minimization uses the exact expected loss. The report must name it as analytic rather than imply that a noisy MC minimum is an independently evaluated optimum. Any MC-selected minimum still requires independent selection/evaluation streams.

## Mathematical artifact review

Reviewed mle_delta_derivation.md and theorem_5_6_compatibility.md. Verified the displayed score/information, Delta derivatives, active-cell asymptotic conditions, boundary probabilities, exact finite-sample RD moments, plug-in variance downward-bias factor, weighted-sum Berry-Esseen expression, pooled-source likelihood description, scalar Gaussian posterior update, submodular marginal, fixed-truth shrinkage bias/covariance, and frozen-source conditional variant. No mathematical error identified in the reviewed versions.

Two interpretation restrictions must remain prominent in the final report: a fixed affine decoder has the same squared risk under any moment-matched observation distribution, so MSE agreement is not Gaussian-shape evidence; and Gaussian posterior intervals with a frozen observed source state do not automatically have fixed-truth frequentist coverage.

## Pending

Final frozen protocol, executable driver, full Monte Carlo outputs, and numerical reconciliation remain to be audited after they exist. This is a prospective/initial review, not a numerical-results certification.

## Frozen protocol and repeated-source implementation review

The root-frozen decisions are now recorded in prospective_audit.md. Reviewed build_inputs.py, calibration_summary.json, and execution.json schema. The source calibration includes all 4,365 source responses and the 47 unknown-category outcomes via the declared uniform-mixture likelihood. Known and unknown label counts match the independent outcome-free inventory. Hamilton allocation preserves scaled arm totals, profiles stay within their declared uncertainty sets, and the 12 distinct farthest-first menu profiles are selected from 29 outcome-free support-eligible designs. All 57 remain in estimator diagnostics. The 13 scenario records contain the planned 46 evaluation conditions.

Reviewed the repeated-source implementation. Four spawned random streams separately generate evaluation bridge/site outcomes, evaluation source outcomes, pilot bridge/site outcomes, and pilot source outcomes. Source draws are independent of future bridge outcomes even when identifiers overlap. The source-response weight matrix is targets*V*source_precision; the exact analytic risk includes its source variance, bridge variance, and squared bias, including actual pooled heterogeneous means under DGP B. The empirical exhaustive oracle selects using pilot risk and is evaluated using the separate main stream. The uniform-random comparator averages all subsets. No error found in these formulas.

## Technical pilot numerical reconciliation

The 200-evaluation/200-pilot technical run was used only to check implementation identities. No scientific threshold, menu, scenario or outcome calibration was changed from these checks. The independent audit runner found no issues: all 8 diagnostic groups contain all 57 sites; exact oracle variance agrees within 5.3e-14 relative error; 114 site-condition finite-MLE frequencies agree with the analytic binomial success probabilities within six Monte Carlo standard errors; maximum standardized mean/variance reconciliation deviations are 2.20 and 2.14 MC standard errors. Across all 2,292 exhaustive subset risk rows, the maximum absolute exact-versus-Monte-Carlo risk discrepancy is 1.67 reported MC standard errors. Analytic risk regrets are nonnegative and the empirical oracle's paired self-regret is zero.

The pilot is a technical validation only. Full-run numerical results and final report interpretation remain pending.

## Completed full-run audit

The full frozen run subsequently completed all 46 conditions. Independent reconciliation found no findings: all 10 freeze hashes match, all 184 estimator/variance groups retain 57 sites, all 5,244 scaled arm totals match, 2,622 finite-MLE success probabilities reconcile with exact binomial probabilities, and 2,237 identified oracle variances agree to maximum relative error 6.7e-13. Extended estimator mean/variance discrepancies remain within 4.28/3.90 MC standard errors. All 50,424 exhaustive risks agree with exact expectations within 3.03 reported MC standard errors; all policy-reconstruction and greedy-bound checks pass. See final_independent_audit.md and numerical_audit_summary.json for the final findings and scientific interpretation limits.

The additional reporting observation about the frozen plan's per-target export promise was subsequently resolved by code/export_target_metrics.py. An independent audit of its 68,816 target rows confirmed 4,048 groups of the original 17 targets, matching availability/replication counts, source-only and unavailable scope, primary means within floating-point tolerance, all nine primary evidence hashes, and all ten original freeze hashes. Static code review confirms same recorded child streams, no refitting, and no policy reselection. See target_export_audit_summary.json; no pending reporting discrepancy remains.
