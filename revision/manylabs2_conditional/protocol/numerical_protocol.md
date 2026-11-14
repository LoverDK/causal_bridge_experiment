# Frozen assumption-conditional numerical protocol

This program implements the user's requested numerical experiment under explicit extra assumptions. `computed_conditional` is independent of the earlier qualification gate. It does not establish an unconditional causal guarantee, repair missing substantive labels, or certify the common-CATE and selection/reporting assumptions.

## Estimand, outcome discipline, and profile sets

The target estimand is the expected Cheap-minus-Expensive binary response ATE of the retained finite canonical valid-response cohort, conditional on the true substantive category, treatment assignment, and missing-label mask. The source statistic is the unadjusted all-participant response difference on the same [-1,1] scale. Additional unverified assumptions are conditional independence of the participant Bernoulli responses given these quantities, a shared category-specific CATE across sites, accurate observed substantive labels, and noninformative selection/reporting needed for the causal interpretation. Main extra source bias and residual profile error are set to zero as conditional assumptions, not estimated facts.

Sex codes 1, 2, 3 denote male, female, other. Code 4 and blank labels have unknown substantive category. For each site/arm, let l be its three known-category counts divided by its full retained n and r its unknown count divided by n. Its exact profile set is l+r Delta_3. No unknown label is imputed. The program requires exact agreement of all category and unknown counts with `sex_profile_set_audit.csv`. Profile eta is deterministically zero conditional on accurate observed labels; no population sampling claim is made.

All target outcomes are absent from `all_design.csv`. The program reads only this design file, the split, and the profile audit while calculating and hashing the four design-only policies. It then opens `source_only.csv`, checks that its 4,365 rows belong to exactly the 40 source sites, and computes the two adaptive baselines. It never opens a canonical response file or any target-Y file. The 17 sealed-target sites include radboud regardless of its earlier coded-1/2 eligibility flag, because the present analysis uses all three substantive categories and uncertainty sets and requires no category-cell division.

## Exact bounds and simultaneous budget

Set L=sqrt(8/3). For nonnegative source weights alpha summing to one and target (l*,r*), the exact robust mismatch is

G_U(alpha) = L max over b,c in {1,2,3} ||l* + r* e_b - sum_i alpha_i l_i - (sum_i alpha_i r_i)e_c||_2.

The maximum over nine vertices is exact because the weighted Minkowski sum of source profile sets is sum alpha_i l_i + (sum alpha_i r_i) Delta_3. There is no 3^40 enumeration or separately optimized coordinate box.

For each source i, beta_i = max over its nine arm profile vertex pairs of (1/2)||p_i1-p_i0||_1. Conditional on the stated response law and shared category CATE, this bounds the centering discrepancy of its unadjusted difference from its full-cohort ATE. No within-category outcome standardization or empty-cell division is performed. Independent bounded responses yield s_i^2=(1/4)(1/n_i1+1/n_i0).

B_U(alpha)=G_U(alpha)+sum alpha_i beta_i+extra_source_bias+residual_rho_source+residual_rho_target. Main additional allowances are zero. `geometry_G_U` records only geometry, while `B_U` records this entire operational bias envelope.

R2(alpha)=B_U(alpha)+c2 ||alpha .* s||_2.

Rinf(alpha)=B_U(alpha)+cInf sum alpha_i s_i.

The single conditional inference failure budget is .05. R2 receives .025 across all 17 targets and all four design R2 policies (uniform, design inverse variance, optimized R2, optimized Rinf): zeta2=.025/(17*4), c2=sqrt(2 log(2/zeta2)). Rinf uses a shared source-coordinate event with zetaInf=.025, cInf=sqrt(2 log(2*40/.025)); it holds for every target and every simplex alpha, including outcome-adaptive weights. These events do not account for failure of the extra response, CATE, label, or selection assumptions. An R2 value is computed for every policy, but adaptive FE and DL R2 values are diagnostic only and cannot govern a release. Optimized Rinf remains a design policy, but its selected bound is Rinf. Its displayed R2 belongs to the four-policy simultaneous design family, although its primary release decision uses Rinf.

## Six policies and numerical optimization

Uniform weights are 1/40. Design inverse-variance weights are proportional to 1/s_i^2. The two optimized policies globally minimize their respective complete radii, including beta, over the nonnegative simplex. They are direct Clarabel primal-dual SOCPs with nine four-dimensional profile cones and, for R2, one 41-dimensional noise cone. Initial tolerances are 1e-10, maximum iterations 500. If status is not `Solved`, a deterministic technical retry uses 1e-9 and then 1e-8 tolerances; this changes no objective or data. This retry was added after a full-pass design-only solve returned `AlmostSolved` with 8.31e-11 gap at brookcuny, before any full-run source outcomes were read. All attempt statuses, gaps, residuals and requested tolerances are archived. The saved audit also reports primal/dual objectives, actual recomputed feasible objective, tiny nonnegative/simplex repairs, and active profile vertex. Successful runs require `Solved`, gap between -1e-7 and 1e-7, and both residuals below 1e-7. Failure aborts rather than silently using a heuristic. A smoke run uses only alphabetical target armstrong but retains the full 17-target inference budget; the full run is unchanged.

For FE, plug-in variance v_i=p_i1(1-p_i1)/(n_i1-1)+p_i0(1-p_i0)/(n_i0-1), with inverse-v weights. If an entire v_i is zero, substitute s_i^2 and record the fallback. DL uses Q, df=39, C=sum w - sum w^2/sum w, tau^2=max(0,(Q-39)/C), and weights proportional to 1/(v_i+tau^2). These are outcome-adaptive; their theorem-style selected radii are Rinf. The native FE approximate common-parameter CI has halfwidth z_.975/sqrt(sum 1/v_i). The native approximate DL new-study prediction interval has halfwidth t_39,.975 sqrt(tau^2+1/sum 1/(v_i+tau^2)). Native intervals are model-based comparison quantities with a different estimand interpretation; they are not theorem-style conditional coverage certificates.

## Release, sensitivity, and archival outputs

Every point prediction is sum alpha_i source_RD_i. Selected intervals store raw endpoints and endpoints clipped to [-1,1]; clipping never changes a release decision. Conditional release uses the unmodified selected radius <= delta. Primary delta=.15; prespecified comparison deltas .10,.20,.30. Native-baseline width comparisons are separately labeled.

Sensitivity is deterministic and does not fit target outcomes: extra source bias b=.025,.05,.10 adds b; common source-and-target residual profile error rho=.025,.05,.10 adds 2rho; noise variance factors 1,2,4 multiply each noise term by sqrt(factor). All weights remain fixed and `reoptimized=False` is explicit. Main noise factor is one. This isolates assumption perturbations without adapting a policy after seeing target responses.

The full run writes 102 frozen prediction rows, all 680 source-target design inputs, 4,080 weights, 34 solver audits, 918 sensitivity rows, 40 source-effect rows, and a numerical summary with input/code hashes, constants, source baseline statistics, fallback counts, solver gaps and release totals. The coordinator must freeze a hash manifest of these artifacts before any target-Y evaluation. Prediction files contain no target outcomes. Any later empirical target evaluation is a separate coordinator operation and cannot change these policies, assumptions, thresholds, or source predictions.

