# NSW Real-Covariate Proxy and Semisynthetic Truth Audit

The formal 100-replicate run uses the pinned NSW data, a fixed participant-
disjoint 40/30/30 development/calibration/validation split, and three frozen
response surfaces. The real-data component reads pretreatment covariates only;
the semisynthetic component uses the original NSW randomized assignment and
shared unit noise to make the finite-neighborhood treatment effect known.

## Results

- Observed-covariate proxy: 14 calibration entities, 13 validation entities,
  calibrated sup-norm radius `1.0664`, validation profile coverage `0.8462`.
- ATLAS: exact-truth interval coverage `1.000` on all three surfaces and
  release rate `0.000`; mean absolute error is `3.001` (constant), `2.766`
  (smooth), and `2.704` (interaction).
- Forced semantic intervals: exact-truth coverage `0.015`, `0.0417`, and
  `0.0933` on the same surfaces.
- Every target-effect flip audit passed; predictions and interval endpoints
  were unchanged after target reference replacement.

The proxy result is a within-trial observed-covariate audit. The causal truth
is exact only for the frozen semisynthetic response surfaces. Neither result
establishes real cross-intervention mechanism-set calibration.

Reproduction:

```powershell
python legacy_audits/scripts/run/run_nsw_real_proxy_truth.py --repetitions 100 --output results/extensions/nsw_real_proxy_truth_new
```
