# Lean verification record

Verified on 2026-09-26 with the standalone project in this directory.

## Pinned environment

- Lean: 4.34.0-rc1, commit `3447a668783dbce1a8fdb97101dd067687b2b418`.
- Lake: 5.0.0-src+3447a66.
- Mathlib input tag: `v4.34.0-rc1`.
- Mathlib resolved commit: `de5ce8a9a66a4aa68a9bdbb35b63a06d34d9ca11`.
- Lake resolved dependencies: pinned in `lake-manifest.json`.

## Checks run

```text
lake env lean --error=warning CausalAtlasBridge.lean    PASS
lake env lean --error=warning AxiomAudit.lean           PASS
lake build                                             PASS (3010 jobs)
```

The module exports the ten explicitly named source and interval lemmas plus
`complementarity_pi_width_table` and
`complementarity_pi_width_violates_diminishing_returns`: twelve audited
theorem outputs in total. `AxiomAudit.lean` prints only `propext`,
`Classical.choice`, and `Quot.sound` for the outputs that use Mathlib
classical/algebraic infrastructure; `selection_substitution` has no axiom
dependencies. No project theorem depends on `sorryAx`.

The project was built with a standalone root module, `LeanProofs.lean`, which
imports `CausalAtlasBridge` and `AxiomAudit`. The source and verification files
are included in the supplementary release manifest. This record concerns
formal checking of the stated deterministic propositions; it does not validate
statistical assumptions, data, or empirical claims.
