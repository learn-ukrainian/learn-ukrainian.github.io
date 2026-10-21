"""Production Monitor plane probe: ok when tunneled, degraded fallback when not."""

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
    assert "Mac" in reason
    assert "job-host" not in reason
    assert "notebook" not in reason
    assert "retired" in reason
    line = gate.format_launcher_line(status, reason)
    assert line.startswith("⚠️")
    assert gate.main([]) == 0


def test_healthy_production_monitor_is_ok_even_when_fleet_schema_is_typed_unavailable(monkeypatch) -> None:
    monkeypatch.delenv(gate.ENV_SKIP, raising=False)
    monkeypatch.delenv("LU_MONITOR_LOOPBACK", raising=False)
    monkeypatch.delenv("DELEGATE_MONITOR_API", raising=False)
    payloads = {
        "/api/health": {"status": "ok", "version": "2.0.0"},
        "/api/fleet/health": {
            "observer": "fleet-comms-v1",
            "ok": True,
            "mode": "authority",
            "writes_enabled": False,
            "schema": {
                "db_exists": False,
                "db_error": "authority_unsupported_component",
            },
        },
    }
    requested_paths = []

    def fake_open(url, timeout=0):
        requested_paths.append(str(url).split("8765", 1)[-1])
        for path, body in payloads.items():
            if path in str(url):
                return _Resp(body)
        raise AssertionError(url)

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_open)
    status, reason = gate.check_driver_plane()
    assert status == "ok"
    assert "loopback" in reason
    assert "production" in reason
    assert "Mac" not in reason
    assert "tunnel" not in reason
    assert "job-host" not in reason
    assert requested_paths == ["/api/health"]


def test_unhealthy_production_monitor_is_degraded(monkeypatch) -> None:
    monkeypatch.delenv(gate.ENV_SKIP, raising=False)

    def fake_open(url, timeout=0):
        if "/api/health" in str(url):
            return _Resp({"status": "degraded"})
        raise AssertionError(url)

    monkeypatch.setattr(gate.urllib.request, "urlopen", fake_open)
    status, reason = gate.check_driver_plane()
    assert status == "degraded"
    assert "Mac" in reason
    assert "retired" in reason


def test_help_contract() -> None:
    help_text = gate.build_parser().format_help()
    assert "Probe the production Monitor on loopback before Mac driver launch." in help_text
    assert "job-host" not in help_text
    assert "notebook" not in help_text
    assert "do not use it to start a second Monitor" in help_text
    assert "Examples:" in help_text
    assert "Outputs:" in help_text
    assert "Exit codes:" in help_text
    assert "Related:" in help_text
    assert "Issue: #7177" in help_text
