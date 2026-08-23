"""Tests for API health tmp usability canary integration (#7164)."""

from __future__ import annotations

from unittest.mock import patch

from scripts.api import main as api_main


def test_tmp_usability_canary_normal() -> None:
    res = api_main._tmp_usability_canary()
    assert isinstance(res, dict)
    assert "ok" in res
    assert "writable" in res
    assert "error" in res


def test_tmp_usability_canary_fail_open_on_exception() -> None:
    with patch("scripts.audit.check_tmp_usability.probe_tmp_usability", side_effect=RuntimeError("unexpected probe crash")):
        res = api_main._tmp_usability_canary()
        assert res["ok"] is True
        assert res["writable"] is True
        assert res["error"] is None
        assert res.get("probe_error") is True


def test_collect_health_orient_data_includes_tmp_usability(monkeypatch) -> None:
    fake_canary_result = {
        "ok": True,
        "writable": True,
        "error": None,
        "used_pct": 12.3,
        "free_bytes": 1024 * 1024 * 1024,
    }
    monkeypatch.setattr(api_main, "_tmp_usability_canary", lambda: fake_canary_result)
    health = api_main._collect_health_orient_data()
    assert health["tmp_usability_ok"] is True
    assert health["tmp_usability"] == fake_canary_result


def test_collect_health_orient_data_surfaces_degraded_tmp(monkeypatch) -> None:
    fake_canary_result = {
        "ok": False,
        "writable": False,
        "error": "edquot",
        "used_pct": 99.9,
        "free_bytes": 0,
    }
    monkeypatch.setattr(api_main, "_tmp_usability_canary", lambda: fake_canary_result)
    health = api_main._collect_health_orient_data()
    assert health["tmp_usability_ok"] is False
    assert health["tmp_usability"]["error"] == "edquot"
