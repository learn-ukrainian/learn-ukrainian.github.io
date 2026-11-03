"""Tests for /healthz endpoint TTL caching (issue #2029)."""

from __future__ import annotations

import threading
import time

from fastapi.testclient import TestClient

from scripts.ai_agent_bridge import openai_proxy as proxy


def _clear_cache() -> None:
    """Reset healthz cache and in-flight state between tests."""
    with proxy._healthz_cache_lock:
        proxy._healthz_cache.clear()
        proxy._healthz_in_flight.clear()


def _make_probes(slow: str | None = None, failing: str | None = None):
    """Build a probe dict that counts calls.

    If *slow* is set to a backend name, that probe sleeps 0.5s before
    returning (to simulate concurrent request overlap).
    If *failing* is set to a backend name, that probe raises an exception.
    """

    calls: dict[str, int] = {}
    lock = threading.Lock()

    def _make(name: str):
        def _probe() -> tuple[bool, str]:
            with lock:
                calls[name] = calls.get(name, 0) + 1
            if name == slow:
                time.sleep(0.5)
            if name == failing:
                raise RuntimeError("probe failed")
            return (True, f"{name}/v1")

        return _probe

    return {name: _make(name) for name in proxy._BACKEND_PROBES}, calls


# ── Test 1: cache hit ──────────────────────────────────────────────────────


# ── Test 2: cache expiry ────────────────────────────────────────────────────


# ── Test 3: concurrent first-request (single-flight) ────────────────────────


def test_healthz_concurrent_first_request(monkeypatch):
    """10 concurrent /healthz with cold cache → max 4 probes (1 per backend)."""
    # Make all probes slow so concurrent requests overlap
    probes, calls = _make_probes(slow="codex")
    monkeypatch.setattr(proxy, "_BACKEND_PROBES", probes)

    _clear_cache()

    errors: list[Exception] = []
    results: list[dict] = []

    def _call():
        try:
            client = TestClient(proxy.app)
            resp = client.get("/healthz")
            results.append(resp.json())
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_call) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Unexpected errors: {errors}"
    assert len(results) == 10

    # Every result should report all 4 backends healthy
    for r in results:
        assert r["ok"] is True
        assert r["backends"] == {
            "codex": True,
            "gemini": True,
            "claude": True,
        }

    # Single-flight: at most 1 probe per backend across all calls
    for name in proxy._BACKEND_PROBES:
        assert calls.get(name, 0) <= 1, (
            f"Backend '{name}' probed {calls.get(name, 0)} times, "
            f"expected ≤1 with single-flight"
        )


# ── Test 4: TTL env var override ────────────────────────────────────────────


# ── Test 5: backend failure does not block other backends ────────────────────
