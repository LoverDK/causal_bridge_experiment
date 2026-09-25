# Descriptive LOSO pilot report

Run date: 2026-09-25. The executable protocol is frozen in
`MICROCREDIT_LOSO_PILOT_PROTOCOL_20260925.md`; the implementation is
`tools/run_microcredit_loso_pilot.py`. The report uses only the three studies
that passed the strict community access, first-endline profit, and traceable
summary gate: Mexico/Angelucci, India/Banerjee endline 1, and
Morocco/Crépon. Mongolia and Ethiopia remain design candidates but their
available Meager summaries combine treatment arms that are not the frozen
single invitation contrast. Bosnia and the Philippines are applicant-level
offer/approval designs.

## Results

The saved `results/microcredit_loso_pilot/loso_results.csv` contains one row
per target and method. At the primary frozen radius tolerance `delta=0.20` USD
PPP per fortnight, every computed method refused all three targets because the
interval radii were much larger than the tolerance. The fixed-effect, robust
range, and descriptive ATLAS methods all produced finite intervals; random
effects and design meta-regression were not identified with only two training
studies. The complete threshold curve is in `release_frontier.csv`.

The point estimates and intervals are noisy-reference diagnostics. The held-out
RCT's `effect +/- 1.96*se` interval is reported alongside the prediction
interval. The result categories are exact study-level counts: prediction and
reference intervals were partially overlapping for all fixed-effect and ATLAS
rows; the robust range contained the full reference interval for one target and
partially overlapped for two. These are not causal-truth coverage or calibration
rates.

The leakage audit in `leakage_audit.csv` flips each target effect after the
prediction decision. All prediction, interval, and release values were
unchanged (`max_prediction_change=0` for all three targets). This verifies the
implementation's information boundary for this pilot; it does not validate the
mechanism representation.

## Limitations and distance to the requirement

This is a three-unit descriptive feasibility audit. The LOSO fits overlap, and
there are only two training studies in every split. No bootstrap or repeated-
trial uncertainty is reported. The pilot does not provide an independent
mechanism-set calibration archive, a real joint 95% radius, or noise-free causal
truth. The coding status is also not a completed human double-blind audit; see
`MICROCREDIT_CODING_STATUS_20260925.md`.

The next feasible step is a fresh two-person outcome-blind coding pass and an
authorized expansion to at least 19 independent, estimand-compatible
interventions. Only then can the paper evaluate a finite-sample real calibration
protocol; a held-out randomized target still supplies a sampling-uncertain
reference rather than an exact individual causal truth.
