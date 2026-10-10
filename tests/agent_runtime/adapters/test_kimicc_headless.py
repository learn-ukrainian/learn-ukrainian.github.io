"""Hermetic contract tests for the KimiCC headless Claude Code wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.kimicc import KimiccHarness
from scripts.agent_runtime.env_sanitize import build_agent_env
from tests.agent_runtime.adapters.kimi_admitted import admitted_tool_config

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
printf 'advisor_disabled=%s\\n' "${CLAUDE_CODE_DISABLE_ADVISOR_TOOL-unset}"
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


def _adapter_plan(
    tmp_path: Path,
    monkeypatch,
    *,
    model: str,
    effort: str | None = None,
    mode: str = "workspace-write",
    tool_config: dict | None = None,
):
    claude = tmp_path / "claude"
    _fake_claude(claude)
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._default_claude_bin", lambda: str(claude))
    monkeypatch.setattr("scripts.agent_runtime.adapters.kimicc._ensure_supported_claude_cli_version", lambda _: None)
    return KimiccHarness().build_invocation(
        prompt="say hi",
        mode=mode,
        cwd=tmp_path,
        model=model,
        task_id="kimicc-headless-contract",
        session_id=None,
        tool_config=admitted_tool_config(tmp_path, tool_config),
        effort=effort,
    )


def test_headless_wrapper_composes_kimicc_env_without_writing_claude_config(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3")
    with monkeypatch.context() as context:
        context.setattr(os, "environ", {**_clean_kimicc_env(home), "KIMICC_AUTH_TOKEN": "test-route-token"})
        env = build_agent_env(provider="kimi", overrides=plan.env_overrides)

    result = subprocess.run(
        plan.cmd,
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
    assert "advisor_disabled=1" in result.stdout
    assert "arg=-p" in result.stdout
    assert "arg=--bare" in result.stdout
    assert "arg=stream-json" in result.stdout
    assert "arg=--permission-mode" not in result.stdout
    assert "arg=--tools" not in result.stdout
    assert "arg=say hi" in result.stdout
    assert "test-route-token" not in result.stdout
    assert not (home / ".claude" / "settings.json").exists()
    assert not (home / ".claude-kimicc").exists()


def test_headless_wrapper_explicit_effort_override_wins_over_k3_default(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3", effort="max")
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(
        plan.cmd,
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "effort=max" in result.stdout
    assert "arg=--effort" in result.stdout
    assert "arg=max" in result.stdout


def test_headless_wrapper_k2_7_does_not_inherit_k3_effort_default(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plan = _adapter_plan(tmp_path, monkeypatch, model="k2.7")
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(
        plan.cmd,
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
        [str(_WRAPPER), "--model", "k3", "--mode", "workspace-write", "--prompt", "say hi"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 1
    assert "no Kimi API credential" in result.stderr
    assert result.stdout == ""


def test_headless_wrapper_workspace_write_does_not_force_plan_mode(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plan = _adapter_plan(tmp_path, monkeypatch, model="k2.7")
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(plan.cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr
    assert plan.cmd[plan.cmd.index("--mode") + 1] == "workspace-write"
    assert "arg=--permission-mode" not in result.stdout
    assert "arg=--dangerously-skip-permissions" not in result.stdout


@pytest.mark.parametrize("mode_args", [["--mode", "read-only"], ["--mode", "danger"], []])
def test_headless_wrapper_refuses_every_mode_but_workspace_write(tmp_path: Path, mode_args: list[str]) -> None:
    """Kimi: web, UI and backend coding only — the wrapper refuses before auth or Claude runs."""
    home = tmp_path / "home"
    home.mkdir()
    claude = tmp_path / "claude"
    _fake_claude(claude)
    env = _clean_kimicc_env(home)
    env.update({"KIMICC_CLAUDE_BIN": str(claude), "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(
        [str(_WRAPPER), "--model", "k3", *mode_args, "--prompt", "say hi"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 2
    assert "ROUTING REFUSED" in result.stderr
    assert "web, UI and backend coding only" in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize("flag", ["--tools", "--setting-sources"])
def test_headless_wrapper_rejects_the_retired_trail_flags(tmp_path: Path, flag: str) -> None:
    """The trail isolation profile needed read-only; its flags are unknown arguments now."""
    home = tmp_path / "home"
    home.mkdir()
    env = _clean_kimicc_env(home)
    env.update({"KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(
        [str(_WRAPPER), "--model", "k3", "--mode", "workspace-write", "--prompt", "say hi", flag, "x"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 2
    assert f"unsupported KimiCC headless argument '{flag}'" in result.stderr


def _wrapper_args(stdout: str) -> list[str]:
    return [line.removeprefix("arg=") for line in stdout.splitlines() if line.startswith("arg=")]


def _sources_grant(tmp_path: Path) -> dict:
    """The retired delegate review grant: strict sources config, allowlist, review marker."""
    trusted = tmp_path / "primary" / ".mcp.json"
    trusted.parent.mkdir(exist_ok=True)
    trusted.write_text('{"mcpServers": {}}', encoding="utf-8")
    return {
        "mcp_config_path": str(trusted),
        "allowed_tools": "mcp__sources__inspect_word,mcp__sources__verify_words",
        "strict_mcp_config": True,
        "review_verdict_required": True,
    }


@pytest.mark.parametrize("mode", ["read-only", "workspace-write"])
def test_adapter_refuses_the_review_grant_before_the_wrapper(tmp_path: Path, monkeypatch, mode: str) -> None:
    """Kimi seats admit web, UI and backend coding only: the review grant never becomes a wrapper argv (#8652 retired)."""
    with pytest.raises(ValueError, match="KIMI CODING-ONLY"):
        _adapter_plan(tmp_path, monkeypatch, model="k3", mode=mode, tool_config=_sources_grant(tmp_path))


@pytest.mark.parametrize("mode", ["read-only", "workspace-write", "danger"])
def test_headless_wrapper_rejects_the_retired_review_flag(tmp_path: Path, mode: str) -> None:
    """--read-only-review is gone: the wrapper refuses it as an unknown argument in every mode."""
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
            mode,
            "--read-only-review",
            "--mcp-config",
            "/any/.mcp.json",
            "--strict-mcp-config",
            "--prompt",
            "say hi",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2, mode
    assert "unsupported KimiCC headless argument '--read-only-review'" in result.stderr
    assert result.stdout == ""


def test_headless_wrapper_forwards_a_strict_mcp_config_on_workspace_write(tmp_path: Path, monkeypatch) -> None:
    """Without the (refused) review marker, a strict MCP config is plain plumbing and never enters plan mode."""
    home = tmp_path / "home"
    home.mkdir()
    grant = _sources_grant(tmp_path)
    grant.pop("review_verdict_required")
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3", tool_config=grant)
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(plan.cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr
    args = _wrapper_args(result.stdout)
    assert args[args.index("--mcp-config") + 1] == grant["mcp_config_path"]
    assert "--strict-mcp-config" in args
    assert "--permission-mode" not in args
    assert "dontAsk" not in args
