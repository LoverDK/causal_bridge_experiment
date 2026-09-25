# Supplementary materials

This directory is the submission package for the current ICLR 2027 manuscript,
*When Can Experiments Transfer? Operational Certificates and Active Causal
Bridging*. It contains the code, public inputs, frozen configurations, saved
numerical outputs, and paper-facing figure/table assets needed to inspect or
reproduce the empirical claims.

The submission archive is an anonymous export of the tracked files. It contains
no Git metadata, local caches, generated scratch directories, or machine-specific
paths. See [ANONYMOUS_EXPORT.md](ANONYMOUS_EXPORT.md) for the export and audit
procedure.

## Start here

The latest revision work and its evidence boundary are recorded in
[REVISION_LOG_20260924.md](REVISION_LOG_20260924.md).

1. Run `python reproduce.py verify` to check the delivered files.
2. Read [CURRENT_ARTIFACTS.md](CURRENT_ARTIFACTS.md) for the paper-item to
   artifact map.
3. Install `requirements.txt`, then use the reproduction commands in
   [README.md](README.md).

The committed result files are the exact evidence used by the manuscript. A
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
- `provenance/`: delivery hashes and imported-data provenance.

The package does not include superseded exploratory experiment families,
development-stage notes, or duplicate pre-integration paper fragments. The
complete ExAtlas procedure is not included because it was not run as a matched
comparator for this manuscript.

The NSW real-covariate and semisynthetic truth audit is in
`legacy_audits/results/extensions/nsw_real_proxy_truth_v2/`. It uses a
participant-disjoint outcome-blind covariate split and frozen response surfaces
with exact finite-neighborhood truth. It is deliberately labelled as a
within-trial proxy and semisynthetic audit; it is not a real cross-intervention
mechanism-set calibration.

## Evidence boundaries

Many Labs 2 is a source-holdout evaluation under a standardized intervention.
NSW is a within-trial reconstruction; its semi-synthetic extension uses known
generated response surfaces. Synthetic audits expose mechanism truth only for
post-hoc scoring. These protocols support the claims stated in the manuscript,
but they do not establish real cross-intervention mechanism calibration or a
universal coverage guarantee.

## Next real-data input

The concrete data and protocol requirements for the outstanding real study are
listed in [REAL_CROSS_INTERVENTION_REQUIREMENTS.md](REAL_CROSS_INTERVENTION_REQUIREMENTS.md).
The short version is: independent interventions, harmonized estimands,
outcome-blind mechanism proxies, a separate calibration archive, a frozen
calibration/target split, and an independently randomized target reference.
