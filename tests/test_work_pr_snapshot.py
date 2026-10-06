"""PR refresh cost never belongs to a Work HTTP request (#9832)."""

from __future__ import annotations

import json
import threading
import time
from datetime import timedelta

import pytest

from scripts import github_rest_cache as github_rest
from scripts.work import sources_public as sources
from scripts.work.normalize import build_projection, qualify_pr_snapshot_age
from scripts.work.schema import validate_projection

REPO = sources.DEFAULT_PUBLIC_REPOSITORY


def _sections(prs):
    return {
        "prs": prs,
        "issues": sources.SectionResult("issues", "ok", payload=[]),
        "streams": sources.SectionResult("streams", "ok", payload={"streams": {}}),
        "delegate_active": sources.SectionResult("delegate_active", "ok", payload={"tasks": []}),
        "delegate_tasks": sources.SectionResult("delegate_tasks", "ok", payload={"tasks": []}),
        "fleet_reviews": sources.SectionResult("fleet_reviews", "ok", payload={"reviews": []}),
    }


def _join(snapshot):
    assert snapshot._thread is not None
    snapshot._thread.join(timeout=15)
    assert not snapshot._thread.is_alive()


def test_snapshot_registry_reuses_the_same_inventory():
    first = sources._pr_snapshot(REPO, 1000)
    assert sources._pr_snapshot(REPO, 1000) is first
    assert sources._pr_snapshot(REPO, 10) is not first


def test_40_slow_prs_refresh_off_request_path(monkeypatch):
    """Five slow reads per PR exceed 5s even with eight detail workers."""
    raw = [{"number": n, "state": "open", "head": {"sha": str(n)}, "title": f"PR {n}"} for n in range(1, 41)]
    reads = []
    started = threading.Event()

    def transport(path, headers, timeout):
        reads.append(path)
        started.set()
        time.sleep(0.22)
        if "/pulls?" in path:
            body = raw
        elif "check-runs" in path:
            body = {
                "total_count": 1,
                "check_runs": [{"name": "CI Gate", "status": "completed", "conclusion": "success"}],
            }
        elif "actions/runs" in path:
            body = {"total_count": 0, "workflow_runs": []}
        elif path.endswith("/status"):
            body = {"total_count": 0, "statuses": []}
        elif "/reviews?" in path:
            body = []
        else:
            body = {"mergeable_state": "clean", "requested_reviewers": []}
        return 200, {}, json.dumps(body).encode()

    cache = github_rest.GitHubRestCache(transport=transport, identity="fixture")
    monkeypatch.setattr(github_rest, "shared_cache", lambda: cache)
    snapshot = sources._PRSnapshot(REPO, 1000)
    monkeypatch.setattr(sources, "_pr_snapshot", lambda *_args: snapshot)
    before = time.perf_counter()
    cold = sources.fetch_open_prs(REPO)
    cold_projection = build_projection(_sections(cold), lifecycle_ledgers=[])
    assert time.perf_counter() - before < 5
    assert cold.status == "unavailable" and cold.observed_at is None and cold.age_s is None
    assert cold_projection["denominator"]["omissions"][0]["reason"] == "gh_pr_snapshot_missing"
    assert started.wait(timeout=2)
    thread = snapshot._thread
    try:
        for _ in range(10):
            assert sources.fetch_open_prs(REPO).payload is None
            assert snapshot._thread is thread
    finally:
        _join(snapshot)
    refresh_s = time.perf_counter() - before
    assert refresh_s > 5
    assert len(reads) == 201
    before = time.perf_counter()
    ready = sources.fetch_open_prs(REPO)
    projection = qualify_pr_snapshot_age(build_projection(_sections(ready), lifecycle_ledgers=[]))
    assert time.perf_counter() - before < 5
    assert ready.status == "ok" and ready.count == 40
    assert ready.age_s >= 5
    meta = projection["sources"][0]["sections"]["prs"]
    assert meta["observed_at"] == ready.observed_at and meta["age_s"] >= 5
    assert len(projection["items"]) == 40
    assert {i["safe_next_action"]["code"] for i in projection["items"]} == {"REQUEST_CF_REVIEW"}
    validate_projection(projection)


@pytest.mark.parametrize("failure", [False, True])
def test_refresh_never_publishes_partial_or_reages_old_snapshot(monkeypatch, failure):
    entered = threading.Event()
    release = threading.Event()
    old = [{"number": 1, "statusCheckRollup": []}]
    new = [{"number": n} for n in range(1, 41)]

    def load(*args, **kwargs):
        entered.set()
        assert release.wait(timeout=5)
        if failure:
            raise github_rest.GitHubRestTimeout(60)
        return github_rest.RestPage(new, truncated=True)

    monkeypatch.setattr(github_rest, "list_open_prs", load)
    snapshot = sources._PRSnapshot(REPO, 1000)
    observed = (sources._utc_now() - timedelta(seconds=45)).isoformat()
    snapshot._snapshot = sources.SectionResult("prs", "ok", payload=old, count=1, observed_at=observed)
    try:
        first = snapshot.read()
        assert entered.wait(timeout=2)
        for _ in range(10):
            result = snapshot.read()
            assert result.status == "stale"
            assert result.payload == old and result.count == 1
            assert result.observed_at == observed and result.age_s >= 45
        first.payload.append({"number": 999})
        assert snapshot.read().count == 1
        assert len(snapshot.read().payload) == 1
    finally:
        release.set()
        _join(snapshot)
    result = snapshot.read()
    if failure:
        assert result.status == "stale" and result.observed_at == observed and result.count == 1
    else:
        assert result.status == "truncated" and result.count == 40 and result.truncated
        assert result.observed_at != observed


def test_failed_cold_refresh_is_omitted_and_can_retry(monkeypatch):
    monkeypatch.setattr(github_rest, "list_open_prs", lambda *a, **kw: None)
    snapshot = sources._PRSnapshot(REPO, 1000)
    snapshot.read()
    _join(snapshot)
    missing = snapshot.read()
    assert missing.status == "unavailable" and missing.reason == "gh_pr_refresh_failed"
    assert missing.payload is None and missing.observed_at is None
    monkeypatch.setattr(github_rest, "list_open_prs", lambda *a, **kw: [])
    snapshot._started_at = float("-inf")
    snapshot.read()
    _join(snapshot)
    assert snapshot.read().status == "ok" and snapshot.read().payload == []


def test_snapshot_age_is_requalified_inside_warm_projection(monkeypatch):
    observed = sources._utc_now() - timedelta(seconds=25)
    raw = [{"number": 1, "statusCheckRollup": [{"name": "CI Gate", "conclusion": "SUCCESS"}]}]
    section = sources.SectionResult("prs", "ok", payload=raw, count=1, age_s=25, observed_at=observed.isoformat())
    payload = build_projection(_sections(section), lifecycle_ledgers=[])
    from scripts.work import normalize

    class Clock:
        @staticmethod
        def now(tz):
            return observed + timedelta(seconds=31)

        fromisoformat = staticmethod(sources.datetime.fromisoformat)

    monkeypatch.setattr(normalize, "datetime", Clock)
    qualified = qualify_pr_snapshot_age(payload)
    item = qualified["items"][0]
    assert item["health"] == "UNKNOWN"
    assert item["safe_next_action"]["code"] == "INSPECT_UNKNOWN"
    assert item["projections"]["verification"]["ci_state"] == "unknown"
    assert item["authority"][0]["age_s"] == 31 and item["authority"][0]["stale"]
    assert qualified["sources"][0]["sections"]["prs"]["observed_at"] == observed.isoformat()
    assert qualified["sources"][0]["sections"]["prs"]["status"] == "stale"
    assert payload["items"][0]["safe_next_action"]["code"] == "REQUEST_CF_REVIEW"
    assert payload["sources"][0]["sections"]["prs"]["age_s"] == 25
    validate_projection(qualified)


def test_stale_and_incomplete_prs_stay_unknown_independently():
    rows = [
        {"number": 1, "statusCheckRollup": [{"name": "CI Gate", "conclusion": "SUCCESS"}]},
        {"number": 2, "detailReadComplete": False, "statusCheckRollup": [{"name": "CI Gate", "conclusion": "SUCCESS"}]},
    ]
    section = sources.SectionResult("prs", "ok", payload=rows, count=2)
    projection = build_projection(_sections(section), lifecycle_ledgers=[])
    assert projection["items"][0]["safe_next_action"]["code"] == "REQUEST_CF_REVIEW"
    assert projection["items"][1]["safe_next_action"]["code"] == "INSPECT_UNKNOWN"
    assert projection["items"][1]["health"] == "UNKNOWN"
    assert projection["items"][1]["projections"]["verification"]["ci_state"] == "unknown"
    section.status = "stale"
    stale = build_projection(_sections(section), lifecycle_ledgers=[])
    assert all(i["health"] == "UNKNOWN" for i in stale["items"])
    assert all(i["projections"]["verification"]["ci_state"] == "unknown" for i in stale["items"])
    assert any(o["class"] == "prs" and o["reason"] == "stale" for o in stale["denominator"]["omissions"])
