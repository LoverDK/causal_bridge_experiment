# Author response: real cross-intervention validation

Date: 2026-09-25

This response addresses the reviewer concern that the paper's central
operational claim requires real mechanism sets `U_i` constructed from design
and implementation information, an independent calibration archive, and a
careful causal reference for a held-out intervention.

## 1. Response to the reviewer

We agree with the reviewer about the evidence boundary. The new experiments
address three narrower concerns. The cross-effect-family Many Labs 2 audit
tests external-validity stress under a fully held-out family split and adds
named baseline procedures. The joint mechanism-set calibration audit tests the
calibration protocol, including its failure under proxy shift, on labelled
synthetic errors. The NSW extension uses real covariates and the original
random assignment in a semisynthetic audit with known potential outcomes.

These additions do not establish that a real cross-intervention archive
provides valid `U_i`, that a real independent calibration archive calibrates
those sets, or that a real trial reveals noise-free individual causal truth.
We have therefore kept the claim conditional: real deployment requires a
separate, outcome-blind mechanism-coding and calibration study. The manuscript
now labels Many Labs 2 as an external-validity/noisy-reference benchmark, the
mechanism audit as a labelled synthetic calibration audit, and NSW as a
within-trial semisynthetic truth audit. None is presented as real
cross-intervention mechanism calibration.

We will use microcredit expansion as the first real-data pilot. The pilot is a
feasibility and protocol test until enough independent interventions are found
for the finite-sample calibration gate.

## 2. Data inventory and evidence status

### Official sources checked

| Source | Verified | Reasonable inference | Not verified |
|---|---|---|---|
| [AEA article page](https://www.aeaweb.org/articles?id=10.1257/app.20170299) | Meager (2019), AEJ: Applied Economics 11(1), pp. 57--91, DOI `10.1257/app.20170299`; the abstract says the analysis covers seven randomized experiments and compares economic intervention features with evaluation protocols. The page lists both the replication package and supplemental appendix. | The seven studies are the intended study-level units in the published synthesis. | Individual-level files, file names, permissions, and per-study sample sizes are not established by the article page. |
| [AEA Supplemental Appendix](https://www.aeaweb.org/articles/materials/10055) | The official PDF is reachable. It has 20 pages. Table B.1 lists Mexico, Mongolia, Bosnia, India, Morocco, Philippines, and Ethiopia. Table C.2 maps the seven study units to Angelucci et al. (2015), Attanasio et al. (2015), Augsburg et al. (2015), Banerjee et al. (2015), Crépon et al. (2015), Karlan and Zinman (2011), and Tarozzi et al. (2015). Table C.1 reports outcome observation counts across all sites in USD PPP per two weeks: profit 36,041; revenues 40,267; expenditures 40,267; consumption 35,793; consumer durables 8,737; temptation goods 30,706. Figure B.1 lists study-level predictors including control mean, randomization unit, target, women, APR, market saturation, promotion, collateralisation, and loan size. | The original analysis used harmonized outcome data and study-level covariates. The listed predictors are plausible starting fields for a mechanism dictionary. | The appendix does not prove that every implementation field needed by `U_i` is available, and its aggregate `N` values are not per-study participant counts. |
| [OpenICPSR DOI landing page](https://www.openicpsr.org/openicpsr/project/116357/version/V1/view) plus the user-supplied local download | The local archive `116357-V1.zip` has SHA-256 `1EC66E45ED401C7CC476548B0AE77DF0AF765942D7D8914202797D6FA4C61BFE`. It contains 306 files: 95 `.dta` files, one cleaned `microcredit_project_data.RData`, 12 nested source ZIPs, R/Stata/Stan code, readmes, survey material and PDFs. Study-specific directories or source packages are present for all seven published units. | The cleaned object and study files make an outcome-blind inventory and estimand audit feasible. The package `data/README.md` says the cleaned input was compiled from seven online datasets and does not import every available variable. | The archive inventory does not establish that all original files can be reused for a new linkage, that every implementation document is present, or that the seven records share the invitation-ITT estimand. Study-specific terms and governance still require review. |
| [DataCite DOI metadata](https://api.datacite.org/dois/10.3886/E116357V1) | The record identifies a 2019 ICPSR dataset, version 1, related to the article DOI. The metadata exposes `rightsList=[]`, empty `sizes` and `formats`, `contentUrl=null`, and no file inventory. The local package root additionally contains `LICENSE.txt`, which states Modified BSD for code and CC BY 4.0 for databases, images, tables and text. | The package-level license supplies attribution terms for material covered by that license. | DataCite and the root license do not by themselves settle upstream trial-file restrictions, consent, ethics, confidentiality, or every proposed use. |

The seven verified candidate units are:

| Candidate unit | Country | Published study label in the official appendix | Current status |
|---|---|---|---|
| 1 | Mexico | Angelucci et al. (2015) | Candidate study unit; package and estimand details not yet inventoried |
| 2 | Mongolia | Attanasio et al. (2015) | Candidate study unit; package and estimand details not yet inventoried |
| 3 | Bosnia | Augsburg et al. (2015) | Candidate study unit; package and estimand details not yet inventoried |
| 4 | India | Banerjee et al. (2015) | Candidate study unit; package and estimand details not yet inventoried |
| 5 | Morocco | Crépon et al. (2015) | Candidate study unit; package and estimand details not yet inventoried |
| 6 | Philippines | Karlan and Zinman (2011) | Candidate study unit; package and estimand details not yet inventoried |
| 7 | Ethiopia | Tarozzi et al. (2015) | Candidate study unit; package and estimand details not yet inventoried |

The authorized local download has now completed. We preserve it locally,
record the DOI, version, license text and SHA-256 hash, and publish only
metadata, code, and permitted summaries. We will not put raw data into GitHub.
The inventory is recorded in
`MICROCREDIT_OPENICPSR_INVENTORY_20260925.md`.

## 3. Comparable estimand

### Primary estimand

For study `i`, let `A_i=1` denote randomized assignment to an offer,
eligibility, promotion, or other access-expansion invitation that is the
closest available design analogue to receiving microcredit services. Let
`A_i=0` denote the contemporaneous usual-service or no-expansion control. The
primary effect is the invitation ITT

`tau_i(h,g) = E[Y_i(h,g) | A_i=1] - E[Y_i(h,g) | A_i=0]`,

where `g` is a predeclared outcome family and `h` is a predeclared follow-up
horizon. Treatment uptake, loan receipt, repayment, and treatment-on-the-treated
effects are not silently substituted for the invitation ITT.

The first analysis will keep two outcome families separate: household business
outcomes and household consumption. The candidate scale is the harmonized
two-week USD-PPP scale used in Table C.1 of the appendix, with a standardized
within-study effect as a companion scale. The final primary outcome and horizon
will be frozen only after the inventory, before held-out target outcomes are
opened. If no common raw scale is defensible, the standardized analysis becomes
the declared estimand and raw-scale results remain study-specific.

### Inclusion rule

We include a study in a pooled stratum only if all of the following can be
matched or deterministically normalized with an auditable rule:

- the randomized treatment is an access/offer/eligibility expansion rather
  than a purely observational borrower comparison;
- the control is a declared usual-service/no-expansion condition, or its
  alternative credit service is explicitly represented as a separate control
  stratum;
- the randomized population and catchment are recorded, including eligibility
  and whether the unit is a person, household, village, or branch;
- the outcome definition and measurement window map to the declared outcome
  family and horizon;
- the effect estimate is an intention-to-treat contrast with a standard error,
  covariance, or a reproducible randomization analysis.

Different countries or loan products are not automatic exclusion criteria.
They become study-level mechanism coordinates or predeclared strata when the
estimand remains the same. A different control service, incompatible outcome,
unresolvable horizon, or non-ITT estimand is analysed separately or excluded
from the transported point estimate. We will not harmonize by label alone.

## 4. Real construction of `U_i`

Each study receives a versioned, outcome-blind design/implementation record.
Candidate coordinates are:

| Coordinate class | Examples | Use in primary `Gamma(Z) -> U` |
|---|---|---|
| Design | product type; planned loan amount and price; APR; repayment frequency; grace period; individual versus group liability; collateral; eligibility rule; randomization unit; target population; planned duration | Primary mechanism proxy, measured before outcomes |
| Delivery and implementation | lender/channel; application and approval process; promotion intensity; planned service availability; fidelity checklist; scheduled follow-up; independent process audit | Eligible only when recorded without target outcomes; report a sensitivity analysis excluding post-assignment process fields |
| Baseline context | prior borrowing; baseline credit access; business ownership and size; local market access/saturation; baseline income; share of women; pre-intervention moderators | Pre-treatment context coordinates and separate effect-modifier analysis |
| Post-treatment variables | realized take-up; amount actually received; repayment; endline business activity; post-assignment outcomes or target-effect labels | Excluded from the primary mechanism set; may be reported descriptively after release decisions |

The coding protocol is:

1. Freeze a data dictionary, units, missingness codes, measurement date, source
   document, and allowed categories before any target effect is read.
2. Have two coders independently extract the fields from protocols, manuals,
   baseline instruments, and process documents. Coders do not see target
   effects or target outcome files.
3. Resolve disagreements with a prespecified rule; retain both raw codings,
   the adjudication record, and an inter-coder agreement table.
4. Have an independent expert audit a prespecified subset against the most
   complete implementation material. Record missingness and measurement error
   rather than imputing an apparently precise mechanism.
5. Map numeric fields to declared units and categorical fields to allowed
   sets. A candidate construction is a scaled joint box/ellipsoid around the
   coded vector, with a study-level measurement-error score. The final map,
   scale matrix, and sensitivity values for `L`, `H`, and `eta` are frozen in
   the split manifest.

The independent calibration archive uses expert or more complete reference
codings for separate interventions. It calibrates a joint maximum score across
all coordinates and all entities in the candidate menu. Marginally calibrating
each coordinate or each source separately is not treated as sufficient for the
archive-wide certificate.

## 5. Independent calibration and sample size

The independent unit is a trial, project, or intervention program. A participant
split, a subgroup split, or a site split inside one RCT does not create new
calibration units. A multi-site program counts as multiple units only if the
design and intervention are independently defined and the independence claim
is recorded.

The minimum formal split is:

- development/training studies for choosing the fixed dictionary and fitting a
  transport rule;
- an intervention-disjoint calibration archive for the joint mechanism score;
- one or more final held-out intervention targets whose outcomes remain sealed
  until the prediction and release decision are frozen.

For a split rank rule with target coverage `1-alpha`, the calibration rank is
`k = ceil((n_cal + 1)(1-alpha))`. At 95% nominal coverage, `n_cal=19` is the
smallest size for which the rank is finite under this convention. This is only
a mathematical non-vacuity floor. It does not make empirical coverage stable,
and it leaves no room for a useful development set or multiple targets.

Seven candidate studies cannot provide 19 independent calibration units. With
seven, every result must be labelled pilot/descriptive; no distribution-free
95% real calibration claim is made. A realistic confirmatory target is at least
25--40 independent interventions overall, with at least 19 held out for
calibration and a separate development/target allocation.

The expansion search will use official repository and author channels: ICPSR/
OpenICPSR, AEA data links, J-PAL and 3ie data portals, World Bank microdata
catalogues, Harvard Dataverse, and trial registries for design metadata. Each
candidate is screened for invitation ITT, outcome/horizon compatibility,
outcome-blind implementation records, independent intervention status, and
data-use permission. A registry entry or published effect is not treated as a
mechanism archive unless its source documents support the coding protocol.

## 6. Causal reference without overclaiming truth

An ordinary held-out RCT identifies an ITT with sampling uncertainty but does
not reveal both potential outcomes for any person. It therefore cannot supply
noise-free individual causal truth. For target `*`, we will retain the target
randomization estimate and a prespecified confidence or randomization interval
`R_*` only after the transport estimate and release decision are frozen.

We report three reference categories:

- **definite reference-compatible:** the ATLAS prediction interval contains the
  full `R_*` interval;
- **definite discrepancy:** the two intervals are disjoint;
- **indeterminate:** the intervals partially overlap.

The point estimate is not used as a noiseless truth label. Exact causal-truth
coverage is evaluated only in the existing semisynthetic experiments with a
known response surface. The real microcredit audit can support statements
about compatibility with an independently randomized causal reference,
selective refusal, and robustness to study-level shift; it cannot support a
claim of exact individual-level causal-truth coverage.

## 7. Fair baselines and preregistered metrics

Every procedure sees the same source summaries, design/implementation proxies,
split manifest, and target information boundary. No method sees the held-out
target outcome before release. The candidate panel is:

- fixed-effects and random-effects meta-analysis;
- transport meta-regression using only frozen mechanism coordinates;
- robust range/partial-identification intervals;
- study-level split conformal and, where justified, family-level conformal;
- ATLAS with jointly calibrated mechanism sets and the same release tolerance.

The threshold, confidence level, outcome families, horizons, and estimand are
fixed before target outcomes are opened. We preregister:

- all-target reference compatibility and its uncertainty-aware interval;
- definite-discrepancy rate among released targets, with the indeterminate
  category reported separately;
- release and refusal rate;
- mean and distribution of interval width;
- risk among released targets, reported with reference uncertainty;
- sign disagreement and sign indeterminacy;
- bridge selections, participant cost, and refusal cost where bridging is used;
- calibration-shift sensitivity, including proxy perturbations and target-domain
  shift.

With few studies, we report study-level counts, exact or Wilson intervals where
appropriate, leave-one-study-out sensitivity, and a predeclared small-sample
warning. We do not use a fitted meta-regression or a conformal radius as if it
had many independent observations. Any threshold sweep is a risk--release
frontier, not a single post-selected result.

## 8. Concrete revision plan

| Priority | Work and required data | Responsible process | Verifiable artifact | Risk and time | Claim strengthened after completion |
|---|---|---|---|---|---|
| 1 | Inventory the authorized Meager package; obtain design documents, codebook, file metadata, terms, and hashes | One analyst inventories; a second person checks the manifest | `MICROCREDIT_OPENICPSR_INVENTORY_20260925.md`, license/access matrix, SHA-256 manifest | Package inventory is complete; study-level terms and codebook review remain; 1--3 days for the next audit | The paper can state exactly what the seven-study pilot contains |
| 2 | Freeze estimand eligibility and code the seven studies from outcome-blind sources | Two independent coders and an adjudicator; no target effects exposed | estimand matrix, mechanism dictionary v1, coder disagreement log | Missing manuals and incompatible endpoints are likely; 1--2 weeks | Reproducible pilot construction of design/implementation proxies |
| 3 | Run the seven-study pilot with ATLAS and all named baselines under leave-one-study-out splits | Analysis script reads only frozen source records and reveals target outcomes after release | pilot split manifest, `U_i` records, reference-interval categories, risk--release table | Very high uncertainty; no 95% calibration claim; 1 week | A bounded feasibility result and a falsification of leakage or post-selection errors |
| 4 | Expand the archive to at least 19 calibration interventions and preferably 25--40 total | Data manager contacts repositories/authors; PI confirms DUA/ethics; no raw data redistribution | candidate registry, approvals, data-use records, independent calibration manifest | Data access and estimand mismatch may take months; weeks to months | The first defensible real finite-sample calibration experiment |
| 5 | Run the preregistered held-out target audit and bridge-cost comparison | Freeze all thresholds and target seals before target outcomes are opened | preregistration, release log, uncertainty-aware audit report, reproducible code | Requires independent target and governance approval; weeks after data access | A real causal-reference audit with an honest evidence boundary |

### Immediately executable without new restricted data

We can create the inventory schema, eligibility matrix, mechanism codebook,
split-manifest template, and synthetic small-sample stress simulations now. We
can also run a seven-unit descriptive leave-one-study-out pilot if authorized
study-level summaries and design records are supplied. These outputs must be
labelled feasibility/pilot and cannot be used as a 95% real calibration claim.

### Requires new access, permission, or governance

Package file inventory, raw-data inspection, independent expert reference
codings, an independent calibration archive, additional intervention studies,
and held-out target outcomes require authorized access. Any linkage of
individual records, new data collection, or use beyond the original consent
must be reviewed under the applicable DUA and ethics/IRB process. If only
published estimates and standard errors are available, the study can still run
an external prediction pilot, but not a real mechanism-set calibration audit.

## 9. Proposed manuscript limitation paragraph

> Our empirical evidence currently separates four claims. The Many Labs 2
> source-holdout and cross-effect-family analyses evaluate leakage-free
> external-validity stress and named baseline comparisons, but their public
> summaries contain noisy study-level references rather than real mechanism
> sets. The NSW extension uses real pretreatment covariates and randomized
> assignment, but its exact causal reference is generated by a frozen
> semisynthetic response surface within one intervention. The mechanism-set
> calibration experiment audits the joint calibration protocol under labelled
> synthetic proxy errors and documents its failure under proxy shift; it is not
> a real cross-intervention calibration study. The Meager microcredit archive
> is currently a seven-study feasibility source. The authorized local package
> contains a cleaned project object, many study-level Stata files, source
> packages, code and some survey/readme material; its package-level license is
> recorded in the inventory, but study-specific reuse and implementation-field
> coverage still require review. A future real audit must freeze an invitation-ITT
> estimand, construct `U_i` from design and implementation information without
> target-outcome access, calibrate those sets on independent interventions, and
> evaluate held-out randomized targets against sampling-uncertain causal
> references. Ordinary trials do not reveal individual-level noise-free causal
> truth, so exact causal-truth coverage remains a semisynthetic result rather
> than a claim about the real microcredit archive.
