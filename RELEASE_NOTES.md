# Release notes

## 25 September 2026: source-corrected microcredit execution

The published-summary microcredit pilot now has a two-study primary input
(Mexico and India EL1) and a separate three-study post-hoc population
sensitivity that adds Morocco's all-sample weighted estimate. The old Morocco
high-propensity estimate is excluded from the primary; the previous mixed-input
results are preserved locally and excluded from this delivery. The source
specification, deterministic input builder, two accepted runs and independent
arithmetic verifier are included. The complete execution and claim boundary
is `MICROCREDIT_PUBLISHED_V1_ACCEPTANCE_20260925.md`.

Primary fixed effect is computed for two held-out targets. Sensitivity fixed
effect and training range are each computed for three targets. All computed
rules refuse at every frozen tolerance; released-target risk is undefined.
ATLAS and design meta-regression remain unqualified. These results are an
auditable descriptive feasibility exercise, not real mechanism calibration,
common-effect identification, or evidence of superiority. The population
selection is explicitly post-hoc, after published cells were visible.

Nine microcredit tests actually execute and pass. Independent verification
matches both saved runs and their input/protocol/output hashes, with maximum
numerical discrepancy 7.11e-15. The current-method suite passed 42 tests before
the portability repair described in the current release validation record.
The 172,800-plan and 345,600-stopped-record ablation audit was independently
reconstructed without changing historical outputs. The exporter's 26 isolated
checks pass; actual archive verification is recorded beside each exported ZIP.

These software and arithmetic checks do not settle empirical validity. The
selection audit tests outcome-adaptive weighting with zero causal discrepancy;
the full bridge workflow uses design-measurable weights. The geometric minimum
has no additional release/cost gain over the barycentric bound in the tested
ablations. The complete ExAtlas procedure and real cross-intervention mechanism
calibration remain untested.

The delivery uses the reviewed working-tree allowlist and current file hashes,
not `git archive HEAD`. Historical page counts below describe earlier drafts
and do not certify the final Overleaf PDF.

## Historical release: 17 September 2026

The two new ablations are incorporated into the ICLR 2027 manuscript as Appendix P, Tables 15 and 16. The limitation paragraph retains the missing complete ExAtlas comparison.

The integrated PDF has 38 pages: main text is pages 1–9, references begin on page 10, main Figures 1/2/3 remain on pages 4/7/8, and the source-estimate Figure 6 remains near the end of the appendix. Page 8 contains the Many Labs figure and text, and page 9 ends at manuscript line 485. The first nine pages' extracted text is identical to the preceding revision. All 31 checked theorem, assumption, corollary, lemma, proposition, and proof environments were preserved. Integration does not claim to repair the previously flagged frozen theoretical conditions.

Validation before release:

- Full ablation run: 28 unit tests and 15 result checks passed.
- Independent audit: 172,800 plans reconstructed; maximum radius discrepancy 2.22e-16 and zero prediction discrepancy.
- All 345,600 stopped records reconstructed; maximum discrepancy 5.11e-15, all costs matched.
- Random-R2 and nearest-R2 records matched the original workflow, 14,400 each.
- Packaged ablation smoke run completed in an isolated directory; all 28 tests passed.
- Packaged original synthetic and Many Labs 2 scripts reproduced the paper's reported main results.
- NSW and requested-extension test modules passed, seven tests each.
- Portable appendix-figure generation completed from archived CSVs.

The supplementary package was subsequently narrowed to the current-paper
evidence: retained NSW and extension protocols, current-method results,
theorem-linked synthetic/Many Labs 2 records, and paper-facing assets. Superseded
experiment families and development-stage status documents were removed from
the delivery tree; Git history retains their provenance.

Primary conclusions are bounded by the specified DGP and protocol. Weight optimization helps bridgeable menus; the minimum of the two geometric bounds has no extra release/cost benefit over the barycentric bound at the tested settings. These results do not establish superiority over the complete ExAtlas pipeline or validate real cross-intervention mechanism calibration.

## Revision audit: 24 September 2026

The repository now includes an independent, outcome-blind mechanism-set
calibration audit. It freezes 11 entities (four archive sources, six bridge
candidates, and one target), calibrates a joint radius from 199 labelled audit
archives, and evaluates 2,000 independent test archives. Nominal joint coverage
is 0.951; reusing a marginal radius across the universe gives 0.544 joint
coverage. A 1.5x test-only proxy shift reduces joint coverage to 0.348, exposing
the exchangeability boundary. Reproduce it with `python reproduce.py
calibration --output reproduced/calibration`.

This audit is controlled labelled-error evidence. It does not establish real
cross-intervention mechanism calibration. The full change record is
`REVISION_LOG_20260924.md`.

## 25 September 2026: cross-effect-family external validity

Added a pinned Many Labs 2 study-level summary and a complete family-holdout
audit. Five complete families are held out in turn (10 target studies); 28 of
32 published summary rows pass the pre-fixed Cohen's d eligibility rule. The
audit compares fixed/random effects, context matching, a robust training range,
and family split-conformal, with release/refusal, width, noisy-reference
coverage, absolute error, sign error, and target-effect flip leakage checks.

The result is real cross-family stress-test evidence, not real mechanism-set
calibration. Fixed-effects all-target coverage is 0.50 and random-effects is
0.90 in this ten-target audit; at half-width thresholds 0.20--1.00 they
release at most 100% and 20%, respectively, while the robust range and
split-conformal rules refuse all targets. The next evidence requirement remains
an independently calibrated, design-metadata mechanism archive collected or
preregistered across interventions.

## 25 September 2026: named baseline panel

The family holdout now has a separate baseline panel covering transport
meta-regression, hierarchical meta-analysis, robust partial identification,
study-level split-conformal, and family-level split-conformal under the same
frozen targets and thresholds. Hierarchical coverage is 0.90 and robust-range
coverage is 1.00 over ten noisy references, but they release at most 2/10 and
0/10 respectively at the preset thresholds. The panel closes the named
baseline comparison gap while retaining the limitation that Many Labs 2 has no
real mechanism sets, independent calibration archive, or causal target truth.

## 25 September 2026: baseline-unit correction and all-family sensitivity

The baseline audit was corrected after finding that `study.name` is a family
label, not a unique study unit. The corrected output uses `study.analysis` for
study-level conformal calibration and is saved separately from the historical
run. Study-level coverage changes from 0.80 to 1.00 on the ten-target panel,
with zero releases at the preset thresholds.

An all-family sensitivity panel holds out all 23 eligible families and 28
valid effects. Hierarchical and transport coverage are 0.964 and 0.929, with
only 2/28 releases each; robust and both conformal methods release 0/28. This
improves audit validity and target-family coverage but does not establish real
mechanism-set calibration or causal target truth.
