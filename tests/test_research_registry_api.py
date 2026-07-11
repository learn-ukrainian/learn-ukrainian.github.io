"""ADR-011 P2 — bounded research discovery API + runtime layer contract tests.

Hermetic: every test builds a synthetic registry under ``tmp_path`` and points the
runtime at it via ``registry._ROOT_OVERRIDE`` (never the operator's live ``.runtime``
state). No GitHub, network, subprocess, ``sources.db``, or embeddings access.

Covers the required P2 matrix: the kill switch (env/live-file precedence and strict
parsing), disabled-mode exactness, fail-open loading, the global routing hash, the
pure AND matcher, context normalization, the two-tier 304 proof, per-record ETag
semantics, drift/traversal/private/oversize refusal, byte/token budgets, and a
static no-side-effects guard.
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
from scripts.research import registry as reg

client = TestClient(api_main.app, raise_server_exceptions=False)


# --------------------------------------------------------------------------- #
# Synthetic registry builder
# --------------------------------------------------------------------------- #
def _digest_body(rid: str, *, extra: str = "") -> str:
    return (
        f"# {rid}\n\n"
        f"Source: https://example.org/{rid}\n\n"
        f"Paraphrase-only compact digest for {rid}. No verbatim passages.\n{extra}"
    )


def _make_record(
    root: Path,
    rid: str,
    *,
    routing: dict[str, Any] | None = None,
    state: str = "deferred",
    access_class: str = "tracked-digest",
    cold_start_roles: list[str] | None = None,
    digest_body: str | None = None,
    title: str | None = None,
    summary: str | None = None,
) -> dict[str, Any]:
    """Write the record's digest and return a schema-valid, drift-free record dict."""
    digest_rel = f"docs/references/research-digests/{rid}.md"
    digest_path = root / digest_rel
    digest_path.parent.mkdir(parents=True, exist_ok=True)
    digest_path.write_text(digest_body if digest_body is not None else _digest_body(rid), "utf-8")

    record: dict[str, Any] = {
        "id": rid,
        "title": title or f"Title {rid}",
        "summary": summary or f"Summary {rid}",
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


def _write_registry(root: Path, records: list[dict[str, Any]], *, header: str = "") -> None:
    refs = root / "docs" / "references"
    refs.mkdir(parents=True, exist_ok=True)
    doc = yaml.safe_dump({"schema_version": 1, "records": records}, sort_keys=False, allow_unicode=True)
    (refs / "research-registry.yaml").write_text(header + doc, "utf-8")


@pytest.fixture
def reg_root(tmp_path, monkeypatch):
    """Point the runtime at a hermetic tmp root and force the feature ON via env."""
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, "true")
    return tmp_path


# --------------------------------------------------------------------------- #
# 1. Kill switch: precedence + strict parsing
# --------------------------------------------------------------------------- #
def test_flag_default_off(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.delenv(reg.ENV_FLAG, raising=False)
    assert reg.is_enabled() is False


@pytest.mark.parametrize("value", ["true", "1", "yes", "on", "TRUE", "On", "YES"])
def test_env_true_spellings(tmp_path, monkeypatch, value):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, value)
    assert reg.is_enabled() is True


@pytest.mark.parametrize("value", ["false", "0", "no", "off", "FALSE", "Off"])
def test_env_false_spellings(tmp_path, monkeypatch, value):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, value)
    assert reg.is_enabled() is False


def test_env_invalid_resolves_false_never_falls_through(tmp_path, monkeypatch):
    # Live file says enabled, but an invalid *higher-precedence* env must not fall
    # through to it — it resolves to False.
    flag = tmp_path / ".runtime" / "api" / "research-registry.json"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text(json.dumps({"research_registry": {"enabled": True}}), "utf-8")
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, "maybe")
    assert reg.is_enabled() is False


def test_live_file_toggle_true_then_false(tmp_path, monkeypatch):
    flag = tmp_path / ".runtime" / "api" / "research-registry.json"
    flag.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.delenv(reg.ENV_FLAG, raising=False)

    flag.write_text(json.dumps({"research_registry": {"enabled": True}}), "utf-8")
    assert reg.is_enabled() is True
    # Same process, flip the file — the change is immediate (dynamic per call).
    flag.write_text(json.dumps({"research_registry": {"enabled": False}}), "utf-8")
    assert reg.is_enabled() is False


def test_env_overrides_live_file(tmp_path, monkeypatch):
    flag = tmp_path / ".runtime" / "api" / "research-registry.json"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text(json.dumps({"research_registry": {"enabled": False}}), "utf-8")
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, "true")
    assert reg.is_enabled() is True


@pytest.mark.parametrize(
    "content",
    ["{ not json", json.dumps({"research_registry": {}}), json.dumps({"other": 1}),
     json.dumps({"research_registry": {"enabled": "true"}})],
)
def test_live_file_malformed_resolves_false(tmp_path, monkeypatch, content):
    flag = tmp_path / ".runtime" / "api" / "research-registry.json"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text(content, "utf-8")
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.delenv(reg.ENV_FLAG, raising=False)
    assert reg.is_enabled() is False


# --------------------------------------------------------------------------- #
# 2. Disabled mode is exact + loader is not invoked
# --------------------------------------------------------------------------- #
def test_disabled_mode_exact(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, "false")

    km = client.get("/api/knowledge/manifest")
    assert km.status_code == 200
    assert km.json() == {"enabled": False, "records": []}

    rec = client.get("/api/knowledge/record/anything")
    assert rec.status_code == 404


def test_disabled_loader_not_invoked(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "_ROOT_OVERRIDE", tmp_path)
    monkeypatch.setenv(reg.ENV_FLAG, "false")

    def _boom(**_kwargs):
        raise AssertionError("load_runtime must not be called while disabled")

    monkeypatch.setattr(reg, "load_runtime", _boom)
    assert client.get("/api/knowledge/manifest").status_code == 200
    assert client.get("/api/knowledge/record/x").status_code == 404
    assert reg.research_manifest_component() is None


# --------------------------------------------------------------------------- #
# 3. Fail-open: enabled + missing/malformed registry or loader exception
# --------------------------------------------------------------------------- #
def test_enabled_missing_registry_fails_open(reg_root):
    # No registry file written at all.
    km = client.get("/api/knowledge/manifest?role=quality")
    assert km.status_code == 200
    assert km.json() == {"enabled": True, "records": []}
    assert client.get("/api/knowledge/record/anything").status_code == 404
    assert reg.research_manifest_component() is None


def test_enabled_malformed_registry_fails_open(reg_root):
    refs = reg_root / "docs" / "references"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "research-registry.yaml").write_text("this: [is not: valid: yaml", "utf-8")
    assert reg.load_runtime(root=reg_root) is None
    assert client.get("/api/knowledge/manifest").status_code == 200


def test_enabled_schema_invalid_fails_open(reg_root):
    _write_registry(reg_root, [{"id": "x", "not": "a valid record"}])
    assert reg.load_runtime(root=reg_root) is None
    assert reg.research_manifest_component() is None


# --------------------------------------------------------------------------- #
# 4. Global hash determinism + sensitivity
# --------------------------------------------------------------------------- #
def test_global_hash_stable_under_yaml_reorder_and_format(reg_root):
    r1 = _make_record(reg_root, "aaa", routing={"roles": ["quality"], "tracks": ["core"]})
    r2 = _make_record(reg_root, "bbb", routing={"roles": ["tts"]})
    _write_registry(reg_root, [r1, r2])
    h1 = reg.load_runtime(root=reg_root).global_hash()

    # Reorder records + add a comment header + trailing whitespace: hash unchanged.
    _write_registry(reg_root, [r2, r1], header="# a comment\n\n\n")
    h2 = reg.load_runtime(root=reg_root).global_hash()
    assert h1 == h2


def test_global_hash_insensitive_to_summary_and_title(reg_root):
    r1 = _make_record(reg_root, "aaa")
    _write_registry(reg_root, [r1])
    h1 = reg.load_runtime(root=reg_root).global_hash()
    r1b = dict(r1, title="A completely different title", summary="different summary")
    _write_registry(reg_root, [r1b])
    assert reg.load_runtime(root=reg_root).global_hash() == h1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda r: r.__setitem__("state", "adopted"),
        lambda r: r.__setitem__("access_class", "public-url"),
        lambda r: r.__setitem__("cold_start_roles", ["quality"]),
        lambda r: r["routing"].__setitem__("roles", ["quality", "pedagogy"]),
        lambda r: r["routing"].__setitem__("task_families", ["difficulty-gate"]),
        lambda r: r["routing"].__setitem__("tracks", ["core"]),
        lambda r: r["routing"].__setitem__("owned_paths", ["scripts/audit/**"]),
    ],
)
def test_global_hash_sensitive_to_routed_fields(reg_root, mutate):
    r1 = _make_record(reg_root, "aaa", routing={"roles": ["quality"]}, state="deferred")
    _write_registry(reg_root, [r1])
    h1 = reg.load_runtime(root=reg_root).global_hash()
    r1b = json.loads(json.dumps(r1))  # deep copy
    mutate(r1b)
    if r1b["state"] == "adopted":  # keep it schema/lifecycle sane for the loader
        r1b["consumer"] = {"kind": "path", "ref": "scripts/audit/text_difficulty.py"}
    _write_registry(reg_root, [r1b])
    assert reg.load_runtime(root=reg_root).global_hash() != h1


def test_global_hash_sensitive_to_content_hash(reg_root):
    r1 = _make_record(reg_root, "aaa", digest_body=_digest_body("aaa"))
    _write_registry(reg_root, [r1])
    h1 = reg.load_runtime(root=reg_root).global_hash()
    # Change the digest AND reconcile the stored hash (a real content edit).
    r1b = _make_record(reg_root, "aaa", digest_body=_digest_body("aaa", extra="\nA new paraphrased line.\n"))
    _write_registry(reg_root, [r1b])
    assert reg.load_runtime(root=reg_root).global_hash() != h1


def test_global_hash_sensitive_to_validity_drift(reg_root):
    r1 = _make_record(reg_root, "aaa")
    _write_registry(reg_root, [r1])
    h1 = reg.load_runtime(root=reg_root).global_hash()
    # Edit the digest WITHOUT reconciling → drift → validity flips → hash changes.
    (reg_root / r1["provenance"]["digest"]).write_text(_digest_body("aaa", extra="\ndrifted\n"), "utf-8")
    runtime = reg.load_runtime(root=reg_root)
    assert runtime.global_hash() != h1
    assert runtime.valid_records == []  # the drifted record is excluded


# --------------------------------------------------------------------------- #
# 5-6. Pure AND matcher: positives, negatives, normalization
# --------------------------------------------------------------------------- #
def _ctx(role=None, family=None, track=None, paths=None):
    return reg.normalize_context(role, family, track, paths)


def test_and_matcher_full_positive():
    routing = {
        "roles": ["quality"],
        "task_families": ["difficulty-gate"],
        "tracks": ["core"],
        "owned_paths": ["scripts/audit/**"],
    }
    ctx = _ctx("quality", "difficulty-gate", "core", ["scripts/audit/text_difficulty.py"])
    assert reg.matches(routing, ctx) is True


def test_and_matcher_same_track_wrong_family_negative():
    routing = {"task_families": ["difficulty-gate"], "tracks": ["core"]}
    ctx = _ctx(track="core", family="module-build")  # track intersects, family does not
    assert reg.matches(routing, ctx) is False


def test_and_matcher_missing_dimension_negative():
    routing = {"roles": ["quality"], "task_families": ["difficulty-gate"]}
    ctx = _ctx(role="quality")  # request lacks task_family the record requires
    assert reg.matches(routing, ctx) is False


def test_and_matcher_omitted_dimension_is_wildcard():
    routing = {"roles": ["quality"]}  # no track requirement
    assert reg.matches(routing, _ctx(role="quality", track="anything")) is True


def test_and_matcher_owned_path_glob():
    routing = {"owned_paths": ["scripts/audit/**"]}
    assert reg.matches(routing, _ctx(paths=["scripts/audit/text_difficulty.py"])) is True
    assert reg.matches(routing, _ctx(paths=["scripts/build/x.py"])) is False
    assert reg.matches(routing, _ctx(paths=[])) is False  # record requires a path, none given


def test_no_context_yields_zero_records(reg_root):
    r1 = _make_record(reg_root, "aaa", routing={})  # all-wildcard routing
    _write_registry(reg_root, [r1])
    runtime = reg.load_runtime(root=reg_root)
    pointers, dropped = reg.select_pointers(runtime, _ctx())
    assert pointers == [] and dropped == []


def test_context_normalization_shares_etag(reg_root):
    r1 = _make_record(reg_root, "aaa", routing={"owned_paths": ["scripts/audit/**"]})
    _write_registry(reg_root, [r1])
    a = client.get("/api/knowledge/manifest?owned_path=scripts/audit/a.py&owned_path=scripts/audit/b.py")
    b = client.get(
        "/api/knowledge/manifest?owned_path=scripts/audit/b.py"
        "&owned_path=scripts/audit/a.py&owned_path=scripts/audit/a.py"
    )
    assert a.status_code == b.status_code == 200
    assert a.content == b.content
    assert a.headers["etag"] == b.headers["etag"]


# --------------------------------------------------------------------------- #
# 7. Pointer field allowlist (no body/summary/source path)
# --------------------------------------------------------------------------- #
def test_pointer_allowlist(reg_root):
    r1 = _make_record(reg_root, "aaa", routing={"roles": ["quality"]}, state="adopted")
    r1["consumer"] = {"kind": "path", "ref": "scripts/audit/text_difficulty.py"}
    _write_registry(reg_root, [r1])
    resp = client.get("/api/knowledge/manifest?role=quality")
    assert resp.status_code == 200
    records = resp.json()["records"]
    assert len(records) == 1
    pointer = records[0]
    assert set(pointer) == {"id", "state", "content_hash", "routing"}
    assert "summary" not in pointer and "provenance" not in pointer
    # No digest path, source URL, ownership, or timestamp leaks anywhere in the body.
    blob = resp.text
    for leak in ("summary", "digest", "source_url", "ownership", "generated_at", "consumer"):
        assert leak not in blob


# --------------------------------------------------------------------------- #
# 8-9. Two-tier 304 + ETag semantics
# --------------------------------------------------------------------------- #
def test_two_tier_304_unrelated_context(reg_root):
    matched = _make_record(reg_root, "aaa", routing={"roles": ["quality"]})
    other = _make_record(reg_root, "zzz", routing={"roles": ["tts"]})
    _write_registry(reg_root, [matched, other])

    # Context A matches 'aaa'; context B (reviewer) matches nothing.
    a0 = client.get("/api/knowledge/manifest?role=quality")
    b0 = client.get("/api/knowledge/manifest?role=reviewer")
    etag_a0, etag_b0 = a0.headers["etag"], b0.headers["etag"]
    global0 = reg.load_runtime(root=reg_root).global_hash()

    # Edit the matched record's routing → global hash changes AND ctx-A projection changes.
    matched_edit = _make_record(reg_root, "aaa", routing={"roles": ["quality"], "tracks": ["core"]})
    _write_registry(reg_root, [matched_edit, other])
    assert reg.load_runtime(root=reg_root).global_hash() != global0

    # Unrelated context B: byte-identical, old If-None-Match → bodyless 304.
    b1 = client.get("/api/knowledge/manifest?role=reviewer", headers={"If-None-Match": etag_b0})
    assert b1.status_code == 304
    assert b1.content == b""
    assert b1.headers["etag"] == etag_b0

    # Matching context A: 200 with a new ETag.
    a1 = client.get("/api/knowledge/manifest?role=quality", headers={"If-None-Match": etag_a0})
    assert a1.status_code == 200
    assert a1.headers["etag"] != etag_a0


@pytest.mark.parametrize("header_tmpl", ['"{h}"', 'W/"{h}"', "*", 'W/"other", "{h}"'])
def test_manifest_etag_variants_yield_304(reg_root, header_tmpl):
    r1 = _make_record(reg_root, "aaa", routing={"roles": ["quality"]})
    _write_registry(reg_root, [r1])
    base = client.get("/api/knowledge/manifest?role=quality")
    etag_hex = base.headers["etag"].strip('"')
    resp = client.get(
        "/api/knowledge/manifest?role=quality",
        headers={"If-None-Match": header_tmpl.format(h=etag_hex)},
    )
    assert resp.status_code == 304
    assert resp.content == b""


def test_manifest_nonmatching_etag_is_200(reg_root):
    r1 = _make_record(reg_root, "aaa", routing={"roles": ["quality"]})
    _write_registry(reg_root, [r1])
    resp = client.get("/api/knowledge/manifest?role=quality", headers={"If-None-Match": '"deadbeef"'})
    assert resp.status_code == 200


# --------------------------------------------------------------------------- #
# 10-11. Per-record endpoint: 304, invalidation, drift/traversal/private/oversize
# --------------------------------------------------------------------------- #
def test_record_body_and_304(reg_root):
    r1 = _make_record(reg_root, "aaa")
    _write_registry(reg_root, [r1])
    resp = client.get("/api/knowledge/record/aaa")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    # ETag is the P1 content hash for the exact normalized body.
    assert resp.headers["etag"].strip('"') == r1["content_hash"].split(":", 1)[1]
    again = client.get("/api/knowledge/record/aaa", headers={"If-None-Match": resp.headers["etag"]})
    assert again.status_code == 304
    assert again.content == b""


def test_record_body_changed_invalidates_etag(reg_root):
    r1 = _make_record(reg_root, "aaa")
    _write_registry(reg_root, [r1])
    old = client.get("/api/knowledge/record/aaa").headers["etag"]
    # Reconcile a real content edit (new digest + new stored hash).
    r1b = _make_record(reg_root, "aaa", digest_body=_digest_body("aaa", extra="\nAdded a paraphrase.\n"))
    _write_registry(reg_root, [r1b])
    new = client.get("/api/knowledge/record/aaa")
    assert new.status_code == 200
    assert new.headers["etag"] != old


def test_record_drift_excluded_but_healthy_served(reg_root):
    healthy = _make_record(reg_root, "aaa")
    drifted = _make_record(reg_root, "bbb")
    _write_registry(reg_root, [healthy, drifted])
    # Silently edit bbb's digest → drift, without touching aaa.
    (reg_root / drifted["provenance"]["digest"]).write_text(_digest_body("bbb", extra="\ndrift\n"), "utf-8")
    assert client.get("/api/knowledge/record/aaa").status_code == 200
    assert client.get("/api/knowledge/record/bbb").status_code == 404
    # Healthy record still routes; drifted one does not.
    runtime = reg.load_runtime(root=reg_root)
    assert [r["id"] for r in runtime.valid_records] == ["aaa"]


@pytest.mark.parametrize("bad_id", ["../etc/passwd", "unknown-id", "UPPER", "has space", "a/b"])
def test_record_bad_ids_are_404(reg_root, bad_id):
    r1 = _make_record(reg_root, "aaa")
    _write_registry(reg_root, [r1])
    assert client.get(f"/api/knowledge/record/{bad_id}").status_code == 404


def test_record_encoded_traversal_is_refused(reg_root):
    r1 = _make_record(reg_root, "aaa")
    _write_registry(reg_root, [r1])
    # Starlette rejects encoded traversal with 403 before the route; 404 is the
    # in-route refusal. Either is a non-leaking refusal.
    assert client.get("/api/knowledge/record/%2e%2e%2fpasswd").status_code in (403, 404)


def test_record_private_local_is_404(reg_root):
    r1 = _make_record(reg_root, "aaa", access_class="private-local")
    _write_registry(reg_root, [r1])
    assert client.get("/api/knowledge/record/aaa").status_code == 404


# --------------------------------------------------------------------------- #
# 12. Budgets: boundary+1, Cyrillic, token estimate, top-5, drop logging
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("n,expected", [(0, 0), (1, 1), (2, 1), (4096, 2048), (4097, 2049)])
def test_est_tokens(n, expected):
    assert reg.est_tokens(n) == expected


def test_record_body_size_boundary(reg_root):
    # Single line of N 'x' + newline normalizes to exactly N bytes.
    ok = _make_record(reg_root, "aaa", digest_body="x" * reg.MAX_RECORD_BYTES + "\n")
    _write_registry(reg_root, [ok])
    body = reg.record_body(reg.load_runtime(root=reg_root), "aaa")
    assert body is not None and len(body[0].encode("utf-8")) == reg.MAX_RECORD_BYTES

    over = _make_record(reg_root, "aaa", digest_body="x" * (reg.MAX_RECORD_BYTES + 1) + "\n")
    _write_registry(reg_root, [over])
    assert reg.record_body(reg.load_runtime(root=reg_root), "aaa") is None
    assert client.get("/api/knowledge/record/aaa").status_code == 404


def test_record_body_cyrillic(reg_root):
    # Cyrillic is 2 UTF-8 bytes/char; ensure bytes + honest hash are correct.
    body_text = "# Заголовок\n\nUkrainian paraphrase: приклад тексту.\n"
    r1 = _make_record(reg_root, "aaa", digest_body=body_text)
    _write_registry(reg_root, [r1])
    resp = client.get("/api/knowledge/record/aaa")
    assert resp.status_code == 200
    assert "приклад" in resp.content.decode("utf-8")
    assert resp.headers["etag"].strip('"') == r1["content_hash"].split(":", 1)[1]


def test_filtered_top5_and_drop_logging(reg_root, caplog):
    records = [
        _make_record(reg_root, f"rec-{i:02d}", routing={"roles": ["quality"]})
        for i in range(7)
    ]
    _write_registry(reg_root, records)
    with caplog.at_level("WARNING"):
        resp = client.get("/api/knowledge/manifest?role=quality")
    ids = [r["id"] for r in resp.json()["records"]]
    assert ids == ["rec-00", "rec-01", "rec-02", "rec-03", "rec-04"]  # lowest-5 by id
    assert "dropped record id" in caplog.text
    assert "rec-05" in caplog.text and "rec-06" in caplog.text


def test_filtered_byte_cap_drops_with_logging(reg_root, caplog):
    # Inflate each pointer via a large *matching* roles list (role=quality still
    # matches) so the ≤1536 byte cap bites before the 5-record cap.
    padded_roles = ["quality"] + [f"padrole-{i}-" + "z" * 60 for i in range(3)]
    records = [
        _make_record(reg_root, f"rec-{i:02d}", routing={"roles": padded_roles})
        for i in range(5)
    ]
    _write_registry(reg_root, records)
    with caplog.at_level("WARNING"):
        resp = client.get("/api/knowledge/manifest?role=quality")
    assert len(resp.content) <= reg.MAX_FILTERED_BYTES
    assert len(resp.json()["records"]) < 5
    assert "dropped record id" in caplog.text


def test_select_bodies_total_cap(reg_root, caplog):
    # Each body ~3 KB; only two fit under the 8 KB selected-body budget.
    body = "y" * 3000 + "\n"
    records = [_make_record(reg_root, f"rec-{i}", digest_body=body) for i in range(4)]
    _write_registry(reg_root, records)
    runtime = reg.load_runtime(root=reg_root)
    with caplog.at_level("WARNING"):
        selected, dropped = reg.select_bodies(runtime, ["rec-0", "rec-1", "rec-2", "rec-3"])
    total = sum(len(item["body"].encode("utf-8")) for item in selected)
    assert total <= reg.MAX_SELECTED_BODIES_BYTES
    assert dropped  # at least one dropped
    assert "select_bodies dropped" in caplog.text


def test_request_caps_reject_excess(reg_root):
    r1 = _make_record(reg_root, "aaa")
    _write_registry(reg_root, [r1])
    many = "&".join(f"owned_path=p{i}" for i in range(reg.MAX_OWNED_PATHS + 1))
    assert client.get(f"/api/knowledge/manifest?{many}").status_code == 422
    long_path = "x" * (reg.MAX_OWNED_PATH_LEN + 1)
    assert client.get(f"/api/knowledge/manifest?owned_path={long_path}").status_code == 422
    long_role = "r" * (reg.MAX_QUERY_VALUE_LEN + 1)
    assert client.get(f"/api/knowledge/manifest?role={long_role}").status_code == 422


# --------------------------------------------------------------------------- #
# 15. No side effects: static guard over the P2 modules
# --------------------------------------------------------------------------- #
def test_no_network_or_subprocess_imports():
    """Static proof: neither P2 module imports network/subprocess/db machinery."""
    import ast

    forbidden = {"subprocess", "socket", "sqlite3", "requests", "httpx", "urllib", "http"}
    root = Path(__file__).resolve().parents[1]
    for rel in ("scripts/research/registry.py", "scripts/api/knowledge_router.py"):
        tree = ast.parse((root / rel).read_text("utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        leaked = imported & forbidden
        assert not leaked, f"{rel} imports forbidden modules: {leaked}"
