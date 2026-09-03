"""Cursor login-probe honesty tests (routing-budget stale-lane fix, #7646).

Root cause: ``probe_cursor_login`` only trusted the CLI's own ``status
--format json`` (``isAuthenticated``), which reflects a different credential
path (``~/.config/cursor/auth.json``) than ``CURSOR_API_KEY`` (env or
``~/.config/cursor-agent/api.key.env``). A driver env with a live
``CURSOR_API_KEY`` — dispatch already resolves and uses this key
independently (see ``CursorAdapter.build_invocation``) — was still reported
NEED_LOGIN whenever the CLI's own session state lagged or errored.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters import cursor as cursor_mod


def _fake_run(payload: dict) -> SimpleNamespace:
    return SimpleNamespace(stdout=json.dumps(payload), stderr="", returncode=0)


def test_cli_authenticated_true_is_authenticated(monkeypatch):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda: None)
    monkeypatch.setattr(cursor_mod.subprocess, "run", lambda *a, **k: _fake_run({"isAuthenticated": True}))

    result = cursor_mod.probe_cursor_login()
    assert result["is_authenticated"] is True
    assert result["login_state"] == "authenticated"


def test_cli_need_login_with_env_api_key_is_authenticated(monkeypatch):
    """Root-cause regression: cursor-agent status can lag a live CURSOR_API_KEY."""
    monkeypatch.setenv("CURSOR_API_KEY", "fixture-cursor-key")
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda: None)
    monkeypatch.setattr(cursor_mod.subprocess, "run", lambda *a, **k: _fake_run({"isAuthenticated": False}))

    result = cursor_mod.probe_cursor_login()
    assert result["is_authenticated"] is True
    assert result["login_state"] == "authenticated"


def test_cli_need_login_with_key_file_is_authenticated(monkeypatch):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda: "file-fixture-key")
    monkeypatch.setattr(cursor_mod.subprocess, "run", lambda *a, **k: _fake_run({"isAuthenticated": False}))

    result = cursor_mod.probe_cursor_login()
    assert result["is_authenticated"] is True
    assert result["login_state"] == "authenticated"


def test_cli_need_login_no_key_anywhere_is_need_login(monkeypatch):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda: None)
    monkeypatch.setattr(cursor_mod.subprocess, "run", lambda *a, **k: _fake_run({"isAuthenticated": False}))

    result = cursor_mod.probe_cursor_login()
    assert result["is_authenticated"] is False
    assert result["login_state"] == "NEED_LOGIN"


def test_missing_binary_with_env_api_key_is_authenticated(monkeypatch):
    """CLI absent entirely (e.g. a PATH race) must not shadow a live API key."""
    monkeypatch.setenv("CURSOR_API_KEY", "fixture-cursor-key")
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda: None)

    def _raise(*_a, **_k):
        raise FileNotFoundError("cursor-agent not found")

    monkeypatch.setattr(cursor_mod.subprocess, "run", _raise)

    result = cursor_mod.probe_cursor_login()
    assert result["is_authenticated"] is True
    assert result["login_state"] == "authenticated"


def test_missing_binary_no_key_is_need_login(monkeypatch):
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda: None)

    def _raise(*_a, **_k):
        raise FileNotFoundError("cursor-agent not found")

    monkeypatch.setattr(cursor_mod.subprocess, "run", _raise)

    result = cursor_mod.probe_cursor_login()
    assert result["is_authenticated"] is False
    assert result["login_state"] == "NEED_LOGIN"
    assert result["error_kind"] == "missing_binary"


def test_cursor_cli_binary_resolves_home_local_when_path_empty(tmp_path, monkeypatch):
    """systemd PATH often omits ~/.local/bin; still find cursor-agent there."""
    fake_home = tmp_path / "home"
    fake_bin = fake_home / ".local" / "bin" / "cursor-agent"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    fake_bin.chmod(0o755)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("PATH", "")

    assert cursor_mod._cursor_cli_binary() == str(fake_bin)


def test_path_missing_binary_and_no_key_is_need_login_missing_binary(tmp_path, monkeypatch):
    """Empty PATH, no ~/.local/bin/cursor-agent, no API key → NEED_LOGIN/missing_binary."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda: None)

    result = cursor_mod.probe_cursor_login()
    assert result["is_authenticated"] is False
    assert result["login_state"] == "NEED_LOGIN"
    assert result["error_kind"] == "missing_binary"
