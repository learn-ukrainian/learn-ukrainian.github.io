"""Tests for Monitor client [A, B] failover and mutation idempotency (#7365)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any
from unittest.mock import Mock

import pytest

from scripts.ai_agent_bridge.monitor_client import MonitorClient, _normalize_base_urls

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
    """HTTP 404/500 from host A is an application response, not a transport error, so no failover."""
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


def test_monitor_client_mutation_idempotent_retries_with_stable_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Idempotent mutation (with idempotency key) retries and fails over across [A, B]."""
    calls: list[tuple[str, dict[str, str]]] = []

    def fake_urlopen(req: urllib.request.Request, timeout: float = 3.0) -> _FakeResponse:
        url = req.full_url
        headers = {k: v for k, v in req.headers.items()}
        calls.append((url, headers))
        if url.startswith("http://host-a:8765"):
            raise urllib.error.URLError("Connection reset")
        if url.startswith("http://host-b:8765"):
            return _FakeResponse(200, json.dumps({"registered": True}))
        raise urllib.error.URLError(f"Unknown host {url}")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    client = MonitorClient(base_urls=["http://host-a:8765", "http://host-b:8765"])

    status, body, _ = client._post(
        "/api/agent-monitor/register",
        json_body={"pid": 1234},
        idempotency_key="stable-token-abc",
    )

    assert status == 200
    assert json.loads(body)["registered"] is True
    assert len(calls) == 2
    assert calls[0][0] == "http://host-a:8765/api/agent-monitor/register"
    assert calls[1][0] == "http://host-b:8765/api/agent-monitor/register"

    # Both requests must carry the exact stable idempotency key
    assert calls[0][1].get("Idempotency-key") == "stable-token-abc"
    assert calls[1][1].get("Idempotency-key") == "stable-token-abc"


def test_monitor_client_cluster_readiness_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MonitorClient(base_urls=["http://host-a:8765"])
    client._get = Mock(return_value=(200, json.dumps({"status": "ready", "ready": True, "ha_claimed": False}), {}))  # type: ignore[method-assign]

    readiness = client.cluster_readiness()
    assert readiness["ready"] is True
    assert readiness["ha_claimed"] is False
