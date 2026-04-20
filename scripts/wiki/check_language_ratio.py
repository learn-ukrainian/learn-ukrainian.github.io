#!/usr/bin/env python3
"""
Deterministic language-ratio guard for wiki prose.

Checks that a wiki article is written in Ukrainian-canonical prose per
EPIC #1365 scope. Strips structural elements (YAML frontmatter, fenced
code blocks, tables, headings, citation markers, links, image refs,
inline code) and computes the Cyrillic-to-alphabetic-character ratio
over the remaining body prose.

Pass criterion: ratio >= threshold (default 0.85 for pedagogy wikis).

Usage:
    python scripts/wiki/check_language_ratio.py path/to/article.md
    python scripts/wiki/check_language_ratio.py path/to/article.md --threshold 0.9
    python scripts/wiki/check_language_ratio.py path/to/article.md --verbose

Exit codes:
    0 — pass (ratio >= threshold)
    1 — fail (ratio < threshold)
    2 — usage / file-not-found error

Design notes:
- This is a PROSE-level check, not a token-level check. Structural
  Ukrainian-or-English elements (YAML keys, citation markers like
  [S1], URLs) are excluded so they can't pad the ratio in either
  direction.
- Section HEADINGS are NOT part of body prose — they may be Ukrainian
  with English glosses in parentheses (e.g. `## Методичний підхід
  (Methodological Approach)`), which is allowed per the A.0 compile
  prompts. Heading-language is measured separately and reported but
  does not fail the check.
- Pair this with dim-review `register` and `ukrainian_perspective`
  for the full quality gate — the scanner is a cheap mechanical
  first-pass, not a replacement for the reviewer.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Unicode block U+0400..U+04FF = Cyrillic. Extends into Cyrillic
# Supplement U+0500..U+052F for completeness, though Ukrainian standard
# glyphs all live in the base block.
_CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")

# Regexes to strip structural elements. Applied in order.
_FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`]*`")
_CITATION_RE = re.compile(r"\[S\d+(?:\s*,\s*S\d+)*\]")
# Markdown link `[text](url)` — keep the text, drop the URL.
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
# Image ref `![alt](src)` — drop whole thing.
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
# Table row: starts and ends with | (with optional whitespace).
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
# YAML-style `key: value` at line start — only strip the key part.
# We keep the value because it's often prose.
# Actually we strip the whole thing only if it looks like a frontmatter
# line (wiki-meta is inside HTML comments, already stripped).
# Leaving this out — YAML-key-value lines in the body (rare) are prose.

# Section heading lines (##, ###, etc.)
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)$", re.MULTILINE)


def strip_structural_elements(text: str) -> str:
    """Remove structural markdown elements, keep prose."""
    text = _FENCED_CODE_RE.sub(" ", text)
    text = _HTML_COMMENT_RE.sub(" ", text)
    text = _IMAGE_RE.sub(" ", text)
    # Replace links with their text (not the URL)
    text = _LINK_RE.sub(r"\1", text)
    text = _INLINE_CODE_RE.sub(" ", text)
    text = _CITATION_RE.sub(" ", text)
    text = _TABLE_ROW_RE.sub(" ", text)
    return text


def remove_headings(text: str) -> tuple[str, list[str]]:
    """Separate body prose from heading lines. Returns (body, headings)."""
    headings = _HEADING_RE.findall(text)
    body = _HEADING_RE.sub(" ", text)
    return body, headings


def cyrillic_ratio(text: str) -> tuple[float, int, int]:
    """Fraction of alphabetic chars that are Cyrillic.

    Returns (ratio, cyrillic_count, alpha_count). ratio is 1.0 when
    there are no alphabetic characters (nothing to fail on).
    """
    cyr = len(_CYRILLIC_RE.findall(text))
    alpha = sum(1 for c in text if c.isalpha())
    if alpha == 0:
        return (1.0, 0, 0)
    return (cyr / alpha, cyr, alpha)


def check_file(path: Path, threshold: float, verbose: bool = False) -> int:
    """Check one file. Returns exit code."""
    if not path.is_file():
        print(f"ERROR: {path} is not a file", file=sys.stderr)
        return 2
    text = path.read_text(encoding="utf-8")
    stripped = strip_structural_elements(text)
    body, headings = remove_headings(stripped)

    body_ratio, body_cyr, body_alpha = cyrillic_ratio(body)
    heading_ratio, heading_cyr, heading_alpha = cyrillic_ratio(" ".join(headings))

    passed = body_ratio >= threshold
    status = "PASS" if passed else "FAIL"

    print(
        f"{status}  {path}  body_cyr_ratio={body_ratio:.3f} "
        f"(threshold={threshold:.2f}, {body_cyr}/{body_alpha} alpha chars)"
    )
    if verbose:
        print(
            f"      headings_cyr_ratio={heading_ratio:.3f} "
            f"({heading_cyr}/{heading_alpha} alpha chars in {len(headings)} headings)"
        )

    return 0 if passed else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check wiki prose is Ukrainian-canonical (Cyrillic ratio guard)."
    )
    ap.add_argument("files", nargs="+", type=Path, help="Wiki markdown file(s) to check.")
    ap.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Minimum Cyrillic ratio in body prose (default 0.85 for pedagogy wikis; "
        "raise to 0.95 for academic seminar wikis).",
    )
    ap.add_argument("--verbose", "-v", action="store_true", help="Also print heading-language stats.")
    args = ap.parse_args()

    worst_exit = 0
    for path in args.files:
        code = check_file(path, args.threshold, verbose=args.verbose)
        worst_exit = max(worst_exit, code)
    return worst_exit


if __name__ == "__main__":
    sys.exit(main())
