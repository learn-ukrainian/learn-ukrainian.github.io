"""Counts-only census, incomplete denominators and immutable retry evidence."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from scripts.orchestration import issue_quality_report as report
from scripts.orchestration.fleet_repos import FleetRepo
from tests.test_check_issue_task_quality import HYGIENE, REGISTRY, REPO, audit_report

PUBLIC = FleetRepo("public", REPO, "public", "public-monorepo", True)
PRIVATE = FleetRepo("infra-private", "unit/private", "private", "private-infra")


def summarize(issues, count, membership=None, codes=(), repo=PUBLIC):
    return report.summarize_repository(repo, issues, count, membership, list(codes), REGISTRY)


def test_private_boundary_golden():
    private_issue = {
        "number": 987654321,
        "title": "TITLE_CANARY",
        "body": "BODY_CANARY",
        "labels": [{"name": "LABEL_CANARY"}],
        "author": "AUTHOR_CANARY",
        "url": "URL_CANARY",
    }
    actual = summarize([private_issue], 1, repo=PRIVATE)
    expected = {
        "key": "infra-private",
        "visibility": "private",
        "coverage": "incomplete",
        "incomplete_codes": ["membership_registry_absent"],
        "open_total": 1,
        "evaluated_total": 1,
        "root_exempt_total": 0,
        "lanes": {
            key: {
                "open": int(key == "membership_unknown"),
                "missing_dor": int(key == "membership_unknown"),
                "missing_dod": int(key == "membership_unknown"),
                "malformed_dod": 0,
                "missing_epic": None,
                "pending_native_link": None,
            }
            for key in ("unassigned", "ambiguous", "membership_unknown")
        },
    }
    assert actual == expected
    serialized = json.dumps(actual)
    assert "CANARY" not in serialized and "987654321" not in serialized and "unit/private" not in serialized


def test_visibility_fails_closed_for_unknown_role():
    unknown = FleetRepo("unknown", "unit/other", "other", "public-ish")
    assert summarize([], 0, repo=unknown)["visibility"] == "private"


def stub_collection(monkeypatch, tmp_path, *, count=1, membership=None):
    monkeypatch.setattr(report, "ROOT", tmp_path)
    monkeypatch.setattr(report.checker, "ROOT", tmp_path)
    monkeypatch.setattr(report.github_client, "check_output", lambda *a, **k: '[{"number":123}]')
    monkeypatch.setattr(report, "read", lambda *a, **k: subprocess.CompletedProcess(
        [], 0, json.dumps({"data": {"repository": {"issues": {"totalCount": count}}}}), ""
    ))
    monkeypatch.setattr(report.checker, "registry_for", lambda *a: REGISTRY)
    snapshot = membership if membership is not None else audit_report(body=[123])
    live = Mock(return_value=snapshot)
    monkeypatch.setattr(report.checker, "live_audit", live)
    monkeypatch.setattr(report.audit, "hygiene_warnings", Mock(side_effect=lambda *a, **k: [dict(w) for w in HYGIENE]))
    return live


def test_daily_report_writes_cache_consumed_by_parentless_checker(monkeypatch, tmp_path):
    live = stub_collection(monkeypatch, tmp_path)
    issues, count, membership, codes = report.collect_repository(PUBLIC)
    assert issues == [{"number": 123}] and count == 1 and codes == []
    live.assert_called_once_with(REPO, REGISTRY, root=tmp_path)
    report.audit.hygiene_warnings.assert_called_once_with(tmp_path, {123})
    path = tmp_path / "batch_state/issue_stream_audit.json"
    payload = json.loads(path.read_text())
    assert payload["schema_version"] == 1
    assert payload["generated_at"] == membership["generated_at"]
    assert payload["membership_complete"] is True
    # The Monitor serves this file: keep run_audit's milestone warnings (#10793).
    assert payload["warnings"] == HYGIENE
    monkeypatch.setattr(report.checker, "read_parent", lambda *a: None)
    live.reset_mock()
    assert report.checker.observe_membership({}, REPO, 123) == {
        "status": "PASS", "errors": [], "pending_native_link": True,
    }
    live.assert_not_called()


@pytest.mark.parametrize("count,change", [
    (2, {}), (None, {}), (1, {"open_issue_numbers": [124]}),
    (1, {"membership_complete": False}), (1, {"generated_at": 0}),
])
def test_daily_report_never_publishes_unverified_cache(monkeypatch, tmp_path, count, change):
    stub_collection(monkeypatch, tmp_path, count=count, membership={**audit_report(body=[123]), **change})
    report.collect_repository(PUBLIC)
    assert not (tmp_path / "batch_state/issue_stream_audit.json").exists()


def test_daily_report_cache_failure_is_typed_and_redacted(monkeypatch, tmp_path):
    stub_collection(monkeypatch, tmp_path)

    def fail(*a, **k):
        raise OSError("PRIVATE_CANARY")

    monkeypatch.setattr(report.checker, "write_membership_cache", fail)
    issues, count, membership, codes = report.collect_repository(PUBLIC)
    assert codes == ["membership_audit_cache_write_failed"]
    result = summarize(issues, count, membership, codes)
    assert result["coverage"] == "incomplete"
    assert result["incomplete_codes"] == codes
    assert "CANARY" not in json.dumps(result)


def test_collection_redacts_exception_data(monkeypatch):
    def fail(*a, **k):
        raise RuntimeError("PRIVATE_CANARY_URL/path")

    monkeypatch.setattr(report.github_client, "check_output", fail)
    monkeypatch.setattr(report, "read", fail)
    issues, count, membership, codes = report.collect_repository(PRIVATE)
    result = summarize(issues, count, membership, codes, PRIVATE)
    assert "CANARY" not in json.dumps(result)
    assert result["incomplete_codes"] == ["forge_unavailable", "membership_registry_absent"]


def test_payload_persisted_before_publish_and_reused(tmp_path, monkeypatch):
    calls = []
    day = datetime.now(UTC).date().isoformat()

    def build():
        calls.append("build")
        return {"schema": "issue-quality-report.v1", "generated_at": "fixture"}

    first = report.persisted_payload(day, root=tmp_path, build=build)
    assert (
        report.persisted_payload(day, root=tmp_path, build=lambda: pytest.fail("retry must reuse payload"))
        == first
    )
    path = tmp_path / f"batch_state/reports/issue-quality-report-{day}.json"
    assert path.is_file() and path.read_bytes() == first
    assert calls == ["build"]

    def run(command, **kwargs):
        assert path.read_bytes() == kwargs["input"]
        assert command[-1] == f"issue-quality-report:{day}"
        assert command[0] == str(expected_interpreter)
        assert "epics" in command and "--source" in command
        return subprocess.CompletedProcess(command, 1)

    assert (
        subprocess.run(
            ["git", "check-ignore", "-q", "batch_state/reports/issue-quality-report-test.json"], check=False, timeout=30
        ).returncode
        == 0
    )
    expected_interpreter = report.project_interpreter(report.ROOT)
    monkeypatch.setattr(report.subprocess, "run", run)
    assert report.publish_payload(first, day, "devops") == 1


def test_checker_error_is_incomplete(monkeypatch):
    def fail(*a, **k):
        raise ValueError("SECRET_CANARY")

    monkeypatch.setattr(report.checker, "score_body", fail)
    result = summarize([{"number": 123}], 1, audit_report())
    assert result["coverage"] == "incomplete"
    assert result["evaluated_total"] == 0
    assert result["incomplete_codes"] == ["checker_error"]
    assert "CANARY" not in json.dumps(result)


@pytest.mark.parametrize("day", ["2000-01-01", "9999-01-01"])
def test_other_day_without_saved_payload_refuses_current_snapshot(tmp_path, day):
    with pytest.raises(ValueError, match="only today's report can be prepared"):
        report.persisted_payload(day, root=tmp_path, build=lambda: pytest.fail("must not fetch today's snapshot"))
    assert list((tmp_path / "batch_state/reports").iterdir()) == []


def test_payload_staging_is_atomic_on_destination_filesystem(tmp_path, monkeypatch):
    day = datetime.now(UTC).date().isoformat()
    link = report.os.link
    calls = []

    def publish(source, destination):
        assert source.parent == destination.parent
        assert json.loads(source.read_bytes()) == {"complete": True}
        assert source.stat().st_mode & 0o777 == 0o600
        assert not destination.exists()
        calls.append(destination)
        link(source, destination)

    monkeypatch.setattr(report.os, "link", publish)
    assert report.persisted_payload(day, root=tmp_path, build=lambda: {"complete": True}) == b'{\n  "complete": true\n}\n'
    assert list((tmp_path / "batch_state/reports").iterdir()) == calls


def test_concurrent_payload_winner_is_kept(tmp_path, monkeypatch):
    day = datetime.now(UTC).date().isoformat()

    def publish(source, destination):
        destination.write_bytes(b'{"winner":true}\n')
        raise FileExistsError

    monkeypatch.setattr(report.os, "link", publish)
    assert report.persisted_payload(day, root=tmp_path, build=lambda: {"loser": True}) == b'{"winner":true}\n'
    assert len(list((tmp_path / "batch_state/reports").iterdir())) == 1


def test_payload_write_failure_leaves_no_partial_report(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("storage failure")

    monkeypatch.setattr(report.os, "fsync", fail)
    with pytest.raises(OSError, match="storage failure"):
        report.persisted_payload(datetime.now(UTC).date().isoformat(), root=tmp_path, build=lambda: {"partial": True})
    assert list((tmp_path / "batch_state/reports").iterdir()) == []
