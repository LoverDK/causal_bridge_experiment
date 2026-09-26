# ExAtlas-style comparison

This folder records a composition-only comparison with ExAtlas (Zhang et al.,
arXiv:2605.27153). It is deliberately labelled **ExAtlas-style**: the
experiment implements the paper's representation reconstruction and
composability decision, but does not claim to reproduce the paper's LLM
enrichment, conflict reconciliation, or bridge-experiment generation.

## Protocol

The comparison uses the existing synthetic DGP, the same generated archive and
held-out target for both methods, and the same 200 spawned random seeds. The
ExAtlas-style representation is the public treatment block, public outcome
block, and their element-wise interaction. It fits nonnegative simplex weights
by least squares, computes the reconstruction residual divided by the median
source-target distance, and releases a point composition only when that ratio
is at most 0.10. This represents a ten-percent residual relative to the local
source-target scale and is fixed before the shared-seed run.
Design-incompatible sources are removed before fitting. This stress runner
uses only the fixed 0.10 residual threshold; it does not run a threshold grid.

The held-out target effect and target outcome records are never used in fitting,
candidate selection, or the composability decision. The target effect is used
only after prediction to compute evaluation metrics. The threshold is fixed
before the run and is a sensitivity parameter, not a learned value.

## Metrics and interpretation

The runner reports composable-target rate and conditional MAE among composable
targets, as well as all-target raw-composition MAE.
The Causal ATLAS release rate and released-target MAE are reported alongside
these quantities. Conditional errors are not comparable to all-target errors;
the output therefore keeps both populations explicit.

From the repository root, run the seven-scenario, 200-repetition stress audit
with a new output directory:

```powershell
python current_method/exatlas/run_exatlas_stress.py --output reproduced/exatlas-stress
```

The output directory is required and must not exist. The runner writes
`stress_summary.csv`, `stress_records.csv`, and `stress_metadata.json` there.
The historical files with these names in this folder are preserved. This result
is suitable as an appendix diagnostic or baseline audit. It should not be
described as a full ExAtlas reproduction or as a comparison of the LLM-generated
bridge module.

## Controlled target-shift stress test

`run_exatlas_stress.py` repeats the comparison under observable
target shifts and hidden-moderator shifts of 0.25, 0.50, and 0.75 toward a
fixed in-domain anchor. The archive, target-outcome isolation, 200 repetitions
per scenario, and residual threshold remain fixed. This audit asks whether the
composition residual and the release decision respond to the type of shift,
while keeping raw composition error and Causal ATLAS release metrics separate.
It does not turn the synthetic shifts into evidence about real text-embedding
performance. The runner writes both `stress_summary.csv` (including fixed 95%
Wilson intervals for the composability and release rates) and
`stress_records.csv` (one row per seeded repetition), so every scenario can be
audited without re-running the generator. These intervals describe Monte Carlo
uncertainty; they are not coverage claims for either method.
