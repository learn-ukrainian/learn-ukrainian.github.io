"""Branch measurements with separate test outcomes and completeness (#11226)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path


class CollectionRecorder:
    """Retain selected node IDs on the controller, including with xdist workers."""

    def __init__(self) -> None:
        self.nodeids: list[str] = []
        self.collections: list[list[str]] = []
        self.core: str | None = None
        self.subprocess_patch: bool | None = None
        self.completed_nodeids: set[str] = set()
        self.failed_nodeids: set[str] = set()
        self.crashed_nodeids: set[str] = set()
        self.collection_errors: list[str] = []
        self.worker_exits: list[dict] = []

    def pytest_runtestloop(self, session) -> Generator[None, None, object]:
        # Read the active pytest-cov instance before it switches to its reporting instance.
        plugin = session.config.pluginmanager.getplugin("_cov")
        if plugin is not None and plugin.cov_controller is not None:
            cov = plugin.cov_controller.cov
            self.core = dict(cov.sys_info())["core"]
            self.subprocess_patch = "subprocess" in cov.get_option("run:patch")
        return (yield)

    def pytest_collection_finish(self, session) -> None:
        self.nodeids = [item.nodeid for item in session.items]

    def pytest_xdist_node_collection_finished(self, node, ids) -> None:
        self.collections.append(list(ids))
        self.nodeids = list(ids)

    def pytest_runtest_logreport(self, report) -> None:
        if report.failed:
            self.failed_nodeids.add(report.nodeid)
        if report.when == "teardown":
            self.completed_nodeids.add(report.nodeid)

    def pytest_collectreport(self, report) -> None:
        if report.failed:
            self.collection_errors.append(report.nodeid)

    def pytest_handlecrashitem(self, crashitem, report, sched) -> None:
        self.crashed_nodeids.add(crashitem)

    def pytest_testnodedown(self, node, error) -> None:
        # Local popen gateways expose the process; other transports remain unknown.
        process = getattr(getattr(node.gateway, "_io", None), "popen", None)
        self.worker_exits.append(
            {
                "worker": node.gateway.id,
                "returncode": process.poll() if process is not None else None,
                "unexpected": error is not None,
            }
        )


def versions() -> dict[str, str]:
    return {name: importlib.metadata.version(name) for name in ("coverage", "pytest-cov", "pytest")}


def run_shard(output: Path, shard: int, pytest_args: list[str]) -> int:
    import pytest

    output.mkdir(parents=True, exist_ok=True)
    # Keep pytest optional for combine, but wrap xdist's first-result runtest hook.
    pytest.hookimpl(wrapper=True)(CollectionRecorder.pytest_runtestloop)
    for hook in ("pytest_xdist_node_collection_finished", "pytest_handlecrashitem", "pytest_testnodedown"):
        pytest.hookimpl(optionalhook=True)(getattr(CollectionRecorder, hook))
    recorder = CollectionRecorder()
    started = time.monotonic()
    # Match `python -m pytest` import semantics despite running a helper outside the measured tree.
    sys.path.insert(0, str(Path.cwd()))
    status = int(pytest.main(pytest_args, plugins=[recorder]))
    consistent = all(ids == recorder.nodeids for ids in recorder.collections)
    receipt = {
        "sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, timeout=30).strip(),
        "workflow_run_id": os.environ["GITHUB_RUN_ID"],
        "workflow_run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "shard": shard,
        "collected_nodeids": recorder.nodeids,
        "collected_count": len(recorder.nodeids),
        "collection_consistent": consistent,
        "pytest_exit_status": status,
        "completed_nodeids": sorted(recorder.completed_nodeids),
        "failed_nodeids": sorted(recorder.failed_nodeids - recorder.crashed_nodeids),
        "crashed_nodeids": sorted(recorder.crashed_nodeids),
        "collection_errors": recorder.collection_errors,
        "worker_exits": recorder.worker_exits,
        "wall_seconds": round(time.monotonic() - started, 3),
        "versions": versions(),
        "core": recorder.core,
        "subprocess_patch": recorder.subprocess_patch,
        "config_sha256": hashlib.sha256(Path(os.environ["COVERAGE_RCFILE"]).read_bytes()).hexdigest(),
        "durations_sha256": hashlib.sha256(Path("ci-artifacts/pytest-file-durations.json").read_bytes()).hexdigest(),
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return int(
        status not in (0, 1)
        or not consistent
        or not recorder.nodeids
        or set(recorder.nodeids) != recorder.completed_nodeids
        or bool(recorder.crashed_nodeids or recorder.collection_errors)
        or (status == 1 and not recorder.failed_nodeids)
        or recorder.core != "CTracer"
        or recorder.subprocess_patch is not True
    )


def combine(root: Path, output: Path, sha: str, shard_count: int, matrix_result: str) -> int:
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "sha": sha,
        "workflow_run_id": os.environ["GITHUB_RUN_ID"],
        "workflow_run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "core": None,
        "subprocess_patch": None,
        "expected_shards": shard_count,
        "matrix_result": matrix_result,
        "versions": {},
        "complete": False,
        "shards": [],
        "errors": [],
        "tests_passed": False,
        "failed_nodeids": [],
        "crashed_nodeids": [],
        "unfinished_nodeids": [],
    }
    errors = manifest["errors"]
    data_files = []
    seen_nodeids: set[str] = set()
    duration_hashes = set()
    # Plain pytest failures return success from run_shard. Any failed job therefore
    # has an additional failure, such as pg_skip_guard or an artifact upload.
    if matrix_result != "success":
        errors.append(f"pytest matrix: {matrix_result}")
    try:
        import coverage

        manifest["versions"] = versions()
        config_hash = hashlib.sha256(Path(os.environ["COVERAGE_RCFILE"]).read_bytes()).hexdigest()
        for shard in range(1, shard_count + 1):
            directory = root / f"coverage-shard-{shard}"
            try:
                receipt = json.loads((directory / "receipt.json").read_text(encoding="utf-8"))
                manifest["shards"].append(receipt)
                if manifest["core"] is None:
                    manifest["core"] = receipt.get("core")
                    manifest["subprocess_patch"] = receipt.get("subprocess_patch")
                if receipt.get("core") != "CTracer" or receipt.get("subprocess_patch") is not True:
                    raise ValueError("CTracer core or subprocess patch was not active")
                if any(
                    receipt.get(key) != manifest[key]
                    for key in (
                        "sha",
                        "workflow_run_id",
                        "workflow_run_attempt",
                        "versions",
                        "core",
                        "subprocess_patch",
                    )
                ):
                    raise ValueError("receipt identity/version mismatch")
                if receipt["shard"] != shard or receipt["config_sha256"] != config_hash:
                    raise ValueError("shard/config mismatch")
                if receipt["collection_consistent"] is not True:
                    raise ValueError("collections differ")
                nodeids = receipt["collected_nodeids"]
                if not nodeids or receipt["collected_count"] != len(nodeids) or len(set(nodeids)) != len(nodeids):
                    raise ValueError("zero or invalid collected count")
                if seen_nodeids.intersection(nodeids):
                    raise ValueError("node IDs overlap another shard")
                seen_nodeids.update(nodeids)
                duration_hashes.add(receipt["durations_sha256"])
                completed = set(receipt["completed_nodeids"])
                failed = set(receipt["failed_nodeids"])
                crashed = set(receipt["crashed_nodeids"])
                if not (completed | failed | crashed) <= set(nodeids):
                    raise ValueError("outcome IDs were not collected")
                unfinished = set(nodeids) - completed
                manifest["failed_nodeids"].extend(sorted(failed))
                manifest["crashed_nodeids"].extend(sorted(crashed))
                manifest["unfinished_nodeids"].extend(sorted(unfinished))
                if unfinished or crashed or receipt["collection_errors"]:
                    errors.append(f"shard {shard}: unfinished tests, worker crash or collection errors")
                if receipt["pytest_exit_status"] not in (0, 1) or (
                    receipt["pytest_exit_status"] == 1 and not (failed or crashed)
                ):
                    errors.append(f"shard {shard}: pytest infrastructure failure ({receipt['pytest_exit_status']})")
                files = list(directory.glob(".coverage*"))
                if not files:
                    raise ValueError("missing raw coverage data")
                for path in files:
                    try:
                        data = coverage.CoverageData(basename=str(path))
                        data.read()
                        if not data.has_arcs() or not data.measured_files():
                            raise ValueError("raw data lacks nonempty branch coverage")
                        # Include pytest-cov's unsuffixed file explicitly.
                        data_files.append(str(path))
                    except (OSError, ValueError, coverage.CoverageException) as error:
                        errors.append(f"shard {shard}: {error}")
            except (OSError, ValueError, KeyError, TypeError, coverage.CoverageException) as error:
                errors.append(f"shard {shard}: {error}")
        if len(duration_hashes) != 1:
            errors.append("missing or differing duration snapshots")
        if data_files:
            cov = coverage.Coverage(data_file=str(output / ".coverage"))
            cov.combine(data_paths=data_files, strict=True, keep=True)
            cov.save()
            report_path = output / "coverage.json"
            cov.json_report(outfile=str(report_path))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            # coverage JSON reports branch arcs only; preserve *all* executed arcs too.
            for name, file_data in report["files"].items():
                file_data["executed_arcs"] = sorted(cov.get_data().arcs(name) or [])
            report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            manifest["coverage_sha256"] = hashlib.sha256(report_path.read_bytes()).hexdigest()
            manifest["total_collected_count"] = len(seen_nodeids)
            manifest["complete"] = not errors
            manifest["tests_passed"] = not errors and not manifest["failed_nodeids"]
    except Exception as error:
        # This is the artifact boundary: even missing coverage/dependencies must leave a failure manifest.
        errors.append(f"combine: {error}")
    finally:
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    summary = {
        key: manifest[key]
        for key in ("complete", "tests_passed", "failed_nodeids", "crashed_nodeids", "unfinished_nodeids", "errors")
    }
    print(json.dumps(summary))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        # Bound both entry counts and lengths, including errors. Full IDs and
        # diagnostics remain in the artifact even for very large parameter sets.
        preview = {}
        for key, value in summary.items():
            if isinstance(value, list):
                preview[f"{key}_count"] = len(value)
                preview[key] = [str(item)[:200] for item in value[:20]]
            else:
                preview[key] = value
        try:
            with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a", encoding="utf-8") as stream:
                stream.write(
                    f"## Coverage measurement for `{sha}`\n\n"
                    "Showing at most 20 entries per list, 200 characters per entry. "
                    "See `coverage-combined/manifest.json` for the full lists.\n\n"
                    f"```json\n{json.dumps(preview, indent=2, ensure_ascii=False)}\n```\n"
                )
        except OSError as error:
            print(f"coverage_ref: could not write step summary: {error}", file=sys.stderr)
    return int(not manifest["complete"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record shard measurements or combine a complete run.\nUse from coverage-ref.yml, not as a CI gate.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  .venv/bin/python scripts/ci/coverage_ref.py run --output raw --shard 1 -- tests/test_example.py\n"
            "  .venv/bin/python scripts/ci/coverage_ref.py combine --input raw --output combined "
            "--sha <40-hex> --matrix-result success\n"
            "Outputs: receipt.json, manifest.json and coverage.json from all valid available data.\n"
            "Exit codes: 0 = complete measurement (tests may fail); 1 = incomplete; 2 = usage error.\n"
            "Requires: GITHUB_RUN_ID, GITHUB_RUN_ATTEMPT, COVERAGE_RCFILE; run also needs the CI duration snapshot.\n"
            "Related: .github/workflows/coverage-ref.yml; scripts/ci/coverage_diff.py; #11226."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Run pytest and record selected node IDs, status, versions and wall time")
    run.add_argument("--output", type=Path, required=True, help="Raw data directory, e.g. ci-artifacts/raw")
    run.add_argument("--shard", type=int, required=True, help="1-based shard number, e.g. 1")
    run.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Arguments after --, e.g. -- tests -n logical")
    merge = sub.add_parser("combine", help="Validate every receipt/data file before combining")
    merge.add_argument("--input", type=Path, required=True, help="Downloaded artifact parent, e.g. ci-artifacts/shards")
    merge.add_argument("--output", type=Path, required=True, help="Report directory, e.g. ci-artifacts/combined")
    merge.add_argument("--sha", required=True, help="Measured 40-hex commit SHA")
    merge.add_argument("--shards", type=int, default=16, help="Required shard count (default: 16), e.g. 16")
    merge.add_argument("--matrix-result", required=True, help="Actions matrix result, e.g. success or failure")
    args = parser.parse_args(argv)
    if args.command == "run":
        pytest_args = args.pytest_args[1:] if args.pytest_args[:1] == ["--"] else args.pytest_args
        return run_shard(args.output, args.shard, pytest_args)
    return combine(args.input, args.output, args.sha, args.shards, args.matrix_result)


if __name__ == "__main__":
    raise SystemExit(main())
