import Mathlib.Probability.Moments.Variance
import Mathlib.Tactic

/-! Fixed-design probability bounds requiring finite variance, with no Gaussian law. -/

open MeasureTheory ProbabilityTheory
open scoped ENNReal

namespace CausalAtlasNonGaussian

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}
  [IsProbabilityMeasure μ]

/-- A deterministic bias plus centered L² noise has a variance-based error bound. -/
theorem shifted_chebyshev_pos {X : Ω → ℝ} (hX : MemLp X 2 μ)
    (hmean : ∫ ω, X ω ∂μ = 0) {V δ B bias : ℝ}
    (hV : 0 < V) (hδ : 0 < δ) (hv : variance X μ ≤ V) (hb : |bias| ≤ B) :
    μ {ω | B + Real.sqrt (V / δ) < |bias + X ω|} ≤ ENNReal.ofReal δ := by
  have hr : 0 < Real.sqrt (V / δ) := Real.sqrt_pos.2 (div_pos hV hδ)
  refine le_trans (measure_mono (t := {ω | Real.sqrt (V / δ) ≤ |X ω - ∫ a, X a ∂μ|}) ?_)
    (le_trans (meas_ge_le_variance_div_sq hX hr) (ENNReal.ofReal_le_ofReal ?_))
  · intro ω hω
    simp only [Set.mem_ofPred_eq, hmean, sub_zero] at *
    linarith [abs_add_le bias (X ω)]
  · simpa [Real.sq_sqrt (div_nonneg hV.le hδ.le), div_le_iff₀ (div_pos hV hδ),
      ← mul_div_assoc, hδ.ne'] using hv

variable {ι : Type*} [Fintype ι]

omit [IsProbabilityMeasure μ] in
/-- Scaling independent noises by deterministic coefficients preserves the variance identity. -/
theorem weighted_variance_eq {ε : ι → Ω → ℝ} (c : ι → ℝ)
    (hε : ∀ i, MemLp (ε i) 2 μ)
    (hindep : Pairwise fun i j => IndepFun (ε i) (ε j) μ) :
    variance (fun ω => ∑ i, c i * ε i ω) μ = ∑ i, c i ^ 2 * variance (ε i) μ := by
  convert
    (IndepFun.variance_sum (s := Finset.univ) (X := fun i ω => c i * ε i ω)
      (fun i _ => (hε i).const_mul (c i))
      (fun i _ j _ hij => (hindep hij).comp
        (measurable_const.mul measurable_id) (measurable_const.mul measurable_id))) using 1
  · congr 1
    funext ω
    simp only [Finset.sum_apply]
  · simp only [variance_const_mul]

omit [IsProbabilityMeasure μ] in
/-- Known individual variance upper bounds yield the weighted variance budget. -/
theorem weighted_variance_le {ε : ι → Ω → ℝ} (c : ι → ℝ)
    (hε : ∀ i, MemLp (ε i) 2 μ)
    (hindep : Pairwise fun i j => IndepFun (ε i) (ε j) μ)
    {v : ι → ℝ} (hv : ∀ i, variance (ε i) μ ≤ v i) :
    variance (fun ω => ∑ i, c i * ε i ω) μ ≤ ∑ i, c i ^ 2 * v i := by
  exact (weighted_variance_eq c hε hindep).trans_le
    (Finset.sum_le_sum fun i _ => mul_le_mul_of_nonneg_left (hv i) (sq_nonneg (c i)))

/-- Fixed coefficients preserve centering of the noises. -/
theorem weighted_mean_zero {ε : ι → Ω → ℝ} (c : ι → ℝ)
    (hε : ∀ i, MemLp (ε i) 2 μ) (hcenter : ∀ i, ∫ ω, ε i ω ∂μ = 0) :
    ∫ ω, (∑ i, c i * ε i ω) ∂μ = 0 := by
  simp only [integral_finsetSum _ (fun i _ => ((hε i).integrable (by norm_num)).const_mul (c i)),
    integral_const_mul, hcenter, mul_zero, Finset.sum_const_zero]

/-- The centered variance bound also covers the degenerate zero-variance case. -/
theorem shifted_chebyshev {X : Ω → ℝ} (hX : MemLp X 2 μ)
    (hmean : ∫ ω, X ω ∂μ = 0) {V δ B bias : ℝ}
    (hδ : 0 < δ) (hv : variance X μ ≤ V) (hb : |bias| ≤ B) :
    μ {ω | B + Real.sqrt (V / δ) < |bias + X ω|} ≤ ENNReal.ofReal δ := by
  by_cases hV : 0 < V
  · exact shifted_chebyshev_pos hX hmean hV hδ hv hb
  · have hvar0 : variance X μ = 0 :=
      le_antisymm (hv.trans (le_of_not_gt hV)) (variance_nonneg X μ)
    have hae : ∀ᵐ ω ∂μ, X ω = 0 := by
      simpa only [hmean] using ae_eq_integral_of_variance_eq_zero hX hvar0
    have hnull : μ {ω | B + Real.sqrt (V / δ) < |bias + X ω|} = 0 :=
      measure_eq_zero_iff_ae_notMem.mpr (hae.mono (fun ω hω => by
        simpa only [Set.mem_ofPred_eq, hω, add_zero] using
          (not_lt_of_ge (hb.trans (le_add_of_nonneg_right (Real.sqrt_nonneg (V / δ)))))))
    exact hnull.le.trans zero_le

/-- A full finite-variance error guarantee from assumptions on the primitive noises.
The coefficients are deterministic; no Gaussian distribution or positive variance is required. -/
theorem weighted_error_probability {ε : ι → Ω → ℝ} (c : ι → ℝ)
    (hε : ∀ i, MemLp (ε i) 2 μ)
    (hindep : Pairwise fun i j => IndepFun (ε i) (ε j) μ)
    (hcenter : ∀ i, ∫ ω, ε i ω ∂μ = 0)
    {v : ι → ℝ} {δ B bias : ℝ}
    (hv : ∀ i, variance (ε i) μ ≤ v i) (hδ : 0 < δ) (hb : |bias| ≤ B) :
    μ {ω | B + Real.sqrt ((∑ i, c i ^ 2 * v i) / δ) <
      |bias + ∑ i, c i * ε i ω|} ≤ ENNReal.ofReal δ := by
  exact shifted_chebyshev
    (memLp_finsetSum _ (fun i _ => (hε i).const_mul (c i)))
    (weighted_mean_zero c hε hcenter) hδ (weighted_variance_le c hε hindep hv) hb

end CausalAtlasNonGaussian
