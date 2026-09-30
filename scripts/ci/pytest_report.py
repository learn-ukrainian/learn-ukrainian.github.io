"""Whole-run checks over every pytest shard's results.

Reads each shard's file list (``pytest-shard-N-files.txt``) and JUnit report
(``pytest-shard-N.xml``) from ``--results`` and fails when

* the shard file lists are not a partition of the tracked test files (a file
  on no shard or on two, or a shard that uploaded no results);
* no test ran;
* the tests skipped for a missing data artifact (``needs_artifact:`` skip
  message) are not exactly ``registry/artifacts/needs-artifact-expected.txt``
  (in CI no artifact store is present, so every marked test in the tier
  either skips with that message or fails its shard).

On success it writes ``--record`` (the ``ci-tested-tree`` artifact the merge
queue reuses): the tested tree, commit and ``tier: full``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from scripts.ci.junit_results import parse_junit
from scripts.storage.test_baseline import nodeid_to_junit_id

EXPECTED_ARTIFACT_SKIPS = Path("registry/artifacts/needs-artifact-expected.txt")
ARTIFACT_SKIP_PREFIX = "needs_artifact:"


def tracked_test_files(root: Path) -> set[str]:
    listed = subprocess.run(
        ["git", "ls-files", "--", "tests"], cwd=root, capture_output=True, text=True, check=True, timeout=30
    ).stdout.split()
    return {name for name in listed if name.endswith(".py") and Path(name).name.startswith("test_")}


def partition_problems(shard_files: dict[str, list[str]], expected: set[str]) -> list[str]:
    problems = []
    owners: dict[str, list[str]] = {}
    for shard, files in sorted(shard_files.items()):
        for name in files:
            owners.setdefault(name, []).append(shard)
    for name, shards in sorted(owners.items()):
        if len(shards) > 1:
            problems.append(f"{name} is on more than one shard: {', '.join(shards)}")
    missing = sorted(expected - owners.keys())
    unknown = sorted(owners.keys() - expected)
    if missing:
        problems.append(f"{len(missing)} tracked test files ran on no shard, e.g. {missing[:5]}")
    if unknown:
        problems.append(f"{len(unknown)} shard files are not tracked test files, e.g. {unknown[:5]}")
    return problems


def artifact_skip_problems(skipped_ids: set[str], expected: set[str]) -> list[str]:
    problems = []
    if missing := sorted(expected - skipped_ids):
        problems.append("expected needs_artifact skips that did not skip:\n  " + "\n  ".join(missing))
    if unexpected := sorted(skipped_ids - expected):
        problems.append("unexpected needs_artifact skips:\n  " + "\n  ".join(unexpected))
    if problems:
        problems.append(f"the expected set is {EXPECTED_ARTIFACT_SKIPS}; update it with the test that changed")
    return problems


def read_expected_skips(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--results", type=Path, required=True, help="directory holding every shard's artifact")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--record", type=Path, required=True, help="where to write the tested-tree record")
    args = parser.parse_args(argv)

    lists = sorted(args.results.rglob("pytest-shard-*-files.txt"))
    shard_files = {path.name.removesuffix("-files.txt"): path.read_text(encoding="utf-8").split() for path in lists}
    problems = partition_problems(shard_files, tracked_test_files(args.root))
    reports = sorted(args.results.rglob("pytest-shard-*.xml"))
    if {path.stem for path in reports} != set(shard_files):
        problems.append(
            f"shards with a file list but no JUnit report (or the reverse): {sorted(shard_files)} vs {[p.stem for p in reports]}"
        )

    results = parse_junit(reports) if reports else []
    outcomes = Counter(result.outcome for result in results)
    if not results:
        problems.append("no test results")
    skipped_ids = {
        nodeid_to_junit_id(result.node_id)
        for result in results
        if result.outcome == "skipped" and ARTIFACT_SKIP_PREFIX in result.message
    }
    problems += artifact_skip_problems(skipped_ids, read_expected_skips(args.root / EXPECTED_ARTIFACT_SKIPS))

    print(
        f"pytest report: shards={len(shard_files)} files={sum(len(files) for files in shard_files.values())} "
        f"tests={len(results)} passed={outcomes['passed']} skipped={outcomes['skipped']} "
        f"failed={outcomes['failed'] + outcomes['error']} needs_artifact_skips={len(skipped_ids)}"
    )
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if problems:
        return 1

    def git(*command: str) -> str:
        return subprocess.run(
            ["git", *command], cwd=args.root, capture_output=True, text=True, check=True, timeout=30
        ).stdout.strip()

    record = {
        "tier": "full",
        "tree": git("rev-parse", "HEAD^{tree}"),
        "sha": git("rev-parse", "HEAD"),
        "tests": len(results),
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    print(f"tested-tree record: {record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
