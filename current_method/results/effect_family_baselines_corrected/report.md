# Many Labs 2 corrected baseline panel under cross-effect-family holdout

The panel uses the pinned Many Labs 2 summary at commit `acef63fc397b8dce7f0b00f863bcea78d324bea8` (SHA-256 `78b3432bebb798595ebb08ee10fb68d3f6f59cd5e0ab49606cfb6835eb226406`), with the same five complete-family holdouts and ten targets as the external-validity audit.

## Baselines

- `transport_meta_regression`: weighted context meta-regression using the pre-existing WEIRD/NONWEIRD design metadata.
- `hierarchical_meta_analysis`: Normal-Normal random-effects predictive interval with DerSimonian--Laird heterogeneity.
- `robust_partial_identification`: training effect envelope plus an N-only sampling allowance.
- `study_split_conformal`: leave-one-`study.analysis`-out absolute residual calibration. The historical run grouped by `study.name`, which is the family label; this corrected run keeps study and family units distinct.
- `family_split_conformal`: leave-one-family-out residual calibration, the stricter family-level comparison.

## Results

| Method | threshold | release | coverage all | coverage released | MAE released | sign error released | width released |
|---|---:|---:|---:|---:|---:|---:|---:|
| family_split_conformal | 0.20 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 0.40 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 0.60 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 0.80 | 0.000 | 0.800 | NA | NA | NA | NA |
| family_split_conformal | 1.00 | 0.000 | 0.800 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.20 | 0.000 | 0.900 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.40 | 0.000 | 0.900 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.60 | 0.000 | 0.900 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.80 | 0.000 | 0.900 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 1.00 | 0.200 | 0.900 | 0.500 | 1.084 | 0.000 | 1.601 |
| robust_partial_identification | 0.20 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_partial_identification | 0.40 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_partial_identification | 0.60 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_partial_identification | 0.80 | 0.000 | 1.000 | NA | NA | NA | NA |
| robust_partial_identification | 1.00 | 0.000 | 1.000 | NA | NA | NA | NA |
| study_split_conformal | 0.20 | 0.000 | 1.000 | NA | NA | NA | NA |
| study_split_conformal | 0.40 | 0.000 | 1.000 | NA | NA | NA | NA |
| study_split_conformal | 0.60 | 0.000 | 1.000 | NA | NA | NA | NA |
| study_split_conformal | 0.80 | 0.000 | 1.000 | NA | NA | NA | NA |
| study_split_conformal | 1.00 | 0.000 | 1.000 | NA | NA | NA | NA |
| transport_meta_regression | 0.20 | 0.000 | 0.800 | NA | NA | NA | NA |
| transport_meta_regression | 0.40 | 0.000 | 0.800 | NA | NA | NA | NA |
| transport_meta_regression | 0.60 | 0.200 | 0.800 | 0.500 | 1.084 | 0.000 | 1.078 |
| transport_meta_regression | 0.80 | 0.200 | 0.800 | 0.500 | 1.084 | 0.000 | 1.078 |
| transport_meta_regression | 1.00 | 0.200 | 0.800 | 0.500 | 1.084 | 0.000 | 1.078 |

Target-effect flip audit: maximum prediction change `0`, maximum radius change `0`.

## Interpretation and next step

This panel closes the naming and implementation gap in the prior audit: transportability, hierarchical meta-analysis, robust partial identification, and conformal/selective baselines are now run under the same frozen family-level split. The ten targets are too few for a definitive method ranking, and held-out standardized effects remain noisy references. The central missing evidence is unchanged: no real mechanism sets U_i, independent real calibration archive, or causal target truth is available. The next feasible experiment is a pre-registered cross-intervention archive with design metadata frozen into mechanism proxies and a separate calibration split before target outcomes are read.
