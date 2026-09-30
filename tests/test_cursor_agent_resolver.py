"""Cursor lookups use ``cursor-agent`` and never execute a generic ``agent`` (#9322)."""

from __future__ import annotations

import os
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import scripts.agent_runtime.binary_resolve as binary_resolve
from scripts.agent_runtime import telemetry as telemetry_mod
from scripts.agent_runtime.adapters import cursor as cursor_mod
from scripts.agent_runtime.adapters.cursor import (
    CursorAdapter,
    CursorAgentMissingError,
    probe_cursor_login,
    resolve_cursor_agent_binary,
)
from scripts.ai_agent_bridge._cursor import _invoke_cursor
from scripts.audit import cursor_judge_calibration as calibration


def _plant(path: Path, marker: Path, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"#!/bin/sh\nprintf '%s\\n' {shlex.quote(label)} >> {shlex.quote(str(marker))}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _isolate(monkeypatch: pytest.MonkeyPatch, home: Path, *path_entries: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", os.pathsep.join(str(entry) for entry in path_entries))
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    monkeypatch.setattr(cursor_mod, "_load_cursor_api_key_from_env_file", lambda path=None: None)


def _marker(marker: Path) -> str:
    return marker.read_text(encoding="utf-8") if marker.exists() else ""


class _Spawn:
    def __init__(self) -> None:
        self.argv: list[list[str]] = []

    def run(self, argv, *args, **kwargs):
        recorded = [str(part) for part in argv]
        self.argv.append(recorded)
        if Path(recorded[0]).name != "cursor-agent":
            raise AssertionError(f"spawned {recorded[0]}")
        return SimpleNamespace(
            returncode=0,
            stdout='{"verdict":"clean","isAuthenticated":false}',
            stderr="",
        )


def _guard(monkeypatch: pytest.MonkeyPatch) -> _Spawn:
    guard = _Spawn()
    monkeypatch.setattr(subprocess, "run", guard.run)
    return guard


def test_resolver_uses_later_cursor_agent_and_never_executes_decoy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """(a) ``cursor-agent`` later on PATH wins; the earlier ``agent`` decoy is not run."""
    decoy_dir = tmp_path / "decoy"
    later_dir = tmp_path / "later"
    marker = tmp_path / "ran"
    home = tmp_path / "home"
    _plant(decoy_dir / "agent", marker, "decoy")
    cursor = later_dir / "cursor-agent"
    _plant(cursor, marker, "cursor-agent")
    _isolate(monkeypatch, home, decoy_dir, later_dir)
    seen: list[str] = []
    original = binary_resolve._which

    def _record(cmd, mode=os.F_OK | os.X_OK, path=None):
        seen.append(cmd)
        return original(cmd, mode=mode, path=path)

    monkeypatch.setattr(binary_resolve, "_which", _record)
    guard = _guard(monkeypatch)
    adapter = CursorAdapter()

    resolved = resolve_cursor_agent_binary()
    plan = adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=tmp_path,
        model="grok-4.7",
        task_id="resolver-a",
        session_id=None,
        tool_config=None,
    )
    probe = probe_cursor_login()
    reply = _invoke_cursor("hello", "composer-2.5")
    judged = calibration.call_cursor("judge this", "composer-2.5")

    cursor_path = cursor.resolve()
    assert Path(resolved) == cursor_path
    assert Path(plan.cmd[0]) == cursor_path
    assert [Path(call[0]) for call in guard.argv] == [cursor_path, cursor_path, cursor_path]
    assert probe["lane"] == "cursor"
    assert reply
    assert judged["verdict"] == "clean"
    assert seen
    assert set(seen) == {"cursor-agent"}
    assert _marker(marker) == ""


def test_resolver_refuses_when_only_decoy_agent_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """(b) No ``cursor-agent`` is a typed refusal. The decoy ``agent`` is not run."""
    decoy_dir = tmp_path / "decoy"
    marker = tmp_path / "ran"
    home = tmp_path / "home"
    _plant(decoy_dir / "agent", marker, "decoy")
    _isolate(monkeypatch, home, decoy_dir)

    def _forbid(argv, *args, **kwargs):
        raise AssertionError(f"spawned {argv[0]}")

    monkeypatch.setattr(subprocess, "run", _forbid)
    adapter = CursorAdapter()

    with pytest.raises(CursorAgentMissingError, match="cursor-agent"):
        resolve_cursor_agent_binary()
    with pytest.raises(CursorAgentMissingError, match="cursor-agent"):
        adapter.build_invocation(
            prompt="hello",
            mode="read-only",
            cwd=tmp_path,
            model="grok-4.7",
            task_id="resolver-b",
            session_id=None,
            tool_config=None,
        )
    with pytest.raises(CursorAgentMissingError, match="cursor-agent"):
        _invoke_cursor("hello", "composer-2.5")
    with pytest.raises(CursorAgentMissingError, match="cursor-agent"):
        calibration.call_cursor("judge this", "composer-2.5")
    probe = probe_cursor_login()

    assert probe["error_kind"] == "missing_binary"
    assert probe["is_authenticated"] is False
    assert _marker(marker) == ""


def test_installer_directory_cursor_agent_beats_decoy_agent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A service PATH that omits the installer dir still selects ``cursor-agent`` there."""
    decoy_dir = tmp_path / "decoy"
    marker = tmp_path / "ran"
    home = tmp_path / "home"
    installed = home / ".local" / "bin" / "cursor-agent"
    _plant(decoy_dir / "agent", marker, "decoy")
    _plant(installed, marker, "installed")
    _isolate(monkeypatch, home, decoy_dir)

    resolved = resolve_cursor_agent_binary()

    assert Path(resolved) == installed.resolve()
    assert _marker(marker) == ""


def _forbid_spawns(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    spawned: list[list[str]] = []

    def _record(argv, *args, **kwargs):
        spawned.append([str(part) for part in argv])
        raise AssertionError(f"spawned {argv[0]}")

    monkeypatch.setattr(cursor_mod.subprocess, "run", _record)
    monkeypatch.setattr(subprocess, "Popen", _record)
    monkeypatch.setattr(telemetry_mod, "_ORIGINAL_SUBPROCESS_POPEN", _record)
    monkeypatch.setattr(telemetry_mod.subprocess, "Popen", _record)
    monkeypatch.setattr(telemetry_mod.subprocess, "run", _record)
    return spawned


@pytest.mark.parametrize("source", ["environment", "stored"])
def test_missing_binary_is_reported_for_either_credential_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    """A missing ``cursor-agent`` stays ``missing_binary`` and does not spawn (#9322)."""
    decoy_dir = tmp_path / "decoy"
    marker = tmp_path / "ran"
    home = tmp_path / "home"
    _plant(decoy_dir / "agent", marker, "decoy")
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", str(decoy_dir))
    if source == "environment":
        monkeypatch.setenv("CURSOR_API_KEY", "fixture-env-key")
    else:
        monkeypatch.delenv("CURSOR_API_KEY", raising=False)
        key_file = home / ".config" / "cursor-agent" / "api.key.env"
        key_file.parent.mkdir(parents=True)
        key_file.write_text("CURSOR_API_KEY=fixture-stored-key\n", encoding="utf-8")
    spawned = _forbid_spawns(monkeypatch)

    probe = probe_cursor_login()

    assert probe["error_kind"] == "missing_binary"
    assert probe["is_authenticated"] is True
    assert spawned == []
    assert _marker(marker) == ""


def test_cursor_version_probe_missing_binary_does_not_spawn(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The version probe calls the resolver and does not spawn when it refuses."""
    decoy_dir = tmp_path / "decoy"
    marker = tmp_path / "ran"
    home = tmp_path / "home"
    _plant(decoy_dir / "agent", marker, "decoy")
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("PATH", str(decoy_dir))
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    spawned = _forbid_spawns(monkeypatch)
    resolver_calls: list[str] = []
    original = cursor_mod.resolve_cursor_agent_binary

    def _counting() -> str:
        resolver_calls.append("call")
        return original()

    monkeypatch.setattr(cursor_mod, "resolve_cursor_agent_binary", _counting)
    telemetry_mod.cursor_cli_version.cache_clear()
    try:
        assert telemetry_mod.cursor_cli_version() is None
        assert telemetry_mod.cursor_cli_version(("agent",)) is None
    finally:
        telemetry_mod.cursor_cli_version.cache_clear()

    assert resolver_calls == ["call"]
    assert spawned == []
    assert _marker(marker) == ""


def test_non_executable_installer_copy_does_not_select_decoy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    decoy_dir = tmp_path / "decoy"
    marker = tmp_path / "ran"
    home = tmp_path / "home"
    installed = home / ".local" / "bin" / "cursor-agent"
    _plant(decoy_dir / "agent", marker, "decoy")
    _plant(installed, marker, "installed")
    installed.chmod(0o644)
    _isolate(monkeypatch, home, decoy_dir)

    with pytest.raises(CursorAgentMissingError, match="cursor-agent"):
        resolve_cursor_agent_binary()
    assert _marker(marker) == ""
