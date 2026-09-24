# All-family sensitivity panel under Many Labs 2 holdout

The panel uses the pinned author summary at commit `acef63fc397b8dce7f0b00f863bcea78d324bea8` (SHA-256 `78b3432bebb798595ebb08ee10fb68d3f6f59cd5e0ab49606cfb6835eb226406`), with every eligible family held out in turn.
There are 23 target families and 28 target studies; all 28 valid Cohen's d records are scored once.

This is a sensitivity analysis for the five-family panel. It is not a causal mechanism certificate: the references are noisy study-level standardized effects and the source contains no U_i labels or causal truth.

## Results

| Method | threshold | release | coverage all | coverage released | MAE released | sign error released | width released |
|---|---:|---:|---:|---:|---:|---:|---:|
| family_split_conformal | 0.20 | 0.000 | 0.929 | NA | NA | NA | NA |
| family_split_conformal | 0.40 | 0.000 | 0.929 | NA | NA | NA | NA |
| family_split_conformal | 0.60 | 0.000 | 0.929 | NA | NA | NA | NA |
| family_split_conformal | 0.80 | 0.000 | 0.929 | NA | NA | NA | NA |
| family_split_conformal | 1.00 | 0.000 | 0.929 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.20 | 0.000 | 0.964 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.40 | 0.000 | 0.964 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.60 | 0.000 | 0.964 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 0.80 | 0.000 | 0.964 | NA | NA | NA | NA |
| hierarchical_meta_analysis | 1.00 | 0.071 | 0.964 | 0.500 | 1.084 | 0.000 | 1.601 |
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
| transport_meta_regression | 0.20 | 0.000 | 0.929 | NA | NA | NA | NA |
| transport_meta_regression | 0.40 | 0.000 | 0.929 | NA | NA | NA | NA |
| transport_meta_regression | 0.60 | 0.071 | 0.929 | 0.500 | 1.084 | 0.000 | 1.078 |
| transport_meta_regression | 0.80 | 0.071 | 0.929 | 0.500 | 1.084 | 0.000 | 1.078 |
| transport_meta_regression | 1.00 | 0.071 | 0.929 | 0.500 | 1.084 | 0.000 | 1.078 |

Target-effect flip audit: maximum prediction change `0`, maximum radius change `0`.

## Interpretation

The all-family panel tests whether the original five-family conclusions are driven by target selection. It remains an external-validity stress test only. The next evidence step is a pre-registered cross-intervention archive with design-metadata mechanism proxies and an independent calibration split frozen before target outcomes.
