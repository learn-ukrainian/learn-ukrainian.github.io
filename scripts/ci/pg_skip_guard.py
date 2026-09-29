"""Fail a pytest shard whose Postgres tests silently skipped (#9062).

The Postgres-backed tests self-skip when ``LEARN_UKRAINIAN_CP_PG_DSN`` is
unset or unusable, so a broken database start would otherwise turn into a
green run of skips. This reads the shard's JUnit files and fails when

* any test skipped with a message naming the DSN variable, or
* a test file that holds Postgres tests (it carries ``pytest.mark.postgres``
  or the DSN skip message) is in the results but has no passing test.

It prints a per-shard ran/skipped count on stdout for the job summary.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import Counter
from pathlib import Path

from scripts.ci.junit_results import TestResult, parse_junit

DSN_ENV = "LEARN_UKRAINIAN_CP_PG_DSN"
# `{_PG_DSN_ENV}` is the literal f-string form the test files use in their DSN
# skip message; it is matched as text, not evaluated.
_PG_FILE_MARKERS = ("pytest.mark.postgres", f"{DSN_ENV} unset/empty", "{_PG_DSN_ENV} unset/empty")


def postgres_test_files(root: Path) -> set[str]:
    """Tracked test files that hold Postgres-backed tests."""
    listed = subprocess.run(
        ["git", "ls-files", "--", "tests"], cwd=root, capture_output=True, text=True, check=True, timeout=30
    ).stdout.split()
    found = set()
    for name in listed:
        if not name.endswith(".py"):
            continue
        text = (root / name).read_text(encoding="utf-8", errors="replace")
        if any(marker in text for marker in _PG_FILE_MARKERS):
            found.add(name)
    return found


def check(results: list[TestResult], pg_files: set[str]) -> tuple[list[str], Counter[str]]:
    """Return (problems, outcome counts over the Postgres files present)."""
    problems: list[str] = []
    per_file: dict[str, Counter[str]] = {}
    counts: Counter[str] = Counter()
    for result in results:
        file = result.node_id.split("::", 1)[0]
        if result.outcome == "skipped" and DSN_ENV in result.message:
            problems.append(f"{result.node_id} skipped: {result.message.splitlines()[0]}")
        if file in pg_files:
            per_file.setdefault(file, Counter())[result.outcome] += 1
            counts[result.outcome] += 1
    for file, outcomes in sorted(per_file.items()):
        if not outcomes["passed"]:
            problems.append(f"{file}: Postgres tests present but none passed ({dict(outcomes)})")
    return problems, counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("junit", nargs="+", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--title", default="pytest")
    args = parser.parse_args(argv)

    results = parse_junit(args.junit)
    problems, counts = check(results, postgres_test_files(args.root))
    print(
        f"{args.title}: Postgres-file tests passed={counts['passed']} "
        f"skipped={counts['skipped']} failed={counts['failed'] + counts['error']}"
    )
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
