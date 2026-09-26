# Microcredit LOSO pilot: author work summary

**Historical, superseded work summary.** The old three-study run and earlier
test-command claims below are not the accepted current evidence. The source
correction, actual nine-test execution, new results and hashes are recorded
in `MICROCREDIT_PUBLISHED_V1_ACCEPTANCE_20260925.md`. This history is preserved
locally but excluded from the new submission allowlist.

Date: 2026-09-25. This summary is written for an independent review of the
next-stage evidence. It records what was completed and what remains outside
the evidence boundary.

## Completed

* The local OpenICPSR V1 archive was inventoried without committing raw
  observations. The archive identity, file counts, study paths, package
  license, and unresolved upstream-use restrictions are recorded in
  `MICROCREDIT_OPENICPSR_INVENTORY_20260925.md`.
* A seven-study design evidence table was assembled from paper sections,
  readmes, labels, and analysis paths. It keeps unresolved treatment meanings,
  control access, implementation, horizons, and assignment-level variance
  visible. The evidence table is `MICROCREDIT_DESIGN_EVIDENCE_20260925.md`.
* The invitation-ITT estimand and compatibility gate were frozen in
  `MICROCREDIT_INVITATION_ITT_PROTOCOL_20260925.md`. The gate retains only
  community/village/neighborhood/PA access designs with first-endline
  self-employment/business profit on the frozen USD-PPP-per-fortnight scale.
  It does not pool consumption, income, labor, applicant approval, actual
  borrowing, or multi-arm contrasts that were not isolated in advance.
* The strict gate yielded three numerical pilot units: Mexico/Angelucci,
  India/Banerjee endline 1, and Morocco/Crépon. Mongolia and Ethiopia remain
  arm-specific reconstruction candidates; Bosnia and the Philippines remain
  applicant-level offer/approval designs. This small compatible set is itself
  a result, not a reason to relax the estimand.
* The executable LOSO protocol and runner are frozen in
  `MICROCREDIT_LOSO_PILOT_PROTOCOL_20260925.md` and
  `tools/run_microcredit_loso_pilot.py`. Every split has two training studies.
  Fixed effect, robust training range, and descriptive design-weighted ATLAS
  run; random effects and design meta-regression are explicitly marked
  unidentified with two training studies.
* The information boundary was corrected and audited. Predictions and release
  decisions use only training-study effects/SEs and the held-out design vector.
  The held-out effect and result SE are opened only afterward for the noisy RCT
  reference interval and scoring. The audit changes both held-out fields and
  leaves every prediction, radius, and release decision unchanged.
* The pilot now reports exact per-target rows, release/refusal, width, point
  error, sign error, released-target error, conditional released-target risk,
  and noisy-reference interval relation. Results are in
  `results/microcredit_loso_pilot/` and summarized in
  `MICROCREDIT_LOSO_PILOT_REPORT_20260925.md`.

## Pilot findings

At the frozen half-width tolerance `delta=0.20` USD PPP per fortnight, all
computed methods refused all three targets. Mean interval widths were 20.975
for fixed effect, 11.928 for the training range, and 30.269 for descriptive
ATLAS. Fixed-effect and ATLAS intervals partially overlapped the held-out RCT
sampling interval in all three splits. The training range was disjoint for one
target and partially overlapped for two. These are noisy-reference counts, not
causal-truth coverage, calibration, or a 95% guarantee. Released-target risk is
undefined because no target was released.

## What remains incomplete

The required two-person outcome-blind coding and adjudication has not been
completed; therefore no inter-coder agreement statistic is reported. The
seven-study archive cannot supply the minimum 19 independent calibration units
for a finite nominal 95% rank/conformal radius, and it has no independent
real-world mechanism-set calibration archive. A held-out RCT estimate remains
sampling-uncertain and is not a noiseless causal truth. Assignment-level
cluster-robust variance reconstruction is also unresolved for some candidate
studies.

The next confirmatory step requires an authorized expansion to at least 19,
preferably 25--40, independent estimand-compatible interventions; frozen
outcome-blind mechanism proxies plus expert reference codings; a disjoint
calibration archive; and a separately held-out randomized target. Individual
records must remain governed by their data-use and ethics conditions.

## Verification

* `python tools/test_microcredit_loso_pilot.py`: passed.
* `python current_method/run_tests.py`: 42 tests passed.
* `python -m py_compile tools/run_microcredit_loso_pilot.py tools/test_microcredit_loso_pilot.py`: passed.
* `python reproduce.py verify`: verified 323 release files.
* `git diff --check`: reports CRLF-related whitespace warnings for generated
  CSV/JSON files under the repository's existing `* -text` policy; no code or
  Markdown syntax failure was found.

No paper source or abstract was changed in this step.
