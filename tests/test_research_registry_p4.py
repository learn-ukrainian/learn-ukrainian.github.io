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
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": True}},
                 open_numbers=[], is_file=True)
    assert _run_strict(root) == 0


def test_strict_gate_rejects_same_closed_issue_as_issue_consumer(strict_root):
    """The SAME closed-but-uniquely-owned issue that passes record ownership
    (previous test) must still fail as an issue-CONSUMER: consumer liveness
    additionally requires the ref to be open, not just uniquely owned
    (PR #4998 corrective pass, item 3)."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="adopted", consumer={"kind": "issue", "ref": "9001"})
    _write_registry(root, [rec])
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": True}},
                 open_numbers=[], is_file=True)
    assert _run_strict(root) == 2


def test_strict_gate_rejects_same_stream_two_epic_ownership(strict_root):
    """Native membership in TWO epics of the SAME stream is still ambiguous —
    ``unique_stream`` requires exactly one EFFECTIVE epic, not merely one
    stream name (codex/gemini review, PR #4998)."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="proposed", ownership={"issue": 9001, "stream": REAL_EPIC})
    _write_registry(root, [rec])
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC, 4969], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": False}}, is_file=True)
    assert _run_strict(root) == 2


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
    """An adopted ``issue`` consumer must be open AND uniquely owned by exactly
    one effective epic — being merely present in the open-issue set is not
    enough (codex/gemini review, PR #4998)."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="adopted", consumer={"kind": "issue", "ref": "9001"})
    _write_registry(root, [rec])
    owned_entry = {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"],
                            "via": "native", "unique_stream": True}}
    _write_cache(cache, owned_entry, open_numbers=[9001], is_file=True)
    assert _run_strict(root) == 0  # open AND uniquely owned → resolves
    # Same registry, issue open but NOT owned by any stream (orphan) → blocked.
    _write_cache(cache, {}, open_numbers=[9001], is_file=True)
    assert _run_strict(root) == 2
    # Same registry, issue not open at all → blocked.
    _write_cache(cache, owned_entry, open_numbers=[1], is_file=True)
    assert _run_strict(root) == 2


def test_strict_gate_rejects_ambiguously_owned_issue_consumer(strict_root):
    """An adopted ``issue`` consumer that IS open but ambiguously multi-homed
    (unique_stream False) must not resolve."""
    root, cache = strict_root
    rec = _make_record(root, "r1", state="adopted", consumer={"kind": "issue", "ref": "9001"})
    _write_registry(root, [rec])
    ambiguous_entry = {"9001": {"epics": [REAL_EPIC, 1234], "streams": ["core-quality", "other"],
                                "via": "native", "unique_stream": False}}
    _write_cache(cache, ambiguous_entry, open_numbers=[9001], is_file=True)
    assert _run_strict(root) == 2


def test_strict_gate_resolves_corpus_consumer_via_atlas_registry(strict_root):
    """The corpus resolver is real: it resolves a genuinely declared Atlas
    intake source family and rejects a dangling one — no cache required."""
    root, cache = strict_root
    _write_cache(cache, {}, is_file=True)
    ok = _make_record(root, "ok", state="adopted", consumer={"kind": "corpus", "ref": "textbook"})
    _write_registry(root, [ok])
    assert _run_strict(root) == 0

    dangling = _make_record(
        root, "dangling", state="adopted", consumer={"kind": "corpus", "ref": "not-a-real-family"}
    )
    _write_registry(root, [dangling])
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


def test_issue_consumer_is_unverified_without_fresh_cache(obs_env):
    """No fresh membership cache in the monitor's env → an issue consumer can be
    neither proven nor disproven — it must land in unverified, never dead."""
    root = obs_env
    ri = _make_record(root, "ri", state="adopted", consumer={"kind": "issue", "ref": "4952"})
    _write_registry(root, [ri])
    m = _monitor(root)
    assert m["dead_consumers"]["unverified"] == ["ri"]
    assert m["dead_consumers"]["dead"] == []
    assert m["adoption"]["effective_adopted"] == 0  # unverified never counts as effective


def test_issue_consumer_resolved_alive_or_dead_with_fresh_cache(obs_env, monkeypatch):
    """With a FRESH membership cache, the monitor must use the SAME resolver
    proof the strict gate uses: open + uniquely owned → alive; closed/orphan/
    ambiguous → dead. Record ownership and issue-consumer resolution are
    validated independently (ADR-011 P4 review)."""
    root = obs_env
    cache = root / "cache.json"
    monkeypatch.setattr(isa, "CACHE_PATH", cache)
    _write_cache(cache, {"9001": {"epics": [REAL_EPIC], "streams": ["core-quality"],
                                  "via": "native", "unique_stream": True}},
                 open_numbers=[9001], is_file=True)
    alive = _make_record(root, "alive", state="adopted", consumer={"kind": "issue", "ref": "9001"})
    dead = _make_record(root, "dead", state="adopted", consumer={"kind": "issue", "ref": "5"})
    _write_registry(root, [alive, dead])
    m = _monitor(root)
    assert m["dead_consumers"]["dead"] == ["dead"]
    assert m["dead_consumers"]["unverified"] == []
    assert m["adoption"]["effective_adopted"] == 1


def test_corpus_consumer_resolved_via_real_atlas_registry(obs_env):
    """The corpus resolver is real and offline (no cache needed): a genuinely
    declared Atlas intake source family is alive, a dangling one is dead."""
    root = obs_env
    ok = _make_record(root, "ok", state="adopted", consumer={"kind": "corpus", "ref": "textbook"})
    dangling = _make_record(
        root, "dangling", state="adopted", consumer={"kind": "corpus", "ref": "not-a-real-family"}
    )
    _write_registry(root, [ok, dangling])
    m = _monitor(root)
    assert m["dead_consumers"]["dead"] == ["dangling"]
    assert m["dead_consumers"]["unverified"] == []
    assert m["adoption"]["effective_adopted"] == 1


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


def test_broken_provenance_counts_invalid_never_effective_adoption(obs_env):
    """Broken provenance (missing digest file) is semantic-invalid REGARDLESS of
    the claimed lifecycle state: it must count as invalid, stay visible in
    invalid_provenance, and never be misreported as merely current (not stale)
    or count toward adopted/effective adoption (ADR-011 P4 review)."""
    root = obs_env
    _stub(root, "scripts/x.py")
    broken = _make_record(root, "broken", state="adopted",
                          consumer={"kind": "path", "ref": "scripts/x.py"}, write_digest=False)
    healthy = _make_record(root, "healthy", state="adopted",
                           consumer={"kind": "path", "ref": "scripts/x.py"})
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


def test_scan_is_newest_first_and_nulls_negative_under_partial_coverage(obs_env, monkeypatch):
    """Byte cap must hide OLDER days, not newer ones — the most recent surface
    survives — and a scan that skipped part of the window must never assert a
    definitive ``surfaced_never_consumed`` (ADR-011 P4 review, item 8)."""
    root = obs_env
    _write_registry(root, [_make_record(root, "recent"), _make_record(root, "old")])
    _surface(root, NOW - timedelta(minutes=5), "t-recent", "recent")  # today, within grace
    # A large padding field inflates this day's line past the cap without
    # affecting event-contract validity (task_id/research_id stay bounded).
    _emit(root, NOW - timedelta(days=20), event_type=consumption.SURFACED_EVENT,
          task_id="t-mid", research_id="recent", surface="dispatch",
          ts=(NOW - timedelta(days=20)).isoformat(), padding="x" * 2000)
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
    huge_line = json.dumps({
        "event_type": consumption.SURFACED_EVENT, "task_id": "t1", "research_id": "r1",
        "surface": "dispatch", "ts": NOW.isoformat(), "padding": "x" * 1_200_000,
    })
    good_line = json.dumps({
        "event_type": consumption.SURFACED_EVENT, "task_id": "t2", "research_id": "r1",
        "surface": "dispatch", "ts": (NOW - timedelta(hours=1)).isoformat(),
    })
    path.write_text(huge_line + "\n" + good_line + "\n", "utf-8")
    c = _consumption(root)
    assert c["oversized_lines"] == 1
    assert c["partial"] is True
    assert c["cap_reason"] == "oversized_line"
    assert c["surfaced_pairs"] == 1  # the good line after the huge one still parsed


def test_invalid_status_and_surface_are_malformed_not_counted(obs_env):
    """A consumed event with an out-of-contract ``status`` and a surfaced event
    carrying the consumption-reserved ``surface`` must both be rejected as
    malformed and never affect any metric (ADR-011 P4 review, item 10)."""
    root = obs_env
    _write_registry(root, [_make_record(root, "r1")])
    _surface(root, NOW - timedelta(hours=2), "task-a", "r1")
    _emit(root, NOW - timedelta(hours=1), event_type=consumption.CONSUMED_EVENT,
          task_id="task-a", research_id="r1", surface="record", status=500,  # not 200/304
          ts=(NOW - timedelta(hours=1)).isoformat())
    _emit(root, NOW - timedelta(minutes=30), event_type=consumption.SURFACED_EVENT,
          task_id="task-b", research_id="r1", surface="record",  # reserved for consumption
          ts=(NOW - timedelta(minutes=30)).isoformat())
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
}


def _assert_no_private_keys(body: dict[str, Any]) -> None:
    assert "effective_membership" not in body
    assert "open_issue_numbers" not in body
    assert body["open_total"] == 3 and body["ok"] is True


def test_issues_streams_endpoint_strips_private_keys_on_fresh(monkeypatch):
    from scripts.api import issues_router

    monkeypatch.setattr(issues_router.audit, "run_audit", lambda: dict(_LEAKY_REPORT))
    resp = client.get("/api/issues/streams", params={"fresh": "true"})
    assert resp.status_code == 200
    _assert_no_private_keys(resp.json())


def test_issues_streams_endpoint_strips_private_keys_on_cache_hit(monkeypatch):
    from scripts.api import issues_router

    monkeypatch.setattr(
        issues_router.audit, "read_cache",
        lambda max_age_s: dict(_LEAKY_REPORT) if max_age_s == 3600 else None,
    )
    resp = client.get("/api/issues/streams")
    assert resp.status_code == 200
    _assert_no_private_keys(resp.json())


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
    python = repo_root / ".venv" / "bin" / "python"
    proc = subprocess.run(
        [str(python), str(script), "--strict-adoption", "--json"],
        cwd=repo_root, capture_output=True, text=True, timeout=30,
    )
    assert "Traceback (most recent call last)" not in proc.stderr, proc.stderr
    assert proc.returncode in (0, 1, 2)  # a gated result, never an uncaught crash
    payload = json.loads(proc.stdout)
    assert "ok" in payload


def test_issues_streams_endpoint_strips_private_keys_on_stale_plus_refresh(monkeypatch):
    from scripts.api import issues_router

    def _fake_read_cache(max_age_s):
        if max_age_s == 3600:
            return None  # no fresh cache
        return dict(_LEAKY_REPORT)  # stale fallback within the 7-day window

    class _FakePopen:
        def __init__(self, *a, **k):
            pass  # never actually spawn a background refresh under test

    monkeypatch.setattr(issues_router.audit, "read_cache", _fake_read_cache)
    monkeypatch.setattr(issues_router.subprocess, "Popen", _FakePopen)
    resp = client.get("/api/issues/streams")
    assert resp.status_code == 200
    body = resp.json()
    assert body["stale"] is True and body["refreshing"] is True
    _assert_no_private_keys(body)
