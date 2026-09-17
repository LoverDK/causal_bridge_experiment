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

The analyzed sample has 57 complete sources and 7,228 responses. Country holdout and leave-one-source-out evaluation are distinct protocols; consult their manifests and source modules. Held-out effects are noisy scoring references, not known causal truths.

## National Supported Work (NSW)

- Public source: https://users.nber.org/~rdehejia/data/nsw_dw.dta
- Local input: `legacy_audits/data/nsw_dw.dta`.
- SHA-256: `d1bd2680a1c6f799f1c6d2455bf29633fdf19be01cb19490621c20a560b4e072`.
- Processing and scaling are in `legacy_audits/src/causal_atlas_sim/nsw_experiment.py` and the experiment metadata.

NSW archive objects are overlapping local reconstructions from one trial. They are not 112 independent studies. The semi-synthetic extension uses NSW covariates with generated outcomes and an exactly specified target effect.

## Terms and file provenance

Public input data retain their upstream authorship and applicable terms. This repository does not assert a new license over third-party datasets or papers. No software license has been selected in this release.

`provenance/import_inventory.json` maps imported files to their original project-relative locations and hashes. Original run manifests describe the historical run environment, including occasional old local paths and then-current source versions. They are not a promise that every historical source hash matches a later source revision. `provenance/release_manifest.json` describes the actual delivered files; it excludes itself, Git metadata, and transient reproduction output. Line-ending conversion is disabled to preserve archived bytes across Git checkouts.
