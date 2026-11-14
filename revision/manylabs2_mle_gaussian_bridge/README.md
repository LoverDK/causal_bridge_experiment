# Bernoulli MLE and Gaussian bridge-design simulation

The frozen aggregate protocol defines the complete synthetic DGP. Main simulation outputs, 68,816 target-level records, mathematical derivation, model-compatibility analysis and historical independent audits are included unchanged. These are simulations calibrated from source data, not a new randomized target trial or an unconditional real-data certificate.

## Reproduce from the public aggregate protocol

Install NumPy, pandas and SciPy. From this package directory, use a fresh output path:

```sh
python -B code/bernoulli_mc.py --protocol protocol/execution.json --outdir ../../reproduced/mle-new-run
python -B code/export_target_metrics.py --protocol protocol/execution.json --outdir ../../reproduced/mle-new-run
```

Inspect the command-line parsers before running; original full execution and target export took about 90 and 34 seconds on the author's machine, and current hardware times may differ. Publication did not rerun the Monte Carlo study.

`data/all_design.csv` and `data/source_only.csv` contain participant records and are intentionally omitted. The aggregate `protocol/execution.json`, site split and profile audit suffice for the simulation. `code/build_inputs.py` is preserved for provenance and requires those original inputs; it is not the public reproduction entry point.

Original `artifact_manifest.json`, `audit/full_run_freeze.json` and other run manifests describe the historical full local run, including omitted participant files and pilot artifacts. They are preserved, not rewritten to imply a different pre-reveal freeze. The repository update manifest enumerates the actually published bytes. The archived audit scripts check original private-input hashes and may need the original full local archive; this does not make the public numerical outputs missing.

Read `final_report.md`, `dgp_specification.md`, `mle_delta_derivation.md`, and `theorem_5_6_compatibility.md` for findings and exact model scope.
