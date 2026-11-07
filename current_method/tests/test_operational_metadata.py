import unittest
from atlas_new.operational_metadata import operational_condition_labels


class OperationalMetadataTests(unittest.TestCase):
    def labels(self, scenario='nominal', method='robust_Rinf'):
        return operational_condition_labels(scenario, method, .05, .05)

    def test_legal_design_and_adaptive_rinf_have_certificate(self):
        for method in ('robust_Rinf', 'design_R2', 'adaptive_Rinf'):
            labels = self.labels(method=method)
            self.assertTrue(labels['certificate_guarantee_applicable'])
            self.assertEqual(labels['nominal_certificate_failure_bound'], .1)

    def test_negative_controls_do_not_inherit_scenario_validity(self):
        reasons = {
            'adaptive_R2_invalid': 'outcome_adaptive',
            'singleton_U': 'singletons',
            'no_curvature': 'Hessian',
        }
        for method, reason in reasons.items():
            labels = self.labels(method=method)
            self.assertFalse(labels['assumption_valid'])
            self.assertIsNone(labels['nominal_certificate_failure_bound'])
            self.assertIn(reason, labels['certificate_unsupported_reasons'])
            self.assertTrue(labels['outer_guarantee_applicable'])

    def test_point_only_has_no_certificate_assumption_boolean(self):
        for method in ('ridge_source_only', 'archive_mean'):
            labels = self.labels(method=method)
            self.assertIsNone(labels['assumption_valid'])
            self.assertEqual(labels['certificate_object'], 'none')
            self.assertTrue(labels['outer_guarantee_applicable'])

    def test_proxy_shift_and_understatement_also_affect_outer(self):
        for scenario in ('proxy_shift', 'understated_LH'):
            labels = self.labels(scenario=scenario)
            self.assertFalse(labels['certificate_guarantee_applicable'])
            self.assertFalse(labels['outer_guarantee_applicable'])
            self.assertIsNone(labels['nominal_outer_failure_bound'])

    def test_high_noise_and_bounded_bias_are_declared_not_omitted(self):
        for scenario in ('high_noise', 'bounded_nuisance_bias', 'extrapolation'):
            self.assertTrue(self.labels(scenario=scenario)['assumption_valid'])

    def test_unknown_inputs_never_get_silent_validity(self):
        with self.assertRaises(ValueError):
            self.labels(method='unknown_method')
        with self.assertRaises(ValueError):
            self.labels(scenario='unknown_scenario')


if __name__ == '__main__':
    unittest.main()
