# Conditional Common-CATE numerical study

This package accompanies Appendix T. All 17 target calculations were executed; scientific qualification remains separate and conditional. The study uses a fixed 40-source/17-target split of the canonical Many Labs 2 framing cohort. It does not replace the older 57-source leave-one-out benchmark.

## Contents

- `results/predictions_pre_reveal.csv`: 102 frozen certificates, including geometry, bias, both radii, admissibility and numerical decisions.
- `results/weights.csv`: 4,080 source weights. `source_inputs.csv` and `source_estimates_pre_reveal.csv` contain the design and effect summaries used.
- `results/optimization_audit.csv`: 34 final cone solves and their deterministic tolerance attempts.
- `results/sensitivity.csv`: 918 fixed-weight sensitivity rows.
- `results/target_references.csv`, `target_evaluation.csv`, `policy_comparison.csv`, and `native_baseline_evaluation.csv`: post-freeze noisy-reference scoring.
- `results/qualification_by_result.csv`: empirical qualification independently of each computed release/refusal decision.
- `aggregate_inputs/`: original frozen site split, original profile audit and aggregated full-site/arm counts. These contain no participant identifiers or individual response records.
- `math_specification.md`, `scientific_qualification.md`, and `protocol/numerical_protocol.md`: the conditional law, model-relative proof and scientific limits.
- `audit/pre_reveal_freeze.json`: original run's pre-target-reveal hash manifest. It records the original participant-level inputs as hashes; those records are not redistributed here. Other audit JSON files preserve independent numeric checks.
- `original_code/run_conditional.py`: byte-identical original numerical implementation, including both SOCP formulations. It expects the original four staged input CSVs under `data/` and the recorded dependencies. It never opens target outcomes. It is preserved for inspection; the participant-level staged files are not included in this aggregate package.
- `replay_aggregates.py`: a portable, read-only check of all saved certificates, sensitivities and main comparisons from aggregated inputs. It neither optimizes weights again nor validates scientific assumptions.

## Portable replay

Use Python with NumPy and pandas (`requirements.txt` lists the original numerical environment, including SciPy/Clarabel for the archived optimizer). From this directory:

```sh
python -B replay_aggregates.py
```

The script first verifies `package_manifest.json`, reconstructs profile geometry, imbalance allowances, count-only noise, frozen weighted estimates and decisions, then checks reference summaries. It prints JSON and does not write over any frozen result. A successful replay establishes arithmetic consistency, not empirical causal coverage or a new prospective holdout experiment.

The original `pre_reveal_freeze.json` hashes refer to the original execution layout. This package preserves all result files byte-for-byte, relocates the original source file under `original_code/`, and adds the portable aggregate replay and count file after target scoring. `package_manifest.json` separately pins these packaged bytes. Do not describe the added replay script as preregistered or pre-reveal.

## Primary interpretation

At illustrative risk-difference tolerance .15, optimized R2 releases 8/17 conditionally. Its mean raw width is .3429 versus Uniform's .8662, while noisy-reference MAE is .08134 versus .07276. Extra source bias .025 leaves one release. FE/DL weights use R-infinity in the matched-certificate comparison; their native approximate model intervals have separate interpretations. No result establishes the substantive Common-CATE, reporting, retention or conditional response assumptions. Source and reference failure budgets are .05 each, hence the combined compatibility assertion has conditional failure bound .10.

No new bridge acquisition or participant-cost comparison was conducted. See the manuscript for the self-contained formulas, all targets, sensitivity and qualification scope.
