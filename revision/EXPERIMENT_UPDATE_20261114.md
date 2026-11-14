# November 2026 experiment update

This update preserves the 37 reviewer-guided experimental commits through `f755e86` and adds archived November 8–9 studies. Numerical results and original code are copied unchanged. No new experiment or manuscript change was performed for publication.

| Package | Contents | Main scope |
|---|---|---|
| [Reviewer experiments](reviewer1_experiments/README.md) | Selection-safe audit, calibration stress, matched weighting, end-to-end reanalysis, smoothness and bridge-objective audit | Synthetic validation and saved-design reanalysis |
| [Many Labs 2 conditional](manylabs2_conditional/README.md) | 40-source/17-target aggregate certificate package and read-only replay | Restricted Common-CATE, assumption-conditional calculation |
| [Bernoulli MLE bridge](manylabs2_mle_gaussian_bridge/README.md) | Frozen data-generating protocol, synthetic outputs and asymptotic analysis | Bernoulli simulation, Gaussian approximation and bridge design |
| `results/` and `non_gaussian_bridge/` | Earlier complete workflows, ablations, analysis and Lean sources | Historical protocol versions retained |

The root September release manifest remains the manifest for its historical export; it does not enumerate this update. `experiment_update_manifest.json` pins the new packaged files. Original run manifests preserve their original paths, source hashes, timestamps and scope. They are provenance records, not universal public-file allowlists.

Participant-level staged Many Labs 2 files, Python caches, build products, pilot duplicates and unfinished budget-extension code are excluded. The budget-extension protocol already in history records planning; only its local smoke existed and it is not presented as a completed full experiment. Five-stream A/B raw arrays remain local and can be regenerated from the saved seeds and generators.

The scientific qualifications in the reports are retained. Neither arithmetic replay nor a synthetic approximation experiment validates unmeasured real-world mechanism assumptions.
