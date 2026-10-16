"""PR refresh cost never belongs to a Work HTTP request (#9832)."""

from __future__ import annotations

import json
import threading
import time
from datetime import timedelta

import pytest

from scripts import github_rest_cache as github_rest
from scripts.work import sources_public as sources
from scripts.work.normalize import build_projection, downgrade_expired_projection, qualify_pr_snapshot_age
from scripts.work.schema import validate_projection

REPO = sources.DEFAULT_PUBLIC_REPOSITORY


@pytest.mark.parametrize("merged", [False, True])
def test_malformed_rest_pr_rows_are_unknown_not_empty(monkeypatch, merged):
    loader = "list_merged_prs" if merged else "list_open_prs"
    monkeypatch.setattr(github_rest, loader, lambda *_a, **_kw: [{"number": "broken"}])
    snapshot = sources._PRSnapshot(REPO, 1000, merged)
    snapshot._refresh(sources._iso_now())
    snapshot._started_at = time.monotonic()
    section = snapshot.read()
    assert section.status == "unavailable"
    assert section.reason == "gh_pr_refresh_failed"
    assert section.age_s is None and section.observed_at is None
    projection = build_projection(
        _sections(section)
        if not merged
        else {**_sections(sources.SectionResult("prs", "ok", payload=[])), "prs_merged": section}
    )
    validate_projection(projection)
    assert projection["items"] == []
    assert projection["denominator"]["prs_open"] == (0 if merged else None)


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


def test_merged_history_actual_projection_regression():
    """Author fixture: a real merge observation must survive the public join."""
    sections = _sections(sources.SectionResult("prs", "ok", payload=[], count=0))
    sections["prs_merged"] = sources.SectionResult(
        "prs_merged",
        "ok",
        count=1,
        payload=[
            {
                "number": 71,
                "state": "MERGED",
                "mergedAt": "2026-10-14T12:00:00Z",
                "mergeCommit": {"oid": "b" * 40},
                "title": "Merged fixture",
            }
        ],
    )
    projection = build_projection(sections, lifecycle_ledgers=[])
    assert [i["remote_id"] for i in projection["items"]] == ["71"]
    row = projection["items"][0]
    assert row["lifecycle"] == "merged"
    assert row["projections"]["verification"]["merged_at"] == "2026-10-14T12:00:00Z"
    assert row["projections"]["verification"]["merge_commit_sha"] == "b" * 40
    assert row["safe_next_action"]["code"] == "NONE"
    assert row["flags"]["attention"] is False
    assert projection["denominator"]["prs_open"] == 0
    assert projection["sources"][0]["sections"]["prs_merged"]["count"] == 1
    validate_projection(projection)


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


@pytest.mark.parametrize("failure", [None, "timeout", "error", "rate_limit", "shape"])
def test_history_snapshot_is_independent_background_and_atomic(monkeypatch, failure):
    entered = threading.Event()
    release = threading.Event()
    raw = [{"number": 71, "mergedAt": "2026-10-14T12:00:00Z", "state": "MERGED"}]

    def load(*args, **kwargs):
        entered.set()
        assert release.wait(timeout=5)
        if failure == "timeout":
            raise github_rest.GitHubRestTimeout(60)
        if failure in {"error", "rate_limit"}:
            raise github_rest.GitHubRestError("private transport text", status=429 if failure == "rate_limit" else 503)
        if failure == "shape":
            return {}
        return github_rest.RestPage(raw, truncated=True, stale=True, age_seconds=90)

    monkeypatch.setattr(github_rest, "list_merged_prs", load)
    snapshot = sources._PRSnapshot(REPO, 1000, True)
    open_snapshot = sources._PRSnapshot(REPO, 1000)
    monkeypatch.setattr(
        sources, "_pr_snapshot", lambda _repo, _limit, merged=False: snapshot if merged else open_snapshot
    )
    open_snapshot._snapshot = sources.SectionResult("prs", "ok", payload=[{"number": 5}], count=1)
    open_snapshot._started_at = time.monotonic()
    try:
        cold = sources.fetch_merged_prs(REPO)
        assert cold.status == "unavailable" and cold.age_s is None and cold.observed_at is None
        assert entered.wait(timeout=2)
        thread = snapshot._thread
        assert sources.fetch_merged_prs(REPO).payload is None
        assert snapshot._thread is thread
        assert sources.fetch_open_prs(REPO).payload == [{"number": 5}]
    finally:
        release.set()
        _join(snapshot)
    result = snapshot.read()
    if failure:
        assert result.status == "unavailable" and result.payload is None
        assert result.observed_at is None and result.age_s is None
        assert result.reason in {"gh_pr_list_timeout", "gh_pr_refresh_failed", "github_rate_limited"}
        assert "private" not in result.reason
    else:
        assert result.status == "stale" and result.truncated and result.age_s >= 90
        assert result.payload == raw and result.count == 1
    assert sources.fetch_open_prs(REPO).status == "ok"


@pytest.mark.parametrize("failure", ["timeout", "error", "rate_limit"])
@pytest.mark.parametrize("observed_age", [0, 80])
def test_history_failed_refresh_preserves_observation_and_coverage(monkeypatch, failure, observed_age):
    def load(*args, **kwargs):
        if failure == "timeout":
            raise github_rest.GitHubRestTimeout(60)
        raise github_rest.GitHubRestError("hidden", status=429 if failure == "rate_limit" else 503)

    monkeypatch.setattr(github_rest, "list_merged_prs", load)
    snapshot = sources._PRSnapshot(REPO, 1000, True)
    observed = (sources._utc_now() - timedelta(seconds=observed_age)).isoformat()
    snapshot._snapshot = sources.SectionResult(
        "prs_merged",
        "truncated",
        payload=[{"number": 71, "mergedAt": "2026-10-14T12:00:00Z"}],
        count=1,
        truncated=True,
        observed_at=observed,
    )
    snapshot.read()
    _join(snapshot)
    result = snapshot.read()
    assert result.status == "stale" and result.truncated and result.count == 1
    assert result.observed_at == observed and result.age_s >= observed_age
    assert result.reason in {"gh_pr_list_timeout", "gh_pr_refresh_failed", "github_rate_limited"}
    projection = build_projection({**_sections(sources.SectionResult("prs", "ok", payload=[])), "prs_merged": result})
    assert projection["items"][0]["safe_next_action"]["code"] == "NONE"
    omissions = projection["denominator"]["omissions"]
    assert {o["reason"] for o in omissions if o["class"] == "prs_merged"} == {"enumeration_cap", result.reason}


def test_history_snapshot_registry_and_missing_age(monkeypatch):
    first = sources._pr_snapshot(REPO, 1000, True)
    assert sources._pr_snapshot(REPO, 1000, True) is first
    assert sources._pr_snapshot(REPO, 1000) is not first
    snapshot = sources._PRSnapshot(REPO, 1000, True)
    snapshot._started_at = time.monotonic()
    snapshot._snapshot = sources.SectionResult("prs_merged", "ok", payload=[], observed_at=None, age_s=None)
    result = snapshot.read()
    assert result.status == "stale" and result.age_s is None and result.observed_at is None


@pytest.mark.parametrize("open_age,history_age", [(10, 45), (45, 10), (10, None)])
def test_projection_requalifies_history_and_open_ages_separately(open_age, history_age):
    from scripts.work.normalize import downgrade_expired_projection

    now = sources._utc_now()
    sections = _sections(
        sources.SectionResult(
            "prs",
            "ok",
            payload=[{"number": 5, "statusCheckRollup": [{"conclusion": "SUCCESS"}]}],
            count=1,
            observed_at=(now - timedelta(seconds=open_age)).isoformat(),
        )
    )
    sections["prs_merged"] = sources.SectionResult(
        "prs_merged",
        "ok",
        payload=[{"number": 71, "mergedAt": "2026-10-14T12:00:00Z"}],
        count=1,
        observed_at=(now - timedelta(seconds=history_age)).isoformat() if history_age is not None else None,
        age_s=history_age,
    )
    original = build_projection(sections)
    qualified = qualify_pr_snapshot_age(original)
    by_id = {row["remote_id"]: row for row in qualified["items"]}
    assert by_id["71"]["safe_next_action"]["code"] == "NONE"
    assert by_id["71"]["flags"]["attention"] is False
    assert by_id["71"]["projections"]["verification"]["merged_at"] == "2026-10-14T12:00:00Z"
    assert by_id["5"]["safe_next_action"]["code"] == ("REQUEST_CF_REVIEW" if open_age < 30 else "INSPECT_UNKNOWN")
    meta = qualified["sources"][0]["sections"]
    assert meta["prs"]["status"] == ("ok" if open_age < 30 else "stale")
    assert meta["prs_merged"]["status"] == ("ok" if history_age is not None and history_age < 30 else "stale")
    if history_age is None:
        assert by_id["71"]["authority"][0]["age_s"] is None
    assert original["sources"][0]["sections"]["prs_merged"]["status"] == "ok"
    expired = downgrade_expired_projection(qualified, age_s=100, freshness_s=30)
    history = next(row for row in expired["items"] if row["remote_id"] == "71")
    attention = next(row for row in expired["attention"] if row["work_id"] == history["work_id"])
    assert history["safe_next_action"]["code"] == attention["safe_next_action"]["code"] == "NONE"
    assert history["flags"]["attention"] is False
    assert history["projections"]["verification"]["merge_evidence"]["state"] == "unknown"
    validate_projection(expired)


def test_raw_public_merge_observation_reaches_actual_projection(monkeypatch):
    raw = [
        {"number": 71, "state": "closed", "merged_at": "2026-10-14T12:00:00Z", "merge_commit_sha": "b" * 40},
        {"number": 72, "state": "closed", "merged_at": None},
    ]
    cache = github_rest.GitHubRestCache(
        identity="fixture",
        transport=lambda *_args: (200, {}, json.dumps(raw).encode()),
    )
    monkeypatch.setattr(github_rest, "shared_cache", lambda: cache)
    snapshot = sources._PRSnapshot(REPO, 1000, True)
    snapshot.read()
    _join(snapshot)
    result = snapshot.read()
    assert result.status == "ok" and result.count == 1
    projection = build_projection({**_sections(sources.SectionResult("prs", "ok", payload=[])), "prs_merged": result})
    assert [row["remote_id"] for row in projection["items"]] == ["71"]
    row = projection["items"][0]
    assert row["lifecycle"] == "merged" and row["projections"]["verification"]["merged_at"] == raw[0]["merged_at"]
    assert row["projections"]["verification"]["merge_commit_sha"] == raw[0]["merge_commit_sha"]
    assert row["authority"][0]["observed_at"] == result.observed_at
    assert projection["sources"][0]["sections"]["prs_merged"]["observed_at"] == result.observed_at
    assert row["safe_next_action"]["code"] == "NONE"
    validate_projection(projection)


def test_history_empty_success_is_not_missing_and_open_failure_behavior_is_preserved(monkeypatch):
    monkeypatch.setattr(github_rest, "list_merged_prs", lambda *_args, **_kwargs: [])
    history = sources._PRSnapshot(REPO, 1000, True)
    history._refresh(sources._iso_now())
    history._started_at = time.monotonic()
    result = history.read()
    assert result.name == "prs_merged" and result.status == "ok" and result.payload == [] and result.count == 0
    assert result.observed_at is not None and result.age_s is not None

    def fail(*_args, **_kwargs):
        raise github_rest.GitHubRestTimeout(60)

    monkeypatch.setattr(github_rest, "list_open_prs", fail)
    opened = sources._PRSnapshot(REPO, 1000)
    opened._snapshot = sources.SectionResult("prs", "ok", payload=[{"number": 5}], count=1)
    observed = opened._snapshot.observed_at
    opened._refresh(sources._iso_now())
    opened._started_at = time.monotonic()
    result = opened.read()
    # The existing open path retains its still-fresh settled observation.
    assert result.status == "ok" and result.observed_at == observed and result.count == 1
    projection = build_projection({**_sections(result), "prs_merged": history.read()})
    assert projection["sources"][0]["sections"]["prs_merged"]["status"] == "ok"
    assert not any(o["class"] == "prs_merged" for o in projection["denominator"]["omissions"])


@pytest.mark.parametrize("expiry", ["pr_snapshot", "projection_cache"])
def test_expiry_revokes_same_head_sealed_verdict_availability(monkeypatch, expiry):
    from scripts.work import normalize

    observed = sources._utc_now()
    head = "a" * 40
    raw = [
        {
            "number": 1,
            "headRefOid": head,
            "reviewDecision": "APPROVED",
            "statusCheckRollup": [{"name": "CI Gate", "conclusion": "SUCCESS"}],
        }
    ]
    sections = _sections(
        sources.SectionResult(
            "prs",
            "ok",
            payload=raw,
            count=1,
            observed_at=observed.isoformat(),
            age_s=0,
        )
    )
    sections["fleet_reviews"] = sources.SectionResult(
        "fleet_reviews",
        "ok",
        payload={
            "reviews": [
                {
                    "review_id": "same-head",
                    "repository": REPO,
                    "pr_number": 1,
                    "head_sha": head,
                    "state": "completed",
                    "sealed_verdict_available": True,
                }
            ]
        },
    )
    payload = build_projection(sections, lifecycle_ledgers=[])
    assert payload["items"][0]["projections"]["review"]["sealed_verdict_available"] is True

    class Clock:
        @staticmethod
        def now(tz):
            return observed + timedelta(seconds=31)

        fromisoformat = staticmethod(sources.datetime.fromisoformat)

    monkeypatch.setattr(normalize, "datetime", Clock)
    if expiry == "pr_snapshot":
        qualified = qualify_pr_snapshot_age(payload)
    else:
        qualified = downgrade_expired_projection(payload, age_s=31, freshness_s=30)
    validate_projection(qualified)
    pr = qualified["items"][0]
    assert pr["projections"]["review"] == {
        "review_ids": ["same-head"],
        "states": ["completed"],
        "latest_attempt_states": [],
        "sealed_verdict_available": False,
        "review_decision": "UNKNOWN",
    }
    assert pr["projections"]["verification"]["head_sha"] == head
    assert pr["projections"]["verification"]["merge_evidence"]["state"] == "unknown"
    assert pr["health"] == "UNKNOWN"
    assert pr["safe_next_action"]["code"] == "INSPECT_UNKNOWN"
    assert payload["items"][0]["projections"]["review"]["sealed_verdict_available"] is True
    assert payload["items"][0]["projections"]["review"]["review_decision"] == "APPROVED"


@pytest.mark.parametrize("history_first", [False, True])
def test_actual_rest_snapshots_keep_conflicting_observations_unknown(monkeypatch, history_first):
    from datetime import UTC, datetime

    from scripts.work import normalize

    class Clock:
        @staticmethod
        def now(tz):
            return datetime(2026, 10, 16, 6, 0, 2, tzinfo=UTC)

        fromisoformat = staticmethod(datetime.fromisoformat)

    monkeypatch.setattr(normalize, "datetime", Clock)
    monkeypatch.setattr(sources, "_utc_now", lambda: Clock.now(UTC))
    opened = {"number": 7, "state": "open", "head": {"sha": "a" * 40}}
    merged = {"number": 7, "state": "closed", "merged_at": "2026-10-16T06:00:00Z"}
    calls = []

    def transport(path, *_args):
        calls.append(path)
        if "pulls?state=open" in path:
            body = [opened]
        elif "pulls?state=closed" in path:
            body = [merged]
        elif "/pulls/7?" not in path and path.endswith("/pulls/7"):
            body = opened
        elif "check-runs" in path:
            body = {"total_count": 0, "check_runs": []}
        elif path.endswith("/status"):
            body = {"total_count": 0, "statuses": []}
        elif "actions/runs" in path:
            body = {"total_count": 0, "workflow_runs": []}
        else:
            body = []
        return 200, {}, json.dumps(body).encode()

    cache = github_rest.GitHubRestCache(transport=transport, identity="fixture")
    monkeypatch.setattr(github_rest, "shared_cache", lambda: cache)
    snapshots = {kind: sources._PRSnapshot(REPO, 1000, merged=kind) for kind in (False, True)}
    observed = {}
    for index, kind in enumerate((True, False) if history_first else (False, True)):
        observed[kind] = f"2026-10-16T06:00:0{index}Z"
        snapshots[kind]._refresh(observed[kind])
        snapshots[kind]._started_at = time.monotonic()
    opened_section, history_section = snapshots[False].read(), snapshots[True].read()
    assert opened_section.status == history_section.status == "ok"
    sections = {**_sections(opened_section), "prs_merged": history_section}
    payload = qualify_pr_snapshot_age(build_projection(sections, lifecycle_ledgers=[]))
    assert payload["denominator"]["prs_open"] is None
    assert len(payload["items"]) == 1
    row = payload["items"][0]
    assert row["lifecycle"] == "open" and row["safe_next_action"]["code"] == "INSPECT_UNKNOWN"
    assert row["projections"]["verification"]["head_sha"] == "a" * 40
    for name, kind in (("prs", False), ("prs_merged", True)):
        meta = payload["sources"][0]["sections"][name]
        assert meta["count"] == 1 and meta["observed_at"] == observed[kind].replace("Z", "+00:00")
    assert opened_section.payload[0]["state"] == "OPEN"
    assert history_section.payload[0]["state"] == "MERGED"
    assert len([p for p in calls if "pulls?state=" in p]) == 2
    validate_projection(payload)
