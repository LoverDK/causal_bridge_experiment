# Microcredit Expansion: Real Cross-Intervention Pilot Protocol

Status: protocol and feasibility gate, 2026-09-25. No empirical result is
claimed by this file.

## Decision

Microcredit expansion is a good first real-data domain for the paper. The
primary question is:

> Using only intervention design and implementation information, can the
> method give a defensible interval for the ITT effect of being invited to
> receive microcredit services in an unseen project or region, and refuse when
> the interval is too wide?

The initial Meager archive is a **pilot**, not yet the formal calibration
experiment. Seven studies can test estimand compatibility, construct a
prespecified mechanism dictionary, and run descriptive leave-one-study-out
stress tests. Seven studies cannot support a stable 95% finite-sample
rank/conformal calibration claim.

## Estimand gate

Each analysis must freeze one outcome family, follow-up horizon, population,
and effect scale. The default estimand is the randomized ITT contrast between
an invitation/eligibility assignment and the study's declared usual-service
control. Business outcomes and household-consumption outcomes are separate
analyses. Take-up or treatment-on-the-treated effects are not silently mixed
with invitation ITT effects.

Studies that cannot be aligned, or cannot be deterministically normalized with
an auditable rule, are excluded from the transported point estimate and
reported as design-only context.

## Outcome-blind mechanism map

Before opening held-out target outcomes, freeze a data dictionary and a
deterministic map `Gamma(Z) -> U`. Candidate coordinates may include loan
amount and price, repayment schedule, individual versus group lending,
eligibility rules, control-group credit access, baseline credit access,
baseline business conditions, delivery channel, and implementation fidelity.

The coding sheet must record units, missingness, measurement time, source
document, coder, disagreement, and uncertainty. A second coder or independent
expert should audit a prespecified subset. Target effects, effect labels,
outcome-derived embeddings, and post-hoc feature selection cannot enter the
map or its radius.

## Split and sample-size gate

The calibration unit is an independent intervention project or trial, not a
participant, site, or subgroup from the same project. The formal rank rule
needs at least 19 independent calibration units for a finite 95% radius; this
is a mathematical floor, not a stability recommendation. For repeated held-out
targets, aim for at least 25--40 independent interventions overall, with a
separate development set, at least 19 calibration units, and one or more
held-out targets. If only seven studies are available, label all results
pilot/descriptive and do not report a distribution-free 95% calibration claim.

The split manifest, candidate universe, calibration rule, and release
tolerance must be frozen before target outcomes are read. A study cannot be
reused as calibration and as a held-out target in the same scored split.

## Causal reference language

An independent randomized held-out trial supplies a noisy causal reference:
its prespecified ITT estimate and uncertainty. It does not reveal an exact
individual-level causal truth. Report prediction/reference comparisons using
three categories: the prediction interval contains the full reference
interval, the intervals are disjoint, or the comparison is indeterminate.
Do not call a hit on a noisy point estimate exact causal-truth coverage.

Exact coverage remains available only in the existing semisynthetic audit with
known potential outcomes. The real experiment should be called a randomized
causal-reference audit.

## Required reporting

Use the same target splits and release thresholds for ATLAS and all baselines:
fixed/random effects, transport meta-regression, robust range or partial
identification, and study/family conformal methods. Report reference-interval
compatibility, definite miss rate, release rate, interval width, error among
released targets, sign errors, and bridge cost. Any false-release metric based
on a target reference must be uncertainty-aware and labelled accordingly.

## Feasibility status of the starting archive

The AEA article page is reachable and identifies Meager's seven-study paper.
The user supplied an authorized local OpenICPSR download. Its recorded SHA-256
is `1EC66E45ED401C7CC476548B0AE77DF0AF765942D7D8914202797D6FA4C61BFE`; the
archive contains 306 files, including 95 Stata files, one cleaned `RData`
object, study-level source packages, readmes, survey material and code. The
metadata-only inventory is in
`MICROCREDIT_OPENICPSR_INVENTORY_20260925.md`.

The package root license states Modified BSD for code and CC BY 4.0 for
databases, images, tables and text. This is evidence about the downloaded
package, not a blanket clearance for every upstream trial file or every new
linkage. Study-specific terms, consent/ethics conditions, and the precise unit
of observation still require review before individual-level modelling or any
redistribution.

The package is therefore sufficient to start an outcome-blind inventory and
estimand/codebook audit. It still cannot be treated as a seven-unit
independent 95% calibration archive. The next action is to map each study's
treatment, control, population, horizon, design proxies, and source terms;
only compatible records then enter the descriptive pilot.
