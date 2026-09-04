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
                "open_issue_titles": {"5921": "Private title should be stripped"},
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
    """FX-10 design-only: capabilities/health advertise mutation:false."""
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
    assert "open_issue_titles" not in blob
    assert "sealed_verdict_blob" not in blob


def test_projection_rejects_private_filter_keys(monkeypatch):
    """FX-09: public projection rejects private_endpoint and free-text saved-view keys."""
    cache_invalidate("work:v1:projection")

    def fake_build(**_kwargs):
        return build_projection(_sections_with_canary(), repository_id=REPO)

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)
    bad = client.get("/api/work/v1/projection?q=secret&private_endpoint=http://127.0.0.1:9")
    assert bad.status_code == 400
    assert bad.json()["detail"]["error"] == "invalid_saved_view"


def test_projection_rejects_oversized_repeated_filters(monkeypatch):
    """Endpoint 400 when raw multivalue exceeds the finite per-key domain bound."""
    from scripts.work.schema import FILTER_MAX_RAW_ITEMS

    cache_invalidate("work:v1:projection")

    def fake_build(**_kwargs):
        raise AssertionError("build must not run after oversized filter rejection")

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)
    qs = "&".join(["health=ON_TRACK"] * (FILTER_MAX_RAW_ITEMS["health"] + 1))
    response = client.get(f"/api/work/v1/projection?{qs}")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "invalid_saved_view"
    assert "exceeds max" in detail["message"]

    # Singleton repository_id also 400s on raw repetition.
    dup_repo = client.get(f"/api/work/v1/projection?repository_id={REPO}&repository_id={REPO}")
    assert dup_repo.status_code == 400
    assert dup_repo.json()["detail"]["error"] == "invalid_saved_view"


def test_source_id_filter_echoed_and_schema_valid(monkeypatch):
    """?source_id=public-monitor is accepted and appears in filters_applied."""
    cache_invalidate("work:v1:projection")
    sections = _sections_with_canary()
    builds: list[dict] = []

    def fake_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        builds.append(dict(filters or {}))
        return build_projection(sections, repository_id=REPO, filters=filters, cache_age_s=cache_age_s)

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
        return build_projection(sections, repository_id=REPO, filters=filters, cache_age_s=cache_age_s)

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)

    first = client.get("/api/work/v1/projection?health=ON_TRACK&health=AT_RISK&kind=pr&kind=issue")
    second = client.get("/api/work/v1/projection?health=AT_RISK&health=ON_TRACK&health=AT_RISK&kind=issue&kind=pr")
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
    """FX-02 adjacent: optional section failure degrades the public envelope, not unavailable."""
    cache_invalidate("work:v1:projection")
    sections = _sections_with_canary()
    sections["fleet_reviews"] = SectionResult("fleet_reviews", "timeout", reason="fleet_reviews_timeout")
    sections["streams"] = SectionResult(
        "streams",
        "stale",
        payload={"stale": True, "orphans": [], "multi_homed": [], "pending_native_link": [], "open_total": 0},
        reason="stale",
    )

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
    # Source status must be degraded (NOT unavailable) when core enumerations succeed
    public_source = next(s for s in data["sources"] if s["source_id"] == "public-monitor")
    assert public_source["status"] == "degraded"
    assert public_source["sections"]["fleet_reviews"]["status"] == "timeout"
    assert public_source["sections"]["streams"]["status"] == "stale"
    assert public_source["sections"]["issues"]["status"] == "ok"
    assert public_source["sections"]["prs"]["status"] == "ok"


# ---------------------------------------------------------------------------
# GET /api/work/v1/next — stream-scoped pick list (#6880)
# ---------------------------------------------------------------------------

NEXT_STREAMS = ["atlas-practice", "devops", "infra-harness"]


def _wid(number: int) -> str:
    from scripts.work.relations import issue_work_id

    return issue_work_id(REPO, number)


def _next_sections() -> dict[str, SectionResult]:
    """Fixture with in-stream, other-stream, unscoped, epic, and non-actionable rows."""

    def issue(number: int, title: str, *, body: str = "") -> dict:
        return {
            "number": number,
            "title": title,
            "labels": [],
            "assignees": [],
            "body": body,
            "createdAt": "2026-08-01T00:00:00Z",
            "updatedAt": "2026-08-02T00:00:00Z",
            "url": f"https://github.com/{REPO}/issues/{number}",
            "state": "OPEN",
        }

    return {
        "issues": SectionResult(
            "issues",
            "ok",
            payload=[
                issue(6001, "Blocked infra work", body="blocked by #1"),
                issue(6002, "Blocked atlas work", body="blocked by #2"),
                issue(6003, "Orphan issue"),
                issue(6004, "Multi-homed issue"),
                issue(6005, "Healthy homed infra issue"),
                issue(6900, "Infra epic"),
            ],
            count=6,
        ),
        "prs": SectionResult(
            "prs",
            "ok",
            payload=[
                {
                    "number": 100,
                    "title": "Reviewable PR",
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
                    "headRefName": "feat/next",
                }
            ],
            count=1,
        ),
        "streams": SectionResult(
            "streams",
            "ok",
            payload={
                "generated_at": 1,
                "open_total": 6,
                "streams": {
                    "infra-harness": [6900],
                    "atlas-practice": [6901],
                    "devops": [6902],
                },
                "orphans": [{"number": 6003, "title": "Orphan issue"}],
                "multi_homed": [
                    {
                        "number": 6004,
                        "title": "Multi-homed issue",
                        "streams": ["atlas-practice", "infra-harness"],
                    }
                ],
                "pending_native_link": [],
                "open_stream_membership": {
                    "6001": ["infra-harness"],
                    "6002": ["atlas-practice"],
                    "6005": ["infra-harness"],
                },
                "ok": False,
            },
            count=6,
        ),
        "delegate_active": SectionResult("delegate_active", "ok", payload={"total": 0, "tasks": []}, count=0),
        "delegate_tasks": SectionResult("delegate_tasks", "ok", payload={"total": 0, "tasks": []}, count=0),
        "fleet_reviews": SectionResult("fleet_reviews", "ok", payload={"total": 0, "reviews": []}, count=0),
    }


def _warm_next_cache() -> dict:
    """Build the fixture projection and install it as the unfiltered warm cache."""
    from scripts.api.state_helpers import cache_set
    from scripts.api.work_router import projection_cache_key

    cache_invalidate("work:v1:projection")
    payload = build_projection(_next_sections(), repository_id=REPO)
    cache_set(projection_cache_key({}), payload)
    return payload


def _patch_known_streams(monkeypatch):
    monkeypatch.setattr(work_router, "_known_streams", lambda *_a, **_k: list(NEXT_STREAMS))


def test_next_stream_scoped_queue_and_digest(monkeypatch):
    """Pick list is in-stream only; everything else is digest counts (#6880 point 1/2/6)."""
    _patch_known_streams(monkeypatch)
    _warm_next_cache()

    response = client.get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["stream"] == "infra-harness"
    assert data["capabilities"]["mutation"] is False

    queue_ids = [row["work_id"] for row in data["queue"]]
    # In-stream actionable only: the multi-homed OFF_TRACK row ranks first,
    # then the blocked homed infra issue.
    assert queue_ids == [_wid(6004), _wid(6001)]
    for row in data["queue"]:
        assert row["url"], row
        assert row["safe_next_action"]["code"] not in {"NONE", "OPEN_GITHUB", "INSPECT_UNKNOWN"}
    # Never other-stream, unscoped, non-actionable, or epic rows.
    remote_ids = {row["remote_id"] for row in data["queue"]}
    assert remote_ids.isdisjoint({"6002", "6003", "6005", "6900", "100"})

    digest = data["digest"]
    # atlas-practice: blocked atlas issue + the multi-homed row; devops: zero.
    assert digest["other_streams"]["actionable_counts_by_stream"] == {
        "atlas-practice": 2,
        "devops": 0,
    }
    # Orphan issue + PR have no stream membership: counted, never picked.
    assert digest["unscoped_actionable_count"] == 2
    blockers = digest["other_streams"]["top_blockers"]
    assert len(blockers) == 1
    assert blockers[0]["work_id"] == _wid(6004)
    assert blockers[0]["health"] == "OFF_TRACK"
    assert blockers[0]["action_code"] == "RESOLVE_MULTI_HOME"


def test_next_other_stream_perspective(monkeypatch):
    """Same projection, atlas caller: its own rows in the queue, infra in the digest."""
    _patch_known_streams(monkeypatch)
    _warm_next_cache()

    response = client.get("/api/work/v1/next?stream=atlas-practice")
    assert response.status_code == 200, response.text
    data = response.json()
    queue_ids = [row["work_id"] for row in data["queue"]]
    assert queue_ids == [_wid(6004), _wid(6002)]
    assert data["digest"]["other_streams"]["actionable_counts_by_stream"] == {
        "devops": 0,
        "infra-harness": 2,
    }
    assert data["digest"]["unscoped_actionable_count"] == 2


def test_next_determinism_two_calls_identical(monkeypatch):
    """Two calls over an unchanged projection return identical order (#6880 point 5)."""
    _patch_known_streams(monkeypatch)
    _warm_next_cache()

    first = client.get("/api/work/v1/next?stream=infra-harness")
    second = client.get("/api/work/v1/next?stream=infra-harness")
    assert first.status_code == 200 and second.status_code == 200
    a, b = first.json(), second.json()
    assert [r["work_id"] for r in a["queue"]] == [r["work_id"] for r in b["queue"]]
    a.pop("cache_age_s")
    b.pop("cache_age_s")
    assert a == b


def test_next_limit_bounds(monkeypatch):
    _patch_known_streams(monkeypatch)
    _warm_next_cache()

    top1 = client.get("/api/work/v1/next?stream=infra-harness&limit=1")
    assert top1.status_code == 200
    assert [r["work_id"] for r in top1.json()["queue"]] == [_wid(6004)]
    assert top1.json()["limit"] == 1

    assert client.get("/api/work/v1/next?stream=infra-harness&limit=0").status_code == 422
    assert client.get("/api/work/v1/next?stream=infra-harness&limit=26").status_code == 422
    default = client.get("/api/work/v1/next?stream=infra-harness")
    assert default.status_code == 200
    assert default.json()["limit"] == 7


def test_next_cold_cache_503_never_builds(monkeypatch):
    """Cold cache → 503 building + retry_after_s; /next never triggers a build."""
    _patch_known_streams(monkeypatch)
    cache_invalidate("work:v1:projection")

    def forbidden_build(**_kwargs):
        raise AssertionError("/next must never build the projection")

    monkeypatch.setattr(work_router, "build_public_projection", forbidden_build)
    scheduled: list[str] = []
    monkeypatch.setattr(
        work_router,
        "_get_or_create_build_task",
        lambda key, filters, ctx=None: scheduled.append(key),
    )
    response = client.get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 503, response.text
    # Wire body is the documented inner object (no FastAPI detail wrapper).
    body = response.json()
    assert body["error"] == "building"
    assert body["retry_after_s"] > 0
    assert "detail" not in body
    assert response.headers.get("retry-after") == "3"
    assert scheduled == []
    assert app.state.ctx.stores.work_in_flight == {}


def test_next_stale_cache_served_with_background_refresh(monkeypatch):
    """Expired-but-present cache is served honestly and kicks the single-flight refresh."""
    import time

    from scripts.api.state_helpers import _ttl_cache
    from scripts.api.work_router import projection_cache_key

    _patch_known_streams(monkeypatch)
    payload = _warm_next_cache()
    key = projection_cache_key({})
    _ttl_cache[key] = (time.monotonic() - 45.0, payload)

    called = []

    def fake_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        called.append(True)
        return build_projection(_next_sections(), repository_id=REPO, filters=filters, cache_age_s=cache_age_s)

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)
    response = client.get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["cache_age_s"] >= 30.0
    assert [r["work_id"] for r in data["queue"]] == [_wid(6004), _wid(6001)]
    # The shared single-flight refresh was scheduled (it may or may not have
    # completed and popped itself by the time the response returns).
    assert called or key in app.state.ctx.stores.work_in_flight


def test_next_max_stale_503_when_refresh_never_finishes(monkeypatch):
    """Cache older than NEXT_MAX_STALE_S fails closed with 503 stale (#6890 #3)."""
    import time

    from scripts.api.state_helpers import _ttl_cache
    from scripts.api.work_router import projection_cache_key

    _patch_known_streams(monkeypatch)
    # Drain any leftover single-flight builds from prior cases so a late
    # cache_set cannot rejuvenate the deliberately aged entry below.
    app.state.ctx.stores.work_in_flight.clear()
    payload = _warm_next_cache()
    key = projection_cache_key({})
    age = work_router.NEXT_MAX_STALE_S + 15.0

    scheduled: list[str] = []
    monkeypatch.setattr(
        work_router,
        "_get_or_create_build_task",
        lambda k, filters, ctx=None: scheduled.append(k),
    )
    _ttl_cache[key] = (time.monotonic() - age, payload)
    response = client.get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 503, response.text
    body = response.json()
    assert body["error"] == "stale"
    assert body["max_stale_s"] == work_router.NEXT_MAX_STALE_S
    assert body["cache_age_s"] >= work_router.NEXT_MAX_STALE_S
    assert body["retry_after_s"] > 0
    assert "detail" not in body
    assert response.headers.get("retry-after") == "3"
    assert scheduled == [key]


def test_next_rejects_unknown_and_missing_stream(monkeypatch):
    _patch_known_streams(monkeypatch)
    _warm_next_cache()

    bad = client.get("/api/work/v1/next?stream=not-a-stream")
    assert bad.status_code == 400
    body = bad.json()
    assert body["error"] == "unknown_stream"
    assert body["valid_streams"] == NEXT_STREAMS
    assert "detail" not in body

    assert client.get("/api/work/v1/next").status_code == 422


def test_next_registry_unavailable_503(monkeypatch):
    """Unreadable registry → 503 registry_unavailable, never 200 empty (#6890 #5)."""
    _warm_next_cache()
    monkeypatch.setattr(work_router, "_known_streams", lambda *_a, **_k: None)
    response = client.get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 503, response.text
    body = response.json()
    assert body["error"] == "registry_unavailable"
    assert body["retry_after_s"] > 0
    assert "detail" not in body
    assert "queue" not in body
    assert response.headers.get("retry-after") == "3"


def test_next_known_streams_come_from_registry():
    """_known_streams reflects scripts/config/issue_streams.yaml."""
    from scripts.orchestration.issue_stream_audit import load_registry

    cache_invalidate(work_router.STREAM_REGISTRY_CACHE_KEY)
    names = work_router._known_streams()
    assert names == sorted(load_registry().keys())
    assert "infra-harness" in names


def test_capabilities_advertise_next_queue():
    caps = client.get("/api/work/v1/capabilities")
    assert caps.status_code == 200
    nq = caps.json()["next_queue"]
    assert nq["route"] == "GET /api/work/v1/next"
    assert "stream" in nq["params"] and "limit" in nq["params"]
    assert "default 7, max 25" in nq["params"]["limit"]
    assert "503" in nq["served_from"]
    assert "registry_unavailable" in nq["served_from"]
    assert "stale" in nq["served_from"]


def test_projection_membership_and_epic_status():
    """Homed issues carry public-safe stream membership; epics get status=epic."""
    projection = build_projection(_next_sections(), repository_id=REPO)
    by_id = {i["work_id"]: i for i in projection["items"]}

    homed = by_id[_wid(6001)]["projections"]["stream"]
    assert homed["status"] == "homed"
    assert homed["streams"] == ["infra-harness"]

    epic = by_id[_wid(6900)]["projections"]["stream"]
    assert epic["status"] == "epic"
    assert epic["streams"] == ["infra-harness"]

    orphan = by_id[_wid(6003)]["projections"]["stream"]
    assert orphan["status"] == "orphan"
    assert orphan["streams"] == []


def test_streams_loader_derives_public_membership_and_strips_private_index():
    """fetch_streams_projection derives open-issue→stream names, drops the raw index."""
    from scripts.work.sources_public import fetch_streams_projection

    def loader():
        return {
            "_status": "ok",
            "generated_at": 1,
            "open_total": 1,
            "streams": {"infra-harness": [6900]},
            "orphans": [],
            "multi_homed": [],
            "pending_native_link": [],
            "ok": True,
            "effective_membership": {
                "6001": {
                    "epics": [6900],
                    "streams": ["infra-harness"],
                    "via": "native",
                    "unique_stream": True,
                },
                "5000": {
                    "epics": [6900],
                    "streams": ["infra-harness"],
                    "via": "body",
                    "unique_stream": True,
                },
            },
            "open_issue_numbers": [6001],
            "open_issue_titles": {"6001": "Title 6001"},
        }

    section = fetch_streams_projection(loader=loader)
    assert section.status == "ok"
    assert section.payload["open_stream_membership"] == {"6001": ["infra-harness"]}
    # Closed issue 5000 never surfaces; the private index keys are stripped.
    assert "effective_membership" not in section.payload
    assert "open_issue_numbers" not in section.payload
    assert "open_issue_titles" not in section.payload
    blob = json.dumps(section.payload)
    assert "5000" not in blob
    assert "unique_stream" not in blob
    assert "via" not in blob


def test_streams_loader_allowlists_derived_and_preset_membership():
    """Unknown stream names are dropped at derive time and on pre-set maps (#6890)."""
    from scripts.work.sources_public import fetch_streams_projection

    def loader_with_typo():
        return {
            "_status": "ok",
            "generated_at": 1,
            "open_total": 2,
            "streams": {"infra-harness": [6900]},
            "orphans": [],
            "multi_homed": [
                {
                    "number": 6004,
                    "title": "Multi",
                    "streams": ["infra-harness", "not-a-real-stream"],
                }
            ],
            "pending_native_link": [],
            "ok": True,
            "effective_membership": {
                "6001": {
                    "epics": [6900],
                    "streams": ["infra-harness", "ghost-lane"],
                    "via": "native",
                    "unique_stream": False,
                },
            },
            "open_issue_numbers": [6001, 6004],
            "open_issue_titles": {"6001": "Title 6001", "6004": "Title 6004"},
            # Pre-set map with a typo — must be re-validated, not trusted.
            "open_stream_membership": {
                "6009": ["infra-harness", "typo-stream"],
                "6010": ["only-typo"],
            },
        }

    section = fetch_streams_projection(loader=loader_with_typo)
    assert section.status == "ok"
    # Derived from effective_membership wins and is allowlisted.
    assert section.payload["open_stream_membership"] == {"6001": ["infra-harness"]}
    assert "ghost-lane" not in json.dumps(section.payload["open_stream_membership"])

    def loader_preset_only():
        return {
            "_status": "ok",
            "generated_at": 1,
            "open_total": 1,
            "streams": {"infra-harness": [6900], "devops": [6902]},
            "orphans": [],
            "multi_homed": [],
            "pending_native_link": [],
            "ok": True,
            "open_stream_membership": {
                "6001": ["infra-harness", "not-registered"],
                "6002": ["not-registered"],
            },
        }

    preset = fetch_streams_projection(loader=loader_preset_only)
    assert preset.payload["open_stream_membership"] == {"6001": ["infra-harness"]}

    projection = build_projection(
        {
            **_next_sections(),
            "streams": SectionResult(
                "streams",
                "ok",
                payload={
                    "generated_at": 1,
                    "open_total": 1,
                    "streams": {"infra-harness": [6900]},
                    "orphans": [],
                    "multi_homed": [
                        {
                            "number": 6004,
                            "title": "Multi",
                            "streams": ["infra-harness", "bogus-stream"],
                        }
                    ],
                    "pending_native_link": [],
                    "open_stream_membership": {
                        "6001": ["infra-harness", "bogus-stream"],
                    },
                    "ok": False,
                },
                count=1,
            ),
        },
        repository_id=REPO,
    )
    by_id = {i["work_id"]: i for i in projection["items"]}
    assert by_id[_wid(6001)]["projections"]["stream"]["streams"] == ["infra-harness"]
    assert by_id[_wid(6004)]["projections"]["stream"]["streams"] == ["infra-harness"]
    assert "bogus-stream" not in json.dumps(projection)


# ---------------------------------------------------------------------------
# /next — pending_native membership, stream aliases, refresh liveness (#6984)
# ---------------------------------------------------------------------------


def _pending_issue(number: int, title: str) -> dict:
    return {
        "number": number,
        "title": title,
        "labels": [{"name": "area:infra"}],
        "assignees": [],
        "body": "",
        "createdAt": "2026-08-01T00:00:00Z",
        "updatedAt": "2026-08-02T00:00:00Z",
        "url": f"https://github.com/{REPO}/issues/{number}",
        "state": "OPEN",
    }


def _next_sections_pending(*, membership: bool) -> dict[str, SectionResult]:
    """Fixture with an AT_RISK pending_native (body-homed) infra ticket.

    With ``membership=True`` the streams authority knows the owning lane via
    the epic-body reference (open_stream_membership); with ``False`` the
    ticket is pending with no derivable lane.
    """
    sections = _next_sections()
    issues = list(sections["issues"].payload)
    issues.append(_pending_issue(6006, "Body-homed infra ticket (migration pending)"))
    sections["issues"] = SectionResult("issues", "ok", payload=issues, count=len(issues))
    streams_payload = dict(sections["streams"].payload)
    streams_payload["pending_native_link"] = [6006]
    membership_map = dict(streams_payload.get("open_stream_membership") or {})
    if membership:
        membership_map["6006"] = ["infra-harness"]
    streams_payload["open_stream_membership"] = membership_map
    sections["streams"] = SectionResult("streams", "ok", payload=streams_payload, count=len(issues))
    return sections


def _warm_cache_from(sections: dict[str, SectionResult]) -> dict:
    from scripts.api.state_helpers import cache_set
    from scripts.api.work_router import projection_cache_key

    cache_invalidate("work:v1:projection")
    payload = build_projection(sections, repository_id=REPO)
    cache_set(projection_cache_key({}), payload)
    return payload


def test_next_includes_pending_native_with_body_membership(monkeypatch):
    """#6984: a body-homed pending_native ticket is visible to its owning lane.

    Native sub-issue migration can lag (5 infra tickets resisted --migrate);
    while pending, the epic-body reference IS membership per the registry
    rule. The item keeps status ``pending_native`` (no fake ``homed``) and
    appears in the lane queue with LINK_PENDING_NATIVE.
    """
    _patch_known_streams(monkeypatch)
    _warm_cache_from(_next_sections_pending(membership=True))

    response = client.get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 200, response.text
    data = response.json()
    queue_ids = [row["work_id"] for row in data["queue"]]
    assert _wid(6006) in queue_ids
    row = next(r for r in data["queue"] if r["work_id"] == _wid(6006))
    assert row["health"] == "AT_RISK"
    assert row["safe_next_action"]["code"] == "LINK_PENDING_NATIVE"
    # Scoped, not silently dumped into the unscoped count.
    assert data["digest"]["unscoped_actionable_count"] == 2
    excluded = data["digest"]["excluded_pending_native"]
    assert all(e["work_id"] != _wid(6006) for e in excluded["items"])
    assert excluded["count"] == 0


def test_next_pending_native_status_and_streams_stay_honest():
    """The projection keeps status=pending_native while listing the body-derived lane."""
    projection = build_projection(_next_sections_pending(membership=True), repository_id=REPO)
    by_id = {i["work_id"]: i for i in projection["items"]}
    stream = by_id[_wid(6006)]["projections"]["stream"]
    assert stream["status"] == "pending_native"
    assert stream["streams"] == ["infra-harness"]


def test_next_pending_native_without_membership_is_named_in_digest(monkeypatch):
    """#6984: an unscoped pending_native ticket is listed with a reason, never silent."""
    _patch_known_streams(monkeypatch)
    _warm_cache_from(_next_sections_pending(membership=False))

    response = client.get("/api/work/v1/next?stream=infra-harness")
    assert response.status_code == 200, response.text
    data = response.json()
    assert _wid(6006) not in [row["work_id"] for row in data["queue"]]
    excluded = data["digest"]["excluded_pending_native"]
    assert excluded["count"] == 1
    entry = next(e for e in excluded["items"] if e["work_id"] == _wid(6006))
    assert entry["reason"] == "no_stream_membership"
    assert entry["streams"] == []
    assert entry["title"] == "Body-homed infra ticket (migration pending)"
    # Still honestly counted as unscoped.
    assert data["digest"]["unscoped_actionable_count"] == 3


def test_next_stream_alias_resolves_via_fleet_taxonomy(monkeypatch):
    """#6984: drivers type SESSION_EPIC area names ('infra'); unambiguous aliases work."""
    _patch_known_streams(monkeypatch)
    _warm_next_cache()

    response = client.get("/api/work/v1/next?stream=infra")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["stream"] == "infra-harness"
    assert data["requested_stream"] == "infra"
    assert [r["work_id"] for r in data["queue"]] == [_wid(6004), _wid(6001)]

    # Canonical names still pass through without a requested_stream echo.
    canonical = client.get("/api/work/v1/next?stream=infra-harness")
    assert canonical.status_code == 200
    assert "requested_stream" not in canonical.json()

    # Unknown selectors still fail closed with the valid stream list.
    bad = client.get("/api/work/v1/next?stream=not-a-stream")
    assert bad.status_code == 400
    assert bad.json()["error"] == "unknown_stream"


def test_next_successful_background_refresh_resets_age(monkeypatch):
    """#6984: a kicked refresh that finishes re-warms the cache; the retry is 200."""
    import time

    from scripts.api.state_helpers import _ttl_cache
    from scripts.api.work_router import projection_cache_key

    _patch_known_streams(monkeypatch)
    payload = _warm_next_cache()
    key = projection_cache_key({})
    _ttl_cache[key] = (time.monotonic() - (work_router.NEXT_MAX_STALE_S + 15.0), payload)

    def fake_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        return build_projection(_next_sections(), repository_id=REPO, filters=filters, cache_age_s=cache_age_s)

    monkeypatch.setattr(work_router, "build_public_projection", fake_build)

    first = client.get("/api/work/v1/next?stream=infra-harness")
    assert first.status_code == 503, first.text
    assert first.json()["error"] == "stale"

    # Sync TestClient does not pump request-loop create_task work; wait on the
    # worker-loop future so the 503 stale contract stays and the retry is 200.
    work_router.wait_for_in_flight_build(key)
    second = client.get("/api/work/v1/next?stream=infra-harness")
    assert second.status_code == 200, "refresh never re-warmed the cache"
    assert second.json()["cache_age_s"] < work_router.NEXT_MAX_STALE_S
    assert [r["work_id"] for r in second.json()["queue"]] == [_wid(6004), _wid(6001)]


def test_next_hung_refresh_frees_single_flight_slot(monkeypatch):
    """#6984: a build that never finishes must not wedge the single-flight slot.

    The background build is bounded by NEXT_BUILD_TIMEOUT_S; once it times
    out the slot frees and the next caller's refresh can succeed.
    """
    import time

    from scripts.api.state_helpers import _ttl_cache
    from scripts.api.work_router import projection_cache_key

    _patch_known_streams(monkeypatch)
    payload = _warm_next_cache()
    key = projection_cache_key({})
    _ttl_cache[key] = (time.monotonic() - (work_router.NEXT_MAX_STALE_S + 15.0), payload)
    monkeypatch.setattr(work_router, "NEXT_BUILD_TIMEOUT_S", 0.2)

    def hanging_build(**_kwargs):
        time.sleep(2.0)
        return build_projection(_next_sections(), repository_id=REPO)

    monkeypatch.setattr(work_router, "build_public_projection", hanging_build)
    first = client.get("/api/work/v1/next?stream=infra-harness")
    assert first.status_code == 503, first.text
    assert first.json()["error"] == "stale"

    # The hung build is abandoned at the timeout and the slot frees.
    work_router.wait_for_in_flight_build(key)
    assert key not in app.state.ctx.stores.work_in_flight, "hung build wedged the single-flight slot"

    # A healthy retry rebuilds and serves 200.
    def fast_build(*, filters=None, cache_age_s=0.0, **_kwargs):
        return build_projection(_next_sections(), repository_id=REPO, filters=filters, cache_age_s=cache_age_s)

    monkeypatch.setattr(work_router, "build_public_projection", fast_build)
    retry = client.get("/api/work/v1/next?stream=infra-harness")
    assert retry.status_code == 503, retry.text
    assert retry.json()["error"] == "stale"
    work_router.wait_for_in_flight_build(key)
    second = client.get("/api/work/v1/next?stream=infra-harness")
    assert second.status_code == 200, "slot stayed wedged after the hung build"
    assert second.json()["cache_age_s"] < work_router.NEXT_MAX_STALE_S
