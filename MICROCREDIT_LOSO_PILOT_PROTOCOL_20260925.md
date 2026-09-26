# Descriptive leave-one-study-out pilot: execution protocol

This file defines the executable pilot. The source-correction amendment below
was made after historical results and published source cells had been seen. It
is not a preregistration. It inherits the estimand and eligibility rules in
`MICROCREDIT_INVITATION_ITT_PROTOCOL_20260925.md`.

## Input table

The accepted source specification is `data/microcredit_published_sources_v1.json`.
`tools/build_microcredit_published_inputs.py` deterministically converts the
explicitly selected published rounded cells. Its versioned outputs are
`data/microcredit_published_v1/primary.csv` (Mexico and India endline 1) and
`data/microcredit_published_v1/population_sensitivity.csv` (these two plus
Morocco's all-sample weighted estimate). `reference_lower` and `reference_upper`
are computed only after predictions are saved. Raw observations are not
written to the repository. The old `data/microcredit_loso_pilot_input.csv` and
`results/microcredit_loso_pilot/` are historical candidates, not this run.

### Source-correction amendment, 2026-09-25

The published Mexico Table 3 cell is 0 (SE 39), N=16005, with SE clustered by
238 randomized geographic clusters. India Table 3A endline-1 profit is
354 (SE 314), N=6239, with weighted area-clustered inference. These published
summaries replace the mixed reconstructed/summary candidate. They do not claim
native Stata reproduction. Exact table locators and PDF hashes are in the
source specification.

Morocco's previously selected 2005 (SE 1210), N=4934, describes the
high-propensity-to-borrow stratum and is excluded from the primary run. A
separate **post-hoc population sensitivity** uses Table 8B, profit -476
(SE 1252), N=5524: inverse sampling weights, paired-village strata,
village-clustered SE, and published 0.5 percent trimming. This cell was chosen
because it targets the selected-village population. Both its value and the
historical results were already visible; it is not an outcome-blind selection.
Primary and sensitivity results must be reported separately, regardless of
signs or decisions. No alternative threshold or source cell is selected by fit.

`verified_common_estimand` is an implementation token for the operational
community-access/profit stratum only; it does not establish identical profit
constructs, populations, horizons, or causal effects. Separate assignment,
outcome, stratum and population statuses and source locators are required.
Variance-based methods also require a published assignment-clustered SE.
All design coordinates retain exploratory status: in particular, the timing
and planned-versus-realized meaning of `loansize_percentincome` (renamed
`loan_share` in the old runner) are not verified. ATLAS and design regression
must remain `not_qualified` in both inputs. Two human outcome-blind coders
have not completed adjudication. The source audit is not a substitute.

The runner additionally refuses a one-point training range: at least two
training studies are needed for `robust_training_range`. This post-hoc
small-sample safeguard prevents a zero-width range from being reported as
identified with only one training study.

## Frozen methods

* `fixed_effect`: inverse-variance mean; radius uses only the weighted
  training-study sampling uncertainty and the normal 0.975 quantile
  (1.9599639845). It omits between-study uncertainty and is a descriptive
  sampling-only baseline, not a validated transport prediction interval.
* `random_effects`: DerSimonian--Laird between-study variance plus a t-based
  predictive radius with `df = n_train - 2`; no bootstrap. The held-out
  study's result SE is excluded from prediction.
* `design_meta_regression`: OLS on the frozen design vector with an intercept,
  only if the training design matrix has full rank and at least
  `max(4, number_of_columns + 1)` training rows; interval uses the residual
  standard error and target leverage.
* `robust_training_range`: the min/max training effect range with at least
  two training studies; it is a range
  baseline, not a causal certificate. The held-out study's result SE is
  excluded from the range and release decision.
* `atlas_descriptive`: inverse-distance design weighting with a fixed
  `radius = 1.96 * sqrt(sum(w_j^2 se_j^2)) + max_j |x_target-x_j|` and no
  independent mechanism calibration. It is deliberately labelled descriptive.

Eligible methods receive the same training effects, training SEs and target
design vector. Source qualification is checked before prediction; numerical
target effect and SE are not passed to the prediction routine. Scoring reads
them after predictions and decisions are serialized and reopened. Release is `width/2 <=
delta`, with `delta` in `{0.10, 0.20, 0.40, 0.80}`; the primary table uses
`delta=0.20`.

## Noisy-reference categories and metrics

The reference interval is `effect +/- 1.96*se`. For each held-out row and
method report estimate, lower/upper, width, release/refusal, training count,
absolute point error, sign error, released-target error beyond `delta`, and
`contains_full`, `disjoint`, or `partial_overlap`. Aggregate only by exact
counts: release rate, mean width, point-error mean, sign errors, released-target
risk conditional on release, and the three reference categories. Do not call
any count coverage or calibration guarantee.

## Leakage audit

After predictions and decisions are saved, rerun each held-out split with its
target effect sign-flipped (a nonzero sentinel when the effect equals zero)
and its result SE changed while leaving the target
design vector fixed. The training table and target design vector are unchanged.
Require identical prediction, interval, width, and release columns. Any
difference is a failed leakage test. The executable audit stores separate
`predictions_unchanged`, `width_unchanged`, and `release_unchanged` fields.
The audit is conditional on fixed source qualification and design coordinates.
It verifies numerical target-effect/SE non-use; it does not verify the
coordinates' outcome-blind provenance. Undefined released-target risk is
serialized as an empty CSV value when no target is released.
