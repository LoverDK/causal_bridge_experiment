import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Analysis.Real.Sqrt

/-!
Finite-dimensional Euclidean inequalities for fixed-parameter certificates.
No matrix inverse identity or probabilistic hypothesis is established here.
-/

namespace CausalAtlas.NonGaussianEuclidean

/-- A Euclidean parameter bound controls the finite linear-estimator imbalance. -/
theorem linear_bias_le_euclidean {ι : Type*} [Fintype ι]
    (d beta : ι → ℝ) (M : ℝ) (hM : 0 ≤ M)
    (hbeta : ∑ j, beta j ^ 2 ≤ M ^ 2) :
    |∑ j, d j * beta j| ≤ Real.sqrt (∑ j, d j ^ 2) * M := by
  have hcs := Finset.sum_mul_sq_le_sq_mul_sq Finset.univ d beta
  have hD : 0 ≤ ∑ j, d j ^ 2 := Finset.sum_nonneg (fun j _ => sq_nonneg (d j))
  apply abs_le_of_sq_le_sq ?_ (mul_nonneg (Real.sqrt_nonneg _) hM)
  simpa [mul_pow, Real.sq_sqrt hD] using
    hcs.trans (mul_le_mul_of_nonneg_left hbeta hD)

#print axioms linear_bias_le_euclidean

end CausalAtlas.NonGaussianEuclidean
