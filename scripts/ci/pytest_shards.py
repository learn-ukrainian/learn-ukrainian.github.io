#!/usr/bin/env python3
"""Plan and verify duration-balanced pytest shards for Cursor Cloud.

GitHub Actions CI no longer invokes this planner (``ci.yml`` uses a modulo
file split). Cursor Cloud's ``cursor_cloud_full_pytest.sh`` still does.

Each shard collects the selected suite locally, groups every selected
node ID by test file, then uses deterministic longest-processing-time (LPT)
assignment.  ``write_plans`` remains available for offline tooling that wants
all four plans in one directory.

Required selection (stage-1 slow-split): the identical mark expression
``not atlas_release and not slow`` is applied on every shard collection and
worker invocation path, fastlane, and coverage inputs.
``pyproject.toml`` ``addopts`` keeps ``-m 'not atlas_release'`` only — never
put ``not slow`` in global addopts (nightly would inherit it).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
# Identical expression everywhere the required gate collects or filters.
REQUIRED_MARKEXPR = "not atlas_release and not slow"
SLOW_MARKEXPR = "slow and not atlas_release"
COMMON_ARGS = (
    "tests/",
    f"--deselect={PLAYGROUND_PERF_TEST}",
    "-m",
    REQUIRED_MARKEXPR,
    "--strict-markers",
)
PLANNER_SCHEMA_VERSION = 2
DURATION_SNAPSHOT_SCHEMA_VERSION = 1
_DURATION_LINE = re.compile(r"^\s*(?P<seconds>\d+(?:\.\d+)?)s\s+(?:call|setup|teardown)\s+(?P<nodeid>\S+)")
_DATASET_VERSION = 1
_P95_HISTORY_LIMIT = 40


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _duration_digest(durations: dict[str, float]) -> str:
    return _canonical_digest(durations)


SELECTION_DIGEST = _canonical_digest(COMMON_ARGS)


def _digest(nodeids: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(nodeids)).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalise_durations(source: Any, *, label: str, strict: bool = False) -> dict[str, float]:
    if not isinstance(source, dict):
        raise ValueError(f"duration file {label} has invalid node_durations")
    durations: dict[str, float] = {}
    for nodeid, duration in source.items():
        valid = (
            isinstance(nodeid, str)
            and isinstance(duration, (int, float))
            and not isinstance(duration, bool)
            and math.isfinite(float(duration))
            and float(duration) > 0
        )
        if not valid:
            if strict:
                raise ValueError(f"duration file {label} contains an invalid timing")
            continue
        durations[nodeid] = float(duration)
    return durations


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
    return _normalise_durations(source, label=str(path))


def write_duration_snapshot(
    *,
    durations_path: Path | None,
    output: Path,
    source_sha: str,
    cache_primary_key: str,
    cache_matched_key: str | None,
    cache_hit: str,
) -> None:
    """Freeze one duration input for every shard in this CI event."""
    durations = load_durations(durations_path)
    mode = "cache" if durations else "median-fallback"
    primary_key = cache_primary_key.strip() or "unspecified"
    matched_key = (cache_matched_key or "").strip()
    snapshot = {
        "cache_hit": cache_hit.strip().lower() == "true",
        "duration_cache_key": matched_key or (primary_key if mode == "cache" else "none"),
        "duration_cache_matched_key": matched_key or None,
        "duration_cache_primary_key": primary_key,
        "duration_mode": mode,
        "duration_snapshot_digest": _duration_digest(durations),
        "node_durations": durations,
        "planner_schema_version": PLANNER_SCHEMA_VERSION,
        "schema_version": DURATION_SNAPSHOT_SCHEMA_VERSION,
        "selection_digest": SELECTION_DIGEST,
        "source_sha": source_sha.strip(),
    }
    if not snapshot["source_sha"]:
        raise ValueError("duration snapshot source_sha must not be empty")
    _write_json(output, snapshot)


def load_duration_snapshot(path: Path, *, expected_source_sha: str | None = None) -> dict[str, Any]:
    """Load and validate the immutable duration snapshot shared by all shards."""
    raw = _read_json(path)
    if not isinstance(raw, dict) or raw.get("schema_version") != DURATION_SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(f"duration snapshot {path} has an unsupported schema")
    if raw.get("planner_schema_version") != PLANNER_SCHEMA_VERSION:
        raise ValueError(f"duration snapshot {path} has an unsupported planner schema")
    if raw.get("selection_digest") != SELECTION_DIGEST:
        raise ValueError(f"duration snapshot {path} has a selection digest mismatch")
    source_sha = raw.get("source_sha")
    if not isinstance(source_sha, str) or not source_sha.strip():
        raise ValueError(f"duration snapshot {path} has no source SHA")
    if expected_source_sha is not None and source_sha != expected_source_sha.strip():
        raise ValueError(f"duration snapshot source SHA {source_sha!r} does not match {expected_source_sha!r}")
    durations = _normalise_durations(raw.get("node_durations"), label=str(path), strict=True)
    if raw.get("duration_snapshot_digest") != _duration_digest(durations):
        raise ValueError(f"duration snapshot {path} has a duration digest mismatch")
    mode = raw.get("duration_mode")
    if mode not in {"cache", "median-fallback"}:
        raise ValueError(f"duration snapshot {path} has an invalid duration mode")
    cache_key = raw.get("duration_cache_key")
    if not isinstance(cache_key, str) or not cache_key:
        raise ValueError(f"duration snapshot {path} has no duration cache identity")
    return {**raw, "node_durations": durations}


def validate_duration_snapshot(path: Path, *, expected_source_sha: str | None = None) -> None:
    """Validate the fast planner-contract input without collecting tests."""
    snapshot = load_duration_snapshot(path, expected_source_sha=expected_source_sha)
    print(
        "validated pytest duration snapshot: "
        f"source_sha={snapshot['source_sha']} "
        f"mode={snapshot['duration_mode']} "
        f"timings={len(snapshot['node_durations'])} "
        f"digest={snapshot['duration_snapshot_digest']}"
    )


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


def _plan_payload(
    *,
    nodeids: Sequence[str],
    assigned: Sequence[str],
    weights: dict[str, float],
    shard_id: int,
    shard_count: int,
    snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    metadata = snapshot or {
        "duration_cache_key": "offline",
        "duration_mode": "local",
        "duration_snapshot_digest": _duration_digest({}),
        "planner_schema_version": PLANNER_SCHEMA_VERSION,
        "selection_digest": SELECTION_DIGEST,
        "source_sha": "offline",
    }
    assigned_files = sorted({nodeid.split("::", 1)[0] for nodeid in assigned})
    return {
        "assigned_digest": _digest(assigned),
        "assigned_nodeids": list(assigned),
        "collected_count": len(nodeids),
        "collected_digest": _digest(nodeids),
        "duration_cache_key": metadata["duration_cache_key"],
        "duration_mode": metadata["duration_mode"],
        "duration_snapshot_digest": metadata["duration_snapshot_digest"],
        "estimated_seconds": sum(weights[filename] for filename in assigned_files),
        "grouping": "file",
        "markexpr": REQUIRED_MARKEXPR,
        "planner_schema_version": metadata["planner_schema_version"],
        "selection_digest": metadata["selection_digest"],
        "serial_nodeids": list(SERIAL_TESTS) if shard_id == 1 else [],
        "shard_count": shard_count,
        "shard_id": shard_id,
        "source_sha": metadata["source_sha"],
        "partition_mode": "lpt-durations",
    }


def _write_plan_outputs(output_dir: Path, plan: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "test-nodeids.txt").write_text("\n".join(plan["assigned_nodeids"]) + "\n", encoding="utf-8")
    _write_json(output_dir / "plan.json", plan)


def assert_set_integrity(nodeids: Sequence[str], shards: Sequence[Sequence[str]]) -> None:
    """Fail closed unless shard union equals the fast collection exactly.

    Empty shards are a silent gate collapse (green with zero work). Duplicates
    or omissions mean the required set drifted from the planner collection.
    """
    if any(not assigned for assigned in shards):
        empty = [index + 1 for index, assigned in enumerate(shards) if not assigned]
        raise RuntimeError(f"planner produced empty shard(s): {empty}")
    assigned = [nodeid for shard in shards for nodeid in shard]
    if len(assigned) != len(set(assigned)):
        raise RuntimeError("a collected test was assigned to more than one shard")
    if set(assigned) != set(nodeids):
        missing = sorted(set(nodeids) - set(assigned))
        extra = sorted(set(assigned) - set(nodeids))
        raise RuntimeError(
            "shard union does not equal fast collection "
            f"(missing={len(missing)}, extra={len(extra)})"
        )
    if len(assigned) != len(nodeids):
        raise RuntimeError("shard assignment count does not match collected selection")


def write_plans(*, durations_path: Path | None, output_dir: Path, shard_count: int = SHARD_COUNT) -> None:
    """Collect once and write every matrix-worker plan from one duration dataset."""
    nodeids = collect_nodeids()
    durations = load_durations(durations_path)
    # Duration keys for deselected slow tests are ignored; unknown files use median.
    # Refresh the committed/cache dataset only when membership imbalance is measured.
    shards = assign_shards(nodeids, shard_count, durations)
    assert_set_integrity(nodeids, shards)
    output_dir.mkdir(parents=True, exist_ok=True)
    weights = _file_weights(nodeids, durations)
    for shard_id, assigned in enumerate(shards, start=1):
        shard_dir = output_dir / f"pytest-shard-{shard_id}"
        _write_plan_outputs(
            shard_dir,
            _plan_payload(
                nodeids=nodeids,
                assigned=assigned,
                weights=weights,
                shard_id=shard_id,
                shard_count=shard_count,
                snapshot=None,
            ),
        )


def write_shard_plan(
    *,
    snapshot_path: Path,
    output_dir: Path,
    shard_id: int,
    shard_count: int = SHARD_COUNT,
    expected_source_sha: str | None = None,
) -> None:
    """Collect and materialize one shard's deterministic plan."""
    if shard_id < 1 or shard_id > shard_count:
        raise ValueError(f"shard_id must be between 1 and {shard_count}")
    snapshot = load_duration_snapshot(snapshot_path, expected_source_sha=expected_source_sha)
    nodeids = collect_nodeids()
    durations = snapshot["node_durations"]
    shards = assign_shards(nodeids, shard_count, durations)
    assert_set_integrity(nodeids, shards)
    weights = _file_weights(nodeids, durations)
    _write_plan_outputs(
        output_dir,
        _plan_payload(
            nodeids=nodeids,
            assigned=shards[shard_id - 1],
            weights=weights,
            shard_id=shard_id,
            shard_count=shard_count,
            snapshot=snapshot,
        ),
    )


def _junit_count(path: Path) -> int:
    root = element_tree.parse(path).getroot()
    if root.tag == "testsuite":
        return int(root.attrib.get("tests", "0"))
    return sum(int(suite.attrib.get("tests", "0")) for suite in root.iter("testsuite"))


def verify_artifacts(
    artifact_dir: Path,
    shard_count: int,
    *,
    expected_source_sha: str | None = None,
    require_plan_metadata: bool = False,
    require_execution_receipt: bool = False,
) -> None:
    """Fail closed unless plan, execution count, and partition all agree."""
    plans: list[dict[str, Any]] = []
    for shard_id in range(1, shard_count + 1):
        shard_dir = artifact_dir / f"pytest-shard-{shard_id}"
        plan_path = shard_dir / "plan.json"
        nodeids_path = shard_dir / "test-nodeids.txt"
        main_junit = shard_dir / "main-junit.xml"
        if not plan_path.exists() or not nodeids_path.exists() or not main_junit.exists():
            raise RuntimeError(f"missing plan, node-ID, or main JUnit artifact for shard {shard_id}")
        plan = _read_json(plan_path)
        if plan.get("shard_id") != shard_id or plan.get("shard_count") != shard_count:
            raise RuntimeError(f"invalid shard identity in {plan_path}")
        assigned = plan.get("assigned_nodeids")
        if not isinstance(assigned, list) or not all(isinstance(nodeid, str) for nodeid in assigned):
            raise RuntimeError(f"invalid assigned node IDs in {plan_path}")
        listed = [line.strip() for line in nodeids_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if listed != assigned:
            raise RuntimeError(f"test-nodeids.txt does not match plan.json in shard {shard_id}")
        if not assigned:
            raise RuntimeError(f"empty shard {shard_id} collapses the required gate")
        if _digest(assigned) != plan.get("assigned_digest"):
            raise RuntimeError(f"assigned node ID digest mismatch in {plan_path}")
        if plan.get("partition_mode") != "lpt-durations" or plan.get("grouping") != "file":
            raise RuntimeError(f"invalid planner mode in {plan_path}")
        if plan.get("markexpr") != REQUIRED_MARKEXPR:
            raise RuntimeError(
                f"plan markexpr must be {REQUIRED_MARKEXPR!r}, got {plan.get('markexpr')!r}"
            )
        if _junit_count(main_junit) != len(assigned):
            raise RuntimeError(f"main JUnit count does not match plan for shard {shard_id}")
        if expected_source_sha is not None and plan.get("source_sha") != expected_source_sha.strip():
            raise RuntimeError(f"source SHA does not match the event SHA for shard {shard_id}")
        if require_plan_metadata:
            for field in (
                "duration_cache_key",
                "duration_mode",
                "duration_snapshot_digest",
                "planner_schema_version",
                "selection_digest",
                "source_sha",
            ):
                if field not in plan:
                    raise RuntimeError(f"plan {plan_path} is missing required field {field}")
            if plan["planner_schema_version"] != PLANNER_SCHEMA_VERSION:
                raise RuntimeError(f"unsupported planner schema in {plan_path}")
            if plan["selection_digest"] != SELECTION_DIGEST:
                raise RuntimeError(f"selection digest mismatch in {plan_path}")
        if require_execution_receipt:
            receipt_path = shard_dir / "execution.json"
            if not receipt_path.exists():
                raise RuntimeError(f"missing execution receipt for shard {shard_id}")
            receipt = _read_json(receipt_path)
            if receipt.get("planned_nodeids") != assigned:
                raise RuntimeError(f"execution receipt plan mismatch for shard {shard_id}")
            reported = receipt.get("reported_nodeids")
            if not isinstance(reported, list) or set(reported) != set(assigned) or len(reported) != len(assigned):
                raise RuntimeError(f"execution receipt does not cover the assigned set for shard {shard_id}")
            if receipt.get("reported_count") != len(assigned) or receipt.get("reported_digest") != _digest(reported):
                raise RuntimeError(f"execution receipt count or digest mismatch for shard {shard_id}")
            if receipt.get("pytest_exit_code") != 0:
                raise RuntimeError(f"pytest execution receipt is not green for shard {shard_id}")
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
    if require_plan_metadata:
        for field in ("source_sha", "duration_snapshot_digest", "duration_cache_key", "duration_mode"):
            if len({plan[field] for plan in plans}) != 1:
                raise RuntimeError(f"shards disagree about {field}")


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


_PUBLISH_EVENTS = frozenset({"merge_group", "push", "schedule"})


def publish_durations(
    *,
    log_paths: Sequence[Path],
    previous: Path | None,
    output: Path,
    summary: Path,
    event: str = "push",
) -> None:
    """Publish landing-tier timings and quote rolling slowest-shard p95."""
    if event not in _PUBLISH_EVENTS:
        raise ValueError(f"unsupported duration-publish event {event!r}")
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
            "event": event,
            "node_durations": node_durations,
            "schema_version": _DATASET_VERSION,
            "slowest_shard_seconds": history,
        },
    )
    event_label = event.replace("_", " ")
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(
        "## Pytest shard duration record\n\n"
        f"Successful {event_label} run shard test durations: "
        f"{', '.join(f'{total:.2f}s' for total in shard_totals)}.\n\n"
        f"Slowest-shard p95: **{p95:.2f}s** across {len(history)} successful landing-tier run(s).\n",
        encoding="utf-8",
    )


class _ExecutionRecorder:
    def __init__(self) -> None:
        self.reported_nodeids: set[str] = set()

    def pytest_runtest_logreport(self, report: Any) -> None:
        self.reported_nodeids.add(report.nodeid)


def _write_execution_receipt(
    path: Path,
    *,
    planned_nodeids: Sequence[str],
    reported_nodeids: Iterable[str],
    pytest_exit_code: int,
) -> None:
    reported = sorted(set(reported_nodeids))
    _write_json(
        path,
        {
            "planned_count": len(planned_nodeids),
            "planned_digest": _digest(planned_nodeids),
            "planned_nodeids": list(planned_nodeids),
            "pytest_exit_code": pytest_exit_code,
            "reported_count": len(reported),
            "reported_digest": _digest(reported),
            "reported_nodeids": reported,
            "schema_version": 1,
        },
    )


def run_nodeids(nodeids_path: Path, pytest_args: Sequence[str], receipt_path: Path | None = None) -> int:
    """Invoke pytest with a shard-produced node-ID list (not shell @file)."""
    import pytest

    if __package__ in (None, ""):
        # Invoked directly as `python scripts/ci/pytest_shards.py`, so the repo
        # root (needed for `scripts.ci.stall_watch`) is not yet on sys.path.
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from scripts.ci.stall_watch import StallWatcher

    nodeids = [line.strip() for line in nodeids_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not nodeids:
        raise RuntimeError(f"node-id file {nodeids_path} is empty")
    if len(set(nodeids)) != len(nodeids):
        raise RuntimeError(f"node-id file {nodeids_path} contains duplicates")
    args = list(pytest_args)
    if args and args[0] == "--":
        args = args[1:]
    # Controller-side stall watch (#5776 leftover): pytest-timeout only fires
    # inside xdist workers, so a hang in the controller or a full worker pipe
    # is otherwise silent until the job's timeout-minutes cancels it.
    with StallWatcher.from_env():
        if receipt_path is None:
            return int(pytest.main([*args, *nodeids]))
        recorder = _ExecutionRecorder()
        exit_code = int(pytest.main([*args, *nodeids], plugins=[recorder]))
        _write_execution_receipt(
            receipt_path,
            planned_nodeids=nodeids,
            reported_nodeids=recorder.reported_nodeids,
            pytest_exit_code=exit_code,
        )
        return exit_code


def _parser() -> argparse.ArgumentParser:
    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
        description=(
            "Plan, execute, and verify the CI Gate's deterministic pytest shard partition.\n"
            "Use it for full-tier CI evidence and local planner/partition tests; it does not replace pytest itself."
        ),
        formatter_class=formatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/ci/pytest_shards.py plan-shard --snapshot ci-artifacts/pytest-duration-snapshot.json --shard-id 1 --output-dir ci-artifacts\n"
            "  .venv/bin/python scripts/ci/pytest_shards.py verify-artifacts --artifact-dir ci-artifacts --expected-source-sha $GITHUB_SHA --require-plan-metadata --require-execution-receipt\n"
            "Outputs: shard plans, node-ID lists, execution receipts, and validation errors; no databases or remote state.\n"
            "Exit codes: 0 means the requested operation passed; 1 means an input, partition, or test failed; 2 means CLI usage failed.\n"
            "Related: .github/workflows/ci.yml, tests/test_ci_shard_partition.py, and docs/runbooks/ci-gate.md."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True, title="commands")
    plan = commands.add_parser("plan", help="Materialize all shard plans in one directory for offline use.", description="Collect once and write all four offline LPT plans.", formatter_class=formatter)
    plan.add_argument("--durations", type=Path, help="Optional JSON duration dataset; missing input uses median fallback.")
    plan.add_argument("--output-dir", type=Path, required=True, help="Directory receiving pytest-shard-N/plan.json and test-nodeids.txt.")
    plan.add_argument("--shard-count", type=int, default=SHARD_COUNT, help=f"Number of shards (default: {SHARD_COUNT}).")
    snapshot = commands.add_parser("snapshot", help="Freeze one shared duration input for a CI event.", description="Normalize a cache restore into an immutable shard input snapshot.", formatter_class=formatter)
    snapshot.add_argument("--durations", type=Path, help="Optional restored duration JSON; missing input selects median fallback.")
    snapshot.add_argument("--output", type=Path, required=True, help="Output JSON snapshot path.")
    snapshot.add_argument("--source-sha", required=True, help="Exact event tree SHA, normally GITHUB_SHA.")
    snapshot.add_argument("--cache-primary-key", required=True, help="Requested cache key used for this event.")
    snapshot.add_argument("--cache-matched-key", help="Matched restore key, when the cache action exposes one.")
    snapshot.add_argument("--cache-hit", default="false", help="Exact cache-hit output (default: false).")
    plan_shard = commands.add_parser("plan-shard", help="Collect and write one shard's plan locally.", description="Collect the required suite once and write one deterministic shard-local LPT plan.", formatter_class=formatter)
    plan_shard.add_argument("--snapshot", type=Path, required=True, help="Immutable duration snapshot JSON shared by all shards.")
    plan_shard.add_argument("--shard-id", type=int, required=True, help="1-based shard number, e.g. 1.")
    plan_shard.add_argument("--output-dir", type=Path, required=True, help="Directory receiving plan.json and test-nodeids.txt.")
    plan_shard.add_argument("--shard-count", type=int, default=SHARD_COUNT, help=f"Total shard count (default: {SHARD_COUNT}).")
    plan_shard.add_argument("--expected-source-sha", help="Require the snapshot source SHA to equal this event SHA.")
    validate = commands.add_parser("validate-snapshot", help="Validate the fast planner-contract snapshot without collection.", description="Check snapshot schema, planner version, selection digest, and source identity without collecting tests.", formatter_class=formatter)
    validate.add_argument("--snapshot", type=Path, required=True, help="Immutable duration snapshot JSON to validate.")
    validate.add_argument("--expected-source-sha", help="Require the snapshot source SHA to equal this event SHA.")
    verify = commands.add_parser("verify-artifacts", help="Fail closed unless all shard evidence forms one complete partition.", description="Verify plans, node-ID lists, JUnit counts, and optional execution/provenance evidence.", formatter_class=formatter)
    verify.add_argument("--artifact-dir", type=Path, required=True, help="Directory containing pytest-shard-1 through pytest-shard-N artifacts.")
    verify.add_argument("--shard-count", type=int, default=SHARD_COUNT, help=f"Expected number of shards (default: {SHARD_COUNT}).")
    verify.add_argument("--expected-source-sha", help="Require every plan source SHA to equal this event SHA.")
    verify.add_argument("--require-plan-metadata", action="store_true", help="Require and cross-check immutable snapshot/planner metadata.")
    verify.add_argument("--require-execution-receipt", action="store_true", help="Require each shard's reported execution node-ID receipt.")
    publish = commands.add_parser("publish-durations", help="Publish landing-tier test timings for later shard balancing.", description="Parse shard logs and write the rolling duration dataset.", formatter_class=formatter)
    publish.add_argument("--log", type=Path, action="append", required=True, help="Pytest log path; repeat once per shard.")
    publish.add_argument("--previous", type=Path, help="Prior duration dataset, if available.")
    publish.add_argument("--output", type=Path, required=True, help="Output duration dataset JSON path.")
    publish.add_argument("--summary", type=Path, required=True, help="Markdown summary output path.")
    publish.add_argument(
        "--event",
        default="push",
        choices=sorted(_PUBLISH_EVENTS),
        help="github.event_name for the summary label (default: push).",
    )
    run = commands.add_parser("run", help="Run exactly the node IDs in a shard plan.", description="Execute a node-ID file with pytest and optionally record reported execution IDs.", formatter_class=formatter)
    run.add_argument("--nodeids", type=Path, required=True, help="Newline-delimited planned node-ID file.")
    run.add_argument("--execution-receipt", type=Path, help="Optional JSON receipt path recording planned and reported node IDs.")
    run.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Arguments passed to pytest after `--`, e.g. -- -q --junitxml=main-junit.xml.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            write_plans(durations_path=args.durations, output_dir=args.output_dir, shard_count=args.shard_count)
        elif args.command == "snapshot":
            write_duration_snapshot(
                durations_path=args.durations,
                output=args.output,
                source_sha=args.source_sha,
                cache_primary_key=args.cache_primary_key,
                cache_matched_key=args.cache_matched_key,
                cache_hit=args.cache_hit,
            )
        elif args.command == "plan-shard":
            write_shard_plan(
                snapshot_path=args.snapshot,
                output_dir=args.output_dir,
                shard_id=args.shard_id,
                shard_count=args.shard_count,
                expected_source_sha=args.expected_source_sha,
            )
        elif args.command == "validate-snapshot":
            validate_duration_snapshot(args.snapshot, expected_source_sha=args.expected_source_sha)
        elif args.command == "verify-artifacts":
            verify_artifacts(
                args.artifact_dir,
                args.shard_count,
                expected_source_sha=args.expected_source_sha,
                require_plan_metadata=args.require_plan_metadata,
                require_execution_receipt=args.require_execution_receipt,
            )
        elif args.command == "publish-durations":
            publish_durations(
                log_paths=args.log,
                previous=args.previous,
                output=args.output,
                summary=args.summary,
                event=args.event,
            )
        elif args.command == "run":
            return run_nodeids(args.nodeids, args.pytest_args, receipt_path=args.execution_receipt)
    except (OSError, RuntimeError, ValueError, element_tree.ParseError) as error:
        print(f"pytest shard error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
