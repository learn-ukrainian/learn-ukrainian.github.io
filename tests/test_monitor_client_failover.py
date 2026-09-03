"""Tests for Monitor client [A, B] failover and mutation idempotency (#7365, #603, #7488)."""

from __future__ import annotations

import http.client
import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from scripts.ai_agent_bridge import monitor_client
from scripts.ai_agent_bridge.monitor_client import MonitorClient, _normalize_base_urls
from scripts.api import epics_router
from scripts.api.config import LIVE_REPO_ROOT
from scripts.api.monitor_context import fixture_context
from scripts.api.route_contracts import ROUTE_CONTRACTS
from tests.epics_monitor_stub import epics_app_for_store

pytestmark = pytest.mark.repo_invariant


class _FakeResponse:
    def __init__(self, status: int = 200, body: str = "{}", headers: dict[str, str] | None = None) -> None:
        self.status = status
        self._body = body.encode("utf-8")
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


def test_normalize_base_urls_various_inputs() -> None:
    # Single string
    assert _normalize_base_urls("http://host-a:8765", None) == ("http://host-a:8765",)
    assert _normalize_base_urls("http://host-a:8765/", None) == ("http://host-a:8765",)

    # Comma-separated string
    assert _normalize_base_urls("http://host-a:8765, http://host-b:8765", None) == (
        "http://host-a:8765",
        "http://host-b:8765",
    )

    # Sequence of strings
    assert _normalize_base_urls(["http://host-a:8765", "http://host-b:8765"], None) == (
        "http://host-a:8765",
        "http://host-b:8765",
    )

    # base_urls kwarg
    assert _normalize_base_urls(None, "http://host-a:8765,http://host-b:8765") == (
        "http://host-a:8765",
        "http://host-b:8765",
    )


def test_normalize_base_urls_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MONITOR_API_URLS", raising=False)
    monkeypatch.delenv("AB_MONITOR_URLS", raising=False)
    monkeypatch.delenv("MONITOR_BASE_URLS", raising=False)
    monkeypatch.delenv("AB_MONITOR_URL", raising=False)
    monkeypatch.delenv("MONITOR_API_URL", raising=False)

    # Default fallback
    assert _normalize_base_urls(None, None) == ("http://localhost:8765",)

    # AB_MONITOR_URLS with comma
    monkeypatch.setenv("AB_MONITOR_URLS", "http://host-a:8765,http://host-b:8765")
    assert _normalize_base_urls(None, None) == ("http://host-a:8765", "http://host-b:8765")

    # AB_MONITOR_URL single endpoint
    monkeypatch.delenv("AB_MONITOR_URLS", raising=False)
    monkeypatch.setenv("AB_MONITOR_URL", "http://127.0.0.1:8765/api/state/summary")
    assert _normalize_base_urls(None, None) == ("http://127.0.0.1:8765",)


def _clear_monitor_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("MONITOR_API_URLS", "AB_MONITOR_URLS", "MONITOR_BASE_URLS", "MONITOR_API_URL", "AB_MONITOR_URL"):
        monkeypatch.delenv(var, raising=False)


def test_normalize_base_urls_strips_endpoint_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    """GH #7489 regression: a base URL must never keep an endpoint path.

    The historical services.sh default exported
    ``AB_MONITOR_URLS=http://localhost:8765/api/state/summary``; the old
    multi-URL branch kept the path, so requests became
    ``/api/state/summary/api/state/manifest``. Every source — constructor arg,
    multi env, single env — now normalizes to the bare origin, once.
    """
    _clear_monitor_env(monkeypatch)

    # Constructor args (string and sequence) lose their paths.
    assert _normalize_base_urls("http://host-a:8765/api/state/summary", None) == ("http://host-a:8765",)
    assert _normalize_base_urls(
        ["http://host-a:8765/api/state/summary", "http://host-b:8765/api/state/summary"], None
    ) == ("http://host-a:8765", "http://host-b:8765")

    # Multi-URL env with paths (the original bug shape).
    monkeypatch.setenv(
        "AB_MONITOR_URLS",
        "http://host-a:8765/api/state/summary, http://host-b:8765/api/state/summary",
    )
    assert _normalize_base_urls(None, None) == ("http://host-a:8765", "http://host-b:8765")


def test_request_never_concatenates_endpoint_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """GH #7489 regression: requests hit <origin>/api/state/manifest, never
    <origin>/api/state/summary/api/state/manifest."""
    _clear_monitor_env(monkeypatch)
    monkeypatch.setenv("AB_MONITOR_URLS", "http://host-a:8765/api/state/summary")
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        calls.append(req.full_url)
        return _FakeResponse(200, "{}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient()
    status, _body, _ = client.get("/api/state/manifest")

    assert status == 200
    assert calls == ["http://host-a:8765/api/state/manifest"]


def test_explicit_empty_string_disables_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """GH #7489: the documented ``AB_MONITOR_URL=""`` disable must be honored.

    An explicitly blank source disables the client — it must NOT fall through
    to a lower-precedence alias or the localhost default, and requests must
    fail soft without touching the network.
    """
    _clear_monitor_env(monkeypatch)
    monkeypatch.setenv("AB_MONITOR_URL", "")

    def forbidden_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        raise AssertionError(f"disabled client attempted network I/O: {req.full_url}")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden_urlopen)

    client = MonitorClient()
    assert client.base_urls == ()
    assert client.base_url == ""
    status, body, _ = client.get("/api/state/manifest")
    assert status == 500
    assert body == ""

    # An explicit blank constructor arg is the same explicit disable.
    assert MonitorClient(base_url="").base_urls == ()
    assert MonitorClient(base_urls="   ").base_urls == ()


def test_canonical_env_var_wins_and_aliases_still_resolve(monkeypatch: pytest.MonkeyPatch) -> None:
    """MONITOR_API_URLS is canonical; deprecated aliases resolve when it is unset."""
    _clear_monitor_env(monkeypatch)
    monkeypatch.setenv("AB_MONITOR_URLS", "http://alias-a:8765")
    monkeypatch.setenv("MONITOR_API_URLS", "http://canonical:8765")
    assert _normalize_base_urls(None, None) == ("http://canonical:8765",)

    monkeypatch.delenv("MONITOR_API_URLS")
    assert _normalize_base_urls(None, None) == ("http://alias-a:8765",)

    # Constructor args always beat every env var.
    assert _normalize_base_urls("http://arg:8765", None) == ("http://arg:8765",)


def test_monitor_client_get_failover_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET fails over from host A to host B upon transport failure."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        if url.startswith("http://host-a:8765"):
            raise urllib.error.URLError("Connection refused")
        if url.startswith("http://host-b:8765"):
            return _FakeResponse(200, json.dumps({"status": "ok", "host": "b"}))
        raise urllib.error.URLError(f"Unknown host {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    status, body, _headers = client._get("/api/state/summary")

    assert status == 200
    assert json.loads(body)["host"] == "b"
    assert len(calls) == 2
    assert calls[0] == "http://host-a:8765/api/state/summary"
    assert calls[1] == "http://host-b:8765/api/state/summary"


def test_monitor_client_get_all_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    """When all hosts in [A, B] fail, transport error is raised."""
    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    with pytest.raises(urllib.error.URLError, match="Connection refused"):
        client._get("/api/state/summary")


def test_monitor_client_get_http_error_does_not_failover(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP 404 from host A is an application response, not a transport error, so no failover."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    status, _body, _ = client._get("/api/missing")

    assert status == 404
    assert len(calls) == 1
    assert calls[0] == "http://host-a:8765/api/missing"


@pytest.mark.parametrize("status", [502, 503, 504])
def test_monitor_client_get_failover_on_ambiguous_transport_statuses(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """HAProxy-shaped 502/503/504 (no app JSON body) is ambiguous transport, so GET hops."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        if url.startswith("http://host-a:8765"):
            raise urllib.error.HTTPError(url, status, "Bad Gateway", {}, None)  # type: ignore[arg-type]
        return _FakeResponse(200, json.dumps({"host": "b"}))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    resp_status, body, _ = client._get("/api/state/summary")

    assert resp_status == 200
    assert json.loads(body)["host"] == "b"
    assert len(calls) == 2


@pytest.mark.parametrize("status", [500, 501, 408, 429])
def test_monitor_client_get_does_not_failover_on_application_statuses(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """500/501/408/429 are always application-origin answers and never trigger a hop."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        raise urllib.error.HTTPError(url, status, "error", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    resp_status, _body, _ = client._get("/api/state/summary")

    assert resp_status == status
    assert len(calls) == 1


def test_monitor_client_get_does_not_failover_on_app_origin_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """A well-formed API 503 is the JSON body shape; a Server header is not required."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        raise urllib.error.HTTPError(
            url,
            503,
            "Service Unavailable",
            {},  # type: ignore[arg-type]
            io.BytesIO(json.dumps({"status": "building"}).encode("utf-8")),
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    status, body, _ = client._get("/api/state/summary")

    assert status == 503
    assert json.loads(body)["status"] == "building"
    assert len(calls) == 1


def test_monitor_client_get_failover_when_uvicorn_header_lacks_app_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``server: uvicorn`` header without the app JSON body is not an answer; GET hops."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        if url.startswith("http://host-a:8765"):
            raise urllib.error.HTTPError(
                url,
                503,
                "Service Unavailable",
                {"server": "uvicorn"},  # type: ignore[arg-type]
                io.BytesIO(b"<html>bad gateway</html>"),
            )
        return _FakeResponse(200, json.dumps({"host": "b"}))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    status, body, _ = client._get("/api/state/summary")

    assert status == 200
    assert json.loads(body)["host"] == "b"
    assert len(calls) == 2


def test_monitor_client_last_exc_does_not_shadow_later_http_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A later HTTP answer (B's 502) must be returned; A's earlier URLError must not win."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        if url.startswith("http://host-a:8765"):
            raise urllib.error.URLError("Connection refused")
        raise urllib.error.HTTPError(url, 502, "Bad Gateway", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    status, _body, _ = client._get("/api/state/summary")

    assert status == 502
    assert len(calls) == 2


def test_monitor_client_later_transport_error_is_raised_not_older_http(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A later transport error is the current outcome; an older 502 must not be returned."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        if url.startswith("http://host-a:8765"):
            raise urllib.error.HTTPError(url, 502, "Bad Gateway", {}, None)  # type: ignore[arg-type]
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    with pytest.raises(urllib.error.URLError, match="Connection refused"):
        client._get("/api/state/summary")
    assert len(calls) == 2


def test_monitor_client_get_failover_on_incomplete_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """``http.client.IncompleteRead`` is an ambiguous transport failure like a socket reset."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        if url.startswith("http://host-a:8765"):
            raise http.client.IncompleteRead(b"partial")
        return _FakeResponse(200, json.dumps({"host": "b"}))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    status, body, _ = client._get("/api/state/summary")

    assert status == 200
    assert json.loads(body)["host"] == "b"
    assert len(calls) == 2


def test_monitor_client_mutation_allowlist_matches_route_contracts() -> None:
    """The client's positive retry allowlist must exactly track the route-contract registry."""
    expected = {
        contract.pattern
        for contract in ROUTE_CONTRACTS
        if contract.mutates and contract.locality == "cluster_authoritative"
    }
    assert expected == monitor_client._CLUSTER_AUTHORITATIVE_MUTATION_PREFIXES


def test_monitor_client_mutation_non_idempotent_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-idempotent mutation (POST without idempotency key) must NEVER fail over across [A, B]."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        calls.append(url)
        raise urllib.error.URLError("Connection reset by peer")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])

    with pytest.raises(urllib.error.URLError, match="Connection reset by peer"):
        client._post("/api/agent-monitor/register", json_body={"pid": 1234})

    # Crucial: only host-a was called; host-b was NOT called!
    assert len(calls) == 1
    assert calls[0] == "http://host-a:8765/api/agent-monitor/register"


def test_monitor_client_keyed_mutation_does_not_retry_while_failover_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A keyed mutation on an allowlisted path must not hop while failover is disabled (#7488)."""
    assert monitor_client._KEYED_MUTATION_FAILOVER_ENABLED is False
    calls: list[tuple[str, dict[str, str]]] = []
    path = "/api/epics/v1/epic:test-failover/handoff"

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        headers = {k: v for k, v in req.headers.items()}
        calls.append((url, headers))
        raise urllib.error.URLError("Connection reset")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])

    with pytest.raises(urllib.error.URLError, match="Connection reset"):
        client._post(
            path,
            json_body={"pid": 1234},
            idempotency_key="stable-token-abc",
        )

    assert len(calls) == 1
    assert calls[0][0] == f"http://host-a:8765{path}"
    assert calls[0][1].get("Idempotency-key") == "stable-token-abc"


def test_keyed_mutation_failover_cannot_fire_while_loopback_fence_holds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#7488: the mutation-failover allowlist is the loopback-fenced epics family.

    Failover cannot hop a keyed mutation while that fence holds: a second
    base would 403 at the fence, and per-host sqlite would duplicate if the
    fence relaxed. Shared atomic key records are not this PR.
    """
    assert monitor_client._KEYED_MUTATION_FAILOVER_ENABLED is False
    expected = {
        contract.pattern
        for contract in ROUTE_CONTRACTS
        if contract.mutates and contract.locality == "cluster_authoritative"
    }
    assert expected == monitor_client._CLUSTER_AUTHORITATIVE_MUTATION_PREFIXES
    assert expected == frozenset({"/api/epics/v1"})

    live = Path(LIVE_REPO_ROOT)
    ctx_root = tmp_path / "ctx"
    ctx_root.mkdir()
    ctx = fixture_context(ctx_root)
    store = ctx.stores.epics_store
    assert store is not None
    epics_router.seed_manifest_inventory(live, store=store, handoff_root=live)
    app = epics_app_for_store(store, ctx_root, live_repo_root=live)
    # Default TestClient peer is not loopback; the fence must refuse before store access.
    remote = TestClient(app)
    for path in (
        "/api/epics/v1/epic:7178/claim",  # allow-hardcoded-epic: loopback fence on allowlisted prefix
        "/api/epics/v1/epic:7178/heartbeat",  # allow-hardcoded-epic: loopback fence on allowlisted prefix
        "/api/epics/v1/epic:7178/handoff",  # allow-hardcoded-epic: loopback fence on allowlisted prefix
        "/api/epics/v1/epic:7178/release",  # allow-hardcoded-epic: loopback fence on allowlisted prefix
        "/api/epics/v1/epic:7178/bundles",  # allow-hardcoded-epic: loopback fence on allowlisted prefix
    ):
        refused = remote.post(path, json={})
        assert refused.status_code == 403, path
        assert refused.json()["detail"] == "loopback mutation required"

    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        calls.append(req.full_url)
        raise urllib.error.URLError("Connection reset")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])
    with pytest.raises(urllib.error.URLError, match="Connection reset"):
        client._post(
            "/api/epics/v1/epic:test-failover/handoff",
            json_body={"type": "state", "body": "working"},
            idempotency_key="stable-token-abc",
        )
    assert calls == ["http://host-a:8765/api/epics/v1/epic:test-failover/handoff"]


def test_monitor_client_mutation_host_affine_never_retries_even_with_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Host-affine mutations (agent-monitor register/heartbeat, ...) never retry, key or not."""
    calls: list[str] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        calls.append(req.full_url)
        raise urllib.error.URLError("Connection reset")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])

    with pytest.raises(urllib.error.URLError, match="Connection reset"):
        client._post(
            "/api/agent-monitor/register",
            json_body={"pid": 1234},
            idempotency_key="stable-token-abc",
        )

    assert len(calls) == 1
    assert calls[0] == "http://host-a:8765/api/agent-monitor/register"


def test_monitor_client_cluster_readiness_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MonitorClient(base_urls=["http://host-a:8765"])
    client._get = Mock(return_value=(200, json.dumps({"status": "ready", "ready": True, "ha_claimed": False}), {}))  # type: ignore[method-assign]

    readiness = client.cluster_readiness()
    assert readiness["ready"] is True
    assert readiness["ha_claimed"] is False
