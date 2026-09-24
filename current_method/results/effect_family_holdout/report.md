# Many Labs 2 cross-effect-family holdout audit

- Pinned source commit: `acef63fc397b8dce7f0b00f863bcea78d324bea8`; SHA-256 `78b3432bebb798595ebb08ee10fb68d3f6f59cd5e0ab49606cfb6835eb226406`.
- Eligible target families frozen before scoring: `Hauser, Huang, Miyamoto, Ross, Savani`.
- Included records: 28/32; target studies: 10.
- The target `ESCI.d` is read only for the final score. Predictions and release/refusal decisions use training records, target N, and the pre-existing WEIRD/NONWEIRD metadata flag.

## Methods

`fixed_effects` and `random_effects` are inverse-variance pooled and DerSimonian--Laird baselines. `context_fixed_effects` pools the same WEIRD context when at least three training records exist. `robust_training_range` reports the training effect envelope enlarged by a conservative N-only sampling allowance. `family_split_conformal` uses leave-one-family-out residuals within the training pool.

## Results

| Method | threshold | release | coverage all | coverage released | MAE released | sign error released | width released |
|---|---:|---:|---:|---:|---:|---:|---:|
| context_fixed_effects | 0.20 | 0.200 | 0.400 | 0.000 | 1.084 | 0.000 | 0.202 |
| context_fixed_effects | 0.40 | 0.400 | 0.400 | 0.000 | 1.210 | 0.500 | 0.473 |
| context_fixed_effects | 0.60 | 0.800 | 0.400 | 0.375 | 0.741 | 0.250 | 0.671 |
| context_fixed_effects | 0.80 | 1.000 | 0.400 | 0.400 | 0.772 | 0.200 | 0.840 |
| context_fixed_effects | 1.00 | 1.000 | 0.400 | 0.400 | 0.772 | 0.200 | 0.840 |
| family_split_conformal | 0.20 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 0.40 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 0.60 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 0.80 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 1.00 | 0.000 | 0.800 | NA | NA | NA | NA |
| fixed_effects | 0.20 | 0.200 | 0.500 | 0.500 | 1.084 | 0.000 | 0.199 |
| fixed_effects | 0.40 | 0.400 | 0.500 | 0.250 | 1.210 | 0.500 | 0.472 |
| fixed_effects | 0.60 | 0.800 | 0.500 | 0.500 | 0.752 | 0.250 | 0.670 |
| fixed_effects | 0.80 | 1.000 | 0.500 | 0.500 | 0.785 | 0.200 | 0.839 |
| fixed_effects | 1.00 | 1.000 | 0.500 | 0.500 | 0.785 | 0.200 | 0.839 |
| random_effects | 0.20 | 0.000 | 0.900 | NA | NA | NA | NA |
| random_effects | 0.40 | 0.000 | 0.900 | NA | NA | NA | NA |
| random_effects | 0.60 | 0.000 | 0.900 | NA | NA | NA | NA |
| random_effects | 0.80 | 0.000 | 0.900 | NA | NA | NA | NA |
| random_effects | 1.00 | 0.200 | 0.900 | 0.500 | 1.084 | 0.000 | 1.601 |
| robust_training_range | 0.20 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_training_range | 0.40 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_training_range | 0.60 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_training_range | 0.80 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_training_range | 1.00 | 0.000 | 1.000 | NA | NA | NA | NA |

Leakage audit maximum prediction change after flipping all held-out target effects: `0`; maximum radius change: `0`.

## Boundary and next step

This experiment adds real cross-effect-family external-validity evidence and tests refusal, interval width, noisy-reference coverage, absolute error, and sign error without target-outcome leakage. It does not satisfy the strongest original requirement: the public summary has no independently audited real mechanism sets U_i, no real calibration archive frozen before target outcomes, and no causal truth for the held-out effects. The next feasible experiment is a preregistered or newly collected cross-intervention archive with design metadata defining mechanism proxies before outcomes are read, an independent calibration split, and the same family-level holdout plus transportability, hierarchical, robust partial-identification, and conformal baselines.
