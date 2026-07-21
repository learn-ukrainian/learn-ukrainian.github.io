"""Unit tests for scripts/lib/kimi_coding_oauth.py (kimi login OAuth helper)."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HELPER = _REPO_ROOT / "scripts" / "lib" / "kimi_coding_oauth.py"


def _resolve_venv_python() -> Path | None:
    """Project venv; falls back to the main worktree when run from a linked worktree."""
    candidates = [_REPO_ROOT / ".venv" / "bin" / "python"]
    try:
        common = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if common.returncode == 0 and common.stdout.strip():
            candidates.append(Path(common.stdout.strip()).parent / ".venv" / "bin" / "python")
    except (OSError, subprocess.SubprocessError):
        pass
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


_PYTHON = _resolve_venv_python()

pytestmark = pytest.mark.skipif(_PYTHON is None, reason="project .venv python required")


def _write_credentials(path: Path, *, expires_in: int, with_refresh: bool = True) -> dict:
    data = {
        "access_token": "old-access-token",
        "expires_at": time.time() + expires_in,
        "expires_in": expires_in,
        "token_type": "Bearer",
        "scope": "kimi-code",
    }
    if with_refresh:
        data["refresh_token"] = "old-refresh-token"
    path.write_text(json.dumps(data), encoding="utf-8")
    path.chmod(0o600)
    return data


def _run_helper(cred_path: Path, **env_overrides: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in tuple(env):
        if name.startswith("KIMI_CODE_"):
            env.pop(name, None)
    env.update(
        {
            "KIMI_CODE_CREDENTIALS_PATH": str(cred_path),
            # Guaranteed-unroutable host: any accidental network call fails fast.
            "KIMI_CODE_OAUTH_HOST": "http://127.0.0.1:9",
        }
    )
    env.update(env_overrides)
    return subprocess.run(
        [str(_PYTHON), str(_HELPER), "token"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class _RefreshServer:
    """Minimal /api/oauth/token endpoint recording the last request body."""

    def __init__(self, payload: dict, status: int = 200) -> None:
        self.payload = payload
        self.status = status
        self.bodies: list[str] = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                outer.bodies.append(self.rfile.read(length).decode("utf-8"))
                body = json.dumps(outer.payload).encode("utf-8")
                self.send_response(outer.status)
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


def test_fresh_token_printed_without_network(tmp_path: Path) -> None:
    cred = tmp_path / "kimi-code.json"
    _write_credentials(cred, expires_in=900)
    result = _run_helper(cred)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "old-access-token"
    # Untouched by the run (no refresh, no rotation).
    assert json.loads(cred.read_text(encoding="utf-8"))["refresh_token"] == "old-refresh-token"


def test_expired_token_refreshes_and_writes_back(tmp_path: Path) -> None:
    cred = tmp_path / "kimi-code.json"
    _write_credentials(cred, expires_in=30)  # inside the 120s margin
    payload = {
        "access_token": "new-access-token",
        "refresh_token": "new-refresh-token",
        "expires_in": 900,
        "token_type": "Bearer",
        "scope": "kimi-code",
    }
    with _RefreshServer(payload) as server:
        result = _run_helper(cred, KIMI_CODE_OAUTH_HOST=server.url)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "new-access-token"

    assert len(server.bodies) == 1
    body = server.bodies[0]
    assert "grant_type=refresh_token" in body
    assert "refresh_token=old-refresh-token" in body
    assert "client_id=" in body

    stored = json.loads(cred.read_text(encoding="utf-8"))
    assert stored["access_token"] == "new-access-token"
    assert stored["refresh_token"] == "new-refresh-token"
    assert stored["expires_at"] > time.time() + 600
    assert stat.S_IMODE(cred.stat().st_mode) == 0o600


def test_missing_credential_file_exits_2(tmp_path: Path) -> None:
    result = _run_helper(tmp_path / "nope.json")
    assert result.returncode == 2
    assert "kimi login" in result.stderr


def test_expired_without_refresh_token_exits_2(tmp_path: Path) -> None:
    cred = tmp_path / "kimi-code.json"
    _write_credentials(cred, expires_in=30, with_refresh=False)
    result = _run_helper(cred)
    assert result.returncode == 2
    assert "refresh_token" in result.stderr


def test_refresh_server_error_exits_3(tmp_path: Path) -> None:
    cred = tmp_path / "kimi-code.json"
    _write_credentials(cred, expires_in=30)
    with _RefreshServer({"error": "invalid_grant"}, status=400) as server:
        result = _run_helper(cred, KIMI_CODE_OAUTH_HOST=server.url)
    assert result.returncode == 3
    assert "HTTP 400" in result.stderr
    # Failed refresh must not clobber the stored credential.
    assert json.loads(cred.read_text(encoding="utf-8"))["access_token"] == "old-access-token"
