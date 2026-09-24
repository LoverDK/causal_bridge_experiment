# Manuscript revision record

The integrated manuscript source is maintained in the adjacent Overleaf
working copy, not in this experiment archive. This file makes the paper-facing
changes reviewable from GitHub and links them to the saved evidence.

## Source

`_overleaf_current_20260924/causal_lab_proposal_subpapers_tex_iclr2027/01.tex`

Title: *When Can Experiments Be Reused? Certified Transport, Refusal, and
Causal Bridging*.

## Changes applied

### Abstract and contribution hierarchy

The abstract now makes selection-safe causal reuse the central object. The
refusal region and bridge policy are described as outputs/extensions of the
same certificate. The bridge guarantee is explicitly restricted to the
nonadaptive linear-Gaussian model.

The contribution list now has this order:

1. selection-safe causal reuse certificate;
2. refusal object and identification limits;
3. bounded bridge-design extension;
4. auditable evidence boundary.

### New empirical subsection

The experiments section now reports the independent outcome-blind calibration
audit. It states the exact universe (4 archive sources, 6 candidate bridges, 1
target), calibration size (199), test size (2,000), dimension (2), and
`eta=0.05`, together with the saved coverage values:

| Setting | Rule | Joint coverage | Per-entity coverage |
|---|---|---:|---:|
| Nominal | Joint row-wise maximum | 0.951 | 0.9955 |
| Nominal | Marginal radius reused jointly | 0.544 | 0.9465 |
| 1.5x test proxy shift | Joint row-wise maximum | 0.348 | 0.9092 |
| 1.5x test proxy shift | Marginal radius reused jointly | 0.0275 | 0.7294 |

The subsection explicitly says that these are labelled synthetic-error results
and do not prove real cross-intervention calibration.

### Boundary wording

Many Labs 2 remains a standardized-intervention source-holdout benchmark, and
NSW remains a within-trial reconstruction stress test. Neither is described as
real mechanism-set calibration. The manuscript keeps the requirement that a
future real study freeze `Gamma`, `L`, `H`, and the calibration split before
target outcomes are inspected.

## Evidence and reproduction mapping

The new subsection is backed by:

- `current_method/run_mechanism_calibration.py`
- `current_method/atlas_new/mechanism_calibration.py`
- `current_method/results/mechanism_calibration/summary.csv`
- `current_method/docs/mechanism_set_calibration_protocol.md`

Reproduce with:

```bash
python reproduce.py calibration --output reproduced/calibration
```
