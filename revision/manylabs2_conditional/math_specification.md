# Conditional common-CATE numerical specification

This is an executable conditional model, not an empirical qualification certificate. The 57-site canonical outcome-observed cohort and its frozen 40-source/17-target split remain fixed. Every canonical outcome is retained in the unadjusted site risk difference. Sparse or empty category-by-treatment cells do not stop this branch. Numerical execution and scientific qualification are separate outputs.

## 1. Estimand, information, and stochastic model

Write T=1 for Cheap, T=0 for Expensive, and Y=1 for Yes. X belongs to the three substantive self-description categories Male, Female, Other. Refusal and blank labels represent unknown X, not additional substantive categories. This definition is conditional on accurate, treatment-invariant measurement of the substantive categories. It is not a biological-sex reclassification.

For each canonical site s let n_st be its positive arm size, p_st its full true three-category arm profile (including unknown labels' true memberships), w_st=n_st/n_s, and p_s=w_s1 p_s1+w_s0 p_s0. The estimand is the **profile-conditional expected effect in the canonical outcome-observed cohort**:

    tau_s^X = sum_b p_sb (q_sb1-q_sb0).

It is not the original eligible-population ATE, the full randomized-cohort ATE, or a realized fixed-potential-outcome SATE.

Let D contain all true X values, source/target identities, treatment assignments, outcome-observation/inclusion masks, category-recording masks, and outcome-free design metadata. D may contain latent X values unavailable to the algorithm. Assume, conditional on D, the retained source and target responses are independent across participants and sites, lie in [0,1], and have means q_sbt in [0,1] depending only on site s, category b, and arm t. The primary structural assumption is

    q_sb1-q_sb0 = gamma_b, for all s,b, with gamma in [-1,1]^3.

For a causal reading these conditional means must also correspond to the declared potential-response law, with consistency, suitable treatment assignment, no relevant interference, treatment-invariant baseline membership, and observation/selection sufficient for the stated canonical-cohort estimand. Randomization alone does not establish the stipulated response law after conditioning on inclusion and recording masks. In particular, conditioning on a response-dependent missingness or retention pattern can invalidate independence or the q_sbt means. This branch assumes the needed conditional law explicitly; it does not infer it from missingness counts.

The primary model implies tau_s^X=mu(p_s)=p_s^T gamma. Site-specific baseline risks q_sb0 may differ freely, subject to valid probabilities and the common contrast. Gamma need not be estimated to construct any radius below. A category can have zero observations in an arm: no category mean or division by a zero cell count enters this estimator or concentration proof.

## 2. Deterministic profile sets

For a site or arm with n records, known category counts k=(k_1,k_2,k_3), and r=n-sum k unknown labels, put l=k/n and u=r/n. Define

    U = l + u Delta_3 = {p in Delta_3: p_b >= k_b/n for all b}.

Its three vertices are l+u e_b, b=1,2,3, with duplicates when u=0. It is the convex hull of all finite integer label completions. Every true cohort profile lies in U deterministically if observed labels are accurate and all unknown labels have one of the three memberships. No MCAR/MAR or representative-sampling assumption is needed for this coordinate containment. Joint containment for all 57 full-cohort profiles and all arm profiles has eta_profile=0 under these measurement assumptions. This is conditional coordinate containment, not verified complete-mechanism coverage.

## 3. Unadjusted RD, imbalance bias, and count-only noise

The estimator is RD_s=Ybar_s1-Ybar_s0, using every canonical outcome. Set d_s=p_s1-p_s0. Direct expansion gives

    E[RD_s | D] - tau_s^X
      = [w_s0 q_s1 + w_s1 q_s0]^T d_s.

Here q_st is the vector of three conditional arm means. The coefficient vector a_s=w_s0 q_s1+w_s1 q_s0 belongs to [0,1]^3. Since sum_b d_sb=0,

    |a_s^T d_s| <= (1/2) ||d_s||_1 = TV(p_s1,p_s0).

Therefore a computable envelope is

    beta_imb,s = max_{b,c=1,2,3} (1/2) ||v_s1,b-v_s0,c||_1,

where v_st,b are the arm-profile vertices. TV is jointly convex, so its maximum over the product of the two polytopes is attained at a vertex pair. This nine-pair evaluation gives the exact maximum-TV envelope for the declared arm-profile sets. It need not be sharp over all q satisfying the common gamma restriction. It is a safe bound and requires no missing-label imputation or cell-effect fitting. The same algebra holds when site-specific conditional effects differ from common gamma; residual departures are charged separately below.

Let b_s=E[RD_s|D]-tau_s^X, xi_s=RD_s-E[RD_s|D]. Conditional bounded-response independence gives

    E[exp(t xi_s)|D] <= exp(t^2 s_s^2/2),
    s_s^2 = (1/4)(1/n_s1+1/n_s0).

Proof: the n_s1 outcomes have coefficient 1/n_s1 and the n_s0 outcomes coefficient -1/n_s0. Hoeffding's bounded-summand MGF bound is exp(t^2/8 times the sum of squared coefficient ranges). Multiplication gives the displayed proxy. This proof does not use a plug-in outcome variance, normality, category positivity, or representative recruitment. It does use the stated independent response law. Fixed-potential complete-randomization inference has a different proof and is not asserted here.

Even though D contains unknown X, weights based on observed masks, counts, and profile sets are D-measurable. The conditional inequality holds for every permitted full-X completion and therefore also yields an unconditional probability inequality under the stipulated model. Merely withholding Y does not justify the argument without this explicit conditional centering and bias decomposition.

## 4. Smoothness and exact robust geometry

Use Euclidean distance in the embedded three-category simplex. On the simplex, the tangent gradient is gamma-gamma_bar 1. The affine ambient extension

    mu_tilde(x) = gamma_bar + (gamma-gamma_bar 1)^T x

agrees with p^T gamma whenever sum p=1. Its gradient norm is at most sqrt(8/3), and its Hessian is zero. Thus valid deterministic constants are

    L = sqrt(8/3), H = 0.

The gradient bound is sharp over gamma in [-1,1]^3: squared norm is sum gamma_b^2-(sum gamma_b)^2/3, a convex function whose cube-vertex maximum is 8/3 (two signs agree and the third differs). Using ambient gradient gamma without this simplex extension would instead require sqrt(3), so the coordinate/metric convention matters. No fitted gamma, model-test p-value, or additional smoothness-estimation failure event is used.

For simplex weights alpha_i>=0, sum alpha_i=1, write U_i=l_i+u_i Delta_3. Their weighted Minkowski sum is exactly

    sum_i alpha_i U_i = l_alpha + u_alpha Delta_3,
    l_alpha=sum_i alpha_i l_i, u_alpha=sum_i alpha_i u_i.

One containment follows from convexity of Delta_3; the reverse follows by choosing the same simplex point in every nonzero summand. Hence the manuscript's H=0 worst-case geometry is exactly

    G_U(alpha) = L max_{b,c=1,2,3}
      ||l_star+u_star e_b-l_alpha-u_alpha e_c||_2.

Maximization of a convex norm over the two simplices reduces to nine vertex pairs. This is exact for the continuous polytopes, not a Monte Carlo approximation or replacement of a simplex by an independent-coordinate box. It can be conservative for the narrower affine gamma cube and for joint restrictions linking source-arm bias and profiles, but it is the specified original smoothness-based envelope.

With a declared extra source bias envelope beta_extra,i>=0, define

    B_U(alpha)=G_U(alpha)+sum_i alpha_i(beta_imb,i+beta_extra,i).

The primary branch takes beta_extra=0 conditionally on its response/measurement assumptions. Positive values are sensitivity assumptions, not estimated correction terms.

## 5. R2, R-infinity, and optimization

For weights chosen exclusively from counts, profiles, masks and fixed model constants,

    R2(alpha;zeta)=B_U(alpha)
       +sqrt(2 log(2/zeta)) ||(alpha_i s_i)_i||_2.

For any allowed weights, including source-outcome-dependent choices, one common coordinate event gives

    Rinf(alpha;zeta)=B_U(alpha)
       +sqrt(2 log(2K/zeta)) sum_i alpha_i s_i, K=40.

On the respective noise event, the triangle inequality and deterministic geometry imply |sum alpha_i RD_i-tau_star^X|<=R. R2 has per-fixed/design-measurable-contrast failure at most zeta. Rinf has failure at most zeta simultaneously for every alpha and all 17 targets sharing the same covered source/target sets. The event is |xi_i|<=sqrt(2log(2K/zeta))s_i for every source.

Both minimizations are convex and admit SOCP form. Introduce g with g>=L||l_star+u_star e_b-sum alpha_i l_i-(sum alpha_i u_i)e_c|| for each of nine pairs. R2 adds a second-order-cone epigraph for ||s odot alpha||; Rinf has a linear noise term. An implementation must check simplex feasibility and independently recompute each displayed objective at the returned weights. A feasible numerical optimizer output gives a valid evaluated radius even without a certified global optimum; only optimality claims require the latter. Failure of numerical convergence is not a scientific model rejection.

For M prespecified design-only weighting methods across 17 targets, a shared R2 guarantee follows by assigning zeta_source/(17 M) to each contrast. This Bonferroni budget is sufficient, not necessary. A shared Rinf event can instead cover any number of methods and targets without an additional method/target factor. The two budget conventions must be stated when comparing R2 and Rinf.

**Frozen execution budget:** the four design-only policies are Uniform, design-IV, optimized R2, and optimized Rinf. A displayed R2 radius for the optimized-Rinf policy also counts in this family. There are 4*17=68 R2 contrasts. Assign zeta_2=.025/68 to each, and assign zeta_infinity=.025 to the one shared source-coordinate event. The union bound then controls all these source-error statements together at failure at most .05, conditionally on the model. Main decisions use R2 for Uniform, design-IV and optimized R2; they use Rinf for optimized Rinf, conventional FE and DL. Thus the optimized-Rinf policy has a displayed family-protected R2 diagnostic but its main decision follows its Rinf radius. This .05 is the combined source-error budget; noisy target-reference evaluation retains its separately stated failure budget and adds to it for a joint source-plus-reference assertion.

FE using sample-outcome variances and DL using estimated heterogeneity generally have outcome-dependent weights. They do not qualify for R2 merely because their formula resembles a weighted mean. Their conventional intervals are approximate model-based baselines; an ATLAS conservative check for those weights can use the shared Rinf event. Uniform or inverse count-only design-variance weights qualify for R2 under the stipulated response law.

## 6. Sensitivity and probability bookkeeping

For a residual model |tau_s^X-mu(p_s)|<=rho_s, target/source residuals contribute

    rho_star + sum_i alpha_i rho_i.

A common deterministic envelope rho contributes 2rho. This is a model extension, not the unchanged exact common-CATE theorem. The TV imbalance envelope remains valid because tau_s^X is still the cohort average of its own q_s1-q_s0. A grid such as rho in {0,.025,.05,.10} or beta_extra in {0,.025,.05,.10} defines sensitivity scenarios. Source residual maxima, random-effects SDs, Q-profile upper limits and nonsignificant heterogeneity tests do not justify a uniform source-and-target rho. Do not assign rho a failure probability unless an actual calibration procedure supplies one. If an external residual-envelope event has a justified failure eta_rho, add eta_rho to the total failure budget. A deterministic structural assumption has no automatically earned probability of truth.

The canonical finite-cohort profile containment needs no random profile budget conditionally on accurate labels. A model-relative 1-zeta_source assertion is conditional on the response, measurement, and transport assumptions. It is not an unconditional empirical real-data causal certificate. Numerical release at R<=delta and numerical refusal at R>delta are both legitimate outputs under the declared conditional model, even when scientific qualification remains false/unverified.

## 7. Evaluation against noisy target RDs

Let the withheld target outcome yield RD_star. Apply the same target conditional response law, imbalance algebra and proxy s_star^2=.25(1/n_star1+1/n_star0). A simultaneous target-reference event of failure zeta_reference uses

    e_star = beta_imb,star
      +sqrt(2log(2*17/zeta_reference)) s_star.

Then, on the source and target events,

    |sum_i alpha_i RD_i - RD_star| <= R_source + e_star,

with any declared target extra bias and residual terms included in their proper positions. The union bound gives failure at most zeta_source+zeta_reference, plus any genuine additional calibrated-event failures. Source and reference events need not be independent for this bound. This is an inclusion check for a noisy observed reference, not direct observation of coverage of tau_star^X. Target outcomes are not used to choose weights, constants, tolerances, model, category map or sensitivity grid. Reports should distinguish raw prediction errors, naive reference inclusion, uncertainty-adjusted inclusion, and conditional latent-effect coverage claims.

Uniform, FE and DL estimates may be compared on the same 17 withheld target RDs. Their conventional confidence/prediction intervals retain their own approximation and model scope; they do not inherit finite-sample ATLAS validity by sharing a table. All release/refusal rates use all 17 targets as denominator for an actually executed conditional branch, while empirical qualification is reported separately.

## 8. Relation to the manuscript

The source manuscript is `reviewer1-sprint/causal_lab_proposal_subpapers_tex_iclr2027/01_three_reviewer_experiments.tex`, operational-envelope and Rinf equations plus its design-measurable R2 alternative. This implementation supplies an explicitly conditional observed-profile instantiation of its geometry/noise/bias decomposition. It changes no manuscript, previous result, frozen split, or original artifact. The response-law assumptions are mathematical scope conditions added explicitly for this numerical branch; prior qualification failure is preserved as an audit finding rather than used as an execution gate.
