# Lean proofs

This directory is a standalone Lean project for the deterministic statements
listed in the manuscript's “Machine-Checked Deterministic Core” appendix.
`lean-toolchain` pins Lean 4.34.0-rc1, `lakefile.lean` pins Mathlib 4.34.0-rc1,
and `lake-manifest.json` pins the resolved dependency commits.

## Build and audit

From this directory, run:

```powershell
lake build
lake env lean --error=warning CausalAtlasBridge.lean
lake env lean --error=warning AxiomAudit.lean
```

The audit prints dependencies for all twelve named theorem outputs. The source
contains no `sorry`, `admit`, user-added `axiom`, or `unsafe` declarations.
Build logs and the toolchain/dependency hashes are recorded in
`VERIFICATION.md` after the checks are run.

## Formalized scope

`CausalAtlasBridge.lean` formalizes finite weighted absolute-value bounds,
substitution of an admissible selected weight, the two-world absolute-loss
inequality, barycentric cancellation, finite interval intersection endpoint
characterization and projection facts, and the partial-identification
complementarity witness. The finite interval results concern closed intervals
represented by endpoint pairs. The PI witness uses the two-dimensional box
and bridge equations specified in the appendix.

This project does not formalize probability spaces, conditional sub-Gaussian
concentration, AIPW expectations, Lindeberg--Feller convergence, Gaussian KL
divergence, or the McShane extension theorem. Lean checks the stated
deterministic propositions under Mathlib's standard foundational axioms; this
does not independently establish the empirical assumptions or statistical
claims in the paper.
