"""Outcome-blind calibration of joint mechanism uncertainty sets.

The calibration unit is an independently audited archive.  Each row contains
proxy errors for the complete decision universe (archive sources, candidate
bridges, and the target).  Calibrating the row-wise maximum gives one event
that remains valid after an outcome-blind selection from that universe.
"""
from __future__ import annotations

import math

import numpy as np

from .core import calibrated_quantile


def validate_errors(errors: np.ndarray) -> np.ndarray:
    """Return finite calibration errors with shape (archive, entity, dimension)."""
    values = np.asarray(errors, dtype=float)
    if values.ndim != 3 or min(values.shape) < 1 or not np.isfinite(values).all():
        raise ValueError("errors must be a finite (archive, entity, dimension) array")
    return values


def calibration_scores(errors: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Compute marginal and row-wise joint proxy-error scores."""
    values = validate_errors(errors)
    norms = np.linalg.norm(values, axis=2)
    return norms.ravel(), norms.max(axis=1)


def fit_joint_calibrator(errors: np.ndarray, eta: float) -> dict:
    """Fit a conformal-style joint radius from independent audit archives."""
    values = validate_errors(errors)
    if not 0 < eta < 1:
        raise ValueError("eta must lie in (0, 1)")
    marginal, joint = calibration_scores(values)
    return {
        "n_calibration": int(values.shape[0]),
        "n_entities": int(values.shape[1]),
        "dimension": int(values.shape[2]),
        "eta": float(eta),
        "joint_radius": calibrated_quantile(joint, eta),
        "marginal_radius": calibrated_quantile(marginal, eta),
        "max_calibration_score": float(joint.max()),
    }


def construct_mechanism_balls(proxies: np.ndarray, calibrator: dict,
                              scale: float = 1.0) -> dict:
    """Construct outcome-blind Euclidean balls ``Gamma(Z)`` around proxies."""
    centers = np.asarray(proxies, dtype=float)
    if centers.ndim != 2 or not np.isfinite(centers).all():
        raise ValueError("proxies must be a finite (entity, dimension) array")
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale must be positive and finite")
    if centers.shape != (calibrator["n_entities"], calibrator["dimension"]):
        raise ValueError("proxy shape must match the frozen calibration universe")
    radius = float(scale * calibrator["joint_radius"])
    return {"centers": centers.tolist(), "radius": radius,
            "calibration": dict(calibrator)}


def coverage(errors: np.ndarray, radius: float, *, joint: bool) -> np.ndarray:
    """Return one boolean per test archive for marginal or joint coverage."""
    values = validate_errors(errors)
    if not math.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and non-negative")
    norms = np.linalg.norm(values, axis=2)
    return np.all(norms <= radius, axis=1) if joint else np.mean(norms <= radius, axis=1)
