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
    "docs/dispatch-briefs/2026-05-05-1665-holovashchuk-ingest.md",
    "docs/dispatch-briefs/2026-05-05-1673-1661-cot-tier1-prompts.md",
    "docs/dispatch-briefs/2026-05-05-1679-search-etymology-removal.md",
    "docs/dispatch-briefs/2026-05-05-1680-vesum-split-and-mcp-wiki-packet.md",
    "docs/dispatch-briefs/2026-05-05-1682-test-delegate-isolation.md",
    "docs/dispatch-briefs/2026-05-05-1687-codeql-suppression-rework.md",
    "docs/dispatch-briefs/2026-05-05-bakeoff-aggregator-script.md",
    "docs/dispatch-briefs/2026-05-05-bakeoff-telemetry-instrumentation.md",
    "docs/dispatch-briefs/2026-05-05-codeql-A-path-injection.md",
    "docs/dispatch-briefs/2026-05-05-codeql-B-secrets-exposure.md",
    "docs/dispatch-briefs/2026-05-05-codeql-C-url-tag-validation.md",
    "docs/dispatch-briefs/2026-05-05-codeql-cleanup-gemini.md",
    "docs/dispatch-briefs/2026-05-08-night/1785-d4-decision-lineage.md",
    "docs/dispatch-briefs/2026-05-08-night/1786-ab-discuss-bugs.md",
    "docs/dispatch-briefs/2026-05-08-night/1787-1.1-brief-linter.md",
    "docs/dispatch-briefs/2026-05-08-night/1787-1.3-status-verifier.md",
    "docs/dispatch-briefs/2026-05-08-night/1787-1.4-anti-menu-linter.md",
    "docs/dispatch-briefs/2026-05-08-night/1787-1.5-handoff-verifier.md",
    "docs/dispatch-briefs/2026-05-08-night/1789-anti-menu-revise-v2.md",
    "docs/dispatch-briefs/2026-05-08-night/1789-anti-menu-revise.md",
    "docs/dispatch-briefs/2026-05-08-night/1790-mcp-streamable-http.md",
    "docs/dispatch-briefs/2026-05-08-night/1797-d4-revise.md",
    "docs/dispatch-briefs/2026-05-13-1965-jsx-uk-attribute-extraction.md",
    "docs/dispatch-briefs/2026-05-13-immersion-gate-phase-a.md",
    "docs/dispatch-briefs/2026-05-13-immersion-gate-phase-b.md",
    "docs/dispatch-briefs/2026-05-13-ingest-pohribnyi-pronunciation-corpus.md",
    "docs/dispatch-briefs/2026-05-13-pipeline-gate-trio.md",
    "docs/dispatch-briefs/2026-05-13-pr1-learner-state-v7-wiring.md",
    "docs/dispatch-briefs/2026-05-13-pr2-ulp-immersion-model.md",
    "docs/dispatch-briefs/2026-05-13-routing-budget-observability.md",
    "docs/dispatch-briefs/2026-05-13-wiki-obligations-manifest.md",
    "docs/dispatch-briefs/2026-05-13-writer-prompt-tune.md",
    "docs/dispatch-briefs/2026-05-14-assembler-tab3-dedupe-vocab-order.md",
    "docs/dispatch-briefs/2026-05-14-multimedia-resources-search.md",
    "docs/dispatch-briefs/2026-05-14-v7-mdx-assembler-alignment.md",
    "docs/dispatch-briefs/2026-05-14-vesum-norm-and-fixblock-parser.md",
    "docs/dispatch-briefs/2026-05-14-writer-phonetic-ipa-directive.md",
    "docs/dispatch-briefs/2026-05-14-yaml-activities-unjumble.md",
    "docs/dispatch-briefs/2026-05-16-2018-activity-schema-gate-codex.md",
    "docs/dispatch-briefs/2026-05-16-grok-stage-3-writer-plumbing-codex.md",
    "docs/dispatch-briefs/2026-05-16-pr2019-vesum-gate-test-failures-codex.md",
    "docs/dispatch-briefs/2026-05-17-judge-calibration-matrix-codex.md",
    # 2026-05-24 → 2026-05-26 carryover backlog (dispatches already completed).
    "docs/dispatch-briefs/2026-05-24-option-c-plan-reference-match-gate-cursor.md",
    "docs/dispatch-briefs/2026-05-24-pr-2256-fixups-gemini.md",
}

# Grandfathered briefs from the 2026-05-24 → 2026-05-26 carryover backlog.
# Each dispatch was already sent and completed; the briefs are archival.
# New briefs going forward must continue to satisfy the venv-guard rule.
ALLOWLIST_VENV_GUARD = {
    "docs/dispatch-briefs/2026-05-24-f2-f3-batch-cleanup-codex.md",
    "docs/dispatch-briefs/2026-05-25-pr-2266-adjustment-codex.md",
}


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
