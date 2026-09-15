"""Cursor provider-window probe: Auto / API / Grok Bot allotments."""

from __future__ import annotations

import io
import json
from urllib.error import URLError

from scripts.agent_runtime.adapters import cursor as cursor_mod


def test_probe_cursor_provider_windows_includes_grok_bot(monkeypatch):
    monkeypatch.setattr(
        cursor_mod,
        "probe_cursor_login",
        lambda **kw: {"is_authenticated": True, "login_state": "authenticated"},
    )
    monkeypatch.setattr(cursor_mod, "_load_cursor_access_token", lambda: "tok")

    calls: list[str] = []

    def fake_urlopen(req, timeout=0):
        url = getattr(req, "full_url", None) or req.get_full_url()
        calls.append(url)
        if "GetCurrentPeriodUsage" in url:
            payload = {
                "billingCycleEnd": 1767225600000,
                "planUsage": {
                    "autoPercentUsed": 12.5,
                    "apiPercentUsed": 40.0,
                    "totalPercentUsed": 18.0,
                },
            }
        elif "GetSandUsageStatus" in url:
            payload = {
                "usagePercent": 33.0,
                "nextResetTimestampUtc": "2026-09-18T00:00:00Z",
                "hasNonZeroIncludedLimit": True,
            }
        else:
            raise AssertionError(url)
        return io.BytesIO(json.dumps(payload).encode())

    # urlopen context manager
    class _CM:
        def __init__(self, buf):
            self._buf = buf

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, *a):
            return self._buf.read(*a)

        def decode(self, *a):  # pragma: no cover
            return self._buf.read().decode(*a)

    def urlopen(req, timeout=0):
        buf = fake_urlopen(req, timeout=timeout)
        return _CM(buf)

    monkeypatch.setattr(cursor_mod.urllib.request, "urlopen", urlopen)
    result = cursor_mod.probe_cursor_provider_windows(timeout_s=3)
    assert result["probe_state"] == "healthy"
    pw = result["provider_windows"]
    assert pw["auto"]["label"] == "Cursor Models (Auto)"
    assert pw["auto"]["used_pct"] == 12.5
    assert pw["api"]["label"] == "Other Models (API)"
    assert pw["api"]["used_pct"] == 40.0
    assert pw["grok_bot"]["label"] == "Grok Bot"
    assert pw["grok_bot"]["window"] == "weekly"
    assert pw["grok_bot"]["used_pct"] == 33.0
    assert pw["total"]["used_pct"] == 18.0
    assert any("GetSandUsageStatus" in u for u in calls)


def test_probe_cursor_grok_bot_failure_is_nonfatal(monkeypatch):
    monkeypatch.setattr(
        cursor_mod,
        "probe_cursor_login",
        lambda **kw: {"is_authenticated": True, "login_state": "authenticated"},
    )
    monkeypatch.setattr(cursor_mod, "_load_cursor_access_token", lambda: "tok")

    class _CM:
        def __init__(self, payload):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, *a):
            return json.dumps(self._payload).encode()

    def urlopen(req, timeout=0):
        url = getattr(req, "full_url", None) or req.get_full_url()
        if "GetSandUsageStatus" in url:
            raise URLError("sand down")
        return _CM(
            {
                "billingCycleEnd": 1767225600000,
                "planUsage": {"autoPercentUsed": 1.0, "apiPercentUsed": 2.0},
            }
        )

    monkeypatch.setattr(cursor_mod.urllib.request, "urlopen", urlopen)
    result = cursor_mod.probe_cursor_provider_windows(timeout_s=3)
    assert result["probe_state"] == "healthy"
    assert result["provider_windows"]["auto"]["used_pct"] == 1.0
    assert result["provider_windows"]["grok_bot"]["used_pct"] is None
    assert result["provider_windows"]["grok_bot"]["probe_state"] == "NEED_PROBE"


def test_empty_windows_always_include_grok_bot_slot(monkeypatch):
    monkeypatch.setattr(
        cursor_mod,
        "probe_cursor_login",
        lambda **kw: {"is_authenticated": False, "login_state": "NEED_LOGIN"},
    )
    result = cursor_mod.probe_cursor_provider_windows(timeout_s=1)
    assert set(result["provider_windows"]) >= {"auto", "api", "grok_bot"}
    assert result["provider_windows"]["grok_bot"]["window"] == "weekly"
