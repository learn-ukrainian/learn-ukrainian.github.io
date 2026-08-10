#!/usr/bin/env python3
"""Plan and verify duration-balanced pytest shards for the CI Gate.

The planner collects the selected suite exactly once, groups every selected
node ID by test file, then uses deterministic longest-processing-time (LPT)
assignment.  Workers execute only the planner-produced node-ID list; CI Gate
reconstructs and verifies the complete partition from their JUnit artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
import xml.etree.ElementTree as element_tree
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

SHARD_COUNT = 4
PLAYGROUND_PERF_TEST = "tests/test_playground_api_stability.py::test_playground_primary_endpoints_keep_health_fast"
SERIAL_TESTS = (PLAYGROUND_PERF_TEST,)
COMMON_ARGS = ("tests/", f"--deselect={PLAYGROUND_PERF_TEST}")
_DURATION_LINE = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+(?:call|setup|teardown)\s+(?P<nodeid>\S+)")
_DATASET_VERSION = 1
_P95_HISTORY_LIMIT = 40


def _digest(nodeids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(nodeids)).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class _NodeidCollector:
    def __init__(self) -> None:
        self.nodeids: list[str] = []

    def pytest_collection_finish(self, session: Any) -> None:
        self.nodeids = [item.nodeid for item in session.items]


def collect_nodeids(args: Sequence[str] = COMMON_ARGS) -> list[str]:
    """Collect the exact selection executed by the matrix workers."""
    import pytest

    collector = _NodeidCollector()
    exit_code = pytest.main([*args, "--collect-only", "-q"], plugins=[collector])
    if exit_code != pytest.ExitCode.OK:
        raise RuntimeError(f"pytest collection failed with exit code {exit_code}")
    if not collector.nodeids:
        raise RuntimeError("pytest collection selected zero tests")
    if len(set(collector.nodeids)) != len(collector.nodeids):
        raise RuntimeError("pytest collection returned duplicate node IDs")
    return collector.nodeids


def load_durations(path: Path | None) -> dict[str, float]:
    """Load only valid node timings from a main-only duration dataset."""
    if path is None or not path.exists():
        return {}
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise ValueError(f"duration file {path} must be a JSON object")
    source = raw.get("node_durations", raw)
    if not isinstance(source, dict):
        raise ValueError(f"duration file {path} has invalid node_durations")
    return {
        nodeid: float(duration)
        for nodeid, duration in source.items()
        if isinstance(nodeid, str) and isinstance(duration, (int, float)) and duration > 0
    }


def _file_nodeids(nodeids: Sequence[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for nodeid in nodeids:
        groups.setdefault(nodeid.split("::", 1)[0], []).append(nodeid)
    return groups


def _file_weights(nodeids: Sequence[str], durations: dict[str, float]) -> dict[str, float]:
    """Return file weights; files without history use the median known file weight."""
    groups = _file_nodeids(nodeids)
    known = {
        filename: sum(durations[nodeid] for nodeid in members if nodeid in durations)
        for filename, members in groups.items()
    }
    observed = sorted(weight for weight in known.values() if weight > 0)
    fallback = statistics.median(observed) if observed else 1.0
    return {filename: weight if weight > 0 else fallback for filename, weight in known.items()}


def assign_shards(nodeids: Sequence[str], shard_count: int, durations: dict[str, float]) -> list[list[str]]:
    """Use deterministic file-grouped LPT scheduling; assign each node ID once."""
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    if len(set(nodeids)) != len(nodeids):
        raise ValueError("nodeids must be unique before sharding")
    groups = _file_nodeids(nodeids)
    weights = _file_weights(nodeids, durations)
    weighted_groups = sorted(groups, key=lambda filename: (-weights[filename], filename))
    shard_groups: list[list[str]] = [[] for _ in range(shard_count)]
    totals = [0.0] * shard_count
    for filename in weighted_groups:
        shard_index = min(range(shard_count), key=lambda index: (totals[index], index))
        shard_groups[shard_index].extend(groups[filename])
        totals[shard_index] += weights[filename]
    return shard_groups


def write_plans(*, durations_path: Path | None, output_dir: Path, shard_count: int = SHARD_COUNT) -> None:
    """Collect once and write every matrix-worker plan from one duration dataset."""
    nodeids = collect_nodeids()
    durations = load_durations(durations_path)
    shards = assign_shards(nodeids, shard_count, durations)
    if any(not assigned for assigned in shards):
        empty = [index + 1 for index, assigned in enumerate(shards) if not assigned]
        raise RuntimeError(f"planner produced empty shard(s): {empty}")
    output_dir.mkdir(parents=True, exist_ok=True)
    weights = _file_weights(nodeids, durations)
    for shard_id, assigned in enumerate(shards, start=1):
        shard_dir = output_dir / f"pytest-shard-{shard_id}"
        shard_dir.mkdir(parents=True, exist_ok=True)
        (shard_dir / "test-nodeids.txt").write_text("\n".join(assigned) + "\n", encoding="utf-8")
        assigned_files = sorted({nodeid.split("::", 1)[0] for nodeid in assigned})
        _write_json(
            shard_dir / "plan.json",
            {
                "assigned_digest": _digest(assigned),
                "assigned_nodeids": assigned,
                "collected_count": len(nodeids),
                "collected_digest": _digest(nodeids),
                "estimated_seconds": sum(weights[filename] for filename in assigned_files),
                "grouping": "file",
                "partition_mode": "lpt-durations",
                "serial_nodeids": list(SERIAL_TESTS) if shard_id == 1 else [],
                "shard_count": shard_count,
                "shard_id": shard_id,
            },
        )


def _junit_count(path: Path) -> int:
    root = element_tree.parse(path).getroot()
    if root.tag == "testsuite":
        return int(root.attrib.get("tests", "0"))
    return sum(int(suite.attrib.get("tests", "0")) for suite in root.iter("testsuite"))


def verify_artifacts(artifact_dir: Path, shard_count: int) -> None:
    """Fail closed unless plan, execution count, and partition all agree."""
    plans: list[dict[str, Any]] = []
    for shard_id in range(1, shard_count + 1):
        shard_dir = artifact_dir / f"pytest-shard-{shard_id}"
        plan_path = shard_dir / "plan.json"
        main_junit = shard_dir / "main-junit.xml"
        if not plan_path.exists() or not main_junit.exists():
            raise RuntimeError(f"missing plan or main JUnit artifact for shard {shard_id}")
        plan = _read_json(plan_path)
        if plan.get("shard_id") != shard_id or plan.get("shard_count") != shard_count:
            raise RuntimeError(f"invalid shard identity in {plan_path}")
        assigned = plan.get("assigned_nodeids")
        if not isinstance(assigned, list) or not all(isinstance(nodeid, str) for nodeid in assigned):
            raise RuntimeError(f"invalid assigned node IDs in {plan_path}")
        if _digest(assigned) != plan.get("assigned_digest"):
            raise RuntimeError(f"assigned node ID digest mismatch in {plan_path}")
        if plan.get("partition_mode") != "lpt-durations" or plan.get("grouping") != "file":
            raise RuntimeError(f"invalid planner mode in {plan_path}")
        if _junit_count(main_junit) != len(assigned):
            raise RuntimeError(f"main JUnit count does not match plan for shard {shard_id}")
        serial = plan.get("serial_nodeids")
        if shard_id == 1:
            playground_junit = shard_dir / "playground-junit.xml"
            if serial != list(SERIAL_TESTS) or not playground_junit.exists():
                raise RuntimeError("shard 1 must execute the documented serial tests")
            if _junit_count(playground_junit) != len(SERIAL_TESTS):
                raise RuntimeError("serial JUnit count does not match the documented serial tests")
        elif serial or (shard_dir / "playground-junit.xml").exists():
            raise RuntimeError(f"only shard 1 may contain serial tests (found shard {shard_id})")
        plans.append(plan)

    counts = {plan["collected_count"] for plan in plans}
    digests = {plan["collected_digest"] for plan in plans}
    if len(counts) != 1 or len(digests) != 1:
        raise RuntimeError("shards disagree about the collected selection")
    assigned = [nodeid for plan in plans for nodeid in plan["assigned_nodeids"]]
    if len(assigned) != len(set(assigned)):
        raise RuntimeError("a collected test was assigned to more than one shard")
    if set(assigned).intersection(SERIAL_TESTS):
        raise RuntimeError("a serial test was also assigned to a parallel shard")
    if len(assigned) != counts.pop() or _digest(assigned) != digests.pop():
        raise RuntimeError("shards do not form a complete partition of the collected selection")


def parse_durations(log_paths: Sequence[Path]) -> dict[str, float]:
    durations: dict[str, float] = {}
    for path in log_paths:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = _DURATION_LINE.match(line)
            if match:
                nodeid = match.group("nodeid")
                durations[nodeid] = durations.get(nodeid, 0.0) + float(match.group("seconds"))
    if not durations:
        raise RuntimeError("no pytest duration lines found in shard logs")
    return durations


def _nearest_rank_p95(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("cannot calculate p95 of an empty history")
    ordered = sorted(values)
    return ordered[max(0, (95 * len(ordered) + 99) // 100 - 1)]


def publish_durations(*, log_paths: Sequence[Path], previous: Path | None, output: Path, summary: Path) -> None:
    """Publish successful-main timings and quote rolling slowest-shard p95."""
    node_durations = parse_durations(log_paths)
    prior: dict[str, Any] = _read_json(previous) if previous and previous.exists() else {}
    history = prior.get("slowest_shard_seconds", []) if isinstance(prior, dict) else []
    if not isinstance(history, list) or not all(isinstance(value, (int, float)) and value > 0 for value in history):
        raise ValueError("previous duration dataset has invalid slowest_shard_seconds")
    shard_totals = [sum(parse_durations([path]).values()) for path in log_paths]
    slowest = max(shard_totals)
    history = [*map(float, history), slowest][-_P95_HISTORY_LIMIT:]
    p95 = _nearest_rank_p95(history)
    _write_json(
        output,
        {
            "node_durations": node_durations,
            "schema_version": _DATASET_VERSION,
            "slowest_shard_seconds": history,
        },
    )
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        "## Pytest shard duration record\n\n"
        f"Successful main run shard test durations: {', '.join(f'{total:.2f}s' for total in shard_totals)}.\n\n"
        f"Slowest-shard p95: **{p95:.2f}s** across {len(history)} successful main run(s).\n",
        encoding="utf-8",
    )


def run_nodeids(nodeids_path: Path, pytest_args: Sequence[str]) -> int:
    """Invoke pytest with a planner-produced node-ID list (not shell @file)."""
    import pytest

    nodeids = [line.strip() for line in nodeids_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not nodeids:
        raise RuntimeError(f"node-id file {nodeids_path} is empty")
    if len(set(nodeids)) != len(nodeids):
        raise RuntimeError(f"node-id file {nodeids_path} contains duplicates")
    args = list(pytest_args)
    if args and args[0] == "--":
        args = args[1:]
    return int(pytest.main([*args, *nodeids]))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--durations", type=Path)
    plan.add_argument("--output-dir", type=Path, required=True)
    plan.add_argument("--shard-count", type=int, default=SHARD_COUNT)
    verify = commands.add_parser("verify-artifacts")
    verify.add_argument("--artifact-dir", type=Path, required=True)
    verify.add_argument("--shard-count", type=int, default=SHARD_COUNT)
    publish = commands.add_parser("publish-durations")
    publish.add_argument("--log", type=Path, action="append", required=True)
    publish.add_argument("--previous", type=Path)
    publish.add_argument("--output", type=Path, required=True)
    publish.add_argument("--summary", type=Path, required=True)
    run = commands.add_parser("run")
    run.add_argument("--nodeids", type=Path, required=True)
    run.add_argument("pytest_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            write_plans(durations_path=args.durations, output_dir=args.output_dir, shard_count=args.shard_count)
        elif args.command == "verify-artifacts":
            verify_artifacts(args.artifact_dir, args.shard_count)
        elif args.command == "publish-durations":
            publish_durations(log_paths=args.log, previous=args.previous, output=args.output, summary=args.summary)
        elif args.command == "run":
            return run_nodeids(args.nodeids, args.pytest_args)
    except (OSError, RuntimeError, ValueError, element_tree.ParseError) as error:
        print(f"pytest shard error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
