#!/usr/bin/env python3
"""Lint dispatch briefs for unsafe worktree-local venv usage and pytest -x."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BRIEFS_GLOB = "docs/dispatch-briefs/**/*.md"

PYTHON_RE = re.compile(r"\.venv/bin/python\b")
PYTEST_X_RE = re.compile(r"\bpytest\b.*\s(?:-x|--exitfirst)\b", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
CD_RE = re.compile(r"\bcd\s+(\"[^\"]+\"|'[^']+'|[^;&|#\s]+)")
SYMLINK_RE = re.compile(
    r"ln\s+-s\s+.*\.venv|#\s*venv\s+symlinked\b|\.venv\b.*\bsymlink(?:ed)?\b",
    re.IGNORECASE,
)
NEGATIVE_MARKER_RE = re.compile(r"//\s*(?:BAD|NOT THIS)\b", re.IGNORECASE)

ALLOWLIST_PYTEST_X = {
    # Finished archival brief kept because docs/best-practices/agent-activity-matrix.md cites it.
    "docs/dispatch-briefs/2026-05-08-night/1785-d4-decision-lineage.md",
}

# Grandfathered archival briefs exempt from the venv-guard rule (none remain).
# New briefs must satisfy the venv-guard rule.
ALLOWLIST_VENV_GUARD: set[str] = set()


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


_PRIMARY_REPO_ROOT_ENV = (
    "${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT}",
    "${LEARN_UKRAINIAN_PRIMARY_REPO_ROOT:-.}",
    "$LEARN_UKRAINIAN_PRIMARY_REPO_ROOT",
)


def _has_main_cd(line: str) -> bool:
    for match in CD_RE.finditer(line):
        path = match.group(1).strip("\"'")
        normalized = path.rstrip("/") or "."
        if normalized in {".", "./", *_PRIMARY_REPO_ROOT_ENV}:
            return True
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


def _is_negative_fence(rows: list[tuple[int, str, int | None]], fence_id: int | None) -> bool:
    if fence_id is None:
        return False
    return any(fid == fence_id and NEGATIVE_MARKER_RE.search(line) for _, line, fid in rows)


def lint_brief(path: Path) -> list[tuple[Path, int, str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        print(f"Error: {path} is not a valid UTF-8 file ({e})", file=sys.stderr)
        sys.exit(1)

    rows = _contexts(content)
    violations = []

    try:
        path_str = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        path_str = str(path)

    for index, (line_number, line, fence_id) in enumerate(rows):
        if (
            fence_id is not None
            and PYTHON_RE.search(line)
            and not _has_guard(rows, index)
            and path_str not in ALLOWLIST_VENV_GUARD
        ):
            violations.append((path, line_number, "missing cd-to-main or symlinked-venv before .venv/bin/python"))

        if PYTEST_X_RE.search(line) and path_str not in ALLOWLIST_PYTEST_X and not _is_negative_fence(rows, fence_id):
            violations.append(
                (path, line_number, "forbid pytest -x in dispatch briefs (masks downstream failures, see #1942)")
            )

    return violations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Lint dispatch briefs for `.venv/bin/python` commands that would break in "
            "unsymlinked worktrees, and for `pytest -x` usage.\n"
            "Use this before committing dispatch briefs; do not use it for general shell-script linting."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python scripts/audit/lint_dispatch_brief.py --brief docs/dispatch-briefs/2026-05-08-task.md
  .venv/bin/python scripts/audit/lint_dispatch_brief.py --all

Outputs:
  Prints one `path:line: message` row per unsafe invocation.
  Does not write files or modify briefs.

Exit codes:
  0 = all scanned briefs are clean
  1 = one or more violations were found
  2 = CLI usage error or unreadable input

Related:
  docs/dispatch-briefs/ authoring guardrail for issue #1787 and #1942.
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

    for path, line_number, msg in violations:
        print(f"{path}:{line_number}: {msg}")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
