# Synthetic calibration smoke — 2026-11-08

The authorized smoke completed all 26 frozen cells with 20 independently regenerated calibration/test worlds per cell (520 total). No real outcome was read. All unfavorable/shift cells remain in the saved summaries. Smoke is implementation evidence only, not a performance estimate.

Runner elapsed time was 0.283 seconds (whole Python invocation approximately 1.1 seconds); independent audit elapsed time was 0.587 seconds. The audit regenerated every calibration array from its seed, computed norms with explicit sums of squares, sorted the complete calibration scores, checked exact Decimal ranks against the runner's rational arithmetic, and recomputed test hits and source/bridge/target means. Maximum floating-point discrepancy was 1.78e-15. Every original run-artifact hash passed. No simulation or optimizer helper was imported by the independent audit.

Verified analytic edges: n_cal=7 or 18 gives infinite .95 joint/marginal radii; n_cal=19 gives joint rank19; n_cal=199,M=11 gives infinite empirical Bonferroni radii, while M=5 is finite. The minimum finite Bonferroni archive count for M=11 is219. B=0 bridge coverage remains undefined. Infinite radii yield coverage one and no localization information; they are not silently capped. Per-world joint coverage is an AND over the complete frozen menu, including all unselected bridges.

Compact raw `.npz` files preserve every world's radius vectors, test norms, entity hits, joint/role fractions, calibration maxima/order statistics, exact ranks, perturbation counts and seed components. The full calibration errors/flags are exactly regenerated rather than stored as a large duplicate archive. This storage-only amendment is recorded in `execution_amendment.md` and changes no cell or method.

Revised forecast before full: generation/paired-world bootstrap/storage20–60 seconds; independent full-world regeneration20–90 seconds; total approximately1–3 minutes on this CPU. Basis: smoke generation scaled by100 worlds, independent audit0.587×100≈59 seconds, and additional bootstrap/report work (100→2000 resamples and20→2000 worlds) estimated separately. No GPU is useful. Full remains pending root communication/go after this report.

Evidence: `smoke01/run_manifest.json`, `smoke01/independent_audit.json`, `smoke01/cell_timing.csv`, `smoke01/summary.csv`, `smoke01/entity_summary.csv`, `smoke01/paired_world_contrasts.csv` and `smoke01/raw/`.

All12 review states remain unchanged. REV-04/05 stay open: synthetic calibration logic does not create real reference labels or compute a real certificate. REV-01/03/11/12 gain an auditable input/implementation/infinity explanation; REV-02/06/07/08/09/10 receive no new substantive result. Full performance interpretation requires its separate seed and independent audit.
