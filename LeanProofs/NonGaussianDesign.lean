import Mathlib.Data.Finset.Max
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

/-!
Deterministic design lemmas for a non-Gaussian bridge extension.
These results do not assert matrix-logdet submodularity or a probability bound.
-/

namespace CausalAtlas.NonGaussianDesign

/-- Finite enumeration has an actual minimizer; optimality is a conclusion. -/
theorem exists_radius_minimizer {Design : Type*}
    (candidates : Finset Design) (radius : Design → ℝ)
    (hne : candidates.Nonempty) :
    ∃ selected ∈ candidates, ∀ comparator ∈ candidates,
      radius selected ≤ radius comparator := by
  exact Finset.exists_min_image candidates radius hne

/-- A mathematical selection from the finite minimizer theorem.
This real-valued definition is not an executable comparison algorithm. -/
noncomputable def selectMinRadius {Design : Type*}
    (candidates : Finset Design) (radius : Design → ℝ)
    (hne : candidates.Nonempty) : Design :=
  Classical.choose (exists_radius_minimizer candidates radius hne)

/-- The selected design is feasible and weakly improves every feasible radius. -/
theorem selectMinRadius_spec {Design : Type*}
    (candidates : Finset Design) (radius : Design → ℝ)
    (hne : candidates.Nonempty) :
    selectMinRadius candidates radius hne ∈ candidates ∧
      ∀ comparator ∈ candidates,
        radius (selectMinRadius candidates radius hne) ≤ radius comparator := by
  exact Classical.choose_spec (exists_radius_minimizer candidates radius hne)

/-- A nonnegative contraction factor propagates the initial optimality gap. -/
theorem geometric_gap_bound (q optimum : ℝ) (hq : 0 ≤ q)
    (gain : ℕ → ℝ) (hzero : gain 0 = 0)
    (n : ℕ)
    (hstep : ∀ t : ℕ, t < n → optimum - gain (t + 1) ≤ q * (optimum - gain t)) :
    optimum - gain n ≤ q ^ n * optimum := by
  induction n with
  | zero => simp [hzero]
  | succ n ih =>
    have hprevious := ih (fun t ht => hstep t (Nat.lt_trans ht (Nat.lt_succ_self n)))
    have hmul := mul_le_mul_of_nonneg_left hprevious hq
    simpa [pow_succ, mul_left_comm, mul_assoc] using
      (hstep n (Nat.lt_succ_self n)).trans hmul

/-- The finite-budget greedy factor follows from the usual gap recurrence.
Deriving that recurrence from a concrete set function is a separate obligation. -/
theorem greedy_finite_budget_bound (budget : ℕ) (hbudget : 1 ≤ budget)
    (optimum : ℝ) (gain : ℕ → ℝ) (hzero : gain 0 = 0)
    (hstep : ∀ t : ℕ, t < budget → optimum - gain (t + 1) ≤
      (1 - 1 / (budget : ℝ)) * (optimum - gain t)) :
    (1 - (1 - 1 / (budget : ℝ)) ^ budget) * optimum ≤ gain budget := by
  have hbudgetReal : (1 : ℝ) ≤ (budget : ℝ) := by exact_mod_cast hbudget
  have hreciprocal : 1 / (budget : ℝ) ≤ 1 := by
    simpa using (one_div_le_one_div_of_le (show (0 : ℝ) < 1 from zero_lt_one) hbudgetReal)
  have hgap := geometric_gap_bound (1 - 1 / (budget : ℝ)) optimum
    (sub_nonneg.mpr hreciprocal) gain hzero budget hstep
  nlinarith only [hgap]

#print axioms exists_radius_minimizer
#print axioms selectMinRadius_spec
#print axioms geometric_gap_bound
#print axioms greedy_finite_budget_bound

end CausalAtlas.NonGaussianDesign
