# Supplementary materials

This directory is the submission package for the current ICLR 2027 manuscript,
*When Can Experiments Transfer? Operational Certificates and Active Causal
Bridging*. It contains the code, public inputs, frozen configurations, saved
numerical outputs, and paper-facing figure/table assets needed to inspect or
reproduce the empirical claims.

## Start here

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

## Evidence boundaries

Many Labs 2 is a source-holdout evaluation under a standardized intervention.
NSW is a within-trial reconstruction; its semi-synthetic extension uses known
generated response surfaces. Synthetic audits expose mechanism truth only for
post-hoc scoring. These protocols support the claims stated in the manuscript,
but they do not establish real cross-intervention mechanism calibration or a
universal coverage guarantee.
