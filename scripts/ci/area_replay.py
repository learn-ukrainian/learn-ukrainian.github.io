"""Replay recorded CI runs through the PR-tier test-area skip (#8872 escape proof).

Input is JSON Lines, one run per line: ``{"id", "paths", "failed"}`` plus
optional ``"labels"``. ``paths`` are the run's changed files and ``failed`` the
test files that failed in it. Every run is replayed as a full-tier
pull_request, the only tier that skips areas, so skipping is an upper bound.
An escape is a failed test file the skip would have dropped.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable
from pathlib import Path

from scripts.ci.classify_changes import skipped_areas_for
from scripts.ci.test_areas import filter_paths, load_areas


def replay(records: Iterable[dict], *, repo: Path | None = None) -> dict:
    areas = load_areas()
    summary = {name: {"selected": 0, "skipped": 0} for name in areas}
    escapes: list[dict[str, object]] = []
    runs = 0
    for record in records:
        runs += 1
        skipped = skipped_areas_for(
            record["paths"], event="pull_request", labels=record.get("labels", []), tier={"pytest_mode": "full"}
        )
        for name in areas:
            summary[name]["skipped" if name in skipped else "selected"] += 1
        failed = sorted(set(record.get("failed", [])))
        kept, _ = filter_paths(failed, skipped, repo=repo)
        escapes.extend({"id": record["id"], "test": test, "skipped": skipped} for test in failed if test not in kept)
    return {"runs": runs, "areas": summary, "escapes": escapes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path, help="JSON Lines replay records")
    args = parser.parse_args(argv)
    lines = args.records.read_text(encoding="utf-8").splitlines()
    result = replay(json.loads(line) for line in lines if line.strip())
    print(json.dumps(result, indent=2))
    return 1 if result["escapes"] else 0


if __name__ == "__main__":
    sys.exit(main())
