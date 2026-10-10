"""Timing refresh changes weights, while preserving the full file partition."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

from scripts.ci import split_tests as split


def test_median_uses_observations_without_treating_absent_files_as_zero() -> None:
    assert split.median_durations(
        [
            {"tests/test_a.py": 2, "tests/test_b.py": 100},
            {"tests/test_a.py": 4},
            {"tests/test_a.py": 90},
        ]
    ) == {"tests/test_a.py": 4, "tests/test_b.py": 100}
    assert split.median_durations([]) == {}


def test_invalid_weights_fail_before_assignment() -> None:
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


def test_refresh_filters_failed_foreign_rerun_expired_and_duplicate_artifacts(tmp_path, monkeypatch, capsys) -> None:
    calls = _api(monkeypatch)
    fallback = tmp_path / "old.json"
    fallback.write_text('{"tests/test_a.py": 1, "tests/test_missing.py": 7}')
    output = tmp_path / "new" / "snapshot.json"
    assert split.refresh_durations("owner/repo", fallback, output) == 2
    assert json.loads(output.read_text()) == {"tests/test_a.py": 25, "tests/test_missing.py": 7}
    assert calls[-2:] == ["repos/owner/repo/actions/artifacts/3/zip", "repos/owner/repo/actions/artifacts/2/zip"]
    assert "2 successful merge-group samples" in capsys.readouterr().out


def test_refresh_honors_sample_limit_and_cli(tmp_path, monkeypatch) -> None:
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


def test_unavailable_lookup_uses_fallback_without_echoing_private_error(tmp_path, monkeypatch, capsys) -> None:
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


def test_malformed_download_retains_fallback(tmp_path, monkeypatch) -> None:
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


def test_github_read_is_bounded_and_captures_output(monkeypatch) -> None:
    def run(command, **kwargs):
        assert command == ["gh", "api", "repos/owner/repo/actions/artifacts"]
        assert kwargs == {"check": True, "capture_output": True, "timeout": 30}
        return subprocess.CompletedProcess(command, 0, stdout=b"{}")

    monkeypatch.setattr(split.github_client, "run", run)
    assert split.github_api("repos/owner/repo/actions/artifacts") == b"{}"


def test_refreshed_partition_preserves_every_collected_case_and_history_pin() -> None:
    cases = {f"tests/test_{i}.py": [f"tests/test_{i}.py::test_case[{j}]" for j in range(i + 1)] for i in range(40)}
    durations = {name: float(index * 100) for index, name in enumerate(cases)}
    pinned = [next(iter(cases))]
    shards = split.assign(list(cases), durations, 16, pinned)
    assert shards == split.assign(list(reversed(cases)), durations, 16, pinned)
    executed = [case for shard in shards for name in shard for case in cases[name]]
    expected = [case for values in cases.values() for case in values]
    assert sorted(executed) == sorted(expected) and len(executed) == len(set(executed))
    assert pinned[0] in shards[0]


def test_workflow_uses_committed_weights_and_publishes_after_partition_proof() -> None:
    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
    jobs = yaml.safe_load(workflow.read_text())["jobs"]
    assert "freeze-durations" not in jobs
    assert jobs["pytest"]["needs"] == ["reuse"]
    assert not any("split_tests refresh" in step.get("run", "") for job in jobs.values() for step in job["steps"])
    steps = jobs["pytest-report"]["steps"]
    proof = next(i for i, s in enumerate(steps) if "scripts.ci.pytest_report" in s.get("run", ""))
    record = next(i for i, s in enumerate(steps) if s.get("name") == "Record pytest durations")
    assert proof < record
    assert jobs["ci-gate"]["name"] == "CI Gate"


@pytest.mark.parametrize("failure", [b"not a zip", b"bad json", "download error"])
def test_bad_sample_does_not_hide_later_valid_sample(tmp_path, monkeypatch, failure) -> None:
    _api(monkeypatch)
    valid_api = split.github_api

    def api(endpoint):
        if endpoint.endswith("/3/zip"):
            if failure == "download error":
                raise subprocess.CalledProcessError(1, ["gh"], stderr="private response")
            if failure == b"bad json":
                return _zip(b"{")
            return failure
        return valid_api(endpoint)

    monkeypatch.setattr(split, "github_api", api)
    fallback = tmp_path / "old.json"
    fallback.write_text('{"tests/test_a.py": 1}')
    output = tmp_path / "snapshot.json"
    assert split.refresh_durations("owner/repo", fallback, output, limit=1) == 1
    assert json.loads(output.read_text()) == {"tests/test_a.py": 20}


def _zip(data: bytes, name="pytest-file-durations.json") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name, data)
    return buf.getvalue()


@pytest.mark.parametrize("kind", ["zip", "member", "missing", "invalid"])
def test_archive_rejects_oversize_or_invalid_timing_member(monkeypatch, kind) -> None:
    data = b'{"tests/test_a.py": 3}'
    payload = _zip(data)
    if kind == "zip":
        monkeypatch.setattr(split, "MAX_ARCHIVE_BYTES", len(payload) - 1)
    elif kind == "member":
        monkeypatch.setattr(split, "MAX_MEMBER_BYTES", len(data) - 1)
    elif kind == "missing":
        payload = _zip(data, "other.json")
    else:
        payload = _zip(b'{"tests/test_a.py": true}')
    with pytest.raises(ValueError):
        split.archive_durations(payload)


@pytest.mark.parametrize("oversize", [False, True])
def test_archive_download_is_spooled_and_size_checked(monkeypatch, oversize) -> None:
    payload = _zip(b'{"tests/test_a.py": 3}')
    if oversize:
        monkeypatch.setattr(split, "MAX_ARCHIVE_BYTES", len(payload) - 1)

    def run(command, **kwargs):
        assert command == ["gh", "api", "repos/owner/repo/actions/artifacts/2/zip"]
        assert kwargs["timeout"] == 30 and kwargs["check"] is True
        assert kwargs["max_response_bytes"] == split.MAX_ARCHIVE_BYTES
        assert kwargs["stderr"] == subprocess.PIPE
        assert "capture_output" not in kwargs
        kwargs["stdout"].write(payload)

    monkeypatch.setattr(split.github_client, "run", run)
    if oversize:
        with pytest.raises(ValueError, match="size limit"):
            split.github_api("repos/owner/repo/actions/artifacts/2/zip")
    else:
        assert split.github_api("repos/owner/repo/actions/artifacts/2/zip") == payload


@pytest.mark.parametrize("data", [None, "{", '{"tests/test_x.py": true}', '{"tests/test_x.py": 3}'])
def test_validate_snapshot_cli(tmp_path, capsys, data) -> None:
    snapshot = tmp_path / "snapshot.json"
    if data is not None:
        snapshot.write_text(data)
    valid = data == '{"tests/test_x.py": 3}'
    assert split.main(["validate", str(snapshot)]) == (0 if valid else 1)
    if not valid:
        assert capsys.readouterr().err == "duration snapshot unavailable or invalid\n"


@pytest.mark.parametrize("case", ["negative", "nonfinite", "foreign", "empty"])
def test_record_durations_validates_before_emitting_json(tmp_path, capsys, case) -> None:
    classname, seconds = "tests.test_x", "1"
    if case == "negative":
        seconds = "-1"
    elif case == "nonfinite":
        seconds = "nan"
    elif case == "foreign":
        classname = "other.test_x"
    else:
        classname = ""
    junit = tmp_path / "junit.xml"
    junit.write_text(f'<testsuite><testcase classname="{classname}" time="{seconds}"/></testsuite>')
    with pytest.raises(ValueError):
        split.main(["durations", str(junit)])
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("snapshot_data", [None, "{", '{"tests/test_x.py": false}', '{"tests/test_x.py": 5}'])
def test_workflow_uses_committed_weights_for_missing_or_invalid_snapshot(tmp_path, snapshot_data) -> None:
    workflow = Path(__file__).resolve().parents[2] / ".github/workflows/ci.yml"
    steps = yaml.safe_load(workflow.read_text())["jobs"]["pytest"]["steps"]
    script = next(step["run"] for step in steps if step.get("name") == "Run pytest")
    selection = script[script.index("durations=scripts/") : script.index("git ls-files")]
    snapshot = tmp_path / "snapshot.json"
    if snapshot_data is not None:
        snapshot.write_text(snapshot_data)
    selection = selection.replace("ci-artifacts/pytest-file-durations.json", str(snapshot))
    # Use the test interpreter when executing the runner's stdlib-only probe locally.
    import shlex

    selection = selection.replace("python3", shlex.quote(sys.executable))
    result = subprocess.run(
        ["bash", "-e", "-c", selection + '\nprintf "%s" "$durations"'],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    expected = str(snapshot) if snapshot_data == '{"tests/test_x.py": 5}' else "scripts/ci/pytest-file-durations.json"
    assert result.stdout.endswith(expected)


def test_duplicate_timing_members_are_rejected() -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("pytest-file-durations.json", '{"tests/test_a.py": 3}')
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr("pytest-file-durations.json", '{"tests/test_a.py": 5}')
    with pytest.raises(ValueError, match="one bounded"):
        split.archive_durations(buf.getvalue())


def test_corrupt_compressed_sample_does_not_hide_later_sample(tmp_path, monkeypatch) -> None:
    import zlib

    _api(monkeypatch)
    reader = split.archive_durations
    calls = 0

    def read(payload):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise zlib.error("invalid compressed data")
        return reader(payload)

    monkeypatch.setattr(split, "archive_durations", read)
    fallback = tmp_path / "old.json"
    fallback.write_text('{"tests/test_a.py": 1}')
    output = tmp_path / "snapshot.json"
    assert split.refresh_durations("owner/repo", fallback, output) == 1
    assert json.loads(output.read_text()) == {"tests/test_a.py": 20}


def test_archive_client_bound_maps_to_existing_size_failure(monkeypatch):
    from scripts.common.github_client import Result

    def oversized(*args, **kwargs):
        failure = subprocess.CalledProcessError(1, args[0])
        failure.github_result = Result(status=413, error="github_http_error")
        raise failure
    monkeypatch.setattr(split.github_client, "run", oversized)
    with pytest.raises(ValueError, match="size limit"):
        split.github_api("repos/owner/repo/actions/artifacts/2/zip")
