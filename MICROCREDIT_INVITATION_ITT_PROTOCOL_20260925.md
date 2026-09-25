# Frozen invitation-ITT protocol for the seven-study pilot

Status: frozen before the LOSO result table was opened, 2026-09-25. This is a
descriptive pilot protocol, not a preregistered 95% calibration experiment.

## Primary estimand

For an eligible community or village population in study `i`, the primary
contrast is the intention-to-treat effect

`tau_i = E[Y_i(assignment=offer/access) - Y_i(assignment=declared usual-service control)]`.

The primary pilot outcome is **self-employment/business profit**, represented by
the study's prespecified profit variable and transformed to USD PPP per
fortnight using the conversion and period factors already recorded in
`data/import_organise_data_v7.R`, lines 746--753. This choice is an operational
pilot target and does not claim that the underlying profit constructs are
identical. Household consumption, income, labor, credit, and business outcomes
are separate estimands and are not pooled with profit.

The unit is the randomization unit for the assignment contrast (village,
community, neighborhood, or PA), with participant/household outcomes aggregated
or analyzed using the study's original assignment-level inference. The target
population is the population eligible for that study's offer/access program,
not actual borrowers. Applicant-level loan approvals are a separate stratum.

## Eligibility and exclusion

An intervention enters the **community access stratum** only if all of the
following are verified from design sources before target outcomes are used:

1. assignment is randomized at village/community/neighborhood/PA level;
2. treatment is an offer, eligibility, promotion, or service availability
   intervention, not actual borrowing or treatment-on-the-treated;
3. the control condition is explicitly documented and its contemporaneous
   access to other credit is recorded as a design coordinate;
4. endline profit has a documented recall period and a deterministic conversion
   to the frozen USD PPP per-fortnight scale;
5. the assignment variable, cluster/pair identifier, outcome variable, and an
   assignment-level standard error or reproducible variance calculation are
   available.

The initial candidate list is Angelucci/Mexico, Attanasio/Mongolia,
Banerjee/India, Crépon/Morocco, and Tarozzi/Ethiopia. Attanasio contributes
one arm-specific contrast only; Tarozzi contributes MF-vs-None only; Banerjee
contributes endline 1 only. Augsburg/Bosnia and Karlan--Zinman/Philippines are
applicant-level offer/approval designs and are excluded from the pooled
community stratum. A candidate is removed if any eligibility fact remains
unresolved after the evidence audit. The result can therefore be an empty or
small compatible set; that is a finding, not a reason to relax the estimand.

## Mechanism and information boundary

The target prediction may use only the frozen design record: randomization unit,
product (group/individual), planned APR/loan size/term, eligibility/targeting,
promotion/delivery channel, baseline credit context, control access, sampling
frame, follow-up horizon, and documented implementation fidelity. Post-treatment
take-up, realized borrowing, repayment, endline outcomes, effect estimates, and
outcome-derived feature selection are forbidden. The seven-study pilot uses a
transparent design vector and does not claim that it is a calibrated real
mechanism set `U_i`.

## Split and prediction rules

The split unit is the entire independent study, never participants within a
study. For each held-out study, all other eligible studies are training
studies. No independent mechanism calibration archive exists; therefore ATLAS
is run only as a descriptive design-vector interval with a fixed conservative
radius rule and is labelled uncalibrated. The release tolerance is frozen at
`delta = 0.20` USD PPP per fortnight for the primary table, with a full curve
at `0.10, 0.20, 0.40, 0.80`.

Baselines use the same held-out study, same training set, and same outcome
information boundary: fixed-effect inverse-variance meta-analysis, random-
effects DerSimonian--Laird style prediction, design/context meta-regression
only when the training design matrix has full rank, and robust training range
expanded by the target sampling uncertainty. No result-dependent threshold or
model choice is allowed.

## Reference and leakage reporting

The held-out RCT estimate is a noisy randomized reference, not a causal truth.
For each method report point estimate, interval, width, release/refusal,
absolute error to the held-out point estimate, and the relation between the
prediction interval and the held-out 95% sampling interval: `contains_full`,
`disjoint`, or `partial_overlap`. Also report sign disagreement only as a noisy
reference diagnostic.

Before reading the target outcome, save predictions and release decisions.
Then run an audit that flips or permutes only the target outcome rows and
recomputes the full pipeline; predictions, widths, and release decisions must
remain unchanged. Because the seven LOSO fits overlap in their training sets,
we report exact per-study rows and no bootstrap or independent-repetition
confidence interval.

## Interpretation gate

This pilot may establish design compatibility, leakage resistance, and the
behavior of descriptive prediction/refusal rules. It cannot estimate or claim
95% real joint coverage, a real independent calibration archive, or noiseless
causal truth. The mathematical rank floor for a finite 95% conformal radius is
19 independent calibration interventions; seven studies do not meet it.
