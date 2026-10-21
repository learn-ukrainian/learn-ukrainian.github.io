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
import os
import urllib.error
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


def _ctx_with_live_repo_root(live_repo_root: Path):
    """Redirect live repo root for HTTP calls through ``client``.

    ``knowledge_router`` resolves registry roots from MonitorContext (#7269 step 12c),
    so tests swap ``app.state.ctx``.
    """
    base = api_main.app.state.ctx
    root = Path(live_repo_root)
    return base.with_roots(live_repo_root=root)


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
    monkeypatch.setattr(api_main.app.state, "ctx", _ctx_with_live_repo_root(tmp_path))
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


def test_cold_start_unknown_and_missing_role_yield_none(reg_root):
    _write_registry(reg_root, [_make_record(reg_root, "r1", cold_start_roles=["quality"])])
    runtime = reg.load_runtime_safe()
    assert reg.select_cold_start_pointers(runtime, "nobody") == ([], [])
    assert reg.select_cold_start_pointers(runtime, None) == ([], [])
    assert reg.select_cold_start_pointers(runtime, "   ") == ([], [])


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
    # No top-level `fetch` field: it is redundant with the documented, well-known
    # GET /api/knowledge/record/{id} and would push the envelope over budget.
    assert "fetch" not in body["research"]
    assert set(body["research"]) == {"enabled", "records"}
    for ptr in body["research"]["records"]:
        assert set(ptr) == {"id", "state", "content_hash", "routing"}


def test_orient_fail_open_when_cold_start_selector_raises(reg_root, monkeypatch):
    _write_registry(reg_root, [_make_record(reg_root, "r1", cold_start_roles=["quality"])])

    def _boom(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(reg, "select_cold_start_pointers", _boom)
    resp = _orient({"role": "quality"})
    assert resp.status_code == 200
    assert "research" not in resp.json()


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


# --------------------------------------------------------------------------- #
# 2b. /api/knowledge/cold-start: dedicated role-only endpoint (never the AND
#     matcher) — the bootstrap routing-algebra bug reproduced against the HTTP
#     surface, not just the pure selector.
# --------------------------------------------------------------------------- #
def test_cold_start_endpoint_uses_cold_start_roles_not_routing(reg_root):
    # routing.roles-only, no cold_start_roles → must NOT announce.
    routed_only = _make_record(reg_root, "routed-only", routing={"roles": ["quality"]}, cold_start_roles=[])
    # cold_start_roles=["quality"] but routing requires a task_family the
    # role-only request can never supply → must STILL announce (cold start is
    # role-only algebra, never the AND matcher).
    announced = _make_record(
        reg_root,
        "announced",
        routing={"roles": ["pedagogy"], "task_families": ["difficulty-gate"]},
        cold_start_roles=["quality"],
    )
    _write_registry(reg_root, [routed_only, announced])
    resp = client.get("/api/knowledge/cold-start", params={"role": "quality"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    assert [r["id"] for r in body["records"]] == ["announced"]


def test_cold_start_endpoint_etag_304(reg_root):
    _write_registry(reg_root, [_make_record(reg_root, "r1", cold_start_roles=["quality"])])
    first = client.get("/api/knowledge/cold-start", params={"role": "quality"})
    etag = first.headers["ETag"]
    second = client.get(
        "/api/knowledge/cold-start", params={"role": "quality"}, headers={"If-None-Match": etag}
    )
    assert second.status_code == 304


# --------------------------------------------------------------------------- #
# 3. Consumption telemetry: attribution vs surfacing, allowlist, validation
# --------------------------------------------------------------------------- #
@pytest.fixture
def task_store(tmp_path, monkeypatch):
    """Redirect the delegate task store (read via delegate_router) to tmp_path."""
    from scripts.api import delegate_router

    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(delegate_router, "_tasks_dir", lambda ctx=None: tasks_dir)

    def _put(task_id: str, *, status: str = "spawning", pid: int | None = None) -> None:
        safe = task_id.replace("/", "_").replace("\\", "_")
        (tasks_dir / f"{safe}.json").write_text(
            json.dumps({"task_id": task_id, "status": status, "pid": pid}), "utf-8"
        )

    return _put


def test_valid_active_task_emits_consumption_on_200(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", status="spawning", pid=os.getpid())
    resp = client.get("/api/knowledge/record/r1", params={"task": "job-1"})
    assert resp.status_code == 200
    consumed = [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]
    assert consumed == [{"task_id": "job-1", "research_id": "r1", "surface": "record", "status": 200}]


def test_cache_backed_304_emits_consumption_after_prior_200(reg_root, emit_sink, task_store):
    # ADR-011 P3: a 304 only counts as consumption when this task already has
    # evidence of a matching prior 200 for this exact record.
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", pid=os.getpid())
    first = client.get("/api/knowledge/record/r1", params={"task": "job-1"})
    etag = first.headers["ETag"]
    resp = client.get(
        "/api/knowledge/record/r1", params={"task": "job-1"}, headers={"If-None-Match": etag}
    )
    assert resp.status_code == 304
    consumed = [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]
    assert [c["status"] for c in consumed] == [200, 304]


def test_manufactured_304_without_prior_fetch_emits_nothing(reg_root, emit_sink, task_store):
    # A caller can learn a record's content_hash/ETag from the public filtered
    # manifest/pointer projection WITHOUT ever fetching the body. Replaying that
    # publicly-known ETag as If-None-Match under an active task must not
    # manufacture a consumption event — there is no proof the task ever consumed
    # the body. The HTTP response (304) is unaffected regardless of attribution.
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", pid=os.getpid())
    etag = client.get("/api/knowledge/record/r1").headers["ETag"]  # unattributed fetch
    resp = client.get(
        "/api/knowledge/record/r1", params={"task": "job-1"}, headers={"If-None-Match": etag}
    )
    assert resp.status_code == 304
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


def test_404_is_never_consumption(reg_root, emit_sink, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("job-1", pid=os.getpid())
    resp = client.get("/api/knowledge/record/does-not-exist", params={"task": "job-1"})
    assert resp.status_code == 404
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


def test_response_invariant_to_task_validity(reg_root, task_store):
    _write_registry(reg_root, [_make_record(reg_root, "r1")])
    task_store("live", status="running", pid=os.getpid())
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
        ("half-spawned", "spawning", None),  # spawning with no PID yet → no attribution
        ("half-spawned-dead", "spawning", 999999),  # spawning with a dead PID
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

    (delegate_router._tasks_dir() / "collide.json").write_text(
        json.dumps({"task_id": "other-id", "status": "running", "pid": os.getpid()}), "utf-8"
    )
    resp = client.get("/api/knowledge/record/r1", params={"task": "collide"})
    assert resp.status_code == 200
    assert not [p for t, p in emit_sink if t == consumption.CONSUMED_EVENT]


def test_telemetry_payloads_carry_no_forbidden_fields(emit_sink):
    consumption.emit_consumption(task_id="job-1", research_id="r1", status=200)
    consumption.emit_surface(research_id="r1", surface=consumption.SURFACE_DISPATCH, task_id="job-1")
    forbidden = {"body", "title", "summary", "source", "source_url", "prompt", "role",
                 "task_family", "track", "owned_paths", "context", "context_fingerprint"}
    for _t, payload in emit_sink:
        assert set(payload) <= {"task_id", "research_id", "surface", "status"}
        assert not (set(payload) & forbidden)


# --------------------------------------------------------------------------- #
# 4. Monitor client: filtered projection caching + bootstrap default compat
# --------------------------------------------------------------------------- #
def test_monitor_research_first_all_then_304_empty_then_changed_only(tmp_path, monkeypatch):
    # ADR-011 P3 changed-pointer semantics: the on-disk cache stores the complete
    # latest projection, but research()/cold_start() return only added/changed
    # pointers. [a, b] -> 304 (empty) -> only 'a' changes -> returns only 'a'.
    from scripts.ai_agent_bridge import monitor_client as mc

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cli = mc.MonitorClient(base_url="http://test")

    full_ab = (
        '{"enabled":true,"records":['
        '{"id":"a","state":"active","content_hash":"sha256:aa","routing":{}},'
        '{"id":"b","state":"active","content_hash":"sha256:bb","routing":{}}]}'
    )
    a_changed = (
        '{"enabled":true,"records":['
        '{"id":"a","state":"active","content_hash":"sha256:ZZ","routing":{}},'
        '{"id":"b","state":"active","content_hash":"sha256:bb","routing":{}}]}'
    )
    state = {"body": full_ab, "etag": "e1"}

    def _fake_get(path, *, headers=None):
        if headers and headers.get("If-None-Match") == f'"{state["etag"]}"':
            return 304, "", {"etag": f'"{state["etag"]}"'}
        return 200, state["body"], {"etag": f'"{state["etag"]}"'}

    monkeypatch.setattr(cli, "_get", _fake_get)

    first = cli.research(role="quality")
    assert first.source == "network"
    assert {r["id"] for r in json.loads(first.body)["records"]} == {"a", "b"}

    second = cli.research(role="quality")
    assert second.source == "not-modified"
    assert json.loads(second.body) == {"enabled": True, "records": []}  # valid, empty

    state["body"] = a_changed
    state["etag"] = "e2"
    third = cli.research(role="quality")
    assert third.source == "network"
    assert [r["id"] for r in json.loads(third.body)["records"]] == ["a"]  # only 'a', never 'b'


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
    # different consumer -> different key, even for the identical context
    d = cli.research(role="quality", consumer="a-different-consumer")
    assert d.key != a.key


def test_monitor_cache_key_never_embeds_raw_consumer_and_is_full_sha256(tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import monitor_client as mc

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cli = mc.MonitorClient(base_url="http://test")
    monkeypatch.setattr(cli, "_get", lambda path, headers=None: (200, '{"enabled":true,"records":[]}', {"etag": '"e"'}))

    result = cli.research(role="quality", consumer="some-secret-consumer-name")
    assert "some-secret-consumer-name" not in result.key
    fingerprint = result.key.split("__", 1)[1]
    assert len(fingerprint) == 64  # full sha256 hex, never the old 16-char truncation

    # A 300-char consumer (over any reasonable bound) must not raise and must
    # still be bounded before hashing, never embedded raw in the key.
    long_consumer = "c" * 300
    result2 = cli.research(role="quality", consumer=long_consumer)
    assert long_consumer not in result2.key
    assert len(result2.key.split("__", 1)[1]) == 64


def test_monitor_research_fails_open_on_transport_urlerror(tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import monitor_client as mc

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cli = mc.MonitorClient(base_url="http://test")

    def _raise(path, *, headers=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(cli, "_get", _raise)
    result = cli.research(role="quality")
    assert result.source.startswith("error:")
    assert result.body == ""


def test_monitor_research_fails_open_on_cache_oserror(tmp_path, monkeypatch):
    from scripts.ai_agent_bridge import _monitor_cache as cache
    from scripts.ai_agent_bridge import monitor_client as mc

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cli = mc.MonitorClient(base_url="http://test")
    monkeypatch.setattr(cli, "_get", lambda path, headers=None: (200, '{"enabled":true,"records":[]}', {"etag": '"e"'}))

    def _boom(_key):
        raise OSError("disk full")

    monkeypatch.setattr(cache, "peek", _boom)
    result = cli.research(role="quality")
    assert result.source.startswith("error:")
    assert result.body == ""


def test_monitor_defensive_304_without_cache_degrades_safely(tmp_path, monkeypatch):
    # Gemini review: the old "304 with no cached body -> re-fetch unconditionally"
    # branch was unreachable (we only ever send If-None-Match when a cached
    # snapshot exists, so the server has no ETag to 304 against otherwise).
    # Removed in favor of an explicit, safe fallback for a rogue/buggy server.
    from scripts.ai_agent_bridge import monitor_client as mc

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cli = mc.MonitorClient(base_url="http://test")
    monkeypatch.setattr(cli, "_get", lambda path, headers=None: (304, "", {}))
    result = cli.research(role="quality")
    assert result.source == "error:304-no-cache"
    assert result.body == ""


def test_bootstrap_role_only_routes_to_cold_start_never_and_manifest(monkeypatch):
    from scripts.ai_agent_bridge import monitor_client as mc

    cli = mc.MonitorClient(base_url="http://test")
    monkeypatch.setattr(cli, "manifest", lambda: {})
    stub = mc.ComponentResult(key="x", body="{}", hash="h", source="cache")
    monkeypatch.setattr(cli, "rules", lambda *, manifest=None: stub)
    monkeypatch.setattr(cli, "session", lambda *, manifest=None: stub)
    calls = {"cold_start": 0, "research": 0}
    monkeypatch.setattr(
        cli, "cold_start", lambda **_kw: calls.__setitem__("cold_start", calls["cold_start"] + 1) or stub
    )
    monkeypatch.setattr(
        cli, "research", lambda **_kw: calls.__setitem__("research", calls["research"] + 1) or stub
    )

    assert set(cli.bootstrap()) == {"rules", "session"}
    assert calls == {"cold_start": 0, "research": 0}

    # role ALONE -> the dedicated cold-start path, never the AND manifest.
    assert set(cli.bootstrap(role="quality")) == {"rules", "session", "research"}
    assert calls == {"cold_start": 1, "research": 0}

    # role PLUS another dimension -> the full AND-matched context.
    assert set(cli.bootstrap(role="quality", task_family="difficulty-gate")) == {
        "rules", "session", "research",
    }
    assert calls == {"cold_start": 1, "research": 1}

    # a dimension with no role -> still the AND-matched context (never cold-start).
    assert set(cli.bootstrap(task_family="difficulty-gate")) == {"rules", "session", "research"}
    assert calls == {"cold_start": 1, "research": 2}


# --------------------------------------------------------------------------- #
# 5. Delegate: flag validation, pointer-only injection, privacy-safe persistence
# --------------------------------------------------------------------------- #
def _delegate():
    import sys

    sys.path.insert(0, str(Path(reg.__file__).resolve().parents[2] / "scripts"))
    import delegate

    return delegate


def test_delegate_state_never_persists_research_null():
    # ADR-011 P3 default compatibility: a no-flags dispatch, a disabled registry,
    # or a degraded injection all resolve research_state to None; the persisted
    # state dict must OMIT the "research" key entirely — never "research": null.
    delegate = _delegate()
    base_state = {"task_id": "t", "status": "spawning"}

    no_flags = delegate._with_optional_research_state(dict(base_state), None)
    assert "research" not in no_flags
    assert no_flags == base_state

    with_context = delegate._with_optional_research_state(
        dict(base_state), {"pointer_ids": ["r1"], "filtered_etag": "e", "dropped_ids": [], "context_fingerprint": "f"}
    )
    assert with_context["research"] == {
        "pointer_ids": ["r1"], "filtered_etag": "e", "dropped_ids": [], "context_fingerprint": "f",
    }


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
