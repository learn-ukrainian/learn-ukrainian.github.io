#!/usr/bin/env python3
"""Plan and verify deterministic pytest shards for the required CI suite.

The planner collects the same hermetic selection that CI executes, then applies
deterministic longest-processing-time scheduling.  A restored duration cache
supplies the processing-time estimates; unknown tests receive the median known
duration (or one second for the first cache-less run).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as element_tree
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

SHARD_COUNT = 4
PLAYGROUND_PERF_TEST = "tests/test_playground_api_stability.py::test_playground_primary_endpoints_keep_health_fast"
SERIAL_TESTS = (
    "tests/test_api_helpers.py::TestCacheFunctions::test_cache_invalidate_by_prefix",
    "tests/test_api_helpers.py::TestCacheFunctions::test_cache_invalidate_default_clears_all",
    PLAYGROUND_PERF_TEST,
)
COMMON_ARGS = (
    "tests/",
    "-v",
    "--tb=short",
    "-k",
    "not slow and not website",
    "--ignore=tests/test_rag.py",
    "--ignore=tests/test_a1_review_scores.py",
    "--ignore=tests/test_agent_runtime.py",
    "--ignore=tests/test_channels_registry.py",
    "--ignore=tests/test_convergence_loop.py",
    "--ignore=tests/test_morphological_validator.py",
    "--ignore=tests/test_plan_hash.py",
    "--ignore=tests/test_scrape_diasporiana.py",
    "--ignore=tests/test_v6_plan_hash_drift.py",
    "--ignore=tests/test_vocab_gen.py",
    "--ignore=tests/test_wiki_channels.py",
    "--ignore=tests/test_wiki_enrichment.py",
    "--ignore=tests/wiki/test_grade_filter.py",
    "--ignore=tests/wiki/test_mlx_fault_injection.py",
    "--ignore=tests/wiki/test_t1_t2_pipeline.py",
    f"--deselect={SERIAL_TESTS[0]}",
    f"--deselect={SERIAL_TESTS[1]}",
    f"--deselect={PLAYGROUND_PERF_TEST}",
)
_DURATION_LINE = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+(?:call|setup|teardown)\s+(?P<nodeid>\S+)")


def _digest(nodeids: Iterable[str]) -> str:
    payload = "\n".join(sorted(nodeids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
    """Collect the exact selection used by the sharded main pytest invocation."""
    # Lazy import: verify-artifacts / parse-durations run in bare venvs without pytest.
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
    if path is None or not path.exists():
        return {}
    raw = _read_json(path)
    if not isinstance(raw, dict):
        raise ValueError(f"duration file {path} must be a JSON object")
    durations: dict[str, float] = {}
    for nodeid, duration in raw.items():
        if isinstance(nodeid, str) and isinstance(duration, (int, float)) and duration > 0:
            durations[nodeid] = float(duration)
    return durations


def _default_weight(nodeids: Sequence[str], durations: dict[str, float]) -> float:
    known = sorted(durations[nodeid] for nodeid in nodeids if nodeid in durations)
    if not known:
        return 1.0
    return known[len(known) // 2]


def assign_shards(nodeids: Sequence[str], shard_count: int, durations: dict[str, float]) -> list[list[str]]:
    """Use deterministic LPT scheduling; every input node ID is assigned once."""
    if shard_count < 1:
        raise ValueError("shard_count must be positive")
    if len(set(nodeids)) != len(nodeids):
        raise ValueError("nodeids must be unique before sharding")
    fallback = _default_weight(nodeids, durations)
    weighted = sorted(((durations.get(nodeid, fallback), nodeid) for nodeid in nodeids), key=lambda item: (-item[0], item[1]))
    shards: list[list[str]] = [[] for _ in range(shard_count)]
    totals = [0.0] * shard_count
    for weight, nodeid in weighted:
        index = min(range(shard_count), key=lambda candidate: (totals[candidate], candidate))
        shards[index].append(nodeid)
        totals[index] += weight
    return shards


def write_plan(*, shard_id: int, shard_count: int, durations_path: Path | None, output: Path, args_output: Path) -> None:
    if not 1 <= shard_id <= shard_count:
        raise ValueError(f"shard_id must be between 1 and {shard_count}")
    nodeids = collect_nodeids()
    durations = load_durations(durations_path)
    shards = assign_shards(nodeids, shard_count, durations)
    assigned = shards[shard_id - 1]
    args_output.parent.mkdir(parents=True, exist_ok=True)
    args_output.write_text("\n".join(assigned) + "\n", encoding="utf-8")
    _write_json(
        output,
        {
            "assigned_nodeids": assigned,
            "assigned_digest": _digest(assigned),
            "collected_count": len(nodeids),
            "collected_digest": _digest(nodeids),
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
        if _junit_count(main_junit) != len(assigned):
            raise RuntimeError(f"main JUnit count does not match plan for shard {shard_id}")
        serial = plan.get("serial_nodeids")
        if not isinstance(serial, list):
            raise RuntimeError(f"invalid serial node IDs in {plan_path}")
        cache_junit = shard_dir / "cache-junit.xml"
        playground_junit = shard_dir / "playground-junit.xml"
        if shard_id == 1:
            if serial != list(SERIAL_TESTS) or not cache_junit.exists() or not playground_junit.exists():
                raise RuntimeError("shard 1 must execute the documented serial tests")
            if _junit_count(cache_junit) + _junit_count(playground_junit) != len(SERIAL_TESTS):
                raise RuntimeError("serial JUnit count does not match the documented serial tests")
        elif serial or cache_junit.exists() or playground_junit.exists():
            raise RuntimeError(f"only shard 1 may contain serial tests (found shard {shard_id})")
        plans.append(plan)

    collected_counts = {plan["collected_count"] for plan in plans}
    collected_digests = {plan["collected_digest"] for plan in plans}
    if len(collected_counts) != 1 or len(collected_digests) != 1:
        raise RuntimeError("shards disagree about the collected selection")
    assigned = [nodeid for plan in plans for nodeid in plan["assigned_nodeids"]]
    if len(assigned) != len(set(assigned)):
        raise RuntimeError("a collected test was assigned to more than one shard")
    if set(assigned).intersection(SERIAL_TESTS):
        raise RuntimeError("a serial test was also assigned to a parallel shard")
    if len(assigned) != collected_counts.pop() or _digest(assigned) != collected_digests.pop():
        raise RuntimeError("shards do not form a complete partition of the collected selection")


def parse_durations(log_paths: Sequence[Path], output: Path) -> None:
    durations: dict[str, float] = {}
    for path in log_paths:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = _DURATION_LINE.match(line)
            if match:
                nodeid = match.group("nodeid")
                durations[nodeid] = durations.get(nodeid, 0.0) + float(match.group("seconds"))
    if not durations:
        raise RuntimeError("no pytest duration lines found in shard logs")
    _write_json(output, durations)


def run_nodeids(nodeids_path: Path, pytest_args: Sequence[str]) -> int:
    """Run pytest on an explicit node-id list (no shell @file; pytest does not support it)."""
    import pytest

    nodeids = [line.strip() for line in nodeids_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not nodeids:
        raise RuntimeError(f"node-id file {nodeids_path} is empty")
    if len(set(nodeids)) != len(nodeids):
        raise RuntimeError(f"node-id file {nodeids_path} contains duplicates")
    # Drop a leading bare "--" separator from argparse.REMAINDER callers.
    args = list(pytest_args)
    if args and args[0] == "--":
        args = args[1:]
    return int(pytest.main([*args, *nodeids]))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--shard-id", type=int, required=True)
    plan.add_argument("--shard-count", type=int, default=SHARD_COUNT)
    plan.add_argument("--durations", type=Path)
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--args-output", type=Path, required=True)
    verify = commands.add_parser("verify-artifacts")
    verify.add_argument("--artifact-dir", type=Path, required=True)
    verify.add_argument("--shard-count", type=int, default=SHARD_COUNT)
    durations = commands.add_parser("parse-durations")
    durations.add_argument("--log", type=Path, action="append", required=True)
    durations.add_argument("--output", type=Path, required=True)
    run = commands.add_parser("run", help="Invoke pytest with node IDs from a file (not shell @file)")
    run.add_argument("--nodeids", type=Path, required=True)
    run.add_argument("pytest_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            write_plan(
                shard_id=args.shard_id,
                shard_count=args.shard_count,
                durations_path=args.durations,
                output=args.output,
                args_output=args.args_output,
            )
        elif args.command == "verify-artifacts":
            verify_artifacts(args.artifact_dir, args.shard_count)
        elif args.command == "parse-durations":
            parse_durations(args.log, args.output)
        elif args.command == "run":
            return run_nodeids(args.nodeids, args.pytest_args)
        else:
            raise RuntimeError(f"unknown command: {args.command}")
    except (OSError, RuntimeError, ValueError, element_tree.ParseError) as error:
        print(f"pytest shard error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
