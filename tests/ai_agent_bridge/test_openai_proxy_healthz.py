"""Tests for /healthz endpoint TTL caching (issue #2029)."""

from __future__ import annotations

import threading
import time

from fastapi.testclient import TestClient

from scripts.ai_agent_bridge import openai_proxy as proxy


def _client() -> TestClient:
    return TestClient(proxy.app)


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


def test_healthz_cache_hit(monkeypatch):
    """Probe once, advance clock 30s, probe again — only 1 set of calls."""
    probes, calls = _make_probes()
    monkeypatch.setattr(proxy, "_BACKEND_PROBES", probes)

    _clear_cache()

    # First call — fills cache
    response1 = _client().get("/healthz")
    assert response1.status_code == 200
    assert response1.json()["backends"] == {
        "codex": True,
        "gemini": True,
        "claude": True,
        "hermes": True,
    }
    assert calls == {"codex": 1, "gemini": 1, "claude": 1, "hermes": 1}

    # Advance clock 30s (within 60s TTL) — capture original before patching
    real_monotonic = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: real_monotonic() + 30)

    # Second call — should use cache, no new probes
    response2 = _client().get("/healthz")
    assert response2.status_code == 200
    assert calls == {"codex": 1, "gemini": 1, "claude": 1, "hermes": 1}


# ── Test 2: cache expiry ────────────────────────────────────────────────────


def test_healthz_cache_expiry(monkeypatch):
    """Probe once, advance clock 70s, probe again — 2 sets of calls."""
    probes, calls = _make_probes()
    monkeypatch.setattr(proxy, "_BACKEND_PROBES", probes)

    _clear_cache()

    # First call
    _client().get("/healthz")
    assert calls == {"codex": 1, "gemini": 1, "claude": 1, "hermes": 1}

    # Advance clock 70s (past 60s TTL)
    real_monotonic = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: real_monotonic() + 70)

    # Second call — cache expired, probes run again
    _client().get("/healthz")
    assert calls == {"codex": 2, "gemini": 2, "claude": 2, "hermes": 2}


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
            "hermes": True,
        }

    # Single-flight: at most 1 probe per backend across all calls
    for name in proxy._BACKEND_PROBES:
        assert calls.get(name, 0) <= 1, (
            f"Backend '{name}' probed {calls.get(name, 0)} times, "
            f"expected ≤1 with single-flight"
        )


# ── Test 4: TTL env var override ────────────────────────────────────────────


def test_healthz_ttl_env_var(monkeypatch):
    """BRIDGE_HEALTHZ_TTL_SECS=5 → cache expires at 5s."""
    probes, calls = _make_probes()
    monkeypatch.setattr(proxy, "_BACKEND_PROBES", probes)
    monkeypatch.setattr(proxy, "_BRIDGE_HEALTHZ_TTL_SECS", 5)

    _clear_cache()

    # First call — fills cache with 5s TTL
    _client().get("/healthz")
    assert calls == {"codex": 1, "gemini": 1, "claude": 1, "hermes": 1}

    # Advance 3s — cache still fresh
    real_monotonic = time.monotonic
    monkeypatch.setattr(time, "monotonic", lambda: real_monotonic() + 3)
    _client().get("/healthz")
    assert calls == {"codex": 1, "gemini": 1, "claude": 1, "hermes": 1}

    # Advance another 3s (total 6s) — cache expired
    monkeypatch.setattr(time, "monotonic", lambda: real_monotonic() + 6)
    _client().get("/healthz")
    assert calls == {"codex": 2, "gemini": 2, "claude": 2, "hermes": 2}


# ── Test 5: backend failure does not block other backends ────────────────────


def test_healthz_backend_failure_does_not_block(monkeypatch):
    """One probe fails — other 3 still return results."""
    probes, calls = _make_probes(failing="gemini")
    monkeypatch.setattr(proxy, "_BACKEND_PROBES", probes)

    _clear_cache()

    response = _client().get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    # gemini is the failing probe → False
    assert body["backends"] == {
        "codex": True,
        "gemini": False,
        "claude": True,
        "hermes": True,
    }
    # All 4 probes were attempted
    assert calls == {"codex": 1, "gemini": 1, "claude": 1, "hermes": 1}
