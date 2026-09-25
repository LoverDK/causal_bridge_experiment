# Seven-study design evidence audit

Date: 2026-09-25. This is a source audit for the Meager OpenICPSR V1
package. It is not an effect estimate and does not certify a common estimand.
Raw records remain in the authorized local archive and are not committed.

## Evidence rules

We accept a design claim only when it is supported by a paper methods/design
section, an official replication readme, a labelled variable, or analysis code
with a precise path and line/section locator. A variable named `treatment`,
`D`, or `randomization` is not sufficient by itself. Where a source says that
the control group could receive another lender's credit, this is recorded as a
control-access/crossover feature rather than silently treated as zero exposure.

The table uses three statuses: **verified** (the source directly states the
claim), **inferred** (a cautious reading of labelled data/code, not enough for
confirmatory inclusion), and **unresolved** (the available package does not
establish the claim).

## Design table

| Study | Randomization unit and assignment | Treatment / control | Population and timing | Outcomes and data locations | Control access, compliance, implementation | Invitation-ITT status and unresolved items |
|---|---|---|---|---|---|---|
| Angelucci et al., Mexico | **Verified:** geographic cluster (neighborhood/town/contiguous towns) randomized to program placement; paper design section, `angelucci-et-al-2014-MicrocreditImpactsEvidence_preview.pdf`, pp. 11--14. `cluster` is labelled “Cluster”; `Treatment` and `BTreatment` are present in `data/microcredit-rct-data/angelucci_et_al_2015.dta`. | **Verified:** treatment clusters received access/promotion for Crédito Mujer; the paper's design text describes no promotion/access before data collection in controls (pp. 2--3). **Unresolved:** the paper/code do not make the exact meaning of `Treatment` versus `BTreatment` identical; the import script says interpretation of `BTreatment` was not confirmed (`data/import_organise_data_v7.R`, lines 74--75). | Potential borrowers in surveyed households; paper p. 4 reports endline timing at a mean of 27 months after expansion. | Profit `Q10_9_toprof` is labelled “Profits in the last 2 weeks”; revenues/expenses and consumption fields are in the DTA. The import script records `angelucci_timegap <- 27` (line 132), but this is a constructed summary, not an independent design document. | Other credit variables (`Q21_3_informal2`, `Q21_3_othformal`, `Q21_3_bank`, `Q21_3_othmfi`) are present. The paper notes control access/crossover; exact compliance for the assignment field is unresolved. | **Candidate, community access ITT.** Must use the paper's assignment field after resolving `Treatment`/`BTreatment`, and retain a control-access flag. Common outcome is not yet confirmed to be comparable to every other study's profit definition. |
| Attanasio et al., Mongolia | **Verified:** village/soum-level assignment to individual-loan, group-loan, or control arms; paper design section, `attanasio-et-al-2014-TheImpactsOfMicrofinanceE_preview.pdf`, pp. 9--13; `treatment` value labels are Control / Ind. Loan / Group Loan. | **Verified:** product offers are distinct arms; control villages are the no-lending arm in the design source. **Inferred:** the source data's `treatment` is assignment, while `treated` is a follow-up interaction and cannot replace assignment. | Rural eligible women/households in the sign-up sample; follow-up timing is represented by `followup` and `nmonths` in `attanasio_processed_for_analysis.dta`; the import script uses follow-up only and records 19 months (lines 145--146, 286). | `profit_j` is labelled “aggregated profit”; enterprise/income/consumption files are present. The import script labels the profit horizon as 1 year in its standardization table (line 746). | Loan and other-credit fields are present; the exact control access to non-study credit and realized take-up are not fully established from the inspected files. | **Candidate only as a predeclared arm-specific contrast:** group-loan offer vs control or individual-loan offer vs control. Do not collapse the two offers. The target population and common profit horizon need a final source check. |
| Augsburg et al., Bosnia | **Verified:** individual marginal-loan applicants randomized to a loan offer/approval decision; paper design section, `augsberg-2014-TheImpactsOfMicrocreditEv_preview.pdf`, pp. 6--8. `ebrd_selected_loan` is labelled “EBRD selected to receive a loan (Y/N)” and randomization date/time fields are present. | **Verified:** treatment is individual-liability MFI loan offer; controls were not to receive that MFI loan during the study period (paper pp. 6--8). Some assignment noncompliance/verification exceptions remain possible. | Marginal applicants screened by the MFI; follow-up is approximately 14 months in the paper and `augsberg_timegap <- 14` in the import script (line 403). | Business profit is assembled from follow-up business files; `profit`/income/consumption sections are in the package. The import script uses `bm_profit` and labels the profit horizon as 1 year (lines 314--327, 746). | Baseline other-credit and loan fields are present. Assignment is individual, not community access; exact noncompliance counts are not reconstructed here. | **Exclude from the community access stratum; retain as applicant-level offer ITT context.** It cannot be pooled with village/cluster expansion without changing the estimand. |
| Banerjee et al., India | **Verified:** neighborhood/slum area assignment to a Spandana branch rollout; `treatment` value labels are Control/Treatment and `areaid` is the cluster field. Design source: `banerjee-et-al-2014-TheMiracleOfMicrofinanceE_preview.pdf`, pp. 10--13. | **Verified:** treated areas received the branch/product rollout; control areas are the comparison areas. The package design text documents later MFI entry/crossover, especially for the later endline. | Poor but not poorest households in eligible Hyderabad areas; endline 1 and endline 2 are distinct. Data labels distinguish `bizprofit_1` (“Business profits (last 30 days, Rs.), endline 1”) and corresponding endline 2 fields. | `bizprofit_1`, `bizrev_1`, `bizexpense_1`, consumption and index fields are in `2013-0533_data_endlines1and2_stata12.dta`; the do-files use `reg ..., cluster(areaid)`. | `spandana_1`, `othermfi_1`, `anybank_1`, and informal-loan fields document access/crossover. The import code explicitly chooses first endline because later control access changes comparability (`data/import_organise_data_v7.R`, lines 412--415). | **Candidate, community access ITT only for endline 1.** Endline 2 is a separate horizon and is not pooled with endline 1. Sampling weights and area-clustered inference must be retained. |
| Crépon et al., Morocco | **Verified:** matched village pairs; `treatment` labelled “1 if treated village”, `paire` is pair ID, and the analysis code clusters by `demi_paire` (`DoFiles/Analysis_Oct2014.do`, lines 200--244 and 504). The paper describes 81 matched pairs. | **Verified:** treated villages received Al Amana promotion/access; paired controls were the comparison villages. | Rural households sampled from a high-borrowing-propensity frame plus a random frame; baseline/endline waves are explicitly retained. `wave` is survey round; endline construction uses `profit_total`. | `profit_total` is labelled “self-employment activities: total profit past 12 months (in MAD)”; outcome construction is in `DoFiles/OutcomeConstruction_endline_Oct2014.do`, and the main analysis keeps `treatment`, `paire`, `demi_paire`, `wave`, and sampling variables (`Analysis_Oct2014.do`, lines 201--244). | Administrative loan terms and other-formal/informal/MFI borrowing fields are present. Sampling probability is estimated and inverse-probability weights are capped at 10 in `Analysis_Oct2014.do`, lines 312--365. | **Candidate, matched-pair community access ITT**, with sampling-frame and wave restrictions frozen. It is not interchangeable with a simple unweighted individual RCT. |
| Karlan--Zinman, Philippines | **Verified:** marginal applicants randomized by credit-score decision windows; paper `karlan-and-zinman-2010-manila.pdf`, pp. 7--8. The nested source has `css_randomizetag`, `css_creditscorefinal`, and `css_loandecision`. | **Verified:** assigned approval/rejection of an individual first-time loan; this is not a village rollout. Exact mapping from `css_randomizetag` to the primary assignment field must be confirmed from the source code. | Marginally creditworthy first-time applicants; paper follow-up is roughly 11--22 months. | Nested `1200138sdataset_clean.dta` has loan terms, business/household outcomes and score fields; exact primary outcome/horizon mapping for a common profit estimand is unresolved. | Individual-loan compliance and post-assignment decision fields are present; noncompliance and other-credit details require the source code/readme. | **Exclude from pooled community access invitation-ITT pending mapping.** It can be reported in an applicant-level offer/approval stratum once the assignment mapping is verified. |
| Tarozzi et al., Ethiopia | **Verified:** Peasant Association/kebele (`pa`) assignment with four arms; `patypen` value labels are Both/Credit/FP/None, while `patypeactual2` is actual treatment. Official `TarozziEtAlReplicationFiles/ReadMe.pdf`, p. 1, and `data.dta` metadata document `time`, `D_MF`, `D_Both`, `D_FP`, `D_None`. | **Verified:** a credit-only vs no-program contrast is representable as assigned MF vs assigned None; the paper/readme also distinguish credit+family-planning and actual treatment. | Rural households in 133 PAs; pooled baseline/endline cross-sections (`time` labels Baseline/Endline). Exact endline window is not fully established from the readme. | `revenues`, `costs`, `net`, loan/debt and household outcomes are in `data.dta`; the import script uses `t_D` and `net` (lines 667--681) and records a 36-month summary (line 719). | `patypeactual2` versus `patypen` and `T_*` versus `D_*` explicitly document implementation noncompliance. | **Candidate only as predeclared MF-vs-None PA-level access ITT**, but do not combine with the Both arm or actual-treatment variables. Exact common outcome window remains unresolved. |

## Allocation, outcome, and uncertainty field map

The following map makes the data locations explicit. `reported_coefficients_profit`
and `reported_coefficients_profit_sds` are seven-element paper-summary vectors,
not raw participant columns; their order is declared by `study_names` in
`data/import_organise_data_v7.R`, lines 735--750. A row is not eligible for a
formal variance-based comparison unless its assignment-level standard error can
be reproduced from the cited study code or a study-specific reported table.

| Study | Assignment field and location | Profit/outcome field and location | Summary effect / SE location | Variance status |
|---|---|---|---|---|
| Mexico | `Treatment`, `BTreatment`, `cluster` in `data/microcredit-rct-data/angelucci_et_al_2015.dta`; import lines 74--75, 106 | `Q10_9_toprof` (last 2 weeks), import lines 76--78 | `reported_coefficients_profit[1]`, `reported_coefficients_profit_sds[1]`, import lines 749--756 | **Unresolved:** ordinary R `lm` is not cluster-robust; study quantile code clusters `cluster`, but an exact mean-profit SE is not frozen |
| Mongolia | `treatment`, `soum`, `followup` in `attanasio_processed_for_rm_analysis.dta`; import lines 145--162, 183 | `profit_j`, import lines 163--165; one-year standardization line 746 | summary vector indices `[2]`, lines 749--756 | **Unresolved:** arm-specific group-vs-control or individual-vs-control SE is not supplied by the current pooled summary |
| Bosnia | `treatment`, `ebrd_selected_loan`, `randomisation_date/time`; baseline/follow-up files in the Augsburg path; import lines 300--301, 371--376 | `bm_profit` in follow-up business file, import lines 314--327 | summary vector index `[3]`, lines 749--756 | **Unresolved for community stratum:** study code clusters at the relevant assignment/design level, but this is an applicant-level contrast |
| India | `treatment` and `areaid` in `2013-0533_data_endlines1and2_stata12.dta`; import lines 415--416, 435 | `bizprofit_1` (last 30 days, endline 1), variable label and import lines 417--419 | summary vector index `[4]`, lines 749--756; study do-files cluster `areaid` | **Candidate:** cluster-robust design code is present; exact reported SE source must be retained with the frozen endline-1 extraction |
| Morocco | `treatment`, `paire`, `demi_paire`, `wave` in `endline_baseline_outcomes.dta`; `Analysis_Oct2014.do`, lines 201--244 | `profit_total` (past 12 months), `OutcomeConstruction_endline_Oct2014.do` and metadata label | summary vector index `[5]`, lines 749--756; main do-file clusters `demi_paire` | **Candidate:** pair-clustered code exists; sampling weights and endline wave must be frozen |
| Philippines | `css_randomizetag`, `css_loandecision_raw`, score fields in nested `1200138sdataset_clean.dta`; import lines 568--574 | constructed `fu_profit_1`...`fu_profit_8`, import lines 574--578 | summary vector index `[6]`, lines 749--756 | **Unresolved:** randomization-tag to primary assignment and a common profit SE are not established |
| Ethiopia | `patypen`, `pa`, `time`, `D_MF`, `D_None` in `TarozziEtAlReplicationFiles/data.dta`; import lines 667--681 | `net` (revenues minus costs), import lines 679--681 | summary vector index `[7]`, lines 749--756 | **Unresolved for frozen MF-vs-None:** existing summary uses `t_D` and does not isolate the required arm contrast |

This map is why the executable numerical pilot uses only the three rows whose
first-endline profit summary and design stratum can be stated without silently
changing arms. It does not claim that their ordinary summary SEs are sufficient
for a confirmatory RCT variance analysis.

## Data-field and variance audit

The package contains study data, but the published Meager import is not a
uniform design-based estimator. For example, its profit replication script
fits `lm(profit ~ treatment)` for all seven studies (`data/replicating-
microcredit-regressions-profit.R`, lines 62--74), while study-specific do-files
cluster by `areaid`, `demi_paire`, or `pa` where appropriate. Therefore a pilot
must not silently treat the ordinary `lm` standard errors as RCT sampling
variances. Any study without an auditable assignment-level variance is marked
variance-unresolved and excluded from a formal 95% statement.

The package README also says the cleaned project object was assembled from seven
online datasets and does not import every available variable
(`data/README.md`, items 5--7). The metadata audit therefore establishes file
locations and labels, not complete mechanism coverage.

## Coding status

The repository has one automated metadata extraction (884 labelled fields) and
an AI design-only second pass. The attempted second pass accidentally exposed
abstract/result-summary and balance-table text while locating method pages; it
did not use numerical treatment-effect values, but it does not qualify as a
strict outcome-blind human double code. No inter-coder agreement statistic is
reported. See `MICROCREDIT_CODING_STATUS_20260925.md`.
