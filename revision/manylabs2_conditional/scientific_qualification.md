# Scientific qualification alongside conditional numerical execution

Status meanings: **Supported** means documented by the available audit or an analytic implication of stated premises; **Conditional** means true only under an explicit additional scientific/stochastic premise; **Unverified** means the available evidence does not establish it; **False** identifies a claim that must not be made. These statuses do not gate numerical execution. The primary branch must compute all 17 target estimates, radii and release/refusal decisions under its declared model, while retaining this qualification record.

## Supported facts and analytic implications

- The prior canonical audit records 7,228 valid framing-response participants across 57 sites and the fixed 40-source/17-target split. Treatment contrast is Cheap minus Expensive and the outcome is Yes risk difference.
- Questionnaire recovery supports the recorded labels 1 Male, 2 Female, 3 Other, 4 Prefer not to answer; blank is separately recorded. Across the canonical cohort, 29 participants report Other and 90 substantive memberships are unknown (58 prefer not to answer and 32 blank). These facts come from the prior `manylabs2_dual_track/track_b/mechanism_sets.md` and associated count audit, not a newly invented classification.
- Conditional on accurate observed labels and the stated three-category membership definition, missing-label completion produces deterministic full-cohort and arm-profile polytopes. Arbitrary missingness does not invalidate this narrow coordinate containment. No missing label is numerically imputed.
- Under the explicitly stated independent bounded conditional response law, unadjusted site RD has the count-only Hoeffding proxy and the arm-profile TV bias envelope derived in `math_specification.md`. The estimator retains all canonical outcomes and does not require nonempty category-by-arm cells.
- Conditional common CATEs imply an affine effect surface on the simplex. The tangent-gradient bound L=sqrt(8/3), H=0 and nine-pair worst-case Minkowski geometry are analytic. Estimation of gamma is unnecessary.

## Conditional assumptions used by the numerical branch

- The substantive profile refers to an accurately recorded, treatment-invariant baseline membership with comparable meaning across questionnaire variants, languages, sites and targets.
- Conditional on full true memberships, assignments, inclusion masks, category-recording masks and design information, the retained responses are independent across participants/sites, bounded in [0,1], and have site/category/arm-specific means q_sbt. The causal contrast interpretation requires a compatible potential-response and observation process.
- The three conditional contrasts q_sb1-q_sb0 equal one common gamma_b across every source and target, including categories with sparse or absent observed arm cells. Site-specific baseline risks may vary.
- The estimand is the profile-conditional expected effect in the canonical outcome-observed cohort. This choice permits conditioning on the realized composition. It does not recover excluded randomized participants or assert representativeness of recruitment populations.
- Primary extra bias and residual allowances equal zero only under these exact premises. Positive beta_extra and rho values are declared sensitivity scenarios. They are not empirically estimated or empirically validated uniform bounds.
- R2 weights depend only on the permitted design/profile information. Rinf can cover outcome-dependent weights on its shared coordinate event. Failure budgets are specified separately for source estimates and noisy target-reference evaluation.

The frozen source-error family includes four design-only policies (Uniform, design-IV, optimized R2, optimized Rinf) across 17 targets: 68 displayed R2 radii with individual failure .025/68, plus one shared Rinf coordinate event with failure .025. Their combined source-error failure is at most .05. Main decisions use R2 for Uniform/design-IV/optimized R2 and Rinf for optimized Rinf/FE/DL. Optimized Rinf's displayed R2 radius is included in the 68 even though its main decision uses Rinf. The target-reference event has a separate budget; joint source-and-reference claims add that budget to .05.

## Unverified empirical conditions

- Accurate baseline-category measurement and treatment-invariant reporting/nonresponse remain unverified. A post-task question can measure a stable trait, but the timing does not establish reporting invariance.
- Retention/exclusion and response dependence sufficient for the stipulated conditional law are unverified. Treating a missingness mask as part of the conditioning information can change response means or independence; deterministic profile coverage does not solve this issue.
- Exact cross-site common CATEs and sufficiency of the three-category profile remain unverified. Randomized treatment supplies no direct evidence that all other effect modifiers or implementation differences vanish conditionally on this profile.
- Sparse Other responses prevent a useful empirical diagnostic of the third common contrast. The prior source-only diagnostics had 12 Other participants among all 40 sources and zero category/site cells meeting their at-least-two-per-arm inferential criterion. This limits diagnostics; it does not make the unadjusted conditional numerical estimator undefined.
- A uniform source-and-target residual envelope has not been independently calibrated. No numerical probability of structural-model truth is supported by the audit.

## Existing source-only diagnostics and what they imply

The prior protocol froze development and internal validation partitions within the 40 sources and used no target outcomes. The all-source sex-category heterogeneity output reports Female Q=43.5009 on 39 degrees of freedom (p=.28565), DL tau-squared=.0012864, approximate Q-profile tau-squared upper limit=.0094359; Male Q=33.4799 on 38 degrees of freedom (p=.67841), DL tau-squared=0, upper limit=.0110900. These are diagnostics with estimated variances, not finite-sample certification statistics.

Development-fitted predictions on supported internal-validation category/site cells have Female RMSE=.12117 and maximum absolute residual=.20233 (20 sites), and Male RMSE=.12607 and maximum absolute residual=.23032 (20 sites). Approximate median detectable deviations were .32704 and .54263 respectively. The relevant CSV files are `manylabs2_dual_track/track_b/common_cate_heterogeneity.csv` and `common_cate_validation_summary.csv`.

These numbers do not reject all common-effect models, establish exact homogeneity, verify the missingness-conditioned response law, or justify a uniform rho. Power and support are limited. The Other contrast remains unvalidated. Conversely, a scientific audit finding of insufficient support is not a mathematical prohibition on executing the explicitly conditional model.

## False claims excluded from reporting

- “All 17 targets are empirically qualified causal releases” merely because a conditional radius is small.
- “Nonsignificant heterogeneity proves common CATEs” or “DL tau-squared=0 proves no residual.”
- “The maximum observed source residual, fitted SD or Q-profile upper limit is a uniform residual bound for every target.”
- “Randomized treatment makes the enrolled cohort representative of its nation or recruitment population.”
- “Deterministic observed-profile containment verifies complete latent-mechanism coverage, label accuracy, or absence of selection bias.”
- “A confidence interval for an average source effect is automatically a prediction interval for a target effect.”
- “A noisy target RD is exact causal truth,” or “observed inclusion is direct measurement of latent-effect coverage.”
- “Conventional outcome-variance FE or estimated-heterogeneity DL weights qualify for R2 without additional selection control.”
- “There are no executable conditional results because the empirical scientific audit did not qualify the model.”

## Required final reporting

For every target, report the actual conditional estimate, source-noise term, profile geometry, source bias allowance, total radius, tolerance, release/refusal decision, and withheld-reference comparison. Compute release/refusal rates with denominator 17 for each completed model/method/scenario. In the same report label scientific qualification as unverified/conditional, preserve the prior `not_qualified` conclusion as a scientific audit result, and identify the new run as conditional numerical execution. Do not replace computed rows by `not_qualified`, suppress all 17 numerical decisions, or rename missing qualification as algorithmic refusal.

No result in this document authorizes a manuscript push, original-file edit, or publication of an unconditional real-data certificate. Previous artifacts remain preserved.
