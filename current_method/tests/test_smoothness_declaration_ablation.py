"""Independent checks for declared bounds, actual branches, and score isolation."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from atlas_new.workflow import make_world,collect,plan
from atlas_new.mechanism_uncertainty_ablation import fixed_prefix_plan,geometry_parts
from atlas_new.smoothness_declaration_ablation import (VARIANTS,MODES,declared_design,declaration_labels,
    branch_labels,score_errors,run_world)

class SmoothnessDeclarationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads((Path(__file__).parents[1]/'configs/workflow_smoke.json').read_text(encoding='utf-8'))
        cls.cfg.update(seed=2026110770,branch_tie_tolerance=1e-12,causal_check_tolerance=1e-10)
        cls.world=make_world(cls.cfg,1,1,0);cls.base=cls.world['design']
        cls.result=run_world((cls.cfg,1,1,0));cls.order=cls.result[-1]['common_random_order']

    def test_baseline_reproduces_original_general_formula_and_random_plan(self):
        new=fixed_prefix_plan(declared_design(self.base,'baseline'),'r2',self.order)
        old,_=plan(self.base,'r2_random',self.order)
        for a,b in zip(new,old):
            self.assertEqual(a['ids'],b['ids']);np.testing.assert_array_equal(a['weights'],b['weights'])
            self.assertEqual(a['radius'],b['radius'])

    def test_declaring_LH_does_not_change_geometry_data_or_sampling(self):
        for variant in VARIANTS:
            d=declared_design(self.base,variant)
            for key in ['centers','radii','target_center','noise_sd']:
                np.testing.assert_array_equal(getattr(d,key),getattr(self.base,key))
        fixed,_,_,plans,_,obs,_=self.result
        for stage in range(4):self.assertEqual(len({tuple(p['ids']) for p in plans if p['stage']==stage}),1)
        for row in obs:
            expected=collect(self.world,row['source_id'],row['n'])
            self.assertEqual(row['effect'],expected['effect']);self.assertEqual(row['treated_mean'],expected['treated_mean'])

    def test_H_zero_validity_depends_on_surface_and_L_half_is_invalid(self):
        for surface in range(3):
            base=make_world(self.cfg,surface,1,0)['design']
            for variant in VARIANTS:
                labels=declaration_labels(base,declared_design(base,variant),variant,True)
                expected=variant!='L_half' and (variant!='H_zero' or surface==0)
                self.assertEqual(labels['smoothness_declaration_valid'],expected)
                self.assertEqual(labels['guarantee_applicable'],expected)
                if not expected:self.assertIsNone(labels['nominal_path_failure_bound'])

    def test_exact_valid_BLip_tie_and_numeric_near_tie_are_distinct(self):
        d=declared_design(self.base,'H_zero');labels=declaration_labels(self.base,d,'H_zero',True)
        exact=branch_labels(dict(geometry_min=.2,Bbar=.2,BLip=.2),labels,1e-12)
        self.assertTrue(exact['selected_bound_valid']);self.assertEqual(exact['valid_branches_attaining_min'],['lipschitz'])
        near=branch_labels(dict(geometry_min=.2,Bbar=.2,BLip=.2+5e-13),labels,1e-12)
        self.assertFalse(near['selected_bound_valid']);self.assertTrue(near['valid_branch_near_min'])
        self.assertFalse(labels['guarantee_applicable']);self.assertIsNone(labels['nominal_path_failure_bound'])

    def test_same_weights_isolate_L_and_H_while_noise_is_identical(self):
        same=self.result[2]
        for mode in MODES:
            for stage in range(4):
                rows={r['variant']:r for r in same if r['mode']==mode and r['stage']==stage};b=rows['baseline']
                for r in rows.values():self.assertEqual(r['weights'],b['weights']);self.assertEqual(r['noise'],b['noise'])
                for key in ['Bbar','BLip','geometry_min']:
                    self.assertLessEqual(rows['L_half'][key],b[key]+1e-12);self.assertLessEqual(b[key],rows['L_double'][key]+1e-12)
                for key in ['Bbar','geometry_min']:
                    self.assertLessEqual(rows['H_zero'][key],b[key]+1e-12);self.assertLessEqual(b[key],rows['H_double'][key]+1e-12)
                self.assertEqual(rows['H_zero']['BLip'],b['BLip']);self.assertEqual(b['BLip'],rows['H_double']['BLip'])

    def test_refusal_changes_with_L_and_is_invariant_to_H(self):
        fixed=self.result[0]
        for mode in MODES:
            for stage in range(4):
                rows={r['variant']:r for r in fixed if r['mode']==mode and r['stage']==stage};b=rows['baseline']
                for key in ['refusal_lower','refusal_upper']:
                    self.assertEqual(rows['H_zero'][key],b[key]);self.assertEqual(rows['H_double'][key],b[key])
                self.assertGreater(rows['L_half']['refusal_lower'],b['refusal_lower'])
                self.assertLess(rows['L_half']['refusal_upper'],b['refusal_upper'])

    def test_signed_error_decomposition_from_true_source_effects(self):
        fixed,_,_,_,_,obs,audit=self.result;observations={r['source_id']:r for r in obs}
        truths=np.asarray(audit['truth'])
        for row in fixed:
            a=np.array(row['weights']);ids=row['source_ids'];ys=np.array([observations[i]['effect'] for i in ids])
            self.assertAlmostEqual(row['causal_error'],float(a@truths[ids]-truths[-1]),places=13)
            self.assertAlmostEqual(row['sampling_error'],float(a@(ys-truths[ids])),places=13)
            self.assertAlmostEqual(row['error'],row['causal_error']+row['sampling_error'],places=13)
            if row['smoothness_declaration_valid'] and row['mechanism_event_holds']:
                self.assertLessEqual(abs(row['causal_error']),row['geometry_min']+1e-10)

    def test_scoring_truth_perturbation_never_mutates_design_plan(self):
        fixed,_,_,plans,_,obs,audit=self.result;before=copy.deepcopy(plans)
        row=fixed[0];byid={r['source_id']:r for r in obs}
        truth=np.array(audit['truth']);altered=truth.copy();altered[-1]+=1
        a=score_errors(row,truth,byid,1e-10);b=score_errors(row,altered,byid,1e-10)
        self.assertAlmostEqual(b['error'],a['error']-1);self.assertEqual(plans,before)

    def test_returned_output_validity_and_cumulative_path_use_actual_output(self):
        rows=self.result[1]
        for variant in VARIANTS:
            for mode in MODES:
                for tolerance in self.cfg['tolerances']:
                    group=sorted([r for r in rows if r['variant']==variant and r['mode']==mode and r['tolerance']==tolerance],key=lambda r:r['budget'])
                    running=True
                    for r in group:
                        expected=r['selected_bound_valid'] if r['released'] else r['declared_L_valid']
                        running=running and expected
                        self.assertEqual(r['returned_output_bound_valid'],expected)
                        self.assertEqual(r['path_all_output_bound_assumptions_satisfied'],running)

    def test_linear_H_groups_have_identical_inputs_and_plans(self):
        base=make_world(self.cfg,0,1,0)['design'];p=[]
        for variant in ['baseline','H_zero','H_double']:
            d=declared_design(base,variant);self.assertEqual(d.H,0.)
            p.append(fixed_prefix_plan(d,'r2',self.order))
        self.assertEqual(p[0],p[1]);self.assertEqual(p[0],p[2])

if __name__=='__main__':unittest.main()
