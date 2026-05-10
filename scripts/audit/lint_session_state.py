#!/usr/bin/env python3
"""Lint session handoffs for environmental file references that do not exist."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_STATE_DIR = PROJECT_ROOT / "docs" / "session-state"
ALLOWLIST_FILE = Path(__file__).with_name("known_user_paths.yaml")

PATH_PATTERN = re.compile(r"(\B~/\.[\w./_-]+\b|\B(?<!\.)\.env(?:\.[\w-]+)?\b)")
FENCE_PATTERN = re.compile(r"^\s*(```|~~~)(.*)$")


@dataclass(frozen=True)
class Violation:
    path: Path
    line_number: int
    reference: str


def load_allowlist(path: Path | None = None) -> set[str]:
    path = path or ALLOWLIST_FILE
    if not path.exists():
        return set()
    data = yaml.safe_load(path.read_text("utf-8")) or {}
    return {str(item) for item in data.get("paths", [])}


def session_state_files() -> list[Path]:
    return sorted(SESSION_STATE_DIR.glob("*.md"))


def project_scoped_roots(project_root: Path) -> list[Path]:
    roots = [project_root]
    git_marker = project_root / ".git"
    if not git_marker.is_file():
        return roots

    prefix = "gitdir:"
    gitdir_line = git_marker.read_text("utf-8").strip()
    if not gitdir_line.startswith(prefix):
        return roots

    gitdir = Path(gitdir_line[len(prefix) :].strip())
    if not gitdir.is_absolute():
        gitdir = project_root / gitdir

    for parent in (gitdir, *gitdir.parents):
        if parent.name == ".git":
            primary_checkout = parent.parent
            if primary_checkout not in roots:
                roots.append(primary_checkout)
            break
    return roots


def reference_exists(reference: str, *, project_root: Path, home: Path) -> bool:
    if reference.startswith("~/"):
        return (home / reference[2:]).exists()
    return any((root / reference).exists() for root in project_scoped_roots(project_root))


def illustrative_fence_lines(lines: list[str]) -> set[int]:
    skip_lines: set[int] = set()
    open_fence: tuple[str, int, bool] | None = None
    block_body: list[str] = []

    for index, line in enumerate(lines, start=1):
        match = FENCE_PATTERN.match(line)
        if match and open_fence is None:
            marker, info = match.groups()
            illustrative = "example" in info.lower() or "illustrative" in info.lower()
            open_fence = (marker, index, illustrative)
            block_body = []
            continue

        if match and open_fence is not None and match.group(1) == open_fence[0]:
            _, start_line, illustrative = open_fence
            body_marks_example = any(
                body_line.strip().lower().startswith(("# example", "# illustrative"))
                for body_line in block_body
            )
            if illustrative or body_marks_example:
                skip_lines.update(range(start_line, index + 1))
            open_fence = None
            block_body = []
            continue

        if open_fence is not None:
            block_body.append(line)

    return skip_lines


def lint_file(
    path: Path,
    *,
    allowlist: set[str],
    project_root: Path | None = None,
    home: Path | None = None,
) -> list[Violation]:
    project_root = project_root or PROJECT_ROOT
    home = home or Path.home()
    lines = path.read_text("utf-8").splitlines()
    skip_lines = illustrative_fence_lines(lines)
    violations: list[Violation] = []

    for line_number, line in enumerate(lines, start=1):
        if line_number in skip_lines:
            continue
        for match in PATH_PATTERN.finditer(line):
            reference = match.group(1)
            if reference in allowlist:
                continue
            if not reference_exists(reference, project_root=project_root, home=home):
                violations.append(Violation(path, line_number, reference))

    return violations


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint docs/session-state handoffs for referenced env/config files "
            "that do not exist.\n"
            "Use before committing handoff docs; do not use for general markdown linting."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/audit/lint_session_state.py --all\n"
            "  .venv/bin/python scripts/audit/lint_session_state.py "
            "--file docs/session-state/current.md\n\n"
            "Outputs: Prints path:line diagnostics to stdout. Writes no files.\n\n"
            "Exit codes: 0 clean, 1 missing referenced env/config files, 2 CLI usage error.\n\n"
            "Related: scripts/audit/known_user_paths.yaml, issue #1787."
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--file",
        type=Path,
        help="Session-state markdown file to lint, e.g. docs/session-state/current.md",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Lint every docs/session-state/*.md file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    paths = session_state_files() if args.all else [args.file]
    allowlist = load_allowlist()

    violations: list[Violation] = []
    for path in paths:
        if not path.exists():
            print(f"{path}: file does not exist", file=sys.stderr)
            return 1
        violations.extend(lint_file(path, allowlist=allowlist))

    for violation in violations:
        print(
            f"{violation.path}:{violation.line_number}: referenced env file "
            f"'{violation.reference}' does not exist"
        )
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
