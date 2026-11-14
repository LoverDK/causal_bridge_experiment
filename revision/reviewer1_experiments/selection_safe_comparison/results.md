# Selection-safe finite-sample comparison

Executed 360,000 independent synthetic worlds: 72 prespecified cells ×5,000, six methods, two paired selection strengths and three thresholds. Full runner 5.19s; independent raw-data reconstruction 10.97s. All results and unfavorable cells retained.

**Scope first.** This tests finite-sample validity after empirical-effect screening. It does not establish that adaptive screening is a useful transport policy, that adaptation improves efficiency, or that real mechanism sets/smoothness can be calibrated. It uses known Gaussian source noise, always-containing synthetic mechanism sets and declared oracle L/H. The convex Taylor geometry is a conservative outer certificate rather than exact original barycentric geometry or a sharp refusal region.

**Design-only radius dominance is mathematical.** At identical inputs/budgets, min R2 ≤ R2(a(Y)) ≤ Rinf(a(Y)). The convex optimization dual certificate brackets the global optimum; saved feasible weights are within the reported tolerance, rather than an exact symbolic optimizer. No Rinf-vs-global-design release reversal can be interpreted as a possible benefit. Observed impossible reversals: 0. Maximum primal/dual gap 3.14e-07.

## Prespecified null check

Balanced-near, equal precision, flat surface, K=16, zero ambiguity (cell 2), strong selection rho=1. This isolates reused-noise selection without transport error. Intervals below are individual 95% Monte Carlo Wilson intervals; widths are full certificate widths, including refused worlds.
- outcome_adaptive_Rinf: coverage 99.40% [99.14%, 99.58%]; mean width 0.7190; release at delta=.30 0.00% [0.00%, 0.08%]; all-world MAE 0.2083; released-world MAE undefined.
- design_only_optimized_R2: coverage 99.44% [99.19%, 99.61%]; mean width 0.1358; release at delta=.30 100.00% [99.92%, 100.00%]; all-world MAE 0.0200; released-world MAE 0.0200.
- honest_half_split_R2: coverage 99.50% [99.26%, 99.66%]; mean width 0.7683; release at delta=.30 0.00% [0.00%, 0.08%]; all-world MAE 0.1130; released-world MAE undefined.
- naive_postselection_R2: coverage 89.56% [88.68%, 90.38%]; mean width 0.5432; release at delta=.30 100.00% [99.92%, 100.00%]; all-world MAE 0.2083; released-world MAE 0.2083.
- uniform_R2: coverage 99.44% [99.19%, 99.61%]; mean width 0.1358; release at delta=.30 100.00% [99.92%, 100.00%]; all-world MAE 0.0200; released-world MAE 0.0200.
- inverse_variance_R2: coverage 99.44% [99.19%, 99.61%]; mean width 0.1358; release at delta=.30 100.00% [99.92%, 100.00%]; all-world MAE 0.0200; released-world MAE 0.0200.

Exact null coverages from the Gaussian maximum distribution: reused sub-Gaussian pointwise radius 0.899418, simultaneous radius 0.994819. The empirical check uses no fitted or target-tuned thresholds.

## Full grid and paired tradeoffs

The complete cell/rho/method/threshold results are in `full/summary.csv`; `full/paired.csv` contains world-paired differences, MC standard errors, individual normal 95% intervals and both directions of release discordance. `paired_discordance.csv` gives cell-level Wilson 95% intervals for each discordance direction. No denominator treats repeated thresholds, methods or strengths as new worlds. Zero-release conditional metrics are empty/undefined. Conditional coverage and selective risk have empirical denominators and no nominal conditional theorem guarantee.

At rho=0.2, ranges over the 72 cells at delta=.30 (ranges are descriptive, not pooled coverage estimates):
- outcome_adaptive_Rinf: coverage 100.00–100.00%; release 0.00–100.00%; all-world MAE 0.0370–0.3754.
- design_only_optimized_R2: coverage 99.06–100.00%; release 0.00–100.00%; all-world MAE 0.0141–0.3099.
- honest_half_split_R2: coverage 99.18–100.00%; release 0.00–100.00%; all-world MAE 0.0300–0.3448.
- naive_postselection_R2: coverage 92.46–100.00%; release 0.00–100.00%; all-world MAE 0.0370–0.3754.
- uniform_R2: coverage 99.06–100.00%; release 0.00–100.00%; all-world MAE 0.0196–0.4113.
- inverse_variance_R2: coverage 99.06–100.00%; release 0.00–100.00%; all-world MAE 0.0141–0.4109.

At rho=1, ranges over the 72 cells at delta=.30 (ranges are descriptive, not pooled coverage estimates):
- outcome_adaptive_Rinf: coverage 99.36–100.00%; release 0.00–53.86%; all-world MAE 0.1318–0.6377.
- design_only_optimized_R2: coverage 99.06–100.00%; release 0.00–100.00%; all-world MAE 0.0141–0.3099.
- honest_half_split_R2: coverage 99.14–100.00%; release 0.00–28.40%; all-world MAE 0.1010–0.4880.
- naive_postselection_R2: coverage 89.38–100.00%; release 0.00–100.00%; all-world MAE 0.1318–0.6377.
- uniform_R2: coverage 99.06–100.00%; release 0.00–100.00%; all-world MAE 0.0196–0.4113.
- inverse_variance_R2: coverage 99.06–100.00%; release 0.00–100.00%; all-world MAE 0.0141–0.4109.

Release discordances summed over all prespecified cell/strength/threshold evaluations (these are overlapping decisions, not independent worlds):
- Rinf releases / design_only_optimized_R2 refuses: 0; reverse direction: 1,020,749.
- Rinf releases / honest_half_split_R2 refuses: 48,176; reverse direction: 331,870.
- Rinf releases / naive_postselection_R2 refuses: 0; reverse direction: 510,060.
- Rinf releases / uniform_R2 refuses: 0; reverse direction: 950,749.
- Rinf releases / inverse_variance_R2 refuses: 15,000; reverse direction: 875,749.

The Rinf-over-inverse-variance discordances occur only in the weak mixture (80% optimized design weights) on one-distant/heterogeneous/curved cells 44, 45 and 47 at delta=.60. This is compatible with a benefit of avoiding a geometry-blind precise distant source; it is not evidence that outcome adaptation itself improves efficiency. Uniform and optimized design weights have no reverse-release losses against Rinf in this grid.

## Prespecified geometry examples

Cells 23, 41, 47, 71 were selected by their design descriptions before full results; all other cells remain in the CSV. These examples are explanatory, not a winning subset.

Cell 23: balanced_near, heterogeneous, curved, K=16, u=0.025, strong selection, delta=.30.
- outcome_adaptive_Rinf: coverage 99.96% [99.85%, 99.99%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 0.9787, all-world MAE 0.2119.
- design_only_optimized_R2: coverage 100.00% [99.92%, 100.00%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 100.00% [99.92%, 100.00%], width 0.2605, all-world MAE 0.0211.
- honest_half_split_R2: coverage 99.90% [99.77%, 99.96%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 1.0265, all-world MAE 0.1135.
- naive_postselection_R2: coverage 99.60% [99.38%, 99.74%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 0.8051, all-world MAE 0.2119.
- uniform_R2: coverage 100.00% [99.92%, 100.00%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 100.00% [99.92%, 100.00%], width 0.2613, all-world MAE 0.0211.
- inverse_variance_R2: coverage 100.00% [99.92%, 100.00%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 100.00% [99.92%, 100.00%], width 0.3283, all-world MAE 0.0200.

Cell 41: one_distant, heterogeneous, linear, K=4, u=0.025, strong selection, delta=.30.
- outcome_adaptive_Rinf: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 0.6393, all-world MAE 0.2244.
- design_only_optimized_R2: coverage 99.70% [99.51%, 99.82%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 99.70% [99.51%, 99.82%], width 0.3506, all-world MAE 0.0476.
- honest_half_split_R2: coverage 99.96% [99.85%, 99.99%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 0.6721, all-world MAE 0.2236.
- naive_postselection_R2: coverage 99.98% [99.89%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 0.6158, all-world MAE 0.2244.
- uniform_R2: coverage 99.82% [99.66%, 99.91%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 99.82% [99.66%, 99.91%], width 0.4161, all-world MAE 0.0631.
- inverse_variance_R2: coverage 99.98% [99.89%, 100.00%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 99.98% [99.89%, 100.00%], width 0.5399, all-world MAE 0.1915.

Cell 47: one_distant, heterogeneous, curved, K=16, u=0.025, strong selection, delta=.30.
- outcome_adaptive_Rinf: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.4517, all-world MAE 0.4503.
- design_only_optimized_R2: coverage 100.00% [99.92%, 100.00%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 100.00% [99.92%, 100.00%], width 0.2629, all-world MAE 0.0204.
- honest_half_split_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.4641, all-world MAE 0.4495.
- naive_postselection_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.4078, all-world MAE 0.4503.
- uniform_R2: coverage 100.00% [99.92%, 100.00%], release 100.00% [99.92%, 100.00%], selective risk 0.00% [0.00%, 0.08%], conditional coverage 100.00% [99.92%, 100.00%], width 0.3925, all-world MAE 0.0322.
- inverse_variance_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 1.2338, all-world MAE 0.2160.

Cell 71: distant_only, heterogeneous, curved, K=16, u=0.025, strong selection, delta=.30.
- outcome_adaptive_Rinf: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.5690, all-world MAE 0.5213.
- design_only_optimized_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 1.8595, all-world MAE 0.2987.
- honest_half_split_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.6985, all-world MAE 0.3836.
- naive_postselection_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.4161, all-world MAE 0.5213.
- uniform_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.2467, all-world MAE 0.4095.
- inverse_variance_R2: coverage 100.00% [99.92%, 100.00%], release 0.00% [0.00%, 0.08%], selective risk undefined, conditional coverage undefined, width 2.0708, all-world MAE 0.3696.

## Audit and limits

Independent verifier reconstructed 2,592 complete summary rows plus all paired differences from NPZ half-sample means, source/target locations, fixed weights and selection indices. Maximum estimate/radius discrepancy 4.44e-16; maximum geometry-bound excess 2.78e-17 (floating point). Source-halves SD is sqrt(2) times the full SD. Target-truth flips cannot enter policies, and changing evaluation half2 cannot change honest-half selection. Design weights have no outcome argument.

Common source resources are identical; splitting pays by discarding the selection half from evaluation. This is not a comparison to additional independent data at zero cost. No target outcome/truth informs selection. All synthetic inputs qualify, so refusal means radius exceeds tolerance, and every refusal still returns its computed outer certificate interval. No sharp-region calculation, bridge acquisition, real calibration or operational deployment cost is evaluated.

The independent checker is a separate implementation written by the same agent; root review of formulas/aggregates remains a distinct oversight step. Individual Monte Carlo intervals have no familywise guarantee. Numerical validity checks do not prove scientific usefulness.

## Numerical timing

The shared 72 convex-design optimizations took 0.1256s total (maximum per cell 0.0050s). A separate three-repeat timing audit reloaded the fixed raw inputs in 0.518s and recomputed each method independently over 720,000 world-strength evaluations per repetition. These are arithmetic timings; optimizer/setup, raw loading, scoring, NPZ compression and I/O are distinguished from policy arithmetic. They are not deployment cost estimates.
- outcome_adaptive_Rinf: median 0.0706s, range 0.0698–0.0735s; 0.098 microseconds per world-strength evaluation.
- design_only_optimized_R2: median 0.0408s, range 0.0400–0.0425s; 0.057 microseconds per world-strength evaluation.
- honest_half_split_R2: median 0.0767s, range 0.0734–0.0784s; 0.107 microseconds per world-strength evaluation.
- naive_postselection_R2: median 0.0745s, range 0.0742–0.0749s; 0.103 microseconds per world-strength evaluation.
- uniform_R2: median 0.0389s, range 0.0387–0.0434s; 0.054 microseconds per world-strength evaluation.
- inverse_variance_R2: median 0.0387s, range 0.0371–0.0435s; 0.054 microseconds per world-strength evaluation.

## Review follow-up

REV-01: saved one-world explanation; author understanding remains unverified. REV-02/07: adds paired outcome-dependent, legal split, optimized and simple-design comparisons, explicitly retaining design dominance and adverse adaptive errors. REV-03/11: method, bound, seed, code/config/raw hashes recorded; no TeX, abstract or global naming changes. REV-04/05: synthetic oracle sets and L/H only, no real calibration/certificate. REV-06: no Many Labs evidence. REV-08: no novelty or closest-work resolution. REV-09: restricted simplex class, no broad optimality. REV-10: no bridge/non-Gaussian extension. REV-12: joint/conditional errors and zero denominators separated; no sharp-region claim. All 12 prior statuses retained; none resolved.

Reproduce in a fresh copy of the code/config files: `python run.py --profile smoke`, `python verify.py smoke`, then after full authorization `python run.py --profile full`, `python verify.py full`, `python timing.py`, `python report.py`, `python audit_intervals.py`, `python report.py`. Existing run directories are protected against overwrite. Frozen configurations and raw per-cell NPZ files permit complete recomputation.
