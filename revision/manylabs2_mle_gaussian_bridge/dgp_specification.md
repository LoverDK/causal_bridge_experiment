# Frozen source-calibrated Bernoulli study specification

This is a conditional simulation and approximation study. It preserves the outcome-observed design of 57 Many Labs 2 sites and 7,228 participants, split into 40 source sites/4,365 participants and 17 held-out target sites/2,863 participants. No real held-out target outcome is read. Simulated sample-size increases are hypothetical future experiments, not extra real participants. Numerical execution proceeds independently of scientific qualification.

## 1. Inputs, code, and access boundary

The builder `code/build_inputs.py` reads only the copied `data/all_design.csv` (no Y column) and `data/source_only.csv` (source outcomes permitted). It asserts cohort counts, the 40/17 site split, source participant identifiers, positive historical arm totals, category definitions, and profile containment. It produces the simulation driver's `protocol/execution.json`, a `protocol/calibration_summary.json`, and `protocol/design_cell_inventory.csv`. Input SHA-256 hashes are in execution.json. The driver consumes that frozen JSON rather than reopening real outcomes.

Categories, in array order, are Male (sex=1), Female (sex=2), and Other (sex=3). Refusal (sex=4) and blank labels mean unknown substantive membership. They are never a fourth category or automatically Other. Treatment indices are 0=Expensive and 1=Cheap; Y=1 means Yes. Sites are sorted lexicographically for all array indices and deterministic tie breaking. Candidate future outcomes are independent fresh draws even if a candidate uses the profile of a historical source or target site.

## 2. Calibration uses every source outcome

For each arm t, known labels contribute binomial likelihood terms with category-specific q_tc. An unknown-label participant contributes a Bernoulli mixture with fixed prespecified latent weights (1/3,1/3,1/3), hence response probability qbar_t=(q_t1+q_t2+q_t3)/3. Its log likelihood is Y log(qbar_t)+(1-Y)log(1-qbar_t). This integrates a declared latent membership model; it does not impute the person's category or assign their outcome to a specific category.

The calibration objective is therefore

\[
 \ell(q)=\sum_{t,c}\{k_{tc}\log q_{tc}
 +(n_{tc}-k_{tc})\log(1-q_{tc})\}
 +\sum_t\{k_{t,u}\log\bar q_t
 +(n_{t,u}-k_{t,u})\log(1-\bar q_t)\}.
\]

Raw q_raw maximizes ell. DGP-only q_smooth maximizes ell+0.5 sum_tc[log(q_tc)+log(1-q_tc)]. This is named **half-count regularization**, not Jeffreys MAP. The penalty adds half a success and half a failure to each known-category likelihood term; the mixture contribution remains intact. It is a frozen DGP-generation procedure, not a replacement for failed simulated logistic MLEs. The unregularized mixture likelihood and penalized objective are concave in q. Multiple deterministic optimizer starts check objective agreement, and the builder records optimizer status, boundary status, and score residuals.

All 4,365 source outcomes enter the fit. Observed known-category support is Male n0=686,k0=204,n1=654,k1=322; Female n0=1,488,k0=490,n1=1,478,k1=756; Other n0=7,k0=4,n1=5,k1=1. Unknown membership contributes n0=20,k0=6,n1=27,k1=13 (47 participants total). Other is extremely sparse despite an interior pooled solution. The latent uniform weights are a scientific assumption, not an identified empirical distribution for missing categories.

The deterministic fitted values, ordered Male/Female/Other, are:

* Raw treatment 0: (0.2967352914, 0.3289885620, 0.4962011275).
* Raw treatment 1: (0.4931059811, 0.5118343235, 0.2790975382).
* DGP treatment 0: (0.2970289605, 0.3291024603, 0.4964863470).
* DGP treatment 1: (0.4929824802, 0.5117669915, 0.3072731200).

Both fits are interior and have finite logit parameters; this is a source-pooled support statement, not success of all site-by-cell estimators. Binary response law, common contrasts, stable underlying category membership, and treatment-invariant recording remain model assumptions. In particular, the post-task measurement of sex does not empirically establish its status as a baseline covariate.

## 3. Profiles, unknown membership, and integer future allocation

For each site s, let k_sc count observed substantive labels, r_s count unknown labels, and n_s count every design participant. Its set U_s={p in simplex: p_c>=k_sc/n_s} is retained exactly. Main profile is its barycenter

\[
 p_{sc}=k_{sc}/n_s+r_s/(3n_s).
\]

Three prespecified extreme completions assign all unknown profile mass to Male, Female, or Other. They change only the latent composition assumption, retain every participant, and stay inside U_s. These are simulation populations, not recovered real categories.

At scale r in {1,2,5,10,20}, each historical site arm total is exactly n_st(r)=r*n_st. Its cell counts use Hamilton largest-remainder allocation of n_st(r)*p_sc: take coordinate floors, then give the remaining units to largest fractional remainders, ties by fixed category index. This preserves exact arm totals, historical treatment allocation ratio, relative site sizes, and target site composition up to recorded integer error (<1 count per cell). Population p_s stays constant across scales. The estimator standardizes to that fixed p_s; realized arm-category composition is its deterministic integer approximation.

This is a prospective allocation design. It does not multiply the historical within-arm category counts, which could preserve active empty cells forever. It also does not force every active cell positive by taking participants from another cell. Active empty cells remain visible for small sample sizes; structural p_sc=0 terms are omitted before division. `design_cell_inventory.csv` records all 57 sites, four profile completions, five scales, exact cells, empty-cell flags, structural zeros, and integer errors.

## 4. DGP A and heterogeneity DGP B

Under A, for every site, Y_stc has probability q_smooth,tc. The category contrast gamma_c=q_1c-q_0c is common and tau_s=p_s^T gamma exactly. Independent binomial counts are generated conditional on the fixed design.

Under B, use seed 2026110901 to draw 57 independent Uniform[-1,1] numbers in lexicographic site order, center them by their site mean, and divide by their maximum absolute centered value. Call the resulting values z_s, so their unweighted site mean is exactly zero numerically and max|z_s|=1. Set

\[
 h=\min\{0.05,\;0.5\min_c(q_{1c},1-q_{1c})\}=0.05,
\quad q_{s0c}=q_{0c},\quad q_{s1c}=q_{1c}+h z_s.
\]

All probabilities remain strictly between zero and one; no clipping is used. The perturbation is the same across categories within a site, so gamma_sc=gamma_c+h*z_s and tau_s=p_s^T gamma+h*z_s. Its mean is zero across all 57 sites, not necessarily within source sites, target sites, selected candidates, or participant-weighted sites. The common linear mean model is violated and that residual does not shrink as n grows. The single realized vector z is frozen and published in execution.json; it is not redrawn to improve results.

## 5. Fixed hypothetical bridge menu

The main menu is constrained **before outcomes** to sites whose active standardized-RD cells are positive at every main scale under the barycenter profile. There are 29 eligible sites among the 57. This is an explicit design-support constraint for future saturated-cell experiments, not an outcome-conditioned successful-site subset. All 57 sites remain in Gaussian-approximation diagnostics, including the 28 sites outside this menu eligibility rule.

Select the lexicographically first eligible site, then repeatedly select the eligible site whose p is farthest in Euclidean distance from its closest already-selected profile; ties are lexicographic. Duplicate profile vectors cannot enter the menu twice. The 12 selected profiles, in acquisition-menu order, are armstrong, radboud, tanzania, ouhk, kwazulu, osnabruck, umich, ulatina, tilburg, pascal, padua, and queensland2. The same site identifiers are frozen across every sensitivity scenario. Extreme-completion cells that become unavailable are reported rather than secretly replacing the menu. These are hypothetical new RCTs using historical profiles, not experiments already performed.

The 17 target profiles are used as design points only. Since they were observed retrospectively and include post-task category recording, this supports a declared simulation stress test rather than a prospective validation of real transport assumptions. Candidate budgets 1,2,4 count experiments; participant expenditures can differ and must be reported separately.

## 6. Frozen working model and replication regime

Initial base prior is mean zero with covariance I_3. Each Monte Carlo replication regenerates all 40 source experiments from the declared DGP. Their counts are pooled by category and arm, retaining every simulated source participant, to form three independent category-RD initial observations with regressors e_c. This differs from requiring 40 site standardized MLEs; the latter remain diagnostics. Every future candidate experiment is generated independently of these source draws. All selected subsets share potential candidate outcomes within a replication for paired comparisons.

There are two nonadaptive noise plans: source-plugin uses q_raw, frozen before simulation, for working source and bridge variances; oracle uses the actual scenario/site Bernoulli probabilities. The regularized q_smooth used for DGP generation differs from raw planning q, so these plans are genuinely distinct even in A. Neither uses simulated bridge outcomes to choose designs or update planning variances. Replicate-specific plug-in Delta standard errors are a separate approximation diagnostic.

For B, the true pooled source mean for category c is

\[
 \bar q_{1c}^{src}-\bar q_{0c}^{src},\quad
 \bar q_{tc}^{src}=\frac{\sum_{s\in src}n_{stc}q_{stc}}{\sum_{s\in src}n_{stc}},
\]

and its true oracle variance is sum_s[n_s1c q_s1c(1-q_s1c)]/N_1c^2 plus the corresponding treatment-0 term. A single common q times 1/N is not that heterogeneous variance. Oracle noise corrects the sampling variance, not the misspecified common source mean or bridge/target structural residuals.

For each scale and noise plan the source posterior covariance and menu scores are frozen across replications because counts and planning noise are fixed; source posterior means vary with repeated source outcomes. The logdet guarantee applies to this deterministic working surrogate objective. Fixed-gamma repeated-source target coverage is assessed empirically and is not inferred from the Bayesian covariance theorem. Source fitting uncertainty beyond the frozen real-source calibration is not included in this conditional DGP experiment.

## 7. Condition inventory, oracles, and diagnostics

Main conditions are two DGPs times five scales, each with 5,000 replications. Secondary conditions use DGP A, scales 1,5,20, and 2,000 replications: three extreme profile completions and nine Other-probability pairs (q_0Other,q_1Other) in {0.2,0.5,0.8} squared. This totals 46 DGP/profile/scale conditions. The baseline posterior model, planning q_raw and menu are unchanged across the prespecified Other grid; the oracle noise uses each grid's true probabilities.

Budgets 1,2,4 compare logdet greedy, exhaustive logdet, a declared target-variance greedy diagnostic, random selection, nearest-profile selection, and a simulation-DGP Bernoulli target-MSE oracle. Exhaustive evaluation covers 12+66+495=573 subsets. The Monte Carlo oracle uses an independent 2,000-replication pilot, then evaluates selected subsets on fresh main or sensitivity replications. An analytic target-MSE oracle is also available because the posterior decoder is linear with fixed variances and Bernoulli first two moments are known. Neither target-MSE oracle inherits the logdet approximation guarantee.

All 57 sites are retained in failure/normality reports; active-empty estimates remain unavailable, and boundary occupied cells are labeled finite-logit failures even when the extended probability MLE K/n is used for a defined RD. Strict parameter normality and scalar functional normality are separate. Oracle variance is exact for the linear Bernoulli RD when its active cells are occupied; normality affects its distribution and interval calibration. The usual plug-in variance is downward biased by its (1-1/n_cell) factors. With fixed decoder weights, moment-matched Gaussian and Bernoulli target MSE agree by first-moment/second-moment algebra even when shape differs; that agreement cannot validate Gaussian tails. Coverage and joint-candidate diagnostics are required.

Adequacy thresholds, failure-denominator conventions, and scientific limitations are recorded prospectively by the independent audit. Report empirical coverage/quantiles, uncertainty and undefined fractions, rather than selecting favorable sites or tuning the DGP. A positive numerical finding supports only the specific conditional DGP/design regime tested. It does not validate real Common-CATE, stable post-task category measurement, finite-sample Gaussianity, or universal non-Gaussian use of Theorem 5.6.
