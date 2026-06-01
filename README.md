# paper-digest

An [Agent Skill](https://www.anthropic.com/news/skills) that turns a research
paper into a **structured, critically-read digest** — not a summary. It outputs
both a human-readable Markdown report and a machine-readable JSON object that
can flow into a notes database or another agent step.

The difference from "summarize this paper": a summary restates the abstract; a
digest does what a sharp reviewer does in five minutes — names the real
contribution, points to the one table that carries the paper, identifies the
experiment that's missing, and tells you whether you can reproduce it.

## What it produces

A fixed-schema digest with ten sections: metadata, TL;DR, problem & motivation,
method, evidence (datasets / baselines / cited results), distilled
contributions, a **strengths / weaknesses / open-questions critique**, a
reproducibility assessment, positioning against prior work, and follow-up
reading. The same content is emitted as JSON (English keys) so it is
composable; the prose follows the user's language.

See [`examples/`](examples/) for a real digest of an IEEE TEVC 2023 paper.

## Why it's built this way

The skill uses **progressive disclosure** — the standard Agent Skill pattern:

```
paper-digest/
├── SKILL.md                  # workflow + output contract (always loaded on trigger)
├── scripts/
│   ├── parse_paper.py        # deterministic PDF → signals + clean text
│   └── check_digest.py       # objective quality checks (runnable eval gate)
├── references/
│   ├── reading_lenses.md     # per-paper-type scrutiny checklists (loaded as needed)
│   └── output_schema.md      # JSON schema + Markdown template + grounding rules
└── evals/
    └── evals.json            # test prompts + assertions
```

The model only pays the token cost of a reference file when it actually needs
it. The deterministic work — extracting the title, arXiv id, DOI, code links,
section headings, and figure/table/citation counts — is done in Python, not by
the model. Feeding the model **verified** signals plus clean text is what keeps
the digest from inventing a result number or a nonexistent code release.

## Quickstart

```bash
# 1. Extract structure from a PDF
python scripts/parse_paper.py paper.pdf --out-dir ./out
#    → out/paper.meta.json (verified signals) + out/paper.txt (clean text)

# 2. (the skill writes the digest following references/output_schema.md)

# 3. Gate the output on objective checks
python scripts/check_digest.py out/paper.digest.json --meta out/paper.meta.json
```

Install as a skill by dropping the folder into your skills directory. It triggers whenever you share a paper and want
to understand, analyze, "digest", or assess it.

## Evaluation — the part most skills skip

`scripts/check_digest.py` makes the quality bar **runnable**. It verifies what
can be checked without human judgment, and exits non-zero so it can gate CI:

| Check | What it catches |
|---|---|
| `all_required_sections_present` | A truncated / lazy digest |
| `critique_has_strengths_and_weaknesses` | A summary masquerading as a review |
| `key_results_cite_sources` | Unattributed, hand-wavy results |
| `code_claim_matches_parser` | A **hallucinated** (or dropped) code release |
| `*_consistent_with_parser` | Invented arXiv id / DOI |

A passing run on the example paper, and a deliberately corrupted digest the
checker rejects:

```
[PASS] critique_has_strengths_and_weaknesses  — strengths=4, weaknesses=5
[PASS] code_claim_matches_parser              — digest=False, parser=False
9/9 checks passed.

# after injecting a fake github link and deleting weaknesses:
[FAIL] critique_has_strengths_and_weaknesses  — strengths=4, weaknesses=0
[FAIL] code_claim_matches_parser              — digest=True, parser=False
7/9 checks passed.   (exit code 1)
```

The negative test matters: an eval that only ever passes proves nothing.

## Engineering notes

The parser was hardened against a real two-column IEEE journal PDF, which
surfaced two bugs a clean arXiv-style paper never would have:

- **Roman-numeral tables.** IEEE labels tables `TABLE I … TABLE VII`, and the
  PDF text layer dropped the space (`TABLEVII`). An Arabic-only, space-required
  regex counted 0 of 7 tables. Fixed by matching Arabic *and* Roman numerals
  with an optional separator.
- **A case-insensitivity bug in header filtering.** The running-header filter
  (`^\d+\s+[A-Z]{4,}`, meant to drop `186 IEEE TRANSACTIONS…`) was compiled with
  `IGNORECASE`, so `[A-Z]{4,}` also matched the first four letters of
  `1 Introduction` and silently deleted real section headings. Fixed by making
  the all-caps page-header pattern case-sensitive and length-guarded.

Both regressions are covered by keeping a clean synthetic paper and the dense
IEEE paper as side-by-side test cases.

## License

MIT — see [LICENSE](LICENSE).
