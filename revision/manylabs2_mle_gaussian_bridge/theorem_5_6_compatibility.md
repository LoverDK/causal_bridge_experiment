# Compatibility with Theorem 5.6: scalar Gaussian surrogate and its limits

Source inspected: `reviewer1-sprint/causal_lab_proposal_subpapers_tex_iclr2027/01_three_reviewer_experiments.tex`, the theorem labeled `thm:logdet`, scalar measurement model in Appendix extended theory, proof of that theorem, and the target-radius corollary. This file changes no manuscript. The theorem concerns a fixed menu, independent scalar Gaussian observations, a positive-definite Gaussian prior covariance, and a cardinality budget.

**Locked execution regime:** base prior mean zero/covariance I_3; repeated simulated 40-site sources summarized by three pooled category RDs; source calibration fixed from all 4,365 permitted source outcomes through a uniform-mixture unknown-label likelihood. DGP probabilities use a half-count-regularized fit while source-plugin planning uses its unregularized fit. The 12-design menu is restricted prospectively to 29 barycenter profiles with positive active cells at all main scales; all 57 sites remain in diagnostics. This is a narrower future-design menu than an unrestricted arbitrary site menu. See `dgp_specification.md` for the exact choices.

## 1. Exact scalar mapping for the declared surrogate

Under simulation DGP A, gamma_c=q_1c-q_0c is common across sites and a future bridge standardized RD has exact mean p_b^T gamma. With positive occupied active cells, its exact conditional Bernoulli variance v_b is derived in `mle_delta_derivation.md`. The Gaussian surrogate is

\[
 Z_b=p_b^T\gamma+\epsilon_b,\quad
 \epsilon_b\overset{ind}{\sim}N(0,v_b),\qquad
 \gamma\mid\text{source}\sim N(m_0,V_0),\quad V_0\succ0.
\]

The mapping is x_b=p_b, sigma_b^2=v_b. Z_b is one scalar, the standardized site RD. The response probability parameters do not become six Gaussian bridge observations. A nonzero prior mean is immaterial: apply the source theorem to beta=gamma-m0 and centered observation Z_b-p_b^T m0. Positive-definite V0 can come from a declared arbitrary PD base covariance plus the source-only Gaussian summary update. Centering and covariance choice do not prove Gaussianity of the original binary data.

The support of a Gaussian prior for gamma extends beyond [-1,1]^3, while actual Bernoulli contrasts cannot. It is a local working prior/surrogate, not an exact generative prior for all admissible Bernoulli probability pairs. Truncating the prior would change the conjugate Gaussian covariance formula and requires a separate analysis.

With fixed v_b>0, define

\[
 V_S=\left(V_0^{-1}+\sum_{b\in S}v_b^{-1}p_bp_b^T\right)^{-1},
\quad
 F(S)=\frac12\log\frac{\det V_0}{\det V_S}
 =\frac12\log\det\left(I+V_0^{1/2}
       \sum_{b\in S}v_b^{-1}p_bp_b^T V_0^{1/2}\right).
\]

The square-root form is a stable way to interpret the determinant; use Cholesky/slogdet numerically. For any fixed PSD rank-one increments this set function is normalized, monotone and submodular by the source proof: the marginal is

\[
 \Delta(b\mid S)=\tfrac12\log(1+v_b^{-1}p_b^TV_Sp_b),
\]

and V_T is no greater than V_S in PSD order when S is contained in T. Thus a size-B greedy set satisfies

\[
 F(S_g)\ge[1-(1-1/B)^B]\max_{|S|\le B}F(S)
 \ge(1-e^{-1})\max_{|S|\le B}F(S).
\]

This **algebraic surrogate-objective guarantee is exact**, even if the actual data are Bernoulli and the surrogate is inaccurate. Its interpretation as mutual information I(gamma;Z_S|source) is exact only within the stated Gaussian surrogate, with observation noise independent of gamma and fixed given the design/calibration information. Bernoulli v_b depends on the underlying q; oracle fixed-v_b Gaussian design is a local design at the stipulated truth, not an exact Bayesian model with varying gamma and conditionally Bernoulli likelihood.

## 2. Candidate menu and budgets

Freeze 12 distinct hypothetical future bridge profiles using only historically available design information, a deterministic selection rule, and documented tie breaking. Fix their participant budgets and treatment ratios in advance. Budgets B in {1,2,4} count selected bridge experiments, not automatically equal participant costs when site sizes differ. Report participant totals as a separate metric. The finite pool has 12, 66 and 495 unordered subsets at those exact sizes, making exhaustive surrogate enumeration feasible. In total there are 573 budget-specific sets.

The 17 historical target profiles are design points for evaluating p_j^T gamma; their real target responses must remain unopened. The use of historical post-task descriptors for future-design hypotheses is retrospective and conditional on the declared stable-membership simulation assumption. Independent new Bernoulli bridge outcomes are generated even when a profile resembles a historical site. These are simulated future RCTs, not new real participants or trials already conducted.

An unavailable active-empty bridge RD cannot simply be assigned zero, a finite surrogate variance, or a smoothed estimate while continuing to call it the original MLE experiment. Either return unavailable and expose the design failure, or predeclare a separately labeled future cell-allocation/estimation design that identifies the functional. No site is deleted after seeing outcomes. Structural p_c=0 terms need no information about that category in that bridge.

## 3. Oracle versus source-fit and bridge-outcome plug-in noise

For each scenario freeze the source-calibrated DGP probabilities and all design counts before generating Monte Carlo bridge outcomes. Keep three variance concepts separate:

* **DGP oracle:** v_b computed using the known simulation response law. It isolates Gaussian distributional approximation from variance-estimation error.
* **Source-fit working variance:** computed from the fit to permitted real source responses, once, and held fixed across bridge replicates. In a simulation whose DGP is exactly that source fit, this numerically equals the DGP oracle; calling the two distinct empirical competitors would be misleading. A difference requires an explicit alternative fit, uncertainty perturbation, or scenario.
* **Bridge plug-in diagnostic:** vhat_b computed from each simulated bridge sample. This measures SE estimation and Wald coverage. If used to change later bridge choices or the menu, selection is outcome-adaptive and the source theorem does not cover that policy.

For heterogeneity, using common source-fit v_b is a misspecified working noise model; an oracle variance using site-specific probabilities separates that misspecification from nonnormality. In all cases use the same declared source covariance construction in compared policies. Positive-definite W can keep the posterior algebra defined but does not conceal weak source information, rank deficiency, or conditioning. Report those quantities.

In the actual execution, raw mixture-MLE q_raw and DGP-only regularized q_smooth are distinct by design, so source-plugin and oracle variance plans differ even under baseline A. This avoids claiming two identical oracle calculations as distinct competitors. The Other sensitivity grid and site heterogeneity can produce larger differences. Every plan is fixed across Monte Carlo outcome realizations. Replicated source observations affect posterior means; their realized outcomes do not alter posterior covariance or acquisition scores under this frozen-variance scheme.

## 4. Bayesian posterior covariance versus fixed-truth repeated-sampling coverage

The theorem's uncertainty reduction is Bayesian under its Gaussian prior. In the Bernoulli Monte Carlo, q and gamma are usually held fixed. A Gaussian posterior variance is then not automatically the repeated-sampling variance of its posterior mean and does not promise uniform fixed-gamma coverage.

For a clear calculation, suppose the initial source summary is z=X_0 gamma+eta_0, eta_0 has covariance D0, the base prior has mean m_prior and precision P=W^-1, and bridge summaries have design X_S and independent covariance D_S=diag(v_b). Define

\[
 J_0=X_0^TD_0^{-1}X_0,\quad J_S=X_S^TD_S^{-1}X_S,
\quad V_S=(P+J_0+J_S)^{-1},
\]

\[
 m_S=V_S\{Pm_{prior}+X_0^TD_0^{-1}z+X_S^TD_S^{-1}Z_S\}.
\]

For fixed true gamma and random independent source and bridge summaries with correct means and variances,

\[
 E[m_S]-\gamma=V_SP(m_{prior}-\gamma),\qquad
 \operatorname{Cov}_\gamma(m_S)=V_S(J_0+J_S)V_S
 =V_S-V_SPV_S.
\]

The formulas remain exact for Bernoulli summaries with those exact first two moments; normality is needed for normal interval calibration, not the covariance algebra. Target j has bias p_j^T V_SP(mprior-gamma) and sampling variance p_j^T(V_S-V_SPV_S)p_j. A reported posterior-normal interval m_target +/- z*sqrt(p_j^TV_Sp_j) is a nominal working Bayesian interval, whose fixed-truth empirical coverage must be measured. Prior shrinkage bias can defeat frequentist coverage despite posterior variance exceeding sampling variance.

If source data are held fixed across Monte Carlo replicates, write initial Gaussian state (m0,V0), J_S as above, and

\[
 E[m_S\mid m_0]-\gamma=V_S V_0^{-1}(m_0-\gamma),\qquad
 \operatorname{Cov}(m_S\mid m_0)=V_SJ_SV_S.
\]

State which replication scheme is used. Reusing a fixed real source fit to calibrate the DGP does not magically add random source replication to a bridge-only simulation. If source fitting uncertainty is omitted from the conditional simulation, say so. Frequentist variance formulas with no bias correction are not alone confidence guarantees. Consistent asymptotic Wald coverage additionally requires prior-induced bias negligible relative to target standard error, consistent covariance estimation, and correctly specified common means.

This study uses the preceding **repeated-source** scheme, with real-source calibration frozen. Therefore source-summary sampling variability is present, while uncertainty in the real calibration of q is absent. For source-plugin weights under B or a grid scenario, the actual response covariance need not equal the working D. Replace the matched-noise sampling covariance by the sandwich V_S X^T D_work^-1 D_true D_work^-1 X V_S (stacking source and selected bridges). Actual source/bridge means supply the structural bias. The identity V_S-V_SPV_S applies only when those working variances match truth and means follow the common model. The oracle plan fixes variances but cannot remove B's structural residuals.

## 5. Why a pointwise CLT does not alone transfer design decisions

Finite-sample Bernoulli summary distributions are discrete, have boundary events, and may have skewness. A pointwise CLT for a single bridge does not establish finite-sample joint approximation, selected-design coverage, or stability of an argmax over designs. Under the fixed 12-design menu, fixed three-dimensional parameterization, and independent experiments, uniformity over candidates can follow from finitely many marginal bounds. Source summaries require their own approximation.

Let F_r(S) be the oracle Gaussian surrogate objective at scale r and Fhat_r(S) a working version. If

\[
 \delta_r=\max_{S:\,|S|\le B}|\widehat F_r(S)-F_r(S)|\to_p0,
\]

then for a maximizer Shat of Fhat_r,

\[
 \max_S F_r(S)-F_r(\widehat S)\le2\delta_r=o_p(1).
\]

A unique optimum with oracle gap g_r satisfying delta_r/g_r ->p 0 gives agreement in probability. If the gap vanishes, regret can vanish without exact set agreement. Greedy path agreement requires every step's best-versus-runner-up marginal gap to dominate its uniform marginal-score error and deterministic tie breaking. A corresponding approximate-greedy bound is q_B*F_r(Sstar)-O(B*delta_r), where q_B=1-(1-1/B)^B; the numerical constant depends on whether delta bounds set scores or marginals. These claims require verified error conditions; they are not consequences of total n alone.

If real source calibration is frozen while only future bridge sample size increases, its estimation error need not vanish, so oracle agreement does not follow automatically. In this study scale is a finite design sensitivity, not a proof that the empirical source fit consistently estimates real population q. When source and candidate sample sizes both grow with positive active proportions, probabilities stay interior, source precision is identified, and plug-in variances are uniformly relatively consistent, smooth covariance/logdet maps provide the required uniform control subject to controlled conditioning.

For Bernoulli-risk design, define the risk of a fixed subset and estimator, for example

\[
 R_r(S)=\frac1{17}\sum_{j=1}^{17}
 E_\gamma[(p_j^Tm_S-p_j^T\gamma)^2].
\]

If a distinct Gaussian risk approximation satisfies sup_S|Rhat_r(S)-R_r(S)| ->0, its exhaustive argmin has vanishing **risk** regret by the same two-error argument. Logdet regret and target-MSE regret are different. In the exact-mean, frozen-linear-update baseline, the MSE equals squared bias plus variance using only first two moments; it can be computed exactly from the Bernoulli variance algebra. Thus good MSE agreement alone may be automatic and is weaker evidence about Gaussian tails than interval coverage or Q-Q diagnostics. The Bernoulli Monte Carlo oracle should use a separate training/evaluation stream or analytic exact risk to avoid optimistic reuse of the same noise for selecting and evaluating a minimum over 573 sets.

## 6. Fixed-menu interval and joint-normality claims

For each fixed S and each fixed target, a correct centered/studentized CLT plus negligible shrinkage bias gives asymptotic marginal Wald coverage. A design S selected only from the frozen profiles and source-calibration state is fixed conditional on that state with respect to future bridge responses. If a policy also selects among source-noise-dependent states, its unconditional assessment must replicate or condition on that selection correctly.

With only finitely many subsets and targets, convergence of every fixed-set approximation can be made uniform by taking the maximum of finitely many error bounds; pointwise-in-parameter convergence still does not imply uniformity over all q near 0,1 or nearly empty profiles. Simultaneous 17-target or all-subset coverage needs a joint critical value or valid multiplicity correction. Pointwise 95% intervals cannot be called 95% simultaneous intervals. Joint candidate diagnostics should test the full 12-vector and report correlations, radial/maximum-coordinate tails, or prespecified projections; aggregate univariate normality alone is insufficient.

## 7. What the guarantee says about targets

Logdet greedy and exhaustive logdet optimize information about all three category contrasts. Target-variance greedy optimizes a declared target criterion such as average or maximum p_j^T V_S p_j; its choice must be frozen. It has no approximation guarantee from Theorem 5.6. Random selection, nearest-profile selection, and exhaustive Bernoulli target-risk oracle likewise do not inherit that guarantee.

The source target-radius corollary requires cond(V_S)<=kappa for every relevant feasible size-B posterior and yields an absolute bound

\[
 r_S(q)\le q\|p_j\|\sqrt\kappa\det(V_S)^{1/(2d)},\qquad d=3.
\]

Combining it with the logdet determinant bound gives the manuscript's stated absolute greedy-radius bound. It does not prove target-variance or target-MSE optimality, a ratio to the target-optimal radius, or fixed-truth interval coverage. Enumerating all 573 subsets makes the condition-number premise auditable on this finite pool. If it is poorly conditioned, still report the numerical experiment and the limitation; scientific qualification is not a numerical execution gate.

## 8. Heterogeneity and approximation error must remain separate

Under DGP B let gamma_bc=q_b1c-q_b0c. The bridge mean is p_b^T gamma_b, which can be written p_b^T gamma+delta_b only by adding a site-dependent residual. Normality of its sampling error may improve with n while delta_b does not vanish. For working posterior mean, the mean error includes V_S sum_b v_b^-1 p_b delta_b (and source-model residual terms). Increasing sample size can narrow intervals around a biased transport limit. Mean-zero perturbations over a hypothetical site distribution do not guarantee zero residual at each fixed selected bridge or target, and nonlinear links/clipping can alter the implied mean. Report the actual perturbation construction and realized residuals.

To isolate effects, compare A versus B using the same designs/seeds where appropriate, oracle versus working variances within each DGP, and Gaussian summary draws with matched actual means/variances versus Bernoulli draws. The first comparison changes structure; the second changes variance calibration; the third targets distributional shape. Do not attribute B's persistent coverage failure to the Delta Method alone.

## 9. Conditions for a genuine finite-sample extension

A finite-sample Bernoulli theorem would require additional proved conditions, such as uniform lower bounds on active allocation and response probabilities; explicit concentration/Berry-Esseen or coupling errors for all relevant summaries; source-calibration and profile uncertainty control; a stable covariance/variance estimation rule; a bound transferring approximation error to the selected objective or loss; and an appropriate frequentist or Bayesian coverage argument matching the estimand. Exact Bernoulli mutual information can be submodular under a coherent prior and conditional independence, but its scalar likelihood, prior, objective, and relation to standardized RD information must be derived separately. It is not the conjugate logdet formula by default.

The supported rebuttal statement is conditional: in the prespecified Bernoulli DGP, sample sizes, profiles, source fit and bridge menu, report observed finite-logit failures, functional normality and Wald-coverage error, and the achieved Bernoulli target risk of Gaussian-selected designs. Scaling evidence may show when this local approximation becomes useful. It cannot prove universal non-Gaussian applicability, validate real Common-CATE, or establish the original theorem exactly for finite Bernoulli trials.
