"""Measurement receipts and fail-closed combination for coverage-ref.yml (#11226)."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import sys
import time
from pathlib import Path


class CollectionRecorder:
    """Retain selected node IDs on the controller, including with xdist workers."""

    def __init__(self) -> None:
        self.nodeids: list[str] = []
        self.collections: list[list[str]] = []

    def pytest_collection_finish(self, session) -> None:
        self.nodeids = [item.nodeid for item in session.items]

    def pytest_xdist_node_collection_finished(self, node, ids) -> None:
        self.collections.append(list(ids))
        self.nodeids = list(ids)


def versions() -> dict[str, str]:
    return {name: importlib.metadata.version(name) for name in ("coverage", "pytest-cov", "pytest")}


def run_shard(output: Path, shard: int, pytest_args: list[str]) -> int:
    import pytest

    output.mkdir(parents=True, exist_ok=True)
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
        "wall_seconds": round(time.monotonic() - started, 3),
        "versions": versions(),
        "core": "ctrace",
        "config_sha256": hashlib.sha256(Path(os.environ["COVERAGE_RCFILE"]).read_bytes()).hexdigest(),
        "durations_sha256": hashlib.sha256(Path("ci-artifacts/pytest-file-durations.json").read_bytes()).hexdigest(),
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return status or int(not consistent or not recorder.nodeids)


def combine(root: Path, output: Path, sha: str, shard_count: int, matrix_result: str) -> int:
    import coverage

    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "sha": sha,
        "workflow_run_id": os.environ["GITHUB_RUN_ID"],
        "workflow_run_attempt": os.environ["GITHUB_RUN_ATTEMPT"],
        "core": "ctrace",
        "subprocess_patch": True,
        "expected_shards": shard_count,
        "matrix_result": matrix_result,
        "versions": versions(),
        "complete": False,
        "shards": [],
        "errors": [],
    }
    errors = manifest["errors"]
    data_files = []
    seen_nodeids: set[str] = set()
    duration_hashes = set()
    config_hash = hashlib.sha256(Path(os.environ["COVERAGE_RCFILE"]).read_bytes()).hexdigest()
    if matrix_result != "success":
        errors.append(f"pytest matrix: {matrix_result}")
    try:
        for shard in range(1, shard_count + 1):
            directory = root / f"coverage-shard-{shard}"
            try:
                receipt = json.loads((directory / "receipt.json").read_text(encoding="utf-8"))
                manifest["shards"].append(receipt)
                if any(
                    receipt.get(key) != manifest[key]
                    for key in ("sha", "workflow_run_id", "workflow_run_attempt", "versions", "core")
                ):
                    raise ValueError("receipt identity/version mismatch")
                if receipt["shard"] != shard or receipt["config_sha256"] != config_hash:
                    raise ValueError("shard/config mismatch")
                if receipt["pytest_exit_status"] != 0 or receipt["collection_consistent"] is not True:
                    raise ValueError("pytest failed or collections differ")
                nodeids = receipt["collected_nodeids"]
                if not nodeids or receipt["collected_count"] != len(nodeids) or len(set(nodeids)) != len(nodeids):
                    raise ValueError("zero or invalid collected count")
                if seen_nodeids.intersection(nodeids):
                    raise ValueError("node IDs overlap another shard")
                seen_nodeids.update(nodeids)
                duration_hashes.add(receipt["durations_sha256"])
                files = list(directory.glob(".coverage*"))
                if not files:
                    raise ValueError("missing raw coverage data")
                nonempty = False
                for path in files:
                    data = coverage.CoverageData(basename=str(path))
                    data.read()
                    if not data.has_arcs():
                        raise ValueError("raw data lacks branch coverage")
                    nonempty = nonempty or bool(data.measured_files())
                if not nonempty:
                    raise ValueError("empty raw coverage data")
                # pytest-cov normally leaves a combined `.coverage`, not `.coverage.*`.
                # Directory discovery in coverage combine ignores that unsuffixed file.
                data_files.extend(str(path) for path in files)
            except (OSError, ValueError, KeyError, TypeError, coverage.CoverageException) as error:
                errors.append(f"shard {shard}: {error}")
        if len(duration_hashes) != 1:
            errors.append("missing or differing duration snapshots")
        if not errors:
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
            manifest["complete"] = True
    except (OSError, ValueError, coverage.CoverageException) as error:
        errors.append(f"combine: {error}")
    finally:
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"complete": manifest["complete"], "errors": errors}))
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
            "Outputs: run writes receipt.json; combine writes manifest.json and, only if complete, coverage.json.\n"
            "Exit codes: 0 = complete success; 1 or pytest status = incomplete; 2 = usage error.\n"
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
