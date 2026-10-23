"""Timeout contracts for the #7213 slice 19 git/identity subprocess sites."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from scripts.agent_runtime import agent_github_identity, env_sanitize


def _raise_timeout(calls: list[dict[str, Any]]):
    def fake_run(*args: object, **kwargs: Any) -> Any:
        calls.append({"args": args, **kwargs})
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    return fake_run


def test_repository_name_git_timeout_raises_identity_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(agent_github_identity.subprocess, "run", _raise_timeout(calls))

    with pytest.raises(agent_github_identity.GitHubIdentityError, match="cannot determine the repository"):
        agent_github_identity._repository_name(tmp_path)

    assert calls[0]["timeout"] == agent_github_identity._GIT_TIMEOUT_SECONDS == 30


def test_isolated_git_env_timeout_keeps_fail_closed_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(env_sanitize.subprocess, "run", _raise_timeout(calls))
    monkeypatch.delenv("GIT_CONFIG_GLOBAL", raising=False)
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    env = env_sanitize._isolated_git_env(str(tmp_path), None)

    assert env == {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    assert calls[0]["timeout"] == env_sanitize._GIT_TIMEOUT_SECONDS == 30
