"""Incomplete measurements must fail closed; subprocess execution must reach the combined report."""

from __future__ import annotations

import ast
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
from scripts.ci.coverage_ref_environment import main as install_environment

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
            "completed_nodeids": [f"tests/test_{shard}.py::test_ok"],
            "failed_nodeids": [],
            "crashed_nodeids": [],
            "collection_errors": [],
            "wall_seconds": 0.1,
            "versions": versions(),
            "core": "CTracer",
            "subprocess_patch": True,
            "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
            "durations_sha256": "same-snapshot",
        }
        (directory / "receipt.json").write_text(json.dumps(receipt))
    return raw, tmp_path / "combined"


def test_failed_test_keeps_both_shards_coverage_and_exact_failure_id(measurement):
    """A test failure must not discard otherwise complete branch measurements."""
    raw, output = measurement
    path = raw / "coverage-shard-2/receipt.json"
    receipt = json.loads(path.read_text())
    receipt.update(pytest_exit_status=1, failed_nodeids=["tests/test_2.py::test_ok"])
    path.write_text(json.dumps(receipt))
    assert combine(raw, output, SHA, 2, "failure") == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is True
    assert manifest["tests_passed"] is False
    assert manifest["failed_nodeids"] == ["tests/test_2.py::test_ok"]
    assert manifest["crashed_nodeids"] == []
    assert json.loads((output / "coverage.json").read_text())["files"]["scripts/a.py"]["executed_lines"] == [1]


def test_crash_keeps_surviving_data_but_names_unfinished_tests(measurement):
    """A crashed worker cannot certify completeness or erase healthy worker data."""
    raw, output = measurement
    path = raw / "coverage-shard-2/receipt.json"
    receipt = json.loads(path.read_text())
    receipt.update(
        pytest_exit_status=1,
        completed_nodeids=[],
        crashed_nodeids=["tests/test_2.py::test_ok"],
    )
    path.write_text(json.dumps(receipt))
    assert combine(raw, output, SHA, 2, "failure") == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is False
    assert manifest["crashed_nodeids"] == ["tests/test_2.py::test_ok"]
    assert manifest["unfinished_nodeids"] == ["tests/test_2.py::test_ok"]
    assert (output / "coverage.json").is_file()


def test_recorder_distinguishes_teardown_failures_and_worker_crashes():
    """Setup/teardown failures and synthetic xdist crash reports need exact IDs."""
    recorder = CollectionRecorder()
    for nodeid, when, failed in [
        ("test_ok", "teardown", False),
        ("test_bad", "setup", True),
        ("test_bad", "teardown", False),
    ]:
        recorder.pytest_runtest_logreport(SimpleNamespace(nodeid=nodeid, when=when, failed=failed))
    recorder.pytest_handlecrashitem("test_crash", None, None)
    assert recorder.completed_nodeids == {"test_ok", "test_bad"}
    assert recorder.failed_nodeids == {"test_bad"}
    assert recorder.crashed_nodeids == {"test_crash"}
    recorder.pytest_collectreport(SimpleNamespace(nodeid="test_import.py", failed=True))
    recorder.pytest_collectreport(SimpleNamespace(nodeid="test_ok.py", failed=False))
    assert recorder.collection_errors == ["test_import.py"]


def test_environment_installation_uses_only_disposable_interpreter_site(tmp_path, monkeypatch):
    """The copied startup module must load through .pth without relying on PYTHONPATH."""
    monkeypatch.setattr("scripts.ci.coverage_ref_environment.sysconfig.get_paths", lambda: {"purelib": str(tmp_path)})
    install_environment([])
    env = {key: value for key, value in os.environ.items() if not key.startswith("COVERAGE_")}
    env["COVERAGE_FILE"] = str(tmp_path / ".coverage")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import site, sys; site.addsitedir({str(tmp_path)!r}); "
            "assert getattr(sys.addaudithook, 'coverage_ref', False)",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr


def test_environment_help_cannot_install_into_the_running_interpreter():
    """Help must exit before the installer can mutate site-packages."""
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/ci/coverage_ref_environment.py"), "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "do not install in a shared venv" in result.stdout


def test_corrupt_worker_file_cannot_discard_healthy_data_in_the_same_shard(measurement):
    """One interrupted SQLite write must leave the other workers' arcs reportable."""
    raw, output = measurement
    (raw / "coverage-shard-1/.coverage.corrupt").write_text("interrupted")
    assert combine(raw, output, SHA, 2, "success") == 1
    assert json.loads((output / "manifest.json").read_text())["complete"] is False
    assert json.loads((output / "coverage.json").read_text())["files"]["scripts/a.py"]["executed_lines"] == [1]


@pytest.mark.parametrize(
    "operation",
    [
        "pass",
        "open('forbidden', 'w')",
        "__import__('os').remove(__import__('os').environ['COVERAGE_FILE'] + '.forged')",
        "__import__('sqlite3').connect(__import__('os').environ['COVERAGE_FILE'] + '.forged')",
    ],
)
def test_import_audit_keeps_child_arcs_without_allowing_source_writes(tmp_path, operation):
    """Coverage's atexit storage must coexist with the actual import-smoke guard."""
    guard_tree = ast.parse((ROOT / "tests/test_source_ingest_entrypoints.py").read_text())
    guard = next(
        ast.literal_eval(node.value)
        for node in guard_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "OFFLINE_GUARD" for target in node.targets)
    )
    (tmp_path / "private").mkdir()
    (tmp_path / "raw").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/child.py").write_text("child_only = 42\nassert child_only == 42\n")
    (tmp_path / "guard.py").write_text(guard)
    program = (
        "import coverage, runpy\n"
        f"runpy.run_path({str(ROOT / 'scripts/ci/coverage_ref_environment.py')!r})['install']()\n"
        "cov = coverage.Coverage(branch=True, source=['scripts'], config_file=False)\n"
        "cov.start()\n"
        "exec(open('guard.py').read())\n"
        "import scripts.child\n"
        "try:\n"
        f"    {operation}\n"
        "except RuntimeError as exc:\n"
        "    print(str(exc))\n"
        "cov.stop()\n"
        "cov.save()\n"
    )
    env = {key: value for key, value in os.environ.items() if not key.startswith("COVERAGE_")}
    env.update(
        COVERAGE_FILE=str(tmp_path / "raw/.coverage"), TMPDIR=str(tmp_path / "private"), PYTHONDONTWRITEBYTECODE="1"
    )
    result = subprocess.run(
        [sys.executable, "-c", program], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Traceback" not in result.stderr
    assert result.stdout == (
        ""
        if operation == "pass"
        else "IMPORT_SMOKE_BLOCKED_WRITE: "
        + ("open" if operation.startswith("open") else "os.remove" if "remove" in operation else "sqlite3.connect")
        + "\n"
    )
    data = coverage.CoverageData(basename=str(tmp_path / "raw/.coverage"))
    data.read()
    child = str(tmp_path / "scripts/child.py")
    assert data.lines(child) == [1, 2]
    assert data.arcs(child) == [(-1, 1), (1, 2), (2, -1)]
    assert not (tmp_path / "forbidden").exists()
    assert not (tmp_path / "raw/.coverage.forged").exists()


def test_complete_combination_preserves_all_executed_arcs(measurement):
    raw, output = measurement
    assert combine(raw, output, SHA, 2, "success") == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is True
    assert manifest["core"] == "CTracer"
    assert manifest["subprocess_patch"] is True
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
        ("core", "PyTracer"),
        ("subprocess_patch", False),
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
    # The surviving valid shard is useful, but its partial report is never complete.
    assert (output / "coverage.json").is_file()


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
    assert (output / "coverage.json").is_file()


def test_source_reporting_failure_keeps_incomplete_manifest(measurement):
    raw, output = measurement
    Path("scripts/a.py").unlink()
    assert combine(raw, output, SHA, 2, "success") == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is False
    assert "combine:" in manifest["errors"][0]


@pytest.mark.parametrize("missing", ["coverage", "metadata", "config"])
def test_prepare_or_dependency_failure_still_writes_incomplete_manifest(measurement, monkeypatch, missing):
    """Combine must leave a manifest even before coverage imports/configuration succeed."""
    raw, output = measurement
    if missing == "coverage":
        result = subprocess.run(
            [
                sys.executable,
                "-S",
                str(ROOT / "scripts/ci/coverage_ref.py"),
                "combine",
                "--input",
                str(raw),
                "--output",
                str(output),
                "--sha",
                SHA,
                "--matrix-result",
                "skipped",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 1, result.stdout + result.stderr
    else:
        if missing == "metadata":

            def missing_version(name):
                from importlib.metadata import PackageNotFoundError

                raise PackageNotFoundError(name)

            monkeypatch.setattr("scripts.ci.coverage_ref.importlib.metadata.version", missing_version)
        else:
            monkeypatch.setenv("COVERAGE_RCFILE", "missing.ini")
        assert combine(raw, output, SHA, 2, "skipped") == 1
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["complete"] is False
    assert manifest["core"] is None
    assert manifest["subprocess_patch"] is None
    assert manifest["errors"][0] == "pytest matrix: skipped"
    assert manifest["errors"][1].startswith("combine:")
    assert not (output / "coverage.json").exists()


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
        (1, [["test_fails"]], 0),
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
        plugins[0].core = "CTracer"
        plugins[0].subprocess_patch = True
        for ids in collections:
            plugins[0].pytest_xdist_node_collection_finished(None, ids)
            plugins[0].completed_nodeids.update(ids)
            if status:
                plugins[0].failed_nodeids.update(ids)
        return status

    monkeypatch.setattr(pytest, "main", fake_pytest)
    assert main(["run", "--output", str(raw), "--shard", "1", "--", "tests", "-n", "2"]) == expected
    receipt = json.loads((raw / "receipt.json").read_text())
    assert receipt["collected_count"] == len(collections[-1])
    assert receipt["pytest_exit_status"] == status
    assert receipt["collection_consistent"] == all(ids == collections[-1] for ids in collections)


@pytest.mark.parametrize(
    "fail,core,patch,expected",
    [
        (False, "ctrace", "subprocess", 0),
        (True, "ctrace", "subprocess", 0),
        ("crash", "ctrace", "subprocess", 1),
        ("timeout", "ctrace", "subprocess", 0),
        (False, "pytrace", "subprocess", 1),
        (False, "ctrace", "", 1),
    ],
)
def test_real_xdist_and_subprocess_measurement_records_status_and_child_lines(tmp_path, fail, core, patch, expected):
    """Catch disabled subprocess patching, lost xdist IDs and masked pytest failures."""
    for directory in ("scripts", ".mcp", "agents_extensions", "packages", "ci-artifacts"):
        (tmp_path / directory).mkdir()
    (tmp_path / "scripts/child.py").write_text("child_only = 42\nassert child_only == 42\n")
    extra_test = ""
    if fail == "crash":
        extra_test = "\ndef test_crash():\n    __import__('os')._exit(17)\n"
    elif fail == "timeout":
        extra_test = (
            "\nimport pytest\n@pytest.mark.timeout(0.1, method='signal')\n"
            "def test_timeout():\n    __import__('time').sleep(5)\n"
        )
    (tmp_path / "test_child.py").write_text(
        "import subprocess, sys\n"
        "def test_child():\n"
        "    subprocess.run([sys.executable, '-c', 'import scripts.child'], check=True, timeout=30)\n"
        f"    assert {fail is not True!r}\n" + extra_test
    )
    (tmp_path / "ci-artifacts/pytest-file-durations.json").write_text("{}")
    config = tmp_path / "coverage.ini"
    config.write_text(
        CONFIG.read_text().replace("core = ctrace", f"core = {core}").replace("patch = subprocess", f"patch = {patch}")
    )
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
            "COVERAGE_RCFILE": str(config),
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
            "-p",
            "pytest_timeout",
            "-n",
            "2",
            "--max-worker-restart=0",
            "--cov=scripts",
            "--cov=.mcp",
            "--cov=agents_extensions",
            "--cov=packages",
            "--cov-branch",
            "--cov-report=",
            f"--cov-config={config}",
            "test_child.py",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    receipt = json.loads((tmp_path / "raw/receipt.json").read_text())
    expected_ids = ["test_child.py::test_child"]
    if extra_test:
        expected_ids.append(f"test_child.py::test_{fail}")
    assert receipt["collected_nodeids"] == expected_ids
    assert receipt["collected_count"] == len(expected_ids)
    assert receipt["pytest_exit_status"] == int(bool(fail))
    assert receipt["crashed_nodeids"] == (["test_child.py::test_crash"] if fail == "crash" else [])
    expected_failed = (
        ["test_child.py::test_child"]
        if fail is True
        else (["test_child.py::test_timeout"] if fail == "timeout" else [])
    )
    assert receipt["failed_nodeids"] == expected_failed
    assert receipt["completed_nodeids"] == (expected_ids[:1] if fail == "crash" else expected_ids)
    if fail == "crash":
        assert any(item["unexpected"] and item["returncode"] == 17 for item in receipt["worker_exits"])
    assert receipt["core"] == ("CTracer" if core == "ctrace" else "PyTracer")
    assert receipt["subprocess_patch"] is bool(patch)
    assert receipt["wall_seconds"] > 0
    data = coverage.CoverageData(basename=str(tmp_path / "raw/.coverage"))
    data.read()
    assert data.has_arcs() is bool(patch)
    assert data.lines("scripts/child.py") == ([1, 2] if patch else [])
