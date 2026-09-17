# Causal bridge experiment archive

Experimental code, public input data, frozen configurations, saved results, and paper figures for **When Can Experiments Transfer? Operational Certificates and Active Causal Bridging**. This release corresponds to the ICLR 2027 manuscript revision of 17 September 2026, including Appendix P's matched-certificate weight and geometric-bound ablations.

The paper-to-file index is [paper_figures/PAPER_MAP.md](paper_figures/PAPER_MAP.md). Data origins and reuse boundaries are in [DATA_SOURCES.md](DATA_SOURCES.md). Manuscript integration and validation are recorded in [RELEASE_NOTES.md](RELEASE_NOTES.md).

## Contents

| Directory | Purpose |
|---|---|
| `paper_original/` | Exact theorem-linked synthetic and Many Labs 2 scripts, with recorded outputs for the main empirical figures |
| `current_method/` | Independent certificate implementation, complete sequential workflow, real-data supplement, selection/calibration audits, and both new ablations |
| `legacy_audits/` | Earlier synthetic, partial-identification, bridge, and NSW audits; retained for the paper's supplementary results and provenance |
| `paper_figures/` | Paper figure assets, LaTeX table fragments, and portable Figure 5/6 renderer |
| `provenance/` | Import inventory and SHA-256 delivery manifest |

Saved full runs are evidence archives. The wrapper below creates a separate output directory and refuses to overwrite an existing one. Historical READMEs and manifests retain their original dates and paths; use the root commands for this release's directory layout.

## Reproduce

Release packaging was tested with Python 3.13.15; original run environments and package versions are recorded in each run manifest. Install dependencies, then verify the delivered bytes:

```bash
python -m pip install -r requirements.txt
python reproduce.py verify
```

Start with a smoke run. Every command requires a fresh output path:

```bash
python reproduce.py ablations --profile smoke --output reproduced/ablation-smoke
python reproduce.py workflow --profile smoke --output reproduced/workflow-smoke
python reproduce.py current --profile smoke --output reproduced/core-smoke
python reproduce.py plus --profile smoke --output reproduced/robustness-smoke
```

Full paper runs and other components:

```bash
python reproduce.py original --output reproduced/original
python reproduce.py current --profile full --output reproduced/core-full
python reproduce.py plus --profile full --output reproduced/robustness-full
python reproduce.py workflow --profile full --workers 4 --output reproduced/workflow-full
python reproduce.py ablations --profile full --workers 4 --output reproduced/ablation-full
python reproduce.py real --output reproduced/real
python reproduce.py legacy-nsw --output reproduced/nsw
python reproduce.py legacy-extensions --profile full --output reproduced/extensions
python reproduce.py figures --output reproduced/figures
python reproduce.py audit-ablations --output reproduced/ablation-audit
python -m unittest discover -s current_method/tests -v
```

`audit-ablations` reconstructs all saved weights, radii, predictions, stopping decisions, and costs, and checks parity with the earlier workflow. It expands `plans.jsonl.gz` in the isolated copy. The raw plan file exceeds GitHub's per-file limit; its committed gzip archive is lossless, with the original uncompressed hash retained in the run manifest. `verify` checks delivery integrity; it does not rerun simulations.

## What the new experiments show

The ablations use 1,800 independent worlds, shared random/nearest acquisition schedules, two certificates, and tolerances 0.2/0.3. The archive includes 172,800 plans and 345,600 stopped records. At tolerance 0.3 on the bridgeable random-order menu, optimized R2 weights release 100% of targets versus 20.33% for uniform weights, with mean new-participant costs of 159.68 versus 283.52. Weight optimization is useful in these settings; it is not uniformly better in point error on already-supported menus.

The geometric result is mixed: the barycentric bound improves release and cost over the Lipschitz bound on bridgeable menus, but taking their minimum adds no release or cost benefit over the barycentric bound alone in any tested cell. Small radius improvements do not necessarily change a decision. All evaluated ablation policies have zero observed bad releases and full empirical path coverage in this run; these conservative simulation results are not universal coverage guarantees.

The complete ExAtlas procedure has **not** been run as a matched-information comparator. Earlier semantic and point-representation baselines must not be relabelled as a full ExAtlas replication. Many Labs 2 is source holdout under a standardized intervention, and NSW is within-trial reconstruction; neither establishes calibrated mechanism sets for real cross-intervention transport. Simulations and code checks do not discharge every theoretical assumption.
