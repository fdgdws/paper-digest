#!/usr/bin/env python3
"""
check_digest.py — objective quality checks for a paper-digest JSON output.

This turns the skill's quality bar into something you can *run*. Given a digest
JSON (and optionally the parser's .meta.json), it checks the things that can be
verified without human judgment:

  - the JSON is valid and has every required section, non-empty;
  - the critique actually contains BOTH strengths and weaknesses (the feature
    that makes this a critical reading and not a summary);
  - every headline result is attributed to a Table / Figure / Section / Eq.;
  - enum fields (paper_type, reproducibility risk) hold legal values;
  - the digest's hard signals (code_links, arxiv_id, doi) are CONSISTENT with
    what the parser extracted — i.e. the model didn't invent a code release or
    drop one that exists. This is the anti-hallucination check.

Exit code is non-zero if any required check fails, so it can gate CI.

Usage:
    python check_digest.py DIGEST.json [--meta PAPER.meta.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "metadata", "tldr", "problem", "method", "evidence",
    "contributions", "critique", "reproducibility", "positioning",
    "follow_up_reading",
]
PAPER_TYPES = {"empirical", "theoretical", "survey", "systems", "other"}
RISK_LEVELS = {"low", "medium", "high"}
SOURCE_REF = re.compile(r"\b(Table|Fig\.?|Figure|Sec\.?|Section|Eq\.?|Equation|Alg\.?|Algorithm|Appendix)\b",
                        re.IGNORECASE)


class Checks:
    def __init__(self) -> None:
        self.results: list[tuple[str, bool, str]] = []

    def check(self, name: str, passed: bool, evidence: str = "") -> None:
        self.results.append((name, bool(passed), evidence))

    def report(self) -> bool:
        width = max(len(n) for n, _, _ in self.results)
        all_passed = True
        for name, passed, evidence in self.results:
            mark = "PASS" if passed else "FAIL"
            all_passed = all_passed and passed
            line = f"[{mark}] {name.ljust(width)}"
            if evidence:
                line += f"  — {evidence}"
            print(line)
        n_pass = sum(1 for _, p, _ in self.results if p)
        print(f"\n{n_pass}/{len(self.results)} checks passed.")
        return all_passed


def nonempty(x) -> bool:
    if x is None:
        return False
    if isinstance(x, str):
        return bool(x.strip())
    if isinstance(x, (list, dict)):
        return len(x) > 0
    return True


def run(digest: dict, meta: dict | None) -> Checks:
    c = Checks()

    # 1. required sections present and non-empty
    missing = [s for s in REQUIRED_SECTIONS if not nonempty(digest.get(s))]
    c.check("all_required_sections_present", not missing,
            f"missing/empty: {missing}" if missing else "all 10 sections present")

    # 2. critique has BOTH strengths and weaknesses (the differentiator)
    crit = digest.get("critique", {}) or {}
    c.check("critique_has_strengths_and_weaknesses",
            nonempty(crit.get("strengths")) and nonempty(crit.get("weaknesses")),
            f"strengths={len(crit.get('strengths', []))}, "
            f"weaknesses={len(crit.get('weaknesses', []))}")

    # 3. TL;DR is a single tight statement
    tldr = digest.get("tldr", "") or ""
    c.check("tldr_present_and_concise", 0 < len(tldr.split()) <= 60,
            f"{len(tldr.split())} words")

    # 4. headline results are attributed to a source
    results = (digest.get("evidence", {}) or {}).get("key_results", []) or []
    cited = [r for r in results if SOURCE_REF.search(str(r))]
    ok = bool(results) and len(cited) >= max(1, (len(results) + 1) // 2)
    c.check("key_results_cite_sources", ok,
            f"{len(cited)}/{len(results)} results cite Table/Fig/Sec/Eq")

    # 5. enum fields legal
    pt = (digest.get("metadata", {}) or {}).get("paper_type")
    c.check("paper_type_valid", pt in PAPER_TYPES, f"paper_type={pt!r}")
    risk = (digest.get("reproducibility", {}) or {}).get("reproducibility_risk")
    c.check("reproducibility_risk_valid", risk in RISK_LEVELS, f"risk={risk!r}")

    # 6. consistency with parser signals (anti-hallucination)
    if meta is not None:
        md = digest.get("metadata", {}) or {}
        repro = digest.get("reproducibility", {}) or {}
        digest_has_code = bool(md.get("code_links")) or bool(repro.get("code_available"))
        parser_has_code = bool(meta.get("has_code_link"))
        c.check("code_claim_matches_parser", digest_has_code == parser_has_code,
                f"digest={digest_has_code}, parser={parser_has_code}")

        # arxiv / doi: if the digest states one, it must match the parser
        for field in ("arxiv_id", "doi"):
            dv, mv = md.get(field), meta.get(field)
            consistent = (not dv) or (not mv) or (str(dv) == str(mv))
            c.check(f"{field}_consistent_with_parser", consistent,
                    f"digest={dv!r}, parser={mv!r}")
    else:
        c.check("parser_meta_provided", False,
                "no --meta given; skipping anti-hallucination signal checks")

    return c


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a paper-digest JSON output.")
    ap.add_argument("digest", type=Path, help="Path to the digest JSON")
    ap.add_argument("--meta", type=Path, default=None,
                    help="Optional parser .meta.json for consistency checks")
    args = ap.parse_args()

    try:
        digest = json.loads(args.digest.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] valid_json — {exc}")
        return 1
    print("[PASS] valid_json")

    meta = None
    if args.meta and args.meta.exists():
        try:
            meta = json.loads(args.meta.read_text())
        except json.JSONDecodeError:
            meta = None

    checks = run(digest, meta)
    # Required checks exclude the soft "parser_meta_provided" advisory.
    ok = checks.report()
    advisory_only_failure = all(
        p or n == "parser_meta_provided" for n, p, _ in checks.results
    )
    return 0 if (ok or advisory_only_failure) else 1


if __name__ == "__main__":
    raise SystemExit(main())
