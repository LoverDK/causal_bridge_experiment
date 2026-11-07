import NonGaussianProbability

/-! Moment-only bounds for a correlated parameter vector and uncorrelated observation noise. -/

open MeasureTheory ProbabilityTheory
open scoped ENNReal

namespace CausalAtlasNonGaussian

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}
  [IsProbabilityMeasure μ]
  {J I : Type*} [Fintype J] [Fintype I]

/-- The variance quadratic form is derived from the primitive covariances. -/
theorem weighted_correlated_variance_eq {β : J → Ω → ℝ} (d : J → ℝ)
    (hβ : ∀ j, MemLp (β j) 2 μ)
    {K : J → J → ℝ} (hK : ∀ j k, covariance (β j) (β k) μ = K j k) :
    variance (fun ω => ∑ j, d j * β j ω) μ = ∑ j, ∑ k, d j * d k * K j k := by
  simpa only [covariance_const_mul_left, covariance_const_mul_right, hK, mul_assoc,
    mul_left_comm] using
    (variance_fun_sum (fun j => (hβ j).const_mul (d j)))

/-- Zero cross covariances imply zero covariance between the two weighted blocks. -/
theorem weighted_cross_covariance_zero {β : J → Ω → ℝ} {ε : I → Ω → ℝ}
    (d : J → ℝ) (a : I → ℝ)
    (hβ : ∀ j, MemLp (β j) 2 μ) (hε : ∀ i, MemLp (ε i) 2 μ)
    (hcross : ∀ j i, covariance (β j) (ε i) μ = 0) :
    covariance (fun ω => ∑ j, d j * β j ω) (fun ω => ∑ i, a i * ε i ω) μ = 0 := by
  simpa only [covariance_const_mul_left, covariance_const_mul_right, hcross,
    mul_zero, Finset.sum_const_zero] using
    (covariance_fun_sum_fun_sum (fun j => (hβ j).const_mul (d j))
      (fun i => (hε i).const_mul (a i)))

theorem block_variance_le {β : J → Ω → ℝ} {ε : I → Ω → ℝ}
    (d : J → ℝ) (a : I → ℝ)
    (hβ : ∀ j, MemLp (β j) 2 μ) (hε : ∀ i, MemLp (ε i) 2 μ)
    (hindep : Pairwise fun i k => IndepFun (ε i) (ε k) μ)
    {K : J → J → ℝ} (hK : ∀ j k, covariance (β j) (β k) μ = K j k)
    (hcross : ∀ j i, covariance (β j) (ε i) μ = 0)
    {v : I → ℝ} (hv : ∀ i, variance (ε i) μ ≤ v i) :
    variance (fun ω => (∑ j, d j * β j ω) + ∑ i, a i * ε i ω) μ ≤
      (∑ j, ∑ k, d j * d k * K j k) + ∑ i, a i ^ 2 * v i := by
  rw [variance_fun_add (memLp_finsetSum _ (fun j _ => (hβ j).const_mul (d j)))
      (memLp_finsetSum _ (fun i _ => (hε i).const_mul (a i))),
    weighted_cross_covariance_zero d a hβ hε hcross,
    weighted_correlated_variance_eq d hβ hK, mul_zero, add_zero]
  exact add_le_add_right (weighted_variance_le a hε hindep hv) _

theorem block_mean_zero {β : J → Ω → ℝ} {ε : I → Ω → ℝ}
    (d : J → ℝ) (a : I → ℝ)
    (hβ : ∀ j, MemLp (β j) 2 μ) (hε : ∀ i, MemLp (ε i) 2 μ)
    (hβmean : ∀ j, ∫ ω, β j ω ∂μ = 0) (hεmean : ∀ i, ∫ ω, ε i ω ∂μ = 0) :
    ∫ ω, ((∑ j, d j * β j ω) + ∑ i, a i * ε i ω) ∂μ = 0 := by
  rw [integral_add
    ((memLp_finsetSum _ (fun j _ => (hβ j).const_mul (d j))).integrable (by norm_num))
    ((memLp_finsetSum _ (fun i _ => (hε i).const_mul (a i))).integrable (by norm_num)),
    weighted_mean_zero d hβ hβmean, weighted_mean_zero a hε hεmean, add_zero]

/-- Correlated parameter coordinates need only a known covariance matrix.
The parameter/noise blocks need zero cross covariance, not Gaussianity or independence. -/
theorem block_error_probability {β : J → Ω → ℝ} {ε : I → Ω → ℝ}
    (d : J → ℝ) (a : I → ℝ)
    (hβ : ∀ j, MemLp (β j) 2 μ) (hε : ∀ i, MemLp (ε i) 2 μ)
    (hβmean : ∀ j, ∫ ω, β j ω ∂μ = 0) (hεmean : ∀ i, ∫ ω, ε i ω ∂μ = 0)
    (hindep : Pairwise fun i k => IndepFun (ε i) (ε k) μ)
    {K : J → J → ℝ} (hK : ∀ j k, covariance (β j) (β k) μ = K j k)
    (hcross : ∀ j i, covariance (β j) (ε i) μ = 0)
    {v : I → ℝ} (hv : ∀ i, variance (ε i) μ ≤ v i)
    {δ : ℝ} (hδ : 0 < δ) :
    μ {ω | Real.sqrt (((∑ j, ∑ k, d j * d k * K j k) +
      ∑ i, a i ^ 2 * v i) / δ) < |(∑ j, d j * β j ω) + ∑ i, a i * ε i ω|}
      ≤ ENNReal.ofReal δ := by
  simpa only [zero_add, Pi.add_apply] using
    (shifted_chebyshev
      ((memLp_finsetSum _ (fun j _ => (hβ j).const_mul (d j))).add
        (memLp_finsetSum _ (fun i _ => (hε i).const_mul (a i))))
      (block_mean_zero d a hβ hε hβmean hεmean) hδ
      (block_variance_le d a hβ hε hindep hK hcross hv)
      (B := 0) (bias := 0) (by simp))

end CausalAtlasNonGaussian
