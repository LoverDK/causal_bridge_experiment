# Unified end-to-end saved-evidence analysis

Completed 2026-11-08. This analysis extends the existing Appendix L/P audit; it generates no worlds or observations and performs no fitting, optimization, source edits, TeX edits or Git operations. The full saved-record analysis took 7.61 seconds, below the frozen 1–4 minute CPU/I/O forecast. The deliverable is evidence about conditional synthetic performance, not real calibration or a universal winner.

## What was compared

The six original workflow policies are targeted R2, targeted Rinf, random R2, nearest-bridge R2, static archive R2 and direct target trials. The matched-weight panel adds uniform, known-noise inverse-variance and nearest-source weights on the same random/nearest paths under R2/Rinf, plus optimized Rinf random/nearest. These are 20 unique policies after exact deduplication. All three geometries, three surfaces, both tolerances and caps 0/96/192/288 are retained.

L and P share 1,800 independent worlds, with 200 worlds per geometry×surface. Their 86,400 and 345,600 rows are repeated states, not independent Monte Carlo samples. We independently rechecked 28,800 optimized-R2 random/nearest shared rows across 11 numerical/event fields: every difference is exactly zero. Existing pooled L metrics agree with the new aggregation to less than 3e-14.

`surface_cap_metrics.csv` contains 1,920 rows: 20 policies×3 geometries×2 tolerances×4 caps×(3 surfaces+pooled). It includes 15 metrics with 95% world-bootstrap intervals, event counts and conditional denominators. `paired_targeted_contrasts.csv` contains 27,360 contrasts, sharing bootstrap worlds across methods. Pooled bootstrap resamples within each surface and averages the three equally sized strata. B=2,000, seed=2026110804; percentile endpoints use nearest empirical quantiles. No method-independence assumption is used. These are exploratory Monte Carlo intervals; degenerate zero-event bootstrap intervals do not prove zero population risk.

## Gains and adverse direct comparisons

On the bridgeable menu at delta .3 and cap288, targeted, random, nearest and direct all release 600/600. Their actual mean new-participant costs are 117.92,159.68,241.60 and96. Targeted-minus-random cost is −41.76 (95% paired CI −46.24 to −37.12); targeted-minus-nearest is −123.68 (−128.00 to −119.20). Targeted-minus-direct is +21.92 (+19.84 to +24.00). Thus targeted saves participants relative to these acquisition alternatives, while direct is cheaper in this cell.

The same stopped-policy comparisons show a precision tradeoff: targeted/direct all-target MAE .03958/.07866 and returned full width .47337/.58412. Targeted-minus-direct MAE is −.03908 (−.04461 to −.03362); width is −.11075 (−.11239 to −.10910). Against random, targeted MAE differs by only −.00034 (−.00321 to +.00244), although its width is narrower by .02260. Do not claim a resolved MAE improvement over random.

At delta .2 cap96, targeted releases29.5%, random7%, nearest0% and direct0%. At cap288, targeted releases66.5%, random38.5%, nearest0% and direct100%. Targeted-minus-random release is +28.0 percentage points (+25.33 to +30.67), but targeted-minus-direct is −33.5 points. Mean cost227.04 versus direct288 reflects different success rates. Conditional first-release cost is196.33 (193.93–198.72) for targeted's399 released worlds, versus288 for direct's600; these are distinct selected populations and do not establish equal-service cost savings. Exhaustion without release is33.5% (33.33–33.83) for targeted and0% for direct.

The .2 pooled release result is strongly surface dependent: targeted releases200/200 linear worlds at mean107.04 participants,199/200 quadratic at286.08, and0/200 sinusoidal at288. Direct releases all200 per surface at288. Aggregation must not obscure this boundary.

At .3, targeted Rinf releases34.67% with mean221.60 participants, compared with targeted R2's100% and117.92. Both planners are design measurable. This is a conservatism comparison, not evidence that the workflow used outcome adaptation or that Rinf provides an empirical adaptivity benefit.

## Reliability, conditional release and sign failures

Retain the direct negative event: bridgeable delta .3 has one bad release among600 direct worlds, conditional returned-interval coverage599/600=.99833 (bootstrap .995–1). Targeted has0/600 bad releases and600/600 interval coverage. The zero-event interval is empirical, not a proof of zero risk. At delta .2 direct final output coverage is600/600 while path coverage is599/600: an earlier interval misses even though the final interval covers. Final and path coverage cannot be substituted.

Sign errors are distinct from tolerance errors and interval misses. Among released bridgeable targets at delta .3 cap288, targeted makes307/600 opposite-sign point estimates:51.17% (47.33–54.67), versus direct274/600=45.67% (41.83–49.50). The paired difference is+5.50 percentage points (+.17 to +10.67). In the quadratic surface targeted's rate is75% (69–80.5), compared with direct42.5% (35.5–49.5). At delta .2, targeted has56.39% sign errors among399 released targets and direct42.17% among600; the different release subsets must be acknowledged.

These bridgeable target effects are near zero (approximately −.01 to −.015). Small absolute errors and valid broad intervals can coexist with frequent incorrect point-estimate signs. A certificate permitting error .2 or .3 is not a sign certificate; the intervals can contain zero. The new sign metric is an explicitly adverse result and prevents a direction-accuracy claim from being inferred from MAE alone. Truth-zero worlds, if present, are excluded from this sign denominator and separately counted; none were silently assigned a correct sign.

All conditional quantities are empirical, not guaranteed conditional coverage. Zero releases give NA for released MAE, release coverage, first-release cost, conditional bad-error risk and sign risk. Confidence intervals recompute their numerator/denominator under resampling. Release-rate, MAE, width and cost all use the complete world denominator.

## Supported and unreachable menus

On supported menus all five original archive policies release without new participants; targeted R2 MAE is .01530 and observed sign error0. Direct uses96 or288 participants. This is a zero-acquisition reference, not evidence that bridges are always useful.

On unreachable menus, targeted/random/nearest/Rinf acquire288 participants and release none for both tolerances; their exhaustion rate is100%. Static refuses at cost0 and is not classified as exhausted acquisition. Direct releases all worlds. The current policy has no early-futility stop or automatic direct switch. This wasted-acquisition negative result remains part of the comparison.

## Weighting and output identity

On bridgeable random paths at delta .3 cap288, optimized R2 releases100% at159.68 participants; uniform releases20.33% at283.52 and IVW releases0% at288. At delta .2 the corresponding releases are38.5%,1.33%,0%. The optimized/random stopped .3 MAE is .039918; the different full-prefix288 MAE is .0334. Uniform stopped .3 MAE is .14234, whereas the full-prefix288 MAE is .1405. Never attach those full-prefix errors to stopped release rates. Likewise uniform fixed-prefix release20.0% differs from stopped20.33% because adding studies can worsen a simple weight rule.

P isolates weighting under common observed prefixes. L isolates acquisition among optimized refits. These two controls support limited component claims, not an unmeasured weight×own-targeted-policy interaction or a claim that every uniform/IVW acquisition policy is beaten. Nearest bridge acquisition and nearest-source weights are separate identities.

Returned width includes the refusal Lipschitz outer region; it is not always2R. Both are reported. Direct at cap0 returns an unbounded interval; its width and bootstrap endpoints remain infinity, not zero or a finite-only average. Its stored zero estimate is a no-data placeholder, so cap0 direct MAE is not evidence from a conducted trial. Unreleased point MAE is a diagnostic of the stored estimate, not a published point decision. Costs include newly randomized participants only, excluding history, calibration, mechanism encoding, audit and deployment.

## What remains a future comparator

IVW with the common certificate is a fair known-noise weighting rule. Ordinary fixed-effect source-average confidence intervals and random-effects target prediction intervals have different estimands or exchangeability assumptions from the declared mechanism-constrained target effect. They are not forced into this panel under a misleading common label. A minimally fair future comparison must freeze the target estimand, shared inputs, heterogeneity/common-effect assumptions, tau estimator if used, target predictive-noise terms, failure budget, stopping and acquisition accounting before fitting.

Similarly, a robust PI comparator must specify the same mechanism uncertainty, smoothness/noise inputs and the target coverage event, and distinguish an outer region from an exact sharp region. No real predictive benchmark is relabelled as an end-to-end calibrated ATLAS certificate. No new fit or simulation is needed to report the supported saved-world comparison; real calibration, outcome-adaptive utility, strong external matched-information competitors and general novelty remain unestablished.

## Reproduction and concern follow-up

Run `python analyze_saved.py` in this directory, then `python verify_saved.py`. `analysis_manifest.json` records all read-only input hashes, the exact source manifests, bootstrap settings, row counts, elapsed time and prior-summary agreement. `artifact_hashes.json` hashes local deliverables. `claim_facts.csv` is a compact pooled bridgeable four-policy extract; all omitted cells remain in the complete surface/cap table. `concern_statuses.json` records all12 before/after statuses unchanged; this milestone strengthens REV-07/12 evidence but closes no concern.

Independent verification passed11,520 pandas-based conditional/sign/exhaustion checks across all1,920 cells, with maximum arithmetic difference5.69e-14. It also checked NA conditional outputs for1,225 zero-release rows, preserved infinite widths for24 direct-cap0 rows, and checked the direct bad-release/path events and all12 unchanged concern statuses. The verifier does not import the analysis implementation. These checks validate recorded arithmetic, not scientific assumptions.

No TeX or experiment source was edited. E remained read only. Author understanding is not assumed from a successful script. The next useful decision is how to present the observed cost/precision and sign tradeoffs while retaining the real-input and comparator limitations.
