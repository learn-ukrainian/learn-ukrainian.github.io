#!/usr/bin/env python3
"""Reject negated GitHub closing references in pull-request prose.

GitHub closing-reference parsing is lexical.  This linter therefore does not
try to infer intent: it rejects a negation placed before a closing keyword and
an issue reference, and leaves deliberate closing references untouched.
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
    """One unsafe closing-reference phrase."""

    line_number: int
    phrase: str


_NEGATED_CLOSING_REFERENCE = re.compile(
    r"\b(?:do(?:es)?\s+not|did\s+not|will\s+not|won['’]t|cannot|can['’]t|without|not)"
    r"(?:\s+[A-Za-z]+){0,3}?\s+"
    r"(?:clos(?:e|es|ed|ing)|fix(?:es|ed|ing)?|resolv(?:e|es|ed|ing))\s+#(?P<issue>[1-9][0-9]*)\b",
    re.IGNORECASE,
)


def scan_text(text: str) -> list[Violation]:
    """Return every negated closing reference, with its one-based line."""

    return [
        Violation(line_number, match.group(0))
        for line_number, line in enumerate(text.splitlines(), start=1)
        for match in _NEGATED_CLOSING_REFERENCE.finditer(line)
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--text", type=Path, help="UTF-8 PR-body fixture to scan")
    inputs.add_argument("--stdin", action="store_true", help="Read a PR body from standard input")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.stdin:
        label = "<stdin>"
        text = sys.stdin.read()
    else:
        label = str(args.text)
        try:
            text = args.text.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"{label}: not utf-8", file=sys.stderr)
            return 2

    violations = scan_text(text)
    for violation in violations:
        print(
            f"{label}:{violation.line_number}: negated GitHub closing reference: "
            f"{violation.phrase!r}; use 'Refs #{_issue_number(violation.phrase)}' "
            "or 'leaves #N open' instead"
        )
    return 1 if violations else 0


def _issue_number(phrase: str) -> str:
    match = _NEGATED_CLOSING_REFERENCE.search(phrase)
    if match is None:  # pragma: no cover - callers pass a regex match phrase.
        raise ValueError("phrase is not a negated closing reference")
    return match.group("issue")


if __name__ == "__main__":
    raise SystemExit(main())
