"""Plan and run deterministic, evidence-producing pytest shards.

The required CI gate never asks a diff which tests to run.  Every invocation
collects the complete test suite, removes only exact node IDs from the committed
quarantine ledger, and assigns every remaining node to one of five jobs.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import signal
import subprocess
import time
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

DEFAULT_SHARD_COUNT = 5
THREAD_SENSITIVE_FILES = frozenset(
    {
        "tests/orchestration/test_thread_handoff.py",
        "tests/orchestration/test_thread_restart_e2e.py",
        "tests/test_pytest_worker_rlimit_isolation.py",
        "tests/wiki/test_ukrainian_wiki_corpus.py",
    }
)
BOUNDED_NETWORK_FILES = frozenset({"tests/test_video_discovery.py"})


def _coverage_enabled() -> bool:
    """Return whether this full-suite invocation must write coverage evidence."""
    return os.environ.get("CI_PYTEST_COVERAGE") == "1"


class ShardPlanError(ValueError):
    """Raised when the test plan or quarantine ledger is inconsistent."""


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _atomic_lines_write(path: Path, values: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text("".join(f"{value}\n" for value in values), encoding="utf-8")
    temporary.replace(path)


def _node_file(nodeid: str) -> str:
    return nodeid.split("::", 1)[0]


def _group_for(nodeid: str) -> str | None:
    """Return a process-sensitive group that must stay in one external shard."""
    test_file = _node_file(nodeid)
    if test_file in THREAD_SENSITIVE_FILES:
        return "thread-sensitive"
    if "inventory" in Path(test_file).name:
        return "source-inventory"
    if test_file in BOUNDED_NETWORK_FILES:
        # This file contains a legitimate 60-second timeout probe. Keeping it
        # together on the otherwise light third shard balances wall time while
        # still executing every node on every workflow invocation.
        return "bounded-network"
    return None


def load_quarantine(path: Path) -> tuple[dict[str, str], ...]:
    """Load and validate the exact-node, human-owned quarantine ledger."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ShardPlanError(f"cannot read quarantine ledger {path}: {error}") from error

    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ShardPlanError("quarantine ledger must be an object with version 1")
    entries = raw.get("entries")
    if not isinstance(entries, list):
        raise ShardPlanError("quarantine ledger entries must be a list")

    validated: list[dict[str, str]] = []
    nodeids: set[str] = set()
    required = ("nodeid", "reason", "owner", "tracking")
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise ShardPlanError(f"quarantine entry {index} must be an object")
        normalized: dict[str, str] = {}
        for field in required:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ShardPlanError(f"quarantine entry {index} has no non-empty {field!r}")
            normalized[field] = value.strip()
        nodeid = normalized["nodeid"]
        if not nodeid.startswith("tests/") or "::" not in nodeid:
            raise ShardPlanError(f"quarantine entry {index} nodeid is not an exact pytest node: {nodeid!r}")
        if nodeid in nodeids:
            raise ShardPlanError(f"quarantine ledger repeats nodeid {nodeid!r}")
        nodeids.add(nodeid)
        validated.append(normalized)
    return tuple(validated)


def collect_nodeids(repo_root: Path) -> list[str]:
    """Collect every test node with the repository's default marker filter disabled."""
    import pytest

    class Collector:
        nodeids: list[str]

        def __init__(self) -> None:
            self.nodeids = []

        def pytest_collection_finish(self, session: pytest.Session) -> None:
            self.nodeids = [item.nodeid for item in session.items]

    collector = Collector()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = pytest.main(
            ["--collect-only", "-q", "-o", "addopts=", str(repo_root / "tests")],
            plugins=[collector],
        )
    if result != pytest.ExitCode.OK:
        raise ShardPlanError(f"pytest collection failed with exit code {result}")
    if not collector.nodeids:
        raise ShardPlanError("pytest collection produced no tests")
    if len(collector.nodeids) != len(set(collector.nodeids)):
        raise ShardPlanError("pytest collection produced duplicate node IDs")
    return sorted(collector.nodeids)


def build_plans(
    nodeids: Sequence[str],
    quarantined_nodeids: Iterable[str],
    *,
    shard_count: int = DEFAULT_SHARD_COUNT,
) -> tuple[list[list[str]], list[str]]:
    """Return a complete, deterministic and balanced node-level partition."""
    if shard_count < 1:
        raise ShardPlanError("shard_count must be positive")
    all_nodes = list(nodeids)
    if len(all_nodes) != len(set(all_nodes)):
        raise ShardPlanError("planner received duplicate test node IDs")

    quarantine = set(quarantined_nodeids)
    collected = set(all_nodes)
    stale = sorted(quarantine - collected)
    if stale:
        raise ShardPlanError(f"quarantine contains node IDs absent from collection: {stale}")

    runnable = [nodeid for nodeid in all_nodes if nodeid not in quarantine]
    if not runnable:
        raise ShardPlanError("quarantine removes every collected test")

    grouped: dict[str, list[str]] = {
        "thread-sensitive": [],
        "source-inventory": [],
        "bounded-network": [],
    }
    ordinary: list[str] = []
    for nodeid in runnable:
        group = _group_for(nodeid)
        if group is None:
            ordinary.append(nodeid)
        else:
            grouped[group].append(nodeid)

    buckets: list[list[str]] = [[] for _ in range(shard_count)]
    for group_name in ("thread-sensitive", "source-inventory", "bounded-network"):
        members = grouped[group_name]
        if members:
            target = min(range(shard_count), key=lambda index: (len(buckets[index]), index))
            buckets[target].extend(members)

    for nodeid in ordinary:
        target = min(range(shard_count), key=lambda index: (len(buckets[index]), index))
        buckets[target].append(nodeid)

    for index, bucket in enumerate(buckets, start=1):
        if not bucket:
            raise ShardPlanError(f"shard {index} would run zero tests")
    partition = [nodeid for bucket in buckets for nodeid in bucket]
    if sorted(partition) != sorted(runnable):
        raise ShardPlanError("planner did not produce an exact partition of runnable nodes")
    return buckets, sorted(quarantine)


def prepare(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    evidence_dir = Path(args.evidence_dir)
    quarantine = load_quarantine(Path(args.quarantine))
    nodeids = collect_nodeids(repo_root)
    plans, _ = build_plans(
        nodeids,
        (entry["nodeid"] for entry in quarantine),
        shard_count=args.shard_count,
    )
    plan = plans[args.shard - 1]

    def quarantine_owner(nodeid: str) -> int:
        group = _group_for(nodeid)
        if group is not None:
            for index, bucket in enumerate(plans):
                if any(_group_for(candidate) == group for candidate in bucket):
                    return index
        # A one-node ordinary file can be fully quarantined.  It still needs a
        # deterministic evidence owner so the gate can prove the ledger was read.
        return sum(nodeid.encode("utf-8")) % args.shard_count

    shard_quarantine = sorted(
        entry["nodeid"] for entry in quarantine if quarantine_owner(entry["nodeid"]) == args.shard - 1
    )
    # Each matrix VM collects independently.  Preserve the complete result as
    # evidence so CI Gate can reject even a same-count collection divergence
    # instead of trusting the local shard plan alone.
    _atomic_lines_write(evidence_dir / "collected.txt", nodeids)
    _atomic_lines_write(evidence_dir / "plan.txt", plan)
    _atomic_lines_write(evidence_dir / "quarantine.txt", shard_quarantine)
    _atomic_json_write(
        evidence_dir / "plan.json",
        {
            "collected_nodes": len(nodeids),
            "planned_nodes": len(plan),
            "quarantined_nodes": len(shard_quarantine),
            "shard": args.shard,
            "shard_count": args.shard_count,
        },
    )
    print(
        f"planned shard {args.shard}/{args.shard_count}: {len(plan)} runnable nodes; "
        f"{len(shard_quarantine)} quarantined nodes"
    )
    return 0


def _terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
        process.wait(timeout=30)


def _read_current_nodeid(path: Path) -> str | None:
    """Return the last node dispatched by pytest's controller, when present."""
    try:
        nodeids = [line for line in path.read_text(encoding="utf-8").splitlines() if line]
    except OSError:
        return None
    return nodeids[-1] if nodeids else None


def run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    evidence_dir = Path(args.evidence_dir)
    plan_path = evidence_dir / "plan.txt"
    executed_path = evidence_dir / "executed.txt"
    current_path = evidence_dir / "current.txt"
    plan = [line for line in plan_path.read_text(encoding="utf-8").splitlines() if line]
    if not plan:
        raise ShardPlanError(f"{plan_path} has no runnable node IDs")

    python = repo_root / ".venv" / "bin" / "python"
    if not python.is_file():
        raise ShardPlanError(f"expected CI virtual environment interpreter at {python}")
    command = [
        str(python),
        "-m",
        "pytest",
        "tests",
        "-o",
        "addopts=",
        "-n",
        "1",
        "--max-worker-restart=0",
        "--dist",
        "loadgroup",
        "--strict-markers",
        "--timeout=900",
        "--timeout-method=thread",
        "-rs",
        "--durations=50",
        "-p",
        "scripts.ci.pytest_evidence",
    ]
    coverage_enabled = _coverage_enabled()
    coverage_file = evidence_dir / "coverage"
    if coverage_enabled:
        command.extend(
            [
                "--cov=scripts",
                "--cov-append",
                "--cov-report=",
            ]
        )
    environment = {
        **os.environ,
        "CI_PYTEST_PLAN_FILE": str(plan_path.resolve()),
        "CI_PYTEST_EXECUTED_FILE": str(executed_path.resolve()),
        "CI_PYTEST_CURRENT_FILE": str(current_path.resolve()),
        "PYTHONFAULTHANDLER": "1",
    }
    if coverage_enabled:
        environment["COVERAGE_FILE"] = str(coverage_file.resolve())
    started = time.monotonic()
    timed_out = False
    current_nodeid: str | None = None
    returncode: int
    process = subprocess.Popen(command, cwd=repo_root, env=environment, start_new_session=True)
    try:
        returncode = process.wait(timeout=args.timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        returncode = 124
        current_nodeid = _read_current_nodeid(current_path)
        current_detail = f"; last_started_node={current_nodeid}" if current_nodeid else ""
        print(
            "::error title=pytest shard timeout::"
            f"shard {args.shard} exceeded the {args.timeout_seconds}-second job wrapper; "
            f"the timeout evidence artifact names it explicitly{current_detail}."
        )
        _atomic_json_write(
            evidence_dir / "timeout.json",
            {
                "shard": args.shard,
                "timeout_seconds": args.timeout_seconds,
                "timed_out": True,
                "current_nodeid": current_nodeid,
            },
        )
        _terminate_process_group(process)
    if returncode == 0 and coverage_enabled and not coverage_file.is_file():
        returncode = 1
        print(
            "::error title=pytest coverage evidence missing::"
            f"shard {args.shard} completed without {coverage_file}"
        )
    elapsed = round(time.monotonic() - started, 3)
    if current_nodeid is None:
        current_nodeid = _read_current_nodeid(current_path)
    _atomic_json_write(
        evidence_dir / "run.json",
        {
            "elapsed_seconds": elapsed,
            "planned_nodes": len(plan),
            "returncode": returncode,
            "shard": args.shard,
            "timed_out": timed_out,
            "coverage_enabled": coverage_enabled,
            "current_nodeid": current_nodeid,
        },
    )
    print(f"pytest shard {args.shard}: returncode={returncode} elapsed_seconds={elapsed}")
    return returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("prepare", "run"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--shard", type=int, required=True, choices=range(1, DEFAULT_SHARD_COUNT + 1))
        subparser.add_argument("--evidence-dir", required=True)
        if command == "prepare":
            subparser.add_argument("--quarantine", required=True)
            subparser.add_argument("--shard-count", type=int, default=DEFAULT_SHARD_COUNT)
        else:
            subparser.add_argument("--timeout-seconds", type=int, default=1800)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "prepare":
        return prepare(args)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
