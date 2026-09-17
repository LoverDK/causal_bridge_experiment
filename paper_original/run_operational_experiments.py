#!/usr/bin/env python3
"""Reproduce the theorem-linked operational Causal Atlas simulations.

The script is deliberately self-contained: it uses only synthetic draws from the
data-generating processes described below, writes every plotted summary to CSV,
and exports both a vector PDF and a high-resolution PNG.  No real-data claim is
made by this file.

Panels
------
A. A recorded descriptor is identical in source and target while an unrecorded
   mechanism coordinate shifts.  A sampling-only interval loses coverage; a
   Lipschitz uncertainty-set certificate remains valid on its declared domain.
B. A coordinate is selected after looking at K Gaussian summaries.  A pointwise
   interval undercovers, whereas a simultaneous Bonferroni interval protects
   arbitrary one-hot selection.
C. In the anchored Gaussian model, the worst-case absolute error of the anchor
   estimator is evaluated over the ambiguity radius Ld and inverse-information
   noise I^{-1/2}.  The two regimes meet on Ld = I^{-1/2}.
D. In Bayesian linear-Gaussian bridge design, log-determinant information gain
   is optimized by greedy selection and compared with exhaustive and random
   selection.  An inset gives an exact counterexample showing that partial-
   identification width reduction need not be submodular.
"""

from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from scipy.stats import norm


ROOT = Path(__file__).resolve().parent
FIGURE_DIR = ROOT / "figures"
SUMMARY_DIR = ROOT / "summaries"
TABLE_DIR = ROOT / "tables"

FIGURE_PDF = FIGURE_DIR / "figure_operational_theory_validation.pdf"
FIGURE_PNG = FIGURE_DIR / "figure_operational_theory_validation.png"

# Fixed seeds are panel-specific so that changing one panel does not perturb the
# draws in any other panel.
SEEDS = {
    "A": 2026091601,
    "B": 2026091602,
    "C": 2026091603,
    "D": 2026091604,
}
N_REP_A = 20_000
N_REP_B = 50_000
N_REP_C = 40_000
N_INSTANCES_D = 200
N_RANDOM_SUBSETS_D = 250

ALPHA = 0.05
Z_POINT = float(norm.ppf(1.0 - ALPHA / 2.0))

# Okabe--Ito colour-blind-safe palette, with neutral greys added for reference
# elements.  Every compared curve also differs in line style and marker.
BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
SKY = "#56B4E9"
PURPLE = "#CC79A7"
YELLOW = "#E69F00"
DARK = "#252525"
MID_GREY = "#737373"
LIGHT_GREY = "#D9D9D9"


def configure_matplotlib() -> None:
    """Use a compact, paper-oriented style with embedded vector text."""

    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 450,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.035,
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.2,
            "axes.titlesize": 9.0,
            "axes.labelsize": 8.2,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 8.0,
            "axes.linewidth": 0.75,
            "lines.linewidth": 1.55,
            "lines.markersize": 4.1,
            "xtick.major.width": 0.65,
            "ytick.major.width": 0.65,
            "xtick.minor.width": 0.5,
            "ytick.minor.width": 0.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def wilson_interval(successes: int, trials: int, alpha: float = ALPHA) -> tuple[float, float]:
    """Wilson score interval for a Bernoulli Monte Carlo proportion."""

    z = float(norm.ppf(1.0 - alpha / 2.0))
    p = successes / trials
    denom = 1.0 + z * z / trials
    centre = (p + z * z / (2.0 * trials)) / denom
    radius = z * math.sqrt(p * (1.0 - p) / trials + z * z / (4.0 * trials**2)) / denom
    return centre - radius, centre + radius


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def simulate_panel_a() -> list[dict[str, object]]:
    """Coverage under a hidden mechanism shift with a fixed uncertainty set."""

    rng = np.random.default_rng(SEEDS["A"])
    lipschitz = 1.0
    uncertainty_radius = 0.30
    n_sources = 4
    n_per_source = 25
    sigma = 1.0
    standard_error = sigma / math.sqrt(n_sources * n_per_source)
    shifts = np.linspace(0.0, 0.50, 26)

    # Common random numbers make differences between nearby shifts more precise.
    centre_noise = rng.normal(0.0, standard_error, size=N_REP_A)
    sampling_radius = Z_POINT * standard_error
    robust_radius = lipschitz * uncertainty_radius + sampling_radius

    rows: list[dict[str, object]] = []
    for shift in shifts:
        true_target = lipschitz * shift
        semantic_cover = np.abs(centre_noise - true_target) <= sampling_radius
        robust_cover = np.abs(centre_noise - true_target) <= robust_radius
        sem_success = int(semantic_cover.sum())
        rob_success = int(robust_cover.sum())
        sem_low, sem_high = wilson_interval(sem_success, N_REP_A)
        rob_low, rob_high = wilson_interval(rob_success, N_REP_A)
        rows.append(
            {
                "hidden_shift": float(shift),
                "recorded_descriptor_distance": 0.0,
                "inside_declared_uncertainty_set": int(shift <= uncertainty_radius + 1e-12),
                "semantic_coverage": sem_success / N_REP_A,
                "semantic_mc95_low": sem_low,
                "semantic_mc95_high": sem_high,
                "robust_certificate_coverage": rob_success / N_REP_A,
                "robust_mc95_low": rob_low,
                "robust_mc95_high": rob_high,
                "sampling_radius": sampling_radius,
                "operational_radius": robust_radius,
                "lipschitz_constant": lipschitz,
                "uncertainty_radius": uncertainty_radius,
                "source_standard_error": standard_error,
                "replications": N_REP_A,
                "seed": SEEDS["A"],
            }
        )

    write_csv(
        SUMMARY_DIR / "operational_panel_a_hidden_shift.csv",
        list(rows[0].keys()),
        rows,
    )
    return rows


def simulate_panel_b() -> list[dict[str, object]]:
    """Coverage after selecting the largest absolute Gaussian coordinate."""

    rng = np.random.default_rng(SEEDS["B"])
    archive_sizes = [1, 2, 4, 8, 16, 32, 64, 128]
    rows: list[dict[str, object]] = []

    for k in archive_sizes:
        z_draws = rng.standard_normal(size=(N_REP_B, k))
        selected_abs_z = np.max(np.abs(z_draws), axis=1)
        simultaneous_critical = float(norm.ppf(1.0 - ALPHA / (2.0 * k)))
        point_cover = selected_abs_z <= Z_POINT
        simultaneous_cover = selected_abs_z <= simultaneous_critical
        point_success = int(point_cover.sum())
        simultaneous_success = int(simultaneous_cover.sum())
        point_low, point_high = wilson_interval(point_success, N_REP_B)
        simultaneous_low, simultaneous_high = wilson_interval(simultaneous_success, N_REP_B)

        single_coordinate_mass = 2.0 * norm.cdf(Z_POINT) - 1.0
        simultaneous_coordinate_mass = 2.0 * norm.cdf(simultaneous_critical) - 1.0
        rows.append(
            {
                "archive_size_K": k,
                "pointwise_coverage": point_success / N_REP_B,
                "pointwise_mc95_low": point_low,
                "pointwise_mc95_high": point_high,
                "pointwise_exact_coverage": float(single_coordinate_mass**k),
                "simultaneous_coverage": simultaneous_success / N_REP_B,
                "simultaneous_mc95_low": simultaneous_low,
                "simultaneous_mc95_high": simultaneous_high,
                "simultaneous_exact_coverage": float(simultaneous_coordinate_mass**k),
                "pointwise_critical_value": Z_POINT,
                "bonferroni_critical_value": simultaneous_critical,
                "replications": N_REP_B,
                "seed": SEEDS["B"],
            }
        )

    write_csv(
        SUMMARY_DIR / "operational_panel_b_post_selection.csv",
        list(rows[0].keys()),
        rows,
    )
    return rows


def simulate_panel_c() -> list[dict[str, object]]:
    """Worst-case anchored-estimator MAE over ambiguity and sampling scales."""

    rng = np.random.default_rng(SEEDS["C"])
    z_draws = rng.standard_normal(size=N_REP_C)
    ambiguity_grid = np.logspace(-2.0, 0.0, 27)
    noise_grid = np.logspace(-2.0, 0.0, 27)
    rows: list[dict[str, object]] = []

    for inverse_information_noise in noise_grid:
        for ambiguity_radius in ambiguity_grid:
            # By symmetry, either endpoint of [-Ld, Ld] attains the same risk.
            absolute_errors = np.abs(
                inverse_information_noise * z_draws - ambiguity_radius
            )
            empirical_mae = float(absolute_errors.mean())
            risk_se = float(absolute_errors.std(ddof=1) / math.sqrt(N_REP_C))
            reference_rate = max(ambiguity_radius, inverse_information_noise)
            rows.append(
                {
                    "ambiguity_radius_Ld": float(ambiguity_radius),
                    "inverse_information_noise": float(inverse_information_noise),
                    "empirical_worst_case_mae": empirical_mae,
                    "mc_standard_error": risk_se,
                    "max_rate_reference": float(reference_rate),
                    "risk_to_max_rate_ratio": empirical_mae / reference_rate,
                    "dominant_regime": (
                        "mechanism ambiguity"
                        if ambiguity_radius >= inverse_information_noise
                        else "sampling noise"
                    ),
                    "replications": N_REP_C,
                    "seed": SEEDS["C"],
                }
            )

    write_csv(
        SUMMARY_DIR / "operational_panel_c_minimax_phase.csv",
        list(rows[0].keys()),
        rows,
    )
    return rows


def information_gain(
    prior_precision: np.ndarray,
    update_matrices: list[np.ndarray],
    subset: tuple[int, ...] | list[int],
) -> float:
    """Gaussian mutual information, up to the standard factor one half."""

    posterior_precision = prior_precision.copy()
    for index in subset:
        posterior_precision += update_matrices[index]
    prior_sign, prior_logdet = np.linalg.slogdet(prior_precision)
    post_sign, post_logdet = np.linalg.slogdet(posterior_precision)
    if prior_sign <= 0 or post_sign <= 0:
        raise RuntimeError("Precision matrices must be positive definite.")
    return 0.5 * float(post_logdet - prior_logdet)


def greedy_subset(
    prior_precision: np.ndarray,
    update_matrices: list[np.ndarray],
    budget: int,
) -> tuple[tuple[int, ...], float]:
    """Cardinality-constrained greedy maximization of information gain."""

    chosen: list[int] = []
    remaining = set(range(len(update_matrices)))
    current_value = 0.0
    for _ in range(budget):
        candidates = []
        for index in sorted(remaining):
            value = information_gain(
                prior_precision, update_matrices, chosen + [index]
            )
            candidates.append((value - current_value, -index, index, value))
        _, _, best_index, best_value = max(candidates)
        chosen.append(best_index)
        remaining.remove(best_index)
        current_value = best_value
    return tuple(sorted(chosen)), current_value


def simulate_panel_d() -> tuple[list[dict[str, object]], np.ndarray]:
    """Compare greedy, random, and exhaustive linear-Gaussian designs."""

    rng = np.random.default_rng(SEEDS["D"])
    dimension = 6
    n_candidates = 12
    budget = 4
    observation_noise_sd = 0.50
    all_subsets = list(itertools.combinations(range(n_candidates), budget))
    rows: list[dict[str, object]] = []
    all_random_ratios: list[float] = []

    for instance in range(N_INSTANCES_D):
        random_basis, _ = np.linalg.qr(rng.normal(size=(dimension, dimension)))
        prior_eigenvalues = np.exp(
            rng.uniform(math.log(0.35), math.log(3.0), size=dimension)
        )
        prior_covariance = (
            random_basis @ np.diag(prior_eigenvalues) @ random_basis.T
        )
        prior_precision = np.linalg.inv(prior_covariance)

        candidate_vectors = rng.normal(size=(n_candidates, dimension))
        candidate_vectors /= np.linalg.norm(candidate_vectors, axis=1, keepdims=True)
        candidate_scales = np.exp(rng.normal(0.0, 0.40, size=n_candidates))
        candidate_vectors *= candidate_scales[:, None]
        update_matrices = [
            np.outer(vector, vector) / observation_noise_sd**2
            for vector in candidate_vectors
        ]

        exhaustive_values = np.asarray(
            [
                information_gain(prior_precision, update_matrices, subset)
                for subset in all_subsets
            ]
        )
        optimal_position = int(np.argmax(exhaustive_values))
        optimal_subset = all_subsets[optimal_position]
        optimal_value = float(exhaustive_values[optimal_position])
        greedy_set, greedy_value = greedy_subset(
            prior_precision, update_matrices, budget
        )

        random_positions = rng.integers(
            0, len(all_subsets), size=N_RANDOM_SUBSETS_D
        )
        random_values = exhaustive_values[random_positions]
        random_ratios = random_values / optimal_value
        all_random_ratios.extend(random_ratios.tolist())

        rows.append(
            {
                "instance": instance,
                "dimension": dimension,
                "candidate_count": n_candidates,
                "budget": budget,
                "exhaustive_subset_count": len(all_subsets),
                "optimal_information_gain": optimal_value,
                "greedy_information_gain": greedy_value,
                "greedy_to_optimal_ratio": greedy_value / optimal_value,
                "random_mean_information_gain": float(random_values.mean()),
                "random_mean_to_optimal_ratio": float(random_ratios.mean()),
                "random_q10_to_optimal_ratio": float(np.quantile(random_ratios, 0.10)),
                "random_q90_to_optimal_ratio": float(np.quantile(random_ratios, 0.90)),
                "greedy_subset": " ".join(map(str, greedy_set)),
                "optimal_subset": " ".join(map(str, optimal_subset)),
                "random_subsets_per_instance": N_RANDOM_SUBSETS_D,
                "seed": SEEDS["D"],
            }
        )

    write_csv(
        SUMMARY_DIR / "operational_panel_d_bridge_design.csv",
        list(rows[0].keys()),
        rows,
    )
    # Exact finite counterexample used by the panel-D inset.  With
    # beta in [-1,1]^2 and target theta=beta_1, A observes beta_1+beta_2=0
    # and B observes beta_2=0.  Neither experiment alone narrows theta,
    # while the pair point-identifies it.
    pi_rows = [
        {"selected_bridges": "empty", "identified_width": 2.0, "width_reduction": 0.0},
        {"selected_bridges": "A", "identified_width": 2.0, "width_reduction": 0.0},
        {"selected_bridges": "B", "identified_width": 2.0, "width_reduction": 0.0},
        {"selected_bridges": "A+B", "identified_width": 0.0, "width_reduction": 2.0},
    ]
    write_csv(
        SUMMARY_DIR / "operational_panel_d_pi_counterexample.csv",
        list(pi_rows[0].keys()),
        pi_rows,
    )
    return rows, np.asarray(all_random_ratios)


def ecdf(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x_values = np.sort(np.asarray(values))
    probabilities = np.arange(1, len(x_values) + 1) / len(x_values)
    return x_values, probabilities


def panel_heading(axis: plt.Axes, letter: str, title: str) -> None:
    axis.text(
        -0.13,
        1.08,
        letter,
        transform=axis.transAxes,
        fontsize=10.2,
        fontweight="bold",
        va="top",
        ha="left",
    )
    axis.set_title(title, loc="left", pad=8.0, fontweight="semibold")


def style_axis(axis: plt.Axes, grid_axis: str = "both") -> None:
    axis.grid(
        True,
        which="major",
        axis=grid_axis,
        color=LIGHT_GREY,
        linewidth=0.55,
        alpha=0.65,
        zorder=0,
    )
    axis.tick_params(direction="out", length=2.6, pad=2.0)
    axis.set_axisbelow(True)


def plot_panel_a(axis: plt.Axes, rows: list[dict[str, object]]) -> None:
    shifts = np.asarray([row["hidden_shift"] for row in rows], dtype=float)
    sem = np.asarray([row["semantic_coverage"] for row in rows], dtype=float)
    sem_low = np.asarray([row["semantic_mc95_low"] for row in rows], dtype=float)
    sem_high = np.asarray([row["semantic_mc95_high"] for row in rows], dtype=float)
    robust = np.asarray(
        [row["robust_certificate_coverage"] for row in rows], dtype=float
    )
    robust_low = np.asarray([row["robust_mc95_low"] for row in rows], dtype=float)
    robust_high = np.asarray([row["robust_mc95_high"] for row in rows], dtype=float)
    q = float(rows[0]["uncertainty_radius"])

    axis.axvspan(0.0, q, color=SKY, alpha=0.11, linewidth=0)
    axis.axvline(q, color=MID_GREY, linestyle=(0, (2, 2)), linewidth=0.9)
    axis.axhline(0.95, color=DARK, linestyle=(0, (1.5, 2.2)), linewidth=0.85)
    axis.fill_between(shifts, sem_low, sem_high, color=ORANGE, alpha=0.15, linewidth=0)
    axis.fill_between(shifts, robust_low, robust_high, color=BLUE, alpha=0.15, linewidth=0)
    axis.plot(
        shifts,
        robust,
        color=BLUE,
        linestyle="-",
        marker="o",
        markevery=5,
        label="Operational set certificate",
        zorder=3,
    )
    axis.plot(
        shifts,
        sem,
        color=ORANGE,
        linestyle="--",
        marker="s",
        markevery=5,
        label="Semantic-only 95% interval",
        zorder=3,
    )
    axis.text(
        q / 2.0,
        0.09,
        r"declared $\mathcal{U}_\star$",
        ha="center",
        va="bottom",
        fontsize=8.0,
        color=BLUE,
    )
    axis.text(
        0.495,
        0.955,
        "95%",
        ha="right",
        va="bottom",
        fontsize=8.0,
        color=DARK,
    )
    axis.set_xlim(0.0, 0.50)
    axis.set_ylim(0.0, 1.02)
    axis.set_xlabel(r"Hidden mechanism shift $|m_\star-m_0|$ (recorded distance $=0$)")
    axis.set_ylabel("Coverage probability")
    axis.set_xticks(np.arange(0.0, 0.51, 0.10))
    axis.set_yticks(np.arange(0.0, 1.01, 0.20))
    axis.legend(loc="center left", frameon=False, handlelength=2.6)
    panel_heading(axis, "A", "Semantic similarity cannot certify reuse")
    style_axis(axis)


def plot_panel_b(axis: plt.Axes, rows: list[dict[str, object]]) -> None:
    k = np.asarray([row["archive_size_K"] for row in rows], dtype=int)
    point = np.asarray([row["pointwise_coverage"] for row in rows], dtype=float)
    point_low = np.asarray([row["pointwise_mc95_low"] for row in rows], dtype=float)
    point_high = np.asarray([row["pointwise_mc95_high"] for row in rows], dtype=float)
    simultaneous = np.asarray([row["simultaneous_coverage"] for row in rows], dtype=float)
    simultaneous_low = np.asarray(
        [row["simultaneous_mc95_low"] for row in rows], dtype=float
    )
    simultaneous_high = np.asarray(
        [row["simultaneous_mc95_high"] for row in rows], dtype=float
    )
    exact_point = np.asarray([row["pointwise_exact_coverage"] for row in rows], dtype=float)
    exact_sim = np.asarray(
        [row["simultaneous_exact_coverage"] for row in rows], dtype=float
    )

    axis.axhline(0.95, color=DARK, linestyle=(0, (1.5, 2.2)), linewidth=0.85)
    axis.fill_between(k, point_low, point_high, color=ORANGE, alpha=0.14, linewidth=0)
    axis.fill_between(
        k,
        simultaneous_low,
        simultaneous_high,
        color=GREEN,
        alpha=0.14,
        linewidth=0,
    )
    axis.plot(k, exact_sim, color=GREEN, linestyle="-", linewidth=1.65)
    axis.plot(k, exact_point, color=ORANGE, linestyle="--", linewidth=1.65)
    axis.scatter(k, simultaneous, color=GREEN, marker="o", s=16, zorder=3)
    axis.scatter(k, point, facecolor="white", edgecolor=ORANGE, marker="s", s=17, zorder=3)
    axis.set_xscale("log", base=2)
    axis.set_xlim(0.85, 155)
    axis.set_ylim(0.0, 1.02)
    axis.set_xticks(k)
    axis.set_xticklabels([str(value) for value in k])
    axis.set_yticks(np.arange(0.0, 1.01, 0.20))
    axis.set_xlabel(r"Archive size $K$ (select largest $|Z_j|$)")
    axis.set_ylabel("Post-selection coverage")
    axis.legend(
        handles=[
            Line2D(
                [0], [0], color=GREEN, marker="o", linestyle="-",
                label="Simultaneous Bonferroni"
            ),
            Line2D(
                [0], [0], color=ORANGE, marker="s", markerfacecolor="white",
                linestyle="--", label="Pointwise after selection"
            ),
        ],
        loc="center left",
        frameon=False,
        handlelength=2.6,
    )
    axis.text(
        145,
        0.955,
        "95%",
        ha="right",
        va="bottom",
        fontsize=8.0,
        color=DARK,
    )
    panel_heading(axis, "B", "Adaptive search needs simultaneous uncertainty")
    style_axis(axis)


def plot_panel_c(axis: plt.Axes, rows: list[dict[str, object]], fig: plt.Figure) -> None:
    ambiguity = np.unique(
        np.asarray([row["ambiguity_radius_Ld"] for row in rows], dtype=float)
    )
    noise = np.unique(
        np.asarray([row["inverse_information_noise"] for row in rows], dtype=float)
    )
    lookup = {
        (float(row["inverse_information_noise"]), float(row["ambiguity_radius_Ld"])):
        float(row["empirical_worst_case_mae"])
        for row in rows
    }
    risk = np.asarray(
        [[lookup[(float(b), float(a))] for a in ambiguity] for b in noise]
    )
    ratios = np.asarray([row["risk_to_max_rate_ratio"] for row in rows], dtype=float)

    mesh = axis.pcolormesh(
        ambiguity,
        noise,
        risk,
        cmap="cividis",
        norm=LogNorm(vmin=float(risk.min()), vmax=float(risk.max())),
        shading="nearest",
        rasterized=False,
    )
    contour_levels = np.asarray([0.03, 0.10, 0.30, 1.00])
    contours = axis.contour(
        ambiguity,
        noise,
        risk,
        levels=contour_levels,
        colors="white",
        linewidths=0.65,
        alpha=0.88,
    )
    axis.clabel(contours, fmt="%.2g", fontsize=8.0, inline=True)
    axis.plot(
        ambiguity,
        ambiguity,
        color=ORANGE,
        linestyle=(0, (4, 2)),
        linewidth=1.35,
    )
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xlim(float(ambiguity.min()), float(ambiguity.max()))
    axis.set_ylim(float(noise.min()), float(noise.max()))
    axis.set_xlabel(r"Mechanism ambiguity $Ld$")
    axis.set_ylabel(r"Sampling scale $I^{-1/2}$")
    axis.text(
        0.028,
        0.56,
        "sampling noise\ndominates",
        color="white",
        fontsize=8.0,
        ha="left",
        va="center",
    )
    axis.text(
        0.34,
        0.024,
        "ambiguity\ndominates",
        color="white",
        fontsize=8.0,
        ha="center",
        va="bottom",
    )
    axis.text(
        0.46,
        0.51,
        r"$Ld=I^{-1/2}$",
        color=ORANGE,
        fontsize=8.0,
        ha="right",
        va="bottom",
        rotation=36,
    )
    axis.text(
        0.045,
        0.013,
        rf"$R/\max\{{Ld,I^{{-1/2}}\}}\in[{ratios.min():.2f},{ratios.max():.2f}]$",
        color="white",
        fontsize=8.0,
        ha="left",
        va="bottom",
        bbox={"facecolor": DARK, "edgecolor": "none", "alpha": 0.52, "pad": 1.6},
    )
    colourbar = fig.colorbar(mesh, ax=axis, fraction=0.047, pad=0.025)
    colourbar.set_label("Worst-case MAE", fontsize=8.0)
    colourbar.ax.tick_params(labelsize=8.0, width=0.55, length=2.2)
    panel_heading(axis, "C", "Anchored risk follows the two-regime rate")
    axis.tick_params(direction="out", length=2.6, pad=2.0)


def add_non_submodular_inset(axis: plt.Axes) -> None:
    inset = axis.inset_axes([0.025, 0.47, 0.47, 0.46])
    inset.set_axis_off()
    box = {"boxstyle": "round,pad=0.18", "fc": "white", "ec": MID_GREY, "lw": 0.65}
    positions = {
        "empty": (0.50, 0.88),
        "a": (0.23, 0.52),
        "b": (0.77, 0.52),
        "ab": (0.50, 0.14),
    }
    inset.text(*positions["empty"], r"$\varnothing$: $w=2$", ha="center", va="center", fontsize=8.0, bbox=box)
    inset.text(*positions["a"], r"$A$: $w=2$", ha="center", va="center", fontsize=8.0, bbox=box)
    inset.text(*positions["b"], r"$B$: $w=2$", ha="center", va="center", fontsize=8.0, bbox=box)
    inset.text(
        *positions["ab"],
        r"$A+B$: $w=0$",
        ha="center",
        va="center",
        fontsize=8.0,
        color=ORANGE,
        bbox={**box, "ec": ORANGE},
    )
    arrow = {"arrowstyle": "-|>", "color": MID_GREY, "lw": 0.55, "shrinkA": 10, "shrinkB": 10}
    for source, target in [("empty", "a"), ("empty", "b"), ("a", "ab"), ("b", "ab")]:
        inset.annotate("", xy=positions[target], xytext=positions[source], arrowprops=arrow)
    inset.text(
        0.50,
        -0.09,
        r"$\Delta(A\mid\varnothing)=0<2=\Delta(A\mid B)$",
        ha="center",
        va="bottom",
        fontsize=8.0,
        color=ORANGE,
        clip_on=False,
    )
    inset.text(
        0.02,
        1.03,
        "PI-width gain is complementary",
        ha="left",
        va="top",
        fontsize=8.0,
        fontweight="semibold",
    )


def plot_panel_d(
    axis: plt.Axes,
    rows: list[dict[str, object]],
    random_ratios: np.ndarray,
) -> None:
    greedy_ratios = np.asarray(
        [row["greedy_to_optimal_ratio"] for row in rows], dtype=float
    )
    random_x, random_y = ecdf(random_ratios)
    greedy_x, greedy_y = ecdf(greedy_ratios)
    guarantee = 1.0 - 1.0 / math.e

    axis.axvspan(0.0, guarantee, color=ORANGE, alpha=0.07, linewidth=0)
    axis.axvline(
        guarantee,
        color=ORANGE,
        linestyle=(0, (2, 2)),
        linewidth=1.0,
    )
    axis.axvline(1.0, color=DARK, linestyle=(0, (1.5, 2.0)), linewidth=0.9)
    axis.plot(
        random_x,
        random_y,
        color=MID_GREY,
        linestyle="--",
        linewidth=1.5,
        label="Random subsets",
    )
    axis.plot(
        greedy_x,
        greedy_y,
        color=BLUE,
        linestyle="-",
        linewidth=1.8,
        label="Logdet greedy",
    )
    axis.scatter(
        greedy_x[:: max(1, len(greedy_x) // 14)],
        greedy_y[:: max(1, len(greedy_y) // 14)],
        color=BLUE,
        marker="o",
        s=10,
        zorder=3,
    )
    axis.set_xlim(0.48, 1.012)
    axis.set_ylim(0.0, 1.02)
    axis.set_xlabel("Information gain / exhaustive optimum")
    axis.set_ylabel("Empirical CDF")
    axis.set_xticks([0.50, guarantee, 0.75, 0.875, 1.00])
    axis.set_xticklabels(["0.50", r"$1-1/e$", "0.75", "0.88", "1.00"])
    axis.set_yticks(np.arange(0.0, 1.01, 0.20))
    axis.text(
        0.996,
        0.045,
        "exhaustive",
        ha="right",
        va="bottom",
        rotation=90,
        fontsize=8.0,
        color=DARK,
    )
    axis.legend(loc="lower right", frameon=False, handlelength=2.6)
    add_non_submodular_inset(axis)
    panel_heading(axis, "D", "A theorem-valid surrogate enables bridge design")
    style_axis(axis)


def render_figure(
    panel_a: list[dict[str, object]],
    panel_b: list[dict[str, object]],
    panel_c: list[dict[str, object]],
    panel_d: list[dict[str, object]],
    random_ratios: np.ndarray,
) -> None:
    configure_matplotlib()
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(6.85, 5.65),
        constrained_layout=True,
        gridspec_kw={"wspace": 0.08, "hspace": 0.10},
    )
    plot_panel_a(axes[0, 0], panel_a)
    plot_panel_b(axes[0, 1], panel_b)
    plot_panel_c(axes[1, 0], panel_c, fig)
    plot_panel_d(axes[1, 1], panel_d, random_ratios)

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "Title": "Operational Causal Atlas theorem-linked simulations",
        "Author": "Generated reproducibly by run_operational_experiments.py",
        "Subject": "Synthetic validation only; no real-data claims",
        "Creator": "Matplotlib",
    }
    fig.savefig(FIGURE_PDF, format="pdf", metadata=metadata)
    fig.savefig(FIGURE_PNG, format="png", dpi=450, metadata={"Software": "Matplotlib"})
    plt.close(fig)


def write_manifest_and_table(
    panel_a: list[dict[str, object]],
    panel_b: list[dict[str, object]],
    panel_c: list[dict[str, object]],
    panel_d: list[dict[str, object]],
) -> list[dict[str, object]]:
    certified_a = [
        row for row in panel_a if int(row["inside_declared_uncertainty_set"]) == 1
    ]
    row_a_q = min(
        panel_a,
        key=lambda row: abs(
            float(row["hidden_shift"]) - float(row["uncertainty_radius"])
        ),
    )
    row_b_max = max(panel_b, key=lambda row: int(row["archive_size_K"]))
    ratios_c = np.asarray(
        [float(row["risk_to_max_rate_ratio"]) for row in panel_c]
    )
    greedy_d = np.asarray(
        [float(row["greedy_to_optimal_ratio"]) for row in panel_d]
    )
    random_d = np.asarray(
        [float(row["random_mean_to_optimal_ratio"]) for row in panel_d]
    )

    manifest = [
        {
            "panel": "A",
            "seed": SEEDS["A"],
            "monte_carlo_units": f"{N_REP_A} replications per hidden-shift value",
            "diagnostic": "minimum robust coverage on declared uncertainty set",
            "value": min(float(row["robust_certificate_coverage"]) for row in certified_a),
        },
        {
            "panel": "A",
            "seed": SEEDS["A"],
            "monte_carlo_units": f"{N_REP_A} replications per hidden-shift value",
            "diagnostic": "semantic-only coverage at uncertainty boundary",
            "value": float(row_a_q["semantic_coverage"]),
        },
        {
            "panel": "B",
            "seed": SEEDS["B"],
            "monte_carlo_units": f"{N_REP_B} replications per K",
            "diagnostic": "pointwise coverage at K=128",
            "value": float(row_b_max["pointwise_coverage"]),
        },
        {
            "panel": "B",
            "seed": SEEDS["B"],
            "monte_carlo_units": f"{N_REP_B} replications per K",
            "diagnostic": "simultaneous coverage at K=128",
            "value": float(row_b_max["simultaneous_coverage"]),
        },
        {
            "panel": "C",
            "seed": SEEDS["C"],
            "monte_carlo_units": f"{N_REP_C} common Gaussian draws on 27x27 grid",
            "diagnostic": "minimum risk / max-rate ratio",
            "value": float(ratios_c.min()),
        },
        {
            "panel": "C",
            "seed": SEEDS["C"],
            "monte_carlo_units": f"{N_REP_C} common Gaussian draws on 27x27 grid",
            "diagnostic": "maximum risk / max-rate ratio",
            "value": float(ratios_c.max()),
        },
        {
            "panel": "D",
            "seed": SEEDS["D"],
            "monte_carlo_units": (
                f"{N_INSTANCES_D} instances; 495 exhaustive and "
                f"{N_RANDOM_SUBSETS_D} random subsets per instance"
            ),
            "diagnostic": "minimum greedy / exhaustive information gain",
            "value": float(greedy_d.min()),
        },
        {
            "panel": "D",
            "seed": SEEDS["D"],
            "monte_carlo_units": (
                f"{N_INSTANCES_D} instances; 495 exhaustive and "
                f"{N_RANDOM_SUBSETS_D} random subsets per instance"
            ),
            "diagnostic": "mean random / exhaustive information gain",
            "value": float(random_d.mean()),
        },
    ]
    write_csv(
        SUMMARY_DIR / "operational_simulation_manifest.csv",
        list(manifest[0].keys()),
        manifest,
    )

    table_path = TABLE_DIR / "app_operational_simulation_manifest.tex"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "% Generated by run_operational_experiments.py; do not edit by hand.",
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Reproducibility manifest for the theorem-linked synthetic experiments. "
        "All entries are Monte Carlo results from prespecified synthetic data-generating "
        "processes; none is a real-data estimate.}",
        "\\label{tab:operational-simulation-manifest}",
        "\\footnotesize",
        "\\begin{tabular}{@{}cllr@{}}",
        "\\toprule",
        "Panel & Seed & Monte Carlo units & Diagnostic value \\\\",
        "\\midrule",
        f"A & {SEEDS['A']} & {N_REP_A:,} per shift & "
        f"min. certified coverage {manifest[0]['value']:.3f} \\\\",
        f"A & {SEEDS['A']} & {N_REP_A:,} per shift & "
        f"semantic coverage at boundary {manifest[1]['value']:.3f} \\\\",
        f"B & {SEEDS['B']} & {N_REP_B:,} per $K$ & "
        f"pointwise/simultaneous at $K=128$: {manifest[2]['value']:.3f}/{manifest[3]['value']:.3f} \\\\",
        f"C & {SEEDS['C']} & {N_REP_C:,} on $27\\times27$ grid & "
        f"risk/rate range [{manifest[4]['value']:.3f}, {manifest[5]['value']:.3f}] \\\\",
        f"D & {SEEDS['D']} & {N_INSTANCES_D} instances & "
        f"min. greedy ratio {manifest[6]['value']:.3f} \\\\",
        f"D & {SEEDS['D']} & {N_RANDOM_SUBSETS_D} random/instance & "
        f"mean random ratio {manifest[7]['value']:.3f} \\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table*}",
        "",
    ]
    table_path.write_text("\n".join(lines), encoding="utf-8")

    caption_path = SUMMARY_DIR / "figure_operational_theory_validation_caption.tex"
    caption_path.write_text(
        "\\caption{Operational uncertainty, rather than semantic proximity alone, "
        "determines when archived causal evidence can be reused. "
        "\\textbf{A}: although every recorded descriptor is identical, a hidden "
        "mechanism shift makes the sampling-only interval undercover; the robust "
        "interval retains at least nominal coverage throughout its declared "
        "uncertainty set (shading). Ribbons are 95\\% Wilson Monte Carlo intervals. "
        "\\textbf{B}: selecting the largest absolute coordinate makes pointwise "
        "coverage collapse with archive size, while simultaneous Bonferroni "
        "protection remains valid. Curves are exact Gaussian probabilities and "
        "markers are Monte Carlo estimates. "
        "\\textbf{C}: in the anchored Gaussian model, the empirical worst-case "
        "mean absolute error follows $\\max\\{Ld,I^{-1/2}\\}$, with the dashed line "
        "separating ambiguity- and noise-dominated regimes; white curves are "
        "iso-risk contours. "
        "\\textbf{D}: for linear-Gaussian bridge design, log-determinant greedy "
        "selection nearly matches exhaustive search across 200 generated design "
        "instances and exceeds the worst-case $1-1/e$ guarantee. The inset gives "
        "an exact non-submodularity witness for partial-identification (PI) width: "
        "for $\\beta\\in[-1,1]^2$ and target $\\beta_1$, bridge "
        "$A$ observes $\\beta_1+\\beta_2=0$ and bridge $B$ observes "
        "$\\beta_2=0$; neither reduces width alone, whereas their combination "
        "point-identifies the target. All panels are synthetic, with seeds and "
        "replication counts in Table~\\ref{tab:operational-simulation-manifest}.}\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    panel_a = simulate_panel_a()
    panel_b = simulate_panel_b()
    panel_c = simulate_panel_c()
    panel_d, random_ratios = simulate_panel_d()
    render_figure(panel_a, panel_b, panel_c, panel_d, random_ratios)
    manifest = write_manifest_and_table(panel_a, panel_b, panel_c, panel_d)

    # Fail loudly if a future code change breaks the theorem-linked invariants.
    certified_a = [
        row for row in panel_a if int(row["inside_declared_uncertainty_set"]) == 1
    ]
    assert min(float(row["robust_certificate_coverage"]) for row in certified_a) >= 0.95
    assert float(panel_b[-1]["simultaneous_coverage"]) >= 0.94
    assert min(float(row["greedy_to_optimal_ratio"]) for row in panel_d) >= 1.0 - 1.0 / math.e - 1e-10

    print(f"Wrote vector figure: {FIGURE_PDF}")
    print(f"Wrote raster preview: {FIGURE_PNG}")
    print(f"Wrote summaries under: {SUMMARY_DIR}")
    print(f"Wrote LaTeX table under: {TABLE_DIR}")
    for row in manifest:
        print(
            f"Panel {row['panel']} | {row['diagnostic']}: "
            f"{float(row['value']):.6f}"
        )


if __name__ == "__main__":
    main()
