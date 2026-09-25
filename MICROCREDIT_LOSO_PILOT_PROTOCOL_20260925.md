# Descriptive leave-one-study-out pilot: execution protocol

This file freezes the executable pilot before its held-out result table. It
inherits the estimand and eligibility rules in
`MICROCREDIT_INVITATION_ITT_PROTOCOL_20260925.md`.

## Input table

The executable input is a committed, non-sensitive study summary table with
one row per eligible study: `study_id`, `effect`, `se`, `reference_lo`,
`reference_hi`, seven design/context coordinates, and source locators. Effects
are extracted from the authorized local OpenICPSR archive only; raw observations
are not written to the repository. If a cluster-robust or design-based SE is
not reproducible, the row is retained as `variance_status=unresolved` and is
not used by the formal meta-analysis.

## Frozen methods

* `fixed_effect`: inverse-variance mean; predictive radius combines the
  weighted sampling SE and a 1.96 normal multiplier.
* `random_effects`: DerSimonian--Laird between-study variance plus a t-based
  predictive radius with `df = n_train - 2`; no bootstrap.
* `design_meta_regression`: OLS on the frozen design vector with an intercept,
  only if the training design matrix has full rank and at least four training
  rows; interval uses the fixed residual standard error and target leverage.
* `robust_training_range`: min/max training effect expanded by `1.96 * target
  se`; it is a range baseline, not a causal certificate.
* `atlas_descriptive`: inverse-distance design weighting with a fixed
  `radius = 1.96 * sqrt(sum(w_j^2 se_j^2)) + max_j |x_target-x_j|` and no
  independent mechanism calibration. It is deliberately labelled descriptive.

All methods receive the same training effects, training SEs and target design
vector. Target effect, target SE, and target-derived values are read only after
the prediction and release decision are serialized. Release is `width/2 <=
delta`, with `delta` in `{0.10, 0.20, 0.40, 0.80}`; the primary table uses
`delta=0.20`.

## Noisy-reference categories and metrics

The reference interval is `effect +/- 1.96*se`. For each held-out row and
method report estimate, lower/upper, width, release/refusal, training count,
absolute point error, and `contains_full`, `disjoint`, or `partial_overlap`.
Aggregate only by exact counts: release rate, mean width, point-error mean,
sign disagreement, and the three reference categories. Do not call any count
coverage or calibration guarantee.

## Leakage audit

After predictions and decisions are saved, rerun each held-out split with its
target effect replaced by its sign-flipped value and by a deterministic
permutation of the target-only reference fields. The training table and target
design vector are unchanged. Require identical prediction, interval, width,
and release columns. Any difference is a failed leakage test.
