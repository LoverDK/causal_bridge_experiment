# Published-summary microcredit pilot: accepted execution record

This record accepts the numerical execution of two explicitly versioned
descriptive analyses on 2026-09-25. It does not accept real mechanism
calibration, measurement equivalence, or the superseded mixed-input run.
The source correction and population sensitivity are post-hoc amendments.

## Sources and eligibility

The exact table cells, PDF hashes, sample definitions and conversion constants
are in `data/microcredit_published_sources_v1.json`. Source papers identify
assignment-clustered standard errors; the repository verifies the deterministic
unit conversion and downstream calculations. No native Stata or raw-data
equivalence is claimed. Source PDFs and private raw records are not redistributed.

| Study and role | Published effect (SE), original units | Population and inference | Converted effect (SE), 2009 USD PPP per fortnight |
|---|---:|---|---:|
| Mexico, primary | 0 (39), two-week pesos | Endline respondents, N=16005; 238 geographic assignment clusters; Table 3 col (3), PDF physical p.40 | 0.000000 (4.003323) |
| India EL1, primary | 354 (314), 30-day rupees | All-household profit, N=6239; weighted area-clustered; Table 3A col (4), PDF physical p.37 | 15.341040 (13.607589) |
| Morocco, population sensitivity only | -476 (1252), annual MAD | All sample weighted, N=5524; inverse sampling weights, 0.5% trimming, paired-village strata and village-clustered SE; Table 8B col (5), PDF physical p.20 / printed p.142 | -4.247724 (11.172586) |

The previous Morocco 2005 (1210), N=4934 cell belongs to the high-propensity
stratum. It is excluded from the primary input. The all-sample replacement is
reported only in a separate population sensitivity, selected for the protocol's
population definition after published values were visible. It is not a new
preregistered primary. Mexico's old Python reconstruction is not mixed with
the rounded published 0 (39) cell.

Bosnia and the Philippines remain outside the community stratum because they
randomize applicant-level approval/offer. Mongolia's arm-specific contrast
and Ethiopia's MF-vs-None outcome/window/SE remain unresolved. No study was
added by pooling treatment arms or using realized borrowing.

The recall periods, measurement constructs, sampling rules and horizons differ.
PPP/period conversion gives an operational scale only. The fixed-effect
baseline is a descriptive rule across these records, not an estimate of a
single common causal effect. Source eligibility does not establish that its
sampling-only interval captures transport heterogeneity.

## Execution results

Primary output: `results/microcredit_primary_published_v1/`. Two held-out
fits, each with one training study:

| Method | Execution status | Computed targets | Released at delta=0.20 | Noisy-reference relation |
|---|---|---:|---:|---|
| Fixed effect | computed | 2 | 0 | 1 contains_full, 1 partial_overlap, 0 disjoint |
| Random effects | not_identified, insufficient frozen degrees of freedom | 0 | not applicable | not evaluated |
| Training range | not_identified, requires at least two training studies | 0 | not applicable | not evaluated |
| Design meta-regression | not_qualified, design provenance gate | 0 | not applicable | not evaluated |
| Descriptive ATLAS | not_qualified, design provenance gate | 0 | not applicable | not evaluated |

Population-sensitivity output: `results/microcredit_population_sensitivity_v1/`.
Three held-out fits, each with two training studies:

| Method | Execution status | Computed targets | Released at delta=0.20 | Noisy-reference relation |
|---|---|---:|---:|---|
| Fixed effect | computed | 3 | 0 | 1 contains_full, 2 partial_overlap, 0 disjoint |
| Training range | computed | 3 | 0 | 0 contains_full, 3 partial_overlap, 0 disjoint |
| Random effects | not_identified, insufficient frozen degrees of freedom | 0 | not applicable | not evaluated |
| Design meta-regression | not_qualified, design provenance gate | 0 | not applicable | not evaluated |
| Descriptive ATLAS | not_qualified, design provenance gate | 0 | not applicable | not evaluated |

Every computed rule also refuses at all four frozen tolerances 0.10, 0.20,
0.40 and 0.80. Released-target risk is **undefined**, represented by an empty
CSV field. It is not zero. Uncomputed methods are not counted as successful
refusals. Primary fixed-effect mean width is 34.516752 and mean point error
15.341040. Sensitivity fixed-effect mean width/error are 21.225352/8.311435;
training-range mean width/error are 13.059176/11.643268. These are descriptive
diagnostics against noisy references, not inferential performance estimates.

The saved sign-disagreement counts are 0 for primary fixed effect, 2 for
sensitivity fixed effect and 2 for sensitivity training range. The runner
records zero-valued predictions or references as no sign disagreement; the
published rounded Mexico effect is zero. These counts must retain that
zero/tie convention and do not establish reliable sign transport.

All five target perturbations change the held-out effect and SE. The zero
Mexico value receives a nonzero sentinel. Saved prediction, radius, width
and release values are unchanged, with maximum change zero. Qualification
and design records are fixed in this test. It demonstrates numerical
target-effect/SE non-use in prediction, not outcome-blind design coding.
The fits overlap in training data; five fits across these two analyses are
not five independent experimental repetitions.

## Run identity and independent verification

| Artifact | SHA-256 |
|---|---|
| Source specification | `0f75ec5d315fb1bfe83b0e5db07c559b60b479e8dcba80ee808ea97a782f1b82` |
| Primary input | `5d8838a9a4a79844428cf294929750997e3f1653c58bd5a47665d70443d8e641` |
| Sensitivity input | `743b78ab4e1c6df2f9f5b4a7c420e20a67aec8bcc282cccfd140483a1f26b811` |
| Runner | `191de90adb37f68dd1e967ccf8ba9e948007a094d6a954c6a1e05ff7b0f1d360` |
| Primary run manifest | `5d8a161fb3302e1b513e7342372527f8fb36c9fe6c97fa7bedf27b5c8b1b3b3d` |
| Sensitivity run manifest | `e94279d32c34cf70595f0c7cbacf4a473c65daa3c3c1147b8604a7e878b99f8c` |

Each run manifest records protocol hashes, input/runner hashes, dependencies,
Git HEAD plus dirty status, and all output hashes. The execution used a
reviewed working tree based on HEAD `0b33a55d2bb2796397d256234a985af8fdf5af71`;
the commit alone does not identify these uncommitted accepted files.

`python -B tools/test_microcredit_loso_pilot.py` executed 9 tests and passed.
`tools/verify_microcredit_published_run.py` independently uses Decimal for
conversion and Python's standard-library normal quantile and arithmetic for
the saved estimates/intervals. Both runs passed, with maximum arithmetic
difference 7.11e-15. Input, protocol and output hashes match. The old input
and old result directory were preserved in the local audit, not overwritten.

Reproduce into new destinations:

```bash
python -B tools/build_microcredit_published_inputs.py --output reproduced/published-inputs
python -B tools/run_microcredit_loso_pilot.py --input data/microcredit_published_v1/primary.csv --output reproduced/microcredit-primary
python -B tools/run_microcredit_loso_pilot.py --input data/microcredit_published_v1/population_sensitivity.csv --output reproduced/microcredit-population-sensitivity
python -B tools/verify_microcredit_published_run.py --run results/microcredit_primary_published_v1
python -B tools/verify_microcredit_published_run.py --run results/microcredit_population_sensitivity_v1
```

## Claim and submission boundary

The accepted contribution is an auditable, source-corrected descriptive
feasibility and refusal exercise. It exposes the effects of population
qualification and very small training archives. It does not validate ATLAS
on real microcredit mechanisms: seven coordinates, especially the timing and
planned-versus-realized interpretation of `loansize_percentincome`, have not
passed source adjudication. No human outcome-blind double code or study-level
data-use/ethics authorization is certified here.

No independent real calibration archive exists. Nineteen independent
calibration interventions is only the finite 95% rank floor, not proof of
stable coverage; two or three study records do not satisfy it. Noisy RCT
estimates are not causal truth. This record supports no real joint 95%
coverage, no superiority ranking, and no claim that the complete matched
ExAtlas procedure has been run.
