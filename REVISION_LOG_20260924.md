# Revision log: certificate-centered revision

Date: 2026-09-24

This log records the work added after the independent PDF-based assessment of
the ICLR 2027 manuscript. It is intentionally separate from the paper's
scientific results and does not overwrite the earlier saved runs.

## Decision taken

The paper is being revised around one defensible technical spine:

> a calibrated mechanism-set and simultaneous-noise certificate remains valid
> after outcome-adaptive archive composition, and refusal is the explicit output
> when that certificate is too wide.

Sharp refusal and bridge design are retained as supporting boundaries. The
manuscript no longer presents all four theory blocks as equally independent
contributions.

## Added to this repository

- `current_method/atlas_new/mechanism_calibration.py`: reusable construction of
  a joint row-wise calibration radius and outcome-blind mechanism balls.
- `current_method/run_mechanism_calibration.py`: fixed-seed audit runner.
- `current_method/tests/test_mechanism_calibration.py`: tests for nominal joint
  coverage, the marginal negative control, and frozen-universe validation.
- `current_method/docs/mechanism_set_calibration_protocol.md`: the protocol,
  scope conditions, and interpretation.
- `current_method/results/mechanism_calibration/`: saved summary, calibrator,
  and run manifest.
- `reproduce.py calibration`: isolated reproduction entry point.

The audit uses 199 independent calibration archives, 11 entities (four archive
sources, six candidate bridges, and one target), two proxy coordinates, and
2,000 independent test archives. Under matched nominal errors, joint coverage
is `0.951`; a marginal radius reused over the full universe has `0.544` joint
coverage. Under a 1.5x test-only proxy shift, joint coverage is `0.348`. These
are controlled labelled-error results, not a claim that a real
cross-intervention archive has already been calibrated.

## Manuscript changes

The ICLR manuscript source at
`_overleaf_current_20260924/causal_lab_proposal_subpapers_tex_iclr2027/01.tex`
was updated to:

1. make the selection-safe reuse certificate the primary contribution;
2. state refusal and bridge design as bounded extensions;
3. add the outcome-blind calibration audit and its exact evidence boundary;
4. distinguish the new labelled calibration audit from Many Labs 2 source
   holdout and NSW within-trial reconstruction.

## Reproduction

From the repository root:

```bash
python reproduce.py calibration --output reproduced/calibration
python current_method/run_tests.py
python reproduce.py verify
```

The final command checks the SHA-256 delivery manifest. The ZIP export must be
created from the committed tree with the procedure in `ANONYMOUS_EXPORT.md`.

The revised manuscript source compiled successfully with the local TinyTeX
`pdflatex` tool on two passes. The compile produced no fatal errors; the source
still contains the existing first-pass citation and cross-reference warnings
until the normal bibliography/Overleaf build is run.

## Remaining evidence gap

No real cross-intervention mechanism labels or independent real calibration
archive were added in this revision. The paper must retain conditional wording
for that claim, and a future real study should freeze `Gamma`, `L`, `H`, and
the calibration split before target outcomes are inspected.

## Follow-up audit: 2026-09-25

The repository now includes a real Many Labs 2 cross-effect-family holdout
audit. It adds the pinned author summary
`current_method/data/manylabs2_original_effects.csv`, the runner
`current_method/run_effect_family_holdout.py`, its unit tests, protocol, and
the saved result directory `current_method/results/effect_family_holdout/`.

The split was fixed before scoring: five complete target families (Hauser,
Huang, Miyamoto, Ross, Savani), ten target studies, and 28 eligible records
from the 32-row summary. Fixed/random effects, context-stratified pooling, a
training-range baseline, and family split-conformal are compared. The audit
reports release/refusal, interval width, noisy-reference coverage, absolute
error, sign error, and a target-effect flip test. Maximum prediction and
radius changes under the leakage test are both zero.

At the pre-set half-width thresholds 0.20--1.00, fixed effects release 20%--
100% with 0.50 coverage over all ten targets; random effects release 0%--20%
with 0.90 all-target coverage; the robust range and split-conformal rules
refuse all targets at these thresholds. The released-target counts are small,
and the references are noisy standardized effects rather than causal truth.

This experiment closes the prior gap of having only same-intervention source
holdout for real data, but it does not close the central mechanism gap: the
public summary has no real `U_i`, independent calibration archive, or causal
truth. The next feasible step is a preregistered/newly collected
cross-intervention archive with design-metadata mechanism proxies frozen before
target outcomes, an independent calibration split, and the same baseline
panel.

## Follow-up baseline panel: 2026-09-25

The same frozen family holdout now has an explicit baseline panel in
`current_method/run_effect_family_baselines.py`, with protocol and tests in
`current_method/docs/effect_family_baselines_protocol.md` and
`current_method/tests/test_effect_family_baselines.py`. The result directory
is `current_method/results/effect_family_baselines/`.

The panel compares transport meta-regression, Normal-Normal hierarchical
meta-analysis, a robust training-range partial-identification baseline,
study-level split-conformal, and stricter family-level split-conformal. It
reports the same release/refusal, width, noisy-reference coverage, absolute
error, and sign-error metrics at thresholds 0.20--1.00, with a per-family
target-effect flip audit.

For the ten held-out studies, hierarchical coverage is 0.90 and robust-range
coverage is 1.00, but hierarchical releases only 2/10 at threshold 1.00 and
the robust and both conformal rules release 0/10 throughout the preset range.
Transport meta-regression releases 2/10 and has all-target coverage 0.80.
Maximum prediction and radius changes under the flip audit are both zero.

This closes the missing named-baseline comparison in the real-data audit. It
does not close the decisive evidence gap: the public Many Labs summary still
contains no real mechanism sets `U_i`, independent calibration archive, or
causal target truth. The next feasible plan is a preregistered or newly
collected cross-intervention archive with design-metadata mechanism proxies,
an independent calibration split, and the same baseline panel.

## Implementation correction and all-family sensitivity: 2026-09-25

An audit of the baseline implementation found that the first panel passed
`study.name` to the study-level conformal routine. In the Many Labs author
summary, `study.name` is the family label, so that run silently collapsed the
study-level and family-level calibration units. The old output remains in
`results/effect_family_baselines/` as a historical audit record; the corrected
five-family output is in `results/effect_family_baselines_corrected/` and now
uses unique `study.analysis` ids for study-level leave-one-out calibration.

The correction changes study-level noisy-reference coverage from 0.80 to
1.00 on the ten-target panel, while its release rate remains 0/10 at every
preset half-width threshold. Family-level conformal remains 0.80 coverage and
0/10 release. A new unit test verifies that the two radii are not silently
identical.

To test target-selection sensitivity, the new
`results/effect_family_baselines_all/` panel holds out all 23 eligible
families and all 28 valid study-level effects. Hierarchical coverage is 0.964
and transport coverage is 0.929; each releases only 2/28 at the preset range.
Robust partial identification and both conformal rules have 1.00 coverage in
this noisy-reference audit but release 0/28. All target-effect flip audits
remain exactly zero.

This correction improves the validity of the baseline comparison and the
all-family sensitivity analysis, but it does not reduce the central distance
to the PDF assessment's strongest requirement: there is still no real `U_i`,
independent outcome-blind calibration archive, or causal target truth. The
next feasible experiment remains a preregistered or newly collected
cross-intervention archive with mechanism proxies and calibration split frozen
before target outcomes are read.
