import Mathlib.Analysis.Real.Sqrt
import Mathlib.Data.Finset.Max
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.Symmetric
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
Target-width ordering, a directly verified matrix rank-one inverse update,
and a finite-menu minimizer of the actual next target half-width.
Positive semidefiniteness, probability coverage, and a multi-step globally
optimal acquisition policy are outside this file's claims.
-/

namespace CausalAtlas.NonGaussianTargetUpdate

/-- At a common positive failure budget, a larger reduction gives a smaller
next half-width. Nonnegativity of actual variance inputs is a separate premise
when this scalar kernel is used for statistical intervals. -/
theorem radius_le_of_score_ge (q alpha selectedScore otherScore : ℝ)
    (halpha : 0 < alpha) (hscore : otherScore ≤ selectedScore) :
    Real.sqrt ((q - selectedScore) / alpha) ≤
      Real.sqrt ((q - otherScore) / alpha) := by
  exact Real.sqrt_le_sqrt
    (div_le_div_of_nonneg_right (sub_le_sub_left hscore q) halpha.le)

/-- Finite score maximization attains a minimum next half-width. -/
theorem exists_best_next_width {Candidate : Type*}
    (candidates : Finset Candidate) (hne : candidates.Nonempty)
    (score : Candidate → ℝ) (q alpha : ℝ) (halpha : 0 < alpha) :
    ∃ selected ∈ candidates,
      (∀ other ∈ candidates, score other ≤ score selected) ∧
      (∀ other ∈ candidates,
        Real.sqrt ((q - score selected) / alpha) ≤
          Real.sqrt ((q - score other) / alpha)) := by
  obtain ⟨selected, hselected, hmax⟩ := Finset.exists_max_image candidates score hne
  exact ⟨selected, hselected, hmax, fun other hother =>
    radius_le_of_score_ge q alpha (score selected) (score other) halpha (hmax other hother)⟩

/-- Actual rank-one inverse update, proved by verifying the product.
The old inverse and the two nonzero scalar denominators are explicit inputs;
positive-definiteness consequences are not claimed by this algebraic theorem. -/
theorem rank_one_inverse_update {ι : Type*} [Fintype ι] [DecidableEq ι]
    (A V : Matrix ι ι ℝ) (x : ι → ℝ) (r : ℝ)
    (hAV : A * V = 1) (hr : r ≠ 0)
    (hden : r + dotProduct x (V.mulVec x) ≠ 0) :
    (A + r⁻¹ • Matrix.vecMulVec x x)⁻¹ =
      V - (r + dotProduct x (V.mulVec x))⁻¹ •
        Matrix.vecMulVec (V.mulVec x) (Matrix.vecMul x V) := by
  apply Matrix.inv_eq_right_inv
  simp only [add_mul, mul_sub, Matrix.mul_smul, Matrix.smul_mul,
    Matrix.mul_vecMulVec, Matrix.vecMulVec_mul,
    Matrix.mulVec_mulVec, hAV, Matrix.one_mulVec]
  simp only [Matrix.smul_mulVec, Matrix.vecMulVec_mulVec, op_smul_eq_smul,
    Matrix.smul_vecMulVec, smul_smul, ← Matrix.dotProduct_mulVec]
  have hscalar : (r + dotProduct x (V.mulVec x))⁻¹ +
      (r + dotProduct x (V.mulVec x))⁻¹ * (r⁻¹ * dotProduct x (V.mulVec x)) = r⁻¹ := by
    field_simp
  rw [← add_smul, hscalar, add_sub_cancel_right]

/-- The target variance reduction is derived from the actual inverse update,
with symmetry supplying the squared target alignment in the numerator. -/
theorem target_quadratic_update {ι : Type*} [Fintype ι] [DecidableEq ι]
    (A V : Matrix ι ι ℝ) (x t : ι → ℝ) (r : ℝ)
    (hAV : A * V = 1) (hV : V.IsSymm) (hr : r ≠ 0)
    (hden : r + dotProduct x (V.mulVec x) ≠ 0) :
    dotProduct t ((A + r⁻¹ • Matrix.vecMulVec x x)⁻¹.mulVec t) =
      dotProduct t (V.mulVec t) -
        (dotProduct t (V.mulVec x)) ^ 2 / (r + dotProduct x (V.mulVec x)) := by
  rw [rank_one_inverse_update A V x r hAV hr hden]
  simp only [Matrix.sub_mulVec, Matrix.smul_mulVec, Matrix.vecMulVec_mulVec,
    dotProduct_sub, dotProduct_smul, op_smul_eq_smul, smul_eq_mul]
  rw [← Matrix.mulVec_transpose, hV.eq, dotProduct_comm (V.mulVec x) t]
  ring

/-- A finite menu admits a bridge minimizing the actual next target half-width.
This is a one-step result, under a common failure budget. The inverse update is
proved above rather than assumed as a scalar variance-reduction identity.
Statistical use also requires nonnegative quadratic forms; this algebraic
ordering theorem does not claim positive semidefiniteness or coverage. -/
theorem exists_best_target_next {ι Candidate : Type*}
    [Fintype ι] [DecidableEq ι]
    (candidates : Finset Candidate) (hne : candidates.Nonempty)
    (A V : Matrix ι ι ℝ) (t : ι → ℝ)
    (x : Candidate → ι → ℝ) (r : Candidate → ℝ) (alpha : ℝ)
    (hAV : A * V = 1) (hV : V.IsSymm) (halpha : 0 < alpha)
    (hr : ∀ b ∈ candidates, r b ≠ 0)
    (hden : ∀ b ∈ candidates, r b + dotProduct (x b) (V.mulVec (x b)) ≠ 0) :
    ∃ selected ∈ candidates, ∀ other ∈ candidates,
      Real.sqrt (dotProduct t
        ((A + (r selected)⁻¹ • Matrix.vecMulVec (x selected) (x selected))⁻¹.mulVec t) /
          alpha) ≤
      Real.sqrt (dotProduct t
        ((A + (r other)⁻¹ • Matrix.vecMulVec (x other) (x other))⁻¹.mulVec t) /
          alpha) := by
  obtain ⟨selected, hselected, _, hmin⟩ := exists_best_next_width candidates hne
    (fun b => (dotProduct t (V.mulVec (x b))) ^ 2 /
      (r b + dotProduct (x b) (V.mulVec (x b))))
    (dotProduct t (V.mulVec t)) alpha halpha
  refine ⟨selected, hselected, fun other hother => ?_⟩
  simpa only [target_quadratic_update A V (x selected) t (r selected) hAV hV
      (hr selected hselected) (hden selected hselected),
    target_quadratic_update A V (x other) t (r other) hAV hV
      (hr other hother) (hden other hother)] using hmin other hother

end CausalAtlas.NonGaussianTargetUpdate

#print axioms CausalAtlas.NonGaussianTargetUpdate.radius_le_of_score_ge
#print axioms CausalAtlas.NonGaussianTargetUpdate.exists_best_next_width
#print axioms CausalAtlas.NonGaussianTargetUpdate.rank_one_inverse_update
#print axioms CausalAtlas.NonGaussianTargetUpdate.target_quadratic_update
#print axioms CausalAtlas.NonGaussianTargetUpdate.exists_best_target_next
