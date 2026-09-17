# Paper-to-artifact map

Numbering follows the integrated 17 September 2026 `01.tex` revision. Repository paths below are relative to the repository root. The full paper and its frozen theory are maintained separately in Overleaf; this repository is the experiment archive.

| Paper item | Data / saved results | Implementation / reproduction |
|---|---|---|
| Figure 1, decision diagram | Conceptual TikZ diagram in the manuscript; no experimental data | Not an empirical result |
| Figure 2, four theorem-linked synthetic panels; Table 4, simulation manifest | `paper_original/recorded/summaries/operational_panel_*.csv`, `operational_simulation_manifest.csv` | `paper_original/run_operational_experiments.py`; `reproduce.py original` |
| Figure 3, Many Labs 2 source holdout and release frontier | `paper_original/recorded/manylabs/`; independently checked in `current_method/results/full/manylabs_*.csv` | `paper_original/run_manylabs2_framing.py`, `current_method/atlas_new/manylabs.py`; `reproduce.py original` / `current` |
| Figure 4, NSW within-trial reconstruction | `legacy_audits/results/nsw_*`; original asset `paper_figures/assets/figure5_nsw.pdf` retains its historical filename | `legacy_audits/src/causal_atlas_sim/nsw_experiment.py`, `paper_figures.py`; `reproduce.py legacy-nsw` |
| Table 5, stronger synthetic baselines | `legacy_audits/results/extensions/synthetic_baselines_records.csv`, `synthetic_summary.csv`, `synthetic_paired_summary.csv` | `legacy_audits/scripts/run/run_requested_extensions.py`, `scripts/build/build_extension_artifacts.py`; `reproduce.py legacy-extensions --profile full` |
| Table 6, NSW reconstruction | `legacy_audits/results/nsw_experiment_summary.csv`, `nsw_method_error_records.csv`; `paper_figures/tables/main_nsw.tex` | NSW module and `reproduce.py legacy-nsw` |
| Table 7, NSW-covariate semi-synthetic extension | `legacy_audits/results/extensions/nsw_semisynthetic_*.csv` | Requested-extension runner; `reproduce.py legacy-extensions --profile full` |
| Figure 5, six-panel workflow; Tables 9/10, pooled/cell results | `current_method/results/workflow_full/`: `workflow_records.csv`, `acquisitions.csv`, `pooled_summary.csv`, `workflow_summary.csv`, paired comparisons and world audits | `current_method/atlas_new/workflow.py`; `reproduce.py workflow --profile full`; render with `reproduce.py figures` |
| Tables 11/12, source/country holdout and competing estimators | `current_method/results/real_supplement/`: holdouts, summaries, matched comparisons, frontiers and leakage checks | `current_method/run_real_supplement.py`; `reproduce.py real` |
| Tables 13/14, selection and joint calibration | `current_method/results/full/selection.csv`, `joint_calibration_summary.csv`, `joint_calibration_records.csv` | `current_method/atlas_new/experiments.py`; `reproduce.py current --profile full` |
| Figure 6, all source effects | `current_method/results/full/manylabs_sources.csv`; `paper_figures/assets/revision_sources.pdf` | `paper_figures/render_appendix_figures.py`; `reproduce.py figures` |
| Tables 15/16, matched-weight / geometric-bound ablations | `current_method/results/ablations_full/`: stopped/fixed-budget cells and summaries, paired differences, same-weight geometry, saved plans, records and audit | `current_method/atlas_new/ablations.py`, `ablation_report.py`; `reproduce.py ablations --profile full`; `reproduce.py audit-ablations` |
| Other supplementary certificate, PI and bridge diagnostics | `current_method/results/full/`, `full_plus/`; earlier results under `legacy_audits/results/` | `current_method/atlas_new/core.py`, `audit_plus.py`, legacy modules and runners |

Tables 1–3 and 8 are assumption, claim/protocol, notation, or fixed-design tables, not additional estimated outcomes. Their source configurations and protocols are included where applicable. Legacy figure filenames and extra audit plots preserve earlier numbering; they are not extra Figures 7/8 appended to the current manuscript.

The `paper_figures/assets/` files are the paper's figure inputs. The portable renderer regenerates Figures 5 and 6 from committed numerical records; PDF metadata and platform fonts can change file bytes. `historical_build_revision_figures.py` is retained for provenance and contains its original machine paths; use the portable renderer for these appendix figures.

The legacy plotting suite can also regenerate Figure 4 from its committed records by running `scripts/build/build_paper_figures.py` inside an isolated copy of `legacy_audits`. No superseded early prototype or missing unrelated dataset is required by the reproduction commands above.
