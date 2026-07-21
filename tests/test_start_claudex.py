"""Behavior checks for the CLIProxyAPI-backed Claude Code launcher."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-claudex.sh"
_STATUS_SETTINGS = (
    _REPO_ROOT / "agents_extensions/shared/statusline/claudex-settings.json"
)


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _run_with_fakes(
    tmp_path: Path,
    arguments: list[str],
    env_overrides: dict[str, str] | None = None,
) -> str:
    home_bin = tmp_path / "home" / ".local" / "bin"
    home_bin.mkdir(parents=True)
    capture = tmp_path / "capture.txt"

    _write_executable(
        home_bin / "claude",
        """#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then
    echo "test-claude"
    exit 0
fi
{
    printf 'base=%s\n' "$ANTHROPIC_BASE_URL"
    printf 'auth=%s\n' "$ANTHROPIC_AUTH_TOKEN"
    printf 'api_key=%s\n' "${ANTHROPIC_API_KEY-unset}"
    printf 'subagent=%s\n' "$CLAUDE_CODE_SUBAGENT_MODEL"
    printf 'effort=%s\n' "$CLAUDE_CODE_ALWAYS_ENABLE_EFFORT"
    printf 'concurrency=%s\n' "$CLAUDE_CODE_MAX_TOOL_USE_CONCURRENCY"
    printf 'tool_search=%s\n' "$ENABLE_TOOL_SEARCH"
    printf 'managed_launch=%s\n' "${LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH-unset}"
    printf 'epic=%s\n' "${SESSION_EPIC:-}"
    printf 'profile=%s\n' "$LEARN_UKRAINIAN_PROFILE_ID"
    printf 'requested_profile=%s\n' "$LEARN_UKRAINIAN_REQUESTED_PROFILE_ID"
    printf 'main_model=%s\n' "$LEARN_UKRAINIAN_MAIN_MODEL_ID"
    printf 'main_window=%s\n' "$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"
    printf 'cold_start=%s\n' "$LEARN_UKRAINIAN_COLD_START_PROFILE"
    printf 'cold_budget=%s\n' "$LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS"
    printf 'profile_auto_compact=%s\n' "$LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS"
    printf 'claude_max_context=%s\n' "$CLAUDE_CODE_MAX_CONTEXT_TOKENS"
    printf 'claude_auto_compact=%s\n' "$CLAUDE_CODE_AUTO_COMPACT_WINDOW"
    printf 'effort_level=%s\n' "$CLAUDE_CODE_EFFORT_LEVEL"
    printf 'profile_reason=%s\n' "$LEARN_UKRAINIAN_RESOLUTION_REASON"
    printf 'profile_trusted=%s\n' "$LEARN_UKRAINIAN_TRUSTED"
    printf 'arg=%s\n' "$@"
} > "$CLAUDEX_TEST_CAPTURE"
""",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "curl", "#!/usr/bin/env bash\nexit 0\n")
    _write_executable(fake_bin / "npm", "#!/usr/bin/env bash\nexit 0\n")

    env = os.environ.copy()
    for variable in (
        "ANTHROPIC_API_KEY",
        "CLAUDEX_BASE_URL",
        "CLAUDEX_AUTH_TOKEN",
        "CLAUDEX_SUBAGENT",
        "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
        "CLAUDE_CODE_EFFORT_LEVEL",
    ):
        env.pop(variable, None)
    env.update(
        {
            "HOME": str(tmp_path / "home"),
            "PATH": f"{fake_bin}:{env['PATH']}",
            "CLAUDEX_TEST_CAPTURE": str(capture),
            "CLAUDEX_SUPERVISOR_TEST_STATE_ROOT": str(tmp_path),
        }
    )
    env.update(env_overrides or {})
    result = subprocess.run(
        [
            str(_LAUNCHER),
            *arguments,
            "--epic",
            "harness",
            "--resume",
            "session-id",
        ],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    return capture.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ([], "gpt-5.6-terra"),
        (["--subagent", "sol"], "gpt-5.6-sol"),
        (["--subagent=terra"], "gpt-5.6-terra"),
        (["--subagent", "luna"], "gpt-5.6-luna"),
    ],
)
def test_routes_lead_and_subagent_models(tmp_path: Path, arguments: list[str], expected: str) -> None:
    output = _run_with_fakes(tmp_path, arguments)
    assert "base=http://127.0.0.1:8317" in output
    assert "auth=sk-dummy" in output
    assert "api_key=unset" in output
    assert f"subagent={expected}" in output
    assert "effort=1" in output
    assert "concurrency=3" in output
    assert "tool_search=true" in output
    assert "managed_launch=unset" in output
    assert "epic=harness" in output
    assert "profile=sol_lead" in output
    assert "requested_profile=sol_lead" in output
    assert "main_model=gpt-5.6-sol" in output
    assert "main_window=272000" in output
    assert "cold_start=compact" in output
    assert "cold_budget=27200" in output
    assert "profile_auto_compact=258400" in output
    assert "claude_max_context=272000" in output
    assert "claude_auto_compact=258400" in output
    assert "effort_level=high" in output
    assert "profile_reason=explicit-profile" in output
    assert "profile_trusted=1" in output
    assert "arg=--model" in output
    assert "arg=gpt-5.6-sol" in output
    assert "arg=--settings" in output
    assert f"arg={_STATUS_SETTINGS}" in output
    assert "arg=session-id" in output
    assert "arg=harness" not in output


def test_claudex_status_settings_cover_main_and_subagent_visibility() -> None:
    settings = json.loads(_STATUS_SETTINGS.read_text(encoding="utf-8"))

    assert settings["statusLine"]["refreshInterval"] == 2
    assert "statusline/statusline.sh" in settings["statusLine"]["command"]
    assert "subagent-statusline.sh" in settings["subagentStatusLine"]["command"]

    main = subprocess.run(
        shlex.split(settings["statusLine"]["command"]),
        input=json.dumps(
            {
                "model": {"display_name": "GPT-5.6 Sol"},
                "workspace": {
                    "current_dir": os.fspath(_REPO_ROOT),
                    "project_dir": os.fspath(_REPO_ROOT),
                },
                "context_window": {
                    "total_input_tokens": 68_000,
                    "context_window_size": 272_000,
                    "used_percentage": 25,
                },
                "effort": {"level": "high"},
            }
        ),
        text=True,
        capture_output=True,
        check=True,
        cwd=_REPO_ROOT,
    )
    assert "[GPT-5.6 Sol]" in main.stdout
    assert "[ctx: 68K/272K (25%)]" in main.stdout
    assert "[effort: high]" in main.stdout

    subagent = subprocess.run(
        shlex.split(settings["subagentStatusLine"]["command"]),
        input=json.dumps(
            {
                "workspace": {
                    "current_dir": os.fspath(_REPO_ROOT),
                    "project_dir": os.fspath(_REPO_ROOT),
                },
                "columns": 100,
                "tasks": [
                    {
                        "id": "agent-1",
                        "name": "repo-map",
                        "status": "running",
                        "description": "Inspect launchers",
                        "tokenCount": 4_200,
                    }
                ],
            }
        ),
        text=True,
        capture_output=True,
        check=True,
        cwd=_REPO_ROOT,
    )
    assert json.loads(subagent.stdout) == {
        "id": "agent-1",
        "content": "[running] repo-map: Inspect launchers · 4K tok",
    }


def test_forwards_proxy_overrides_without_anthropic_api_key(tmp_path: Path) -> None:
    output = _run_with_fakes(
        tmp_path,
        [],
        {
            "ANTHROPIC_API_KEY": "must-be-unset",
            "CLAUDEX_BASE_URL": "https://proxy.example.com:8443/",
            "CLAUDEX_AUTH_TOKEN": "custom-token",
        },
    )

    assert "base=https://proxy.example.com:8443" in output
    assert "auth=custom-token" in output
    assert "api_key=unset" in output


def test_rejects_unknown_subagent() -> None:
    result = subprocess.run(
        [str(_LAUNCHER), "--subagent", "unknown"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "unsupported subagent" in result.stderr


def test_rejects_missing_subagent_value() -> None:
    result = subprocess.run(
        [str(_LAUNCHER), "--subagent"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "requires sol, terra, or luna" in result.stderr


@pytest.mark.parametrize("argument", ["--model", "--model=gpt-5.6-luna"])
def test_rejects_lead_model_override(argument: str) -> None:
    result = subprocess.run(
        [str(_LAUNCHER), argument],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 2
    assert "keeps the lead model on gpt-5.6-sol" in result.stderr


def test_reports_proxy_check_failure(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "curl", "#!/usr/bin/env bash\nexit 22\n")
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}:{env['PATH']}"
    env["CLAUDEX_BASE_URL"] = "{scheme}{separator}{authority}?{query}".format(
        scheme="https",
        separator="://",
        authority="".join(("user", ":", "private", "@", "proxy.invalid")),
        query="".join(("token", "=", "private")),
    )

    result = subprocess.run(
        [str(_LAUNCHER)],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "CLIProxyAPI check failed" in result.stderr
    assert "proxy.invalid" not in result.stderr
    assert "private" not in result.stderr


def test_reports_missing_curl(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for command in ("dirname", "mktemp", "rm"):
        executable = shutil.which(command)
        assert executable is not None
        (fake_bin / command).symlink_to(executable)
    env = os.environ.copy()
    env["PATH"] = str(fake_bin)

    result = subprocess.run(
        ["/bin/bash", str(_LAUNCHER)],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "curl is required" in result.stderr


def test_rejects_settings_max_context_override(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        '{"env":{"CLAUDE_CODE_MAX_CONTEXT_TOKENS":"1000000"}}',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("CLAUDE_CONFIG_DIR", None)
    env["CLAUDE_SETTINGS_PATH"] = os.fspath(settings)

    result = subprocess.run(
        [str(_LAUNCHER)],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 1
    assert "CLAUDE_CODE_MAX_CONTEXT_TOKENS" in result.stderr
    assert "settings.json env OVER process environment" in result.stderr


@pytest.mark.parametrize("argument", ["-h", "--help"])
def test_prints_launcher_help(argument: str) -> None:
    result = subprocess.run(
        [str(_LAUNCHER), argument],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0
    assert "Usage: ./start-claudex.sh" in result.stdout
