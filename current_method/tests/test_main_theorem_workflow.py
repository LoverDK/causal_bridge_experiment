"""Independent algebra, sampling, and workflow checks for archived designs."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from atlas_new.main_theorem_workflow import inputs,make_plans,sample_design_worlds,standardized_t5,states_for_counts

class MainTheoremWorkflowChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive=json.loads((Path(__file__).parents[1]/'results/full/bridge_designs.json').read_text('utf-8'))
        cls.design=cls.archive[0]
        cls.cfg=dict(direct_noise_sd=.5,failure_probability=.05,scientific_halfwidth=.30,
                     max_study_observations=4096,initial_without_replacement=0,random_path_seed=2026091801,
                     trace_design_id=0,trace_world=0)
        cls.plans,cls.scores=make_plans(cls.design,cls.cfg)

    def test_archive_inputs_are_not_modified(self):
        a=copy.deepcopy(self.design);make_plans(a,self.cfg);self.assertEqual(a,self.design)

    def test_primitive_budget_matches_independent_expansion(self):
        p,pi,t,x,v=inputs(self.design,self.cfg);counts=np.array([1,2,0,4,0,1,2,0,3,0,1,2,0])
        state=states_for_counts(p,pi,t,x,v,counts,.05)[0]
        rows=np.repeat(x,counts,axis=0);vars_=np.repeat(v,counts)
        V=np.linalg.inv(np.linalg.inv(p)+rows.T@(rows/vars_[:,None]))
        weights=(rows@V@t)/vars_;residual=rows.T@weights-t
        W=float(residual@p@residual+np.dot(weights**2,vars_))
        self.assertAlmostEqual(W,state['W'],places=12)
        self.assertAlmostEqual(state['W'],float(t@V@t),places=12)

    def test_target_and_logdet_choose_their_declared_objectives(self):
        groups={}
        for row in self.scores:groups.setdefault((row['method'],row['stage']),[]).append(row)
        for (method,stage),rows in groups.items():
            chosen=[r for r in rows if r['selected']];self.assertEqual(len(chosen),1)
            if method=='target_radius':self.assertLessEqual(chosen[0]['W_after'],min(r['W_after'] for r in rows)+1e-13)
            if method=='logdet':self.assertGreaterEqual(chosen[0]['logdet_gain'],max(r['logdet_gain'] for r in rows)-1e-13)

    def test_stop_is_first_width_crossing_and_cost_is_observations(self):
        for method,p in self.plans.items():
            self.assertTrue(p['attained']);self.assertLessEqual(p['path'][-1]['width'],.60)
            self.assertTrue(all(s['width']>.60 for s in p['path'][:-1]))
            for s in p['path']:self.assertEqual(sum(s['counts']),s['study_observations'])
        self.assertIn(self.plans['direct_target']['stop_stage'],[55,56])

    def test_random_is_fixed_cycle_and_repeated_visits_are_distinct(self):
        p=self.plans['frozen_random'];order=p['random_order'];visits={i:0 for i in range(12)}
        for s in p['path'][1:]:
            self.assertEqual(s['selected'],order[(s['stage']-1)%12])
            self.assertEqual(s['visit'],visits[s['selected']]);visits[s['selected']]+=1

    def test_non_gaussian_sampler_is_exact_standardized_t5(self):
        a=np.random.default_rng(238);b=np.random.default_rng(238)
        np.testing.assert_array_equal(standardized_t5(a,100),b.standard_t(5,100)*np.sqrt(3/5))

    def test_recorded_observations_independently_reconstruct_trace(self):
        records,stats,trace,ledger=sample_design_worlds(self.design,self.cfg,self.plans,2026091802,2)
        prior,pi,t,x,var=inputs(self.design,self.cfg)
        for method,p in self.plans.items():
            actions=[r for r in ledger if r['method']==method]
            for row in [r for r in trace if r['method']==method]:
                prefix=actions[:row['stage']]
                G=sum((np.outer(x[a['candidate_type']],x[a['candidate_type']])/var[a['candidate_type']] for a in prefix),start=np.zeros_like(prior))
                z=sum((x[a['candidate_type']]*a['observed_y']/var[a['candidate_type']] for a in prefix),start=np.zeros(6))
                estimate=float(t@np.linalg.solve(pi+G,z))
                self.assertAlmostEqual(estimate,row['estimate'],places=10)
            for replicate in range(2):
                rr=next(r for r in records if r['method']==method and r['replicate']==replicate)
                ss=[r for r in stats if r['method']==method and r['replicate']==replicate]
                self.assertAlmostEqual(sum(r['sum_y']*r['weight_per_observation'] for r in ss),rr['estimate'],places=11)

    def test_outcomes_change_centers_not_plans_or_terminal_widths(self):
        a=sample_design_worlds(self.design,self.cfg,self.plans,2026091803,1)[0]
        b=sample_design_worlds(self.design,self.cfg,self.plans,2026091804,1)[0]
        self.assertNotEqual(a[0]['estimate'],b[0]['estimate'])
        for aa,bb in zip(a,b):
            self.assertEqual(aa['width'],bb['width']);self.assertEqual(aa['study_observations'],bb['study_observations'])

    def test_paired_methods_share_only_identical_type_visits(self):
        rows=sample_design_worlds(self.design,self.cfg,self.plans,2026091805,1)[3]
        cache={}
        for r in rows:
            key=(r['candidate_type'],r['visit'])
            if key in cache:self.assertEqual(cache[key],r['observed_y'])
            cache[key]=r['observed_y']
        values=[v for (k,visit),v in cache.items() if k==12]
        self.assertEqual(len(values),len(set(values)))

if __name__=='__main__':unittest.main()
