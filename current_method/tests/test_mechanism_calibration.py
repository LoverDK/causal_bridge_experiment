import unittest

import numpy as np

from atlas_new.mechanism_calibration import (coverage, fit_joint_calibrator,
                                             construct_mechanism_balls)


class MechanismCalibrationChecks(unittest.TestCase):
    def test_joint_radius_covers_a_calibrated_test_archive(self):
        rng = np.random.default_rng(51)
        cal = rng.normal(size=(199, 11, 2))
        fit = fit_joint_calibrator(cal, .05)
        test = rng.normal(size=(500, 11, 2))
        joint = coverage(test, fit["joint_radius"], joint=True)
        self.assertGreater(joint.mean(), .90)
        self.assertLess(joint.mean(), .995)

    def test_marginal_radius_is_not_a_joint_certificate(self):
        rng = np.random.default_rng(52)
        cal = rng.normal(size=(199, 11, 2))
        fit = fit_joint_calibrator(cal, .05)
        test = rng.normal(size=(1000, 11, 2))
        joint = coverage(test, fit["marginal_radius"], joint=True)
        self.assertLess(joint.mean(), .90)

    def test_gamma_does_not_accept_outcomes(self):
        fit = fit_joint_calibrator(np.ones((20, 3, 2)), .05)
        balls = construct_mechanism_balls(np.zeros((3, 2)), fit)
        self.assertEqual(len(balls["centers"]), 3)
        self.assertGreater(balls["radius"], 0)
        with self.assertRaises(ValueError):
            construct_mechanism_balls(np.zeros((2, 2)), fit)


if __name__ == "__main__":
    unittest.main()
