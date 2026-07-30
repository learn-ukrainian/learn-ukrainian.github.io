"""Hermetic contract tests for the KimiCC headless Claude Code wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_WRAPPER = _REPO_ROOT / "scripts" / "agent_runtime" / "kimicc_headless.sh"


def _fake_claude(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf 'base=%s\\n' "${ANTHROPIC_BASE_URL-unset}"
if [ -n "${ANTHROPIC_AUTH_TOKEN:-}" ]; then printf 'auth=SET\\n'; else printf 'auth=UNSET\\n'; fi
printf 'model=%s\\n' "${ANTHROPIC_MODEL-unset}"
printf 'effort=%s\\n' "${CLAUDE_CODE_EFFORT_LEVEL-unset}"
printf 'transport=%s\\n' "${LEARN_UKRAINIAN_TRANSPORT-unset}"
printf 'arg=%s\\n' "$@"
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _clean_kimicc_env(home: Path) -> dict[str, str]:
    env = os.environ.copy()
    for name in (
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "KIMICC_AUTH_TOKEN",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_API_KEY",
        "KIMI_CODE_CREDENTIALS_PATH",
        "KIMI_CODE_OAUTH_HOST",
        "KIMICC_ENDPOINT",
        "KIMICC_MODEL",
        "KIMICC_BASE_URL",
        "CLAUDE_CONFIG_DIR",
    ):
        env.pop(name, None)
    env["HOME"] = str(home)
    return env


def test_headless_wrapper_composes_kimicc_env_without_writing_claude_config(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    claude = tmp_path / "claude"
    _fake_claude(claude)
    env = _clean_kimicc_env(home)
    env.update({"KIMICC_CLAUDE_BIN": str(claude), "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(
        [str(_WRAPPER), "--model", "k3", "--mode", "read-only", "--prompt", "say hi"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "base=https://api.kimi.com/coding" in result.stdout
    assert "auth=SET" in result.stdout
    assert "model=k3" in result.stdout
    assert "effort=high" in result.stdout
    assert "transport=kimicc" in result.stdout
    assert "arg=-p" in result.stdout
    assert "arg=--bare" in result.stdout
    assert "arg=stream-json" in result.stdout
    assert "arg=say hi" in result.stdout
    assert "test-route-token" not in result.stdout
    assert not (home / ".claude" / "settings.json").exists()
    assert not (home / ".claude-kimicc").exists()


def test_headless_wrapper_explicit_effort_override_wins_over_k3_default(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    claude = tmp_path / "claude"
    _fake_claude(claude)
    env = _clean_kimicc_env(home)
    env.update({"KIMICC_CLAUDE_BIN": str(claude), "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(
        [
            str(_WRAPPER),
            "--model",
            "k3",
            "--mode",
            "read-only",
            "--prompt",
            "say hi",
            "--effort",
            "max",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "effort=high" in result.stdout
    assert "arg=--effort" in result.stdout
    assert "arg=max" in result.stdout


def test_headless_wrapper_k2_7_does_not_inherit_k3_effort_default(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    claude = tmp_path / "claude"
    _fake_claude(claude)
    env = _clean_kimicc_env(home)
    env.update({"KIMICC_CLAUDE_BIN": str(claude), "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(
        [str(_WRAPPER), "--model", "k2.7", "--mode", "read-only", "--prompt", "say hi"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "effort=unset" in result.stdout
    assert "arg=--effort" not in result.stdout


def test_headless_wrapper_refuses_missing_credentials_before_claude_runs(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    claude = tmp_path / "claude"
    _fake_claude(claude)
    env = _clean_kimicc_env(home)
    env.update(
        {
            "KIMICC_CLAUDE_BIN": str(claude),
            "KIMI_CODE_CREDENTIALS_PATH": str(tmp_path / "missing-kimi-login.json"),
        }
    )

    result = subprocess.run(
        [str(_WRAPPER), "--model", "k3", "--mode", "read-only", "--prompt", "say hi"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 1
    assert "no Kimi API credential" in result.stderr
    assert result.stdout == ""
