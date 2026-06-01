# Reading Lenses

Different kinds of papers hide their real contribution — and their real
weaknesses — in different places. Pick the lens that matches the paper, then
read the corresponding sections with that lens's questions in mind. Most ML/AI
papers are **empirical**; when in doubt, use that lens.

Detecting the type quickly:
- Lots of tables, datasets, baselines, "we evaluate" → **empirical**
- Theorems, proofs, bounds, "we prove", few/no experiments → **theoretical**
- "We survey", taxonomy, dozens of citations, no new method → **survey**
- New system/library/framework, throughput/latency, deployment → **systems / applied**

---

## Empirical (most ML/NLP papers)

The contribution is a method + evidence that it works. The danger is that the
evidence is weaker than the abstract implies.

Scrutinize:
- **Baselines.** Are they strong and current, or weak strawmen? Are they tuned
  as carefully as the proposed method? Unfair baselines are the #1 way results
  get inflated.
- **The delta vs. the variance.** Is the improvement larger than the noise? Look
  for error bars / multiple seeds. A "+0.3" with no variance reported is suspect.
- **Apples-to-apples.** Same data, same compute budget, same model size as
  baselines? Or does the gain come from more parameters / more data?
- **Ablations.** Do they actually isolate the claimed mechanism, or change
  several things at once?
- **Generalization.** One dataset / one model size / one language → narrow.
  Note this explicitly even if the writing implies broad applicability.
- **Cherry-picking.** Are qualitative examples representative, or hand-picked?

Common overclaim: "state of the art" on a benchmark that the field has moved
past, or where the SOTA comparison omits a stronger concurrent method.

---

## Theoretical

The contribution is a proof, bound, or formal result. The danger is that the
assumptions quietly do the heavy lifting, or the result doesn't transfer to
practice.

Scrutinize:
- **Assumptions.** What must hold for the theorem to apply? Are they realistic
  (e.g. convexity, infinite width, i.i.d. data) or convenient fictions?
- **What the bound actually says.** Is it tight or loose? Asymptotic or
  finite-sample? A bound that's vacuous in practice is a weak contribution even
  if technically correct.
- **Gap to practice.** Do the authors connect the theory to anything empirical,
  or is it theory in a vacuum? Either is fine — but say which it is.
- **Novelty of technique.** Is the proof technique new, or a known argument
  applied to a new setting?

---

## Survey / Review

The contribution is organization and synthesis, not a new method. The danger is
a flat list of papers with no real insight.

Scrutinize:
- **Taxonomy quality.** Is the organizing structure illuminating, or arbitrary?
  A good survey gives you a mental map you didn't have before.
- **Synthesis vs. enumeration.** Does it draw connections and identify trends /
  open problems, or just summarize papers one by one?
- **Coverage & recency.** Are major works or recent directions missing? Is there
  a citation bias toward the authors' own group?
- **Critical stance.** Does it evaluate the field's claims, or just report them?

---

## Systems / Applied

The contribution is a working system, framework, or engineering result. The
danger is that the impressive demo doesn't generalize beyond the authors' setup.

Scrutinize:
- **What's actually new** vs. integration of existing components. Both can be
  valuable — be clear which it is.
- **Evaluation realism.** Real workloads or toy benchmarks? Are the baselines
  production-grade alternatives or naive implementations?
- **Cost honesty.** Throughput/latency gains reported against what hardware and
  what budget? Are trade-offs (memory, accuracy, complexity) disclosed?
- **Reproducibility.** Is the system released and runnable, or a description of
  something internal? This matters more for systems papers than any other type.

---

## Cross-cutting questions (apply to every paper)

- What would have to be true for the central claim to be wrong?
- If you removed the single best result, is the paper still convincing?
- Who benefits from this being true, and does that shape how it's presented?
- Is the limitation section honest, or perfunctory?
