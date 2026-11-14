# Independent statistical and numerical audit

The frozen main Monte Carlo run passed the independent implementation checks below. This validates numerical consistency under the declared simulation, not real-data causal qualification or the exact finite-sample application of Theorem 5.6.

## Preservation and provenance

The audit did not open real held-out target responses. Its original-data access was limited to outcome-free design information, the header of permitted source_only.csv, and the prior mathematical specification. The new builder uses only real source outcomes for calibration. All 10 files in full_run_freeze.json retained their frozen hashes. The full execution comprises 46 conditions: 10 with 5,000 evaluation replications and 36 with 2,000, each with an independent 2,000-replication oracle-selection pilot. Source and future bridge responses are generated from independent random streams.

The audit itself writes only within this audit directory. Manuscripts, PDFs, Overleaf, GitHub, and prior study outputs were not changed by the audit.

## Independent numerical reconciliation

The audit script audit_results.py reads new-branch simulated outputs and independently recomputes binomial probabilities and moments, allocation totals, exhaustive optima, and policy invariants. It produced no failure or review findings on the full frozen run.

* All 10,488 estimator-diagnostic rows are present: 46 conditions, 57 sites, two estimator conventions, and two variance conventions. Every one of the 184 groups has denominator 57.
* All 5,244 simulated site-arm schedules preserve the original treatment-arm totals multiplied by the declared scale. Population-profile standardization remains fixed while integer category allocations use the documented Hamilton rule.
* All 2,622 site-condition finite-logit success rates agree with the exact independent-binomial boundary-event calculation within six Monte Carlo standard errors.
* For the 2,237 identified extended-estimator site conditions, reported oracle variance agrees with an independent exact binomial calculation to maximum relative error 6.7e-13. Maximum mean and sample-variance discrepancies are 4.28 and 3.90 Monte Carlo standard errors, respectively.
* Across 50,424 exhaustive subset risk rows, the maximum absolute difference between Monte Carlo risk and exact analytic risk is 3.03 reported Monte Carlo standard errors. This check includes both independently regenerated source variance and bridge variance.
* Independent reconstruction found zero disagreements for the pilot-selected Monte Carlo oracle, analytic expected-risk oracle, exhaustive logdet optimum, uniform-subset expected risk, or the greedy logdet objective bound.

The two unavailable bridge-comparison conditions are the prespecified all-Male and all-Female unknown-membership completions at scale 1. Their fixed menus contain a required empty cell; policy rows remain unavailable rather than changing the menu or imputing an MLE. Their 57-site estimator diagnostics remain present. There are consequently 44 available conditions times two noise models times 573 exhaustive subsets, giving 50,424 risk rows.

## Adequacy findings that the report must preserve

At the original scale, only 29 of 57 barycenter site functionals are identified by the saturated estimator. All 29 pass the extended-estimator oracle-variance criteria in both A and B; the other 28 remain failures. It would be false to describe this as all-site adequacy.

For the full 57-site scope, the extended estimator first passes every frozen oracle-variance criterion at scale 5, and every plug-in-variance criterion at scale 10, under both main DGPs. These passes persist at the remaining larger tested scales. The strict finite-logit MLE never passes at every site through scale 20: only 28 of 57 sites in A and 27 in B pass its 99% existence gate at that largest scale.

The supported 12-design menu has a narrower, explicitly prespecified domain. Its extended-estimator oracle marginal-plus-joint gate passes from scale 1; its plug-in marginal-plus-joint gate first passes at scale 5. The strict finite-logit marginal-plus-joint gate first passes at scale 20, with joint validity .9932 in A and .9912 in B. This menu was selected from 29 support-eligible outcome-free designs; its favorable result does not describe all 57 original sites.

Under common-CATE A with source-fitted planning variances, logdet greedy has zero analytic target-MSE regret at budgets 1 and 2 and approximately .48% regret at budget 4 across scales. These are fixed-menu simulation findings. They do not follow as a target-MSE guarantee from the logdet theorem.

Under heterogeneous B, centered functional normality can pass while transport inference fails. Greedy nominal posterior-interval coverage is approximately .52-.54 at scale 1 and .108-.118 at scale 20, depending on budget. Moment-matched Gaussian coverage is close to the Bernoulli coverage. The worsening intervals therefore expose common-mean structural bias as uncertainty shrinks; they do not demonstrate failure of the centered Gaussian approximation.

## Exact limits on positive interpretation

For fixed nonempty cells, the extended saturated probability estimate is K/n. Its standardized RD is exactly unbiased under its stipulated cell response law, and the oracle Delta variance is its exact finite-sample variance. The Gaussian step concerns distributional shape and interval calibration. Boundary probability MLE availability must not be relabeled finite-logit MLE existence.

For the fixed affine posterior decoder, squared risk depends only on means and covariances. Bernoulli and moment-matched Gaussian target MSE therefore coincide algebraically. Good MSE agreement is an implementation check and a decision-risk result, not independent evidence of normal tails. MAE and coverage comparisons provide distributional evidence.

The true category effects are fixed in this Monte Carlo, while the zero-mean identity-covariance Gaussian prior is a working model. Its posterior covariance is not automatically a repeated-sampling variance or a frequentist coverage guarantee. The repeated-source sampling covariance and shrinkage/structural bias used in this implementation are required for interpretation.

The post-task category stability assumption, uniform latent-membership likelihood for unknown source labels, continuous representative population profiles, retrospective target design profiles, deliberate support eligibility restriction, and finite menu/scale grid all remain scope conditions. No finding proves universal Bernoulli applicability or exact finite-sample Gaussian-theorem validity.

## Completed per-target export audit

The reporting discrepancy has been resolved through a separate deterministic export from the same recorded evaluation streams. Independently verified 68,816 target rows = 4,048 policy-condition groups times exactly the original 17 distinct target identifiers. Every group matches the primary availability and replication count. All 2,856 unavailable target rows occur in the two prespecified scale-1 completion conditions, retain missing errors and zero unconditional interval success, and are not substituted with successful subsets. All 3,128 source-only target rows are available with budget zero, including in those two conditions.

The 17-target means independently reconcile with primary MSE and MAE to maximum absolute differences 6.6e-17 and 7.7e-17; conditional and unconditional interval-coverage differences are at most 6.92e-14 and 1.34e-14. The nine primary evidence hashes, all ten original freeze hashes, protocol hash, target-export hash, and exporter-code hash match their manifests. Static review verifies reconstruction of each recorded condition SeedSequence and reuse of child streams 0 and 1 for evaluation bridge/site and source outcomes. Exported policy choices come directly from the frozen comparison CSV; no fit, selection, new condition, or scientific threshold is introduced. Per-target Monte Carlo standard errors are calculated separately and are not averaged to reconstruct the target-average standard error, since target errors are correlated.

See target_export_audit_summary.json and the appended target_export_audit section in numerical_audit_summary.json. No reporting discrepancy remains from this audit.
