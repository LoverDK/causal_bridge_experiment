# Requirements for the real cross-intervention study

This checklist defines the minimum material needed before running a real
cross-intervention mechanism-set, independent calibration, and causal-reference
audit. The goal is to make the split and evidence boundary reviewable before
any target outcome is inspected.

## 1. Independent intervention archive

- At least three independent randomized interventions or trials are needed;
  five or more is preferable for a meaningful leave-one-intervention-out
  evaluation. Repeated subgroups or sites from one intervention do not count
  as independent interventions.
- For every intervention, provide a stable ID, study/trial ID, intervention
  description, control condition, population, recruitment frame, follow-up
  window, exposure rule, treatment uptake, implementation details, and the
  version of the protocol.
- Provide the unit-level data when permitted, or an audited effect summary with
  the estimate, standard error or covariance, sample sizes, randomization
  details, and nuisance-bias envelope. The estimand must be on one declared
  scale after harmonization.

## 2. Outcome-blind mechanism proxies

For each source intervention and the held-out target, provide proxies that are
available before target outcomes are read. Useful fields include treatment
components, dose or intensity, delivery channel, exposure and take-up,
control services, timing, implementation fidelity, measured moderators, and
the prespecified population descriptors. Each field needs a data dictionary,
units, missingness rule, measurement date, and provenance.

The proxy map must be frozen before scoring. We need a declared
`Gamma(Z) -> U`, distance or score, coordinate scaling, and the sensitivity
values for `L`, `H`, and `eta`. Outcome-derived embeddings, target-effect
labels, or post-hoc feature selection cannot enter this map.

## 3. Independent real calibration archive

- Supply separate intervention records or an external measurement archive that
  is not used as a target and is not reused as a source in the final score.
- Freeze the calibration/validation split, the calibration unit, the joint
  score, the order statistic or other calibration rule, and the candidate
  universe before target outcomes are opened.
- Record which participants, studies, or intervention records belong to each
  split. Include negative controls or repeat measurements when they are part of
  the measurement audit.
- The archive must support a joint event over all source sets, bridge sets, and
  the target. Marginal coverage of individual sets is insufficient for the
  certificate used in this paper.

## 4. Causal reference for the target

The strongest real audit has an independently randomized target intervention
with the same declared estimand, its raw outcomes, the randomization scheme,
and a prespecified analysis. Provide the target effect estimate and sampling
uncertainty only after the transport prediction and release decision are
frozen.

Literal noise-free individual causal truth requires both potential outcomes
for the target units, which ordinary real trials do not observe. If those
potential outcomes are unavailable, a randomized target estimate with its
uncertainty supports a real reference audit, not exact causal-truth coverage.
Frozen response surfaces on real covariates remain useful as a semisynthetic
truth audit and must be labelled that way, as in the NSW extension.

## 5. Files and governance

Please provide the raw files or an access path, variable dictionaries, codebook,
license or data-use permission, source URLs and version/commit IDs, SHA-256
hashes, and any de-identification or weighting rules. Also provide the exact
freeze date and the pre-outcome split manifest. If individual-level data cannot
be shared, a reproducible container or an audited summary package is required.

## What can start immediately

With the materials above, the next run will first validate hashes and estimand
compatibility, construct and freeze the mechanism sets, calibrate on the
independent archive, and only then open target outcomes for the held-out
causal-reference audit. The current NSW files alone cannot satisfy the
independent cross-intervention requirement because they contain one
job-training intervention and no observed individual potential outcomes.
