"""Tests of matched sources, actual input geometry, and stopped-output semantics."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from atlas_new.workflow import make_world,collect,plan,refusal_envelope,certificate,multipliers
from atlas_new.mechanism_uncertainty_ablation import (VARIANTS,MODES,variant_design,geometry_parts,
    fixed_prefix_plan,condition_labels,evaluate_prefix,stopped_outputs,run_world)

class MechanismAblationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((Path(__file__).parents[1]/'configs/workflow_smoke.json').read_text(encoding='utf-8'))
        cls.cfg.update(seed=2026110760,variants=list(VARIANTS),bound_modes=list(MODES))
        cls.world=make_world(cls.cfg,1,1,0);cls.base=cls.world['design']
        cls.result=run_world((cls.cfg,1,1,0))
        cls.order=cls.result[-1]['common_random_order']

    def test_calibrated_variant_preserves_old_random_policy_and_formula(self):
        d=variant_design(self.base,'calibrated_U');new=fixed_prefix_plan(d,'r2',self.order)
        old,_=plan(self.base,'r2_random',self.order)
        for a,b in zip(new,old):
            self.assertEqual(a['ids'],b['ids']);np.testing.assert_allclose(a['weights'],b['weights'],atol=1e-12)
            self.assertAlmostEqual(a['radius'],b['radius'],places=12)

    def test_common_paths_and_actual_two_arm_observations(self):
        fixed,stopped,same,plans,designs,obs,audit=self.result
        for stage in range(4):self.assertEqual(len({tuple(p['ids']) for p in plans if p['stage']==stage}),1)
        self.assertEqual(len(obs),7)
        for o in obs:
            expected=collect(self.world,o['source_id'],o['n'])
            for k in ['effect','treated_mean','control_mean','noise_sd']:self.assertEqual(o[k],expected[k])
        for state in fixed:
            byid={o['source_id']:o for o in obs}
            expected=np.dot(state['weights'],[byid[i]['effect'] for i in state['source_ids']])
            self.assertAlmostEqual(state['estimate'],expected,places=13)

    def test_same_weight_diagnostic_holds_weights_and_noise_fixed(self):
        fixed,_,same,plans,_,_,_=self.result
        for mode in MODES:
            for stage in range(4):
                reference=next(p for p in plans if p['variant']=='calibrated_U' and p['mode']==mode and p['stage']==stage)
                rows=[r for r in same if r['mode']==mode and r['stage']==stage]
                for row in rows:
                    self.assertEqual(row['weights'],reference['weights']);self.assertEqual(row['source_ids'],reference['ids'])
                self.assertEqual(len({r['noise'] for r in rows}),1)
                cal=next(r for r in rows if r['variant']=='calibrated_U');proxy=next(r for r in rows if r['variant']=='proxy_point')
                self.assertGreaterEqual(cal['radius']+1e-12,proxy['radius'])
                self.assertGreater(cal['linear_set_radius'],0);self.assertEqual(proxy['linear_set_radius'],0)
                # Curvature is zero at a simplex vertex even when balls have radius.
                self.assertGreaterEqual(cal['set_radius_curvature_inflation'],0)
                oracle=next(r for r in rows if r['variant']=='oracle_true_point')
                if cal['mechanism_event_holds']:
                    self.assertGreaterEqual(cal['geometry_min']+1e-12,oracle['geometry_min'])

    def test_both_geometric_branches_and_curvature_split_independently(self):
        a=np.array([.1,.2,.3,.4]);ids=[0,1,2,3]
        for variant in VARIANTS:
            d=variant_design(self.base,variant,self.world['locations'] if variant=='oracle_true_point' else None)
            c=d.centers[ids];r=d.radii[ids]
            for mode in MODES:
                z=geometry_parts(d,ids,a,mode)
                pair=sum(a[i]*a[j]*(np.linalg.norm(c[i]-c[j])+r[i]+r[j])**2 for i in range(4) for j in range(4) if i!=j)
                bary=d.L*(np.linalg.norm(a@c-d.target_center)+d.target_radius+a@r)+d.H/4*pair
                lip=d.L*sum(a[i]*(np.linalg.norm(c[i]-d.target_center)+r[i]+d.target_radius) for i in range(4))
                self.assertAlmostEqual(z['Bbar'],bary,places=13);self.assertAlmostEqual(z['BLip'],lip,places=13)
                self.assertAlmostEqual(z['total_curvature'],z['center_curvature']+z['set_radius_curvature_inflation'],places=13)

    def test_refusal_uses_each_variants_geometry(self):
        _,_,_,plans,_,obs,_=self.result;byid={o['source_id']:o for o in obs}
        for variant in VARIANTS:
            d=variant_design(self.base,variant,self.world['locations'] if variant=='oracle_true_point' else None)
            p=next(p for p in plans if p['variant']==variant and p['mode']=='r2' and p['stage']==0)
            state=evaluate_prefix(d,p,byid,'r2')
            expected=refusal_envelope(d,p['ids'],byid,'r2')
            self.assertEqual((state['refusal_lower'],state['refusal_upper']),expected)
            if variant=='proxy_point':self.assertNotEqual(expected,refusal_envelope(self.base,p['ids'],byid,'r2'))

    def test_truth_changes_do_not_enter_nonoracle_design_or_plan(self):
        corrupt=np.full_like(self.world['locations'],10.)
        for variant in ['calibrated_U','proxy_point']:
            a=variant_design(self.base,variant,self.world['locations']);b=variant_design(self.base,variant,corrupt)
            np.testing.assert_array_equal(a.centers,b.centers)
            self.assertEqual(fixed_prefix_plan(a,'r2',self.order),fixed_prefix_plan(b,'r2',self.order))
        a=variant_design(self.base,'oracle_true_point',self.world['locations'])
        b=variant_design(self.base,'oracle_true_point',corrupt)
        self.assertFalse(np.array_equal(a.centers,b.centers))

    def test_conditions_are_variant_specific_not_scenario_labels(self):
        for scenario in [0,1,2]:
            w=make_world(self.cfg,1,scenario,0)
            for variant in VARIANTS:
                d=variant_design(w['design'],variant,w['locations'] if variant=='oracle_true_point' else None)
                labels=condition_labels(variant,d,w['locations'])
                self.assertEqual(labels['guarantee_applicable'],variant!='proxy_point')
                if variant=='proxy_point':self.assertIsNone(labels['nominal_path_failure_bound'])
                if variant=='oracle_true_point':self.assertTrue(labels['mechanism_event_holds'])
                if variant=='calibrated_U':self.assertEqual(labels['mechanism_event_holds'],w['joint_set_covered'])

    def test_stopped_states_carry_without_reading_post_stop_outcomes(self):
        states=[]
        for stage,r in enumerate([1.,.1,.05,.02]):
            states.append(dict(stage=stage,radius=r,estimate=float(stage),certificate_lower=stage-r,
                certificate_upper=stage+r,refusal_lower=-2.,refusal_upper=2.))
        rows=stopped_outputs(states,self.order,.2,self.cfg)
        self.assertEqual([r['actual_stage'] for r in rows],[0,1,1,1])
        self.assertEqual([r['actual_new_n'] for r in rows],[0,96,96,96])
        self.assertEqual([r['estimate'] for r in rows],[0.,1.,1.,1.])
        self.assertFalse(rows[1]['carried_after_stop']);self.assertTrue(rows[2]['carried_after_stop'])
        self.assertEqual(rows[2]['lower'],.9)

    def test_multipliers_keep_all_sources_and_four_prefixes(self):
        expected_r2=np.sqrt(2*np.log(2*4/(.05/2)))
        expected_inf=np.sqrt(2*np.log(2*10/.05))
        for variant in VARIANTS:
            d=variant_design(self.base,variant,self.world['locations'] if variant=='oracle_true_point' else None)
            self.assertAlmostEqual(multipliers(d,'r2')[0],expected_r2,places=13)
            self.assertAlmostEqual(multipliers(d,'rinf')[0],expected_inf,places=13)

    def test_saved_calibration_scores_reproduce_exact_quantile(self):
        audit=self.result[-1];scores=sorted(audit['calibration_scores'])
        rank=int(np.ceil((len(scores)+1)*(1-self.cfg['eta'])))
        self.assertEqual(scores[rank-1],audit['calibration_q']);self.assertEqual(max(scores),audit['calibration_max'])

if __name__=='__main__':unittest.main()
