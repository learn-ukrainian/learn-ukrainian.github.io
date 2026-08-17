#!/usr/bin/env python3
"""Lint test files for hard-coded stale-pinned epic/stream assertions (#6968).

Tests asserting on live, derivable workflow state must derive stream IDs from
scripts/config/issue_streams.yaml (or corresponding runtime registries) rather
than hard-coding literal 'epic:<int>' values or bare stream IDs in assertions.

Hard-coding derivable state stales tests across epic succession and turns
unrelated provider or schema transitions into red CI gates.

Designated exceptions:
1. Synthetic/test epic IDs: epic:9999, epic:999999, epic:1001, epic:1002,
   epic:2001, epic:3001, epic:123, epic:4700, epic:4220, epic:0, or prefixed
   with fixture/mock/synthetic.
2. Negative assertions verifying obsolete/old epics are NOT emitted:
   e.g. `assert "epic:4707" not in text`.
3. Designated fixture patterns / local parameter tests annotated with
   `# noqa: epic-id`, `# allow-hardcoded-epic`, `# fixture`, or `# designated-fixture`.
4. Legacy taxonomy lookup tests covered by the explicit allowlist below.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Regex matching epic ID stream literals
_EPIC_ID_RE = re.compile(r"\bepic:\d+\b", re.IGNORECASE)

# Synthetic IDs explicitly reserved for tests/fixtures
_SYNTHETIC_EPIC_IDS: frozenset[str] = frozenset(
    {
        "epic:0",
        "epic:123",
        "epic:1001",
        "epic:1002",
        "epic:2001",
        "epic:3001",
        "epic:4220",
        "epic:4700",
        "epic:9999",
        "epic:999999",
    }
)

# Inline directive comments that allow hard-coded literals for designated fixtures
_ALLOW_DIRECTIVES: tuple[str, ...] = (
    "# noqa: epic-id",
    "# allow-hardcoded-epic",
    "# fixture",
    "# test-fixture",
    "# designated-fixture",
)

# Scoped allowlist for legacy tests exercising static lookup maps / historical records
_LEGACY_ALLOWLIST: frozenset[str] = frozenset(
    {
        "tests/fleet_comms/test_cold_start_board.py",
        "tests/orchestration/test_thread_restart_e2e.py",
        "tests/test_codex_lane_canary.py",
        "tests/test_fleet_taxonomy_aliases.py",
        "tests/test_fleet_taxonomy_slot_addressing.py",
        "tests/test_grok_lane_session_canary.py",
        "tests/test_kimi_lane_bootstrap.py",
        "tests/test_lint_test_assertions.py",
        "tests/test_session_streams_api.py",
        "tests/test_session_streams_dual_write_status.py",
        "tests/test_session_supervisor_shell.py",
    }
)


@dataclass(frozen=True)
class AssertionViolation:
    """One prohibited hard-coded epic/stream assertion."""

    path: str
    line_number: int
    snippet: str
    epic_id: str
    reason: str


def _is_negative_assertion(node: ast.Assert, source_segment: str) -> bool:
    """Return True if this assertion verifies absence (e.g. `not in` or `!=`)."""
    if " not in " in source_segment or " != " in source_segment:
        return True
    test = node.test
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return True
    if isinstance(test, ast.Compare):
        for op in test.ops:
            if isinstance(op, (ast.NotIn, ast.IsNot, ast.NotEq)):
                return True
    return False


def _has_allow_directive(lines: list[str], lineno: int) -> bool:
    """Check if the assertion line or previous line contains an allow directive."""
    for idx in (lineno - 1, lineno - 2):
        if 0 <= idx < len(lines):
            line = lines[idx]
            if any(directive in line for directive in _ALLOW_DIRECTIVES):
                return True
    return False


def scan_file(file_path: Path, repo_root: Path | None = None) -> list[AssertionViolation]:
    """Scan a single Python test file for forbidden hard-coded epic assertions."""
    root = (repo_root or REPO_ROOT).resolve()
    rel_path = file_path.resolve().relative_to(root).as_posix()

    if rel_path in _LEGACY_ALLOWLIST:
        return []

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return []

    lines = content.splitlines()
    violations: list[AssertionViolation] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue

        lineno = node.lineno
        if _has_allow_directive(lines, lineno):
            continue

        source_segment = (ast.get_source_segment(content, node) or "").strip()
        if _is_negative_assertion(node, source_segment):
            continue

        for child in ast.walk(node):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                for match in _EPIC_ID_RE.finditer(child.value):
                    epic_id = match.group(0)
                    if epic_id.lower() in _SYNTHETIC_EPIC_IDS:
                        continue
                    violations.append(
                        AssertionViolation(
                            path=rel_path,
                            line_number=lineno,
                            snippet=source_segment,
                            epic_id=epic_id,
                            reason=(
                                f"hard-coded stream literal '{epic_id}' in assertion; "
                                "derive from issue_streams.yaml or use a designated fixture pattern "
                                "(e.g. # noqa: epic-id or synthetic epic ID)"
                            ),
                        )
                    )

    return violations


def find_stale_pinned_assertions(
    repo_root: Path | None = None,
    paths: Sequence[Path] | None = None,
) -> list[AssertionViolation]:
    """Scan test files under repo_root or explicit paths for stale pinned assertions."""
    root = (repo_root or REPO_ROOT).resolve()
    if paths:
        target_files = [p.resolve() for p in paths if p.is_file() and p.suffix == ".py"]
    else:
        tests_dir = root / "tests"
        if not tests_dir.is_dir():
            return []
        target_files = sorted(tests_dir.rglob("*.py"))

    findings: list[AssertionViolation] = []
    for file_path in target_files:
        findings.extend(scan_file(file_path, repo_root=root))

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional specific test files or directories to check",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root directory",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths: list[Path] | None = None
    if args.paths:
        paths = []
        for p in args.paths:
            if p.is_dir():
                paths.extend(sorted(p.rglob("*.py")))
            elif p.is_file():
                paths.append(p)

    findings = find_stale_pinned_assertions(repo_root=args.root, paths=paths)

    if not findings:
        print("OK: no forbidden hard-coded epic/stream assertions found in tests")
        return 0

    print("Forbidden hard-coded epic assertions found in tests:", file=sys.stderr)
    for v in findings:
        print(f"  {v.path}:{v.line_number}: [{v.epic_id}] {v.snippet}", file=sys.stderr)
        print(f"    ↳ {v.reason}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
