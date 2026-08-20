"""Notebook driver plane probe: ok when tunneled, degraded fallback when not."""

from __future__ import annotations

import json

from scripts.orchestration import plane_tunnel_gate as gate


class _Resp:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _Resp:
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_skip_env(monkeypatch) -> None:
    monkeypatch.setenv(gate.ENV_SKIP, "1")
    assert gate.check_driver_plane()[0] == "skipped"


def test_unreachable_is_degraded_not_refused(monkeypatch) -> None:
    monkeypatch.delenv(gate.ENV_SKIP, raising=False)

    def boom(*_a, **_k):
        raise TimeoutError("down")

    monkeypatch.setattr(gate.urllib.request, "urlopen", boom)
    status, reason = gate.check_driver_plane(timeout=0.1)
    assert status == "degraded"
    assert "notebook" in reason
    assert "retired" in reason
    line = gate.format_launcher_line(status, reason)
    assert line.startswith("⚠️")
    assert gate.main() == 0


def test_healthy_observer_is_ok(monkeypatch) -> None:
    monkeypatch.delenv(gate.ENV_SKIP, raising=False)
    payloads = {
        "/api/health": {"status": "ok", "version": "2.0.0"},
        "/api/fleet/health": {
            "observer": "fleet-comms-v1",
            "writes_enabled": False,
            "schema": {"db_exists": True, "applied_version": 7},
        },
    }

    def fake_open(url, timeout=0):
        for path, body in payloads.items():
            if path in str(url):
                return _Resp(body)
        raise AssertionError(url)

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_open)
    status, reason = gate.check_driver_plane()
    assert status == "ok"
    assert "loopback" in reason


def test_missing_fleet_db_is_degraded(monkeypatch) -> None:
    monkeypatch.delenv(gate.ENV_SKIP, raising=False)

    def fake_open(url, timeout=0):
        if "/api/health" in str(url):
            return _Resp({"status": "ok"})
        return _Resp({"schema": {"db_exists": False}})

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_open)
    assert gate.check_driver_plane()[0] == "degraded"
