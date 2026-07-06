from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.env_sanitize import build_agent_env


def test_user_and_logname_pass_through() -> None:
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "USER": "example",
            "LOGNAME": "example",
        },
        clear=True,
    ):
        env = build_agent_env(provider="claude")

    assert env["USER"] == "example"
    assert env["LOGNAME"] == "example"


def test_user_logname_not_provider_specific() -> None:
    parent_env = {
        "PATH": "/usr/bin",
        "HOME": "/Users/example",
        "USER": "example",
        "LOGNAME": "example",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        envs = {
            provider: build_agent_env(provider=provider)
            for provider in ("gemini", "claude", "codex", "bridge")
        }

    for env in envs.values():
        assert env["USER"] == "example"
        assert env["LOGNAME"] == "example"


def test_anthropic_api_key_still_passes_through_for_claude() -> None:
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "ANTHROPIC_API_KEY": "sk-ant-fake",
        },
        clear=True,
    ):
        env = build_agent_env(provider="claude")

    assert env["ANTHROPIC_API_KEY"] == "sk-ant-fake"


def test_secrets_still_scrubbed() -> None:
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "USER": "example",
            "LOGNAME": "example",
            "GITHUB_TOKEN": "ghp_fakegithubtoken",
        },
        clear=True,
    ):
        env = build_agent_env(provider="claude")

    assert env["USER"] == "example"
    assert env["LOGNAME"] == "example"
    assert "GITHUB_TOKEN" not in env


def test_git_global_config_sandboxed_system_left_intact() -> None:
    """#2842: agent `git config --global` writes go to a throwaway sandbox copy,
    while system config (the host's credential.helper) is left untouched."""
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "USER": "example",
        },
        clear=True,
    ):
        env = build_agent_env(provider="claude")

    # Global config redirected to the runtime's throwaway sandbox copy.
    assert env["GIT_CONFIG_GLOBAL"].endswith("agent.gitconfig")
    assert "lu-agent-runtime-git" in env["GIT_CONFIG_GLOBAL"]
    # System config deliberately NOT disabled — credential.helper must survive.
    assert "GIT_CONFIG_NOSYSTEM" not in env
    assert "GIT_CONFIG_SYSTEM" not in env


def test_workdir_repointing_git_env_is_scrubbed() -> None:
    """#4446: the child env must not carry vars that re-point its working root
    back to the primary checkout. The strict allowlist drops GIT_WORK_TREE /
    GIT_DIR / GIT_INDEX_FILE and PWD / OLDPWD, so a write-capable child cannot
    escape its worktree cwd via inherited git-discovery or shell state."""
    hostile = {
        "PATH": "/usr/bin",
        "HOME": "/Users/example",
        "GIT_WORK_TREE": "/repo/primary",
        "GIT_DIR": "/repo/primary/.git",
        "GIT_INDEX_FILE": "/repo/primary/.git/index",
        "GIT_COMMON_DIR": "/repo/primary/.git",
        "PWD": "/repo/primary",
        "OLDPWD": "/repo/primary/sub",
    }
    with patch.dict("os.environ", hostile, clear=True):
        env = build_agent_env(provider="codex")

    for leaked in ("GIT_WORK_TREE", "GIT_DIR", "GIT_INDEX_FILE",
                   "GIT_COMMON_DIR", "PWD", "OLDPWD"):
        assert leaked not in env, f"{leaked} must be scrubbed from the child env"
