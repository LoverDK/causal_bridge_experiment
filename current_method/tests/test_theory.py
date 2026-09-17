import unittest
import numpy as np
from scipy.stats import norm
from atlas_new.core import (box_vertices, geometry, radius, optimize_radius,
    calibrated_quantile, sharp_lipschitz, complementarity, posterior, information, logdet_greedy)
from atlas_new.manylabs import predict


class TheoryChecks(unittest.TestCase):
    def test_box_maximum_dominates_interior_points(self):
        rng=np.random.default_rng(721)
        boxes=np.array([[-.9,-.2],[.1,.8],[-.1,.6]])
        a=np.array([.35,.65]);v=box_vertices(boxes)
        maximum=geometry(a,v,1.2,.6)
        for _ in range(500):
            m=rng.uniform(boxes[:,0],boxes[:,1]);mean=a@m[:-1]
            direct=1.2*abs(m[-1]-mean)+.3*np.sum(a*(m[:-1]-mean)**2)
            self.assertLessEqual(direct,maximum+1e-12)

    def test_uniform_bound_survives_adaptive_choice(self):
        rng=np.random.default_rng(29);k=4;s=np.array([.1,.2,.05,.08]);beta=np.full(k,.03)
        boxes=np.array([[-.7,-.5],[-.2,.0],[.3,.5],[.7,.9],[.1,.3]])
        v=box_vertices(boxes);q=np.sqrt(2*np.log(2*k/.05))
        for _ in range(200):
            m=rng.uniform(boxes[:,0],boxes[:,1]);tau=.6*m+.3*m*m
            noise=rng.uniform(-q,q,k)*s;b=rng.uniform(-1,1,k)*beta;observed=tau[:-1]+noise+b
            # Select after observing effects. The deterministic eventwise assertion must still hold.
            a=np.eye(k)[np.argmax(abs(observed))]
            self.assertLessEqual(abs(tau[-1]-a@observed),radius(a,v,1.2,.6,s,beta)+1e-10)

    def test_fixed_radius_no_larger_than_simultaneous(self):
        a=np.array([.2,.8]);v=box_vertices([[-.2,.2],[.5,.6],[.1,.2]])
        self.assertLessEqual(radius(a,v,1,.3,[.1,.2],[0,0],mode='fixed'),
                             radius(a,v,1,.3,[.1,.2],[0,0]))

    def test_optimizer_feasible_and_geometry_only(self):
        b=np.array([[-.8,-.6],[.1,.3],[.6,.7],[-.05,.05]])
        a,r,d=optimize_radius(b,1.2,.6,[.1,.1,.1],[0,0,0])
        self.assertAlmostEqual(a.sum(),1)
        self.assertTrue((a>=0).all());self.assertFalse(d['global_optimum_certified'])
        self.assertLessEqual(r,radius(np.ones(3)/3,box_vertices(b),1.2,.6,[.1]*3,[0]*3)+1e-10)

    def test_optimizer_handles_infeasible_internal_iterates(self):
        rng=np.random.default_rng(731)
        for _ in range(12):
            c=rng.uniform(-1,1,5)
            boxes=np.column_stack((np.maximum(c-.15,-1),np.minimum(c+.15,1)))
            a,r,_=optimize_radius(boxes,1.2,.6,np.linspace(.04,.1,4),np.zeros(4))
            self.assertAlmostEqual(a.sum(),1)
            self.assertTrue(np.isfinite(r))

    def test_lp_closed_form_and_witnesses(self):
        rng=np.random.default_rng(89)
        for _ in range(20):
            x=rng.uniform(-1,1,6);t=rng.uniform(-1,1);y=.4*x+.2*x*x
            r=sharp_lipschitz(x,t,y,y,1)
            self.assertAlmostEqual(r['lower'],max(y-abs(x-t)),places=8)
            self.assertAlmostEqual(r['upper'],min(y+abs(x-t)),places=8)
            self.assertLessEqual(r['max_pairwise_violation'],1e-8)

    def test_lp_source_constraints_and_infeasibility(self):
        r=sharp_lipschitz([0,.1],.05,[0,1],[0,1],1)
        self.assertEqual(r['status'],'infeasible');self.assertTrue(np.isnan(r['width']))
        self.assertEqual(sharp_lipschitz([],0,[],[],1)['status'],'unbounded')
        r=sharp_lipschitz([-1,1],0,[0,0],[0,0],1)
        self.assertEqual(r['width'],2)

    def test_quantile_rank_and_infinite_case(self):
        self.assertEqual(calibrated_quantile(np.arange(199),.05),189)
        self.assertTrue(np.isinf(calibrated_quantile(np.arange(10),.05)))

    def test_complementarity(self):
        self.assertEqual([d['width'] for d in complementarity()],[2,2,2,0])

    def test_logdet_diminishing_returns(self):
        rng=np.random.default_rng(31);prior=np.eye(3);x=rng.normal(size=(7,3));s=np.full(7,.5)
        vs=posterior(prior,x,s,[0]);vt=posterior(prior,x,s,[0,1,2])
        self.assertGreaterEqual(np.linalg.eigvalsh(vs-vt).min(),-1e-10)
        for b in [3,4,5,6]:
            gs=information(prior,posterior(prior,x,s,[0,b]))-information(prior,vs)
            gt=information(prior,posterior(prior,x,s,[0,1,2,b]))-information(prior,vt)
            self.assertGreaterEqual(gs+1e-10,gt)
        self.assertEqual(len(set(logdet_greedy(prior,x,s,4))),4)

    def test_analytic_selection_boundary(self):
        self.assertAlmostEqual((2*norm.cdf(norm.ppf(.975))-1)**128,.95**128)
        for k in [1,4,16,128]:self.assertGreaterEqual((1-.05/k)**k,.95-1e-12)

    def test_real_prediction_interface_has_no_target_effect(self):
        r=predict([.1,.2,.3],[.04,.05,.06],(50,50))
        self.assertGreater(r['fixed'][1],0)
        self.assertGreater(r['random'][1],0)
        with self.assertRaises(TypeError):predict([.1,.2,.3],[.04,.05,.06],(50,50),target_effect=99)


if __name__=='__main__':unittest.main()
