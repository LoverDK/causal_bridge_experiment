import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "run"))

from run_nsw_real_proxy_truth import (  # noqa: E402
    _potential_outcomes,
    _quantile_order_statistic,
    split_participants,
)


class NswRealProxyTruthTests(unittest.TestCase):
    def test_nsw_split_is_disjoint_and_preserves_original_assignment_counts(self):
        treatment = np.array([0] * 260 + [1] * 185)
        pools = split_participants(treatment)
        self.assertFalse(set(pools["development"]) & set(pools["calibration"]))
        self.assertFalse(set(pools["development"]) & set(pools["validation"]))
        self.assertFalse(set(pools["calibration"]) & set(pools["validation"]))
        self.assertEqual(sorted(np.concatenate(list(pools.values())).tolist()), list(range(len(treatment))))
        self.assertEqual(sum(len(ids) for ids in pools.values()), len(treatment))
        for arm in (0, 1):
            self.assertEqual(sum(int(np.sum(treatment[ids] == arm)) for ids in pools.values()), int(np.sum(treatment == arm)))

    def test_semisynthetic_potential_outcomes_have_exact_unit_effect_and_share_noise(self):
        x = np.arange(80, dtype=float).reshape(10, 8) / 10
        noise = np.linspace(-1, 1, 10)
        for surface in ("constant", "smooth", "interaction"):
            y0, y1, tau = _potential_outcomes(x, noise, surface)
            np.testing.assert_allclose(y1 - y0, tau)

    def test_split_conformal_order_statistic_uses_finite_sample_rank(self):
        self.assertEqual(_quantile_order_statistic([1, 2, 3, 4], alpha=0.4), 3)
        self.assertTrue(np.isinf(_quantile_order_statistic([1, 2], alpha=0.1)))


if __name__ == "__main__":
    unittest.main()
