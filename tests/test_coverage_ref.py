"""Incomplete measurements must fail closed; subprocess execution must reach the combined report."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import coverage
import pytest

from scripts.ci.coverage_ref import CollectionRecorder, combine, main, versions

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "scripts/ci/coverage-ref.ini"
SHA = "a" * 40


@pytest.fixture
def measurement(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("COVERAGE_RCFILE", str(CONFIG))
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/a.py").write_text("value = 1\n")
    raw = tmp_path / "raw"
    for shard in (1, 2):
        directory = raw / f"coverage-shard-{shard}"
        directory.mkdir(parents=True)
        data = coverage.CoverageData(basename=str(directory / ".coverage"))
        data.add_arcs({"scripts/a.py": [(-1, 1), (1, -1)]})
        data.write()
        receipt = {
            "sha": SHA,
            "workflow_run_id": "123",
            "workflow_run_attempt": "1",
            "shard": shard,
            "collected_nodeids": [f"tests/test_{shard}.py::test_ok"],
            "collected_count": 1,
            "collection_consistent": True,
            "pytest_exit_status": 0,
            "wall_seconds": 0.1,
            "versions": versions(),
            "core": "ctrace",
            "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
            "durations_sha256": "same-snapshot",
        }
        (directory / "receipt.json").write_text(json.dumps(receipt))
    return raw, tmp_path / "combined"


def test_complete_combination_preserves_all_executed_arcs(measurement):
    raw, output = measurement
    assert combine(raw, output, SHA, 2, "success") == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is True
    assert manifest["total_collected_count"] == 2
    report_path = output / "coverage.json"
    assert manifest["coverage_sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    report = json.loads(report_path.read_text())
    assert report["files"]["scripts/a.py"]["executed_lines"] == [1]
    assert report["files"]["scripts/a.py"]["executed_arcs"] == [[-1, 1], [1, -1]]


@pytest.mark.parametrize(
    "field,value",
    [
        ("sha", "b" * 40),
        ("pytest_exit_status", 1),
        ("collected_count", 0),
        ("collection_consistent", False),
        ("workflow_run_id", "other-run"),
        ("workflow_run_attempt", "2"),
        ("versions", {}),
        ("config_sha256", "changed"),
        ("durations_sha256", "changed"),
        ("shard", 3),
        ("collected_nodeids", ["tests/test_1.py::test_ok"]),
    ],
)
def test_incomplete_or_mixed_shards_never_publish_success(measurement, field, value):
    raw, output = measurement
    path = raw / "coverage-shard-2/receipt.json"
    receipt = json.loads(path.read_text())
    receipt[field] = value
    path.write_text(json.dumps(receipt))
    assert combine(raw, output, SHA, 2, "success") == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is False
    assert manifest["errors"]
    assert not (output / "coverage.json").exists()


@pytest.mark.parametrize("missing", ["receipt.json", ".coverage"])
def test_missing_shard_evidence_is_incomplete(measurement, missing):
    raw, output = measurement
    (raw / "coverage-shard-1" / missing).unlink()
    assert combine(raw, output, SHA, 2, "success") == 1
    assert json.loads((output / "manifest.json").read_text())["complete"] is False


@pytest.mark.parametrize("kind", ["corrupt", "lines_only", "empty"])
def test_invalid_raw_data_cannot_be_skipped_as_success(measurement, kind):
    raw, output = measurement
    path = raw / "coverage-shard-1/.coverage"
    path.unlink()
    if kind == "corrupt":
        path.write_text("broken sqlite")
    else:
        data = coverage.CoverageData(basename=str(path))
        if kind == "lines_only":
            data.add_lines({"scripts/a.py": [1]})
        else:
            data.add_arcs({})
        data.write()
    assert combine(raw, output, SHA, 2, "success") == 1
    assert json.loads((output / "manifest.json").read_text())["complete"] is False


def test_failed_matrix_blocks_even_with_successful_receipts(measurement):
    raw, output = measurement
    assert (
        main(
            [
                "combine",
                "--input",
                str(raw),
                "--output",
                str(output),
                "--sha",
                SHA,
                "--shards",
                "2",
                "--matrix-result",
                "failure",
            ]
        )
        == 1
    )
    assert json.loads((output / "manifest.json").read_text())["errors"] == ["pytest matrix: failure"]


def test_source_reporting_failure_keeps_incomplete_manifest(measurement):
    raw, output = measurement
    Path("scripts/a.py").unlink()
    assert combine(raw, output, SHA, 2, "success") == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is False
    assert "combine:" in manifest["errors"][0]


def test_xdist_collection_recorder_retains_controller_ids():
    recorder = CollectionRecorder()
    recorder.pytest_collection_finish(SimpleNamespace(items=[SimpleNamespace(nodeid="serial::test")]))
    assert recorder.nodeids == ["serial::test"]
    recorder.pytest_xdist_node_collection_finished(None, ["parallel::test"])
    assert recorder.nodeids == ["parallel::test"]
    assert recorder.collections == [["parallel::test"]]


@pytest.mark.parametrize(
    "status,collections,expected",
    [
        (0, [["test_ok"]], 0),
        (1, [["test_fails"]], 1),
        (0, [[]], 1),
        (0, [["test_one"], ["test_other"]], 1),
    ],
)
def test_runner_records_failures_and_rejects_empty_or_inconsistent_collection(
    measurement,
    monkeypatch,
    status,
    collections,
    expected,
):
    """A zero pytest status alone must not certify an empty or inconsistent shard."""
    raw, _ = measurement
    Path("ci-artifacts").mkdir()
    Path("ci-artifacts/pytest-file-durations.json").write_text("{}")
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: SHA)

    def fake_pytest(args, plugins):
        assert args == ["tests", "-n", "2"]
        for ids in collections:
            plugins[0].pytest_xdist_node_collection_finished(None, ids)
        return status

    monkeypatch.setattr(pytest, "main", fake_pytest)
    assert main(["run", "--output", str(raw), "--shard", "1", "--", "tests", "-n", "2"]) == expected
    receipt = json.loads((raw / "receipt.json").read_text())
    assert receipt["collected_count"] == len(collections[-1])
    assert receipt["pytest_exit_status"] == status
    assert receipt["collection_consistent"] == all(ids == collections[-1] for ids in collections)


@pytest.mark.parametrize("fail", [False, True])
def test_real_xdist_and_subprocess_measurement_records_status_and_child_lines(tmp_path, fail):
    """Catch disabled subprocess patching, lost xdist IDs and masked pytest failures."""
    for directory in ("scripts", ".mcp", "agents_extensions", "packages", "ci-artifacts"):
        (tmp_path / directory).mkdir()
    (tmp_path / "scripts/child.py").write_text("child_only = 42\nassert child_only == 42\n")
    (tmp_path / "test_child.py").write_text(
        "import subprocess, sys\n"
        "def test_child():\n"
        "    subprocess.run([sys.executable, '-c', 'import scripts.child'], check=True, timeout=30)\n"
        f"    assert {not fail!r}\n"
    )
    (tmp_path / "ci-artifacts/pytest-file-durations.json").write_text("{}")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Coverage test",
            "-c",
            "user.email=coverage@example.invalid",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "fixture",
        ],
        check=True,
        timeout=30,
    )
    env = {key: value for key, value in os.environ.items() if not key.startswith("COVERAGE_")}
    env.update(
        {
            "COVERAGE_RCFILE": str(CONFIG),
            "COVERAGE_FILE": str(tmp_path / "raw/.coverage"),
            "GITHUB_RUN_ID": "456",
            "GITHUB_RUN_ATTEMPT": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/ci/coverage_ref.py"),
            "run",
            "--output",
            "raw",
            "--shard",
            "1",
            "--",
            "-p",
            "xdist.plugin",
            "-p",
            "pytest_cov",
            "-n",
            "2",
            "--max-worker-restart=0",
            "--cov=scripts",
            "--cov=.mcp",
            "--cov=agents_extensions",
            "--cov=packages",
            "--cov-branch",
            "--cov-report=",
            f"--cov-config={CONFIG}",
            "test_child.py",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == int(fail), result.stdout + result.stderr
    receipt = json.loads((tmp_path / "raw/receipt.json").read_text())
    assert receipt["collected_nodeids"] == ["test_child.py::test_child"]
    assert receipt["collected_count"] == 1
    assert receipt["pytest_exit_status"] == int(fail)
    assert receipt["core"] == "ctrace"
    assert receipt["wall_seconds"] > 0
    data = coverage.CoverageData(basename=str(tmp_path / "raw/.coverage"))
    data.read()
    assert data.has_arcs()
    assert data.lines("scripts/child.py") == [1, 2]
