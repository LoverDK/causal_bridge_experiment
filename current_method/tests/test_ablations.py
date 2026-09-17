import json
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from atlas_new.ablations import weights, radius, fit, common_order, make_path, run_world
from atlas_new.workflow import make_world, plan, execute


class AblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((Path(__file__).parents[1]/'configs/workflow_full.json').read_text())
        cls.cfg.update(schedules=['random','nearest'],modes=['r2','rinf'])
        cls.world=make_world(cls.cfg,1,1,0)
        cls.d=cls.world['design']

    def test_ivw_uses_variance_not_standard_error(self):
        a=weights(self.d,[0,4],'inverse_variance')
        np.testing.assert_allclose(a,[800/896,96/896])
        self.assertEqual(np.count_nonzero(weights(self.d,[0,4],'nearest_source')),1)

    def test_minimum_path_matches_existing_random_workflow(self):
        order=[4,6,8,5,7,9]
        old,_=plan(self.d,'r2_random',order)
        new=make_path(self.d,'r2','optimized','minimum',order)
        for a,b in zip(old,new):
            self.assertEqual(a['ids'],b['ids'])
            np.testing.assert_allclose(a['weights'],b['weights'],atol=1e-12)
            self.assertAlmostEqual(a['radius'],b['radius'])

    def test_single_source_bounds_coincide_and_invalid_bound_rejected(self):
        for mode in ['r2','rinf']:
            self.assertAlmostEqual(radius(self.d,[0],[1.],mode,'barycentric'),
                                   radius(self.d,[0],[1.],mode,'lipschitz'))
        with self.assertRaises(ValueError):
            radius(self.d,[0],[1.],'r2','wrong')

    def test_branch_fallback_valid_when_solver_fails(self):
        from types import SimpleNamespace
        with patch('atlas_new.ablations.minimize',return_value=SimpleNamespace(success=False)):
            p=fit(self.d,[0,1,2,3],'r2','optimized','barycentric')
        self.assertEqual(p['solver_failures'],2)
        self.assertAlmostEqual(p['radius'],radius(self.d,p['ids'],p['weights'],'r2','barycentric'))
        self.assertFalse(p['global_optimum_certified'])

    def test_no_outcome_or_truth_access_and_stop_is_respected(self):
        order=common_order(self.d,'nearest',range(4,10))
        path=make_path(self.d,'r2','uniform','minimum',order)
        changed=dict(self.world,truth=self.world['truth'].copy())
        changed['truth'][-1]+=1e6
        a,ae=execute(self.cfg,self.world,'r2_random',path,100.)
        b,be=execute(self.cfg,changed,'r2_random',path,100.)
        self.assertEqual(ae,[]);self.assertEqual(be,[])
        for x,y in zip(a,b):
            for key in ['radius','weights','estimate','released','new_n']:
                self.assertEqual(x[key],y[key])

    def test_paired_variants_share_prefixes_and_geometric_error_bound(self):
        rows,plans=run_world((self.cfg,1,1,0))
        self.assertEqual(len(rows),192);self.assertEqual(len(plans),96)
        for schedule in self.cfg['schedules']:
            for stage in range(4):
                ids={tuple(p['ids']) for p in plans if p['schedule']==schedule and p['stage']==stage}
                self.assertEqual(len(ids),1)
        for p in plans:
            if p['joint_set_covered']:
                self.assertGreaterEqual(p['minimum_radius']-p['noise_radius']+1e-9,p['causal_bias'])


if __name__=='__main__':
    unittest.main()
