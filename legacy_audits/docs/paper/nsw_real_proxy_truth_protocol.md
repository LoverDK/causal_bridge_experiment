# NSW Real-Proxy Calibration and Semisynthetic Truth Protocol

## Scope

This audit uses the public National Supported Work (NSW) job-training trial.
It is one randomized treatment contrast, not a collection of independent
interventions. The audit therefore separates (i) an outcome-blind calibration
of observed baseline-covariate profile proxies on disjoint participant pools
from (ii) a semisynthetic causal-truth experiment. Neither component is called
real cross-intervention mechanism calibration.

## Outcome-blind covariate-proxy audit

The runner verifies the pinned `nsw_dw.dta` SHA-256 before reading the eight
prespecified pretreatment covariates and the original randomized assignment.
Within each treatment arm, one fixed seed assigns disjoint participants to a
development pool, a calibration pool, and a validation pool in proportions
40/30/30. Outcomes are not read by this component. Scaling is estimated only
from the development pool.

Calibration and validation entities each contain four treated and four
control participants, sampled without replacement within their respective
participant pool. Half of each entity supplies its proxy mean; all eight
observed baseline profiles define that entity's finite-sample reference mean.
The score is the maximum absolute standardized-coordinate difference. A
split-conformal order statistic is calibrated on the calibration entities and
evaluated once on the unit-disjoint validation entities. The manifest records
the participant IDs in each pool and entity so overlap can be checked.

This estimates repeatability of an observed-covariate profile proxy under the
NSW participant distribution. It does not identify latent mechanisms, test
transport across interventions, or provide archive-level simultaneous
coverage across 11 mechanism sets. Calibration entities are independent at
the participant level within this one trial; they are not an independent
study-level calibration archive.

## Semisynthetic causal-truth audit

The second component reuses the frozen NSW source/target participant split and
the original treatment assignment. Three response surfaces are frozen in
code. For each replicate, a shared unit-level noise draw defines both
potential outcomes, `Y(0)=mu(X)+epsilon` and `Y(1)=mu(X)+tau(X)+epsilon`.
Thus each target neighborhood has an exactly known finite-population causal
effect equal to its mean `tau(X)`. Observed outcomes follow the original NSW
assignment. The target outcome and target effect are withheld from every
prediction method; they are joined only for scoring. A target-effect flip
audit must leave predictions and interval endpoints unchanged.

The results support statements about performance with real NSW baseline
covariates and assignment under the declared semisynthetic outcome surfaces.
They do not establish noise-free causal truth in the observed NSW outcomes.

## Reproduction

From the repository root, run:

```powershell
python legacy_audits/scripts/run/run_nsw_real_proxy_truth.py --repetitions 100
```

Outputs are written to a new versioned directory under
`legacy_audits/results/extensions/nsw_real_proxy_truth/`; prior NSW outputs are
not overwritten. The manifest pins the protocol, runner, implementation,
input hash, environment, seed, and output hashes.
