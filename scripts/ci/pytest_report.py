"""Whole-run checks over every pytest shard's results.

Reads each shard's file list (``pytest-shard-N-files.txt``), JUnit report
(``pytest-shard-N.xml``) and collected ``needs_artifact`` tests
(``pytest-shard-N-needs-artifact.txt``, written by tests/conftest.py before
``-m`` deselects anything) from ``--results`` and fails when

* the shard file lists are not a partition of the tracked test files (a file
  on no shard or on two, or a shard that uploaded no results);
* no test ran;
* the collected ``needs_artifact`` tests are not exactly
  ``registry/artifacts/needs-artifact-expected.txt``;
* the tests skipped for a missing data artifact (``needs_artifact:`` skip
  message) are not exactly that expected set either. In CI no artifact store
  is present, so every marked test must run in the tier and skip with that
  message: a marked test deselected as ``slow``, skipped for another reason,
  or passing fails one of the two comparisons.

On success it writes ``--record`` (the ``ci-tested-tree`` artifact the merge
queue reuses, scripts/ci/reuse_green_run.py): the tested tree and commit,
``tier: full``, the test count, and the event, PR number, run id and attempt
that produced it.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

from scripts.ci.junit_results import parse_junit
from scripts.storage.test_baseline import nodeid_to_junit_id

EXPECTED_ARTIFACT_SKIPS = Path("registry/artifacts/needs-artifact-expected.txt")
ARTIFACT_SKIP_PREFIX = "needs_artifact:"
COLLECTED_SUFFIX = "-needs-artifact.txt"


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


def artifact_problems(collected_ids: set[str], skipped_ids: set[str], expected: set[str]) -> list[str]:
    """Collected marked tests and artifact skips must each be exactly ``expected``."""
    problems = []
    if missing := sorted(expected - collected_ids):
        problems.append("expected needs_artifact tests that were not collected:\n  " + "\n  ".join(missing))
    if unexpected := sorted(collected_ids - expected):
        problems.append("collected needs_artifact tests that are not expected:\n  " + "\n  ".join(unexpected))
    if missing := sorted(expected - skipped_ids):
        problems.append(
            "expected needs_artifact tests that did not skip for a missing artifact "
            "(deselected as slow, skipped for another reason, or run):\n  " + "\n  ".join(missing)
        )
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
    collected_lists = {
        path.name.removesuffix(COLLECTED_SUFFIX): path
        for path in args.results.rglob(f"pytest-shard-*{COLLECTED_SUFFIX}")
    }
    if set(collected_lists) != set(shard_files):
        problems.append(
            f"shards with a file list but no collected needs_artifact list (or the reverse): "
            f"{sorted(shard_files)} vs {sorted(collected_lists)}"
        )
    collected_ids = {
        nodeid_to_junit_id(line.strip())
        for path in collected_lists.values()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    results = parse_junit(reports) if reports else []
    outcomes = Counter(result.outcome for result in results)
    if not results:
        problems.append("no test results")
    skipped_ids = {
        nodeid_to_junit_id(result.node_id)
        for result in results
        if result.outcome == "skipped" and ARTIFACT_SKIP_PREFIX in result.message
    }
    problems += artifact_problems(collected_ids, skipped_ids, read_expected_skips(args.root / EXPECTED_ARTIFACT_SKIPS))

    print(
        f"pytest report: shards={len(shard_files)} files={sum(len(files) for files in shard_files.values())} "
        f"tests={len(results)} passed={outcomes['passed']} skipped={outcomes['skipped']} "
        f"failed={outcomes['failed'] + outcomes['error']} needs_artifact_collected={len(collected_ids)} "
        f"needs_artifact_skips={len(skipped_ids)}"
    )
    for problem in problems:
        print(f"::error::{problem}", file=sys.stderr)
    if problems:
        return 1

    def git(*command: str) -> str:
        return subprocess.run(
            ["git", *command], cwd=args.root, capture_output=True, text=True, check=True, timeout=30
        ).stdout.strip()

    def env_int(name: str) -> int | None:
        return int(os.environ[name]) if os.environ.get(name) else None

    record = {
        "tier": "full",
        "tree": git("rev-parse", "HEAD^{tree}"),
        "sha": git("rev-parse", "HEAD"),
        "tests": len(results),
        "event": os.environ.get("GITHUB_EVENT_NAME"),
        "pr": env_int("PR_NUMBER"),
        "run_id": env_int("GITHUB_RUN_ID"),
        "run_attempt": env_int("GITHUB_RUN_ATTEMPT"),
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    args.record.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    print(f"tested-tree record: {record}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
