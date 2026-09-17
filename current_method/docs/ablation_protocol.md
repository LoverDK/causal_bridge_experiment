# Matched-certificate weight and geometry ablations

Protocol fixed before the new runs on 2026-09-17. These are post-review analyses of
the existing synthetic DGP, not newly preregistered independent confirmation.
No ExAtlas replication is included.

Use the exact workflow_full seeds, 200 replicates per surface/scenario, three
surfaces, three support geometries, 199 calibration archives, four initial
sources, six candidates, three acquisitions, 96 participants per acquisition,
and tolerances 0.2 and 0.3. This yields 1,800 independent worlds. All comparisons
share each world's calibration, proxy noise and source-specific trial streams.

To isolate weights, freeze a common random or nearest-proxy acquisition order
before evaluating any outcomes. Recompute weights on each shared source prefix.
This does not compare separately retargeted acquisition policies. Random and
nearest schedules are both reported, including supported/unreachable cases.

Experiment 1: optimized, uniform, inverse-noise-variance, and nearest-proxy-source
weights, all with min(Bbar, BLip). Run separately for R2 and R-infinity with the
original finite-horizon multipliers. All weights are design-only, including
inverse variance (known DGP scales), so both certificates are valid per policy.
Nearest-source ties use the earliest source in the shared prefix.

Experiment 2: optimize using Bbar alone, BLip alone, or their minimum. Keep source
prefixes and stochastic penalties identical. Report both reoptimized results and
all three radii at exactly the same minimum-objective weights to distinguish a
tighter envelope from a change in fitted weights. Bbar bounds the original G;
BLip bounds causal error directly and need not bound G. No global optimum claim.
SLSQP settings and fallbacks match the existing workflow implementation.

Primary reporting: all methods at each fixed acquisition budget, plus paths that
stop at first radius <= tolerance. Stopped cost counts actual acquisitions, and
outputs are carried after release. Fixed-budget counterfactual source outcomes
are scored separately and never enter planning. Fixed-budget width is twice the
release certificate; stopped output width includes the refusal outer region.
Report release, unconditional bad release, path coverage, certificate coverage,
all-target and released MAE, width, and actual participants. Conditional MAE for
zero releases remains missing. Uniform/IVW may worsen on adding noisy sources;
do not silently replace them by a best historical solution.

Paired differences: optimized minimum minus each comparator, pairing by world
within each surface/scenario. Pool surfaces equally and bootstrap whole worlds
within surface strata (2,000 draws, seed 2026091702). CIs are exploratory individual
95% intervals, not a multiple-comparison superiority claim. Calibration checks
use one-sided binomial tests against the per-policy 0.10 path failure budget,
with familywise 0.01 across reported cells. Non-rejection is not a proof.

Run smoke first for implementation verification, then full once. Refuse existing
output directories. Preserve source hashes, configuration, saved plans, all
policy states, summaries and negative results. Original results and manuscript
remain untouched.
