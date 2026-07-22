"""Behavior checks for the interactive Claude Code + Kimi (kimicc) launcher."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LAUNCHER = _REPO_ROOT / "start-kimicc.sh"


def _resolve_venv_python() -> Path | None:
    """Project venv; falls back to the main worktree when run from a linked worktree."""
    candidates = [_REPO_ROOT / ".venv" / "bin" / "python"]
    try:
        common = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if common.returncode == 0 and common.stdout.strip():
            candidates.append(Path(common.stdout.strip()).parent / ".venv" / "bin" / "python")
    except (OSError, subprocess.SubprocessError):
        pass
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


_VENV_PYTHON = _resolve_venv_python()


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)


def _require_launcher_sources() -> None:
    """Seed from checkout once; do not depend on root scripts surviving full CI suite."""
    missing = [path for path in (
        _LAUNCHER,
        _REPO_ROOT / "scripts" / "lib" / "claude_route_guard.sh",
        _REPO_ROOT / "scripts" / "lib" / "profile_resolver.sh",
        _REPO_ROOT / "scripts" / "lib" / "context_profiles.py",
        _REPO_ROOT / "scripts" / "lib" / "kimi_coding_oauth.py",
    ) if not path.is_file()]
    if missing:
        names = ", ".join(str(path.relative_to(_REPO_ROOT)) for path in missing)
        raise FileNotFoundError(f"kimicc launcher sources missing: {names}")


def _seed_fake_project(tmp_path: Path) -> Path:
    """Copy launcher + sourced helpers into an isolated project root."""
    _require_launcher_sources()
    project = tmp_path / "project"
    lib = project / "scripts" / "lib"
    lib.mkdir(parents=True)
    cfg = project / "scripts" / "config"
    cfg.mkdir(parents=True)
    venv_bin = project / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    _write_executable(project / "start-kimicc.sh", _LAUNCHER.read_text(encoding="utf-8"))
    _write_executable(
        project / "start-claude.sh",
        "#!/usr/bin/env bash\n# Test stub: kimicc already exported env; exec fake claude from PATH.\nexec claude \"$@\"\n",
    )
    for name in ("claude_route_guard.sh", "profile_resolver.sh", "context_profiles.py", "kimi_coding_oauth.py"):
        src = _REPO_ROOT / "scripts" / "lib" / name
        dest = lib / name
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        if name.endswith(".py"):
            dest.chmod(0o755)
    profiles = _REPO_ROOT / "scripts" / "config" / "context_profiles.yaml"
    if profiles.is_file():
        (cfg / "context_profiles.yaml").write_text(profiles.read_text(encoding="utf-8"), encoding="utf-8")
    # Point profile resolver at a real Python that has project deps if present.
    py_body = (
        f'#!/usr/bin/env bash\nexec "{_VENV_PYTHON}" "$@"\n'
        if _VENV_PYTHON is not None
        else "#!/usr/bin/env bash\nexec /usr/bin/env python3 \"$@\"\n"
    )
    _write_executable(venv_bin / "python", py_body)
    return project


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
    printf 'helper_ttl=%s\\n' "${CLAUDE_CODE_API_KEY_HELPER_TTL_MS-unset}"
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
            "KIMICC_AGENT",
            "KIMICC_ISOLATE_CONFIG",
            "KIMICC_DRY_RUN",
            "KIMICC_API_KEY_HELPER_TTL_MS",
            "CLAUDE_CODE_API_KEY_HELPER_TTL_MS",
            "KIMI_CODE_CREDENTIALS_PATH",
            "KIMI_CODE_OAUTH_HOST",
            "KIMI_CODE_OAUTH_MARGIN",
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

    project = _seed_fake_project(tmp_path)
    result = subprocess.run(
        [str(project / "start-kimicc.sh"), *arguments],
        cwd=project,
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
    # Explicitly pin the platform endpoint and live config: the launcher
    # defaults are now coding + isolated config.
    output, result = _run_with_fakes(
        tmp_path, ["--endpoint", "platform", "--no-isolate-config", *arguments]
    )
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
        ["--endpoint", "platform", "--no-isolate-config"],
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
    assert "base=https://api.kimi.com/coding" in output
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


def _write_oauth_credentials(tmp_path: Path, *, expires_in: int = 900) -> Path:
    cred = tmp_path / "oauth-creds" / "kimi-code.json"
    cred.parent.mkdir(parents=True)
    cred.write_text(
        json.dumps(
            {
                "access_token": "oauth-acc",
                "refresh_token": "oauth-ref",
                "expires_at": time.time() + expires_in,
                "expires_in": expires_in,
                "token_type": "Bearer",
                "scope": "kimi-code",
            }
        ),
        encoding="utf-8",
    )
    cred.chmod(0o600)
    return cred


_OAUTH_ENV_CLEAR = {
    "MOONSHOT_API_KEY": "",
    "KIMI_API_KEY": "",
    "KIMICC_AUTH_TOKEN": "",
    "ANTHROPIC_AUTH_TOKEN": "",
}


def test_coding_endpoint_falls_back_to_kimi_login_oauth(tmp_path: Path) -> None:
    cred = _write_oauth_credentials(tmp_path)
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "coding", "--no-isolate-config"],
        env_overrides={
            **_OAUTH_ENV_CLEAR,
            "KIMI_CODE_CREDENTIALS_PATH": str(cred),
            # Fresh stored token (900s > 120s margin): no network needed.
            "KIMI_CODE_OAUTH_HOST": "http://127.0.0.1:9",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "base=https://api.kimi.com/coding" in output
    assert "auth=oauth-acc" in output
    assert "model=k3" in output
    assert "oauth(kimi login)" in result.stdout
    assert "short-lived" in result.stdout


def test_coding_oauth_isolate_config_installs_api_key_helper(tmp_path: Path) -> None:
    cred = _write_oauth_credentials(tmp_path)
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "coding", "--isolate-config"],
        env_overrides={
            **_OAUTH_ENV_CLEAR,
            "KIMI_CODE_CREDENTIALS_PATH": str(cred),
            "KIMI_CODE_OAUTH_HOST": "http://127.0.0.1:9",
        },
    )
    assert result.returncode == 0, result.stderr
    # apiKeyHelper mode: no static token is exported into the process env.
    assert "auth=unset" in output
    assert "helper_ttl=300000" in output
    assert "apiKeyHelper" in result.stdout
    settings_path = tmp_path / "home" / ".claude-kimicc" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    helper = settings.get("apiKeyHelper", "")
    assert "kimi_coding_oauth.py token" in helper
    # Operator's live config is never touched.
    assert not (tmp_path / "home" / ".claude" / "settings.json").exists()


def test_coding_oauth_missing_credentials_mentions_kimi_login(tmp_path: Path) -> None:
    _, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "coding"],
        env_overrides={
            **_OAUTH_ENV_CLEAR,
            "KIMI_CODE_CREDENTIALS_PATH": str(tmp_path / "does-not-exist.json"),
        },
    )
    assert result.returncode == 1
    assert "no Kimi API credential" in result.stderr
    assert "kimi login" in result.stderr


def test_dry_run_resolves_route_without_launching(tmp_path: Path) -> None:
    output, result = _run_with_fakes(
        tmp_path,
        [],
        env_overrides={"KIMICC_DRY_RUN": "1"},
    )
    assert result.returncode == 0, result.stderr
    assert "KIMICC_DRY_RUN=1: would exec" in result.stdout
    assert "auth=MOONSHOT_API_KEY" in result.stdout
    # Fake claude was never executed.
    assert output == ""


def test_defaults_are_coding_isolated_infra_agent(tmp_path: Path) -> None:
    """Bare launch: coding endpoint + isolated config + infra-orchestrator agent."""
    cred = _write_oauth_credentials(tmp_path)
    output, result = _run_with_fakes(
        tmp_path,
        [],
        env_overrides={
            **_OAUTH_ENV_CLEAR,
            "KIMI_CODE_CREDENTIALS_PATH": str(cred),
            "KIMI_CODE_OAUTH_HOST": "http://127.0.0.1:9",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "base=https://api.kimi.com/coding" in output
    # OAuth + isolation → apiKeyHelper mode, no static token exported.
    assert "auth=unset" in output
    assert "helper_ttl=300000" in output
    assert "config_dir=" in output
    assert ".claude-kimicc" in output
    # Default agent injected and forwarded.
    assert "arg=--agent" in output
    assert "arg=infra-orchestrator" in output
    assert "agent=infra-orchestrator (default; override with --agent)" in result.stdout


def test_explicit_agent_overrides_default(tmp_path: Path) -> None:
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "platform", "--no-isolate-config", "--agent", "curriculum-orchestrator"],
    )
    assert result.returncode == 0, result.stderr
    assert "arg=curriculum-orchestrator" in output
    assert "arg=infra-orchestrator" not in output
    assert "default; override with --agent" not in result.stdout


def test_no_isolate_config_uses_live_config_dir(tmp_path: Path) -> None:
    cred = _write_oauth_credentials(tmp_path)
    output, result = _run_with_fakes(
        tmp_path,
        ["--no-isolate-config"],
        env_overrides={
            **_OAUTH_ENV_CLEAR,
            "KIMI_CODE_CREDENTIALS_PATH": str(cred),
            "KIMI_CODE_OAUTH_HOST": "http://127.0.0.1:9",
        },
    )
    assert result.returncode == 0, result.stderr
    assert "config_dir=unset" in output
    # Without isolation the OAuth token is exported directly (short-session mode).
    assert "auth=oauth-acc" in output
    assert "helper_ttl=unset" in output


def test_epic_flag_is_forwarded(tmp_path: Path) -> None:
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "platform", "--no-isolate-config", "--epic=atlas"],
    )
    assert result.returncode == 0, result.stderr
    assert "arg=--epic=atlas" in output
    # Epic implies the lane identity: the infra-orchestrator default must NOT
    # be injected (an infra persona on the atlas lane would be a mismatch).
    assert "arg=--agent" not in output
    assert "arg=infra-orchestrator" not in output
    assert "identity derives from --epic" in result.stdout


def test_epic_plus_explicit_agent_keeps_agent(tmp_path: Path) -> None:
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "platform", "--no-isolate-config", "--epic", "atlas", "--agent", "infra-orchestrator"],
    )
    assert result.returncode == 0, result.stderr
    assert "arg=--epic" in output
    assert "arg=infra-orchestrator" in output


def test_isolate_config_env_rejects_invalid_value(tmp_path: Path) -> None:
    _, result = _run_with_fakes(
        tmp_path,
        [],
        env_overrides={"KIMICC_ISOLATE_CONFIG": "2"},
    )
    assert result.returncode == 2
    assert "KIMICC_ISOLATE_CONFIG must be 0 or 1" in result.stderr


def test_empty_kimicc_agent_inherits_project_default(tmp_path: Path) -> None:
    """KIMICC_AGENT='' (set but empty) suppresses the default --agent injection,
    so Claude Code falls back to the project settings.json default agent."""
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "platform", "--no-isolate-config"],
        env_overrides={"KIMICC_AGENT": ""},
    )
    assert result.returncode == 0, result.stderr
    assert "arg=--agent" not in output
    assert "arg=infra-orchestrator" not in output


def test_ddash_passthrough_forwards_colliding_flags(tmp_path: Path) -> None:
    """Args after -- reach Claude Code verbatim, even ones colliding with
    launcher flags (a bare --endpoint would otherwise be consumed by it)."""
    output, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "platform", "--no-isolate-config", "--", "--verbose", "--endpoint"],
    )
    assert result.returncode == 0, result.stderr
    assert "arg=--verbose" in output
    assert "arg=--endpoint" in output


def test_ddash_forwarded_model_still_rejected(tmp_path: Path) -> None:
    """-- does not smuggle a lead-model override past the launcher."""
    _, result = _run_with_fakes(
        tmp_path,
        ["--endpoint", "platform", "--no-isolate-config", "--", "--model", "opus"],
    )
    assert result.returncode == 2
    assert "owns the lead model" in result.stderr
    assert "default; override with --agent" not in result.stdout
