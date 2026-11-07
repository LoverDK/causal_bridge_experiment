"""Checks for the moment model, information boundary, acquisition and stopping."""
import copy
import json
from pathlib import Path
import unittest

import numpy as np

from atlas_new.non_gaussian_target_bridge import (METHODS, ObservationOracle, collect_mode,
    make_plans, normalized_config, run_world, score_rows, standardized, state_from_design)


class NonGaussianTargetChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frozen = json.loads((Path(__file__).parents[2]/'revision'/'NON_GAUSSIAN_TARGET_RUN01.json').read_text('utf-8'))
        cls.cfg = normalized_config(cls.frozen)
        cls.plans, cls.scores, cls.random_paths = make_plans(cls.cfg)

    def oracle(self, beta=0, noise=0, replicate=0):
        # Published old seed for tests; do not spend the independently frozen experiment seed.
        return ObservationOracle(self.cfg, 2026091801, 0, beta, noise, replicate)

    def test_primitive_variance_equals_covariance_quadratic_and_sherman(self):
        for path in self.plans.values():
            for state in path:
                self.assertAlmostEqual(state['W'], state['q'], places=12)
                self.assertAlmostEqual(state['W'], state['parameter_component']+state['noise_component'], places=14)
        for row in self.scores:
            self.assertAlmostEqual(row['exact_gain'], row['sherman_gain'], places=12)

    def test_target_really_minimizes_next_W_and_logdet_uses_half_gain(self):
        for geometry in self.cfg['geometries']:
            for stage in range(1,5):
                group = [r for r in self.scores if r['geometry']==geometry and r['stage']==stage and r['method']=='target_radius']
                self.assertEqual(sum(r['selected'] for r in group), 1)
                self.assertAlmostEqual(next(r['W_after'] for r in group if r['selected']), min(r['W_after'] for r in group))
                logrow = next(r for r in self.scores if r['geometry']==geometry and r['stage']==stage and r['method']=='logdet' and r['selected'])
                path = self.plans[(geometry, 'logdet')]
                before = np.asarray(path[stage-1]['inverse_precision'])
                after = np.asarray(path[stage]['inverse_precision'])
                self.assertAlmostEqual(logrow['logdet_gain'], .5*(np.linalg.slogdet(before)[1]-np.linalg.slogdet(after)[1]), places=11)

    def test_linear_estimator_uses_every_observation_and_common_information(self):
        state = self.plans[('distractor','target_radius')][2]
        y = np.array([.7, -.1, .2, -.3])
        X = np.asarray(state['features'])
        v = np.asarray(state['variances'])
        expected = np.asarray(self.cfg['target']) @ np.asarray(state['inverse_precision']) @ X.T @ (y/v)
        self.assertAlmostEqual(np.dot(state['weights'], y), expected, places=13)
        for geometry in self.cfg['geometries']:
            self.assertEqual(self.plans[(geometry,'target_radius')][0], self.plans[(geometry,'direct_target')][0])

    def test_stopped_and_prefix_agree_until_stop_then_stop_has_no_future_data(self):
        path = self.plans[('target_informative','target_radius')]
        oracle = self.oracle()
        stopped, se = collect_mode(self.cfg,path,oracle.acquire,'stopped')
        prefix, pe = collect_mode(self.cfg,path,oracle.acquire,'prefix')
        first = next((r['budget_stage'] for r in stopped if r['released']),4)
        self.assertEqual(len(se), first)
        self.assertEqual(len(pe),4)
        for s,p in zip(stopped[:first+1],prefix[:first+1]):
            self.assertEqual({k:v for k,v in s.items() if k!='mode'}, {k:v for k,v in p.items() if k!='mode'})
        for row in stopped[first:]:
            self.assertEqual(row['new_participants'],64*first)
            self.assertEqual(row['estimate'],stopped[first]['estimate'])
        self.assertEqual([r['new_participants'] for r in prefix],[0,64,128,192,256])

    def test_truth_cannot_change_any_policy_output(self):
        path = self.plans[('target_informative','frozen_random')]
        rows, _ = collect_mode(self.cfg,path,self.oracle().acquire,'prefix')
        a,b = score_rows(rows,0.),score_rows(rows,1000.)
        for raw,left,right in zip(rows,a,b):
            for key in raw:
                self.assertEqual(left[key],right[key])
        self.assertNotEqual(a[-1]['absolute_error'],b[-1]['absolute_error'])

    def test_outcomes_change_estimates_not_paths_widths_or_stop_cost(self):
        for geometry in self.cfg['geometries']:
            for method in METHODS:
                path = self.plans[(geometry,method)]
                base = self.oracle()
                def shifted(observation):
                    result = base.acquire(observation)
                    result['observed_effect'] += 123.
                    return result
                a,_ = collect_mode(self.cfg,path,base.acquire,'stopped')
                b,_ = collect_mode(self.cfg,path,shifted,'stopped')
                for left,right in zip(a,b):
                    for key in ['selected','W','radius','path_radius','new_participants','released','actual_stage']:
                        self.assertEqual(left[key],right[key])
                self.assertNotEqual(a[-1]['estimate'],b[-1]['estimate'])

    def test_real_balanced_arms_and_distinct_direct_visit_streams(self):
        oracle = self.oracle(beta=1,noise=2)
        path = self.plans[('target_informative','direct_target')]
        observations = [oracle.acquire(s['observations'][-1]) for s in path[1:]]
        self.assertEqual(len({tuple(o['stream_key']) for o in observations}),4)
        self.assertEqual(len({o['observed_effect'] for o in observations}),4)
        for o in observations:
            self.assertEqual(o['treated_n']+o['control_n'],64)
            self.assertAlmostEqual(o['observed_effect'],o['treated_mean']-o['control_mean'],places=15)
            self.assertEqual(o['noise_variance'],1/64)
        self.assertEqual(observations[0],oracle.acquire(path[1]['observations'][-1]))

    def test_distribution_scaling_and_frozen_random_path(self):
        a = standardized(np.random.default_rng(19),'student_t5',8)
        b = np.random.default_rng(19).standard_t(5,8)*np.sqrt(3/5)
        np.testing.assert_array_equal(a,b)
        changed = copy.deepcopy(self.cfg)
        changed['profiles']['full']['seed'] += 700
        _,_,again = make_plans(changed)
        self.assertEqual(self.random_paths,again)

    def test_width_thresholds_are_full_width_and_joint_budget_has_five_looks(self):
        self.assertEqual(self.cfg['width_thresholds'],[.4,.6,.8])
        self.assertEqual(self.cfg['main_halfwidth'],.3)
        for path in self.plans.values():
            for state in path:
                self.assertAlmostEqual(state['path_radius']/state['radius'],np.sqrt(5),places=12)

    def test_scientific_error_and_interval_miss_are_distinct_events(self):
        path = self.plans[('target_informative','target_radius')]
        rows,_ = collect_mode(self.cfg,path,self.oracle().acquire,'stopped')
        released = next(r for r in rows if r['released'])
        # This error exceeds the attained radius but still meets the declared .30 accuracy.
        intermediate_error = (released['radius'] + self.cfg['main_halfwidth']) / 2
        scored = score_rows([released],released['estimate']-intermediate_error)[0]
        self.assertTrue(scored['interval_miss_on_release'])
        self.assertFalse(scored['bad_release_scientific'])
        worse = score_rows([released],released['estimate']-1.)[0]
        self.assertTrue(worse['bad_release_scientific'])

    def test_every_estimate_reconstructs_from_saved_history_and_new_observations(self):
        cfg = copy.deepcopy(self.cfg)
        cfg['profiles']['smoke']['seed'] = 2026091801
        rows,events,_,history = run_world(cfg,'smoke',self.plans,0,1,2,1)
        self.assertEqual(len(history),2)
        for row in rows:
            observed = {h['id']:h['observed_effect'] for h in history}
            observed.update({e['id']:e['observed_effect'] for e in events
                             if e['method']==row['method'] and e['mode']==row['mode'] and e['stage']<=row['actual_stage']})
            state = self.plans[(row['geometry'],row['method'])][row['actual_stage']]
            rebuilt = np.dot(state['weights'],[observed[i] for i in state['ids']])
            self.assertAlmostEqual(rebuilt,row['estimate'],places=13)


if __name__ == '__main__':
    unittest.main()
