# Output Schema

`paper-digest` produces **two** artifacts for every paper: a human-readable
Markdown report and a machine-readable JSON object. They contain the same
information; the JSON exists so the digest can flow into a knowledge base,
a notes database, or another agent step.

Write the digest in the **same language the user used in their request**
(e.g. a Chinese request → a Chinese report). Field *keys* in the JSON stay
in English so downstream tools can rely on them.

## Grounding rules (read these first)

These rules are what separate a digest from a generic summary:

- **Never invent numbers.** Only report a metric, dataset size, or result if
  it appears in the paper. If a field cannot be filled, write the value
  `"not reported"` (JSON) or `*not reported*` (Markdown). Do not guess.
- **Attribute claims.** When you state a headline result, point to where it
  came from — e.g. "(Table 2)", "(Sec. 4.3)", "(Fig. 3)". This lets a reader
  verify, and it keeps you honest.
- **Separate the authors' claims from your read.** The `contributions` and
  `key_results` fields report what the paper says. The `critique` field is
  *your* analysis: what is convincing, what is thin, what is unverifiable.
- **Use the parsed signals.** `code_links`, `arxiv_id`, figure/table counts
  come from `parse_paper.py` — trust those over your own scan of the text.

## JSON schema

```json
{
  "metadata": {
    "title": "string",
    "authors": "string | not reported",
    "venue_year": "string | not reported",
    "arxiv_id": "string | null",
    "doi": "string | null",
    "code_links": ["string"],
    "paper_type": "empirical | theoretical | survey | systems | other"
  },
  "tldr": "One sentence: what they did and why it matters.",
  "problem": {
    "problem": "What problem is addressed.",
    "motivation": "Why it matters / what gap exists in prior work."
  },
  "method": {
    "core_idea": "The central idea in 1-3 sentences.",
    "how_it_works": "Key technical components / mechanism.",
    "assumptions": "Stated or implicit assumptions (or 'not reported')."
  },
  "evidence": {
    "datasets": ["string"],
    "baselines": ["string"],
    "key_results": ["Result with source, e.g. '+3.2 BLEU over X (Table 2)'"],
    "metrics": ["string"]
  },
  "contributions": ["Distilled contribution claimed by the authors."],
  "critique": {
    "strengths": ["What is genuinely convincing."],
    "weaknesses": ["Where evidence is thin, claims overreach, or scope is narrow."],
    "open_questions": ["What you'd want to check or what they leave unanswered."]
  },
  "reproducibility": {
    "code_available": true,
    "data_available": "yes | no | partial | not reported",
    "compute_reported": "string | not reported",
    "reproducibility_risk": "low | medium | high",
    "notes": "string"
  },
  "positioning": "How this sits relative to prior work — what it builds on, what it departs from.",
  "follow_up_reading": ["Paper / topic worth reading next, and why."]
}
```

## Markdown report template

ALWAYS follow this section order:

```markdown
# [Title]

**Authors:** ...  ·  **Venue/Year:** ...  ·  **arXiv:** ...  ·  **Code:** ...
**Paper type:** empirical | theoretical | survey | systems

## TL;DR
One sentence.

## Problem & Motivation
What problem, and why the gap matters.

## Method
- **Core idea:** ...
- **How it works:** ...
- **Assumptions:** ...

## Evidence
- **Datasets:** ...
- **Baselines:** ...
- **Key results:** ... *(cite Table/Figure/Section for each)*

## Contributions
- ...

## Critical Reading
- **Strengths:** ...
- **Weaknesses / what to question:** ...
- **Open questions:** ...

## Reproducibility
Code / data availability, compute, and a risk rating with one line of reasoning.

## Positioning
Where it sits relative to prior work.

## Follow-up Reading
- ...
```

## Worked mini-example (abbreviated)

For a fictional paper "FastAttn: Linear-Time Attention via Bucketed Hashing":

```markdown
## TL;DR
FastAttn approximates softmax attention in linear time using locality-sensitive
hashing, claiming near-identical quality at 4x longer context.

## Critical Reading
- **Strengths:** Clean ablations isolating the hashing budget (Table 3); code released.
- **Weaknesses / what to question:** All results are on a single model size (125M);
  the quality-parity claim (Sec. 5.1) is shown only on perplexity, not downstream tasks.
- **Open questions:** Does the linear-time claim hold once hashing overhead is counted
  at short sequence lengths? Not reported.
```

Note how the critique cites sections, flags the single-model-size limitation,
and separates "what they showed" from "what they did not show."
