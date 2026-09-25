# Coding and adjudication status

Date: 2026-09-25.

## Required process

The frozen protocol requires two independent coders who work from design,
implementation, codebook, and metadata sources without seeing target effect
estimates. Each coder records the assignment, control, population, outcome
definition/horizon, implementation/crossover, source locator, and uncertainty.
Disagreements are resolved by a prespecified adjudicator; raw codings and the
adjudication log are retained. Agreement is summarized only after the blind
phase is complete.

## What was actually completed

* Coder A: automated metadata extraction from Stata headers using
  `tools/inspect_microcredit_metadata.py` and `pyreadstat` with
  `metadataonly=True`; 884 variable-name/label rows are in
  `microcredit_variable_label_audit.csv`. This is not a human design code.
* Coder B: an AI-assisted design synthesis using package readmes, design
  sections, value labels, and code paths. While locating method pages, the
  pass also encountered non-numeric abstract/result-summary text and balance
  tables. It did not use numerical effect values, but this exposure means the
  pass is **not a strictly outcome-blind independent coder**.
* No human second coder, adjudicator, signed coding sheets, or independent
  expert mechanism audit has been supplied.

## Consequence

Double coding and inter-coder agreement are **not completed**. We do not report
percent agreement, Cohen's kappa, or a claim of independent blind validation.
`MICROCREDIT_DESIGN_EVIDENCE_20260925.md` is an auditable single-author/AI
source audit with unresolved fields explicitly retained. A real confirmatory
analysis requires a fresh two-person blind pass, with the effect files sealed
from both coders, followed by adjudication.
