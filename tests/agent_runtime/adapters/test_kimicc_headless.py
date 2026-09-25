"""Hermetic contract tests for the KimiCC headless Claude Code wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from scripts.agent_runtime.adapters import kimicc as kimicc_adapter
from scripts.agent_runtime.adapters.kimicc import KimiccHarness

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


def _adapter_plan(
    tmp_path: Path,
    monkeypatch,
    *,
    model: str,
    effort: str | None = None,
    mode: str = "read-only",
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
        tool_config=tool_config,
        effort=effort,
    )


def test_headless_wrapper_composes_kimicc_env_without_writing_claude_config(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3")
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
    assert "base=https://api.kimi.com/coding" in result.stdout
    assert "auth=SET" in result.stdout
    assert "model=k3" in result.stdout
    assert "effort=high" in result.stdout
    assert "transport=kimicc" in result.stdout
    assert "arg=-p" in result.stdout
    assert "arg=--bare" in result.stdout
    assert "arg=stream-json" in result.stdout
    assert "arg=--permission-mode" in result.stdout
    assert "arg=plan" in result.stdout
    assert "arg=--tools" in result.stdout
    assert "arg=Read,Grep,Glob,LS" in result.stdout
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


def test_headless_wrapper_workspace_write_does_not_force_plan_mode(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plan = _adapter_plan(tmp_path, monkeypatch, model="k2.7")
    plan.cmd[plan.cmd.index("--mode") + 1] = "workspace-write"
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(plan.cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr
    assert "arg=--permission-mode" not in result.stdout
    assert "arg=Read,Grep,Glob,LS" not in result.stdout


def test_headless_wrapper_keeps_explicit_tools_profile(tmp_path: Path) -> None:
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
            "k2.7",
            "--mode",
            "read-only",
            "--prompt",
            "say hi",
            "--tools",
            "mcp__trail__trail_status",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert result.returncode == 0, result.stderr
    assert "arg=--permission-mode" in result.stdout
    assert "arg=plan" in result.stdout
    assert result.stdout.count("arg=--tools") == 1
    assert "arg=mcp__trail__trail_status" in result.stdout
    assert "arg=Read,Grep,Glob,LS" not in result.stdout


def _wrapper_args(stdout: str) -> list[str]:
    return [line.removeprefix("arg=") for line in stdout.splitlines() if line.startswith("arg=")]


def _sources_grant(tmp_path: Path, monkeypatch) -> dict:
    """The delegate review grant, with the adapter's trusted config under tmp_path."""
    trusted = tmp_path / "primary" / ".mcp.json"
    trusted.parent.mkdir(exist_ok=True)
    trusted.write_text('{"mcpServers": {}}', encoding="utf-8")
    monkeypatch.setattr(kimicc_adapter, "trusted_mcp_config_path", lambda: trusted)
    return {
        "mcp_config_path": str(trusted),
        "allowed_tools": "mcp__sources__inspect_word,mcp__sources__verify_words",
        "strict_mcp_config": True,
        kimicc_adapter.REVIEW_VERDICT_MARKER_KEY: True,
    }


def test_headless_wrapper_read_only_review_leaves_plan_mode_and_denies_writes(tmp_path: Path, monkeypatch) -> None:
    """Plan mode refuses MCP calls, so the sources review runs in dontAsk (#8652)."""
    home = tmp_path / "home"
    home.mkdir()
    grant = _sources_grant(tmp_path, monkeypatch)
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3", tool_config=grant)
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(plan.cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr
    args = _wrapper_args(result.stdout)
    assert "plan" not in args
    assert args.count("--permission-mode") == 1
    assert args[args.index("--permission-mode") + 1] == "dontAsk"
    assert args[args.index("--allowedTools") + 1] == grant["allowed_tools"]
    assert args[args.index("--mcp-config") + 1] == grant["mcp_config_path"]
    assert "--strict-mcp-config" in args
    assert args[args.index("--tools") + 1] == "Read,Grep,Glob,LS"
    denied = set(args[args.index("--disallowedTools") + 1].split(","))
    assert {"Write", "Edit", "NotebookEdit", "Bash"} <= denied
    assert "--dangerously-skip-permissions" not in args
    assert "--read-only-review" not in args
    assert args[-2:] == ["--", "say hi"]


def test_headless_wrapper_plain_read_only_keeps_plan_mode(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3")
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(plan.cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr
    args = _wrapper_args(result.stdout)
    assert args[args.index("--permission-mode") + 1] == "plan"
    assert "dontAsk" not in args
    assert "--disallowedTools" not in args


def test_headless_wrapper_workspace_write_review_grant_is_unchanged(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    home.mkdir()
    grant = _sources_grant(tmp_path, monkeypatch)
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3", mode="workspace-write", tool_config=grant)
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(plan.cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr
    args = _wrapper_args(result.stdout)
    assert "--permission-mode" not in args
    assert "--disallowedTools" not in args
    assert "--tools" not in args


def test_headless_wrapper_refuses_review_profile_outside_read_only(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    claude = tmp_path / "claude"
    _fake_claude(claude)
    env = _clean_kimicc_env(home)
    env.update({"KIMICC_CLAUDE_BIN": str(claude), "KIMICC_AUTH_TOKEN": "test-route-token"})

    for mode in ("workspace-write", "danger"):
        result = subprocess.run(
            [str(_WRAPPER), "--model", "k3", "--mode", mode, "--read-only-review", "--prompt", "say hi"],
            cwd=_REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=20,
        )
        assert result.returncode == 2, mode
        assert "--read-only-review requires --mode read-only" in result.stderr
        assert result.stdout == ""


def test_headless_wrapper_read_only_review_with_write_capable_tool_keeps_plan_mode(tmp_path: Path, monkeypatch) -> None:
    """A write-capable MCP tool in the grant never reaches dontAsk (#8652)."""
    home = tmp_path / "home"
    home.mkdir()
    grant = _sources_grant(tmp_path, monkeypatch)
    grant["allowed_tools"] += ",mcp__github__create_pull_request"
    plan = _adapter_plan(tmp_path, monkeypatch, model="k3", tool_config=grant)
    env = _clean_kimicc_env(home)
    env.update({**plan.env_overrides, "KIMICC_AUTH_TOKEN": "test-route-token"})

    result = subprocess.run(plan.cmd, cwd=_REPO_ROOT, env=env, capture_output=True, text=True, timeout=20)

    assert result.returncode == 0, result.stderr
    args = _wrapper_args(result.stdout)
    assert args[args.index("--permission-mode") + 1] == "plan"
    assert "dontAsk" not in args


def test_headless_wrapper_refuses_review_profile_without_strict_mcp_config(tmp_path: Path) -> None:
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
            "--read-only-review",
            "--mcp-config",
            "/any/.mcp.json",
            "--allowedTools",
            "mcp__sources__verify_words",
            "--prompt",
            "say hi",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2
    assert "--read-only-review requires --strict-mcp-config" in result.stderr
    assert result.stdout == ""
