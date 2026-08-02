"""Contracts for non-destructive Entire 0.8.42 native harness onboarding."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEX_HOOKS = ROOT / "agents_extensions" / "codex" / "hooks.json"
CODEX_CONFIG = ROOT / "agents_extensions" / "codex" / "config.toml"
CLAUDE_SETTINGS = ROOT / "agents_extensions" / "shared" / "settings.json"
ENTIRE_SETTINGS = ROOT / ".entire" / "settings.json"
OPENCODE_PLUGIN = ROOT / ".opencode" / "plugins" / "entire.ts"
OPENCODE_EXIT_TRAP = ROOT / ".opencode" / "plugins" / "entire-exit.ts"


def _hook_commands(payload: dict, event: str) -> list[dict]:
    return [
        hook
        for entry in payload["hooks"][event]
        for hook in entry.get("hooks", [])
    ]


def _entire_hooks(payload: dict, harness: str) -> list[dict]:
    needle = f"entire hooks {harness}"
    return [
        hook
        for event in payload["hooks"]
        for hook in _hook_commands(payload, event)
        if needle in hook.get("command", "")
    ]


def test_entire_settings_are_pinned_private_and_nontelemetric() -> None:
    settings = json.loads(ENTIRE_SETTINGS.read_text(encoding="utf-8"))
    assert settings == {
        "enabled": True,
        "external_agents": True,
        "strategy_options": {
            "checkpoint_remote": {
                "provider": "github",
                "repo": "learn-ukrainian/entire-checkpoints-private",
            }
        },
        "telemetry": False,
    }


def test_codex_cli_and_desktop_share_four_composed_entire_hooks() -> None:
    hooks = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))
    config = tomllib.loads(CODEX_CONFIG.read_text(encoding="utf-8"))
    entire_hooks = _entire_hooks(hooks, "codex")

    assert config["features"]["hooks"] is True
    assert len(entire_hooks) == 4
    assert {
        command["command"].rsplit(" ", 1)[-1].rstrip("'")
        for command in entire_hooks
    } == {"session-start", "post-tool-use", "user-prompt-submit", "stop"}
    assert all(command["timeout"] == 30 for command in entire_hooks)
    assert all("if ! command -v entire" in command["command"] for command in entire_hooks)

    # Existing project hook semantics must survive onboarding unchanged. The
    # stock 0.8.42 installer rewrites these objects and drops this metadata.
    session_setup = next(
        hook
        for hook in _hook_commands(hooks, "SessionStart")
        if "session-setup.sh" in hook["command"]
    )
    assert session_setup == {
        "type": "command",
        "command": 'bash "$(git rev-parse --show-toplevel)/.codex/hooks/session-setup.sh"',
        "timeout": 15,
        "statusMessage": "Checking learn-ukrainian session state",
        "additionalContextLimit": 1200,
    }
    policy = next(
        hook
        for hook in _hook_commands(hooks, "PreToolUse")
        if "codex_hook_entry.sh" in hook["command"]
    )
    assert policy["timeout"] == 45
    assert policy["statusMessage"] == "Running Codex tool policy"


def test_claude_hosted_models_share_seven_composed_claude_code_hooks() -> None:
    settings = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    entire_hooks = _entire_hooks(settings, "claude-code")

    assert len(entire_hooks) == 7
    assert all(command["timeout"] == 30 for command in entire_hooks)
    assert all("if ! command -v entire" in command["command"] for command in entire_hooks)
    assert settings["permissions"]["deny"] == ["Read(./.entire/metadata/**)"]

    existing = {
        hook["command"]: hook
        for event in settings["hooks"]
        for hook in _hook_commands(settings, event)
        if "entire hooks" not in hook["command"]
    }
    assert existing["$CLAUDE_PROJECT_DIR/.claude/hooks/session-setup.sh"]["timeout"] == 10
    assert existing["$CLAUDE_PROJECT_DIR/.claude/hooks/guard-primary-checkout-write.py"][
        "timeout"
    ] == 5
    assert existing["$CLAUDE_PROJECT_DIR/.claude/hooks/thread-lease-heartbeat.sh"][
        "timeout"
    ] == 3
    assert existing["$CLAUDE_PROJECT_DIR/.claude/hooks/release-thread-lease.sh"][
        "timeout"
    ] == 5


def test_entire_hooks_fail_open_when_cli_is_unavailable() -> None:
    codex = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))
    claude = json.loads(CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    commands = _entire_hooks(codex, "codex") + _entire_hooks(claude, "claude-code")

    for hook in commands:
        result = subprocess.run(
            ["/bin/sh", "-c", hook["command"]],
            input="{}\n",
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": "/usr/bin:/bin"},
            timeout=5,
        )
        assert result.returncode == 0
        assert result.stderr == ""


def test_opencode_plugin_tracks_real_host_model_and_fails_open() -> None:
    plugin_bytes = OPENCODE_PLUGIN.read_bytes()
    plugin = plugin_bytes.decode("utf-8")
    exit_trap = OPENCODE_EXIT_TRAP.read_text(encoding="utf-8")

    assert "entire hooks opencode" in plugin
    assert "currentModel = msg.modelID" in plugin
    assert 'case "session.created"' in plugin
    assert 'case "message.updated"' in plugin
    assert 'case "server.instance.disposed"' in plugin
    assert "plugin failures must not crash OpenCode" in plugin
    assert "refs/entire" not in plugin
    assert hashlib.sha256(plugin_bytes).hexdigest() == (
        "516fc7c811560f61cf860f8ea0f76f67d57f30279d018c9dabb8e37fc1142d88"
    )
    assert 'process.once("beforeExit", endCurrentSession)' in exit_trap
    assert 'process.once("exit", endCurrentSession)' in exit_trap
    assert "entire hooks opencode session-end" in exit_trap
    assert "termination capture can never crash OpenCode" in exit_trap


def test_no_public_entire_refs_in_native_onboarding_files() -> None:
    paths = (
        CODEX_HOOKS,
        CLAUDE_SETTINGS,
        ENTIRE_SETTINGS,
        OPENCODE_PLUGIN,
        OPENCODE_EXIT_TRAP,
    )
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "refs/entire" not in combined
    assert "learn-ukrainian/entire-checkpoints-private" in combined
