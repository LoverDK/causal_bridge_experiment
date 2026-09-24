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
