# Retained NSW and extension artifacts

This directory contains only experiment components used by the current paper:

- the public 445-person NSW input and within-trial reconstruction;
- stronger source-only baselines;
- the NSW covariate semi-synthetic extension;
- the finite-library bridge diagnostic used by the extension protocol; and
- the shared implementation of the paper's bridge and partial-identification
  routines.

Run the retained checks from this directory with:

```powershell
python -m unittest discover -s tests -v
python scripts/run/run_nsw_experiment.py
python scripts/run/run_requested_extensions.py synthetic
python scripts/run/run_requested_extensions.py nsw
python scripts/run/run_requested_extensions.py bridge
python scripts/build/build_extension_artifacts.py
```

The extension protocol and its bounded interpretation are in
`docs/paper/extension_protocol_v2.md` and `docs/paper/extension_results_v2.md`.
Superseded exploratory runners, stage notes, and old result families are not
part of this delivery tree.
