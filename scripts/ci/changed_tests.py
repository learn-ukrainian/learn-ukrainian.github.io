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
from pathlib import PurePosixPath


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


def select_test_modules(paths: Iterable[str]) -> list[str]:
    """Return a sorted, duplicate-free direct-test plan from changed paths."""
    return sorted({path for path in paths if is_test_module(path)})


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
    args = parser.parse_args(argv)

    try:
        selected = select_test_modules(changed_files(comparison_range(args.base, args.head)))
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
