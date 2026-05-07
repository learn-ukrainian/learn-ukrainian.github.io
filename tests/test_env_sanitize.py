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
