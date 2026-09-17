import json
from dataclasses import replace
from pathlib import Path
import unittest

import numpy as np

from atlas_new.workflow import (make_world, plan, execute, collect, certificate,
                                objective_parts, multipliers, surface)


class WorkflowChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = json.loads((Path(__file__).parents[1]/'configs'/'workflow_smoke.json').read_text())
        cls.world = make_world(cls.cfg, 1, 1, 0)
        cls.design = cls.world['design']

    def test_ball_bound_dominates_realized_geometry(self):
        rng = np.random.default_rng(82910)
        d = self.design; ids = list(range(4)); objective = objective_parts(d,ids,'r2')
        q,_ = multipliers(d,'r2')
        for _ in range(200):
            a=rng.dirichlet(np.ones(4))
            directions=rng.normal(size=(5,2)); directions/=np.linalg.norm(directions,axis=1)[:,None]
            locations=np.vstack([d.centers[ids],d.target_center])+directions*d.target_radius*rng.random((5,1))
            mean=a@locations[:-1]
            geometry=d.L*np.linalg.norm(locations[-1]-mean)+d.H/2*float(a@np.sum((locations[:-1]-mean)**2,axis=1))
            noise=q*np.linalg.norm(a*d.noise_sd[ids])
            self.assertGreaterEqual(objective(a,'barycentric')[0]+1e-10,geometry+noise)
            # The smaller Lipschitz bound need not dominate G, but must bound true effect error.
            values,_,_=surface('quadratic',locations)
            self.assertGreaterEqual(certificate(d,ids,a,'r2')-noise+1e-10,
                                    abs(values[-1]-a@values[:-1]))

    def test_analytic_gradients(self):
        d=self.design; ids=list(range(4)); a=np.array([.1,.2,.3,.4]); eps=1e-6
        for mode in ['r2','rinf']:
            f=objective_parts(d,ids,mode)
            for branch in ['barycentric','lipschitz']:
                _,gradient=f(a,branch)
                numeric=np.array([(f(a+eps*v,branch)[0]-f(a-eps*v,branch)[0])/(2*eps)
                                  for v in np.eye(4)])
                np.testing.assert_allclose(gradient,numeric,rtol=1e-5,atol=1e-7)

    def test_summary_noise_matches_two_balanced_arms(self):
        # Compare actual randomized-trial simulation against its independently derived variance.
        observations=[]
        for rep in range(1000):
            world=dict(self.world,replicate=rep)
            observations.append(collect(world,4,96)['effect']-world['truth'][4])
        self.assertAlmostEqual(np.var(observations,ddof=1),1/96,delta=.0015)
        record=collect(self.world,4,96)
        self.assertEqual(record['effect'],record['treated_mean']-record['control_mean'])

    def test_planning_and_stop_ignore_target_truth_and_future_outcomes(self):
        # Planner interface has no world/outcome argument. Perturb the scorer's
        # target truth and an uncollected candidate outcome; selection stays fixed.
        path,_=plan(self.design,'r2_targeted',range(4,10))
        cfg=self.cfg
        states,events=execute(cfg,self.world,'r2_targeted',path,100.)
        altered=dict(self.world,truth=self.world['truth'].copy())
        altered['truth'][-1]+=1e6
        altered['truth'][4:]+=1000
        states2,events2=execute(cfg,altered,'r2_targeted',path,100.)
        self.assertEqual(events,[]);self.assertEqual(events2,[])
        for a,b in zip(states,states2):
            for key in ['selected','weights','radius','estimate','released','new_n','lower','upper']:
                self.assertEqual(a[key],b[key])

    def test_no_collect_after_release_and_cumulative_target_batches(self):
        rows,events=execute(self.cfg,self.world,'target_only',[],.3)
        self.assertEqual(len(events),1)
        self.assertFalse(rows[0]['released']);self.assertTrue(rows[1]['released'])
        self.assertEqual([r['new_n'] for r in rows],[0,96,96,96])
        full,events=execute(self.cfg,self.world,'target_only',[],0.)
        self.assertEqual(len(events),3)
        for stage in range(1,4):
            self.assertAlmostEqual(full[stage]['estimate'],np.mean([e['effect'] for e in events[:stage]]))

    def test_final_radius_recomputed_and_old_weights_remain_available(self):
        for method,mode in [('r2_targeted','r2'),('rinf_targeted','rinf')]:
            path,_=plan(self.design,method,range(4,10))
            for p in path:
                self.assertAlmostEqual(p['radius'],certificate(self.design,p['ids'],p['weights'],mode))
                self.assertFalse(p['global_optimum_certified'])
            self.assertTrue(np.all(np.diff([p['radius'] for p in path])<=1e-8))

    def test_same_world_reproduces_and_calibration_covers_candidate_universe(self):
        other=make_world(self.cfg,1,1,0)
        np.testing.assert_array_equal(other['design'].centers,self.design.centers)
        self.assertEqual(len(self.design.centers),10)
        joint=np.linalg.norm(np.vstack([self.design.centers,self.design.target_center])-self.world['locations'],axis=1)
        self.assertEqual(self.world['joint_set_covered'],bool(np.all(joint<=self.design.target_radius)))
        for mode in ['r2','rinf']:
            q,coordinate=multipliers(self.design,mode)
            coordinate_budget=self.design.zeta/(2 if mode=='r2' else 1)
            self.assertAlmostEqual(2*10*np.exp(-coordinate**2/2),coordinate_budget)
            if mode=='r2':
                self.assertAlmostEqual(2*4*np.exp(-q*q/2),self.design.zeta/2)


if __name__=='__main__':unittest.main()
