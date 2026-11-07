import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Tactic
import NonGaussianProbability
import NonGaussianDesign
import NonGaussianMoments

open scoped BigOperators
open MeasureTheory ProbabilityTheory

namespace NonGaussianBridge

/-- Exact linear estimation error. All coefficients are fixed before evaluation outcomes. -/
theorem linear_error_decomposition
    {I J : Type*} [Fintype I] [Fintype J]
    (a : I → ℝ) (x : I → J → ℝ) (target beta : J → ℝ) (noise : I → ℝ) :
    (∑ i, a i * ((∑ j, x i j * beta j) + noise i)) - ∑ j, target j * beta j =
      (∑ j, ((∑ i, a i * x i j) - target j) * beta j) + ∑ i, a i * noise i := by
  simp only [mul_add, Finset.sum_add_distrib, Finset.mul_sum, sub_mul,
    Finset.sum_sub_distrib, Finset.sum_mul, mul_assoc]
  rw [Finset.sum_comm]
  ring

/-- A computable box envelope, without a prior on the unknown coefficients. -/
theorem box_bias_bound {J : Type*} [Fintype J]
    (d beta bound : J → ℝ) (hbeta : ∀ j, |beta j| ≤ bound j) :
    |∑ j, d j * beta j| ≤ ∑ j, |d j| * bound j := by
  apply le_trans (Finset.abs_sum_le_sum_abs _ _)
  simp only [abs_mul]
  exact Finset.sum_le_sum fun j _ => mul_le_mul_of_nonneg_left (hbeta j) (abs_nonneg _)

/-- Exact matching removes approximation bias for every unknown parameter vector. -/
theorem exact_matching_error
    {I J : Type*} [Fintype I] [Fintype J]
    (a : I → ℝ) (x : I → J → ℝ) (target beta : J → ℝ) (noise : I → ℝ)
    (hmatch : ∀ j, ∑ i, a i * x i j = target j) :
    (∑ i, a i * ((∑ j, x i j * beta j) + noise i)) - ∑ j, target j * beta j =
      ∑ i, a i * noise i := by
  rw [linear_error_decomposition]
  simp only [hmatch, sub_self, zero_mul, Finset.sum_const_zero, zero_add]

variable {Ω : Type*} {mΩ : MeasurableSpace Ω} {μ : Measure Ω}
  [IsProbabilityMeasure μ]

/-- Complete fixed-parameter certificate, with a declared coordinate envelope. -/
theorem fixed_parameter_bridge_coverage
    {I J : Type*} [Fintype I] [Fintype J]
    (a : I → ℝ) (x : I → J → ℝ) (target beta bound : J → ℝ)
    (noise : I → Ω → ℝ) (v : I → ℝ) (δ : ℝ)
    (hbeta : ∀ j, |beta j| ≤ bound j)
    (hnoise : ∀ i, MemLp (noise i) 2 μ)
    (hindep : Pairwise fun i k => IndepFun (noise i) (noise k) μ)
    (hcenter : ∀ i, ∫ ω, noise i ω ∂μ = 0)
    (hv : ∀ i, variance (noise i) μ ≤ v i) (hδ : 0 < δ) :
    μ {ω | (∑ j, |(∑ i, a i * x i j) - target j| * bound j) +
      Real.sqrt ((∑ i, a i ^ 2 * v i) / δ) <
      |(∑ i, a i * ((∑ j, x i j * beta j) + noise i ω)) -
        ∑ j, target j * beta j|} ≤ ENNReal.ofReal δ := by
  simp_rw [linear_error_decomposition]
  exact CausalAtlasNonGaussian.weighted_error_probability a hnoise hindep hcenter hv hδ
    (box_bias_bound (fun j => (∑ i, a i * x i j) - target j) beta bound hbeta)

/-- Exact target matching gives coverage for every fixed parameter, without a parameter bound. -/
theorem exact_matching_bridge_coverage
    {I J : Type*} [Fintype I] [Fintype J]
    (a : I → ℝ) (x : I → J → ℝ) (target beta : J → ℝ)
    (noise : I → Ω → ℝ) (v : I → ℝ) (δ : ℝ)
    (hmatch : ∀ j, ∑ i, a i * x i j = target j)
    (hnoise : ∀ i, MemLp (noise i) 2 μ)
    (hindep : Pairwise fun i k => IndepFun (noise i) (noise k) μ)
    (hcenter : ∀ i, ∫ ω, noise i ω ∂μ = 0)
    (hv : ∀ i, variance (noise i) μ ≤ v i) (hδ : 0 < δ) :
    μ {ω | Real.sqrt ((∑ i, a i ^ 2 * v i) / δ) <
      |(∑ i, a i * ((∑ j, x i j * beta j) + noise i ω)) -
        ∑ j, target j * beta j|} ≤ ENNReal.ofReal δ := by
  simp_rw [exact_matching_error a x target beta _ hmatch]
  simpa only [zero_add] using
    (CausalAtlasNonGaussian.weighted_error_probability a hnoise hindep hcenter hv hδ
      (B := 0) (bias := 0) (by norm_num))

/-- Computable moment radius, retaining every off-diagonal parameter covariance. -/
noncomputable def momentRadius {I J : Type*} [Fintype I] [Fintype J]
    (a : I → ℝ) (x : I → J → ℝ) (target : J → ℝ)
    (K : J → J → ℝ) (v : I → ℝ) (δ : ℝ) : ℝ :=
  Real.sqrt (((∑ j, ∑ k,
    ((∑ i, a i * x i j) - target j) *
    ((∑ i, a i * x i k) - target k) * K j k) +
    ∑ i, a i ^ 2 * v i) / δ)

/-- Actual estimation error under the linear observation model. -/
def observationError {I J : Type*} [Fintype I] [Fintype J]
    (a : I → ℝ) (x : I → J → ℝ) (target : J → ℝ)
    (beta : J → Ω → ℝ) (noise : I → Ω → ℝ) (ω : Ω) : ℝ :=
  (∑ i, a i * ((∑ j, x i j * beta j ω) + noise i ω)) -
    ∑ j, target j * beta j ω

/-- End-to-end joint coverage for the original zero-mean parameter model with only moments.
Parameter coordinates may be correlated; no parameter norm bound or Gaussian law is assumed. -/
theorem moment_prior_bridge_coverage
    {I J : Type*} [Fintype I] [Fintype J]
    (a : I → ℝ) (x : I → J → ℝ) (target : J → ℝ)
    (beta : J → Ω → ℝ) (noise : I → Ω → ℝ)
    (K : J → J → ℝ) (v : I → ℝ) (δ : ℝ)
    (hbeta : ∀ j, MemLp (beta j) 2 μ) (hnoise : ∀ i, MemLp (noise i) 2 μ)
    (hbetaMean : ∀ j, ∫ ω, beta j ω ∂μ = 0)
    (hnoiseMean : ∀ i, ∫ ω, noise i ω ∂μ = 0)
    (hindep : Pairwise fun i k => IndepFun (noise i) (noise k) μ)
    (hK : ∀ j k, covariance (beta j) (beta k) μ = K j k)
    (hcross : ∀ j i, covariance (beta j) (noise i) μ = 0)
    (hv : ∀ i, variance (noise i) μ ≤ v i) (hδ : 0 < δ) :
    μ {ω | momentRadius a x target K v δ <
      |observationError a x target beta noise ω|} ≤ ENNReal.ofReal δ := by
  simp only [momentRadius, observationError, linear_error_decomposition]
  exact CausalAtlasNonGaussian.block_error_probability
    (fun j => (∑ i, a i * x i j) - target j) a hbeta hnoise hbetaMean hnoiseMean
    hindep hK hcross hv hδ

/-- A finite design-only menu has a minimum-radius plan with the actual joint coverage.
This is an existence/optimality theorem, not executable real-number comparison code. -/
theorem exists_best_moment_bridge
    {I J : Type*} [Fintype I] [Fintype J]
    (candidates : Finset (I → ℝ)) (hne : candidates.Nonempty)
    (x : I → J → ℝ) (target : J → ℝ)
    (beta : J → Ω → ℝ) (noise : I → Ω → ℝ)
    (K : J → J → ℝ) (v : I → ℝ) (δ : ℝ)
    (hbeta : ∀ j, MemLp (beta j) 2 μ) (hnoise : ∀ i, MemLp (noise i) 2 μ)
    (hbetaMean : ∀ j, ∫ ω, beta j ω ∂μ = 0)
    (hnoiseMean : ∀ i, ∫ ω, noise i ω ∂μ = 0)
    (hindep : Pairwise fun i k => IndepFun (noise i) (noise k) μ)
    (hK : ∀ j k, covariance (beta j) (beta k) μ = K j k)
    (hcross : ∀ j i, covariance (beta j) (noise i) μ = 0)
    (hv : ∀ i, variance (noise i) μ ≤ v i) (hδ : 0 < δ) :
    ∃ a ∈ candidates,
      (∀ comparator ∈ candidates,
        momentRadius a x target K v δ ≤ momentRadius comparator x target K v δ) ∧
      μ {ω | momentRadius a x target K v δ <
        |observationError a x target beta noise ω|} ≤ ENNReal.ofReal δ := by
  obtain ⟨a, ha, hminimal⟩ := CausalAtlas.NonGaussianDesign.exists_radius_minimizer
    candidates (fun a => momentRadius a x target K v δ) hne
  exact ⟨a, ha, hminimal,
    moment_prior_bridge_coverage a x target beta noise K v δ hbeta hnoise
      hbetaMean hnoiseMean hindep hK hcross hv hδ⟩

end NonGaussianBridge
