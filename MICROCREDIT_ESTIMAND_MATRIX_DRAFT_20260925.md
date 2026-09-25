# Draft estimand compatibility matrix

This is a pre-analysis design matrix, not an effect table. It records only
what can currently be supported by package readmes, variable labels and file
structure. `Unknown` means that the design paper or value-label review is still
required. No study is treated as pooled merely because its file contains a
variable named `treatment`.

| Study | Treatment information currently supported | Control information currently supported | Outcome/horizon information | Current decision |
|---|---|---|---|---|
| Angelucci et al. (Mexico) | `Treatment` and `BTreatment` fields are present; their exact intervention contrast is not frozen | Unknown from the header audit | Business, loan and consumption candidate fields are present; common horizon not frozen | Design review before invitation-ITT use |
| Attanasio et al. (Mongolia) | `treatment` is labelled “Soum belongs to treatment”; group/individual and follow-up treatment fields are present | Unknown for the exact pooled contrast | Credit, self-employment, income, labour and consumption files are present; horizon not frozen | Keep multi-arm contrasts separate until protocol review |
| Augsburg et al. (Bosnia) | `treatment` and `ebrd_selected_loan` are present; randomisation date/time fields are present | Unknown from the inspected section | Baseline loans, consumption, income and business sections are present; follow-up linkage/horizon not frozen | Candidate after design and linkage review |
| Banerjee et al. (India) | `treatment` is labelled “Treatment area” | Unknown from the header audit | Baseline/endline, credit, business, income and consumption index fields are present; horizon not frozen | Candidate after wave and control review |
| Crépon et al. (Morocco) | `treatment` is labelled “1 if treated village”; `wave` and `random5_final` are present | Other-village control is plausible but not accepted until design source confirms it | Baseline/endline and administrative loan terms are present; multiple waves require a frozen horizon | Candidate after design review |
| Karlan and Zinman (Philippines) | `css_randomizetag` is labelled “decision randomized”; no simple invitation assignment field was found | Unknown | Credit score, loan decision and loan-term fields are present; target estimand is not yet established | Exclude from pooled invitation-ITT pilot pending design review |
| Tarozzi et al. (Ethiopia) | Official readme documents PA-level randomization; `patypen` is assigned arm, with `D_MF`, `D_Both`, `D_FP`, `D_None` labels | `D_None` is the assigned-none arm in the data documentation | Baseline/endline are marked by `time`; credit, revenue, cost and consumption candidates are present | Candidate for a predeclared MF-versus-none ITT contrast, subject to paper-level confirmation |

## Proposed freeze rule

The first confirmatory stratum will include a study only after two coders agree
on: randomized offer/eligibility treatment, contemporaneous control service,
population and unit, outcome family, follow-up horizon, and effect scale. A
multi-arm study contributes one contrast only when that contrast is frozen in
advance. Actual borrowing, repayment, or treatment-on-the-treated fields do not
replace the invitation ITT.

Until that review is complete, this matrix supports only a descriptive
leave-one-study-out feasibility audit. It does not support a real calibration
certificate or a cross-study causal estimate.
