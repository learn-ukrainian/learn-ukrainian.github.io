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


def test_git_global_config_sandboxed_without_operator_credential_fallback() -> None:
    """#2842: agent `git config --global` writes go to a throwaway sandbox copy,
    while credential helpers cannot reach the operator's keychain."""
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "USER": "example",
            "LU_AGENT_GITHUB_TOKEN": "ghp_agenttoken",
        },
        clear=True,
    ):
        env = build_agent_env(provider="claude")

    # Global config redirected to the runtime's throwaway sandbox copy.
    assert env["GIT_CONFIG_GLOBAL"].endswith("agent.gitconfig")
    assert "lu-agent-runtime-git" in env["GIT_CONFIG_GLOBAL"]
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GIT_CONFIG_KEY_0"] == "credential.helper"
    assert env["GIT_CONFIG_KEY_1"] == "http.https://github.com/.extraheader"
    assert env["GIT_ASKPASS"].endswith("git-askpass.sh")
    assert env["GH_TOKEN"] == "ghp_agenttoken"


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


def test_gh_auth_chain_preserved_without_identity_token(tmp_path) -> None:
    """#7166 / #7472: on a job host the ops account is logged in via
    `gh auth login` and no GH_TOKEN/App material exists. The worker/review
    seat must keep the host gh auth chain: a usable GH_CONFIG_DIR (with
    hosts.yml) passes through (not redirected to an empty sandbox), the
    credential helper is NOT blanked, and no GIT_ASKPASS is injected. The
    extraheader stays neutralized and global-config writes stay sandboxed.
    """
    gh_config = tmp_path / "gh-config"
    gh_config.mkdir()
    (gh_config / "hosts.yml").write_text("github.com:\n    user: ops\n", encoding="utf-8")

    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "USER": "example",
            "GH_CONFIG_DIR": str(gh_config),
        },
        clear=True,
    ):
        env = build_agent_env(provider="kimi")

    assert "GH_TOKEN" not in env
    assert "GITHUB_TOKEN" not in env
    assert "GIT_ASKPASS" not in env
    assert env["GH_CONFIG_DIR"] == str(gh_config)
    # credential.helper must NOT be blanked in no-token mode.
    keys = [v for k, v in env.items() if k.startswith("GIT_CONFIG_KEY_")]
    assert "credential.helper" not in keys
    assert "http.https://github.com/.extraheader" in keys
    # Write isolation (#2842) stays: global config is still the sandbox copy.
    assert "lu-agent-runtime-git" in env["GIT_CONFIG_GLOBAL"]
    assert env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert env["GH_PROMPT_DISABLED"] == "1"


def test_gh_config_dir_defaults_to_home_without_identity_token() -> None:
    """#7166: with no explicit host GH_CONFIG_DIR, leave it unset so gh falls
    back to its default config dir under the preserved HOME — never to an
    empty sandbox dir."""
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "USER": "example",
        },
        clear=True,
    ):
        env = build_agent_env(provider="kimi")

    assert "GH_CONFIG_DIR" not in env
    assert env["HOME"] == "/Users/example"


def test_empty_sandbox_gh_config_dir_rejected_without_identity_token(tmp_path) -> None:
    """#7472: an inherited empty lu-agent-runtime-git GH_CONFIG_DIR must not
    pass through — leave unset so gh recovers to $HOME/.config/gh."""
    empty_sandbox = tmp_path / "lu-agent-runtime-git-deadbeef" / "gh"
    empty_sandbox.mkdir(parents=True)

    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "USER": "example",
            "GH_CONFIG_DIR": str(empty_sandbox),
        },
        clear=True,
    ):
        env = build_agent_env(provider="codex")

    assert "GH_CONFIG_DIR" not in env
    assert env["HOME"] == "/Users/example"
    assert "GH_TOKEN" not in env


def test_credential_helper_survives_sandbox_copy_without_identity_token(tmp_path) -> None:
    """#7166: the copied global config keeps `gh auth git-credential`-style
    helpers in no-token mode (push/comment must work) but still drops the
    extraheader. Token mode keeps the #2842 behavior of stripping the helper.
    """
    gitconfig = tmp_path / ".gitconfig"
    gitconfig.write_text(
        "[user]\n"
        "\tname = Example\n"
        "[credential]\n"
        "\thelper = !/usr/bin/gh auth git-credential\n"
        "[http \"https://github.com/\"]\n"
        "\textraheader = AUTHORIZATION: basic c2VjcmV0\n",
        encoding="utf-8",
    )

    with patch.dict(
        "os.environ",
        {"PATH": "/usr/bin", "HOME": str(tmp_path), "USER": "example"},
        clear=True,
    ):
        no_token_env = build_agent_env(provider="kimi")
        sandbox_no_token = Path(no_token_env["GIT_CONFIG_GLOBAL"]).read_text(
            encoding="utf-8"
        )

    assert "gh auth git-credential" in sandbox_no_token
    assert "extraheader" not in sandbox_no_token.lower()

    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": str(tmp_path),
            "USER": "example",
            "LU_AGENT_GITHUB_TOKEN": "ghp_agenttoken",
        },
        clear=True,
    ):
        token_env = build_agent_env(provider="kimi")
        sandbox_token = Path(token_env["GIT_CONFIG_GLOBAL"]).read_text(
            encoding="utf-8"
        )

    assert "gh auth git-credential" not in sandbox_token
    assert token_env["GIT_ASKPASS"].endswith("git-askpass.sh")


def test_usable_host_gh_config_dir_requires_hosts_yml(tmp_path) -> None:
    from agent_runtime.env_sanitize import usable_host_gh_config_dir

    empty = tmp_path / "empty"
    empty.mkdir()
    assert usable_host_gh_config_dir(str(empty)) is None

    good = tmp_path / "good"
    good.mkdir()
    (good / "hosts.yml").write_text("github.com:\n    user: ops\n", encoding="utf-8")
    assert usable_host_gh_config_dir(str(good)) == str(good)
    assert usable_host_gh_config_dir(None) is None
    assert usable_host_gh_config_dir("") is None
