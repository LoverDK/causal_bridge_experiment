# Data sources and provenance

Only the public datasets used by the paper's experiments are included. Synthetic datasets are generated from the committed configurations and seeds.

## Many Labs 2 framing replication

- Study: Klein et al. (2018), Many Labs 2; Tversky and Kahneman framing replication.
- Upstream repository: https://github.com/ManyLabsOpenScience/ManyLabs2
- Pinned revision: `acef63fc397b8dce7f0b00f863bcea78d324bea8`.
- OSF project: https://osf.io/8cd4r/
- Local input: `current_method/data/manylabs2_framing.csv`.
- SHA-256: `15898b5c241696adc7fd91a638839ba49a9f9be64c78da9151b39018d66bfbd3`.
- The exact download URL, byte count, and revision are retained in `current_method/data/provenance.json`.

## Many Labs 2 original study-level effects

- Upstream file: `OSFdata/!!RawData/ML2_OriginalEffects.csv` at commit
  `acef63fc397b8dce7f0b00f863bcea78d324bea8`.
- Local input: `current_method/data/manylabs2_original_effects.csv`.
- Exact URL, byte count, and hash are also recorded in
  `current_method/data/manylabs2_original_effects_provenance.json`.
- SHA-256: `78b3432bebb798595ebb08ee10fb68d3f6f59cd5e0ab49606cfb6835eb226406`.
- The cross-effect-family audit freezes five target families and retains 28 of
  32 summary rows with finite Cohen's d, positive variance, and N > 1. The
  complete rules are in `current_method/docs/effect_family_holdout_protocol.md`.
- These standardized effects are noisy scoring references and provide neither
  real mechanism labels nor causal ground truth.

The analyzed sample has 57 complete sources and 7,228 responses. Country holdout and leave-one-source-out evaluation are distinct protocols; consult their manifests and source modules. Held-out effects are noisy scoring references, not known causal truths.

## National Supported Work (NSW)

- Public source: https://users.nber.org/~rdehejia/data/nsw_dw.dta
- Local input: `legacy_audits/data/nsw_dw.dta`.
- SHA-256: `d1bd2680a1c6f799f1c6d2455bf29633fdf19be01cb19490621c20a560b4e072`.
- Processing and scaling are in `legacy_audits/src/causal_atlas_sim/nsw_experiment.py` and the experiment metadata.

NSW archive objects are overlapping local reconstructions from one trial. They are not 112 independent studies. The semi-synthetic extension uses NSW covariates with generated outcomes and an exactly specified target effect.

The versioned `legacy_audits/results/extensions/nsw_real_proxy_truth_v2/` audit
uses a participant-disjoint split of the same trial for an outcome-blind
pretreatment-covariate proxy check and a separate semisynthetic causal-truth
run. The proxy is explicitly `observed_covariate_proxy`, not a latent mechanism
set; the causal truth is exact only for the frozen generated response surfaces.

## Meager microcredit pilot inventory

- Official article: https://www.aeaweb.org/articles?id=10.1257/app.20170299.
- Official supplemental appendix: https://www.aeaweb.org/articles/materials/10055.
- OpenICPSR package DOI: https://doi.org/10.3886/E116357V1.
- User-supplied local archive: `116357-V1.zip (local archive; not redistributed)`.
- Archive SHA-256: `1EC66E45ED401C7CC476548B0AE77DF0AF765942D7D8914202797D6FA4C61BFE`.
- The archive has 306 files, including 95 `.dta` files, one cleaned project
  `RData`, 12 nested source ZIPs, and code/readme/survey materials for the seven
  published study units. The metadata-only inventory is in
  `MICROCREDIT_OPENICPSR_INVENTORY_20260925.md`.
- The package root `LICENSE.txt` states Modified BSD for code and CC BY 4.0 for
  databases, images, tables and text. This repository does not claim that the
  package-level license resolves every upstream trial-file, consent, ethics or
  linkage restriction. Raw Meager files are not committed here.
- The package is a feasibility/pilot source. It does not by itself provide 19
  independent interventions for a finite-sample 95% calibration archive.

## Terms and file provenance

Public input data retain their upstream authorship and applicable terms. This repository does not assert a new license over third-party datasets or papers. No software license has been selected in this release.

Run manifests record the environment and source hashes for the corresponding
saved outputs. `provenance/release_manifest.json` describes the actual delivered
files; it excludes itself, Git metadata, and transient reproduction output.
Line-ending conversion is disabled to preserve archived bytes across Git
checkouts.
