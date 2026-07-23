"""Tests for the runnable Kimi OAuth refresh-chain canary."""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

from scripts.canary import kimi_oauth_canary as canary
from scripts.lib import kimi_coding_oauth


class _RefreshServer:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.bodies: list[str] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                outer.bodies.append(self.rfile.read(length).decode("utf-8"))
                body = json.dumps(outer.payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args: object) -> None:
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> _RefreshServer:
        self.thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def _credential(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "access_token": "old-access",
                "refresh_token": "old-refresh",
                "expires_at": time.time() + 3_600,
            }
        ),
        encoding="utf-8",
    )
    path.chmod(0o600)


def test_force_refresh_proves_grant_and_rotates_credential(tmp_path: Path, monkeypatch) -> None:
    credential = tmp_path / "kimi-code.json"
    _credential(credential)
    monkeypatch.setenv("KIMI_CODE_CREDENTIALS_PATH", str(credential))
    payload = {"access_token": "new-access", "refresh_token": "new-refresh", "expires_in": 900}

    with _RefreshServer(payload) as server:
        monkeypatch.setenv("KIMI_CODE_OAUTH_HOST", server.url)
        token = kimi_coding_oauth.force_refresh_token()

    assert token == "new-access"
    assert "grant_type=refresh_token" in server.bodies[0]
    stored = json.loads(credential.read_text(encoding="utf-8"))
    assert stored["access_token"] == "new-access"
    assert stored["refresh_token"] == "new-refresh"


def test_success_does_not_print_or_alert_token(capsys) -> None:
    alerts: list[str] = []
    result = canary.run_canary(refresh=lambda: "do-not-print-this-token", alert=alerts.append)

    assert result == canary.CanaryResult(exit_code=0, alert_posted=False)
    assert alerts == []
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "do-not-print-this-token" not in captured.out + captured.err


def test_missing_credentials_alerts_with_compatible_exit_code(capsys) -> None:
    alerts: list[str] = []
    result = canary.run_canary(
        refresh=lambda: (_ for _ in ()).throw(kimi_coding_oauth.NoCredentialsError("missing")),
        alert=lambda kind: alerts.append(kind) or True,
    )

    assert result == canary.CanaryResult(exit_code=2, alert_posted=True, failure_kind="credentials")
    assert alerts == ["credentials"]
    assert "FAIL (credentials)" in capsys.readouterr().err


def test_refresh_failure_is_redacted_even_when_alert_delivery_fails(capsys) -> None:
    secret = "refresh-token-must-not-leak"
    result = canary.run_canary(
        refresh=lambda: (_ for _ in ()).throw(kimi_coding_oauth.RefreshFailedError(secret)),
        alert=lambda _: False,
    )

    assert result == canary.CanaryResult(exit_code=3, alert_posted=False, failure_kind="refresh")
    captured = capsys.readouterr()
    assert "FAIL (refresh)" in captured.err
    assert secret not in captured.out + captured.err


def test_failure_alert_uses_action_required_fleet_comms_message() -> None:
    with patch("scripts.canary.kimi_oauth_canary._channels.post") as post:
        assert canary.post_failure_alert("refresh") is True

    args, kwargs = post.call_args
    assert args[0] == "fleet-comms"
    assert args[1] == "kimi"
    assert "failure_kind=refresh" in args[2]
    assert kwargs["to_agents"] == ["kimi", "claude-infra"]
    assert kwargs["kind"] == "system"
    assert kwargs["priority"] == "action_required"
    assert kwargs["auto_snapshot"] is False
    assert kwargs["verify_citations"] is False


def test_failure_alert_does_not_raise_when_fleet_comms_is_unavailable(capsys) -> None:
    with patch("scripts.canary.kimi_oauth_canary._channels.post", side_effect=RuntimeError("down")):
        assert canary.post_failure_alert("local_io") is False

    assert "fleet-comms alert failed: RuntimeError" in capsys.readouterr().err
