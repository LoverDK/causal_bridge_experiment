# Current paper artifact map

Paths are relative to the repository root. The saved outputs are the numerical
records used for the integrated manuscript; the commands below regenerate them
in an isolated directory.

| Paper item | Committed evidence | Source and reproduction |
|---|---|---|
| Figure 2 and Table 4 | `paper_original/recorded/summaries/operational_panel_*.csv`, `operational_simulation_manifest.csv` | `paper_original/run_operational_experiments.py`; `python reproduce.py original` |
| Figure 3 | `paper_original/recorded/manylabs/`, with the independent source-level records in `current_method/results/full/` | `paper_original/run_manylabs2_framing.py`; `python reproduce.py original` |
| Figure 4 and Table 6 | `paper_figures/assets/figure5_nsw.pdf`, `legacy_audits/results/nsw_*`, `paper_figures/tables/main_nsw.tex` | `legacy_audits/scripts/run/run_nsw_experiment.py`; `python reproduce.py legacy-nsw` |
| Table 5 | `legacy_audits/results/extensions/synthetic_*` | `legacy_audits/scripts/run/run_requested_extensions.py synthetic` and `scripts/build/build_extension_artifacts.py`; `python reproduce.py legacy-extensions --profile full` |
| Table 7 | `legacy_audits/results/extensions/nsw_semisynthetic_*` | `legacy_audits/scripts/run/run_requested_extensions.py nsw`; `python reproduce.py legacy-extensions --profile full` |
| Figure 5 and Tables 9--10 | `current_method/results/workflow_full/` | `python reproduce.py workflow --profile full` |
| Tables 11--12 | `current_method/results/real_supplement/` | `python reproduce.py real` |
| Tables 13--14 and Figure 6 | `current_method/results/full/`, `paper_figures/assets/revision_sources.pdf` | `python reproduce.py current --profile full` and `python reproduce.py figures` |
| Tables 15--16 | `current_method/results/ablations_full/` | `python reproduce.py ablations --profile full`; `python reproduce.py audit-ablations` |
| Mechanism-set calibration audit | `current_method/results/mechanism_calibration/` | `python reproduce.py calibration --output reproduced/calibration` |

The existing PDF assets are the paper inputs. `paper_figures/render_appendix_figures.py`
regenerates the portable Figure 5/6 assets from committed CSV files; font and
PDF metadata differences can change their bytes without changing the plotted
values.

## Retained extension scope

The `legacy_audits/` directory is intentionally narrow. Its retained code is
the NSW protocol, the stronger source-only baselines, the NSW covariate
semi-synthetic extension, and the bridge/partial-identification dependencies
used by the extension builder. Earlier calibration, minimax, risk-coverage,
representation-sensitivity, and exploratory runner families are not part of
the current paper package.
