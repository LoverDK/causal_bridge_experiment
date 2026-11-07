import Mathlib.Data.Matrix.Basic
import Mathlib.Data.Real.Basic
import Mathlib.LinearAlgebra.Matrix.PosDef

/-!
Algebraic matrix kernels for the moment-based bridge estimator.
The first theorem takes explicit inverse identities. The second derives these
identities for actual inverse matrices from `V0.PosDef` and `G.PosSemidef`.
This file does not construct G from candidate vectors, define the selected
observation coefficients, or connect the scalar W to a probability theorem.
-/

namespace CausalAtlas.NonGaussianMatrix

theorem sandwich_identity {ι : Type*} [Fintype ι] [DecidableEq ι]
    (A0 V0 G V : Matrix ι ι ℝ)
    (hprior : A0 * V0 = 1) (hdesign : V * (A0 + G) = 1) :
    V * A0 * V0 * A0 * V + V * G * V = V := by
  rw [mul_assoc V A0 V0, hprior, mul_one]
  rw [← add_mul, ← mul_add, hdesign, one_mul]

/-- Positive definiteness and semidefiniteness establish the inverse premises
for the actual inverse matrices, rather than assuming the sandwich identity. -/
theorem sandwich_identity_of_posDef {ι : Type*} [Fintype ι] [DecidableEq ι]
    (V0 G : Matrix ι ι ℝ) (hV0 : V0.PosDef) (hG : G.PosSemidef) :
    let A0 := V0⁻¹
    let V := (A0 + G)⁻¹
    V * A0 * V0 * A0 * V + V * G * V = V := by
  have hA : (V0⁻¹ + G).PosDef := hV0.inv.add_posSemidef hG
  have hprior : V0⁻¹ * V0 = 1 :=
    Matrix.nonsing_inv_mul V0 ((Matrix.isUnit_iff_isUnit_det V0).mp hV0.isUnit)
  have hdesign : (V0⁻¹ + G)⁻¹ * (V0⁻¹ + G) = 1 :=
    Matrix.nonsing_inv_mul (V0⁻¹ + G)
      ((Matrix.isUnit_iff_isUnit_det (V0⁻¹ + G)).mp hA.isUnit)
  exact sandwich_identity V0⁻¹ V0 G (V0⁻¹ + G)⁻¹ hprior hdesign

#print axioms sandwich_identity
#print axioms sandwich_identity_of_posDef

end CausalAtlas.NonGaussianMatrix
