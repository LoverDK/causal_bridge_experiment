# SELECTION-SAFE-COMPARISON01 — frozen before simulation

Prepared 2026-11-08. No experiment is to execute until the root agent has written its priority report and authorized execution. Source experiment-rebuild is read only; this folder is the sole write destination. No TeX or Git changes.

Question: what reliability/width/release tradeoff protects genuinely outcome-dependent source weighting, compared with design-only pooling and honest sample splitting? Primary reviewer links: WGDN.W1a/Q1, REV-02/07; attribution and statistical semantics REV-03/11/12. This is a finite-sample synthetic selection audit, not bridge acquisition and not evidence that selecting extreme source effects improves target estimation.

## Unit, inputs, frozen grid

One unit is an independently simulated archive and target world; all policies, strengths, and thresholds reuse that world. 72 cells = geometry (3) × precision (2) × surface (3) × K (2) × ambiguity (2), with 5,000 independent worlds per full cell. Strength rho=.2/1 and delta=.15/.30/.60 are repeated evaluations, not extra independent worlds. Smoke uses 50 worlds/cell and a distinct seed. Config fixes seeds before results are seen.

Source center layouts: balanced_near evenly spans [-.12,.12]; one_distant has first center .75, other centers evenly span [-.10,.10]; distant_only evenly spans [.55,.85]. Target center is zero. Equal source full-mean SD=.10. Heterogeneous SD spans [.06,.14], except first source is .025 for one_distant, so a highly precise distant study competes with moderately precise close studies. The precision×geometry factorial retains the corresponding equal-precision control.

True source positions are independently uniform in [center-u,center+u]; true target position is uniform [-u,u]. Known compact sets always contain these positions; no calibration failure is simulated (eta=0). Domain [-1,1]. Source response surface is flat f=0 (L=H=0), linear f=.3x (L=.3,H=0), or curved f=.3x+.4x² (L=1.1,H=.8). These are declared oracle smoothness constants from the generator, not realistic calibrated inputs.

Two independent source half-estimates have mean f(x_i) and SD sqrt(2)s_i. Their average is the shared full estimate, with SD s_i. All policies share both halves and actual total source sample resources. The split policy uses first half for selection and second half for evaluation, and cannot reuse first-half evaluation noise.

## Geometry and certificates

Use the valid convex Taylor upper bound, with target center 0:

 B(a)=L(|sum_i a_i c_i|+2u)+(H/2)sum_i a_i(|c_i|+2u)^2.

Taylor-expand each source around the actual target: the derivative term is at most L|sum a_i x_i-x*| and remainder at most (H/2)sum a_i(x_i-x*)². Triangle inequalities over the compact sets give B. This is a conservative outer certificate, not exact original B_U, not the sharp Lipschitz region, and not a real-data calibration claim.

Set q=sqrt(2log(2/alpha)), qK=sqrt(2log(2K/alpha)). R2=B+q||a*s||2; Rinf=B+qK sum a_i s_i. Both use alpha=.05, known independent Gaussian noise, zero nuisance bias, one evaluation look. Honest split uses sqrt(2)s in R2. Every refusal still returns the same computed certificate interval [estimate-radius,estimate+radius], explicitly not a separate sharp refusal region. All inputs qualify synthetically.

Design-only a0 globally minimizes this convex R2 objective; SLSQP provides a primal point and an independent feasible dual supporting lower bound certifies its gap at <=2e-6. Failure aborts without replacing configurations. For fixed a, R2<=Rinf; globally min_a R2<=R2(a(Y))<=Rinf(a(Y)). Thus this experiment cannot demonstrate an Rinf release when the global design optimum refuses under the same geometry/noise/budget. Report zero expected impossible discordances and numerical tolerance, and separately compare Rinf to prespecified uniform/IV alternatives. No local-optimum reversal can be sold as selection safety.

## Six policies and information timing

1. outcome_adaptive_Rinf: j=argmax_i |Y_i|/s_i; a=(1-rho)a0+rho e_j, evaluate full Y, valid simultaneous radius.
2. design_only_optimized_R2: a0 depends on centers/sets/L/H/s, evaluate full Y.
3. honest_half_split_R2: same selection rule from half1 using its SD, same mixture with a0, evaluate half2 only; valid conditional-on-half1 pointwise radius with sqrt(2)s.
4. naive_postselection_R2: exactly policy 1 weights and full Y, but invalid reused pointwise R2. Explicit negative control; no theorem guarantee.
5. uniform_R2: fixed 1/K full Y.
6. inverse_variance_R2: fixed normalized s^-2 full Y.

Selection screens large standardized empirical source effects; it never receives source true effects, true positions, target true effects, or target observations. Those are supplied only to the generator/scorer. A flip test changes scorer target truth while holding policy inputs fixed and requires identical weights/estimates/radii/releases; changing evaluation half2 must not change split selection. Changing source data must leave a0 unchanged. No target trial is run.

## Metrics and uncertainty

For each cell/rho/policy/delta: coverage, average width and its world-level MC SE, release and refusal rates, bad-release probability P(release & |error|>delta), selective risk P(|error|>delta | release), all-world MAE, released-world MAE, conditional coverage given release. Rates get 95% Wilson MC intervals; zero-release conditional metrics are null/undefined. Conditional coverage has no theorem guarantee. Paired differences use within-world contrasts, MC SE and normal 95% descriptive intervals. These are individual Monte Carlo intervals, not multiplicity-adjusted scientific tests. Widths include refused worlds. Save point error and radius separately. Timing measures common optimizer, policy arithmetic and total wall clock; no claim of operational deployment cost.

Expected falsifiable pattern: naive coverage can fail strongly on flat strong-selection K=16; simultaneous and honest split retain nominal unconditional validity, with width penalties; optimized design can dominate radius/release and often MAE. Rinf may beat simple fixed alternatives in some geometries, without beating the global design optimum. Flat/null, unfavorable or no-discordance cells stay in the report.

## Verification and artifacts

Before full: deterministic formula checks, dual gaps, source/target isolation flip tests, sample-split independence checks, then smoke with throughput-based full forecast. Save config/protocol, run command, dependency versions, code/input hashes, per-cell npz raw halves/true positions/selection indices/estimates/radii, full summary and paired CSV, raw independent recomputation audit, and manifest. Raw aggregate check is a separately written reconstruction from saved half data, design weights and selection index. No existing original output is overwritten.

Initial runtime forecast: smoke 5–20s, full 30–120s, based on 72 small convex optimizations plus vectorized arithmetic and raw npz compression; one CPU process and I/O, no GPU. Update from measured smoke; long tasks require a resource choice opportunity. No simulation has yet run at freeze.

## All-review check before and after

REV-01 adds one inspectable synthetic world; author comprehension remains unverified. REV-02 directly adds outcome-dependent and honest split audit, with negative comparisons preserved. REV-03 numeric attribution kept method-specific; no abstract edits. REV-04 oracle sets/L/H only; real calibration remains open. REV-05 no real certificate; real closure unchanged. REV-06 no Many Labs or target-noise work. REV-07 six paired policies and split cost, not ExAtlas/direct trials or real total cost. REV-08 no novelty/closest-work closure. REV-09 simplex retained, no estimator-class optimality. REV-10 no bridge policy or new non-Gaussian evidence. REV-11 new code/config/raw hashes; no global naming closure. REV-12 conditional and joint risks, refusal and zero denominators explicit; no real validity/sharp-region closure. All inherited issue statuses remain unchanged; none becomes resolved from execution.
