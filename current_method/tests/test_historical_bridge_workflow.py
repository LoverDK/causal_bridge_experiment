"""Independent observation reconstruction and information-boundary checks."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from atlas_new.historical_bridge_workflow import (METHODS,REFERENCE,inputs,history_selection,make_plans,
    sample_design_worlds,standardized_t5,states_for_counts,ci_sign)

class HistoricalBridgeWorkflowChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design=json.loads((Path(__file__).parents[1]/'results/full/bridge_designs.json').read_text())[0]
        cls.cfg=dict(direct_noise_sd=.5,failure_probability=.05,history_studies=4,
            history_selection_seed=2026110740,random_path_seed=2026110743,budgets=[0,1,2,4,8],
            reference_direct_observations=64,point_difference_threshold=.30,
            reference_noise_stream='independent_of_all_policy_future_observations',trace_design_id=0,trace_world=0)
        cls.plans,cls.scores=make_plans(cls.design,cls.cfg)
        cls.rows,cls.stats,cls.history,cls.trace,cls.ledger=sample_design_worlds(cls.design,cls.cfg,cls.plans,2026110741,2)

    def test_archived_inputs_unchanged_and_history_fixed_without_replacement(self):
        d=copy.deepcopy(self.design);make_plans(d,self.cfg);self.assertEqual(d,self.design)
        order,counts=history_selection(d,self.cfg)
        expected=np.random.default_rng(np.random.SeedSequence([2026110740,0])).permutation(12)[:4].tolist()
        self.assertEqual(order,expected);self.assertEqual(len(set(order)),4);self.assertEqual(counts.sum(),4)
        self.assertEqual(counts[12],0)

    def test_primitive_W_includes_history_and_future_actual_observation_counts(self):
        P,pi,t,x,v=inputs(self.design,self.cfg)
        for method,plan in self.plans.items():
            state=plan['path'][-1];counts=np.array(state['total_counts'])
            rows=np.repeat(x,counts,axis=0);variance=np.repeat(v,counts)
            V=np.linalg.inv(pi+rows.T@(rows/variance[:,None]));a=rows@V@t/variance
            residual=rows.T@a-t;W=float(residual@P@residual+np.sum(a*a*variance))
            self.assertAlmostEqual(W,state['W'],places=12)
            self.assertAlmostEqual(W,float(t@V@t),places=12)

    def test_actual_history_reconstructs_shared_budget_zero(self):
        P,pi,t,x,v=inputs(self.design,self.cfg)
        for world in range(2):
            history=[r for r in self.history if r['replicate']==world]
            self.assertEqual(len(history),4)
            G=sum((np.outer(x[r['candidate_type']],x[r['candidate_type']])/v[r['candidate_type']] for r in history),start=np.zeros_like(P))
            rhs=sum((x[r['candidate_type']]*r['observed_y']/v[r['candidate_type']] for r in history),start=np.zeros(6))
            estimate=float(t@np.linalg.solve(pi+G,rhs))
            baseline=[r for r in self.rows if r['replicate']==world and r['new_budget']==0]
            self.assertEqual(len(baseline),4)
            self.assertTrue(all(abs(r['estimate']-estimate)<1e-11 for r in baseline))
        self.assertNotEqual(self.rows[0]['estimate'],0.)

    def test_full_trace_reconstructs_from_history_and_actual_new_Y(self):
        P,pi,t,x,v=inputs(self.design,self.cfg)
        history=[r for r in self.history if r['replicate']==0]
        for method in (*METHODS,REFERENCE):
            ledger=[r for r in self.ledger if r['method']==method]
            for row in [r for r in self.trace if r['method']==method]:
                observations=history+ledger[:row['stage']]
                G=sum((np.outer(x[r['candidate_type']],x[r['candidate_type']])/v[r['candidate_type']] for r in observations),start=np.zeros_like(P))
                rhs=sum((x[r['candidate_type']]*r['observed_y']/v[r['candidate_type']] for r in observations),start=np.zeros(6))
                estimate=float(t@np.linalg.solve(pi+G,rhs))
                self.assertAlmostEqual(estimate,row['estimate'],places=11)

    def test_saved_prefix_stats_reconstruct_all_budget_endpoints(self):
        for row in self.rows:
            state=self.plans[row['method']]['path'][row['new_budget']]
            hs=np.zeros(13);fs=np.zeros(13)
            for h in self.history:
                if h['replicate']==row['replicate']:hs[h['candidate_type']]=h['observed_y']
            for kind,count in enumerate(state['future_counts']):
                if count:
                    matching=[s for s in self.stats if s['replicate']==row['replicate'] and s['candidate_type']==kind
                              and s['stream']==row['future_stream'] and s['future_observations']==count]
                    self.assertEqual(len(matching),1);fs[kind]=matching[0]['sum_future_y']
            self.assertAlmostEqual(float(np.dot(state['weights'],hs+fs)),row['estimate'],places=12)

    def test_reference_future_is_independent_and_policy_visits_are_paired(self):
        cache={}
        for row in self.ledger:
            key=(row['stream'],row['candidate_type'],row['visit'])
            if key in cache:self.assertEqual(row['observed_y'],cache[key])
            cache[key]=row['observed_y']
        for visit in range(8):
            self.assertNotEqual(cache[('policy_future',12,visit)],cache[('reference_future',12,visit)])
        self.assertEqual(len([key for key in cache if key[0]=='reference_future']),64)
        for h in [r for r in self.history if r['replicate']==0]:
            key=('policy_future',h['candidate_type'],0)
            if key in cache:self.assertNotEqual(cache[key],h['observed_y'])

    def test_no_outcome_or_width_stopping_and_future_visits_count_separately(self):
        altered=dict(self.cfg,point_difference_threshold=10000.)
        other,_=make_plans(self.design,altered)
        for method,plan in self.plans.items():
            horizon=64 if method==REFERENCE else 8
            self.assertEqual(len(plan['path']),horizon+1)
            visits=np.zeros(13,int)
            for row,row2 in zip(plan['path'],other[method]['path']):
                self.assertEqual(row['selected'],row2['selected']);self.assertEqual(row['width'],row2['width'])
                self.assertEqual(sum(row['total_counts']),4+row['stage'])
                self.assertEqual(sum(row['future_counts']),row['stage'])
                if row['stage']:
                    self.assertEqual(row['visit'],visits[row['selected']]);visits[row['selected']]+=1

    def test_actual_minimum_next_W_and_logdet_objectives(self):
        grouped={}
        for r in self.scores:grouped.setdefault((r['method'],r['stage']),[]).append(r)
        for (method,stage),rows in grouped.items():
            chosen=[r for r in rows if r['selected']];self.assertEqual(len(chosen),1)
            if method=='target_radius':self.assertAlmostEqual(chosen[0]['W_after'],min(r['W_after'] for r in rows),places=13)
            if method=='logdet':self.assertAlmostEqual(chosen[0]['logdet_gain'],max(r['logdet_gain'] for r in rows),places=13)

    def test_non_gaussian_sampler_is_standardized_t5_and_history_changes_centers(self):
        a=np.random.default_rng(987);b=np.random.default_rng(987)
        np.testing.assert_array_equal(standardized_t5(a,100),b.standard_t(5,100)*np.sqrt(3/5))
        new=sample_design_worlds(self.design,self.cfg,self.plans,2026110750,1)[0]
        self.assertNotEqual(new[0]['estimate'],self.rows[0]['estimate'])
        self.assertEqual(new[0]['width'],self.rows[0]['width'])

    def test_direction_has_three_states_and_reference_is_not_truth(self):
        self.assertEqual(ci_sign(0.,1.),0);self.assertEqual(ci_sign(-1.,0.),0)
        self.assertEqual(ci_sign(.1,1.),1);self.assertEqual(ci_sign(-1.,-.1),-1)
        for row in self.rows:
            self.assertAlmostEqual(row['point_difference'],row['estimate']-row['reference_estimate'])
            self.assertAlmostEqual(row['error'],row['estimate']-row['truth'])
            self.assertNotEqual(row['reference_estimate'],row['truth'])
            if row['method']==REFERENCE:
                self.assertEqual(row['point_difference'],0.)
                self.assertLessEqual(row['width'],2*np.sqrt(.25/(64*.05))+1e-12)

if __name__=='__main__':unittest.main()
