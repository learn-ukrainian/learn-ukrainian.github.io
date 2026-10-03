"""Headless Claude policy reaches the CLI after runtime environment sanitization."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import ClaudeAdapter
from scripts.agent_runtime.env_sanitize import build_agent_env


@pytest.mark.parametrize(
    "mode,config",
    [
        ("read-only", {}),
        ("read-only", {"reviewer_tools": True}),
        ("read-only", {"allowed_tools": "Bash,Read"}),
        ("read-only", {"allowed_tools": ""}),
        ("read-only", {"discussion_readonly": True}),
        ("read-only", {"review_attempt_boundary": True}),
        ("workspace-write", {}),
        ("workspace-write", {"allowed_tools": "Bash,Read,Edit"}),
        ("danger", {}),
    ],
)
@pytest.mark.parametrize("session", ["fresh", "new", "resume"])
def test_fake_claude_cannot_leave_background_work_pending(tmp_path: Path, monkeypatch, mode, config, session):
    fake = tmp_path / "claude.py"
    fake.write_text(
        "import json, os, sys, time\n"
        "if '--version' in sys.argv:\n"
        "    print('2.1.288 (Claude Code)')\n"
        "    sys.exit(0)\n"
        "settings = json.loads(sys.argv[sys.argv.index('--settings') + 1])\n"
        "os.environ.update(settings.get('env', {}))\n"
        "if os.environ.get('CLAUDE_CODE_DISABLE_BACKGROUND_TASKS') == '1':\n"
        "    time.sleep(0.01)\n"
        "    report = 'Slow command complete. Full report available.'\n"
        "else:\n"
        "    report = 'Background task pending; report will follow.'\n"
        "print(json.dumps({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': report}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CODE_DISABLE_BACKGROUND_TASKS", "0")
    config = {**config, "cmd_prefix": [sys.executable, str(fake)]}
    if session == "new":
        config["is_new_session"] = True
    adapter = ClaudeAdapter()
    plan = adapter.build_invocation(
        prompt="Run a slow command and give the complete report.",
        mode=mode,
        cwd=tmp_path,
        model=None,
        task_id=None,
        session_id=None if session == "fresh" else "11111111-1111-4111-8111-111111111111",
        tool_config=config,
    )
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    assert settings["env"]["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"
    # Long foreground commands must not inherit the CLI's two-minute default.
    assert settings["env"]["BASH_DEFAULT_TIMEOUT_MS"] == "86400000"
    assert settings["env"]["BASH_MAX_TIMEOUT_MS"] == "86400000"
    assert settings["permissions"]["deny"] == ["Monitor"]
    assert "Bash" not in settings["permissions"]["deny"]
    if mode == "workspace-write" or config.get("reviewer_tools"):
        assert "Bash" in plan.cmd[plan.cmd.index("--allowedTools") + 1].split(",")
    if session != "fresh":
        assert ("--session-id" if session == "new" else "--resume") in plan.cmd
    env = build_agent_env(provider="claude", overrides=plan.env_overrides)
    completed = subprocess.run(plan.cmd, cwd=plan.cwd, env=env, capture_output=True, text=True, timeout=10)
    parsed = adapter.parse_response(
        stdout=completed.stdout, stderr=completed.stderr, returncode=completed.returncode, output_file=None, plan=plan
    )
    assert parsed.ok, completed.stderr
    assert parsed.response == "Slow command complete. Full report available."


def test_npx_fallback_and_stdin_prompt_keep_foreground_policy(tmp_path: Path, monkeypatch):
    from scripts.agent_runtime.adapters import claude

    monkeypatch.setattr(claude, "_default_claude_bin", lambda: None)
    monkeypatch.setattr(claude.shutil, "which", lambda name: "/fake/npx" if name == "npx" else None)
    monkeypatch.setattr(claude, "_ensure_supported_claude_cli_version", lambda prefix: (2, 1, 288))
    prompt = "x" * 100_000
    plan = ClaudeAdapter().build_invocation(
        prompt=prompt, mode="read-only", cwd=tmp_path, model=None, task_id=None, session_id=None, tool_config=None
    )
    assert plan.cmd[:2] == ["npx", "@anthropic-ai/claude-code@latest"]
    assert plan.stdin_payload == prompt
    settings = json.loads(plan.cmd[plan.cmd.index("--settings") + 1])
    assert settings["env"]["CLAUDE_CODE_DISABLE_BACKGROUND_TASKS"] == "1"
    assert settings["permissions"]["deny"] == ["Monitor"]
