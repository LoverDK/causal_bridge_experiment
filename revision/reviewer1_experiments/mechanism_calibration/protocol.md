# Frozen proposal: incremental joint calibration stress audit

Status: design only, awaiting root priority/go. No execution. Config v1 dated 2026-11-08. Primary concerns: WGDN.W2a/Q2 and KoBT.W1/Q1 (REV-04); secondary REV-11/12. Real external validity remains unresolved regardless of synthetic outcome.

## Question and experimental unit

Compare joint-max, entitywise marginal and entitywise Bonferroni calibration when menu size, dimension, dependence and descriptor reliability vary. A world is a newly generated calibration sample of independent complete archives plus one independent test archive. Each complete archive contains K historical sources, B eligible bridges and one target, M=K+B+1 entities. Every entity is included whether eventually selected or not. There are no causal outcomes, target effects, optimizers or bridge-selection policies in this audit.

In the baseline, each coordinate error is sqrt(rho)*A + sqrt(1-rho)*E with independent standard normal A per archive/coordinate and E per archive/entity/coordinate. Coordinates are independent. rho denotes within-archive entity correlation, not within-coordinate correlation or causal dependence. Use Euclidean norm in standardized coordinates and eta=.05. Redraw both calibration and test per world; thus world-unit confidence intervals integrate calibration-sample variability. Do not confuse these with the existing single-fitted-calibrator conditional test interval.

Missing descriptors: independently flag each entity-coordinate with probability `missing_cal` or `missing_test`, adding a standard normal error multiplied by 3 to its proxy error. This represents a frozen zero-imputation stress model with synthetic known reference truth, not a recommended real imputation. Unreliable descriptors: independently flag each entity-coordinate with probability `unreliable_cal/test`, adding standard normal error multiplied by 2. All flags are saved. `scale_test` multiplies final test errors. Matched calibration/test perturbations preserve archive exchangeability; test-only changes break it. No cell is tuned after observing results. Synthetic errors are explicit ground truth only within this generator.

## Calibration rules and finite ranks

Joint-max: s_a=max_j ||e_aj||; rank r=ceil((n_cal+1)*(1-eta)); q=s_(r), or positive infinity if r>n_cal. One q is applied to every entity in the frozen full menu. Validity requires exchangeability of complete archive scores, compatible menu and fixed dimension/map; arbitrary dependence within an archive is allowed.

Entitywise: for each fixed entity slot j, calibrate q_j at eta using independent archive rows. This provides marginal protection per slot under archive exchangeability, not simultaneous protection of all slots. It is the negative control for a joint claim. Do not flatten correlated entities and count them as n_cal*M independent calibration units.

Bonferroni: calibrate each fixed slot at eta/M using the same n_cal archive rows, again with positive infinity for ranks outside sample size. A union bound protects all M slots under marginal archive exchangeability; entity independence is unnecessary. At eta=.05 a finite threshold for every slot requires n_cal >=20M-1. At baseline M=11 and n_cal=199, all Bonferroni ranks are therefore infinite; report this honestly. B=0,M=5,ncal=199 admits a finite Bonferroni threshold, so the grid includes a useful finite comparison. Gaussian parametric union bounds in old outputs are not a substitute for this empirical rule.

Compute ranks with decimal/rational-safe arithmetic to avoid a floating-point ceil creating a spurious extra rank. Allow q=+infinity through scoring; infinity means an uninformative unbounded ball and must never be replaced by the largest finite score. Never put literal Infinity into strict JSON; use a separate infinity indicator and a null numeric value.

## Frozen grid and precision

Use all 26 explicitly listed config cells: baseline, one-factor changes and 11 declared interactions, not a full combinatorial sweep. Missing/unreliable rates distinguish matched degradation from test-only shift. Do not drop difficult cells or claim missingness is benign because a matching synthetic calibration law was stipulated.

Smoke uses 20 worlds per cell, seed 20261108021, only schema/rank/reproducibility checks. Full uses 2,000 worlds per cell, seed 20261108022. World-wise shared calibration/test errors pair all three rules within a cell. Cells have separately spawned random streams. Nominal .95 Bernoulli coverage has Monte Carlo standard error about .0049 at 2,000 independent worlds; intervals can easily overlap .95 and cannot establish exact coverage.

For every cell/rule report joint coverage (one boolean per test archive), entity coverage (mean hit fraction per archive), and source/bridge/target breakdown. Report individual entity-slot means as secondary diagnostics, using the same world denominator. Joint and fixed-slot Bernoulli intervals use Wilson 95% intervals; entity-average and source/bridge-average intervals use 2,000 world bootstrap resamples. Preserve entity correlation and paired methods within each resampled world. Report paired joint and entity-fraction differences with paired world bootstrap intervals. Intervals are descriptive pointwise MC intervals; no multiplicity-adjusted superiority claim. B=0 bridge coverage is undefined, not zero. Show finite-radius quantiles and infinity fraction separately; never average finite radii while concealing infinite cases.

## Evidence and validation

Save frozen config, runner source, dependencies, timestamps, actual commands, elapsed times and SHA-256 manifest. Save per-world calibration rank/radius, test entity norms/hits, perturbation counts and joint/fraction outcomes. Store full calibration entity norms in compressed numerical files for independent rank reconstruction, budget approximately 0.5–1.5 GB uncompressed across all cells; do not dump rows into chat. Store synthetic error generator seeds and flags for exact replay. Label raw generation, independent recomputation and summary separately.

Before full, independently recompute rank and hit summaries from saved smoke norms without importing calibration helpers. Required edge checks: n_cal=18 returns infinite joint/marginal; n_cal=19 joint rank=19; baseline empirical Bonferroni infinity; M=5,ncal=199 finite Bonferroni; positive within-archive correlation never increases independent calibration count; test-only shifts marked assumption-invalid; all-infinite outputs have coverage one and no information; B=0 breakdown undefined. Verify the joint event equals AND over every source, every bridge and target. Save one baseline world as a readable trace, not a selected favorable example.

Potential localized source issue found during read-only audit: `atlas_new/core.py:calibrated_quantile` already returns infinity correctly, but `atlas_new/mechanism_calibration.py:coverage` rejects nonfinite radii. The original mechanism-calibration audit with n_cal=199 never exercises that edge. Do not edit the external source tree. Any new runner must support infinity explicitly and record its implementation identity. This is a scope-specific helper limitation, not evidence that the existing full_plus infinity results are wrong.

## Runtime and execution gates

Initial unmeasured forecast: smoke 5–20 seconds; full 1–5 minutes generation/scoring plus 1–3 minutes compressed I/O and bootstrap reporting. Basis: tensor operation counts, tens to hundreds of millions of normal draws/norm evaluations, and no SLSQP; not a claim of measured throughput. CPU and compression/I/O are the bottlenecks, GPU unnecessary. Bound batches to 10–20 worlds; largest tensor at n_cal=199,M=29,p=8 remains small per batch. Before full revise the forecast using actual smoke generation bytes and seconds. Root must communicate its go and updated forecast; if forecast unexpectedly exceeds 10 minutes, send an updated scaling estimate before proceeding.

The external archive remains read-only. All outputs stay under this assigned directory. No real data fits, no invented labels, no changes to published archives/thresholds, no TeX or Git operations. After any approved milestone, review all 12 issues and retain REV-04/05 open; this audit supplies synthetic stress evidence only.
