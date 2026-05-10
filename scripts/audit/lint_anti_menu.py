#!/usr/bin/env python3
"""Detect MEMORY #0I anti-menu sign-off prompts in markdown.

The detector is intentionally heuristic. It looks for these regex shapes:

- Inline parenthesized choice labels with chooser context: ``(a) ... vs ... (b)``
  or ``(a) ... or ... (b)`` near ``do we``, ``decision``, ``sign off``, etc.
- Direct user-delegation questions: ``Want me to A, B, or C?`` and
  ``Should I/we do X or Y?``.
- Inline numbered chooser menus: ``1) Do X 2) Do Y 3) Do Z -- which?``.
- Sign-off preambles: ``Sign off on these N options:`` followed shortly by
  a numbered list.

Exemptions are markdown-aware enough for handoff docs: fenced code blocks,
tables, ``## Acceptance criteria`` sections, meta-example preambles, and lines
with or immediately after ``Done:``, ``Status:``, or ``Plan:`` are skipped.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    """One anti-menu match in a scanned document."""

    line_number: int
    snippet: str


PAREN_OPTION_RE = re.compile(
    r"\([a-z]\)[^\n]{0,120}\b(?:vs\.?|or)\b[^\n]{0,120}\([a-z]\)",
    re.IGNORECASE,
)
PAREN_OPTION_CONTEXT_RE = re.compile(
    r"\b(?:decision|do we|should i|should we|want me|approve|approval|sign off|choose)\b",
    re.IGNORECASE,
)
META_EXAMPLE_RE = re.compile(
    r"\b(?:forbid|forbids|forbidden|not acceptable|do not propose|no menus?|anti-menu|anti-pattern|wrong pattern)\b",
    re.IGNORECASE,
)
DIRECT_QUESTION_RE = re.compile(
    r"\b(?:do you want me to|want me to|should i|should we)\b[^\n?]{0,180}\bor\b[^\n?]{0,100}\?",
    re.IGNORECASE,
)
INLINE_NUMBERED_MENU_RE = re.compile(
    r"(?:^|\s)1\)\s+\S[^\n]{0,100}(?:^|\s)2\)\s+\S[^\n]{0,160}\b(?:which|pick|choose|sign off)\b[^\n?]*\?",
    re.IGNORECASE,
)
SIGNOFF_OPTIONS_RE = re.compile(
    r"\bsign\s+off\s+on\s+these\s+\d+\s+options\s*:?",
    re.IGNORECASE,
)
NUMBERED_LIST_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?\d+[.)]\s+\S")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
PREFIX_EXEMPT_RE = re.compile(
    r"^\s*(?:[-*]\s*)?(?:Done|Status|Plan|Forbidden patterns?):(?:\s|$)",
    re.IGNORECASE,
)
META_EXAMPLE_LOOKBACK_LINES = 3


def _is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 2


def _normalize_heading(text: str) -> str:
    text = text.rstrip("#").strip().rstrip(":")
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text).strip().lower()
    return text.rstrip(":")


def _trim_snippet(snippet: str, limit: int = 120) -> str:
    collapsed = " ".join(snippet.split())
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[: limit - 3]}..."


def _find_numbered_list_after(lines: list[str], start_index: int) -> bool:
    checked = 0
    for line in lines[start_index + 1 : start_index + 7]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return False
        checked += 1
        if NUMBERED_LIST_LINE_RE.search(line):
            return True
        if checked >= 4:
            return False
    return False


def _has_meta_example_context(lines: list[str], index: int) -> bool:
    start = max(0, index - META_EXAMPLE_LOOKBACK_LINES)
    return any(META_EXAMPLE_RE.search(line) for line in lines[start : index + 1])


def scan_text(text: str) -> list[Violation]:
    """Return anti-menu violations in markdown text."""

    violations: list[Violation] = []
    lines = text.splitlines()
    in_fence = False
    in_acceptance_criteria = False
    acceptance_heading_level: int | None = None
    previous_nonblank = ""

    for index, line in enumerate(lines):
        stripped = line.strip()

        if FENCE_RE.match(line):
            in_fence = not in_fence
            previous_nonblank = stripped or previous_nonblank
            continue

        heading = HEADING_RE.match(stripped)
        if heading:
            level = len(heading.group(1))
            heading_text = _normalize_heading(heading.group(2))
            if in_acceptance_criteria and acceptance_heading_level is not None and level <= acceptance_heading_level:
                in_acceptance_criteria = False
                acceptance_heading_level = None
            if heading_text == "acceptance criteria":
                in_acceptance_criteria = True
                acceptance_heading_level = level

        exempt = (
            in_fence
            or in_acceptance_criteria
            or _is_table_line(line)
            or bool(PREFIX_EXEMPT_RE.match(line))
            or bool(PREFIX_EXEMPT_RE.match(previous_nonblank))
        )

        if not exempt and not _has_meta_example_context(lines, index):
            paren_match = PAREN_OPTION_RE.search(line)
            if paren_match and PAREN_OPTION_CONTEXT_RE.search(line):
                violations.append(Violation(index + 1, _trim_snippet(paren_match.group(0))))
                continue

            for pattern in (DIRECT_QUESTION_RE, INLINE_NUMBERED_MENU_RE):
                match = pattern.search(line)
                if match:
                    violations.append(Violation(index + 1, _trim_snippet(match.group(0))))
                    break
            else:
                signoff_match = SIGNOFF_OPTIONS_RE.search(line)
                if signoff_match and _find_numbered_list_after(lines, index):
                    violations.append(Violation(index + 1, _trim_snippet(signoff_match.group(0))))

        if stripped:
            previous_nonblank = stripped

    return violations


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Detect MEMORY #0I anti-menu sign-off prompts in markdown.\n"
            "Use before committing handoffs or dispatch briefs; do not use as a general markdown style linter."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/audit/lint_anti_menu.py --text docs/session-state/current.md
  cat handoff.md | .venv/bin/python scripts/audit/lint_anti_menu.py --stdin

Outputs:
  Prints one line per violation as: path:line: anti-menu pattern detected — '<matched-snippet>'
  Writes no files and has no side effects.

Exit codes:
  0 = no anti-menu patterns detected
  1 = one or more anti-menu patterns detected
  2 = input file is not valid UTF-8

Related:
  MEMORY.md rule #0I; issue #1787 sub-task 1.4.
""",
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", type=Path, help="Markdown file to scan, e.g. docs/session-state/current.md")
    input_group.add_argument("--stdin", action="store_true", help="Read markdown text from stdin instead of a file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.stdin:
        label = "<stdin>"
        text = sys.stdin.read()
    else:
        label = str(args.text)
        try:
            text = args.text.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            print(f"Error: {label} is not a valid UTF-8 file ({e})", file=sys.stderr)
            return 1

    violations = scan_text(text)
    for violation in violations:
        print(f"{label}:{violation.line_number}: anti-menu pattern detected — '{violation.snippet}'")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
