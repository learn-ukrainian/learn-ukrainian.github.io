#!/usr/bin/env python3
"""Select directly changed pytest modules for CI's advisory fast lane.

The required pytest matrix deliberately does *not* use this helper: selecting
only files touched by a change is an early failure signal, not merge authority.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Iterable, Sequence
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath

REPO_INVARIANTS_MANIFEST = Path(__file__).with_name("fastlane_always_tests.txt")


def comparison_range(base: str, head: str) -> str:
    """Return a deterministic merge-base comparison range for git diff."""
    return base if "..." in base else f"{base}...{head}"


def changed_files(git_range: str, *, cwd: str | None = None) -> list[str]:
    """Return changed added or modified paths, sorted independently of git."""
    result = subprocess.run(
        [
            "git",
            "diff",
            "--no-ext-diff",
            "--no-renames",
            "--name-only",
            "--diff-filter=AM",
            git_range,
        ],
        check=True,
        capture_output=True,
        cwd=cwd,
        text=True,
    )
    return sorted(path for path in result.stdout.splitlines() if path)


def is_test_module(path: str) -> bool:
    """Whether a repository-relative path is a conventional pytest module."""
    candidate = PurePosixPath(path)
    return (
        len(candidate.parts) >= 2
        and candidate.parts[0] == "tests"
        and candidate.suffix == ".py"
        and (candidate.name.startswith("test_") or candidate.name.endswith("_test.py"))
    )


def is_repo_invariant_trigger(path: str) -> bool:
    """Whether a PR-tier change can affect a repo-wide invariant."""
    candidate = PurePosixPath(path)
    return (
        candidate.suffix == ".py"
        or path == "pyproject.toml"
        or fnmatchcase(candidate.name, "requirements*.txt")
        or path == ".github/workflows/ci.yml"
        or path == "scripts/ci/fastlane_always_tests.txt"
        or path.startswith("tests/fixtures/")
    )


def load_repo_invariant_tests() -> list[str]:
    """Read the explicit fastlane manifest in its declared order."""
    return [
        line.strip()
        for line in REPO_INVARIANTS_MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def select_test_modules(
    paths: Iterable[str], *, include_repo_invariants: bool = False
) -> list[str]:
    """Return direct tests, optionally unioned with triggered repo invariants."""
    changed_paths = list(paths)
    selected = sorted({path for path in changed_paths if is_test_module(path)})

    if include_repo_invariants and any(is_repo_invariant_trigger(path) for path in changed_paths):
        selected = sorted(set(selected).union(load_repo_invariant_tests()))

    return selected


def write_plan(path: str, selected: Sequence[str]) -> None:
    """Write the newline-delimited pytest file plan without a trailing fake item."""
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        if selected:
            stream.write("\n".join(selected) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base",
        default="origin/main",
        help="base SHA/ref, or an explicit three-dot range (default: origin/main)",
    )
    parser.add_argument("--head", default="HEAD", help="head SHA/ref when --base is a ref (default: HEAD)")
    parser.add_argument("--output", help="write the newline-delimited selected test-file plan here")
    parser.add_argument(
        "--include-repo-invariants",
        action="store_true",
        help="append the invariant manifest when repository-wide trigger paths changed",
    )
    args = parser.parse_args(argv)

    try:
        selected = select_test_modules(
            changed_files(comparison_range(args.base, args.head)),
            include_repo_invariants=args.include_repo_invariants,
        )
    except subprocess.CalledProcessError as exc:
        print(f"changed-test selection failed: git exited {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1

    if args.output:
        write_plan(args.output, selected)
    else:
        print("\n".join(selected))
    print(f"changed-test fastlane plan: {len(selected)} test module(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
