"""Main-session profile behavior for the native Claude Code wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-claude.sh"


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _run_native_wrapper(
    tmp_path: Path,
    arguments: list[str],
    env_overrides: dict[str, str] | None = None,
) -> tuple[dict[str, str], subprocess.CompletedProcess[str]]:
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
    printf 'base=%s\n' "${ANTHROPIC_BASE_URL-unset}"
    printf 'auth=%s\n' "${ANTHROPIC_AUTH_TOKEN-unset}"
    if [[ -n "${ANTHROPIC_API_KEY:-}" ]]; then printf 'api_key=SET\n'; else printf 'api_key=UNSET\n'; fi
    printf 'subagent=%s\n' "${CLAUDE_CODE_SUBAGENT_MODEL-unset}"
    printf 'tool_search=%s\n' "${ENABLE_TOOL_SEARCH-unset}"
    printf 'claudex_run_id=%s\n' "${LEARN_UKRAINIAN_CLAUDEX_RUN_ID-unset}"
    printf 'claudex_generation=%s\n' "${LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION-unset}"
    printf 'managed_launch=%s\n' "${LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH-unset}"
    printf 'max_context=%s\n' "${CLAUDE_CODE_MAX_CONTEXT_TOKENS-unset}"
    printf 'auto_compact=%s\n' "${CLAUDE_CODE_AUTO_COMPACT_WINDOW-unset}"
    printf 'profile=%s\n' "$LEARN_UKRAINIAN_PROFILE_ID"
    printf 'requested_profile=%s\n' "${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-}"
    printf 'transport=%s\n' "$LEARN_UKRAINIAN_TRANSPORT"
    printf 'main_model=%s\n' "$LEARN_UKRAINIAN_MAIN_MODEL_ID"
    printf 'main_window=%s\n' "$LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS"
    printf 'cold_start=%s\n' "$LEARN_UKRAINIAN_COLD_START_PROFILE"
    printf 'cold_budget=%s\n' "$LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS"
    printf 'reason=%s\n' "$LEARN_UKRAINIAN_RESOLUTION_REASON"
    printf 'trusted=%s\n' "$LEARN_UKRAINIAN_TRUSTED"
    printf 'arg=%s\n' "$@"
} > "$CLAUDE_PROFILE_TEST_CAPTURE"
""",
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    _write_executable(fake_bin / "npm", "#!/usr/bin/env bash\nexit 0\n")

    env = os.environ.copy()
    for name in tuple(env):
        if name.startswith("LEARN_UKRAINIAN_") or name in {
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS",
            "CLAUDE_CODE_SUBAGENT_MODEL",
            "SESSION_EPIC",
            "SESSION_HANDOFF_AGENT",
        }:
            env.pop(name, None)
    env.update(
        {
            "HOME": os.fspath(tmp_path / "home"),
            "PATH": f"{fake_bin}:{env['PATH']}",
            "CLAUDE_PROFILE_TEST_CAPTURE": os.fspath(capture),
        }
    )
    env.update(env_overrides or {})
    result = subprocess.run(
        [os.fspath(_LAUNCHER), *arguments, "--resume", "session-id"],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    values = dict(
        line.split("=", 1)
        for line in capture.read_text(encoding="utf-8").splitlines()
        if not line.startswith("arg=")
    )
    return values, result


def test_certified_native_route_keeps_native_capacity_and_clears_proxy_flags(
    tmp_path: Path,
) -> None:
    values, result = _run_native_wrapper(
        tmp_path,
        ["--model", "claude-opus-4-8"],
        {
            "ANTHROPIC_BASE_URL": "https://stale-proxy.invalid",
            "ANTHROPIC_AUTH_TOKEN": "not-a-real-token",
            "ANTHROPIC_API_KEY": "test-native-key",
            "CLAUDE_CODE_SUBAGENT_MODEL": "gpt-5.6-terra",
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "258400",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "272000",
        },
    )

    assert values == {
        "base": "unset",
        "auth": "unset",
        "api_key": "SET",
        "subagent": "unset",
        "tool_search": "unset",
        "claudex_run_id": "unset",
        "claudex_generation": "unset",
        "managed_launch": "unset",
        "max_context": "unset",
        "auto_compact": "unset",
        "profile": "native_claude",
        "requested_profile": "native_claude",
        "transport": "native",
        "main_model": "claude-native-family",
        "main_window": "1000000",
        "cold_start": "full",
        "cold_budget": "100000",
        "reason": "explicit-profile",
        "trusted": "1",
    }
    assert "Context profile: id=native_claude" in result.stdout


def test_nested_native_launch_drops_ambient_claudex_route(
    tmp_path: Path,
) -> None:
    values, _ = _run_native_wrapper(
        tmp_path,
        [],
        {
            "ANTHROPIC_BASE_URL": "https://stale-proxy.invalid",
            "ANTHROPIC_AUTH_TOKEN": "not-a-real-token",
            "CLAUDE_CODE_SUBAGENT_MODEL": "gpt-5.6-terra",
            "ENABLE_TOOL_SEARCH": "true",
            "LEARN_UKRAINIAN_CLAUDEX_RUN_ID": "stale-run",
            "LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION": "3",
            "LEARN_UKRAINIAN_REQUESTED_PROFILE_ID": "sol_lead",
            "LEARN_UKRAINIAN_TRANSPORT": "claudex",
        },
    )

    assert values["profile"] == "native_claude"
    assert values["requested_profile"] == "native_claude"
    assert values["transport"] == "native"
    assert values["base"] == "unset"
    assert values["auth"] == "unset"
    assert values["subagent"] == "unset"
    assert values["tool_search"] == "unset"
    assert values["claudex_run_id"] == "unset"
    assert values["claudex_generation"] == "unset"
    assert values["managed_launch"] == "unset"


def test_custom_non_claude_model_without_route_metadata_fails_closed(
    tmp_path: Path,
) -> None:
    values, result = _run_native_wrapper(
        tmp_path,
        ["--model=gpt-5.6-sol"],
        {
            "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "1000000",
            "CLAUDE_CODE_MAX_CONTEXT_TOKENS": "1000000",
        },
    )

    assert values["profile"] == "fallback"
    assert values["transport"] == "unknown"
    assert values["main_model"] == "unknown"
    assert values["main_window"] == "0"
    assert values["cold_start"] == "compact"
    assert values["auto_compact"] == "unset"
    assert values["max_context"] == "unset"
    assert values["reason"] == "model-mismatch"
    assert values["trusted"] == "0"
    assert "using compact fallback" in result.stderr
    assert "without a fabricated context window" in result.stderr
