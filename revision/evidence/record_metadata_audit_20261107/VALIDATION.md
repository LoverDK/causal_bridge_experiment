# Validation record

Date: 2026-11-07. This is a deterministic record-label repair, not a new experiment.

Command, from `current_method`:

```powershell
$env:PYTHONIOENCODING='utf-8'
D:/python/python.exe -c "import time,unittest; t=time.perf_counter(); suite=unittest.TestSuite(unittest.defaultTestLoader.discover('tests',pattern=p) for p in ['test_audit_plus.py','test_operational_metadata.py']); result=unittest.TextTestRunner(verbosity=2).run(suite); print('elapsed_seconds=',round(time.perf_counter()-t,3)); raise SystemExit(not result.wasSuccessful())"
```

Result: all 10 tests passed; unittest execution 0.003 seconds, total including Python imports 1.036 seconds. `git diff --check` passed. Tests check the actual quantile return classification, valid design/adaptive-Rinf cases, invalid controls, point-only NA, outer-envelope conditions, declared high noise/bias, and unknown-label rejection.

The first test attempt encountered Windows sandbox temporary-directory write/cleanup denial. The test now captures the writer's DataFrame via a mocked `save` call, so it tests the record content without relying on host temporary-directory permissions. No scientific code or test expectation changed to bypass a numerical failure.

Read-only archive audit command:

```text
D:/python/python.exe audit_legacy_record_labels.py --output ../revision/evidence/record_metadata_audit_20261107
```

Audit time: 0.36728 seconds. Five archived CSV SHA256 hashes match before and after. The independent label table contains all 9600 operational records and all 216 frontier records. No optimizer, model fit, outcome sampling, numerical-result rewriting, or real-data processing occurred.

Source changes in `experiments.operational` are restricted to metadata emission and the nominal-bound label. The estimator, optimizer inputs, radii, acquisition policy, observations, numeric coverage, and original result files remain unchanged. The quantile core was already correct and is unchanged.

Independent review: the report agent rebuilt labels directly from archived scenario/method identities without importing the new helper. It independently obtained 2400 applicable certificate rows, 4800 unsupported-condition rows, 2400 point-only rows, and 144 of 216 frontier rows without an applicable bound, and matched all five archive hashes. Root also reviewed the changed numerical-code locations and exact-Bbar identity. Neither review found a blocking issue.
