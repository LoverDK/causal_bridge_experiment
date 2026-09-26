import Mathlib.Data.Real.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Finset.Fold
import Mathlib.Tactic

open scoped BigOperators

namespace CausalAtlasBridge

theorem simplex_weighted_noise_bound
    {ι : Type*} [Fintype ι] (w noise scale : ι → ℝ)
    (hw : ∀ i, 0 ≤ w i) (hnoise : ∀ i, |noise i| ≤ scale i) :
    |∑ i, w i * noise i| ≤ ∑ i, w i * scale i := by
  calc
    |∑ i, w i * noise i| ≤ ∑ i, |w i * noise i| := Finset.abs_sum_le_sum_abs _ _
    _ = ∑ i, |w i| * |noise i| := by simp only [abs_mul]
    _ ≤ ∑ i, w i * scale i := by
      apply Finset.sum_le_sum
      intro i hi
      rw [abs_of_nonneg (hw i)]
      exact mul_le_mul_of_nonneg_left (hnoise i) (hw i)

theorem simplex_weighted_bias_bound
    {ι : Type*} [Fintype ι] (w bias envelope : ι → ℝ)
    (hw : ∀ i, 0 ≤ w i) (hbias : ∀ i, |bias i| ≤ envelope i) :
    |∑ i, w i * bias i| ≤ ∑ i, w i * envelope i := by
  exact simplex_weighted_noise_bound w bias envelope hw hbias

theorem selection_substitution
    {Ω : Type*} {α : Type*} (admissible certificate : α → Prop)
    (hbound : ∀ a, admissible a → certificate a) (select : Ω → α)
    (hselect : ∀ ω, admissible (select ω)) :
    ∀ ω, certificate (select ω) := by
  intro ω
  exact hbound (select ω) (hselect ω)

theorem two_world_absolute_loss (x d : ℝ) (hd : 0 ≤ d) :
    2 * d ≤ |x - d| + |x + d| := by
  by_cases h₁ : 0 ≤ x - d
  · by_cases h₂ : 0 ≤ x + d
    · simp [abs_of_nonneg h₁, abs_of_nonneg h₂]
      linarith
    · have hn₂ : x + d < 0 := lt_of_not_ge h₂
      simp [abs_of_nonneg h₁, abs_of_neg hn₂]
      linarith
  · have hn₁ : x - d < 0 := lt_of_not_ge h₁
    by_cases h₂ : 0 ≤ x + d
    · simp [abs_of_neg hn₁, abs_of_nonneg h₂]
      linarith
    · have hn₂ : x + d < 0 := lt_of_not_ge h₂
      simp [abs_of_neg hn₁, abs_of_neg hn₂]
      linarith

theorem barycentric_cancellation
    {ι : Type*} {V : Type*} [Fintype ι] [AddCommGroup V] [Module ℝ V]
    (w : ι → ℝ) (point : ι → V) (hw : ∑ i, w i = 1) :
    ∑ i, w i • (point i - ∑ j, w j • point j) = 0 := by
  calc
    ∑ i, w i • (point i - ∑ j, w j • point j)
        = (∑ i, w i • point i) - (∑ i, w i) • (∑ j, w j • point j) := by
          simp only [smul_sub, Finset.sum_sub_distrib, Finset.sum_smul]
    _ = (∑ i, w i • point i) - 1 • (∑ j, w j • point j) := by
      simp [hw]
    _ = 0 := by simp

def foldMaxPair (xs : List (ℝ × ℝ)) (initial : ℝ) : ℝ :=
  xs.foldl (fun acc p => max acc p.1) initial

def foldMinPair (xs : List (ℝ × ℝ)) (initial : ℝ) : ℝ :=
  xs.foldl (fun acc p => min acc p.2) initial

def intervalLowerEndpoint : List (ℝ × ℝ) → ℝ
  | [] => 0
  | (lo, _) :: rest => foldMaxPair rest lo

def intervalUpperEndpoint : List (ℝ × ℝ) → ℝ
  | [] => 0
  | (_, hi) :: rest => foldMinPair rest hi

private theorem foldMaxPair_le_iff (xs : List (ℝ × ℝ)) (initial x : ℝ) :
    foldMaxPair xs initial ≤ x ↔ initial ≤ x ∧ ∀ p ∈ xs, p.1 ≤ x := by
  induction xs generalizing initial with
  | nil => simp [foldMaxPair]
  | cons p rest ih =>
      change foldMaxPair rest (max initial p.1) ≤ x ↔ _
      rw [ih]
      simp only [max_le_iff]
      constructor
      · rintro ⟨hmax, hrest⟩
        refine ⟨hmax.1, ?_⟩
        intro q hq
        simp only [List.mem_cons] at hq
        rcases hq with rfl | hq
        · exact hmax.2
        · exact hrest q hq
      · rintro ⟨hinit, hrest⟩
        have hp := hrest p (by simp)
        have htail : ∀ q ∈ rest, q.1 ≤ x := by
          intro q hq
          exact hrest q (by simp [hq])
        exact ⟨⟨hinit, hp⟩, htail⟩

private theorem le_foldMinPair_iff (xs : List (ℝ × ℝ)) (initial x : ℝ) :
    x ≤ foldMinPair xs initial ↔ x ≤ initial ∧ ∀ p ∈ xs, x ≤ p.2 := by
  induction xs generalizing initial with
  | nil => simp [foldMinPair]
  | cons p rest ih =>
      change x ≤ foldMinPair rest (min initial p.2) ↔ _
      rw [ih]
      simp only [le_min_iff]
      constructor
      · rintro ⟨hmin, hrest⟩
        refine ⟨hmin.1, ?_⟩
        intro q hq
        simp only [List.mem_cons] at hq
        rcases hq with rfl | hq
        · exact hmin.2
        · exact hrest q hq
      · rintro ⟨hinit, hrest⟩
        have hp := hrest p (by simp)
        have htail : ∀ q ∈ rest, x ≤ q.2 := by
          intro q hq
          exact hrest q (by simp [hq])
        exact ⟨⟨hinit, hp⟩, htail⟩

theorem interval_intersection_endpoint_characterization
    (intervals : List (ℝ × ℝ)) (hne : intervals ≠ []) (x : ℝ) :
    (∀ p ∈ intervals, p.1 ≤ x ∧ x ≤ p.2) ↔
      intervalLowerEndpoint intervals ≤ x ∧ x ≤ intervalUpperEndpoint intervals := by
  cases intervals with
  | nil => contradiction
  | cons first rest =>
      cases first with
      | mk lo hi =>
          constructor
          · intro hall
            have hfirst := hall (lo, hi) (by simp)
            constructor
            · apply (foldMaxPair_le_iff rest lo x).2
              constructor
              · exact hfirst.1
              · intro p hp
                exact (hall p (by simp [hp])).1
            · apply (le_foldMinPair_iff rest hi x).2
              constructor
              · exact hfirst.2
              · intro p hp
                exact (hall p (by simp [hp])).2
          · intro hend
            have hlo := (foldMaxPair_le_iff rest lo x).1 hend.1
            have hhi := (le_foldMinPair_iff rest hi x).1 hend.2
            intro p hp
            simp only [List.mem_cons] at hp
            rcases hp with rfl | hp
            · exact ⟨hlo.1, hhi.1⟩
            · exact ⟨hlo.2 p hp, hhi.2 p hp⟩

theorem interval_projection_nonempty_implies_ordered
    (intervals : List (ℝ × ℝ)) (hne : intervals ≠ [])
    (h : ∃ x, ∀ p ∈ intervals, p.1 ≤ x ∧ x ≤ p.2) :
    intervalLowerEndpoint intervals ≤ intervalUpperEndpoint intervals := by
  obtain ⟨x, hx⟩ := h
  have hx' := (interval_intersection_endpoint_characterization intervals hne x).1 hx
  exact le_trans hx'.1 hx'.2

theorem interval_projection_ordered_implies_nonempty
    (intervals : List (ℝ × ℝ)) (hne : intervals ≠ [])
    (h : intervalLowerEndpoint intervals ≤ intervalUpperEndpoint intervals) :
    ∃ x, ∀ p ∈ intervals, p.1 ≤ x ∧ x ≤ p.2 := by
  refine ⟨intervalLowerEndpoint intervals, ?_⟩
  exact (interval_intersection_endpoint_characterization intervals hne _).2 ⟨le_rfl, h⟩

theorem interval_projection_lower_endpoint_feasible
    (intervals : List (ℝ × ℝ)) (hne : intervals ≠ [])
    (h : intervalLowerEndpoint intervals ≤ intervalUpperEndpoint intervals) :
    ∀ p ∈ intervals, p.1 ≤ intervalLowerEndpoint intervals ∧
      intervalLowerEndpoint intervals ≤ p.2 := by
  have hmem := (interval_intersection_endpoint_characterization intervals hne
    (intervalLowerEndpoint intervals)).2 ⟨le_rfl, h⟩
  exact hmem

theorem interval_projection_upper_endpoint_feasible
    (intervals : List (ℝ × ℝ)) (hne : intervals ≠ [])
    (h : intervalLowerEndpoint intervals ≤ intervalUpperEndpoint intervals) :
    ∀ p ∈ intervals, p.1 ≤ intervalUpperEndpoint intervals ∧
      intervalUpperEndpoint intervals ≤ p.2 := by
  have hmem := (interval_intersection_endpoint_characterization intervals hne
    (intervalUpperEndpoint intervals)).2 ⟨h, le_rfl⟩
  exact hmem

def projectFirst (region : Set (ℝ × ℝ)) : Set ℝ :=
  {x | ∃ y, (x, y) ∈ region}

def piNoBridge : Set (ℝ × ℝ) :=
  {z | -1 ≤ z.1 ∧ z.1 ≤ 1 ∧ -1 ≤ z.2 ∧ z.2 ≤ 1}

def piBridgeA : Set (ℝ × ℝ) :=
  {z | -1 ≤ z.1 ∧ z.1 ≤ 1 ∧ -1 ≤ z.2 ∧ z.2 ≤ 1 ∧ z.1 + z.2 = 0}

def piBridgeB : Set (ℝ × ℝ) :=
  {z | -1 ≤ z.1 ∧ z.1 ≤ 1 ∧ -1 ≤ z.2 ∧ z.2 ≤ 1 ∧ z.2 = 0}

def piBothBridges : Set (ℝ × ℝ) :=
  {z | -1 ≤ z.1 ∧ z.1 ≤ 1 ∧ -1 ≤ z.2 ∧ z.2 ≤ 1 ∧ z.1 + z.2 = 0 ∧ z.2 = 0}

private theorem project_no_bridge :
    projectFirst piNoBridge = Set.Icc (-1) 1 := by
  ext x
  constructor
  · rintro ⟨y, hxlo, hxhi, hylo, hyhi⟩
    exact ⟨hxlo, hxhi⟩
  · rintro ⟨hxlo, hxhi⟩
    exact ⟨0, hxlo, hxhi, by norm_num, by norm_num⟩

private theorem project_bridge_a :
    projectFirst piBridgeA = Set.Icc (-1) 1 := by
  ext x
  simp only [projectFirst, Set.mem_ofPred_eq, Set.mem_Icc]
  constructor
  · rintro ⟨y, hxlo, hxhi, hylo, hyhi, hsum⟩
    exact ⟨hxlo, hxhi⟩
  · rintro ⟨hxlo, hxhi⟩
    refine ⟨-x, hxlo, hxhi, ?_, ?_, ?_⟩ <;> nlinarith

private theorem project_bridge_b :
    projectFirst piBridgeB = Set.Icc (-1) 1 := by
  ext x
  simp only [projectFirst, Set.mem_ofPred_eq, Set.mem_Icc]
  constructor
  · rintro ⟨y, hxlo, hxhi, hylo, hyhi, hy⟩
    exact ⟨hxlo, hxhi⟩
  · rintro ⟨hxlo, hxhi⟩
    refine ⟨0, hxlo, hxhi, by norm_num, by norm_num, rfl⟩

private theorem project_both_bridges :
    projectFirst piBothBridges = Set.Icc 0 0 := by
  ext x
  simp only [projectFirst, Set.mem_ofPred_eq, Set.mem_Icc]
  constructor
  · rintro ⟨y, hxlo, hxhi, hylo, hyhi, hsum, hy⟩
    have hxzero : x = 0 := by nlinarith [hsum, hy]
    exact ⟨by linarith, by linarith⟩
  · intro hx
    have hxzero : x = 0 := by nlinarith
    subst x
    exact ⟨0, by norm_num, by norm_num, by norm_num, by norm_num, by norm_num, rfl⟩

structure ProjectionInterval (region : Set ℝ) where
  lower : ℝ
  upper : ℝ
  ordered : lower ≤ upper
  exact : region = Set.Icc lower upper

def ProjectionInterval.width {region : Set ℝ} (i : ProjectionInterval region) : ℝ :=
  i.upper - i.lower

def noBridgeProjection : ProjectionInterval (projectFirst piNoBridge) :=
  ⟨-1, 1, by norm_num, project_no_bridge⟩

def bridgeAProjection : ProjectionInterval (projectFirst piBridgeA) :=
  ⟨-1, 1, by norm_num, project_bridge_a⟩

def bridgeBProjection : ProjectionInterval (projectFirst piBridgeB) :=
  ⟨-1, 1, by norm_num, project_bridge_b⟩

def bothBridgesProjection : ProjectionInterval (projectFirst piBothBridges) :=
  ⟨0, 0, by norm_num, project_both_bridges⟩

theorem complementarity_pi_width_table :
    noBridgeProjection.width = 2 ∧ bridgeAProjection.width = 2 ∧
      bridgeBProjection.width = 2 ∧ bothBridgesProjection.width = 0 := by
  norm_num [ProjectionInterval.width, noBridgeProjection, bridgeAProjection,
    bridgeBProjection, bothBridgesProjection]

theorem complementarity_pi_width_violates_diminishing_returns :
    noBridgeProjection.width - bridgeAProjection.width <
      bridgeBProjection.width - bothBridgesProjection.width := by
  rcases complementarity_pi_width_table with ⟨h0, hA, hB, hAB⟩
  rw [h0, hA, hB, hAB]
  norm_num

end CausalAtlasBridge
