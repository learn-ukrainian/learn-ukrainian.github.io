"""Fail closed unless every required pytest shard executed its exact plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.ci.pytest_shard import ShardPlanError, load_quarantine


def _read_nodeids(path: Path) -> list[str]:
    if not path.is_file():
        raise ShardPlanError(f"missing evidence file: {path}")
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line]


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise ShardPlanError(f"missing evidence file: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ShardPlanError(f"invalid JSON evidence {path}: {error}") from error
    if not isinstance(data, dict):
        raise ShardPlanError(f"JSON evidence {path} must be an object")
    return data


def verify(
    root: Path,
    quarantine_path: Path,
    shard_count: int,
    *,
    require_coverage: bool = False,
) -> list[str]:
    expected_quarantine = {entry["nodeid"] for entry in load_quarantine(quarantine_path)}
    seen_plans: set[str] = set()
    seen_quarantine: set[str] = set()
    summary: list[str] = []

    for shard in range(1, shard_count + 1):
        artifact = root / f"pytest-evidence-{shard}"
        plan = _read_nodeids(artifact / "plan.txt")
        executed = _read_nodeids(artifact / "executed.txt")
        quarantined = _read_nodeids(artifact / "quarantine.txt")
        run = _read_json(artifact / "run.json")
        if run.get("returncode") != 0 or run.get("timed_out") is not False:
            raise ShardPlanError(f"shard {shard} did not finish successfully: {run}")
        if require_coverage:
            coverage = artifact / "coverage"
            if run.get("coverage_enabled") is not True or not coverage.is_file() or coverage.stat().st_size == 0:
                raise ShardPlanError(
                    f"shard {shard} did not produce required main-branch coverage evidence: {coverage}"
                )
        if not plan:
            raise ShardPlanError(f"shard {shard} planned zero runnable tests")
        if len(plan) != len(set(plan)):
            raise ShardPlanError(f"shard {shard} planned duplicate node IDs")
        if len(executed) != len(set(executed)):
            raise ShardPlanError(f"shard {shard} reported duplicate executed node IDs")
        if set(plan) != set(executed):
            missing = sorted(set(plan) - set(executed))
            unexpected = sorted(set(executed) - set(plan))
            raise ShardPlanError(
                f"shard {shard} execution did not match its plan; "
                f"missing={missing[:10]} unexpected={unexpected[:10]}"
            )
        overlap = seen_plans.intersection(plan)
        if overlap:
            raise ShardPlanError(f"node IDs appear in more than one shard plan: {sorted(overlap)[:10]}")
        seen_plans.update(plan)
        seen_quarantine.update(quarantined)
        summary.append(
            f"pytest shard {shard}: {len(plan)} planned/executed nodes; "
            f"{run.get('elapsed_seconds')}s"
        )

    if seen_quarantine != expected_quarantine:
        missing = sorted(expected_quarantine - seen_quarantine)
        unexpected = sorted(seen_quarantine - expected_quarantine)
        raise ShardPlanError(
            "quarantine evidence is incomplete or unexpected; "
            f"missing={missing} unexpected={unexpected}"
        )
    summary.append(f"quarantine: {len(expected_quarantine)} exact node IDs")
    summary.append(f"pytest union: {len(seen_plans)} planned/executed nodes")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--quarantine", required=True, type=Path)
    parser.add_argument("--shard-count", type=int, default=4)
    parser.add_argument(
        "--require-coverage",
        action="store_true",
        help="Fail unless every shard supplied a non-empty coverage data file.",
    )
    args = parser.parse_args()
    try:
        for line in verify(
            args.root,
            args.quarantine,
            args.shard_count,
            require_coverage=args.require_coverage,
        ):
            print(line)
    except ShardPlanError as error:
        print(f"::error title=pytest evidence verification failed::{error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
