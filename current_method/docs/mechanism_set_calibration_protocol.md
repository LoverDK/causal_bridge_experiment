# Mechanism-set calibration protocol

This protocol records the additional audit added after the external review of
the manuscript. It turns the paper's joint-coverage assumption into a runnable
outcome-blind construction, while keeping its scope explicit.

## Construction

1. Define the decision universe before looking at target outcomes: all archived
   sources, all candidate bridges that may be selected, and the target.
2. Collect an independent audit archive with labelled mechanism measurements.
   For each audit archive and each entity in the universe, record a proxy error
   vector in the same standardized coordinate system.
3. For each audit archive, compute the maximum Euclidean proxy error over the
   entire universe. The calibrated radius is the finite-sample rank quantile
   `ceil((n_cal+1)(1-eta))` of these row-wise maxima.
4. For a new study, define `Gamma(Z_i)` as a ball around its proxy with that
   radius, optionally intersected with the declared mechanism domain. The same
   radius covers every candidate in one event, so an outcome-blind selection
   from the frozen menu does not require a new multiplicity correction.
5. Freeze the sets and all constants before reading target outcomes. Report the
   calibration sample size, entity count, dimension, radius, and source hash.

## Audit included in this repository

`run_mechanism_calibration.py` uses 199 independent audit archives, 11 entities
(four archive sources, six bridge candidates, and one target), two coordinates,
`eta=0.05`, and 2,000 independent test archives. The nominal test distribution
matches the audit distribution. `proxy_shift` multiplies test proxy errors by
1.5 and is an assumption-boundary stress test. The marginal rule calibrates the
95th percentile of individual entity errors; it is retained as a negative
control because it does not protect the joint selection event.

Run it with:

```bash
python current_method/run_mechanism_calibration.py
```

The saved `summary.csv`, `calibrator.json`, and `run_manifest.json` are the
evidence record. The summary reports both per-entity coverage and the joint
coverage event. This is a controlled calibration audit, not evidence that a
real cross-intervention mechanism archive has already been calibrated. Many
Labs 2 remains a standardized-intervention source-holdout benchmark, and no
target outcome is used by this protocol.
