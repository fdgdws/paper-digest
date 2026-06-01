---
name: paper-digest
description: >-
  Produce a rigorous, structured analysis of an academic paper — not a generic
  summary, but a critical reading with a fixed schema (problem, method, evidence,
  contributions, a strengths/weaknesses critique, reproducibility assessment, and
  positioning in prior work), output as both a Markdown report and a JSON object.
  Use this skill whenever the user shares a research paper (PDF, arXiv link, or
  pasted text) and wants to understand it, analyze it, "digest" or "break down" a
  paper, extract its contributions, assess a method, judge whether results hold up,
  build literature notes, or decide if a paper is worth reading in full — even if
  they just say "what's this paper about?" or "is this any good?". Tuned for
  machine learning / AI / NLP papers but works for any technical research paper.
  Prefer this over an ad-hoc summary whenever a paper is involved.
---

# Paper Digest

Turn a research paper into a structured, critically-read digest. The output is
deliberately more than a summary: it separates what the authors *claim* from
what the evidence *shows*, flags reproducibility risk, and positions the work
against prior art. This is the difference between "tell me about this paper" and
a digest a researcher can actually rely on for a literature review.

## When the input is a PDF (the main case)

### Step 1 — Parse the PDF deterministically

Run the bundled script first. Do not eyeball the PDF and start writing — the
script extracts verified signals (title, arXiv id, DOI, code links, figure /
table / citation counts, section headings, abstract) and a cleaned text dump.
Trusting these signals over an unaided read is what keeps the digest from
hallucinating result numbers or a nonexistent code release.

```bash
python scripts/parse_paper.py PAPER.pdf --out-dir ./out
```

This writes `out/PAPER.meta.json` (the signals) and `out/PAPER.txt` (clean
text). Read both. Use `meta.json`'s `code_links`, `arxiv_id`, and counts
directly in the output — they are verified; your own scan is not.

If the script reports `num_pages` but near-empty text, the PDF is likely
scanned/image-only — tell the user it needs OCR before it can be digested.

### Step 2 — Pick the reading lens

Read `references/reading_lenses.md` and select the lens matching the paper type
(empirical / theoretical / survey / systems). Most ML papers are empirical. The
lens tells you which sections to scrutinize and what overclaims to watch for —
this is where the *critical* part of the reading comes from.

### Step 3 — Read the relevant sections

From `PAPER.txt`, read the abstract, introduction, method, and experiments/results
closely; skim related work and read the limitations/conclusion. Use the section
headings in `meta.json` to navigate. Note the section/table/figure number next to
every result you plan to report, so you can attribute it.

### Step 4 — Write the digest

Follow `references/output_schema.md` exactly. Produce **both** outputs:
a Markdown report (the section order is fixed) and the JSON object. Save the JSON
to a file (e.g. `out/PAPER.digest.json`) so it can feed a knowledge base, and
show the Markdown report in the response. If a `present_files` tool is available,
present the JSON file.

## When the input is an arXiv link or pasted text

No PDF to parse. If it's an arXiv URL, note the id; if the user pasted text, work
from that. Skip Step 1, but still apply the lens (Step 2) and the same output
contract (Step 4). Be explicit in the report about what you could and could not
see (e.g. "results read from pasted abstract only").

## Non-negotiable grounding rules

These are restated from the schema because they matter most:

- **Never invent a number.** Report a metric only if it is in the paper. Missing
  → `not reported`. Guessing a result is the worst failure this skill can make.
- **Attribute every headline result** to its Table / Figure / Section.
- **Keep the authors' claims and your critique separate.** `contributions` and
  `evidence` report the paper; `critique` is your independent read.
- **Match the user's language** for the prose; keep JSON keys in English.

## What good looks like

A weak digest restates the abstract. A strong digest does what a sharp reviewer
does in five minutes: names the real contribution, points to the one table that
carries the paper, identifies the experiment that's missing, and tells you
whether you can reproduce it. Aim for that.

## Reference files

- `scripts/parse_paper.py` — deterministic PDF signal + text extraction (Step 1).
- `references/reading_lenses.md` — per-paper-type scrutiny checklists (Step 2).
- `references/output_schema.md` — the JSON schema, Markdown template, grounding
  rules, and a worked example (Step 4). Read this before writing the digest.
