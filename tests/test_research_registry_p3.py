"""ADR-011 P3 — task-scoped pointers, bounded cold start, consumption telemetry.

Hermetic: every test builds a synthetic registry under ``tmp_path`` and points the
runtime at it via ``registry._ROOT_OVERRIDE`` (never the operator's live state). The
central telemetry emitter is monkeypatched to an in-memory sink; the delegate task
store is redirected to ``tmp_path`` — no GitHub, network, subprocess, or real event
log is touched.

Covers the P3 matrix: role-only cold-start selection (uses ``cold_start_roles``,
never the AND matcher), default orient/bootstrap byte compatibility, cache isolation
across roles/contexts, consumption attribution (200/304 with a validated active
task) vs surfacing, conservative task-id validation (traversal / collision /
finished-task spoof), telemetry payload allowlist, delegate flag validation +
pointer-only injection + privacy-safe persistence, and the automatic-body-bytes-zero
proof.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

import scripts.api.main as api_main
from scripts.audit import check_research_registry as crr
from scripts.research import consumption
from scripts.research import registry as reg

client = TestClient(api_main.app, raise_server_exceptions=False)


# --------------------------------------------------------------------------- #
# Synthetic registry builder (mirrors the P2 API test builder)
# --------------------------------------------------------------------------- #
def _digest_body(rid: str) -> str:
    return (
        f"# {rid}\n\n"
        f"Source: https://example.org/{rid}\n\n"
        f"Paraphrase-only compact digest for {rid}. No verbatim passages.\n"
    )


def _make_record(
    root: Path,
    rid: str,
    *,
    routing: dict[str, Any] | None = None,
    state: str = "deferred",
    access_class: str = "tracked-digest",
    cold_start_roles: list[str] | None = None,
) -> dict[str, Any]:
    digest_rel = f"docs/references/research-digests/{rid}.md"
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
        "cold_start_roles": cold_start_roles or [],
        "ownership": None,
        "consumer": None,
        "reason": "Deferred for the test." if state == "deferred" else None,
        "replacement": None,
        "access_class": access_class,
    }
    record["content_hash"] = crr.expected_content_hash(record, root)
    return record


def _write_registry(root: Path, records: list[dict[str, Any]]) -> None:
    refs = root / "docs" / "references"
    refs.mkdir(parents=True, exist_ok=True)
    doc = yaml.safe_dump({"schema_version": 1, "records": records}, sort_keys=False, allow_unicode=True)
    (refs / "research-registry.yaml").write_text(doc, "utf-8")


@pytest.fixture
def reg_root(tmp_path, monkeypatch):
    """Hermetic tmp root with the feature forced ON via env."""
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, "true")
    return tmp_path


@pytest.fixture
def emit_sink(monkeypatch):
    """Capture central telemetry events in memory (event_type, payload)."""
    events: list[tuple[str, dict[str, Any]]] = []

    def _fake_emit(event_type: str, payload: dict[str, Any], **_kw: Any) -> None:
        events.append((event_type, dict(payload)))

    monkeypatch.setattr(consumption, "emit_event", _fake_emit)
    return events


# --------------------------------------------------------------------------- #
# 1. Cold-start selector: cold_start_roles only, never the AND matcher
# --------------------------------------------------------------------------- #
def test_cold_start_uses_cold_start_roles_not_routing(reg_root):
    # routing.roles=[quality] but cold_start_roles empty → NOT announced at cold start.
    rec = _make_record(reg_root, "routed-only", routing={"roles": ["quality"]}, cold_start_roles=[])
    ann = _make_record(reg_root, "announced", routing={"roles": ["pedagogy"]}, cold_start_roles=["quality"])
    _write_registry(reg_root, [rec, ann])
    runtime = reg.load_runtime_safe()
    pointers, dropped = reg.select_cold_start_pointers(runtime, "quality")
    assert [p["id"] for p in pointers] == ["announced"]
    assert dropped == []


def test_cold_start_unknown_and_missing_role_yield_none(reg_root):
    _write_registry(reg_root, [_make_record(reg_root, "r1", cold_start_roles=["quality"])])
    runtime = reg.load_runtime_safe()
    assert reg.select_cold_start_pointers(runtime, "nobody") == ([], [])
    assert reg.select_cold_start_pointers(runtime, None) == ([], [])
    assert reg.select_cold_start_pointers(runtime, "   ") == ([], [])


def test_cold_start_deterministic_order_and_pointer_fields_only(reg_root):
    # P1 caps cold_start_roles at 5/role, so the max valid set is 5; the selector
    # returns them deterministically sorted by id, pointer-fields only.
    five = [_make_record(reg_root, f"cs-{i}", cold_start_roles=["quality"]) for i in (2, 0, 4, 1, 3)]
    _write_registry(reg_root, five)
    runtime = reg.load_runtime_safe()
    pointers, dropped = reg.select_cold_start_pointers(runtime, "quality")
    assert [p["id"] for p in pointers] == ["cs-0", "cs-1", "cs-2", "cs-3", "cs-4"]
    assert dropped == []
    # allowlisted pointer fields only — no title/summary/body/source/provenance.
    for ptr in pointers:
        assert set(ptr) == {"id", "state", "content_hash", "routing"}


# --------------------------------------------------------------------------- #
# 2. Orient: role opt-in, default byte compatibility, no shared cache
# --------------------------------------------------------------------------- #
def _orient(params: dict[str, str] | None = None):
    return client.get("/api/orient", params={"sections": "health", **(params or {})})


def test_orient_default_has_no_research_key(reg_root):
    _write_registry(reg_root, [_make_record(reg_root, "r1", cold_start_roles=["quality"])])
    body = _orient().json()
    assert "research" not in body


def test_orient_role_adds_pointer_only_research(reg_root):
    _write_registry(reg_root, [_make_record(reg_root, "r1", cold_start_roles=["quality"])])
    body = _orient({"role": "quality"}).json()
    assert body["research"]["enabled"] is True
    assert [p["id"] for p in body["research"]["records"]] == ["r1"]
    assert body["research"]["fetch"] == "/api/knowledge/record/{id}"
    for ptr in body["research"]["records"]:
        assert set(ptr) == {"id", "state", "content_hash", "routing"}


def test_orient_roles_do_not_share_cache(reg_root):
    _write_registry(
        reg_root,
        [
            _make_record(reg_root, "q-rec", cold_start_roles=["quality"]),
            _make_record(reg_root, "t-rec", cold_start_roles=["tts"]),
        ],
    )
    quality = _orient({"role": "quality"}).json()["research"]["records"]
    tts = _orient({"role": "tts"}).json()["research"]["records"]
    assert [p["id"] for p in quality] == ["q-rec"]
    assert [p["id"] for p in tts] == ["t-rec"]  # would be contaminated by a shared cache


def test_orient_disabled_has_no_research_even_with_role(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, "false")
    _write_registry(tmp_path, [_make_record(tmp_path, "r1", cold_start_roles=["quality"])])
    assert "research" not in _orient({"role": "quality"}).json()


def test_orient_role_never_calls_record_endpoint_body(reg_root):
    # Cold start announces pointers, never bodies: the response carries no digest text.
    _write_registry(reg_root, [_make_record(reg_root, "r1", cold_start_roles=["quality"])])
    body = _orient({"role": "quality"}).json()
    blob = json.dumps(body)
    assert "Paraphrase-only" not in blob and "digest" not in blob


# --------------------------------------------------------------------------- #
# 3. Consumption telemetry: attribution vs surfacing, allowlist, validation
# --------------------------------------------------------------------------- #
@pytest.fixture
def task_store(tmp_path, monkeypatch):
    """Redirect the delegate task store (read via delegate_router) to tmp_path."""
    from scripts.api import delegate_router

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(delegate_router, "TASKS_DIR", tasks_dir)

    def _put(task_id: str, *, status: str = "spawning", pid: int | None = None) -> None:
        safe = task_id.replace("/", "_").replace("\\", "_")
        (tasks_dir / f"{safe}.json").write_text(
            json.dumps({"task_id": task_id, "status": status, "pid": pid}), "utf-8"
        )

    return _put


def test_valid_active_task_emits_consumption_on_200(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", status="spawning")
    resp = client.get("/api/knowledge/record/r1", params={"task": "job-1"})
    assert resp.status_code == 200
    consumed = [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]
    assert consumed == [{"task_id": "job-1", "research_id": "r1", "surface": "record", "status": 200}]


def test_cache_backed_304_emits_consumption(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1")
    etag = client.get("/api/knowledge/record/r1").headers["ETag"]
    resp = client.get(
        "/api/knowledge/record/r1", params={"task": "job-1"}, headers={"If-None-Match": etag}
    )
    assert resp.status_code == 304
    consumed = [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]
    assert consumed[0]["status"] == 304


def test_no_task_no_consumption_but_still_serves(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    resp = client.get("/api/knowledge/record/r1")
    assert resp.status_code == 200
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


def test_404_is_never_consumption(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1")
    resp = client.get("/api/knowledge/record/does-not-exist", params={"task": "job-1"})
    assert resp.status_code == 404
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


def test_response_invariant_to_task_validity(reg_root, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("live", status="running", pid=1)  # pid=1 always alive
    valid = client.get("/api/knowledge/record/r1", params={"task": "live"})
    invalid = client.get("/api/knowledge/record/r1", params={"task": "ghost"})
    assert valid.status_code == invalid.status_code == 200
    assert valid.content == invalid.content
    assert valid.headers["ETag"] == invalid.headers["ETag"]


@pytest.mark.parametrize(
    "task_id,status,pid",
    [
        ("../../etc/passwd", "spawning", None),  # traversal
        ("finished", "done", None),  # finished-task spoof
        ("zombie", "running", 999999),  # running status, dead pid → zombie
        ("a" * 129, "spawning", None),  # oversize
    ],
)
def test_invalid_or_inactive_task_no_consumption(reg_root, emit_sink, task_store, task_id, status, pid):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    if "/" not in task_id and len(task_id) <= 200:
        task_store(task_id, status=status, pid=pid)
    resp = client.get("/api/knowledge/record/r1", params={"task": task_id})
    assert resp.status_code == 200
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


def test_task_id_collision_requires_exact_stored_match(reg_root, emit_sink, task_store):
    # A state file exists at a sanitized path, but its stored task_id differs from
    # the request → no attribution (defeats collisions via path sanitization).
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    from scripts.api import delegate_router

    (delegate_router.TASKS_DIR / "collide.json").write_text(
        json.dumps({"task_id": "other-id", "status": "running", "pid": 1}), "utf-8"
    )
    resp = client.get("/api/knowledge/record/r1", params={"task": "collide"})
    assert resp.status_code == 200
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


def test_surface_event_is_distinct_from_consumption(emit_sink):
    consumption.emit_surface(research_id="r1", surface=consumption.SURFACE_DISPATCH, task_id="job-1")
    assert emit_sink == [
        (consumption.SURFACED_EVENT, {"task_id": "job-1", "research_id": "r1", "surface": "dispatch"})
    ]


def test_telemetry_payloads_carry_no_forbidden_fields(emit_sink):
    consumption.emit_consumption(task_id="job-1", research_id="r1", status=200)
    consumption.emit_surface(research_id="r1", surface=consumption.SURFACE_COLD_START)
    forbidden = {"body", "title", "summary", "source", "source_url", "prompt", "role",
                 "task_family", "track", "owned_paths", "context", "context_fingerprint"}
    for _t, payload in emit_sink:
        assert set(payload) <= {"task_id", "research_id", "surface", "status"}
        assert not (set(payload) & forbidden)


# --------------------------------------------------------------------------- #
# 4. Monitor client: filtered projection caching + bootstrap default compat
# --------------------------------------------------------------------------- #
def test_monitor_research_first_surfaces_then_304_reuses(tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import monitor_client as mc

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cli = mc.MonitorClient(base_url="http://test")
    calls: list[dict[str, str]] = []

    def _fake_get(path, *, headers=None):
        calls.append(headers or {})
        if headers and "If-None-Match" in headers:
            return 304, "", {"etag": '"abc"'}
        return 200, '{"enabled":true,"records":[{"id":"r1"}]}', {"etag": '"abc"'}

    monkeypatch.setattr(cli, "_get", _fake_get)

    first = cli.research(role="quality")
    assert first.source == "network"
    assert "r1" in first.body
    second = cli.research(role="quality")
    assert second.source == "not-modified"
    assert second.body == first.body  # warm reuse, zero changed pointers
    assert "If-None-Match" in calls[1]


def test_monitor_research_context_isolation_by_fingerprint(tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import _monitor_cache as cache
    from scripts.ai_agent_bridge import monitor_client as mc

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cli = mc.MonitorClient(base_url="http://test")
    monkeypatch.setattr(cli, "_get", lambda path, headers=None: (200, '{"records":[]}', {"etag": '"e"'}))
    a = cli.research(role="quality")
    b = cli.research(role="tts")
    assert a.key != b.key  # different fingerprints → different cache keys
    # neither key leaks a raw path
    c = cli.research(role="quality", owned_paths=["scripts/secret/path.py"])
    assert "scripts/secret/path.py" not in c.key
    assert cache.peek(c.key) is not None


def test_bootstrap_default_is_exactly_rules_and_session(monkeypatch):
    from scripts.ai_agent_bridge import monitor_client as mc

    cli = mc.MonitorClient(base_url="http://test")
    monkeypatch.setattr(cli, "manifest", lambda: {})
    stub = mc.ComponentResult(key="x", body="b", hash="h", source="cache")
    monkeypatch.setattr(cli, "rules", lambda *, manifest=None: stub)
    monkeypatch.setattr(cli, "session", lambda *, manifest=None: stub)
    called = {"research": False}
    monkeypatch.setattr(cli, "research", lambda **_kw: called.__setitem__("research", True) or stub)

    assert set(cli.bootstrap()) == {"rules", "session"}
    assert called["research"] is False
    assert set(cli.bootstrap(role="quality")) == {"rules", "session", "research"}
    assert called["research"] is True


# --------------------------------------------------------------------------- #
# 5. Delegate: flag validation, pointer-only injection, privacy-safe persistence
# --------------------------------------------------------------------------- #
def _delegate():
    import sys

    sys.path.insert(0, str(Path(reg.__file__).resolve().parents[2] / "scripts"))
    import delegate

    return delegate


def _args(**over):
    import argparse

    ns = argparse.Namespace(
        research_role=None, research_task_family=None, research_track=None, research_owned_path=None
    )
    for key, value in over.items():
        setattr(ns, key, value)
    return ns


def test_delegate_no_flags_yields_no_context():
    delegate = _delegate()
    assert delegate._build_research_context(_args()) is None


def test_delegate_rejects_oversize_and_overcount():
    delegate = _delegate()
    with pytest.raises(delegate.ResearchContextError):
        delegate._build_research_context(_args(research_role="x" * (reg.MAX_QUERY_VALUE_LEN + 1)))
    with pytest.raises(delegate.ResearchContextError):
        delegate._build_research_context(
            _args(research_owned_path=["p"] * (reg.MAX_OWNED_PATHS + 1))
        )
    with pytest.raises(delegate.ResearchContextError):
        delegate._build_research_context(
            _args(research_owned_path=["x" * (reg.MAX_OWNED_PATH_LEN + 1)])
        )


def test_delegate_injection_is_pointer_only_and_persists_safely(reg_root, monkeypatch):
    delegate = _delegate()
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", reg_root)
    monkeypatch.setattr(delegate, "_REPO_ROOT", reg_root)
    _write_registry(
        reg_root,
        [
            _make_record(
                reg_root,
                "cefr",
                routing={"roles": ["quality"], "task_families": ["difficulty-gate"]},
            )
        ],
    )
    surfaced: list[tuple[str, dict]] = []
    monkeypatch.setattr(consumption, "emit_event", lambda t, p, **k: surfaced.append((t, p)))

    ctx = reg.normalize_context("quality", "difficulty-gate", None, [])
    block, state = delegate._resolve_research_injection(ctx, "task-9")

    # pointer-only prompt block: ids + fetch instruction, never a digest body
    assert "cefr" in block and "/api/knowledge/record/{id}" in block
    assert "Paraphrase-only" not in block
    # persistence allowlist: ids / etag / dropped / fingerprint only
    assert set(state) == {"pointer_ids", "filtered_etag", "dropped_ids", "context_fingerprint"}
    assert state["pointer_ids"] == ["cefr"]
    assert "owned_paths" not in state and "role" not in state
    # a surface (not consumption) event was emitted for the injected pointer
    assert surfaced == [
        (consumption.SURFACED_EVENT, {"task_id": "task-9", "research_id": "cefr", "surface": "dispatch"})
    ]


def test_delegate_injection_fail_open_when_disabled(reg_root, monkeypatch):
    delegate = _delegate()
    monkeypatch.setattr(delegate, "_REPO_ROOT", reg_root)
    monkeypatch.setenv(reg.ENV_FLAG, "false")
    ctx = reg.normalize_context("quality", "difficulty-gate", None, [])
    assert delegate._resolve_research_injection(ctx, "t") == ("", None)


# --------------------------------------------------------------------------- #
# 6. Byte measurement: automatic body bytes are zero; bounded pointer payloads
# --------------------------------------------------------------------------- #
def test_automatic_surface_never_injects_body_bytes(reg_root):
    _write_registry(
        reg_root,
        [_make_record(reg_root, "r1", routing={"roles": ["quality"]}, cold_start_roles=["quality"])],
    )
    # Cold-start orient projection carries pointers, never the digest body bytes.
    body = _orient({"role": "quality"}).json()["research"]
    projection = json.dumps(body).encode("utf-8")
    digest = (reg_root / "docs/references/research-digests/r1.md").read_text("utf-8")
    assert digest.strip() not in json.dumps(body)
    # And it stays well within the filtered budget.
    assert len(projection) <= reg.MAX_FILTERED_BYTES
