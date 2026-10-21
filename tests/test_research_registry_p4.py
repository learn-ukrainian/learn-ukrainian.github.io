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
import sys
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


def _ctx_with_live_repo_root(live_repo_root: Path):
    """Redirect live repo root for HTTP calls through ``client``.

    ``knowledge_router`` resolves registry roots from MonitorContext (#7269 step 12c),
    so tests swap ``app.state.ctx``.
    """
    base = api_main.app.state.ctx
    root = Path(live_repo_root)
    return base.with_roots(live_repo_root=root)


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
    report: dict[str, Any] = {
        "generated_at": int(time.time()) - age_s,
        "membership_complete": True,
        "incomplete_nodes": [],
    }
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
    _emit(
        root,
        ts,
        event_type=consumption.SURFACED_EVENT,
        task_id=task,
        research_id=rid,
        surface="dispatch",
        ts=ts.isoformat(),
    )


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
    _write_cache(
        cache,
        {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"], "via": "native", "unique_stream": True}},
        is_file=True,
    )
    assert _run_strict(root) == 0


def test_strict_gate_accepts_closed_uniquely_owned_record_ownership(strict_root):
    """Regression for the unlp-2026-cefr-assessment gate bug (PR #4998
    corrective pass, item 1-3): record OWNERSHIP proof can be historical. An
    issue that is uniquely owned by the claimed epic but is CLOSED (absent
    from ``open_issue_numbers``) must still pass ownership — closing the
    implementation issue does not retroactively un-own the record."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    # 9001 is uniquely owned but NOT in open_issue_numbers — i.e. closed.
    _write_cache(
        cache,
        {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"], "via": "native", "unique_stream": True}},
        open_numbers=[],
        is_file=True,
    )
    assert _run_strict(root) == 0


def test_strict_gate_rejects_same_closed_issue_as_issue_consumer(strict_root):
    """The SAME closed-but-uniquely-owned issue that passes record ownership
    (previous test) must still fail as an issue-CONSUMER: consumer liveness
    additionally requires the ref to be open, not just uniquely owned
    (PR #4998 corrective pass, item 3)."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="adopted", consumer={"kind": "issue", "ref": "9001"})
    _write_registry(root, [rec])
    _write_cache(
        cache,
        {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"], "via": "native", "unique_stream": True}},
        open_numbers=[],
        is_file=True,
    )
    assert _run_strict(root) == 2


def test_strict_gate_rejects_same_stream_two_epic_ownership(strict_root):
    """Native membership in TWO epics of the SAME stream is still ambiguous —
    ``unique_stream`` requires exactly one EFFECTIVE epic, not merely one
    stream name (codex/gemini review, PR #4998)."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    _write_cache(
        cache,
        {"9001": {"epics": [REAL_EPIC, 4969], "streams": ["core-quality"], "via": "native", "unique_stream": False}},
        is_file=True,
    )
    assert _run_strict(root) == 2


def test_strict_gate_rejects_wrong_epic(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    # Issue is owned by a DIFFERENT epic than claimed.
    _write_cache(
        cache,
        {"9001": {"epics": [1234], "streams": ["core-quality"], "via": "native", "unique_stream": True}},
        is_file=True,
    )
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
    _write_cache(
        cache,
        {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"], "via": "native", "unique_stream": True}},
        age_s=10_000,
        is_file=True,
    )
    assert _run_strict(root, max_age="3600") == 2


def test_strict_gate_fails_closed_on_incomplete_cache(strict_root):
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    report = {
        "generated_at": int(time.time()),
        "effective_membership": {
            "9001": {"epics": [REAL_EPIC], "streams": ["core-quality"], "via": "native", "unique_stream": True}
        },
        "open_issue_numbers": [9001],
        "membership_complete": False,
        "incomplete_nodes": [20],
    }
    cache.write_text(json.dumps(report), "utf-8")
    assert _run_strict(root, max_age="3600") == 2


def test_strict_gate_resolves_issue_consumer(strict_root):
    """An adopted ``issue`` consumer must be open AND uniquely owned by exactly
    one effective epic — being merely present in the open-issue set is not
    enough (codex/gemini review, PR #4998)."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="adopted", consumer={"kind": "issue", "ref": "9001"})
    _write_registry(root, [rec])
    owned_entry = {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"], "via": "native", "unique_stream": True}}
    _write_cache(cache, owned_entry, open_numbers=[9001], is_file=True)
    assert _run_strict(root) == 0  # open AND uniquely owned → resolves
    # Same registry, issue open but NOT owned by any stream (orphan) → blocked.
    _write_cache(cache, {}, open_numbers=[9001], is_file=True)
    assert _run_strict(root) == 2
    # Same registry, issue not open at all → blocked.
    _write_cache(cache, owned_entry, open_numbers=[1], is_file=True)
    assert _run_strict(root) == 2


def test_strict_gate_resolves_corpus_consumer_via_atlas_registry(strict_root):
    """The corpus resolver is real: it resolves a genuinely declared Atlas
    intake source family and rejects a dangling one — no cache required."""
    root, cache = strict_root
    _write_cache(cache, {}, is_file=True)
    ok = _make_record(root, "ok", state="adopted", consumer={"kind": "corpus", "ref": "textbook"})
    _write_registry(root, [ok])
    assert _run_strict(root) == 0

    dangling = _make_record(root, "dangling", state="adopted", consumer={"kind": "corpus", "ref": "not-a-real-family"})
    _write_registry(root, [dangling])
    assert _run_strict(root) == 2


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
    healthy = _make_record(root, "healthy", state="adopted", consumer={"kind": "path", "ref": "scripts/x.py"})
    _stub(root, "scripts/x.py")
    drifted = _make_record(root, "drifted", state="deferred", drift=True)
    _write_registry(root, [healthy, drifted])
    life = _monitor(root)["lifecycle"]
    assert life["stale"] == ["drifted"]
    assert life["counts"]["total"] == 2  # healthy record stays visible


def test_degraded_telemetry_fallback_preserves_unknown_ids_schema(obs_env, monkeypatch):
    """When the telemetry scan itself raises, ``build_monitor`` degrades to a
    safe fallback payload -- but that fallback must expose the SAME response
    schema as the normal path, in particular
    ``consumption.unknown_research_ids.distinct_research_ids`` (zero on
    fallback), not a payload missing the key entirely (ADR-011 P4 review,
    item 4)."""
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])

    def _boom(*_a, **_k):
        raise RuntimeError("telemetry scan exploded")

    monkeypatch.setattr(obs, "_scan_telemetry", _boom)
    m = _monitor(root)
    consumption_view = m["consumption"]
    assert consumption_view["status"] == "error"
    assert consumption_view["unknown_research_ids"]["distinct_research_ids"] == 0
    # Same keys as a healthy _blank_record_agg()-derived bucket -- the fallback
    # must not silently drop fields a real scan would always include.
    assert set(consumption_view["unknown_research_ids"]) == set(obs._blank_unknown_agg())


def test_broken_provenance_counts_invalid_never_effective_adoption(obs_env):
    """Broken provenance (missing digest file) is semantic-invalid REGARDLESS of
    the claimed lifecycle state: it must count as invalid, stay visible in
    invalid_provenance, and never be misreported as merely current (not stale)
    or count toward adopted/effective adoption (ADR-011 P4 review)."""
    root = obs_env
    _stub(root, "scripts/x.py")
    broken = _make_record(
        root, "broken", state="adopted", consumer={"kind": "path", "ref": "scripts/x.py"}, write_digest=False
    )
    healthy = _make_record(root, "healthy", state="adopted", consumer={"kind": "path", "ref": "scripts/x.py"})
    _write_registry(root, [broken, healthy])
    m = _monitor(root)
    assert m["lifecycle"]["invalid_provenance"] == ["broken"]
    assert m["lifecycle"]["counts"]["invalid"] == 1
    assert m["lifecycle"]["counts"]["adopted"] == 1  # only "healthy" counted
    assert m["lifecycle"]["stale"] == []  # never misreported as merely "current"/stale
    assert m["adoption"]["adopted"] == 1
    assert m["adoption"]["effective_adopted"] == 1
    assert "broken" not in m["dead_consumers"]["dead"]
    assert "broken" not in m["dead_consumers"]["unverified"]


def test_invalid_raw_ids_counted_anonymously_never_echoed(obs_env):
    """Only schema-valid slug ids may appear in the public monitor payload.
    Missing/non-string/oversized/secret-like/non-slug raw ids — and non-dict
    record entries — are dropped BEFORE lifecycle classification and folded
    into an anonymous count; the raw value is never echoed (ADR-011 P4 review)."""
    root = obs_env
    good = _make_record(root, "good", state="deferred")
    bad_id_dict = _make_record(root, "placeholder", state="deferred")
    bad_id_dict["id"] = "SECRET-Key-ABCDEFG"  # not a valid slug (uppercase)
    non_string_id = _make_record(root, "placeholder2", state="deferred")
    non_string_id["id"] = 12345
    empty_id = _make_record(root, "placeholder3", state="deferred")
    empty_id["id"] = ""
    records = [good, bad_id_dict, non_string_id, empty_id, "not-even-a-dict"]
    refs = root / "docs" / "references"
    refs.mkdir(parents=True, exist_ok=True)
    doc = yaml.safe_dump({"schema_version": 1, "records": records}, sort_keys=False, allow_unicode=True)
    (refs / "research-registry.yaml").write_text(doc, "utf-8")

    m = _monitor(root)
    assert m["lifecycle"]["counts"]["total"] == 1  # only "good" is schema-valid
    assert m["lifecycle"]["invalid_ids"] == 4
    blob = json.dumps(m)
    assert "SECRET-Key-ABCDEFG" not in blob
    assert "not-even-a-dict" not in blob
    assert "placeholder2" not in blob and "placeholder3" not in blob


# --------------------------------------------------------------------------- #
# 3. Observability — consumption telemetry scan
# --------------------------------------------------------------------------- #
def _consumption(root: Path, **kw: Any) -> dict[str, Any]:
    return _monitor(root, **kw)["consumption"]


def test_malformed_lines_are_counted_not_fatal(obs_env):
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{NOW:%Y-%m-%d}.jsonl"
    path.write_text("{not json\n[]\n", "utf-8")  # bad json + non-dict
    _surface(root, NOW - timedelta(hours=3), "t1", "r1")
    c = _consumption(root)
    assert c["malformed_lines"] == 2
    assert c["surfaced_pairs"] == 1  # the good event still counted


def test_scan_is_newest_first_and_nulls_negative_under_partial_coverage(obs_env, monkeypatch):
    """Byte cap must hide OLDER days, not newer ones — the most recent surface
    survives — and a scan that skipped part of the window must never assert a
    definitive ``surfaced_never_consumed`` (ADR-011 P4 review, item 8)."""
    root = obs_env
    _write_registry(root, [_make_record(root, "recent"), _make_record(root, "old")])
    _surface(root, NOW - timedelta(minutes=5), "t-recent", "recent")  # today, within grace
    # A large padding field inflates this day's line past the cap without
    # affecting event-contract validity (task_id/research_id stay bounded).
    _emit(
        root,
        NOW - timedelta(days=20),
        event_type=consumption.SURFACED_EVENT,
        task_id="t-mid",
        research_id="recent",
        surface="dispatch",
        ts=(NOW - timedelta(days=20)).isoformat(),
        padding="x" * 2000,
    )
    _surface(root, NOW - timedelta(days=40), "t-old", "old")  # oldest — must be skipped

    monkeypatch.setattr(obs, "MAX_SCAN_BYTES", 500)
    c = _consumption(root, window_days=45)

    assert c["partial"] is True
    assert c["cap_reason"] == "byte_cap"
    assert c["files_skipped"] >= 1
    assert c["files_in_window"] > c["files_scanned"]
    assert c["surfaced_never_consumed"] is None  # partial coverage: no definitive negative
    assert c["surfaced_never_consumed_observed"] == 0  # lower bound still reported
    assert "recent" in c["per_record"]
    assert c["per_record"]["recent"]["pending"] == 1  # today's event retained, not lost
    assert "old" not in c["per_record"]  # oldest day never reached — silently a lower bound


def test_oversized_line_is_malformed_and_does_not_desync_next_line(obs_env):
    """A pathological multi-MB no-newline record must never be buffered whole —
    it is marked malformed/partial and the reader resynchronizes on the next
    real line boundary (ADR-011 P4 review, item 9)."""
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{NOW:%Y-%m-%d}.jsonl"
    huge_line = json.dumps(
        {
            "event_type": consumption.SURFACED_EVENT,
            "task_id": "t1",
            "research_id": "r1",
            "surface": "dispatch",
            "ts": NOW.isoformat(),
            "padding": "x" * 1_200_000,
        }
    )
    good_line = json.dumps(
        {
            "event_type": consumption.SURFACED_EVENT,
            "task_id": "t2",
            "research_id": "r1",
            "surface": "dispatch",
            "ts": (NOW - timedelta(hours=1)).isoformat(),
        }
    )
    path.write_text(huge_line + "\n" + good_line + "\n", "utf-8")
    c = _consumption(root)
    assert c["oversized_lines"] == 1
    assert c["partial"] is True
    assert c["cap_reason"] == "oversized_line"
    assert c["surfaced_pairs"] == 1  # the good line after the huge one still parsed


def test_line_at_exact_max_line_chars_boundary_is_not_oversized(obs_env):
    """A physical line whose CONTENT is exactly ``MAX_LINE_CHARS`` chars, plus its
    own trailing newline, must fit in one read and never be treated as
    requiring a drain (ADR-011 P4 review, item 3). Also proves the reader never
    consumes a second physical line to "drain" a boundary line that already
    ended in ``\\n`` — the following valid event still parses as its own pair."""
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{NOW:%Y-%m-%d}.jsonl"

    base = json.dumps(
        {
            "event_type": consumption.SURFACED_EVENT,
            "task_id": "t1",
            "research_id": "r1",
            "surface": "dispatch",
            "ts": NOW.isoformat(),
            "padding": "",
        }
    )
    pad_len = obs.MAX_LINE_CHARS - len(base)
    assert pad_len > 0
    boundary_line = json.dumps(
        {
            "event_type": consumption.SURFACED_EVENT,
            "task_id": "t1",
            "research_id": "r1",
            "surface": "dispatch",
            "ts": NOW.isoformat(),
            "padding": "x" * pad_len,
        }
    )
    assert len(boundary_line) == obs.MAX_LINE_CHARS  # exact boundary, by construction

    good_line = json.dumps(
        {
            "event_type": consumption.SURFACED_EVENT,
            "task_id": "t2",
            "research_id": "r1",
            "surface": "dispatch",
            "ts": (NOW - timedelta(hours=1)).isoformat(),
        }
    )
    path.write_text(boundary_line + "\n" + good_line + "\n", "utf-8")

    c = _consumption(root)
    assert c["oversized_lines"] == 0
    assert c["partial"] is False
    assert c["cap_reason"] is None
    # Both lines parsed as DISTINCT (task, research) pairs — proves the reader
    # never swallowed good_line while "draining" the boundary line.
    assert c["surfaced_pairs"] == 2


def test_oversized_line_counts_toward_byte_cap_and_stops_the_scan(obs_env, monkeypatch):
    """Bytes discarded while draining an oversized line must still be charged
    against ``MAX_SCAN_BYTES`` -- otherwise a multi-GB no-newline file can be
    read start-to-finish while ``bytes_scanned`` stays near zero (ADR-011 P4
    review, item 2). A small enough cap must trip mid-drain and stop the scan
    without reading past the remaining budget."""
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / f"{NOW:%Y-%m-%d}.jsonl"
    huge_line = json.dumps(
        {
            "event_type": consumption.SURFACED_EVENT,
            "task_id": "t1",
            "research_id": "r1",
            "surface": "dispatch",
            "ts": NOW.isoformat(),
            "padding": "x" * 3_000_000,
        }
    )
    good_line = json.dumps(
        {
            "event_type": consumption.SURFACED_EVENT,
            "task_id": "t2",
            "research_id": "r1",
            "surface": "dispatch",
            "ts": (NOW - timedelta(hours=1)).isoformat(),
        }
    )
    path.write_text(huge_line + "\n" + good_line + "\n", "utf-8")

    # Cap sits well below the huge line's real size (~3MB) but above one
    # max_line_chars-sized drain read, so the drain trips the cap mid-line.
    monkeypatch.setattr(obs, "MAX_SCAN_BYTES", 2 * 1024 * 1024)
    c = _consumption(root)
    assert c["partial"] is True
    assert c["cap_reason"] == "byte_cap"
    assert c["bytes_scanned"] <= obs.MAX_SCAN_BYTES
    assert c["surfaced_pairs"] == 0  # neither line was ingested -- cap hit mid-drain


def test_partial_from_unreadable_file_nulls_per_record_negative_too(obs_env):
    """A hidden consumption event could be sitting inside an unreadable file --
    the per-record ``surfaced_never_consumed`` must be nulled under partial
    coverage, not just the top-level aggregate (ADR-011 P4 review, item 1)."""
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _surface(root, NOW - timedelta(hours=3), "task-a", "r1")  # old enough to be "never" at face value
    events_dir = root / "batch_state" / "telemetry" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    # A second, unreadable day poisons the scan with partial coverage -- the
    # real consuming event for r1 could be hiding inside it.
    (events_dir / f"{(NOW - timedelta(days=1)):%Y-%m-%d}.jsonl").write_bytes(b"\xff\xfe not utf-8\n")

    c = _consumption(root)
    assert c["partial"] is True
    assert c["surfaced_never_consumed"] is None
    assert c["per_record"]["r1"]["surfaced_never_consumed"] is None
    assert c["per_record"]["r1"]["surfaced_never_consumed_observed"] == 1


def test_invalid_status_and_surface_are_malformed_not_counted(obs_env):
    """A consumed event with an out-of-contract ``status`` and a surfaced event
    carrying the consumption-reserved ``surface`` must both be rejected as
    malformed and never affect any metric (ADR-011 P4 review, item 10)."""
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _surface(root, NOW - timedelta(hours=2), "task-a", "r1")
    _emit(
        root,
        NOW - timedelta(hours=1),
        event_type=consumption.CONSUMED_EVENT,
        task_id="task-a",
        research_id="r1",
        surface="record",
        status=500,  # not 200/304
        ts=(NOW - timedelta(hours=1)).isoformat(),
    )
    _emit(
        root,
        NOW - timedelta(minutes=30),
        event_type=consumption.SURFACED_EVENT,
        task_id="task-b",
        research_id="r1",
        surface="record",  # reserved for consumption
        ts=(NOW - timedelta(minutes=30)).isoformat(),
    )
    c = _consumption(root)
    assert c["malformed_lines"] == 2
    assert c["consumed_pairs"] == 0
    assert c["surfaced_pairs"] == 1  # only the one genuinely valid surfaced event


# --------------------------------------------------------------------------- #
# 4. Endpoint — ungated availability, fail-soft, privacy, validation
# --------------------------------------------------------------------------- #
@pytest.fixture
def endpoint_root(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setattr(isa, "CACHE_PATH", tmp_path / "no-cache.json")
    monkeypatch.setattr(api_main.app.state, "ctx", _ctx_with_live_repo_root(tmp_path))
    return tmp_path


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
    _surface(endpoint_root, datetime.now(UTC) - timedelta(minutes=5), "secret-task-id-1234", "r1")
    blob = json.dumps(client.get("/api/knowledge/monitor").json())
    for leak in (
        "secret-task-id-1234",
        "run_x",
        "sess_x",
        "task_id",
        "Title r1",
        "Summary r1",
        "example.org",
        "Paraphrase",
    ):
        assert leak not in blob


# --------------------------------------------------------------------------- #
# 6. HTTP regression: /api/issues/streams strips private keys over the real
#    endpoint for the fresh / cache-hit / stale+refresh paths (ADR-011 P4
#    review, item 11 — the pure-function test above is not enough on its own).
# --------------------------------------------------------------------------- #
_LEAKY_REPORT = {
    "generated_at": int(NOW.timestamp()),
    "open_total": 3,
    "ok": True,
    "orphans": [],
    "effective_membership": {"5": {"epics": [100], "streams": ["s"], "unique_stream": True}},
    "open_issue_numbers": [5, 100],
    "open_issue_titles": {"5": "Issue 5 title", "100": "Issue 100 title"},
    # #10793: the validated membership cache writer's per-root index.
    "root_results": {"100": {"native": [], "body": [5]}},
}

_IDLE_REFRESH = {
    "schema_version": 1,
    "run_id": None,
    "phase": "idle",
    "requested_at": None,
    "started_at": None,
    "last_outcome": "none",
    "last_outcome_at": None,
    "failure_code": None,
    "cooldown_until": None,
}

_SCHEDULED_REFRESH = {
    **_IDLE_REFRESH,
    "run_id": "internal-run-id",
    "phase": "scheduled",
    "requested_at": int(NOW.timestamp()),
}


def _assert_no_private_keys(body: dict[str, Any]) -> None:
    assert "effective_membership" not in body
    assert "open_issue_numbers" not in body
    assert "open_issue_titles" not in body
    assert "root_results" not in body
    assert not set(isa.PRIVATE_CACHE_KEYS) & set(body)
    assert body["open_total"] == 3 and body["ok"] is True


def test_issues_streams_endpoint_strips_private_keys_on_fresh(monkeypatch):
    from scripts.api import issues_router

    calls = []
    monkeypatch.setattr(
        issues_router.audit,
        "read_cache",
        lambda max_age_s: dict(_LEAKY_REPORT) if max_age_s == 3600 else None,
    )
    monkeypatch.setattr(
        issues_router.audit,
        "schedule_refresh",
        lambda *, force: calls.append(force) or dict(_SCHEDULED_REFRESH),
    )
    monkeypatch.setattr(
        issues_router.audit,
        "run_audit",
        lambda: (_ for _ in ()).throw(AssertionError("request must not run audit")),
    )
    resp = client.get("/api/issues/streams", params={"fresh": "true"})
    assert resp.status_code == 200
    body = resp.json()
    _assert_no_private_keys(body)
    assert calls == [True]
    assert body["refreshing"] is True and body["refresh"]["phase"] == "scheduled"
    assert "run_id" not in json.dumps(body)


@pytest.mark.parametrize("publisher", ["membership_writer", "run_audit"])
def test_issues_streams_serves_membership_cache_writer_output_without_private_keys(tmp_path, monkeypatch, publisher):
    """#10793: a cache published by either writer (the strict checker's validated
    publication or a Monitor ``run_audit`` refresh) leaks no private key through
    the route or the Work projection, and keeps run_audit's warnings."""
    from scripts.api import issues_router
    from scripts.ci import check_issue_task_quality as checker
    from scripts.work import sources_public

    repo = "learn-ukrainian/learn-ukrainian.github.io"
    registry = {"devops": [5703], "harness": [6943]}
    report = isa.classify(
        [{"number": 123, "title": "PRIVATE_TITLE_CANARY"}], registry, {5703: (set(), {123}), 6943: (set(), set())}
    )
    report.update(repository=repo, warnings=[])
    hygiene = [
        {"code": "closed_epic_reopened", "stream": "devops", "epic": 4000},
        {"code": "milestone_closed_issue", "stream": "devops", "issue": 77},
    ]
    monkeypatch.setattr(checker, "ROOT", tmp_path)
    monkeypatch.setattr(isa, "hygiene_warnings", lambda *a, **k: [dict(w) for w in hygiene])
    if publisher == "membership_writer":
        assert checker.write_membership_cache(report, repo, registry)
    else:
        (tmp_path / "scripts/config").mkdir(parents=True)
        (tmp_path / "scripts/config/issue_streams.yaml").write_text(
            "streams:\n  devops:\n    epics: [5703]\n  harness:\n    epics: [6943]\n"
        )
        monkeypatch.setattr(isa, "_repo_owner_name", lambda *a: tuple(repo.split("/")))
        monkeypatch.setattr(isa, "fetch_open_issues", lambda *a: [{"number": 123, "title": "PRIVATE_TITLE_CANARY"}])
        monkeypatch.setattr(
            isa,
            "_fetch_subissue_batch",
            lambda cursors, *a: {n: {"body": "- [ ] #123" if n == 5703 else "", "subIssues": {"nodes": []}} for n in cursors},
        )
        isa.run_audit(tmp_path)
    cache = tmp_path / "batch_state/issue_stream_audit.json"
    assert json.loads(cache.read_text())["schema_version"] == 1
    assert json.loads(cache.read_text())["root_results"]["5703"] == {"native": [], "body": [123]}
    monkeypatch.setattr(isa, "CACHE_PATH", cache)
    monkeypatch.setattr(issues_router.audit, "read_refresh_state", lambda: dict(_IDLE_REFRESH))
    monkeypatch.setattr(
        issues_router.audit,
        "schedule_refresh",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("fresh cache must not schedule")),
    )

    resp = client.get("/api/issues/streams")
    assert resp.status_code == 200
    body = resp.json()
    # Allowlist tripwire: a new writer key fails here until it is classified.
    assert set(body) == {
        "closed_or_missing_epics", "generated_at", "incomplete_nodes", "membership_complete", "multi_homed",
        "ok", "open_total", "orphans", "pending_native_link", "refresh", "refreshing", "repository",
        "schema_version", "streams", "warnings",
    }
    assert "root_results" not in body and not set(isa.PRIVATE_CACHE_KEYS) & set(body)
    assert "PRIVATE_TITLE_CANARY" not in json.dumps(body)
    assert body["warnings"] == hygiene

    projection = sources_public.fetch_streams_projection()
    assert projection.status == "ok"
    assert "root_results" not in projection.payload
    assert not set(isa.PRIVATE_CACHE_KEYS) & set(projection.payload)
    assert "PRIVATE_TITLE_CANARY" not in json.dumps(projection.payload)
    assert projection.payload["open_stream_membership"] == {"123": ["devops"]}


def test_strict_adoption_gate_runs_as_bare_script():
    """Regression (ADR-011 P4 review, item 12): running this validator as a bare
    script — ``python scripts/audit/check_research_registry.py``, exactly how
    the session-setup cold-start hook and a human/CI invocation call it, NOT
    ``-m`` — must never crash. Bare-script invocation sets ``sys.path[0]`` to
    the file's own directory (``scripts/audit/``); a naive
    ``from scripts.audit import atlas_intake_registry`` would run
    ``scripts/audit/__init__.py``, which imports ``scripts/audit/config.py``,
    whose bare ``from config import ...`` then self-shadows against
    ``scripts/audit/config.py`` instead of the intended ``scripts/config.py``
    and crashes on a circular partial import. This proves the gate is not a
    dead CLI and stays runnable exactly as invoked in practice."""
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "audit" / "check_research_registry.py"
    python = sys.executable
    proc = subprocess.run(
        [str(python), str(script), "--strict-adoption", "--json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "Traceback (most recent call last)" not in proc.stderr, proc.stderr
    assert proc.returncode in (0, 1, 2)  # a gated result, never an uncaught crash
    payload = json.loads(proc.stdout)
    assert "ok" in payload


def test_issues_streams_no_cache_and_failure_are_bounded_and_private(monkeypatch):
    from scripts.api import issues_router

    monkeypatch.setattr(issues_router.audit, "read_cache", lambda max_age_s: None)
    monkeypatch.setattr(
        issues_router.audit,
        "schedule_refresh",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("credential body stderr")),
    )
    failed = {
        **_IDLE_REFRESH,
        "last_outcome": "failed",
        "last_outcome_at": int(NOW.timestamp()),
        "failure_code": "source_error",
        "cooldown_until": int(NOW.timestamp()) + 60,
    }
    monkeypatch.setattr(issues_router.audit, "read_refresh_state", lambda: failed)

    resp = client.get("/api/issues/streams")
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] == "issue_stream_state_unavailable"
    assert body["refreshing"] is False
    assert body["refresh"]["failure_code"] == "source_error"
    blob = json.dumps(body)
    for forbidden in ("credential", "body", "stderr", "run_id", "effective_membership"):
        assert forbidden not in blob


def test_issues_streams_no_cache_schedules_once_and_returns_immediately(monkeypatch):
    from scripts.api import issues_router

    calls = []
    monkeypatch.setattr(issues_router.audit, "read_cache", lambda max_age_s: None)
    monkeypatch.setattr(
        issues_router.audit,
        "schedule_refresh",
        lambda *, force: calls.append(force) or dict(_SCHEDULED_REFRESH),
    )
    resp = client.get("/api/issues/streams")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "no-cache" and body["ok"] is None
    assert body["refreshing"] is True and body["refresh"]["phase"] == "scheduled"
    assert calls == [False]
