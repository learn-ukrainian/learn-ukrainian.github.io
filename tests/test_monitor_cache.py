"""Tests for ``scripts/ai_agent_bridge/_monitor_cache.py`` (GH #1309).

The persistent cache is the thing that makes the manifest hash useful
— without it, every cold start re-downloads everything. These tests
exercise the round-trip + invalidation contract.
"""

from __future__ import annotations

import hashlib

import pytest

from scripts.ai_agent_bridge import _monitor_cache as cache


@pytest.fixture
def tmp_cache(tmp_path, monkeypatch):
    """Redirect the cache at a fresh tmp dir per test."""
    monkeypatch.setenv("MONITOR_CACHE_DIR", str(tmp_path / "cache"))
    return tmp_path / "cache"


def _h(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def test_roundtrip_put_then_get(tmp_cache):
    body = "# Rules\n\nBe nice.\n"
    cache.put("rules", body, body_hash=_h(body), url="/api/rules?format=markdown")

    got = cache.get("rules", _h(body))
    assert got == body


def test_get_returns_none_when_hash_mismatch(tmp_cache):
    body = "v1"
    cache.put("rules", body, body_hash=_h(body), url="/api/rules")
    # Ask for a different hash — simulates manifest saying content changed.
    assert cache.get("rules", _h("v2")) is None


def test_get_returns_none_without_entry(tmp_cache):
    assert cache.get("missing", "a" * 64) is None


def test_get_with_empty_hash_returns_none(tmp_cache):
    """Empty hash means manifest couldn't compute one — can't validate the cache."""
    body = "v"
    cache.put("rules", body, body_hash=_h(body), url="/api/rules")
    assert cache.get("rules", "") is None


def test_invalidate_one_key(tmp_cache):
    cache.put("rules", "rules body", body_hash="h1", url="/api/rules")
    cache.put("session", "session body", body_hash="h2", url="/api/session/current")

    assert cache.invalidate("rules") == 1

    # Rules gone, session still there.
    assert cache.get("rules", "h1") is None
    assert cache.get("session", "h2") == "session body"


def test_invalidate_all(tmp_cache):
    cache.put("a", "A", body_hash="ha", url="/x")
    cache.put("b", "B", body_hash="hb", url="/y")
    assert cache.invalidate() == 2
    assert cache.get("a", "ha") is None
    assert cache.get("b", "hb") is None


def test_atomic_write_survives_fsync(tmp_cache):
    """The atomic-write path uses os.replace; partial writes must not leak.

    We can't easily simulate a crash in pytest, but we can at least
    assert the final file matches what we wrote — this exercises the
    happy path of ``_atomic_write``.
    """
    body = "x" * 1024 + "y"
    cache.put("big", body, body_hash=_h(body), url="/big")
    assert cache.get("big", _h(body)) == body


def test_env_override_respected(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    monkeypatch.setenv("MONITOR_CACHE_DIR", str(elsewhere))
    cache.put("rules", "body", body_hash="h", url="/api/rules")
    assert (elsewhere / "rules.body").is_file()
    assert (elsewhere / "rules.meta.json").is_file()
