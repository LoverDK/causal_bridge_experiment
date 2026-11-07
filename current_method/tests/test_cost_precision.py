"""Meaningful checks for changed acquisition, paired outputs and information flow."""
import copy
import json
import math
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from atlas_new.cost_precision import (collect_full_prefix, evaluate_prefix, execute_prefix,
                                     predict_snapshot, radius_decomposition, reconstruct_calibration,
                                     run_world, validate_outputs)
from atlas_new.workflow import certificate, collect, execute, make_world, plan


class CostPrecisionChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((Path(__file__).parents[1]/'configs'/'cost_precision_smoke.json').read_text('utf-8'))
        # Tests use an already published seed, not the unobserved new full seed.
        cls.cfg['seed'] = 2026091801
        cls.world = make_world(cls.cfg, 0, 1, 0)
        cls.design = cls.world['design']
        cls.paths = {method: ([] if method == 'target_only' else plan(cls.design, method, [4,5,6,7,8,9])[0])
                     for method in cls.cfg['methods']}

    def test_agrees_with_legacy_execute_until_its_first_stop(self):
        for method, path in self.paths.items():
            for tolerance in self.cfg['tolerances']:
                with self.subTest(method=method, tolerance=tolerance):
                    prefix, pevents = execute_prefix(self.cfg, self.world, method, path, tolerance)
                    stopped, sevents = execute(self.cfg, self.world, method, path, tolerance)
                    for left, right in zip(prefix, stopped):
                        for key in ['estimate','radius','lower','upper','refusal_lower','refusal_upper','width']:
                            self.assertAlmostEqual(left[key], right[key], places=11)
                        for key in ['selected','source_ids','weights','released','new_n','covered','path_covered']:
                            self.assertEqual(left[key], right[key])
                        if right['released'] or method == 'r2_static':
                            break
                    self.assertEqual(pevents[:len(sevents)], sevents)

    def test_collects_after_release_while_legacy_stops(self):
        prefix, pevents = execute_prefix(self.cfg, self.world, 'target_only', [], .3)
        stopped, sevents = execute(self.cfg, self.world, 'target_only', [], .3)
        self.assertEqual(len(pevents), 3)
        self.assertEqual(len(sevents), 1)
        self.assertEqual([r['new_n'] for r in prefix], [0,96,192,288])
        self.assertEqual([r['new_n'] for r in stopped], [0,96,96,96])
        for stage in range(1,4):
            self.assertAlmostEqual(prefix[stage]['estimate'], np.mean([e['effect'] for e in pevents[:stage]]))
            for e in pevents[:stage]:
                self.assertEqual(e['effect'], e['treated_mean']-e['control_mean'])
        supported = make_world(self.cfg, 0, 0, 0)
        path = plan(supported['design'],'r2_targeted',[4,5,6,7,8,9])[0]
        pre, acquired = execute_prefix(self.cfg,supported,'r2_targeted',path,.3)
        old, old_acquired = execute(self.cfg,supported,'r2_targeted',path,.3)
        self.assertTrue(old[0]['released'])
        self.assertEqual(old_acquired, [])
        self.assertEqual(len(acquired), 3)
        self.assertEqual(pre[-1]['new_n'], 288)

    def test_static_does_not_spend_an_available_budget(self):
        rows, events = execute_prefix(self.cfg,self.world,'r2_static',self.paths['r2_static'],.2)
        self.assertEqual(events, [])
        self.assertEqual([r['new_n'] for r in rows], [0,0,0,0])
        self.assertTrue(all(not r['new_observation'] for r in rows))

    def test_scoring_truth_cannot_change_multiround_decisions_or_data(self):
        snapshots, events = collect_full_prefix(self.cfg,self.world,'r2_targeted',self.paths['r2_targeted'])
        a = evaluate_prefix(self.design,'r2_targeted',snapshots,.2,-.015,True)
        b = evaluate_prefix(self.design,'r2_targeted',snapshots,.2,1000.,True)
        self.assertEqual(len(events),3)
        for left, right in zip(a,b):
            for key in ['selected','weights','radius','estimate','released','new_n','lower','upper','refusal_reason']:
                self.assertEqual(left[key],right[key])
        self.assertNotEqual(a[-1]['covered'],b[-1]['covered'])

    def test_changed_observed_effects_change_estimate_not_design_decisions(self):
        path = self.paths['r2_targeted']
        ids = path[2]['ids']
        obs = {j:collect(self.world,j,self.cfg['archive_participants'] if j<4 else 96) for j in ids}
        altered = copy.deepcopy(obs)
        for observation in altered.values():
            observation['effect'] += .7
            observation['treated_mean'] += .7
        before = predict_snapshot(self.design,'r2_targeted',2,path,obs,[])
        after = predict_snapshot(self.design,'r2_targeted',2,path,altered,[])
        self.assertEqual(before['weights'],after['weights'])
        self.assertEqual(before['radius'],after['radius'])
        self.assertAlmostEqual(after['estimate']-before['estimate'],.7)
        self.assertAlmostEqual(after['refusal_lower']-before['refusal_lower'],.7)
        self.assertAlmostEqual(after['refusal_upper']-before['refusal_upper'],.7)

    def test_saved_decomposition_matches_legacy_certificate(self):
        for method,path in self.paths.items():
            if method == 'target_only':
                continue
            mode = 'rinf' if method == 'rinf_targeted' else 'r2'
            for state in path:
                parts = radius_decomposition(self.design,state['ids'],state['weights'],mode)
                radius = certificate(self.design,state['ids'],state['weights'],mode)
                self.assertAlmostEqual(min(parts['barycentric_bound'],parts['lipschitz_bound'])+parts['noise_term'],radius)
        curved = make_world(self.cfg,1,1,0)
        path = plan(curved['design'],'r2_targeted',[4,5,6,7,8,9])[0]
        for state in path:
            parts = radius_decomposition(curved['design'],state['ids'],state['weights'],'r2')
            self.assertGreaterEqual(parts['curvature'],0)
            self.assertAlmostEqual(parts['geometric_bound']+parts['noise_term'],state['radius'])

    def test_calibration_reconstruction_and_joint_coverage_log(self):
        for surface_id,scenario_id in [(0,1),(1,0),(2,2)]:
            world = make_world(self.cfg,surface_id,scenario_id,0)
            c = reconstruct_calibration(self.cfg,world)
            self.assertEqual(c['rank'],190)
            self.assertEqual(len(c['scores']),199)
            self.assertEqual(c['quantile'],sorted(c['scores'])[189])
            self.assertEqual(c['quantile'],world['calibration_q'])
            self.assertEqual(c['radius'],world['design'].target_radius)
            d=world['design']
            errors=np.linalg.norm(np.vstack([d.centers,d.target_center])-world['locations'],axis=1)
            self.assertEqual(world['joint_set_covered'],bool(np.all(errors<=c['radius'])))

    def test_halfwidth_and_midpoint_preserve_refusal_semantics(self):
        rows,_ = execute_prefix(self.cfg,self.world,'r2_targeted',self.paths['r2_targeted'],.2)
        self.assertEqual(rows[1]['output_kind'],'refusal_outer')
        self.assertAlmostEqual(rows[1]['output_halfwidth'],.652879251026209/2)
        self.assertNotAlmostEqual(rows[1]['output_halfwidth'],rows[1]['radius'])
        self.assertNotAlmostEqual(rows[1]['midpoint'],rows[1]['estimate'])
        self.assertEqual(rows[2]['output_kind'],'released_interval')
        self.assertAlmostEqual(rows[2]['output_halfwidth'],rows[2]['radius'])
        targets,_ = execute_prefix(self.cfg,self.world,'target_only',[],.3)
        self.assertEqual(targets[0]['output_kind'],'unbounded')
        self.assertTrue(math.isinf(targets[0]['output_halfwidth']))
        self.assertTrue(math.isnan(targets[0]['midpoint']))
        snapshots,_=collect_full_prefix(self.cfg,self.world,'r2_targeted',self.paths['r2_targeted'])
        altered=copy.deepcopy(snapshots[:1]);altered[0]['refusal_lower']=2.;altered[0]['refusal_upper']=1.
        bad=evaluate_prefix(self.design,'r2_targeted',altered,.2,-.015,True)[0]
        self.assertEqual(bad['interval_status'],'inconsistent')
        self.assertTrue(math.isnan(bad['output_halfwidth']))
        self.assertTrue(math.isnan(bad['midpoint']))
        self.assertFalse(bad['covered'])

    def test_path_coverage_is_joint_across_each_output(self):
        snapshots,_=collect_full_prefix(self.cfg,self.world,'r2_targeted',self.paths['r2_targeted'])
        rows=evaluate_prefix(self.design,'r2_targeted',snapshots,.2,.2,True)
        covered=True
        for row in rows:
            covered=covered and row['lower']<=.2<=row['upper']
            self.assertEqual(row['path_covered'],covered)
            self.assertEqual(row['bad_release'],row['released'] and row['error']>.2)

    def test_saved_artifact_validation_detects_cost_corruption(self):
        cfg=dict(self.cfg,surfaces=['linear'],scenarios=['bridgeable'],repetitions_per_cell=1)
        result=run_world((cfg,0,0,0))
        test_root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='.cost-precision-check-',dir=test_root) as directory:
            out=Path(directory)
            # TemporaryDirectory recursively cleans only its verified workspace child.
            self.assertEqual(out.resolve().parent,test_root)
            for key in ['prefix_records','stopped_records','acquisitions']:
                pd.DataFrame(result[key]).to_csv(out/f'{key}.csv',index=False,float_format='%.15g')
            for filename,records in [('plans.jsonl',result['plans']),
                                      ('world_audits.jsonl',[result['world_audit']]),
                                      ('calibration_scores.jsonl',[result['calibration']])]:
                (out/filename).write_text(''.join(json.dumps(r)+'\n' for r in records),encoding='utf-8')
            checks,_=validate_outputs(cfg,out)
            self.assertEqual([c['name'] for c in checks if not c['passed']],[])
            frame=pd.read_csv(out/'prefix_records.csv')
            frame.loc[1,'new_n']+=96
            frame.to_csv(out/'prefix_records.csv',index=False,float_format='%.15g')
            checks,_=validate_outputs(cfg,out)
            self.assertTrue(any(not c['passed'] and 'actual cost' in c['name'] for c in checks))


if __name__ == '__main__':
    unittest.main()
