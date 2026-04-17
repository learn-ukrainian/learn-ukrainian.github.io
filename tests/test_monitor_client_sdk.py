"""Tests for scripts/monitor_client.py SDK + ETag + deprecation (GH #1309).

The SDK is how agents are supposed to consume the Monitor API on
cold-start. These tests exercise the contract end-to-end against the
TestClient (no real socket), including the cache-hit path where
nothing leaves the machine.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure ``scripts/`` is on sys.path for direct ``ai_agent_bridge``
# imports (conftest.py does this for the suite; we add it here too
# so running this file standalone still works).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from ai_agent_bridge import _monitor_cache as cache
from ai_agent_bridge import monitor_client

import scripts.api.main as api_main
import scripts.api.rules_router as rules_router
import scripts.api.session_router as session_router

client = TestClient(api_main.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------
# ETag support on /api/rules and /api/session/current
# ---------------------------------------------------------------------


@pytest.fixture
def stub_rules(monkeypatch, tmp_path):
    rule = tmp_path / "rule.md"
    rule.write_text("# Rules\n\nBe careful.\n", encoding="utf-8")
    monkeypatch.setattr(rules_router, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(rules_router, "RULE_SOURCES", ("rule.md",))
    return rule


@pytest.fixture
def stub_session(monkeypatch, tmp_path):
    state = tmp_path / "docs" / "session-state"
    state.mkdir(parents=True)
    (state / "current.md").write_text("# Now\nThinking.\n", encoding="utf-8")
    monkeypatch.setattr(session_router, "PROJECT_ROOT", tmp_path)
    return state


def test_rules_etag_matches_returns_304(stub_rules):
    resp = client.get("/api/rules")
    assert resp.status_code == 200
    etag = resp.headers["etag"]

    # Client sends the same ETag back; server 304s.
    resp_304 = client.get("/api/rules", headers={"If-None-Match": etag})
    assert resp_304.status_code == 304
    assert resp_304.content == b""
    assert resp_304.headers["etag"] == etag


def test_rules_etag_mismatch_returns_200(stub_rules):
    resp = client.get("/api/rules", headers={"If-None-Match": '"not-a-real-hash"'})
    assert resp.status_code == 200
    assert "Be careful." in resp.text


def test_rules_etag_wildcard_returns_304(stub_rules):
    resp_304 = client.get("/api/rules", headers={"If-None-Match": "*"})
    assert resp_304.status_code == 304


def test_rules_weak_etag_matches(stub_rules):
    resp = client.get("/api/rules")
    bare_hash = resp.headers["etag"].strip('"')
    resp_304 = client.get(
        "/api/rules", headers={"If-None-Match": f'W/"{bare_hash}"'},
    )
    assert resp_304.status_code == 304


def test_session_etag_matches_returns_304(stub_session):
    resp = client.get("/api/session/current")
    assert resp.status_code == 200
    etag = resp.headers["etag"]

    resp_304 = client.get("/api/session/current", headers={"If-None-Match": etag})
    assert resp_304.status_code == 304


# ---------------------------------------------------------------------
# SDK — cache-hit round-trip
# ---------------------------------------------------------------------


class _TestClientAdapter:
    """Thin shim so ``MonitorClient`` can hit FastAPI's TestClient.

    The SDK uses urllib against localhost; we monkeypatch its ``_get``
    method to use the in-process TestClient instead. That avoids
    spinning up a real HTTP server for the test, which would slow
    things down and introduce port-collision flake.
    """

    def __init__(self, c: TestClient) -> None:
        self.c = c

    def __call__(self, path: str, *, headers=None):
        r = self.c.get(path, headers=headers or {})
        resp_headers = {k.lower(): v for k, v in r.headers.items()}
        # TestClient returns bytes; SDK expects a decoded str.
        return r.status_code, r.content.decode("utf-8", errors="replace"), resp_headers


@pytest.fixture
def sdk(monkeypatch, tmp_path, stub_rules, stub_session):
    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    # Start from an empty cache every time.
    cache.invalidate()

    sdk_client = monitor_client.MonitorClient(base_url="http://testserver")
    adapter = _TestClientAdapter(client)
    monkeypatch.setattr(sdk_client, "_get", adapter)
    return sdk_client


def test_sdk_first_call_goes_to_network(sdk):
    result = sdk.rules()
    assert result.source == "network"
    assert "Be careful." in result.body
    assert result.hash


def test_sdk_second_call_hits_cache(sdk):
    first = sdk.rules()
    second = sdk.rules()

    assert first.source == "network"
    assert second.source == "cache"
    # Same bytes either way.
    assert first.body == second.body
    assert first.hash == second.hash


def test_sdk_bootstrap_returns_both_components(sdk):
    boot = sdk.bootstrap()
    assert set(boot) == {"rules", "session"}
    assert "Be careful." in boot["rules"].body
    assert "Thinking." in boot["session"].body


def test_sdk_not_modified_path(sdk, monkeypatch):
    """When the manifest hash matches cache but local cache lookup
    accidentally misses (e.g. file was evicted between manifest read
    and component read), the SDK falls back to a 304-aware GET and
    still succeeds.

    This simulates the edge case where a client just invalidated its
    cache but the server ETag hasn't changed. We hand-seed the cache
    under the expected key, invalidate it, then ask for rules. The
    server will see If-None-Match with the matching ETag, return
    304, and the SDK will fall through to a fresh GET without the
    header.
    """
    # Populate the cache first so the second call is a cache-miss path.
    sdk.rules()
    # Evict the cache but keep the manifest hash in hand.
    cache.invalidate("rules")

    result = sdk.rules()
    # After eviction the SDK has to re-fetch — either as a 304 fall-
    # through or a plain 200. Either way the body must be populated.
    assert result.source in {"network", "not-modified"}
    assert "Be careful." in result.body


# ---------------------------------------------------------------------
# Deprecation headers
# ---------------------------------------------------------------------


def test_blue_live_status_carries_deprecation_header():
    resp = client.get("/api/blue/live-status")
    assert resp.status_code == 200
    assert resp.headers.get("X-Deprecated") == "true"
    assert resp.headers.get("X-Deprecated-Use") == "/api/state/build-status"


def test_comms_live_activity_carries_deprecation_header():
    resp = client.get("/api/comms/live-activity")
    # Endpoint may 500 if the broker DB isn't available in the test
    # environment — the deprecation header must still be on the
    # response so clients see it either way.
    assert resp.headers.get("X-Deprecated") == "true"
    assert resp.headers.get("X-Deprecated-Use") == "/api/state/build-status"


# ---------------------------------------------------------------------
# Post-review regression tests (GH #1309 final review pass)
# ---------------------------------------------------------------------


def test_manifest_hash_matches_rules_etag_and_header(stub_rules):
    """Codex final-review coverage gap: assert the three hashes match.

    /api/state/manifest's ``rules.hash`` must equal the ETag on
    /api/rules AND the X-Rules-Hash header. They all derive from the
    same sha256 by design, but tests never asserted it — which means
    the contract could silently drift.
    """
    manifest = client.get("/api/state/manifest").json()
    manifest_hash = manifest["rules"]["hash"]
    assert manifest_hash, "manifest.rules.hash must be set"

    resp = client.get("/api/rules")
    etag = resp.headers["etag"].strip('"')
    x_hash = resp.headers["x-rules-hash"]

    assert etag == manifest_hash == x_hash


def test_manifest_hash_matches_session_etag_and_header(stub_session):
    manifest = client.get("/api/state/manifest").json()
    manifest_hash = manifest["session"]["hash"]
    assert manifest_hash

    resp = client.get("/api/session/current")
    etag = resp.headers["etag"].strip('"')
    x_hash = resp.headers["x-session-hash"]

    assert etag == manifest_hash == x_hash


def test_sdk_survives_session_404(monkeypatch, tmp_path):
    """bootstrap() must not crash when current.md is missing.

    Reviewer CONCERN Gemini-A / #1309: ``urllib.urlopen`` raises
    ``HTTPError`` on any non-2xx response. A fresh checkout without
    ``docs/session-state/current.md`` 404s on /api/session/current,
    which previously crashed the SDK at cold-start.
    """
    # Point session router at a docs/ tree with NO current.md.
    empty_docs = tmp_path / "empty-repo"
    (empty_docs / "docs" / "session-state").mkdir(parents=True)
    monkeypatch.setattr(session_router, "PROJECT_ROOT", empty_docs)

    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    cache.invalidate()

    sdk_client = monitor_client.MonitorClient(base_url="http://testserver")
    monkeypatch.setattr(sdk_client, "_get", _TestClientAdapter(client))

    # Should NOT raise. The session component returns an error sentinel
    # but the SDK still hands back a ComponentResult.
    result = sdk_client.session()
    assert result.source.startswith("error:"), (
        f"expected error sentinel, got source={result.source!r}"
    )
    assert result.body == ""
    assert result.hash == ""
