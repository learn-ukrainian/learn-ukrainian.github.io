"""Counts-only census, incomplete denominators and immutable retry evidence."""

from __future__ import annotations

import json
import subprocess

import pytest

from scripts.orchestration import issue_quality_report as report
from scripts.orchestration.fleet_repos import FleetRepo
from tests.test_check_issue_task_quality import COMPLETE, REGISTRY, REPO, audit_report

PUBLIC = FleetRepo("public", REPO, "public", "public-monorepo", True)
PRIVATE = FleetRepo("infra-private", "unit/private", "private", "private-infra")


def summarize(issues, count, membership=None, codes=(), repo=PUBLIC):
    return report.summarize_repository(repo, issues, count, membership, list(codes), REGISTRY)


def test_listing_500_of_612_is_incomplete_independently_of_audit():
    issues = [{"number": n, "title": "", "body": COMPLETE} for n in range(100, 600)]
    membership = audit_report()
    membership["open_total"] = 500
    result = summarize(issues, 612, membership)
    assert result["open_total"] == 612
    assert result["coverage"] == "incomplete"
    assert "listing_truncated" in result["incomplete_codes"]
    assert "listing_count_mismatch" in result["incomplete_codes"]
    assert result["evaluated_total"] == 500


def test_partial_outage_is_unknown_never_zero():
    result = summarize(None, None, codes=["forge_unavailable"], repo=PRIVATE)
    assert result["open_total"] is None
    assert result["coverage"] == "incomplete"
    assert all(v is None for v in result["lanes"]["membership_unknown"].values())


def test_roots_exempt_containers_ordinary_and_counts_reconcile():
    issues = [{"number": n, "body": COMPLETE, "title": ""} for n in [5703, 123, 456]]
    membership = audit_report(native=[123, 456])
    membership["open_total"] = 3
    result = summarize(issues, 3, membership)
    assert result["root_exempt_total"] == 1
    assert result["evaluated_total"] == 2
    assert result["lanes"]["devops"] == dict.fromkeys(report.COUNTERS, 0) | {"open": 3}
    assert result["coverage"] == "complete"


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


@pytest.mark.parametrize(
    "mutate,code",
    [
        (lambda r: r.update(membership_complete=False), "membership_audit_incomplete"),
        (lambda r: r.update(generated_at=0), "membership_audit_stale"),
        (lambda r: r.update(open_total=2), "membership_audit_incomplete"),
    ],
)
def test_audit_incompleteness_never_reports_zero_membership(mutate, code):
    membership = audit_report(native=[123])
    mutate(membership)
    result = summarize([{"number": 123, "body": COMPLETE}], 1, membership)
    assert code in result["incomplete_codes"]
    assert result["lanes"]["membership_unknown"]["open"] == 1
    assert result["lanes"]["membership_unknown"]["missing_epic"] is None


def test_pending_native_and_ambiguous():
    membership = audit_report(body=[123])
    result = summarize([{"number": 123, "body": COMPLETE}], 1, membership)
    assert result["lanes"]["devops"]["pending_native_link"] == 1
    membership["effective_membership"]["123"].update(
        unique_stream=False, epics=[5703, 6943], streams=["devops", "harness"]
    )
    result = summarize([{"number": 123, "body": COMPLETE}], 1, membership)
    assert result["lanes"]["ambiguous"]["missing_epic"] == 1


def test_collection_uses_one_audit_and_independent_count(monkeypatch):
    calls = []
    monkeypatch.setattr(report.github_client, "check_output", lambda *a, **k: '[{"number":123}]')

    def read(name, **kwargs):
        calls.append(name)
        return subprocess.CompletedProcess([], 0, '{"data":{"repository":{"issues":{"totalCount":612}}}}', "")

    monkeypatch.setattr(report, "read", read)
    monkeypatch.setattr(report.audit, "run_audit", lambda *a: calls.append("audit") or audit_report())
    issues, count, _, codes = report.collect_repository(PUBLIC)
    assert issues == [{"number": 123}] and count == 612 and codes == []
    assert calls == ["issue-count", "audit"]
    calls.clear()
    report.collect_repository(PRIVATE)
    assert calls == ["issue-count"]


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

    def build():
        calls.append("build")
        return {"schema": "issue-quality-report.v1", "generated_at": "fixture"}

    first = report.persisted_payload("2026-10-15", root=tmp_path, build=build)
    assert (
        report.persisted_payload("2026-10-15", root=tmp_path, build=lambda: pytest.fail("retry must reuse payload"))
        == first
    )
    path = tmp_path / "batch_state/reports/issue-quality-report-2026-10-15.json"
    assert path.is_file() and path.read_bytes() == first
    assert calls == ["build"]

    def run(command, **kwargs):
        assert path.read_bytes() == kwargs["input"]
        assert command[-1] == "issue-quality-report:2026-10-15"
        assert "epics" in command and "--source" in command
        return subprocess.CompletedProcess(command, 1)

    assert (
        subprocess.run(
            ["git", "check-ignore", "-q", "batch_state/reports/issue-quality-report-test.json"], check=False, timeout=30
        ).returncode
        == 0
    )
    monkeypatch.setattr(report.subprocess, "run", run)
    assert report.publish_payload(first, "2026-10-15", "devops") == 1


def test_build_enumerates_catalog(monkeypatch):
    monkeypatch.setattr(report.fleet_repos, "load_fleet_repos", lambda: {"public": PUBLIC, "infra-private": PRIVATE})
    monkeypatch.setattr(report.audit, "load_registry", lambda *a, **k: REGISTRY)
    monkeypatch.setattr(report, "collect_repository", lambda r: ([], 0, audit_report(), []))
    result = report.build_report()
    assert result["schema"] == "issue-quality-report.v1"
    assert set(result["repositories"]) == {"public", "infra-private"}
    assert len(result["source_sha"]) == 40


def test_report_cli_persists_prints_and_propagates_publish_failure(monkeypatch, capsys):
    calls = []
    payload = b'{"schema":"issue-quality-report.v1"}\n'
    monkeypatch.setattr(report, "persisted_payload", lambda day: calls.append(("persist", day)) or payload)
    monkeypatch.setattr(report, "publish_payload", lambda *a: calls.append(("publish", *a)) or 1)
    assert report.main(["--date", "2026-10-15"]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == "issue-quality-report.v1"
    assert report.main(["--date", "2026-10-15", "--publish", "--sender", "devops"]) == 1
    assert calls[-2:] == [("persist", "2026-10-15"), ("publish", payload, "2026-10-15", "devops")]

    def fail(*a):
        raise RuntimeError("SECRET_EXCEPTION_CANARY")

    monkeypatch.setattr(report, "persisted_payload", fail)
    assert report.main([]) == 1
    assert capsys.readouterr().out.strip() == "issue quality report: checker_error"


def test_checker_error_is_incomplete(monkeypatch):
    def fail(*a, **k):
        raise ValueError("SECRET_CANARY")

    monkeypatch.setattr(report.checker, "score_body", fail)
    result = summarize([{"number": 123}], 1, audit_report())
    assert result["coverage"] == "incomplete"
    assert result["evaluated_total"] == 0
    assert result["incomplete_codes"] == ["checker_error"]
    assert "CANARY" not in json.dumps(result)


def test_collection_rate_limit_never_zeros(monkeypatch):
    def limited(*a, **k):
        raise report.github_client.GitHubRateLimited(2000)

    monkeypatch.setattr(report.github_client, "check_output", limited)
    monkeypatch.setattr(report, "read", limited)
    issues, count, membership, codes = report.collect_repository(PRIVATE)
    assert issues is count is membership is None
    assert set(codes) == {"rate_limited"}
