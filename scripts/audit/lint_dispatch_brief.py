#!/usr/bin/env python3
"""Lint dispatch briefs for unsafe worktree-local venv usage."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BRIEFS_GLOB = "docs/dispatch-briefs/**/*.md"

PYTHON_RE = re.compile(r"\.venv/bin/python\b")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
CD_RE = re.compile(r"\bcd\s+(\"[^\"]+\"|'[^']+'|[^;&|#\s]+)")
SYMLINK_RE = re.compile(
    r"ln\s+-s\s+.*\.venv|#\s*venv\s+symlinked\b|\.venv\b.*\bsymlink(?:ed)?\b",
    re.IGNORECASE,
)


def _contexts(text: str) -> list[tuple[int, str, int | None]]:
    """Return `(line_number, line, fence_id)` tuples for markdown text."""
    rows: list[tuple[int, str, int | None]] = []
    in_fence = False
    fence_char = ""
    fence_id: int | None = None
    next_fence_id = 0

    for line_number, line in enumerate(text.splitlines(), 1):
        match = FENCE_RE.match(line)
        if match:
            char = match.group(1)[0]
            if not in_fence:
                in_fence = True
                fence_char = char
                fence_id = next_fence_id
                next_fence_id += 1
            elif char == fence_char:
                rows.append((line_number, line, fence_id))
                in_fence = False
                fence_char = ""
                fence_id = None
                continue
        rows.append((line_number, line, fence_id))
    return rows


def _has_main_cd(line: str) -> bool:
    for match in CD_RE.finditer(line):
        path = match.group(1).strip("\"'")
        if "learn-ukrainian" in path and ".worktrees/" not in path:
            return True
    return False


def _has_guard(rows: list[tuple[int, str, int | None]], index: int) -> bool:
    _, line, fence_id = rows[index]
    python_match = PYTHON_RE.search(line)
    if python_match:
        prefix = line[: python_match.start()]
        if _has_main_cd(prefix) or SYMLINK_RE.search(prefix):
            return True

    for _, previous_line, previous_fence_id in rows[max(0, index - 5) : index]:
        if previous_fence_id != fence_id:
            continue
        if _has_main_cd(previous_line) or SYMLINK_RE.search(previous_line):
            return True
    return False


def lint_brief(path: Path) -> list[tuple[Path, int]]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        print(f"Error: {path} is not a valid UTF-8 file ({e})", file=sys.stderr)
        sys.exit(1)

    rows = _contexts(content)
    return [
        (path, line_number)
        for index, (line_number, line, fence_id) in enumerate(rows)
        if fence_id is not None and PYTHON_RE.search(line) and not _has_guard(rows, index)
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lint dispatch briefs for `.venv/bin/python` commands that would break in "
            "unsymlinked worktrees.\n"
            "Use this before committing dispatch briefs; do not use it for general shell-script linting."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/audit/lint_dispatch_brief.py --brief docs/dispatch-briefs/2026-05-08-task.md
  .venv/bin/python scripts/audit/lint_dispatch_brief.py --all

Outputs:
  Prints one `path:line: message` row per unsafe `.venv/bin/python` invocation.
  Does not write files or modify briefs.

Exit codes:
  0 = all scanned briefs are clean
  1 = one or more unsafe `.venv/bin/python` invocations were found
  2 = CLI usage error or unreadable input

Related:
  docs/dispatch-briefs/ authoring guardrail for issue #1787.
  .pre-commit-config.yaml local hook `lint-dispatch-brief-venv`.
""",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--brief",
        type=Path,
        help="Path to one dispatch brief markdown file, e.g. docs/dispatch-briefs/2026-05-08-task.md.",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help=f"Scan every markdown brief matching {BRIEFS_GLOB} under the repo root.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    paths = sorted(PROJECT_ROOT.glob(BRIEFS_GLOB)) if args.all else [args.brief]
    violations = []

    for path in paths:
        if not path.exists() or not path.is_file():
            parser.error(f"brief does not exist or is not a file: {path}")
        violations.extend(lint_brief(path))

    for path, line_number in violations:
        print(f"{path}:{line_number}: missing cd-to-main or symlinked-venv before .venv/bin/python")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
