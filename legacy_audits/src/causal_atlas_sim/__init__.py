"""Retained NSW and extension implementation for the current paper package.

Import submodules explicitly; the package initializer intentionally has no
side-effect imports so removed historical experiment families cannot be
pulled in accidentally.
"""
from .dgp import (
    EFFECT_CURVATURE_BOUND,
    EFFECT_LIPSCHITZ_BOUND,
    SimulationConfig,
    effect_gradient,
    effect_hessian,
    generate_minimal_archive,
    minimal_assumption_report,
)

__all__ = [
    'EFFECT_CURVATURE_BOUND', 'EFFECT_LIPSCHITZ_BOUND', 'SimulationConfig',
    'effect_gradient', 'effect_hessian', 'generate_minimal_archive',
    'minimal_assumption_report',
]
