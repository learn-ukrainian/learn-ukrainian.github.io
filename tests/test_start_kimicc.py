"""Behavior checks for the interactive Claude Code + Kimi (kimicc) launcher."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-kimicc.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _run_with_fakes(
    tmp_path: Path,
    arguments: list[str],
    *,
    env_overrides: dict[str, str] | None = None,
    settings_env: dict[str, str] | None = None,
) -> tuple[str, subprocess.CompletedProcess[str]]:
    home = tmp_path / "home"
    home_bin = home / ".local" / "bin"
    home_bin.mkdir(parents=True)
    capture = tmp_path / "capture.txt"

    if settings_env is not None:
        claude_dir = home / ".claude"
        claude_dir.mkdir(parents=True)
        (claude_dir / "settings.json").write_text(
            json.dumps({"env": settings_env, "model": "opus[1m]"}),
            encoding="utf-8",
        )

    _write_executable(
        home_bin / "claude",
        """#!/usr/bin/env bash
if [[ "${1:-}" == "--version" ]]; then
    echo "test-claude"
    exit 0
fi
{
    printf 'base=%s\\n' "${ANTHROPIC_BASE_URL-unset}"
    printf 'auth=%s\\n' "${ANTHROPIC_AUTH_TOKEN-unset}"
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then printf 'api_key=SET\\n'; else printf 'api_key=UNSET\\n'; fi
    printf 'model=%s\\n' "${ANTHROPIC_MODEL-unset}"
    printf 'opus=%s\\n' "${ANTHROPIC_DEFAULT_OPUS_MODEL-unset}"
    printf 'sonnet=%s\\n' "${ANTHROPIC_DEFAULT_SONNET_MODEL-unset}"
    printf 'haiku=%s\\n' "${ANTHROPIC_DEFAULT_HAIKU_MODEL-unset}"
    printf 'fable=%s\\n' "${ANTHROPIC_DEFAULT_FABLE_MODEL-unset}"
    printf 'subagent=%s\\n' "${CLAUDE_CODE_SUBAGENT_MODEL-unset}"
    printf 'tool_search=%s\\n' "${ENABLE_TOOL_SEARCH-unset}"
    printf 'effort=%s\\n' "${CLAUDE_CODE_EFFORT_LEVEL-unset}"
    printf 'auto_compact=%s\\n' "${CLAUDE_CODE_AUTO_COMPACT_WINDOW-unset}"
    printf 'profile=%s\\n' "$LEARN_UKRAINIAN_PROFILE_ID"
    printf 'transport=%s\\n' "$LEARN_UKRAINIAN_TRANSPORT"
    printf 'main_window=%s\\n' "$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"
    printf 'config_dir=%s\\n' "${CLAUDE_CONFIG_DIR-unset}"
    printf 'arg=%s\\n' "$@"
} > "$KIMICC_TEST_CAPTURE"
""",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "npm", "#!/usr/bin/env bash\nexit 0\n")

    env = os.environ.copy()
    for name in tuple(env):
        if name.startswith("LEARN_UKRAINIAN_") or name in {
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
            "CLAUDE_CODE_SUBAGENT_MODEL",
            "CLAUDE_CODE_EFFORT_LEVEL",
            "ANTHROPIC_BASE_URL",
            "ANTHROPIC_AUTH_TOKEN",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_MODEL",
            "MOONSHOT_API_KEY",
            "KIMI_API_KEY",
            "KIMICC_AUTH_TOKEN",
            "KIMICC_BASE_URL",
            "KIMICC_MODEL",
            "KIMICC_ENDPOINT",
            "CLAUDE_CONFIG_DIR",
            "SESSION_EPIC",
            "SESSION_HANDOFF_AGENT",
        }:
            env.pop(name, None)
    env.update(
        {
            "HOME": str(home),
            "PATH": f"{fake_bin}:{env['PATH']}",
            "KIMICC_TEST_CAPTURE": str(capture),
            "MOONSHOT_API_KEY": "sk-test-moonshot",
        }
    )
    env.update(env_overrides or {})

    result = subprocess.run(
        [str(_LAUNCHER), *arguments],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    output = capture.read_text(encoding="utf-8") if capture.exists() else ""
    return output, result


@pytest.mark.parametrize(
    ("arguments", "model", "profile", "window", "compact", "effort"),
    [
        ([], "kimi-k3[1m]", "kimicc_k3", "1048576", "996147", "max"),
        (["--model", "k3"], "kimi-k3[1m]", "kimicc_k3", "1048576", "996147", "max"),
        (["--model", "k2.7"], "kimi-k2.7-code", "kimicc_k27", "262144", "249036", "unset"),
        (
            ["--model", "k2.7-highspeed"],
            "kimi-k2.7-code-highspeed",
            "kimicc_k27_highspeed",
            "262144",
            "249036",
            "unset",
        ),
    ],
)
def test_routes_models_and_compaction(
    tmp_path: Path,
    arguments: list[str],
    model: str,
    profile: str,
    window: str,
    compact: str,
    effort: str,
) -> None:
    output, result = _run_with_fakes(tmp_path, arguments)
    assert result.returncode == 0, result.stderr
    assert "base=https://api.moonshot.ai/anthropic" in output
    assert "auth=sk-test-moonshot" in output
    assert "api_key=UNSET" in output
    assert f"model={model}" in output
    assert f"opus={model}" in output
    assert f"sonnet={model}" in output
    assert f"haiku={model}" in output
    assert f"fable={model}" in output
    assert f"subagent={model}" in output
    assert "tool_search=false" in output
    assert f"effort={effort}" in output
    assert f"auto_compact={compact}" in output
    assert f"profile={profile}" in output
    assert "transport=kimicc" in output
    assert f"main_window={window}" in output
    assert "arg=--model" in output
    assert f"arg={model}" in output


def test_coding_endpoint_uses_subscription_base_and_model_ids(tmp_path: Path) -> None:
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "coding", "--model", "k2.7"],
        env_overrides={"KIMICC_AUTH_TOKEN": "sk-coding-token"},
    )
    assert result.returncode == 0, result.stderr
    assert "base=https://api.kimi.com/coding" in output
    assert "auth=sk-coding-token" in output
    assert "model=kimi-for-coding" in output
    assert "profile=kimicc_k27" in output


def test_refuses_settings_json_route_env_pins(tmp_path: Path) -> None:
    output, result = _run_with_fakes(
        tmp_path,
        [],
        settings_env={"ANTHROPIC_BASE_URL": "https://evil.example/anthropic"},
    )
    assert result.returncode == 1
    assert "refuses to launch" in result.stderr
    assert "ANTHROPIC_BASE_URL" in result.stderr
    assert output == ""
    # Original settings file is not mutated.
    settings = (tmp_path / "home" / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert "evil.example" in settings


def test_isolate_config_bypasses_live_settings_pins(tmp_path: Path) -> None:
    output, result = _run_with_fakes(
        tmp_path,
        ["--isolate-config"],
        settings_env={"ANTHROPIC_BASE_URL": "https://evil.example/anthropic"},
    )
    assert result.returncode == 0, result.stderr
    assert "base=https://api.moonshot.ai/anthropic" in output
    assert str(tmp_path / "home" / ".claude-kimicc") in output or "config_dir=" in output
    assert "config_dir=" in output
    assert "evil.example" not in output


def test_missing_api_key_fails_cleanly(tmp_path: Path) -> None:
    _, result = _run_with_fakes(
        tmp_path,
        [],
        env_overrides={
            # Explicitly clear every credential source the launcher accepts.
            "MOONSHOT_API_KEY": "",
            "KIMI_API_KEY": "",
            "KIMICC_AUTH_TOKEN": "",
            "ANTHROPIC_AUTH_TOKEN": "",
        },
    )
    # Empty strings are still "set"; re-run with keys removed entirely.
    env = os.environ.copy()
    for name in (
        "MOONSHOT_API_KEY",
        "KIMI_API_KEY",
        "KIMICC_AUTH_TOKEN",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_API_KEY",
    ):
        env.pop(name, None)
    home = tmp_path / "home-no-key"
    (home / ".local" / "bin").mkdir(parents=True)
    _write_executable(home / ".local" / "bin" / "claude", "#!/usr/bin/env bash\nexit 0\n")
    fake_bin = tmp_path / "bin-no-key"
    fake_bin.mkdir()
    _write_executable(fake_bin / "npm", "#!/usr/bin/env bash\nexit 0\n")
    env.update({"HOME": str(home), "PATH": f"{fake_bin}:{env['PATH']}"})
    result = subprocess.run(
        [str(_LAUNCHER)],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 1
    assert "no Kimi API credential" in result.stderr


def test_rejects_forwarded_model_flag(tmp_path: Path) -> None:
    _, result = _run_with_fakes(tmp_path, ["--model", "k3", "--model", "opus"])
    # Second --model is parsed as the lead alias and fails as unsupported.
    assert result.returncode == 2
    assert "unsupported model" in result.stderr


def test_help_mentions_native_kimi_headless_separation(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(_LAUNCHER), "--help"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "ask-kimi" in result.stdout
    assert "settings.json" in result.stdout
