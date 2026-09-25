# Microcredit metadata audit

Date: 2026-09-25. This audit reads archive metadata and variable names only.
It does not estimate effects and does not use target outcomes to construct a
mechanism set.

## Findings

The downloaded package contains enough structured material to begin an
outcome-blind design audit. Six study files expose a recognisable assignment or
treatment field in the inspected files; Tarozzi's official replication readme
also documents the randomization unit and treatment-arm variables. The
Karlan--Zinman source package exposes credit-score and randomization-tag fields
but no simple treatment variable in the inspected data file. It therefore
requires a separate design decision before it can enter the invitation-ITT
stratum.

The reproducible label extractor `tools/inspect_microcredit_metadata.py` was
run against the local archive with `pyreadstat` in header-only mode. It wrote
884 variable-name/label records to `microcredit_variable_label_audit.csv`.
The file contains no individual values; it is intended as the starting sheet
for the second coder and adjudicator.

Row counts below are file row counts, not participant sample sizes. Some files
pool baseline/endline waves, include individual records, or contain repeated
household records. They must not be used as the final sample-size table.

## Study-level metadata

| Study | Inspected file | Rows x columns | Assignment/treatment fields | Design/proxy fields visible in metadata | Documentation | Pilot status |
|---|---|---:|---|---|---|---|
| Angelucci et al. (Mexico) | `angelucci_et_al_2015.dta` | 21,523 x 124 | `Treatment`, `BTreatment` | `BE_Q21_anyloan`, `BE_foodconsump`, `business_before`, `survey` | Study readme PDF and source code present | Candidate; treatment/control definition and horizon need design coding |
| Attanasio et al. (Mongolia) | `attanasio_processed_for_rm_analysis.dta` | 2,109 x 2,062 | `treatment`, `treated`, `treated_g`, `treated_i`, `treatgloan`, `treatiloan` | `BLtot_amount_loans`, `BLdum_any_loan`, `loan_baseline`, `followup`, loan-use fields | Official study readme text and analysis outputs present | Candidate, but multiple arms require a prespecified invitation-ITT contrast |
| Augsburg et al. (Bosnia) | `BL---SECTION-2---Loans-cl.dta` | 1,240 x 94 | `treatment`, `ebrd_selected_loan` | `randomisation_date`, `randomisation_time`, baseline loan and other-credit fields | Official study readme text and analysis code present | Candidate; follow-up linkage and target horizon need coding |
| Banerjee et al. (India) | `2013-0533_data_endlines1and2_stata12.dta` | 6,863 x 187 | `treatment` | `anyloan_1`, `anyloan_amt_1`, `credit_index_1`, `income_index_1`, `consumption_index_1` | Study readme PDF and source package present | Candidate; baseline/endline wave mapping needs coding |
| Crépon et al. (Morocco) | `endline_baseline_outcomes.dta` | 5,524 x 518 | `treatment`, `wave`, `random5_final` | `admin_loanlength`, `admin_1stloan_amt`, `admin_1stloan_group`, `admin_1stloan_indiv`, `_bl` baseline fields | English/French endline survey instruments and source code present | Candidate; treatment assignment and multiple waves need coding |
| Karlan and Zinman (Philippines) | nested `1200138sdataset_clean.dta` | 1,978 x 1,953 | No simple `treatment` field found | `css_randomizetag`, `css_creditscorefinal`, `css_loandecision`, loan terms and collateral fields | Paper/code source ZIP present | Design review required; do not silently include in invitation-ITT pool |
| Tarozzi et al. (Ethiopia) | `TarozziEtAlReplicationFiles/data.dta` | 12,675 x 336 | `patypen`, `patypeactual2`, `D`, `T`, `D_MF`, `D_Both`, `D_FP`, `D_None` | `time`, `mf_coll`, `mf_borrow`, loan balances, revenues and costs | Official replication readme PDF present | Candidate; randomized PA-level multi-arm design needs explicit contrast |

## Interpretation boundary

The presence of a variable named `treatment`, `D`, or `T` does not prove that
the variable represents the same intervention. It may encode a multi-arm offer,
actual take-up, an interaction with follow-up, or a different credit product.
The next coding pass must read the study design documents and value labels,
then freeze one invitation/eligibility ITT contrast, population, outcome family
and horizon before any target outcome is opened.

The available baseline and implementation-related fields are promising for a
mechanism dictionary. They are not yet an independent calibration archive: the
seven records are still too few for a stable distribution-free 95% calibration
claim, and no expert reference coding or independent intervention split has
been completed.

## Next executable analysis

1. Extract only variable labels, value labels, study readmes and design tables
   for the seven candidates.
2. Build a two-coder estimand matrix and mark each field as design, baseline,
   implementation, post-treatment or outcome-derived.
3. Freeze a seven-study leave-one-study-out feasibility split. Use it only to
   test compatibility, leakage controls and descriptive refusal behaviour.
4. Keep Karlan--Zinman separate until its credit-score experiment can be shown
   to identify the declared invitation-ITT estimand.
