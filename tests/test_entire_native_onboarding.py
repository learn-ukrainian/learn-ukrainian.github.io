"""Contracts for non-destructive Entire 0.8.42 native harness onboarding."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import tomllib
from pathlib import Path

from scripts.entire.validate_checkpoint_routing import EXPECTED_PRIVATE_RECALL, validate

ROOT = Path(__file__).resolve().parents[1]
CODEX_HOOKS = ROOT / "agents_extensions" / "codex" / "hooks.json"
CODEX_CONFIG = ROOT / "agents_extensions" / "codex" / "config.toml"
CLAUDE_SETTINGS = ROOT / "agents_extensions" / "shared" / "settings.json"
ENTIRE_SETTINGS = ROOT / ".entire" / "settings.json"
PRIVATE_RECALL = ROOT / ".entire" / "private-recall.json"
OPENCODE_PLUGIN = ROOT / ".opencode" / "plugins" / "entire.ts"
OPENCODE_EXIT_TRAP = ROOT / ".opencode" / "plugins" / "entire-exit.ts"


def _hook_commands(payload: dict, event: str) -> list[dict]:
    return [hook for entry in payload["hooks"][event] for hook in entry.get("hooks", [])]


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


def test_private_native_recall_policy_is_exact_and_non_authoritative() -> None:
    policy = json.loads(PRIVATE_RECALL.read_text(encoding="utf-8"))

    assert policy == EXPECTED_PRIVATE_RECALL
    assert validate(ROOT) is None
    assert policy["automatic_intake"] is True
    assert policy["public_promotion"] is False
    assert policy["authoritative"] is False
    assert "--all-repos" in policy["forbidden_flags"]
    assert policy["operations"]["search"][-1] == ("learn-ukrainian/learn-ukrainian.github.io")
    assert "--full" in policy["operations"]["explain_full"]
    assert "explain_full" not in policy["operator_request_required"]
    assert "--raw-transcript" in policy["forbidden_flags"]
    assert "--transcript" in policy["forbidden_flags"]


def _write_routing_fixture(root: Path, policy: dict) -> None:
    entire_dir = root / ".entire"
    entire_dir.mkdir()
    (entire_dir / "settings.json").write_text(
        json.dumps(
            {
                "enabled": True,
                "strategy_options": {
                    "checkpoint_remote": {
                        "provider": "github",
                        "repo": "learn-ukrainian/entire-checkpoints-private",
                    }
                },
                "telemetry": False,
                "external_agents": True,
            }
        ),
        encoding="utf-8",
    )
    (entire_dir / "phase05-allowlist.json").write_text(
        json.dumps(
            {
                "version": 1,
                "checkpoint_endpoints": [{"github_repo": "learn-ukrainian/entire-checkpoints-private"}],
            }
        ),
        encoding="utf-8",
    )
    (entire_dir / "private-recall.json").write_text(json.dumps(policy), encoding="utf-8")


def test_private_recall_validator_rejects_disabled_automatic_intake(tmp_path: Path) -> None:
    policy = copy.deepcopy(EXPECTED_PRIVATE_RECALL)
    policy["automatic_intake"] = False
    _write_routing_fixture(tmp_path, policy)

    assert validate(tmp_path) == ("private recall policy does not match the canonical private-only contract")


def test_private_recall_validator_rejects_broader_search_scope(tmp_path: Path) -> None:
    policy = copy.deepcopy(EXPECTED_PRIVATE_RECALL)
    policy["operations"]["search"][-1] = "*"
    _write_routing_fixture(tmp_path, policy)

    assert validate(tmp_path) == ("private recall policy does not match the canonical private-only contract")


def test_codex_cli_and_desktop_share_four_composed_entire_hooks() -> None:
    hooks = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))
    config = tomllib.loads(CODEX_CONFIG.read_text(encoding="utf-8"))
    entire_hooks = _entire_hooks(hooks, "codex")

    assert config["features"]["hooks"] is True
    assert len(entire_hooks) == 4
    assert {
        re.search(r"entire hooks codex (\S+)", command["command"]).group(1)
        for command in entire_hooks
    } == {
        "session-start",
        "post-tool-use",
        "user-prompt-submit",
        "stop",
    }
    assert all(command["timeout"] == 30 for command in entire_hooks)
    assert all("if ! command -v entire" in command["command"] for command in entire_hooks)
    # Entire capture is optional: an installed CLI that fails (hook parse or
    # agent errors) must exit 0 so Codex exec is never poisoned by it.
    assert all(command["command"].endswith("|| true'") for command in entire_hooks)

    # Existing project hook semantics must survive onboarding unchanged. The
    # stock 0.8.42 installer rewrites these objects and drops this metadata.
    session_setup = next(
        hook for hook in _hook_commands(hooks, "SessionStart") if "session-setup.sh" in hook["command"]
    )
    assert session_setup == {
        "type": "command",
        "command": 'bash "$(git rev-parse --show-toplevel)/.codex/hooks/session-setup.sh"',
        "timeout": 15,
        "statusMessage": "Checking learn-ukrainian session state",
        "additionalContextLimit": 1200,
    }
    policy = next(hook for hook in _hook_commands(hooks, "PreToolUse") if "codex_hook_entry.sh" in hook["command"])
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
    assert existing["$CLAUDE_PROJECT_DIR/.claude/hooks/guard-primary-checkout-write.py"]["timeout"] == 5
    # thread-lease-heartbeat.sh was removed from PostToolUse (diagnostic-only by
    # its own header; the Stop hook still refreshes once per turn) — PR #6413 rec 2.
    assert "$CLAUDE_PROJECT_DIR/.claude/hooks/thread-lease-heartbeat.sh" not in existing
    assert existing["$CLAUDE_PROJECT_DIR/.claude/hooks/release-thread-lease.sh"]["timeout"] == 5


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


def test_entire_codex_hooks_fail_open_when_installed_cli_errors(tmp_path: Path) -> None:
    """An installed Entire CLI that errors must never poison Codex exec.

    Evidence 2026-09-02: Entire 0.8.42 exits rc=1 with
    ``failed to parse hook event: empty hook input`` on empty stdin, and
    ``unknown agent`` when the agent is missing.  Both are optional-capture
    failures, so every Codex Entire hook must still exit 0.
    """
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_entire = fake_bin / "entire"
    fake_entire.write_text(
        "#!/bin/sh\n"
        "echo 'failed to parse hook event: empty hook input' >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake_entire.chmod(0o755)
    codex = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))

    for hook in _entire_hooks(codex, "codex"):
        for stdin in ("", "{}\n"):
            result = subprocess.run(
                ["/bin/sh", "-c", hook["command"]],
                input=stdin,
                capture_output=True,
                text=True,
                check=False,
                env={"PATH": f"{fake_bin}:/usr/bin:/bin"},
                timeout=5,
            )
            assert result.returncode == 0, (hook["command"], result.returncode)


def test_opencode_plugin_tracks_real_host_model_and_fails_open() -> None:
    plugin_bytes = OPENCODE_PLUGIN.read_bytes()
    plugin = plugin_bytes.decode("utf-8")
    exit_trap = OPENCODE_EXIT_TRAP.read_text(encoding="utf-8")

    assert "entire hooks opencode" in plugin
    assert "exec entire" not in plugin
    assert "|| true" in plugin
    assert "currentModel = msg.modelID" in plugin
    assert 'case "session.created"' in plugin
    assert 'case "message.updated"' in plugin
    assert 'case "server.instance.disposed"' in plugin
    assert "plugin failures must not crash OpenCode" in plugin
    assert "refs/entire" not in plugin
    assert hashlib.sha256(plugin_bytes).hexdigest() == (
        "7e562fdc276798ce4771c95d703dc07ccbbdc22bece2286f7c5a2f0d17e2884f"
    )
    assert 'process.once("beforeExit", endCurrentSession)' in exit_trap
    assert 'process.once("exit", endCurrentSession)' in exit_trap
    assert "exec entire" not in exit_trap
    assert "|| true" in exit_trap
    assert "entire hooks opencode session-end" in exit_trap
    assert "termination capture can never crash OpenCode" in exit_trap


def test_opencode_plugin_wrappers_fail_open_when_cli_errors(tmp_path: Path) -> None:
    """The shell wrappers used by OpenCode swallow an installed CLI failure."""
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_entire = fake_bin / "entire"
    args_log = tmp_path / "entire-args.log"
    fake_entire.write_text(
        "#!/bin/sh\n"
        "printf '%s\\n' \"$*\" >> \"$ENTIRE_ARGS\"\n"
        "echo 'failed to parse hook event: empty hook input' >&2\n"
        "exit 1\n",
        encoding="utf-8",
    )
    fake_entire.chmod(0o755)
    env = {"PATH": f"{fake_bin}:/usr/bin:/bin", "ENTIRE_ARGS": str(args_log)}

    plugin = OPENCODE_PLUGIN.read_text(encoding="utf-8")
    command_match = re.search(
        r'return \["sh", "-c", `([^`]*command -v entire[^`]*)`\]',
        plugin,
    )
    assert command_match is not None
    command_template = command_match.group(1)
    for hook_name in ("session-start", "turn-start", "turn-end", "session-end"):
        result = subprocess.run(
            ["/bin/sh", "-c", command_template.replace("${hookName}", hook_name)],
            input="{}\n",
            capture_output=True,
            text=True,
            check=False,
            env=env,
            timeout=5,
        )
        assert result.returncode == 0, (hook_name, result.stderr)

    assert args_log.read_text(encoding="utf-8").splitlines() == [
        "hooks opencode session-start",
        "hooks opencode turn-start",
        "hooks opencode turn-end",
        "hooks opencode session-end",
    ]

    exit_trap = OPENCODE_EXIT_TRAP.read_text(encoding="utf-8")
    exit_match = re.search(r'"(if ! command -v entire[^"\n]+session-end \|\| true)"', exit_trap)
    assert exit_match is not None
    result = subprocess.run(
        ["/bin/sh", "-c", exit_match.group(1)],
        input="{}\n",
        capture_output=True,
        text=True,
        check=False,
        env=env,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert args_log.read_text(encoding="utf-8").splitlines()[-1] == "hooks opencode session-end"


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
