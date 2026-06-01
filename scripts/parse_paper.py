#!/usr/bin/env python3
"""
parse_paper.py — deterministic structure extraction for academic papers.

Given a PDF, this script extracts the signals that a language model should
NOT have to guess at: the title, arXiv id, DOI, links to code, section
headings, the abstract, and counts of figures / tables / citation markers.
It writes two artifacts and prints a short summary:

  <stem>.meta.json   structured signals (machine-readable)
  <stem>.txt         cleaned full text (so the model can read sections)

The point is reliability: feeding the model a clean text dump plus verified
metadata reduces hallucination (e.g. inventing a result number or claiming a
code release that does not exist) far more than asking it to eyeball a PDF.

Usage:
    python parse_paper.py PAPER.pdf [--out-dir DIR] [--max-chars N]

Requires: pdfplumber (preferred). Falls back to pypdf if pdfplumber is absent.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ----------------------------------------------------------------------------
# Text extraction
# ----------------------------------------------------------------------------

def extract_text(pdf_path: Path) -> tuple[str, int]:
    """Return (full_text, num_pages). Tries pdfplumber, then pypdf."""
    try:
        import pdfplumber  # type: ignore

        pages: list[str] = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        return "\n".join(pages), len(pages)
    except ImportError:
        pass

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(pdf_path))
        pages = [(p.extract_text() or "") for p in reader.pages]
        return "\n".join(pages), len(reader.pages)
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "No PDF library available. Install pdfplumber or pypdf."
        ) from exc


# ----------------------------------------------------------------------------
# Signal extraction (regex / heuristics)
# ----------------------------------------------------------------------------

ARXIV_RE = re.compile(r"arXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Z0-9]+)\b", re.IGNORECASE)
CODE_HOST_RE = re.compile(
    r"https?://(?:www\.)?(?:github\.com|gitlab\.com|huggingface\.co|"
    r"bitbucket\.org|sourceforge\.net|zenodo\.org)/[^\s)\]}>,]+",
    re.IGNORECASE,
)
# Figures/tables may be Arabic (Fig. 3) or Roman (TABLE VII, IEEE style).
FIGURE_RE = re.compile(r"\b(?:Figure|Fig\.?)\s*(\d+|[IVXLCDM]+)\b", re.IGNORECASE)
TABLE_RE = re.compile(r"\bTable\s*(\d+|[IVXLCDM]+)\b", re.IGNORECASE)
CITATION_MARKER_RE = re.compile(r"\[(\d+)\]")

# Journal running header (case-insensitive substring) and page header
# ("186 IEEETRANSACTIONS..."). The page-header pattern is case-SENSITIVE and
# length-guarded so it does not swallow short numbered headings like
# "1 Introduction" (whose IGNORECASE [A-Z]{4,} match was the original bug).
RUNNING_HEADER_RE = re.compile(r"IEEE\s*TRANSACTIONS|TRANSACTIONS\s+ON", re.IGNORECASE)
PAGE_HEADER_RE = re.compile(r"^\d+\s+[A-Z]{4,}")

# Numbered lines that are algorithm pseudocode, not section headings.
PSEUDOCODE_WORDS = {
    "begin", "end", "while", "for", "if", "else", "elseif", "initialize",
    "calculate", "evaluate", "sample", "select", "update", "generate", "make",
    "find", "compare", "return", "output", "input", "parameter", "note", "set",
    "perform", "randomly", "use", "denote", "suppose", "repeat", "until", "do",
    "then", "obtain", "construct", "build",
}

# Three heading styles:
#   Arabic   "3 Method" / "3.1 Setup"  (arXiv / ML style)
#   Roman    "II. PRELIMINARY"         (IEEE section style)
#   Lettered "B. Related Work"         (IEEE subsection style)
ARABIC_HEADING_RE = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s+([A-Z][^\n]{1,70})\s*$")
ROMAN_HEADING_RE = re.compile(r"^\s*(IX|IV|VI{0,3}|V|I{1,3}|X)\.\s+([A-Z][^\n]{1,70})\s*$")
LETTER_HEADING_RE = re.compile(r"^\s*([A-Z])\.\s+([A-Z][A-Za-z][^\n]{1,68})\s*$")
KNOWN_HEADINGS = [
    "abstract", "introduction", "related work", "background", "preliminaries",
    "method", "methods", "methodology", "approach", "model", "architecture",
    "experiments", "experimental setup", "evaluation", "results",
    "analysis", "ablation", "discussion", "limitations", "conclusion",
    "conclusions", "future work", "references", "appendix", "acknowledgments",
    "acknowledgements", "broader impact",
]
KNOWN_HEADING_RE = re.compile(
    r"^\s*(?:\d+\.?\s+)?(" + "|".join(re.escape(h) for h in KNOWN_HEADINGS) + r")\s*$",
    re.IGNORECASE,
)


def clean_text(raw: str) -> str:
    """Light normalization: de-hyphenate line breaks, collapse blank runs."""
    # join words split across line breaks: "represen-\ntation" -> "representation"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", raw)
    # collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def guess_title(text: str) -> str | None:
    """Best-effort title: first substantial line(s) on page 1 before 'abstract'."""
    lines = [ln.strip() for ln in text.splitlines()]
    candidates: list[str] = []
    for ln in lines[:25]:
        low = ln.lower()
        if not ln:
            if candidates:
                break
            continue
        if low.startswith("abstract") or "arxiv:" in low:
            break
        # author byline / affiliation / running header → title is done
        if re.search(r"@|\bhttp|\bemail|university|institute|\d{4}\b|"
                     r"\bieee\b|member|fellow", low):
            if candidates:
                break
            continue
        if len(ln) < 4:
            continue
        candidates.append(ln)
        if len(" ".join(candidates)) > 120:
            break
    title = " ".join(candidates).strip()
    return title or None


def extract_abstract(text: str) -> str | None:
    """Grab text between 'Abstract' and the first section / 'Introduction'."""
    m = re.search(r"\babstract\b", text, re.IGNORECASE)
    if not m:
        return None
    tail = text[m.end():]
    stop = re.search(
        r"\n\s*(?:\d+\.?\s+)?(?:introduction|1[\.\s]+introduction|keywords)\b",
        tail,
        re.IGNORECASE,
    )
    abstract = tail[: stop.start()] if stop else tail[:2500]
    abstract = re.sub(r"\s+", " ", abstract).strip(" :.-\n")
    return abstract[:2000] or None


def find_headings(text: str) -> list[str]:
    # Cut the bibliography so author initials ("A. Gupta, ...") don't look like
    # lettered subsections. Scan only the body for headings.
    cut = re.search(r"^\s*(REFERENCES|References)\s*$", text, re.MULTILINE)
    scan = text[: cut.start()] if cut else text

    headings: list[str] = []
    seen: set[str] = set()

    def add(h: str) -> None:
        h = h.strip()
        key = h.lower()
        if h and key not in seen and len(h) <= 80:
            seen.add(key)
            headings.append(h)

    for ln in scan.splitlines():
        s = ln.strip()
        if not s or RUNNING_HEADER_RE.search(s):
            continue
        if PAGE_HEADER_RE.match(s) and len(s) > 30:
            continue  # long all-caps running header, not a section
        # Drop formula/garbled lines where most tokens are single characters
        # (e.g. an extracted equation rendered as "1 K 1 1 K K").
        toks = s.split()
        if toks and sum(1 for t in toks if len(t) <= 1) / len(toks) > 0.5:
            continue
        if ROMAN_HEADING_RE.match(s) or LETTER_HEADING_RE.match(s):
            add(s)
            continue
        m = ARABIC_HEADING_RE.match(s)
        if m:
            first_word = m.group(2).split()[0].lower().rstrip(":")
            if first_word in PSEUDOCODE_WORDS:
                continue  # algorithm line, not a section heading
            add(s)
            continue
        if KNOWN_HEADING_RE.match(s):
            add(s)

    if cut:
        add("References")
    return headings


def distinct_count(pattern: re.Pattern, text: str) -> int:
    return len({m.group(1).upper() for m in pattern.finditer(text)})


def dedupe_keep_order(items: list[str]) -> list[str]:
    out, seen = [], set()
    for it in items:
        k = it.rstrip("/").lower()
        if k not in seen:
            seen.add(k)
            out.append(it.rstrip(".,);]"))
    return out


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def analyze(pdf_path: Path, max_chars: int) -> tuple[dict, str]:
    raw, num_pages = extract_text(pdf_path)
    text = clean_text(raw)

    code_links = dedupe_keep_order(CODE_HOST_RE.findall(text))
    arxiv = ARXIV_RE.search(text)
    doi = DOI_RE.search(text)

    meta = {
        "source_file": pdf_path.name,
        "num_pages": num_pages,
        "title_guess": guess_title(text),
        "arxiv_id": arxiv.group(1) if arxiv else None,
        "doi": doi.group(1) if doi else None,
        "code_links": code_links,
        "has_code_link": bool(code_links),
        "num_figures": distinct_count(FIGURE_RE, text),
        "num_tables": distinct_count(TABLE_RE, text),
        "num_citation_markers": distinct_count(CITATION_MARKER_RE, text),
        "section_headings": find_headings(text),
        "abstract": extract_abstract(text),
        "char_count": len(text),
        "truncated": len(text) > max_chars,
    }
    return meta, text[:max_chars]


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract structure from a paper PDF.")
    ap.add_argument("pdf", type=Path, help="Path to the paper PDF")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="Where to write outputs (default: alongside the PDF)")
    ap.add_argument("--max-chars", type=int, default=120_000,
                    help="Max characters of cleaned text to write (default 120k)")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"error: file not found: {args.pdf}", file=sys.stderr)
        return 1

    out_dir = args.out_dir or args.pdf.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.pdf.stem

    meta, text = analyze(args.pdf, args.max_chars)

    meta_path = out_dir / f"{stem}.meta.json"
    text_path = out_dir / f"{stem}.txt"
    meta["text_file"] = text_path.name
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    text_path.write_text(text)

    # Human-readable summary to stdout
    print(f"Parsed: {args.pdf.name}")
    print(f"  pages={meta['num_pages']}  figures={meta['num_figures']}  "
          f"tables={meta['num_tables']}  citations={meta['num_citation_markers']}")
    print(f"  title_guess: {meta['title_guess']}")
    print(f"  arxiv: {meta['arxiv_id']}   doi: {meta['doi']}")
    print(f"  code: {meta['code_links'] or 'none found'}")
    print(f"  sections ({len(meta['section_headings'])}): "
          f"{', '.join(meta['section_headings'][:12])}"
          + (" ..." if len(meta["section_headings"]) > 12 else ""))
    print(f"  wrote: {meta_path.name}, {text_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
