#!/usr/bin/env python3
"""Inventory the GitHub Actions runner slots started by pull-request workflows.

The ceiling is intentionally a constant here: changing it is a visible one-line
policy change, while the runbook explains why and how to make that change.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

# #5818/#5907: the measured PR inventory is 29 runner slots (including the
# parallel pytest fastlane and four-way pytest matrix). Two slots are deliberate
# headroom for an incident response without silently oversubscribing runners.
CI_SLOT_CEILING = 31

# CI's planner and its Python job document a four-way pytest topology. This
# constant is also the fail-closed count for that job should its shard matrix
# become a runtime expression that static YAML cannot expand.
PYTEST_SHARD_CEILING = 4

DEFAULT_WORKFLOW_DIR = Path(".github/workflows")


@dataclass(frozen=True)
class WorkflowInventory:
    """One PR-path workflow and its expanded runner-slot count."""

    path: Path
    jobs: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.jobs.values())


def _mapping(value: Any, *, description: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{description} must be a mapping")
    return value


def _trigger_config(workflow: Mapping[str, Any]) -> Any:
    """Return `on`, accounting for YAML 1.1 parsing the word as boolean true."""
    return workflow.get("on", workflow.get(True))


def is_pr_path(workflow: Mapping[str, Any]) -> bool:
    """Whether a workflow runs for PRs or merge-queue candidates."""
    triggers = _trigger_config(workflow)
    if isinstance(triggers, str):
        return triggers in {"pull_request", "merge_group"}
    if isinstance(triggers, Sequence) and not isinstance(triggers, (str, bytes)):
        return bool({"pull_request", "merge_group"} & set(triggers))
    if isinstance(triggers, Mapping):
        return bool({"pull_request", "merge_group"} & set(triggers))
    return False


def _static_values(value: Any, *, location: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{location} must be a non-empty static YAML list")
    if any(isinstance(item, str) and "${{" in item for item in value):
        raise ValueError(f"{location} contains a dynamic GitHub expression")
    return value


def _matches(candidate: Mapping[str, Any], selector: Mapping[str, Any]) -> bool:
    return all(candidate.get(key) == value for key, value in selector.items())


def _matrix_slots(matrix: Any, *, workflow_name: str, job_name: str) -> int:
    """Count a documented static matrix; reject unknown runtime expansion."""
    matrix_map = _mapping(matrix, description=f"{workflow_name}:{job_name} matrix")
    include = matrix_map.get("include", [])
    exclude = matrix_map.get("exclude", [])
    dimensions = {key: value for key, value in matrix_map.items() if key not in {"include", "exclude"}}

    if workflow_name == "ci.yml" and job_name == "python" and isinstance(dimensions.get("shard"), str):
        shard_expression = dimensions["shard"]
        if "${{" not in shard_expression:
            raise ValueError("ci.yml:python shard matrix must be a static list or GitHub expression")
        if set(dimensions) != {"shard"}:
            raise ValueError("ci.yml:python dynamic shard matrix may not have other dimensions")
        return PYTEST_SHARD_CEILING

    values = {
        key: _static_values(value, location=f"{workflow_name}:{job_name} matrix.{key}")
        for key, value in dimensions.items()
    }
    if not values:
        combinations: list[dict[str, Any]] = [{}]
    else:
        combinations = [dict(zip(values, items, strict=True)) for items in itertools.product(*values.values())]

    for selector in exclude:
        selector_map = _mapping(selector, description=f"{workflow_name}:{job_name} matrix.exclude entry")
        combinations = [candidate for candidate in combinations if not _matches(candidate, selector_map)]

    if not isinstance(include, list):
        raise ValueError(f"{workflow_name}:{job_name} matrix.include must be a list")
    original_combinations = combinations
    for entry in include:
        entry_map = _mapping(entry, description=f"{workflow_name}:{job_name} matrix.include entry")
        # GitHub augments every original combination that has no conflicting
        # key. An entry that conflicts with every original combination creates
        # exactly one additional matrix job.
        if not any(
            all(key not in candidate or candidate[key] == value for key, value in entry_map.items())
            for candidate in original_combinations
        ):
            combinations.append(dict(entry_map))

    if workflow_name == "ci.yml" and job_name == "python":
        shards = values.get("shard")
        if shards is None:
            raise ValueError("ci.yml:python must retain its documented shard matrix")
        if len(shards) > PYTEST_SHARD_CEILING:
            raise ValueError(
                f"ci.yml:python has {len(shards)} shards, above PYTEST_SHARD_CEILING={PYTEST_SHARD_CEILING}"
            )
    return len(combinations)


def job_slots(job: Mapping[str, Any], *, workflow_name: str, job_name: str) -> int:
    """Return the number of runner jobs produced by one top-level job."""
    strategy = job.get("strategy")
    if strategy is None:
        return 1
    strategy_map = _mapping(strategy, description=f"{workflow_name}:{job_name} strategy")
    matrix = strategy_map.get("matrix")
    return 1 if matrix is None else _matrix_slots(matrix, workflow_name=workflow_name, job_name=job_name)


def inventory_workflows(workflow_dir: Path = DEFAULT_WORKFLOW_DIR) -> list[WorkflowInventory]:
    """Parse and expand every PR or merge-queue workflow in ``workflow_dir``."""
    inventories: list[WorkflowInventory] = []
    for path in sorted(workflow_dir.glob("*.yml")):
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"{path}: invalid YAML: {exc}") from exc
        workflow = _mapping(loaded or {}, description=str(path))
        if not is_pr_path(workflow):
            continue
        raw_jobs = _mapping(workflow.get("jobs", {}), description=f"{path}: jobs")
        jobs = {
            job_name: job_slots(_mapping(job, description=f"{path}:{job_name}"), workflow_name=path.name, job_name=job_name)
            for job_name, job in raw_jobs.items()
        }
        inventories.append(WorkflowInventory(path=path, jobs=jobs))
    return inventories


def inventory_report(workflow_dir: Path = DEFAULT_WORKFLOW_DIR) -> dict[str, Any]:
    """Return a JSON-serializable report for a repository or test fixture."""
    workflows = inventory_workflows(workflow_dir)
    total = sum(workflow.total for workflow in workflows)
    return {
        "ceiling": CI_SLOT_CEILING,
        "pass": total <= CI_SLOT_CEILING,
        "pytest_shard_ceiling": PYTEST_SHARD_CEILING,
        "total": total,
        "workflows": [
            {"jobs": workflow.jobs, "total": workflow.total, "workflow": str(workflow.path)} for workflow in workflows
        ],
    }


def _print_human(report: Mapping[str, Any]) -> None:
    print("CI runner-slot inventory")
    for workflow in report["workflows"]:
        jobs = ", ".join(f"{name}={count}" for name, count in workflow["jobs"].items())
        print(f"  {workflow['workflow']}: {workflow['total']} ({jobs})")
    status = "PASS" if report["pass"] else "FAIL"
    print(f"{status}: {report['total']} slots / ceiling {report['ceiling']}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-dir", type=Path, default=DEFAULT_WORKFLOW_DIR, help="workflow directory to inventory")
    parser.add_argument("--check", action="store_true", help="fail when the inventory exceeds the configured ceiling")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args(argv)

    try:
        report = inventory_report(args.workflow_dir)
    except (OSError, ValueError) as exc:
        print(f"CI runner-slot inventory failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        _print_human(report)
        print(json.dumps(report, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
