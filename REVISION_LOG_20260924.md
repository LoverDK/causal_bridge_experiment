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

## ICLR 2027 paper integration: 2026-09-25

The corrected five-family panel and the all-family sensitivity panel were
integrated into the ICLR 2027 Overleaf source
`causal_lab_proposal_subpapers_tex_iclr2027/01.tex`.

- The main Experiments section now reports the five-family holdout (10 targets)
  and all-family sensitivity (23 families, 28 valid effects), the five named
  baselines, release frontiers, and zero target-effect flip leakage.
- The Discussion now states that these results are external-validity and
  baseline evidence only; Many Labs 2 standardized effects are noisy references
  and do not provide real mechanism sets, an independent real calibration
  archive, or causal target truth.
- The appendix now freezes the pinned commit and eligibility rule, records the
  corrected `study.analysis` unit, preserves the historical `study.name` run as
  an audit artifact, and includes the five-family/all-family summary table.

The local ICLR source compiled successfully with TeX Live 2026 to a 38-page
PDF. The main text occupies pages 1--9, page 8 contains the Many Labs figure
and surrounding text rather than a blank block, and page 9 ends at manuscript
line 485 after a complete Discussion sentence. References begin on page 10;
the remaining pages are appendix/references material. The Overleaf project was
updated with the same `01.tex` and its recompile completed successfully.
Existing warnings are layout warnings (underfull/one small overfull box); no
LaTeX error occurred.

## NSW real-covariate and semisynthetic truth audit: 2026-09-25

The repository now includes `legacy_audits/results/extensions/nsw_real_proxy_truth_v2/`,
generated by `legacy_audits/scripts/run/run_nsw_real_proxy_truth.py`. This is a
separate audit from the Many Labs family holdout and preserves the requested
NSW experiment without overwriting the earlier result directory.

- The real-data component reads only eight pretreatment NSW covariates and the
  pinned randomized assignment. A participant-disjoint 40/30/30
  development/calibration/validation split yields 14 calibration and 13
  validation entities. The calibrated sup-norm proxy radius is `1.0664`, and
  validation profile coverage is `0.8462`.
- The causal-truth component uses the real NSW covariates and original
  assignment with three frozen response surfaces and shared unit noise. The
  finite-neighborhood treatment effect is therefore known exactly for scoring
  in the generated outcomes. Across 100 repetitions and 600 target
  evaluations per surface, ATLAS has causal-truth coverage `1.000` and release
  rate `0.000`; forced semantic intervals cover `0.015`, `0.0417`, and `0.0933`
  on the constant, smooth, and interaction surfaces.
- Every target-effect flip audit passed. Predictions and interval endpoints
  were unchanged when held-out target references were replaced.

This experiment strengthens the evidence boundary in a real covariate and
assignment setting, but it does not create the missing evidence. NSW contains
one job-training intervention, the proxy is observed-covariate rather than a
latent mechanism set, and causal truth is exact only for the frozen
semisynthetic surfaces. The paper therefore continues to state that real
cross-intervention mechanism calibration, an independent real calibration
archive, and a real causal target reference remain open.

## Materials needed for the next real-data study

The checklist for starting the real cross-intervention study is recorded in
`REAL_CROSS_INTERVENTION_REQUIREMENTS.md`. In brief, the study needs multiple
independent interventions or randomized trials, harmonized treatment/control/
outcome/population/horizon definitions, outcome-blind design-based mechanism
proxies for every source and target, a separate calibration archive, a frozen
split and set-construction protocol, and an independently randomized target
reference. Individual-level potential outcomes are required for literal
noise-free causal truth; a randomized target estimate with its sampling
uncertainty supports a real reference audit but must be labelled as such.

## Microcredit expansion pilot protocol: 2026-09-25

Microcredit expansion was selected as the first real cross-intervention domain.
The pilot question is whether design and implementation information alone can
produce a useful ITT interval for an unseen project or region and refuse when
the interval is too wide. `MICROCREDIT_PILOT_PROTOCOL.md` freezes the scope:
the default estimand is invitation/eligibility ITT against usual service,
business and household outcomes are analysed separately, and incompatible
studies are excluded rather than silently harmonized.

The seven-study Meager archive is treated as a feasibility and pilot source.
It can support an inventory, mechanism dictionary, coder audit, and descriptive
leave-one-study-out stress test. It cannot support a stable distribution-free
95% finite-sample calibration claim. The formal gate is at least 19 independent
calibration interventions for the finite rank rule, with 25--40 total
interventions preferred for repeated held-out evaluation.

The AEA article page is reachable. The OpenICPSR project returned HTTP 403 in
the current environment, and DataCite metadata for `10.3886/E116357V1` exposes
no explicit rights entry. File inventory, individual-level coverage, and reuse
terms therefore remain unverified until a local package or accessible export
is supplied. No Meager file is redistributed or used to claim real mechanism
calibration before that verification.

## OpenICPSR package inventory: 2026-09-25

The user supplied an authorized download of `116357-V1.zip`. Its SHA-256 is
`1EC66E45ED401C7CC476548B0AE77DF0AF765942D7D8914202797D6FA4C61BFE`. The
archive contains 306 files: 95 Stata `.dta` files, one cleaned project
`RData`, 12 nested source ZIPs, analysis code, readmes, survey material and
PDFs. Study-specific directories or source packages are present for the seven
published units (Mexico, Mongolia, Bosnia, India, Morocco, Philippines and
Ethiopia). The root license states Modified BSD for code and CC BY 4.0 for
databases, images, tables and text.

This closes the prior *package inventory* gap. It does not close the scientific
gap: study-specific terms, the exact invitation-ITT alignment, complete
implementation fields, an independent calibration archive, and a causal
reference for a held-out intervention still require separate review. Raw files
remain local and are not committed to GitHub. The metadata-only record is in
`MICROCREDIT_OPENICPSR_INVENTORY_20260925.md`.

## Outcome-blind metadata audit: 2026-09-25

The first read-only metadata pass inspected one representative or cleaned data
file for each published study, recording rows, columns, assignment-field names,
candidate design/proxy fields, and documentation. Mexico, Mongolia, Bosnia,
India, Morocco and Ethiopia expose recognizable assignment/treatment fields in
the inspected files. The Philippines source package exposes credit-score and
randomization-tag fields but no simple treatment field, so it remains a design
review candidate rather than an automatically pooled invitation-ITT unit.

The audit is recorded in `MICROCREDIT_METADATA_AUDIT_20260925.md` and
`microcredit_metadata_audit.csv`. It is metadata-only: no effect estimates were
computed, no target outcomes were used for feature construction, and no raw
records were committed. The next required step is a two-coder design review of
the treatment arms, control conditions, outcome family and follow-up horizon.

The header-only extractor `tools/inspect_microcredit_metadata.py` generated
`microcredit_variable_label_audit.csv` with 884 candidate field labels. This
provides a concrete coder handoff, while retaining the rule that variable names
alone do not establish a common treatment or estimand.

## Distance to the reviewer requirement after this step

The package-access and file-inventory gap is closed, and the feasibility of
outcome-blind proxy construction is now supported by actual variable metadata.
The decisive gaps remain: a frozen common invitation-ITT estimand, blinded
dual-coder mechanism records, an intervention-disjoint calibration archive with
at least 19 independent units, and an independently randomized target
reference. The seven-study package remains a pilot and cannot be described as a
real 95% distribution-free calibration study.
