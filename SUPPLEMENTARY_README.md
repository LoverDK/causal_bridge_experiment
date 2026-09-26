# Supplementary materials

This directory is the submission package for the current ICLR 2027 manuscript,
*When Can Experiments Be Reused? Certified Transport, Refusal, and Causal
Bridging*. It contains the code, public inputs, frozen configurations, saved
numerical outputs, and paper-facing figure/table assets needed to inspect or
reproduce the empirical claims.

The submission archive is an export of the hash-pinned release allowlist. It
contains no Git metadata, local caches, generated scratch directories, or
machine-specific paths. The manifest and `tools/export_submission.py` define
the file-level export and integrity checks.

## Start here

1. Run `python reproduce.py verify` to check the delivered files.
2. Read [CURRENT_ARTIFACTS.md](CURRENT_ARTIFACTS.md) for the paper-item to
   artifact map.
3. Install `requirements.txt`, then use the reproduction commands in
   [README.md](README.md).

The release manifest identifies the exact accepted evidence bytes. A
reproduction command writes to a new output directory and never overwrites
these files. Smoke profiles check the software path; full profiles regenerate
the reported experiments.

## Package layout

- `current_method/`: current certificate, workflow, real-data supplement,
  selection/calibration audits, and the matched weight/geometric ablations.
- `paper_original/`: theorem-linked synthetic and Many Labs 2 framing runs.
- `legacy_audits/`: only the retained NSW reconstruction and the stronger
  baseline/semi-synthetic extension, plus their shared bridge and
  partial-identification implementation.
- `paper_figures/`: committed figure inputs, table fragments, and the portable
  renderer for the appendix figures.
- `LeanProofs/`: standalone Lean/Mathlib project for the deterministic
  mathematical kernels named in the manuscript appendix.
- `provenance/`: delivery hashes and imported-data provenance.

The package does not include superseded exploratory experiment families,
development-stage notes, or duplicate pre-integration paper fragments. The
complete ExAtlas procedure is not included because it was not run as a matched
comparator for this manuscript.
The retained `current_method/exatlas/` audit implements only the composition
stage. It uses one fixed residual threshold (0.10), with seven scenarios and
200 repetitions each. Its repaired standalone runner reproduces all historical
output bytes; this does not add a complete-system comparison.

The NSW real-covariate and semisynthetic truth audit is in
`legacy_audits/results/extensions/nsw_real_proxy_truth_v2/`. It uses a
participant-disjoint outcome-blind covariate split and frozen response surfaces
with exact finite-neighborhood truth. It is deliberately labelled as a
within-trial proxy and semisynthetic audit; it is not a real cross-intervention
mechanism-set calibration.
Its anonymous historical run manifest is supplied in
`provenance/nsw_real_proxy_truth_v2_public_manifest.json`. That labelled copy
preserves historical hashes while replacing the original machine-specific
output directory; the transformation is recorded in the manifest itself.

## Evidence boundaries

The source-corrected microcredit pilot is documented in
`MICROCREDIT_PUBLISHED_V1_REPORT_20260925.md`: two primary studies and a
separate post-hoc three-study population sensitivity. The published rounded
effect/SE source cells and unit conversions are versioned. ATLAS and design
meta-regression remain unqualified because the coordinate audit is incomplete.
All computed baselines refuse at the fixed tolerances, so conditional released
risk is undefined. This is descriptive feasibility evidence, not a validated
real mechanism-set benchmark. The old mixed-input output is not included.

Many Labs 2 is a source-holdout evaluation under a standardized intervention.
NSW is a within-trial reconstruction; its semi-synthetic extension uses known
generated response surfaces. Synthetic audits expose mechanism truth only for
post-hoc scoring. These protocols support the claims stated in the manuscript,
but they do not establish real cross-intervention mechanism calibration or a
universal coverage guarantee.

## Next real-data input

The outstanding real-study requirement is methodological: independent
interventions, harmonized estimands, outcome-blind mechanism proxies, a
separate calibration archive, a frozen calibration/target split, and an
independently randomized target reference.

The Lean project pins its compiler and Mathlib dependency and limits the
machine-checked scope to deterministic algebraic and interval statements. Its
README records the exact build and axiom-audit commands. Statistical
concentration, AIPW expectation identities, asymptotic arguments, and metric
extension results remain outside that formalization.
