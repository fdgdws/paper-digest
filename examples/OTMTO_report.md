# Orthogonal Transfer for Multitask Optimization

**Authors:** Sheng-Hao Wu, Zhi-Hui Zhan, Kay Chen Tan, Jun Zhang · **Venue/Year:** IEEE TEVC 27(1), 2023 · **arXiv:** — · **Code:** none found
**Paper type:** empirical

> Example output of `paper-digest`. The companion machine-readable JSON is
> [`OTMTO.digest.json`](OTMTO.digest.json).

## TL;DR
OTMTO improves knowledge transfer in evolutionary multitask optimization for
tasks of *different dimensionalities*, via an optimization-based cross-task
mapping (CTM) plus orthogonal-experimental-design transfer (OT) that learns
which dimensions to combine.

## Problem & Motivation
Knowledge transfer (KT) in evolutionary multitask optimization struggles when
tasks have different dimensionalities and when dimensions differ in importance
(Sec. I). Unified-representation methods pad redundant dimensions, causing
negative transfer; uniform-probability crossover transfers low-quality
dimensions (Sec. II-C).

## Method
- **Core idea:** perform KT in each task's *original* space — map the source
  global-best into the target space (CTM), then use OED to find the best
  combination of dimensions (OT) (Sec. III).
- **How it works:** CTM frames the mapping as an inner optimization solved by
  DE/best/1, interpreted as aligning kNN hypotheses of the two tasks (Sec.
  III-B, Alg. 1). OT applies OED needing `2^ceil(log2(D+1))` evaluations instead
  of exponential (Sec. III-C). CDT transfers across similar dimensions via
  KL-divergence similarity (Sec. III-D). Transfer probabilities are
  reward-adapted (Eq. 11, 14).

## Evidence
- **Datasets:** CEC17 multitask benchmark; a new MTOP-DD benchmark (144
  problems); real-world Double Pole Balancing.
- **Baselines:** SODE, MFEA, MFEA2, EMTEA, MTGA.
- **Key results:** better than MFEA on 16/18 CEC17 tasks (Table II); on MTOP-DD
  outperforms all four EMTO baselines on most tasks, where EMTEA sometimes does
  worse than single-task SODE — direct evidence of negative transfer (Table
  III); ablations support each component (Tables IV–V); higher DPB success rates
  (Table VI).

## Contributions
- CTM mapping for tasks of different dimensionalities.
- OT: OED-based dimension-combination learning with few extra evaluations.
- CDT: KL-divergence cross-dimension transfer.
- Reward-based adaptive control of transfer intensity.
- A new configurable MTOP-DD benchmark suite.

## Critical Reading
- **Strengths:** addresses an under-studied, realistic setting and contributes a
  reusable benchmark; broad evaluation (standard + new + real-world + 3/5-task
  scalability) with Wilcoxon significance; thorough component ablations; a
  theoretical reading of CTM.
- **Weaknesses / what to question:** no code release, so reproduction means
  rebuilding an intricate multi-component algorithm; much evidence (other
  dimension combinations, running time) is supplementary-only; baselines reflect
  the ~2021 EMTO family; CTM's per-transfer inner optimization adds overhead
  that is only partly accounted for; variance/effect sizes are not foregrounded.
- **Open questions:** scalability to high dimensionality / many tasks given the
  inner-optimization cost (the authors flag this); when does CTM fail for very
  dissimilar tasks; do gains persist with other base solvers?

## Reproducibility
No code link found; benchmark data partly in supplementary; FE budgets and full
parameters are reported. **Risk: medium** — detailed pseudocode (Alg. 1–4) makes
reimplementation feasible, but no released code plus supplementary-only results
raise practical risk.

## Positioning
Extends EMTO from MFEA (single-population, unified representation, implicit KT)
toward multipopulation, explicit, dimension-aware KT in original spaces.
Distinct from autoencoder mappings (EMTEA) and random dimension shuffling
(MTGA); claims the first use of OED for cross-task KT.

## Follow-up Reading
MFEA [22], MFEA-II [33], EMTEA [28], CEC17 benchmark [65].
