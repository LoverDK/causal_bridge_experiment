# Saturated logistic MLE, standardized risk differences, and the Gaussian bridge

This is a derivation for the declared Bernoulli simulation, conditional on its population profiles and treatment/category counts. It does not establish a causal model for the real Many Labs 2 responses. The derivation uses the source manuscript's scalar linear-Gaussian design model but does not extend its exact finite-sample theorem to Bernoulli observations.

**Execution lock:** the study uses repeated simulated source observations and base prior mean zero/covariance I_3. DGP probabilities are the source-only half-count-regularized mixture fit; source-plugin planning probabilities are the separate raw mixture MLE. Both are frozen before simulation. The 12-candidate main menu is selected from 29 sites satisfying an outcome-blind active-cell support constraint at all five main scales; diagnostics retain all 57 sites. See `dgp_specification.md` and `protocol/execution.json` for exact fitted values, completion profiles, Hamilton allocation, and the 46 conditions. Generic alternatives discussed below explain scope rather than changing this locked implementation.

## 1. Sampling model and estimand

For experiment s, treatment t in {0,1}, and substantive category c in {Male,Female,Other}, write

\[
 K_{stc}\sim\operatorname{Binomial}(n_{stc},q_{stc}),
 \qquad \beta_{stc}=\operatorname{logit}(q_{stc}).
\]

These binomial counts are independent conditional on the specified designs. Under DGP A, q_stc=q_tc for every site. Define gamma_c=q_1c-q_0c and the prespecified population profile p_s in the three-category simplex. The target effect and its standardized estimator are

\[
 \tau_s=\sum_c p_{sc}(q_{s1c}-q_{s0c}),\qquad
 \widehat\tau_s=\sum_c p_{sc}(\widehat q_{s1c}-\widehat q_{s0c}).
\]

Under A, tau_s=p_s^T gamma exactly. This is a scalar observation; p_s is the actual three-dimensional scalar-observation regressor. It must not be replaced by a category-observation vector to conceal a change of experiment.

The weights are the declared simulation population composition, not the realized treatment-arm composition. Conditional on positive cell counts, known fixed p, and the Bernoulli model, the probability-space estimator is exactly unbiased, and its oracle variance below is exact. The Gaussian distributional approximation, and the accuracy of its plug-in standard error, remain finite-sample questions.

Unknown recorded labels are retained. A latent completion of each observed-profile uncertainty set is a simulation assumption. Its barycenter is a continuous representative profile, not a claim that an unknown person's real category is known. Integer assignments must be declared, deterministic or independently randomized according to a frozen rule, and shared by all outcome-blind methods in a scenario. Sex was recorded after the task; stable underlying membership and treatment-invariant reporting are assumptions, not empirical findings.

## 2. Likelihood, finite MLE, and empty cells

The saturated log likelihood, with terms having n=0 omitted, is

\[
 \ell_s(\beta)=\sum_{t,c}\{K_{stc}\beta_{stc}
       -n_{stc}\log(1+e^{\beta_{stc}})\}.
\]

The score is K-nq and observed/expected information is diagonal with entries n q(1-q). If n>0 and 0<K<n, the unique finite estimate is

\[
 \widehat\beta=\log\frac K{n-K},\qquad \widehat q=K/n.
\]

Three cases must be distinguished:

1. **Interior occupied cell:** n>0 and 0<K<n. Both the finite-logit MLE and probability MLE exist.
2. **Boundary occupied cell:** n>0 and K=0 or K=n. There is no finite beta MLE; the likelihood supremum occurs at beta=-infinity or +infinity. The explicitly named **extended probability MLE**, maximizing the binomial likelihood over the closed interval [0,1], is still qhat=K/n. It is a mathematically defined estimator, not an arbitrary imputation, convergence repair, or smoothed MLE. A plug-in variance contribution is zero at such a boundary, which can materially understate uncertainty.
3. **Empty cell:** n=0. The likelihood is constant in that cell's q, so q is unidentified. If p_sc>0, the requested saturated standardized RD is undefined without an additional estimation model. Return missing/undefined with an active-empty flag. If p_sc=0, that category is structurally irrelevant to the functional; omit the term before division. Do not evaluate 0/0, assign it a q, or call it an active-cell failure.

Report both the finite-logit MLE success rate and the extended-RD availability rate. A closed-form implementation has no iterative nonconvergence when an interior finite MLE exists; analytic nonexistence and solver failure are different diagnostics. Do not classify finite-beta failure as successful logistic convergence merely because qhat=0 or 1 is computable.

When a cell has fixed positive q in (0,1), its boundary probability is exactly

\[
 \Pr(K\in\{0,n\})=(1-q)^n+q^n\quad(n>0).
\]

With independent occupied cells, strict finite-logit success over a required set is the product of one minus these probabilities. This is a useful analytic audit of Monte Carlo failure counts. A structurally absent category is excluded from the functional success event. If reporting the six-parameter saturated model, separately report that all-six identification can fail even when the functional is defined.

## 3. MLE normality and the Delta Method

Consider a sequence of experiments with N_s increasing and n_stc/N_s -> a_stc>0 on every active cell c with p_sc>0. Assume q_stc is fixed and lies in [epsilon,1-epsilon] for epsilon>0. Independence and binomial CLTs yield

\[
 \sqrt{N_s}(\widehat\beta_s-\beta_s)
 \rightsquigarrow N\!\left(0,
 \operatorname{diag}_{tc}\{[a_{stc}q_{stc}(1-q_{stc})]^{-1}\}\right)
\]

for the identifiable active parameter subvector. The probability of a boundary occupied cell tends to zero, so an arbitrary definition of beta on the failure event does not affect this limiting assertion; it does not make beta finite on those realizations.

For g_s(beta)=sum_c p_sc[expit(beta_s1c)-expit(beta_s0c)], the derivative for cell (t,c) is

\[
 \frac{\partial g_s}{\partial\beta_{stc}}
 =\begin{cases}p_{sc}q_{s1c}(1-q_{s1c}),&t=1,\\
 -p_{sc}q_{s0c}(1-q_{s0c}),&t=0.\end{cases}
\]

The Delta Method gives

\[
 \frac{\widehat\tau_s-\tau_s}{\sqrt{v_s}}\rightsquigarrow N(0,1),
\quad
 v_s=\sum_{c:p_{sc}>0}p_{sc}^2
 \left\{\frac{q_{s1c}(1-q_{s1c})}{n_{s1c}}
       +\frac{q_{s0c}(1-q_{s0c})}{n_{s0c}}\right\}.
\]

The displayed v_s is also the **exact conditional variance** of the extended probability-RD estimator whenever all active counts are positive. Its finite-sample distribution is a weighted convolution of binomials and is discrete, not Gaussian. Plugging qhat into this expression yields the requested Delta variance

\[
 \widehat v_s=\sum_{c:p_{sc}>0}p_{sc}^2
 \left\{\frac{\widehat q_{s1c}(1-\widehat q_{s1c})}{n_{s1c}}
       +\frac{\widehat q_{s0c}(1-\widehat q_{s0c})}{n_{s0c}}\right\}.
\]

For K~Binomial(n,q), E[qhat(1-qhat)]=(1-1/n)q(1-q). Thus the uncorrected plug-in variance is downward biased, particularly when n is small. A separately labeled n/(n-1) correction is possible for n>1, but must not replace the prespecified main estimator after inspecting coverage. At n=1 it cannot identify q(1-q) from a single Bernoulli observation. A zero total plug-in variance produces an invalid standardized error or degenerate interval; retain and count that failure.

The qhat=K/n estimator and its exact variance can be derived directly from binomial means. The logistic route supplies the requested link to the MLE/Delta argument, but is not needed to prove unbiasedness or the variance identity.

In this execution the raw source calibration is a different model from the simulated per-site saturated MLE: it uses every real source outcome and integrates unknown-label responses with a fixed uniform latent-category mixture. Half-count regularization is applied only to produce DGP probabilities. It is never used to fill a failed simulated site cell or alter its MLE diagnostic.

## 4. Strict parameter normality versus functional normality

Full six-parameter normality requires identifiability and diverging information in all six cells. A standardized RD can have a good approximation when this stronger condition fails. For example, a category of very small population weight can cause frequent finite-logit separation while contributing little to total RD variance. This must be demonstrated, not inferred from a large total site n.

For a triangular array, write the centered RD as a sum of centered participant Bernoulli responses with coefficients +p_sc/n_s1c or -p_sc/n_s0c. A convenient sufficient Lindeberg condition is

\[
 \max_{t,c:p_{sc}>0}\frac{p_{sc}/n_{stc}}{\sqrt{v_s}}\longrightarrow0,
 \qquad v_s>0.
\]

Bounded Bernoulli responses then imply the scalar CLT. Under fixed profiles with all active cell proportions bounded away from zero, the condition follows automatically. A useful finite-sample Berry-Esseen diagnostic is

\[
 L_s=v_s^{-3/2}\sum_{t,c:p_{sc}>0}
 \frac{p_{sc}^3}{n_{stc}^2}
 q_{stc}(1-q_{stc})\{q_{stc}^2+(1-q_{stc})^2\}.
\]

An absolute universal constant times L_s bounds the Kolmogorov normal-approximation error for the independent weighted sum. A small L_s is sufficient evidence from the stipulated DGP, not a real-data model test. Sparse terms can alternatively be shown negligible relative to sqrt(v_s), while a CLT is applied to the remaining terms. An active empty cell remains an identification failure; a negligible-weight argument does not define its missing qhat for free.

Consequently diagnostics must display all 57 sites, active/structural emptiness, boundary frequencies, finite-logit success, RD availability, and normality/coverage for the declared functional. Success-conditioned diagnostics alone select unusual binomial samples and do not describe unconditional estimator performance. Display missing or invalid fractions explicitly; report unconditional interval success with unavailable intervals counted as failures, together with any separately named availability-conditioned diagnostics.

## 5. Composition, integer allocation, and scaling

Preserve each site's declared population profile and historical treatment ratio. One valid future-RCT sequence sets n_st(r)=r*n_st at scales r in {1,2,5,10,20}, allocates n_stc(r) by a frozen largest-remainder rule targeting n_st(r)*p_sc (or generates a prespecified multinomial allocation), and records resulting counts. It preserves site population composition asymptotically, historical arm totals exactly, and relative site size exactly; integer approximation error must be recorded. A multinomial version makes p a population rather than exact realized cohort profile and requires conditional-versus-unconditional variance bookkeeping.

If instead historical within-arm category counts are multiplied exactly, a historical n_stc=0 remains zero at every scale. When p_sc>0, such a sequence never reaches the stated saturated-MLE regularity conditions. Scaling total site n does not fix that failure. Report this distinction. Completion scenarios must remain inside U_s and keep unknown participants in the design; extreme feasible completions define separate DGP scenarios, not outcome-driven corrections.

## 6. Joint candidate normality

For a fixed menu of 12 independent future bridge experiments, with p_b fixed and all their functional CLT conditions satisfied, their centered standardized RD vector converges jointly to N(0,I_12). This follows from independence and marginal CLTs (or Cramer-Wold). The approximation is local to this finite menu. Shared controls, participant reuse, common estimated profiles, or noisy nuisance parameters shared across experiments can induce correlation and invalidate the independent scalar-noise model unless conditioned out or modeled explicitly.

A source-fitted DGP is held fixed when generating outcomes in a condition. Conditioning on that frozen fit removes calibration randomness from the conditional simulation, but does not establish that real-data calibration uncertainty is negligible. Oracle v_b uses the stipulated DGP probabilities. Source-fit plug-in v_b uses probabilities fitted once to real source outcomes and frozen before any bridge outcomes. Replicate-specific bridge qhat variance is a separate estimator diagnostic; using it to choose later bridges would create outcome-adaptive design and falls outside the stated theorem.

## 7. Source-only Gaussian summary model without participant deletion

Under DGP A, pool simulated source participants by treatment and latent completed category, rather than requiring each of the 40 sites to have every cell. With N_tc=sum_{s in source}n_stc and K_tc=sum_s K_stc, define

\[
 z_c=K_{1c}/N_{1c}-K_{0c}/N_{0c},\qquad
 a_c=\frac{q_{1c}(1-q_{1c})}{N_{1c}}+
     \frac{q_{0c}(1-q_{0c})}{N_{0c}}.
\]

Then z_c is unbiased for gamma_c with exact variance a_c; distinct categories use disjoint independent responses. The approximation is three scalar source observations z_c=e_c^T gamma+eta_c with eta approximately N(0,a_c). Every source participant belongs to one completed latent category and contributes once. The 40 individual source-site diagnostics must still be reported; pooling is an explicitly different initial summary model, not a claim that their saturated site MLEs all succeeded.

Choose a **prespecified arbitrary positive-definite** base covariance W (for example I_3), with declared base mean m_prior (for example zero). With A=diag(a_c), the source Gaussian update is

\[
 V_0=(W^{-1}+A^{-1})^{-1},\qquad
 m_0=V_0\{W^{-1}m_{prior}+A^{-1}z\}.
\]

Do not call an arbitrary ridge an estimated real-data covariance. W is a modeling choice whose influence should be reported. If any pooled active source cell is empty, z_c is undefined; the Gaussian source likelihood cannot use that coordinate. Retaining the corresponding unupdated prior precision from W is an explicit prior model, not MLE recovery. A finite W ensures V0 is positive definite, but does not repair an empirical rank problem or validate the prior.

For comparison, a source site-level design matrix X_source with rows p_s and variance matrix D_source would give precision W^-1+X_source^T D_source^-1 X_source when all its required summaries exist. Its rank, eigenvalues, condition number, and any unavailable site summaries must be disclosed. Pooled e_c summaries avoid the category-empty site estimators under DGP A and differ statistically from a regression on 40 site RDs; use one declared source construction consistently across design comparisons.

Under site heterogeneity, the pooled counts are generally sums of binomials with different q_stc; their variance uses sum_s n_stc q_stc(1-q_stc)/N_tc^2. Arm-specific site weights can also change the pooled mean contrast. Do not carry the exact A source model into B as if the Common-CATE assumption remained true.

For this study W=I_3, m_prior=0 and source z is regenerated in every replication. The covariance A is fixed per condition and noise plan: oracle uses the actual scenario probabilities and sum-of-binomial variance, while source-plugin uses the frozen raw source probabilities. Thus V0 is deterministic within a condition, m0 is random through repeated source z, and source calibration itself is held fixed. Under B, actual pooled source means are arm/category-count-weighted means of q_stc. Correct oracle variance does not make those means equal to one globally shared gamma.
