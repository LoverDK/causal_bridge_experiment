# Reviewer 1 experiment archive

Frozen reports, code, configurations, summaries and independent checks for five experiment streams. All copied experimental files retain their original bytes.

- `selection_safe_comparison`: 5,000 worlds/cell; `PROTOCOL.md`, `config.json`, `run.py`, `verify.py`, `full/summary.csv`, `full/paired.csv`, `results.md`.
- `mechanism_calibration`: 26 conditions × 2,000 archives; `protocol.md`, `run_calibration_stress.py`, `independent_audit.py`, `full01/`, `RESULTS.md`.
- `matched_weighting`: archived Appendix P reanalysis; `protocol.json`, `analyze.py`, `verify_saved_summaries.py`, `REPORT.md`.
- `end_to_end_baselines`: archived Appendix L/P common-world comparisons; `PROTOCOL.md`, `analyze_saved.py`, `verify_saved.py`, `REPORT.md`.
- `sensitivity_bridge_robustness`: saved smoothness and 200-design objective comparisons; `deterministic_protocol.json`, `run_deterministic.py`, `check_deterministic.py`, `deterministic_reanalysis01/RESULTS.md`.

## Reproduction and path relocation

Use the original manifest commands and fresh output directories. A/B generators refuse to overwrite existing outputs. Their excluded `full/raw`, `smoke/raw`, `full01/raw`, and `smoke01/raw` arrays are reproducible from the stored seed schedule. The original ledgers retain the original local raw-file hashes.

C/D/E archived programs retain author-machine absolute paths for provenance. Run them only in a scratch copy, adapting path constants to this repository without changing numerical code or protocols:

1. C: point `ROOT` after loading `protocol.json` to the repository root. Inputs live under `current_method/results/ablations_full/` and `current_method/results/workflow_full/`; expand `plans.jsonl.gz` losslessly if needed. The existing `run_manifest.json` records the uncompressed hash. Normalize Windows path separators when checking its `source_sha256` keys on POSIX.
2. D: point `E` to the repository root and `A` to `revision/reviewer1_baseline_revision/`, which holds all three prior comparison/provenance inputs.
3. E: point the two frozen design/record paths to `current_method/results/full/bridge_designs.json` and `bridge_records.csv`; retain protocol hashes and use a fresh output location. The source-preservation audit also refers to the original manuscript as provenance; the manuscript is not part of this experiment release.

Saved results are retained unchanged. Path relocation is required for C/D/E full reanalysis on another computer; this publication step does not claim a new end-to-end rerun. Packages include the original independent checks.
