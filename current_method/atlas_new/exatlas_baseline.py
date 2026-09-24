"""A transparent ExAtlas-style composition baseline.

This module implements the composition part of ExAtlas (arXiv:2605.27153)
without its LLM enrichment, reconciliation, or bridge-suggestion modules.
It is an evaluation baseline, not a claim of reproducing the full system.
The target outcome is never used for fitting or the composability decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .dgp import ExperimentData
from .methods import design_compatible


@dataclass(frozen=True)
class ExAtlasConfig:
    """Protocol constants for the composition-only comparison."""

    residual_threshold: float = 0.35
    candidate_limit: int | None = None
    ridge: float = 1e-8

    def __post_init__(self) -> None:
        if self.residual_threshold < 0.0:
            raise ValueError("residual_threshold must be nonnegative.")
        if self.candidate_limit is not None and self.candidate_limit < 1:
            raise ValueError("candidate_limit must be positive when supplied.")
        if self.ridge < 0.0:
            raise ValueError("ridge must be nonnegative.")


@dataclass(frozen=True)
class ExAtlasResult:
    """Prediction and composability diagnostics for one held-out target."""

    method: str
    candidate_indices: tuple[int, ...]
    weights: np.ndarray
    representation_residual: float
    normalized_residual: float
    composable: bool
    point_estimate: float | None
    raw_point_estimate: float


def exatlas_representation(experiment: ExperimentData) -> np.ndarray:
    """Build the paper's treatment--outcome--interaction style representation.

    The synthetic archive has two public coordinates assigned to a treatment
    block and two to an outcome block.  The cross-block interaction is included
    to mirror ExAtlas's joint treatment/outcome representation.  This mapping
    is fixed before seeing target outcomes.
    """

    treatment = np.asarray(experiment.observed_representation[:2], dtype=float)
    outcome = np.asarray(experiment.observed_representation[2:], dtype=float)
    return np.concatenate((treatment, outcome, treatment * outcome))


def _project_to_simplex(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    order = np.sort(values)[::-1]
    cumulative = np.cumsum(order)
    eligible = order - (cumulative - 1.0) / (np.arange(values.size) + 1) > 0
    if not np.any(eligible):
        return np.full(values.size, 1.0 / values.size)
    rho = int(np.flatnonzero(eligible)[-1])
    threshold = (cumulative[rho] - 1.0) / (rho + 1)
    return np.maximum(values - threshold, 0.0)


def _simplex_least_squares(
    source_matrix: np.ndarray,
    target: np.ndarray,
    ridge: float,
) -> np.ndarray:
    """Solve min ||target - X^T alpha||^2 + ridge||alpha||^2 on a simplex."""

    gram = source_matrix @ source_matrix.T + ridge * np.eye(source_matrix.shape[0])
    linear = source_matrix @ target
    # Projected gradient uses a conservative Lipschitz step and is deterministic.
    largest = float(np.linalg.eigvalsh(2.0 * gram).max())
    step = 1.0 / max(largest, 1e-12)
    weights = np.full(source_matrix.shape[0], 1.0 / source_matrix.shape[0])
    for _ in range(4000):
        gradient = 2.0 * (gram @ weights - linear)
        proposal = _project_to_simplex(weights - step * gradient)
        if np.linalg.norm(proposal - weights) <= 1e-11:
            return proposal
        weights = proposal
    return weights


def fit_exatlas_style(
    archive: Sequence[ExperimentData],
    target: ExperimentData,
    config: ExAtlasConfig | None = None,
) -> ExAtlasResult:
    """Fit composition-only ExAtlas-style transport on public archive inputs."""

    config = config or ExAtlasConfig()
    compatible = tuple(
        index for index, source in enumerate(archive) if design_compatible(source, target)
    )
    if config.candidate_limit is not None:
        target_representation = exatlas_representation(target)
        compatible = tuple(
            sorted(
                compatible,
                key=lambda index: (
                    float(np.linalg.norm(exatlas_representation(archive[index]) - target_representation)),
                    index,
                ),
            )[: config.candidate_limit]
        )
    if not compatible:
        return ExAtlasResult(
            method="exatlas_style",
            candidate_indices=(),
            weights=np.zeros(len(archive), dtype=float),
            representation_residual=float("inf"),
            normalized_residual=float("inf"),
            composable=False,
            point_estimate=None,
            raw_point_estimate=float("nan"),
        )

    source_matrix = np.vstack([exatlas_representation(archive[index]) for index in compatible])
    target_representation = exatlas_representation(target)
    local_weights = _simplex_least_squares(source_matrix, target_representation, config.ridge)
    reconstruction = local_weights @ source_matrix
    residual = float(np.linalg.norm(target_representation - reconstruction))
    pairwise = np.linalg.norm(source_matrix - target_representation, axis=1)
    local_scale = float(np.median(pairwise))
    normalized = residual / max(local_scale, 1e-12)
    composable = bool(normalized <= config.residual_threshold + 1e-12)
    weights = np.zeros(len(archive), dtype=float)
    weights[list(compatible)] = local_weights
    raw = float(sum(weight * source.estimated_effect for weight, source in zip(weights, archive, strict=True)))
    return ExAtlasResult(
        method="exatlas_style",
        candidate_indices=compatible,
        weights=weights,
        representation_residual=residual,
        normalized_residual=normalized,
        composable=composable,
        point_estimate=raw if composable else None,
        raw_point_estimate=raw,
    )
