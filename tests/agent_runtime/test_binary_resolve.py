"""Tests for login-PATH agent binary resolution (#7161)."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import pytest

from scripts.agent_runtime.binary_resolve import augment_path_for_login_bins, resolve_agent_binary


def _write_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def test_resolve_finds_binary_only_under_login_local_bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Resolver must find seat CLIs installed under ~/.local/bin when spawn PATH omits it."""
    fake_home = tmp_path / "home"
    local_bin = fake_home / ".local" / "bin"
    binary = local_bin / "cursor-agent"
    _write_executable(binary)

    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    minimal_path = "/usr/bin:/bin"

    resolved = resolve_agent_binary("cursor-agent", path=minimal_path)
    assert resolved == str(binary.resolve())

    # Mutation check: bare shutil.which on the unaugmented PATH must miss.
    assert shutil.which("cursor-agent", path=minimal_path) is None


def test_resolve_finds_binary_only_under_login_opencode_bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_home = tmp_path / "home"
    opencode_bin = fake_home / ".opencode" / "bin"
    binary = opencode_bin / "opencode"
    _write_executable(binary)

    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))
    minimal_path = "/usr/bin:/bin"

    resolved = resolve_agent_binary("opencode", path=minimal_path)
    assert resolved == str(binary.resolve())


def test_augment_path_appends_login_dirs_once(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_home = tmp_path / "home"
    local_bin = str(fake_home / ".local" / "bin")
    opencode_bin = str(fake_home / ".opencode" / "bin")
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    augmented = augment_path_for_login_bins("/usr/bin:/bin")
    parts = augmented.split(os.pathsep)
    assert parts[:2] == ["/usr/bin", "/bin"]
    assert local_bin in parts
    assert opencode_bin in parts
    assert parts.count(local_bin) == 1
    assert parts.count(opencode_bin) == 1


def test_resolve_returns_none_when_binary_genuinely_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path / "home"))
    assert resolve_agent_binary("cursor-agent", path="/usr/bin:/bin") is None


def test_prepare_spawn_command_resolves_argv0(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.agent_runtime.runner import _prepare_spawn_command

    fake_home = tmp_path / "home"
    local_bin = fake_home / ".local" / "bin"
    binary = local_bin / "cursor-agent"
    _write_executable(binary)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    cmd, env = _prepare_spawn_command(["cursor-agent", "--help"], {"PATH": "/usr/bin:/bin"})
    assert cmd[0] == str(binary.resolve())
    assert cmd[1:] == ["--help"]
    assert str(local_bin) in env["PATH"].split(os.pathsep)
