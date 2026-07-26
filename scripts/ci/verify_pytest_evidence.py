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
    expected_collection: set[str] | None = None
    summary: list[str] = []

    for shard in range(1, shard_count + 1):
        artifact = root / f"pytest-evidence-{shard}"
        collected = _read_nodeids(artifact / "collected.txt")
        plan = _read_nodeids(artifact / "plan.txt")
        executed = _read_nodeids(artifact / "executed.txt")
        quarantined = _read_nodeids(artifact / "quarantine.txt")
        plan_metadata = _read_json(artifact / "plan.json")
        run = _read_json(artifact / "run.json")
        if not collected:
            raise ShardPlanError(f"shard {shard} collected zero tests")
        if len(collected) != len(set(collected)):
            raise ShardPlanError(f"shard {shard} collected duplicate node IDs")
        if expected_collection is None:
            expected_collection = set(collected)
        elif set(collected) != expected_collection:
            missing = sorted(expected_collection - set(collected))
            unexpected = sorted(set(collected) - expected_collection)
            raise ShardPlanError(
                f"shard {shard} collection differs from the other matrix runners; "
                f"missing={missing[:10]} unexpected={unexpected[:10]}"
            )
        expected_metadata = {
            "collected_nodes": len(collected),
            "planned_nodes": len(plan),
            "quarantined_nodes": len(quarantined),
            "shard": shard,
            "shard_count": shard_count,
        }
        for field, expected in expected_metadata.items():
            actual = plan_metadata.get(field)
            if type(actual) is not int or actual != expected:
                raise ShardPlanError(
                    f"shard {shard} plan metadata {field!r} is {actual!r}; "
                    f"expected {expected!r}"
                )
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
        if len(quarantined) != len(set(quarantined)):
            raise ShardPlanError(f"shard {shard} reported duplicate quarantined node IDs")
        planned_nodes = set(plan)
        quarantined_nodes = set(quarantined)
        if not planned_nodes.issubset(collected) or not quarantined_nodes.issubset(collected):
            raise ShardPlanError(f"shard {shard} planned or quarantined nodes absent from its collection")
        if planned_nodes.intersection(quarantined_nodes):
            raise ShardPlanError(f"shard {shard} marks node IDs as both planned and quarantined")
        if planned_nodes != set(executed):
            missing = sorted(planned_nodes - set(executed))
            unexpected = sorted(set(executed) - planned_nodes)
            raise ShardPlanError(
                f"shard {shard} execution did not match its plan; "
                f"missing={missing[:10]} unexpected={unexpected[:10]}"
            )
        overlap = seen_plans.intersection(planned_nodes)
        if overlap:
            raise ShardPlanError(f"node IDs appear in more than one shard plan: {sorted(overlap)[:10]}")
        overlap = seen_quarantine.intersection(quarantined_nodes)
        if overlap:
            raise ShardPlanError(f"node IDs appear in more than one shard quarantine record: {sorted(overlap)[:10]}")
        overlap = seen_plans.intersection(quarantined_nodes) | seen_quarantine.intersection(planned_nodes)
        if overlap:
            raise ShardPlanError(f"node IDs appear as both planned and quarantined: {sorted(overlap)[:10]}")
        seen_plans.update(planned_nodes)
        seen_quarantine.update(quarantined_nodes)
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
    if expected_collection is None:
        raise ShardPlanError("no pytest collection evidence was supplied")
    accounted_for = seen_plans | seen_quarantine
    if accounted_for != expected_collection:
        missing = sorted(expected_collection - accounted_for)
        unexpected = sorted(accounted_for - expected_collection)
        raise ShardPlanError(
            "pytest plans and quarantine do not account for the complete collected suite; "
            f"missing={missing[:10]} unexpected={unexpected[:10]}"
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
