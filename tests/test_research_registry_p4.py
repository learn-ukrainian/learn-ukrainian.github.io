"""ADR-011 P4 — strict adoption gate + registry observability.

Hermetic: every test builds a synthetic registry (and, where needed, a synthetic
issue-stream membership cache and telemetry JSONL) under ``tmp_path``. No GitHub,
network, subprocess, ``sources.db``, or live ``.runtime`` state is touched. The
strict gate and the observability monitor both read a FRESH cache produced by a
separate auditor run — never the network — so these tests inject that cache
directly and monkeypatch ``issue_stream_audit.CACHE_PATH``.

Covers: strict-gate ownership (native/body/wrong/closed/multi-home/missing/stale
cache) and issue-consumer resolution; default ``--check`` unchanged and network
free; lifecycle drift/dead/unverified/deferred/superseded/effective-adoption/zero
denominator; raw-record visibility (not the runtime loader); the telemetry scan's
window bounds, future events, 200/304 dedupe, grace, malformed, unreadable, byte
cap, unknown ids, empty dir; and the endpoint's ungated availability, fail-soft,
privacy allowlist, and window validation.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.audit import check_research_registry as crr
from scripts.orchestration import issue_stream_audit as isa
from scripts.research import consumption
from scripts.research import observability as obs
from scripts.research import registry as reg

client = TestClient(api_main.app, raise_server_exceptions=False)

# A real declared stream epic (core-quality) — validate_registry loads streams from
# the committed issue_streams.yaml, so strict-gate CLI tests use a real epic number.
REAL_EPIC = 4274
NOW = datetime(2026, 7, 11, 12, 0, 0, tzinfo=UTC)


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
def _digest_body(rid: str) -> str:
    return (
        f"# {rid}\n\nSource: https://example.org/{rid}\n\n"
        f"Paraphrase-only compact digest for {rid}. No verbatim passages.\n"
    )


def _make_record(
    root: Path,
    rid: str,
    *,
    state: str = "deferred",
    ownership: dict[str, int] | None = None,
    consumer: dict[str, str] | None = None,
    routing: dict[str, Any] | None = None,
    reason: str | None = None,
    replacement: str | None = None,
    drift: bool = False,
    write_digest: bool = True,
) -> dict[str, Any]:
    digest_rel = f"docs/references/research-digests/{rid}.md"
    if write_digest:
        digest_path = root / digest_rel
        digest_path.parent.mkdir(parents=True, exist_ok=True)
        digest_path.write_text(_digest_body(rid), "utf-8")
    record: dict[str, Any] = {
        "id": rid,
        "title": f"Title {rid}",
        "summary": f"Summary {rid}",
        "content_hash": "sha256:" + "0" * 64,
        "state": state,
        "provenance": {
            "digest": digest_rel,
            "digest_anchor": None,
            "source_url": f"https://example.org/{rid}",
        },
        "routing": routing if routing is not None else {"roles": ["quality"]},
        "cold_start_roles": [],
        "ownership": ownership,
        "consumer": consumer,
        "reason": reason or ("Deferred for the test." if state == "deferred" else None),
        "replacement": replacement,
        "access_class": "tracked-digest",
    }
    if write_digest:
        record["content_hash"] = crr.expected_content_hash(record, root)
        if drift:
            record["content_hash"] = "sha256:" + "1" * 64  # force hash-drift
    return record


def _write_registry(root: Path, records: list[dict[str, Any]]) -> None:
    refs = root / "docs" / "references"
    refs.mkdir(parents=True, exist_ok=True)
    doc = yaml.safe_dump({"schema_version": 1, "records": records}, sort_keys=False, allow_unicode=True)
    (refs / "research-registry.yaml").write_text(doc, "utf-8")


def _stub(root: Path, rel: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# stub\n", "utf-8")


def _write_streams(root: Path, epic: int = REAL_EPIC, stream: str = "core-quality") -> None:
    path = root / "scripts" / "config" / "issue_streams.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"schema_version": 1, "streams": {stream: {"title": stream, "epics": [epic]}}}),
        "utf-8",
    )


def _write_cache(
    root_or_path: Path,
    membership: dict[str, dict] | None,
    *,
    open_numbers: list[int] | None = None,
    age_s: int = 0,
    is_file: bool = False,
) -> Path:
    """Write a membership cache. ``root_or_path`` is the cache file if ``is_file``."""
    cache = root_or_path if is_file else root_or_path / "issue_stream_audit.json"
    # Freshness is judged against real wall-clock (read_membership_index uses
    # time.time()), so stamp from now, not the fixed NOW used for telemetry.
    report: dict[str, Any] = {"generated_at": int(time.time()) - age_s}
    if membership is not None:
        report["effective_membership"] = membership
    if open_numbers is not None:
        report["open_issue_numbers"] = open_numbers
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(report), "utf-8")
    return cache


def _emit(root: Path, day: datetime, **fields: Any) -> None:
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{day:%Y-%m-%d}.jsonl"
    envelope = {"schema_version": 1, "run_id": "run_x", "session_id": "sess_x", "source": "local"}
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({**envelope, **fields}) + "\n")


def _surface(root: Path, ts: datetime, task: str, rid: str) -> None:
    _emit(root, ts, event_type=consumption.SURFACED_EVENT, task_id=task, research_id=rid,
          surface="dispatch", ts=ts.isoformat())


def _consume(root: Path, ts: datetime, task: str, rid: str, status: int = 200) -> None:
    _emit(root, ts, event_type=consumption.CONSUMED_EVENT, task_id=task, research_id=rid,
          surface="record", status=status, ts=ts.isoformat())


# --------------------------------------------------------------------------- #
# 1. Strict adoption gate (CLI) — fresh cache only, fail-closed, offline
# --------------------------------------------------------------------------- #
@pytest.fixture
def strict_root(tmp_path, monkeypatch):
    """A registry root plus a monkeypatched cache path for the strict gate."""
    cache = tmp_path / "cache.json"
    monkeypatch.setattr(isa, "CACHE_PATH", cache)
    return tmp_path, cache


def _run_strict(root: Path, max_age: str = "3600") -> int:
    return crr.main(["--strict-adoption", "--max-age", max_age], project_root=root)


def test_strict_gate_passes_with_verified_ownership(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": True}}, is_file=True)
    assert _run_strict(root) == 0


def test_strict_gate_rejects_wrong_epic(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    # Issue is owned by a DIFFERENT epic than claimed.
    _write_cache(cache, {"9001": {"epics": [1234], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": True}}, is_file=True)
    assert _run_strict(root) == 2


def test_strict_gate_rejects_multi_home(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC], "streams": ["a", "b"],
                                  "via": "native", "unique_stream": False}}, is_file=True)
    assert _run_strict(root) == 2


def test_strict_gate_rejects_closed_or_unknown_issue(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    _write_cache(cache, {}, is_file=True)  # issue not in the index → fail closed
    assert _run_strict(root) == 2


def test_strict_gate_fails_closed_on_missing_cache(strict_root):
    root, _cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    # No cache file written → gate cannot verify → exit 2 (fail closed).
    assert _run_strict(root) == 2


def test_strict_gate_fails_closed_on_stale_cache(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": True}}, age_s=10_000, is_file=True)
    assert _run_strict(root, max_age="3600") == 2


def test_strict_gate_resolves_issue_consumer(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="adopted", consumer={"kind": "issue", "ref": "9001"})
    _write_registry(root, [rec])
    _write_cache(cache, {}, open_numbers=[9001], is_file=True)
    assert _run_strict(root) == 0  # issue consumer resolves against the open set
    # Same registry, issue not open → blocked (unverified issue consumer).
    _write_cache(cache, {}, open_numbers=[1], is_file=True)
    assert _run_strict(root) == 2


def test_default_check_is_unchanged_and_needs_no_cache(strict_root, monkeypatch):
    """The offline --check path never reads the membership cache and never fails on
    a proposed record with plausible (structurally valid) ownership."""
    root, _cache = strict_root
    # Point the cache at a poisoned/raising path — --check must not touch it.
    def _boom(*_a, **_k):  # pragma: no cover - asserts non-invocation
        raise AssertionError("--check must not read the membership cache")

    monkeypatch.setattr(isa, "read_membership_index", _boom)
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    assert crr.main(["--check", "--quiet"], project_root=root) == 0


# --------------------------------------------------------------------------- #
# 2. Observability — lifecycle + adoption (raw records + P1 helpers)
# --------------------------------------------------------------------------- #
@pytest.fixture
def obs_env(tmp_path, monkeypatch):
    """Hermetic observability root: no membership cache, feature flag off."""
    monkeypatch.setattr(isa, "CACHE_PATH", tmp_path / "no-cache.json")
    monkeypatch.delenv(reg.ENV_FLAG, raising=False)
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    return tmp_path


def _monitor(root: Path, **kw: Any) -> dict[str, Any]:
    return obs.build_monitor(root=root, now=NOW, **kw)


def test_one_drift_is_stale_healthy_remains_visible(obs_env):
    root = obs_env
    healthy = _make_record(root, "healthy", state="adopted",
                           consumer={"kind": "path", "ref": "scripts/x.py"})
    _stub(root, "scripts/x.py")
    drifted = _make_record(root, "drifted", state="deferred", drift=True)
    _write_registry(root, [healthy, drifted])
    life = _monitor(root)["lifecycle"]
    assert life["stale"] == ["drifted"]
    assert life["counts"]["total"] == 2  # healthy record stays visible


def test_dead_consumer_detected(obs_env):
    root = obs_env
    rec = _make_record(root, "r1", state="adopted",
                       consumer={"kind": "path", "ref": "scripts/does-not-exist.py"})
    _write_registry(root, [rec])
    m = _monitor(root)
    assert m["dead_consumers"]["dead"] == ["r1"]
    assert m["adoption"]["effective_adopted"] == 0


def test_issue_and_corpus_consumers_are_unverified_not_dead(obs_env):
    root = obs_env
    ri = _make_record(root, "ri", state="adopted", consumer={"kind": "issue", "ref": "4952"})
    rc = _make_record(root, "rc", state="adopted", consumer={"kind": "corpus", "ref": "intake-x"})
    _write_registry(root, [ri, rc])
    m = _monitor(root)
    assert m["dead_consumers"]["unverified"] == ["rc", "ri"]
    assert m["dead_consumers"]["dead"] == []
    assert m["adoption"]["effective_adopted"] == 0  # unverified never counts as effective


def test_effective_adoption_requires_alive_consumer_and_current_hash(obs_env):
    root = obs_env
    ok = _make_record(root, "ok", state="adopted", consumer={"kind": "path", "ref": "scripts/ok.py"})
    _stub(root, "scripts/ok.py")
    stale = _make_record(root, "stale", state="adopted",
                         consumer={"kind": "path", "ref": "scripts/ok.py"}, drift=True)
    _write_registry(root, [ok, stale])
    m = _monitor(root)
    assert m["adoption"]["adopted"] == 2
    assert m["adoption"]["effective_adopted"] == 1  # drifted one excluded despite alive consumer
    assert "stale" in m["lifecycle"]["stale"]


def test_deferred_and_superseded_ids_and_zero_denominator(obs_env):
    root = obs_env
    a = _make_record(root, "a", state="superseded", replacement="b")
    b = _make_record(root, "b", state="superseded", replacement="a")
    _write_registry(root, [a, b])
    m = _monitor(root)
    assert sorted(m["lifecycle"]["superseded"]) == ["a", "b"]
    assert m["adoption"]["eligible_total"] == 0
    assert m["adoption"]["rate"] is None  # zero non-superseded → null rate, no divide error


def test_adoption_rate_over_non_superseded(obs_env):
    root = obs_env
    recs = [
        _make_record(root, "ad", state="adopted", consumer={"kind": "path", "ref": "scripts/a.py"}),
        _make_record(root, "df", state="deferred"),
        _make_record(root, "sup", state="superseded", replacement="ad"),
    ]
    _stub(root, "scripts/a.py")
    _write_registry(root, recs)
    m = _monitor(root)["adoption"]
    assert m["eligible_total"] == 2  # 3 total − 1 superseded
    assert m["rate"] == 0.5


def test_orphaned_vs_ownership_unverified(obs_env):
    root = obs_env
    _write_streams(root)  # declares core-quality epic REAL_EPIC
    # No ownership at all → orphaned.
    orphan = _make_record(root, "orphan", state="proposed", ownership=None)
    # Plausible ownership (declared epic) but no fresh cache → ownership_unverified,
    # NOT falsely orphaned.
    unver = _make_record(root, "unver", state="proposed",
                         ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [orphan, unver])
    life = _monitor(root)["lifecycle"]
    assert life["orphaned"] == ["orphan"]
    assert life["ownership_unverified"] == ["unver"]
    assert life["ownership_cache"] == "missing"


def test_ownership_verified_with_fresh_cache(obs_env, monkeypatch):
    root = obs_env
    _write_streams(root)
    cache = root / "cache.json"
    monkeypatch.setattr(isa, "CACHE_PATH", cache)
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": True}}, is_file=True)
    rec = _make_record(root, "owned", state="proposed",
                       ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    life = _monitor(root)["lifecycle"]
    assert life["orphaned"] == [] and life["ownership_unverified"] == []
    assert life["ownership_cache"] == "fresh"


def test_semantic_invalid_record_stays_visible(obs_env):
    """The monitor reads RAW records: a record the runtime loader would reject
    (superseded with a missing replacement) must still appear in the counts."""
    root = obs_env
    bad = _make_record(root, "bad", state="superseded", replacement="nonexistent")
    _write_registry(root, [bad])
    # load_runtime_safe would hide the whole registry; the monitor does not.
    assert reg.load_runtime_safe(root=root) is None
    m = _monitor(root)
    assert m["lifecycle"]["counts"]["total"] == 1
    assert m["lifecycle"]["counts"]["superseded"] == 1


def test_missing_registry_degrades_safely(obs_env):
    m = _monitor(obs_env)  # no registry written
    assert m["lifecycle"]["status"] == "missing"
    assert m["consumption"]["status"] in {"empty", "ok"}
    assert m["adoption"]["rate"] is None


# --------------------------------------------------------------------------- #
# 3. Observability — consumption telemetry scan
# --------------------------------------------------------------------------- #
def _consumption(root: Path, **kw: Any) -> dict[str, Any]:
    return _monitor(root, **kw)["consumption"]


def test_distinct_pairs_dedupe_across_200_and_304(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _surface(root, NOW - timedelta(hours=3), "task-a", "r1")
    _consume(root, NOW - timedelta(hours=2), "task-a", "r1", status=200)
    _consume(root, NOW - timedelta(hours=1), "task-a", "r1", status=304)  # same pair
    c = _consumption(root)
    assert c["consumed_events"] == 2  # raw events counted
    assert c["consumed_pairs"] == 1  # deduped to one (task,research) pair
    assert c["surfaced_never_consumed"] == 0


def test_surfaced_never_consumed_after_grace(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _surface(root, NOW - timedelta(hours=3), "task-a", "r1")  # old, no consumption
    c = _consumption(root)
    assert c["surfaced_never_consumed"] == 1
    assert c["pending"] == 0


def test_recent_surface_is_pending_within_grace(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _surface(root, NOW - timedelta(minutes=30), "task-a", "r1")  # inside 1h grace
    c = _consumption(root)
    assert c["pending"] == 1
    assert c["surfaced_never_consumed"] == 0


def test_consumption_before_surface_does_not_count(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _consume(root, NOW - timedelta(hours=3), "task-a", "r1", status=200)  # before surface
    _surface(root, NOW - timedelta(hours=2), "task-a", "r1")
    c = _consumption(root)
    # Consumption predates first surface → the pair is surfaced_never_consumed.
    assert c["surfaced_never_consumed"] == 1


def test_window_bounds_exclude_old_and_future(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _surface(root, NOW - timedelta(days=40), "old", "r1")  # outside 30d window
    _surface(root, NOW + timedelta(hours=1), "future", "r1")  # future event
    _surface(root, NOW - timedelta(hours=3), "in", "r1")  # inside
    c = _consumption(root, window_days=30)
    assert c["surfaced_pairs"] == 1  # only the in-window pair


def test_unknown_research_ids_aggregate_only(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "known")])
    _surface(root, NOW - timedelta(hours=3), "t1", "known")
    _surface(root, NOW - timedelta(hours=3), "t2", "ghost-1")  # not in registry
    _surface(root, NOW - timedelta(hours=3), "t3", "ghost-2")
    c = _consumption(root)
    assert "known" in c["per_record"]
    # Unknown ids never appear as keys; only an aggregate with a distinct count.
    assert "ghost-1" not in c["per_record"] and "ghost-2" not in c["per_record"]
    assert c["unknown_research_ids"]["distinct_research_ids"] == 2
    assert c["unknown_research_ids"]["surfaced_pairs"] == 2
    blob = json.dumps(c)
    assert "ghost-1" not in blob and "ghost-2" not in blob


def test_malformed_lines_are_counted_not_fatal(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{NOW:%Y-%m-%d}.jsonl"
    path.write_text("{not json\n[]\n" , "utf-8")  # bad json + non-dict
    _surface(root, NOW - timedelta(hours=3), "t1", "r1")
    c = _consumption(root)
    assert c["malformed_lines"] == 2
    assert c["surfaced_pairs"] == 1  # the good event still counted


def test_unreadable_file_marks_partial(obs_env, monkeypatch):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    (events_dir / f"{NOW:%Y-%m-%d}.jsonl").write_bytes(b"\xff\xfe not utf-8\n")
    c = _consumption(root)
    assert c["unreadable_files"] == 1
    assert c["partial"] is True and c["status"] == "partial"


def test_byte_cap_marks_partial(obs_env, monkeypatch):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    monkeypatch.setattr(obs, "MAX_SCAN_BYTES", 10)  # tiny cap
    _surface(root, NOW - timedelta(hours=3), "task-a", "r1")
    _surface(root, NOW - timedelta(hours=3), "task-b", "r1")
    c = _consumption(root)
    assert c["partial"] is True


def test_empty_events_dir(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    c = _consumption(root)
    assert c["files_scanned"] == 0
    assert c["distinct_pairs"] == 0
    assert c["surfaced_never_consumed"] == 0


# --------------------------------------------------------------------------- #
# 4. Endpoint — ungated availability, fail-soft, privacy, validation
# --------------------------------------------------------------------------- #
@pytest.fixture
def endpoint_root(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setattr(isa, "CACHE_PATH", tmp_path / "no-cache.json")
    return tmp_path


def test_monitor_available_when_discovery_disabled(endpoint_root, monkeypatch):
    monkeypatch.setenv(reg.ENV_FLAG, "false")  # kill switch OFF
    _write_registry(endpoint_root, [_make_record(endpoint_root, "r1", state="deferred")])
    resp = client.get("/api/knowledge/monitor")
    assert resp.status_code == 200
    body = resp.json()
    assert body["discovery_enabled"] is False  # governance survives serving-off
    assert body["lifecycle"]["counts"]["total"] == 1


def test_monitor_reports_discovery_enabled_when_on(endpoint_root, monkeypatch):
    monkeypatch.setenv(reg.ENV_FLAG, "true")
    _write_registry(endpoint_root, [_make_record(endpoint_root, "r1")])
    assert client.get("/api/knowledge/monitor").json()["discovery_enabled"] is True


def test_monitor_fail_soft_on_broken_registry(endpoint_root, monkeypatch):
    monkeypatch.setenv(reg.ENV_FLAG, "false")
    refs = endpoint_root / "docs" / "references"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "research-registry.yaml").write_text("{ this: [is not: valid", "utf-8")
    resp = client.get("/api/knowledge/monitor")
    assert resp.status_code == 200  # never 500
    assert resp.json()["lifecycle"]["status"] in {"unreadable", "invalid"}


def test_monitor_privacy_allowlist_no_sensitive_fields(endpoint_root, monkeypatch):
    monkeypatch.setenv(reg.ENV_FLAG, "false")
    _write_registry(endpoint_root, [_make_record(endpoint_root, "r1")])
    _surface(endpoint_root, datetime.now(UTC) - timedelta(minutes=5),
             "secret-task-id-1234", "r1")
    blob = json.dumps(client.get("/api/knowledge/monitor").json())
    for leak in ("secret-task-id-1234", "run_x", "sess_x", "task_id",
                 "Title r1", "Summary r1", "example.org", "Paraphrase"):
        assert leak not in blob


@pytest.mark.parametrize("bad", [0, 366, -1])
def test_monitor_window_validation(endpoint_root, bad):
    assert client.get("/api/knowledge/monitor", params={"window_days": bad}).status_code == 422


def test_monitor_window_accepts_bounds(endpoint_root, monkeypatch):
    monkeypatch.setenv(reg.ENV_FLAG, "false")
    _write_registry(endpoint_root, [_make_record(endpoint_root, "r1")])
    for wd in (1, 365):
        resp = client.get("/api/knowledge/monitor", params={"window_days": wd})
        assert resp.status_code == 200
        assert resp.json()["window_days"] == wd


# --------------------------------------------------------------------------- #
# 5. Public issues API strips the private membership index
# --------------------------------------------------------------------------- #
def test_issues_streams_strips_private_index(tmp_path, monkeypatch):
    from scripts.api import issues_router

    report = {
        "generated_at": int(NOW.timestamp()),
        "open_total": 3,
        "ok": True,
        "orphans": [],
        "effective_membership": {"5": {"epics": [100], "streams": ["s"], "unique_stream": True}},
        "open_issue_numbers": [5, 100],
    }
    stripped = issues_router._strip_private_index(report)
    assert "effective_membership" not in stripped
    assert "open_issue_numbers" not in stripped
    assert stripped["open_total"] == 3 and stripped["ok"] is True
