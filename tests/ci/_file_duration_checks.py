"""Timing refresh changes weights, while preserving the full file partition."""

from __future__ import annotations

import io
import json
import subprocess
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts.ci import split_tests as split


def check_median_uses_observations_without_treating_absent_files_as_zero() -> None:
    assert split.median_durations(
        [
            {"tests/test_a.py": 2, "tests/test_b.py": 100},
            {"tests/test_a.py": 4},
            {"tests/test_a.py": 90},
        ]
    ) == {"tests/test_a.py": 4, "tests/test_b.py": 100}
    assert split.median_durations([]) == {}


def check_invalid_weights_fail_before_assignment() -> None:
    for value in (
        {},
        [],
        {"other.py": 1},
        {"tests/test_x.py": True},
        {"tests/test_x.py": -1},
        {"tests/test_x.py": float("nan")},
        {"tests/test_x.py": float("inf")},
    ):
        with pytest.raises(ValueError):
            split.validate_durations(value)
    assert split.validate_durations({"tests/test_x.py": 0}) == {"tests/test_x.py": 0}


def _api(monkeypatch: pytest.MonkeyPatch, *, bad_archive: bool = False) -> list[str]:
    calls = []
    runs = [
        dict(
            id=i,
            event="merge_group",
            status="completed",
            conclusion="success",
            run_attempt=1,
            path=".github/workflows/ci.yml",
        )
        for i in range(8, 0, -1)
    ]
    runs[0]["conclusion"] = "failure"
    runs[1]["event"] = "pull_request"
    runs[2]["run_attempt"] = 2
    runs[3]["path"] = "other.yml"
    artifacts = [
        dict(id=i, name=split.TIMING_ARTIFACT, expired=i == 4, workflow_run={"id": i}) for i in range(8, 0, -1)
    ]
    artifacts.append(dict(id=101, name=split.TIMING_ARTIFACT, expired=False, workflow_run={"id": 1}))

    def api(endpoint: str) -> bytes:
        calls.append(endpoint)
        if "/workflows/" in endpoint:
            return json.dumps({"workflow_runs": runs}).encode()
        if "?name=" in endpoint:
            return json.dumps({"artifacts": artifacts}).encode()
        if bad_archive:
            return b"not a zip"
        artifact_id = int(endpoint.split("/")[-2])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as archive:
            archive.writestr("pytest-file-durations.json", json.dumps({"tests/test_a.py": artifact_id * 10}))
        return buf.getvalue()

    monkeypatch.setattr(split, "github_api", api)
    return calls


def check_refresh_filters_failed_foreign_rerun_expired_and_duplicate_artifacts(tmp_path, monkeypatch, capsys) -> None:
    calls = _api(monkeypatch)
    fallback = tmp_path / "old.json"
    fallback.write_text('{"tests/test_a.py": 1, "tests/test_missing.py": 7}')
    output = tmp_path / "new" / "snapshot.json"
    assert split.refresh_durations("owner/repo", fallback, output) == 2
    assert json.loads(output.read_text()) == {"tests/test_a.py": 25, "tests/test_missing.py": 7}
    assert calls[-2:] == ["repos/owner/repo/actions/artifacts/3/zip", "repos/owner/repo/actions/artifacts/2/zip"]
    assert "2 successful merge-group samples" in capsys.readouterr().out


def check_refresh_honors_sample_limit_and_cli(tmp_path, monkeypatch) -> None:
    calls = _api(monkeypatch)
    fallback = tmp_path / "old.json"
    fallback.write_text('{"tests/test_a.py": 1}')
    output = tmp_path / "snapshot.json"
    assert (
        split.main(
            ["refresh", "--repo", "owner/repo", "--fallback", str(fallback), "--output", str(output), "--limit", "1"]
        )
        == 0
    )
    assert json.loads(output.read_text()) == {"tests/test_a.py": 30}
    assert len(calls) == 3


def check_unavailable_lookup_uses_fallback_without_echoing_private_error(tmp_path, monkeypatch, capsys) -> None:
    fallback = tmp_path / "old.json"
    fallback.write_text('{"tests/test_a.py": 1}')
    output = tmp_path / "snapshot.json"

    def unavailable(endpoint):
        raise subprocess.CalledProcessError(1, ["gh"], stderr="private response")

    monkeypatch.setattr(split, "github_api", unavailable)
    assert split.refresh_durations("owner/repo", fallback, output) == 0
    assert json.loads(output.read_text()) == {"tests/test_a.py": 1}
    printed = capsys.readouterr()
    assert "unavailable" in printed.err and "private response" not in printed.err


def check_malformed_download_retains_fallback(tmp_path, monkeypatch) -> None:
    _api(monkeypatch, bad_archive=True)
    fallback = tmp_path / "old.json"
    fallback.write_text('{"tests/test_a.py": 1}')
    output = tmp_path / "snapshot.json"
    assert split.refresh_durations("owner/repo", fallback, output) == 0
    assert json.loads(output.read_text()) == {"tests/test_a.py": 1}
    with pytest.raises(ValueError):
        split.refresh_durations("owner/repo", fallback, output, 0)
    with pytest.raises(ValueError):
        split.refresh_durations("../repo", fallback, output)


def check_github_read_is_bounded_and_captures_output(monkeypatch) -> None:
    def run(command, **kwargs):
        assert command == ["gh", "api", "repos/owner/repo/actions/artifacts"]
        assert kwargs == {"check": True, "capture_output": True, "timeout": 30}
        return subprocess.CompletedProcess(command, 0, stdout=b"{}")

    monkeypatch.setattr(subprocess, "run", run)
    assert split.github_api("repos/owner/repo/actions/artifacts") == b"{}"


def check_refreshed_partition_preserves_every_collected_case_and_history_pin() -> None:
    cases = {f"tests/test_{i}.py": [f"tests/test_{i}.py::test_case[{j}]" for j in range(i + 1)] for i in range(40)}
    durations = {name: float(index * 100) for index, name in enumerate(cases)}
    pinned = [next(iter(cases))]
    shards = split.assign(list(cases), durations, 16, pinned)
    assert shards == split.assign(list(reversed(cases)), durations, 16, pinned)
    executed = [case for shard in shards for name in shard for case in cases[name]]
    expected = [case for values in cases.values() for case in values]
    assert sorted(executed) == sorted(expected) and len(executed) == len(set(executed))
    assert pinned[0] in shards[0]


def check_workflow_freezes_once_and_publishes_after_partition_proof() -> None:
    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
    jobs = yaml.safe_load(workflow.read_text())["jobs"]
    checks = jobs["checks"]
    assert checks["permissions"] == {"contents": "read", "actions": "read"}
    assert any("split_tests refresh" in step.get("run", "") for step in checks["steps"])
    uploads = [step["with"]["name"] for step in checks["steps"] if "upload-artifact@" in step.get("uses", "")]
    assert uploads == ["pytest-duration-snapshot"]
    assert jobs["pytest"]["needs"] == ["reuse", "checks"]
    download = next(step for step in jobs["pytest"]["steps"] if "download-artifact@" in step.get("uses", ""))
    assert download["with"]["name"] == "pytest-duration-snapshot"
    steps = jobs["pytest-report"]["steps"]
    proof = next(i for i, s in enumerate(steps) if "scripts.ci.pytest_report" in s.get("run", ""))
    record = next(i for i, s in enumerate(steps) if s.get("name") == "Record pytest durations")
    assert proof < record
    assert jobs["ci-gate"]["name"] == "CI Gate"
