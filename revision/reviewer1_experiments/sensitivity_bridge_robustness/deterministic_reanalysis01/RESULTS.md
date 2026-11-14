# Saved-design target-greedy reanalysis

The one-step target-variance rule is usually close to exhaustive target-optimal design on these archived Gaussian instances, but it is not globally optimal. At budget4, its target-radius ratio to the exhaustive optimum is1.029687 on average,1.000 at the median,1.092738 at the90th percentile and1.623690 at the worst instance. It reaches the optimum in118/200 designs and is suboptimal in82. No new theorem or general approximation ratio is claimed.

## Frozen task and one computational unit

Inputs are exactly the200 archived `bridge_designs.json` instances, IDs0–199, each with p=6 parameter dimensions,12 candidate observations, positive-definite prior covariance P, target vector t and sigma=.5 observation standard deviations. Every candidate can be selected at most once. All12,66 and495 subsets at budgets1,2 and4 are enumerated per design;114,600 subsets total. No beta, observationY or Monte Carlo world was generated. Prior/candidate/target values, costs and Gaussian assumptions were unchanged.

For one design, every saved subsetS determines V=(P^-1+sum x*x'/sigma^2)^-1. Its target variance is W=t'Vt and the reported Gaussian target radius is1.96sqrt(W). Logdet information is .5log(detP/detV). The two greedy rules use different scores on the same remaining candidates: target greed maximizes (t'Vx)^2/(sigma^2+x'Vx), and logdet greed maximizes .5log(1+x'Vx/sigma^2). Both update the same covariance by the rank-one formula. Paths depend only on design, not outcomes. Exhaustive target and logdet optima use their respective whole-budget objectives. The radius is a Gaussian posterior target-radius diagnostic, not a sharp partial-identification width, a U/L/H certificate or evidence of empirical coverage.

For illustration, archived design0 at budget4 yields target-greedy sequence[2,0,6,3], radius1.018124; logdet-greedy sequence[2,0,10,8], radius1.118453; exhaustive target set[2,4,8,9], radius .958400. Thus target greed improves the target objective relative to logdet on this instance yet leaves a6.23% radius gap to the global target optimum. This is an illustrative fixed-ID example, not the aggregate evidence.

Protocol/input hashes were frozen in `../deterministic_protocol.json` before execution. Computation was forecast at5–20 seconds CPU; actual4.788 seconds. Independent audit took9.389 seconds, separate from computation. No GPU was used.

## All budgets and both objectives

- Budget1: target greed is exact in200/200, as expected because its single-step search spans every feasible singleton. This is an implementation check, not evidence of a multistep theorem.
- Budget2: target radius/target optimum mean1.025156, median1.000,90th percentile1.069974, maximum1.601548;151/200 exact and49 suboptimal.
- Budget4, the frozen primary comparison: mean1.029687, median1.000,90th percentile1.092738, maximum1.623690;118/200 exact and82 suboptimal. A small average gap conceals substantial losses in a few instances.

At budget4, logdet greedy has target-radius ratio mean1.326554, median1.258243,90th percentile1.668269, maximum2.327697 and is target-optimal in1/200. Exhaustive logdet has target-radius ratio mean1.329217, maximum2.531905 and is target-optimal in2/200. Exhaustively solving the information objective does not make it the target objective.

The information tradeoff is explicit: mean information/optimal-information is .763916 for target greed, .792200 for exhaustive target-optimal design and .998884 for logdet greed. Target greed is not presented as an information-maximizing method.

All paired comparisons are retained in `paired_comparisons.csv`:

- Against logdet greedy, target greed is narrower/tied/wider in164/36/0 designs atB1,187/11/2 atB2 and196/2/2 atB4.
- The two adverseB4 cases have target-greedy radius up to1.026072 times the logdet-greedy radius. Hence even this within-archive comparison does not support pointwise dominance.
- Against exhaustive logdet atB4, the counts are196/3/1, with worst target-greedy/comparator radius1.025981. The frozen exhaustive target optimum remains the primary benchmark.

Exact-optimum counts use ratio<=1+1e-9; paired width ties use absolute radius difference<=1e-9. Slight ratios below1 at floating-point scale are preserved in raw data and represent numerical roundoff.

## Condition strata and adverse instance

The protocol froze strata using the maximum posterior condition number over **all feasible subsets at the same budget**, rather than selecting strata from target-greedy losses. AtB4:

- Kappa<25:15 designs, target-greedy mean ratio1.007132,90th percentile1.022832, maximum1.035329;10 exact.
- 25<=kappa<50:90 designs, mean1.015395,90th percentile1.053392, maximum1.142014;62 exact.
- 50<=kappa<100:74 designs, mean1.038699,90th percentile1.101839, maximum1.445544;37 exact.
- Kappa>=100:21 designs, mean1.075293,90th percentile1.168831, maximum1.623690;9 exact.

These are descriptive conditional summaries of fixed saved designs. They are not a causal test of anisotropy, an externally validated cutoff, or a greedy guarantee conditional on a stratum. All budget/stratum/method rows are in `summary.csv`. Prior-standardized target/candidate correlations are also saved in `method_results.csv` and `greedy_candidate_scores.csv`; no outcome-adaptive policy or new correlated-DGP stress was tested.

The worstB4 target-greedy instance is178, identified after looking at all200 and shown as an adverse diagnostic. Greedy sequence[3,8,9,2] reduces variance1.283282 -> .821267 -> .530046 -> .403644 -> .334827. Its radius1.134139 is1.623690 times exhaustive target radius .698495 from set[0,2,3,10]; its variance is2.636369 times optimal. Logdet greed gives radius1.569062. Greedy decisions are individually optimal for the next step but cannot revisit earlier choices to obtain the best four-element set.

In this instance target greed has posterior condition34.817, whereas the better target-optimal set has condition145.100. Lower overall condition number alone does not imply smaller variance in the specific target direction. The theorem's all-feasible-subset condition bound and the actual target objective are different diagnostics; neither these strata nor this example proves that target-direction performance is determined by condition number alone.

## Verification, artifacts and claim limits

`../check_deterministic.py` does not import the runner. It reconstructs posterior matrices by direct linear solves, independently enumerates unique lexicographic subsets, checks both exhaustive extrema, and checks greedy scores through objective differences rather than the runner's rank-one gain formulas. It verified all200 IDs,114,600 subsets,2,400 method rows,1,600 greedy steps,16,800 candidate scores and1,200 extrema. All600 archivedB4 greedy/logdet-optimum/target-optimum rows reproduce within the archived numerical precision. Original hashes match before/after, and all run output hashes pass.

Maximum absolute discrepancies are approximately1.1e-14 for covariances,1.6e-14 for rank-one/candidate target gains,2.7e-11 for subset condition numbers and4.9e-10 against rounded archived metrics. `independent_audit.json` contains exact values and tolerances. No scientific assumption is established by these checks.

Raw/provenance files: `input_designs.json`, `subset_scores.csv`, `method_results.csv`, `greedy_candidate_scores.csv`, `greedy_steps.csv`, `summary.csv`, `paired_comparisons.csv`, `run_manifest.json`, `independent_audit.json`; source scripts `../run_deterministic.py` and `../check_deterministic.py`; frozen `../deterministic_protocol.json`; complete hashes `../delivery_manifest.json`.

This supplements REV10/KoBT.W4 with a finite-budget global comparator and its adverse outcomes. It helps REV07 compare selection objectives and REV12 preserve design-level denominators. It does not establish a general target-greedy theorem, validate the U/L/H prospective-radius heuristic, demonstrate direct-PI submodularity, provide real mechanism calibration, compare to a direct trial, or justify nonlinear/outcome-adaptive acquisition. All12 reviewer concern statuses remain as recorded in `../REPORT.md`.
