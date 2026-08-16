"""API integration tests for the public Work projection."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

import scripts.api.work_router as work_router
from scripts.api.main import app
from scripts.api.state_helpers import cache_invalidate
from scripts.work.normalize import build_projection
from scripts.work.sources_public import SectionResult

client = TestClient(app, raise_server_exceptions=False)
REPO = "learn-ukrainian/learn-ukrainian.github.io"


def _sections_with_canary() -> dict[str, SectionResult]:
    return {
        "issues": SectionResult(
            "issues",
            "ok",
            payload=[
                {
                    "number": 5921,
                    "title": "Public issue",
                    "labels": [{"name": "infrastructure"}],
                    "assignees": [{"login": "operator"}],
                    "body": "fx07-private-body-NEVER-PUBLIC-9f3c2a blocked by #1",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "url": f"https://github.com/{REPO}/issues/5921",
                    "state": "OPEN",
                }
            ],
            count=1,
        ),
        "prs": SectionResult(
            "prs",
            "ok",
            payload=[
                {
                    "number": 100,
                    "title": "Public PR",
                    "state": "OPEN",
                    "isDraft": False,
                    "reviewDecision": "REVIEW_REQUIRED",
                    "statusCheckRollup": [{"state": "SUCCESS"}],
                    "mergeStateStatus": "BLOCKED",
                    "labels": [],
                    "assignees": [],
                    "url": f"https://github.com/{REPO}/pull/100",
                    "createdAt": "2026-08-01T00:00:00Z",
                    "updatedAt": "2026-08-02T00:00:00Z",
                    "headRefOid": "deadbeef",
                    "headRefName": "feat/work",
                }
            ],
            count=1,
        ),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "generated_at": 1,
                "open_total": 1,
                "orphans": [{"number": 5921, "title": "Public issue"}],
                "multi_homed": [],
                "pending_native_link": [],
                "ok": False,
                # Inject private keys that public streams API must strip — Work must not reintroduce them.
                "effective_membership": {"5921": {"private": True}},
                "open_issue_numbers": [5921],
            },
            count=1,
        ),
        "delegate_active": SectionResult(
            "delegate_active",
            "ok",
            payload={"total": 0, "tasks": []},
            count=0,
        ),
        "delegate_tasks": SectionResult(
            "delegate_tasks",
            "ok",
            payload={
                "total": 1,
                "tasks": [
                    {
                        "task_id": "task-issue-5921",
                        "agent": "grok",
                        "status": "running",
                        "started_at": "2026-08-16T00:00:00Z",
                        "result": "fx07-secret-token-NEVER-PUBLIC-b71e44",
                        "result_file": "/Users/private-opsec/infra-private/secret-runbook.md",
                    }
                ],
            },
            count=1,
        ),
        "fleet_reviews": SectionResult(
            "fleet_reviews",
            "ok",
            payload={
                "total": 1,
                "reviews": [
                    {
                        "review_id": "rev-100",
                        "repository": REPO,
                        "pr_number": 100,
                        "head_sha": "deadbeef",
                        "gate_kind": "code",
                        "state": "pending",
                        "sealed_verdict_available": True,
                        "sealed_verdict_blob": "SHOULD-NOT-APPEAR",
                    }
                ],
            },
            count=1,
        ),
    }


def test_capabilities_and_health_endpoints():
    caps = client.get("/api/work/v1/capabilities")
    assert caps.status_code == 200
    data = caps.json()
    assert data["mutation"] is False
    assert data["foundation_status"] == "FOUNDATION_COMPLETE"
    assert data["private_source"]["available"] is False
    assert data["private_source"]["reason_if_unavailable"] == "not_configured"
    assert data["github_enumerations_per_refresh"] == 2

    health = client.get("/api/work/v1/health")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    assert health.json()["mutation"] is False


def test_projection_endpoint_with_injected_sources(monkeypatch):
    cache_invalidate("work:v1:projection")
    sections = _sections_with_canary()

    def fake_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        return build_projection(sections, repository_id=REPO, filters=filters, cache_age_s=cache_age_s)

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)

    response = client.get("/api/work/v1/projection?health=AT_RISK&kind=issue")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["schema_version"] == "work-projection.v1"
    assert data["foundation_status"] == "FOUNDATION_COMPLETE"
    assert data["capabilities"]["mutation"] is False
    assert "cache_age_s" in data
    assert data["denominator"]["class4"]["fleet_reviews"] is True
    assert any(s["source_id"] == "private-local-adapter" and s["status"] == "unavailable" for s in data["sources"])
    assert all(item["source_id"] == "public-monitor" for item in data["items"])
    # Filters applied
    assert data.get("filters_applied", {}).get("health") == ["AT_RISK"]

    blob = json.dumps(data)
    assert "fx07-private-body-NEVER-PUBLIC-9f3c2a" not in blob
    assert "fx07-secret-token-NEVER-PUBLIC-b71e44" not in blob
    assert "/Users/private-opsec/" not in blob
    assert "SHOULD-NOT-APPEAR" not in blob
    assert "effective_membership" not in blob
    assert "open_issue_numbers" not in blob
    assert "sealed_verdict_blob" not in blob


def test_projection_rejects_private_filter_keys(monkeypatch):
    cache_invalidate("work:v1:projection")

    def fake_build(**_kwargs):
        return build_projection(_sections_with_canary(), repository_id=REPO)

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)
    bad = client.get("/api/work/v1/projection?q=secret&private_endpoint=http://127.0.0.1:9")
    assert bad.status_code == 400
    assert bad.json()["detail"]["error"] == "invalid_saved_view"


def test_source_id_filter_echoed_and_schema_valid(monkeypatch):
    """?source_id=public-monitor is accepted and appears in filters_applied."""
    cache_invalidate("work:v1:projection")
    sections = _sections_with_canary()
    builds: list[dict] = []

    def fake_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        builds.append(dict(filters or {}))
        return build_projection(
            sections, repository_id=REPO, filters=filters, cache_age_s=cache_age_s
        )

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)
    response = client.get("/api/work/v1/projection?source_id=public-monitor")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["filters_applied"]["source_id"] == ["public-monitor"]
    assert builds and builds[0]["source_id"] == ["public-monitor"]
    assert all(item["source_id"] == "public-monitor" for item in data["items"])


def test_duplicate_multivalue_filters_share_cache_entry(monkeypatch):
    """Reordered/duplicated multivalue query forms must not create distinct cache keys."""
    cache_invalidate("work:v1:projection")
    sections = _sections_with_canary()
    build_count = {"n": 0}

    def fake_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        build_count["n"] += 1
        return build_projection(
            sections, repository_id=REPO, filters=filters, cache_age_s=cache_age_s
        )

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)

    first = client.get(
        "/api/work/v1/projection?health=ON_TRACK&health=AT_RISK&kind=pr&kind=issue"
    )
    second = client.get(
        "/api/work/v1/projection?health=AT_RISK&health=ON_TRACK&health=AT_RISK"
        "&kind=issue&kind=pr"
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert build_count["n"] == 1
    assert first.json()["filters_applied"] == second.json()["filters_applied"]
    assert first.json()["filters_applied"]["health"] == ["AT_RISK", "ON_TRACK"]
    assert first.json()["filters_applied"]["resource_kind"] == ["issue", "pr"]

    # Distinct canonical filters still get their own entry.
    third = client.get("/api/work/v1/projection?health=OFF_TRACK")
    assert third.status_code == 200, third.text
    assert build_count["n"] == 2


def test_independent_degradation_when_one_section_fails(monkeypatch):
    cache_invalidate("work:v1:projection")
    sections = _sections_with_canary()
    sections["fleet_reviews"] = SectionResult(
        "fleet_reviews", "timeout", reason="fleet_reviews_timeout"
    )
    sections["streams"] = SectionResult("streams", "stale", payload={"stale": True, "orphans": [], "multi_homed": [], "pending_native_link": [], "open_total": 0}, reason="stale")

    def fake_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        return build_projection(sections, repository_id=REPO, filters=filters, cache_age_s=cache_age_s)

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)
    response = client.get("/api/work/v1/projection")
    assert response.status_code == 200
    data = response.json()
    # Healthy GH issues still present
    assert data["denominator"]["issues_open"] == 1
    assert data["denominator"]["class4"]["fleet_reviews"] is False
    assert any(o["class"] == "fleet_reviews" for o in data["denominator"]["omissions"])
    assert any(o["class"] == "streams" for o in data["denominator"]["omissions"])
