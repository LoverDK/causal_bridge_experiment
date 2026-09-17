# Release: 17 September 2026

The two new ablations have been incorporated into the Overleaf manuscript's `causal_lab_proposal_subpapers_tex_iclr2027/01.tex` as Appendix P, Tables 15 and 16. The earlier limitation paragraph now points to these ablations while retaining the missing complete ExAtlas comparison. Dated run notes that say the draft has not yet been inserted describe the pre-integration state.

The integrated PDF has 37 pages: main text is pages 1–9, references begin on page 10, main Figures 1/2/3 remain on pages 4/7/8, and the source-estimate Figure 6 remains on page 35. The first nine pages' extracted text is identical to the preceding revision. All 31 checked theorem, assumption, corollary, lemma, proposition, and proof environments were preserved. Integration does not claim to repair the previously flagged frozen theoretical conditions.

Validation before release:

- Full ablation run: 28 unit tests and 15 result checks passed.
- Independent audit: 172,800 plans reconstructed; maximum radius discrepancy 2.22e-16 and zero prediction discrepancy.
- All 345,600 stopped records reconstructed; maximum discrepancy 5.11e-15, all costs matched.
- Random-R2 and nearest-R2 records matched the original workflow, 14,400 each.
- Packaged ablation smoke run completed in an isolated directory; all 28 tests passed.
- Packaged original synthetic and Many Labs 2 scripts reproduced the paper's reported main results.
- NSW and requested-extension test modules passed, seven tests each.
- Portable appendix-figure generation completed from archived CSVs.

Primary conclusions are bounded by the specified DGP and protocol. Weight optimization helps bridgeable menus; the minimum of the two geometric bounds has no extra release/cost benefit over the barycentric bound at the tested settings. These results do not establish superiority over the complete ExAtlas pipeline or validate real cross-intervention mechanism calibration.
