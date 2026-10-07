"""Family identity contract shared by Bash launchers and worker sanitization."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime import env_sanitize
from scripts.lib.git_identity import git_identity_env

REPO = Path(__file__).resolve().parents[1]
CASES = [
    ("agy", None, "Gemini"),
    ("gemini", None, "Gemini"),
    ("codex", None, "OpenAI"),
    ("terra", None, "OpenAI"),
    ("claude", None, "Claude"),
    ("kimi", None, "Kimi"),
    ("glm", None, "GLM"),
    ("opencode", None, "GLM"),
    ("deepseek", None, "DeepSeek"),
    ("grok", None, "Grok"),
    ("ox-alpha", None, "LU Unknown"),
    ("acp", None, "LU Unknown"),
    ("unmapped", "gpt-6.1-sol", "LU Unknown"),
    ("cursor", "grok-4.7-high", "Grok"),
    ("cursor", "Grok 4.7 256K High", "Grok"),
    ("cursor", "composer-2.5", "Kimi"),
    ("cursor", "Composer 2.5", "Kimi"),
    ("cursor", "claude-opus-5-5", "Claude"),
    ("cursor", "gpt-6.1-sol", "OpenAI"),
    ("cursor", "gemini-3.8-flash-high", "Gemini"),
    ("cursor", "auto", "LU Unknown"),
    ("cursor", None, "LU Unknown"),
    ("cursor", "unresolvable", "LU Unknown"),
    ("cursor", "fixture", "LU Unknown"),
    ("cursor", "qwen-3", "LU Unknown"),
    (" CODEX ", None, "OpenAI"),
]


def expected_identity(name):
    slug = "unknown" if name == "LU Unknown" else name.lower()
    return {
        f"GIT_{role}_{field}": value
        for role in ("AUTHOR", "COMMITTER")
        for field, value in (("NAME", name), ("EMAIL", f"{slug}@local.invalid"))
    }


@pytest.mark.parametrize("provider,model,name", CASES)
def test_git_identity_mapping(provider, model, name):
    assert git_identity_env(provider, model) == expected_identity(name)


@pytest.mark.parametrize("provider,model,name", CASES)
def test_identity_recreated_after_sanitization(monkeypatch, provider, model, name):
    # Both inherited and adapter-supplied Git identity are untrusted.
    for key, value in expected_identity("Parent").items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("LC_MODEL", "claude-opus-5-5")
    monkeypatch.setenv("GIT_DIR", "parent-git-dir")
    monkeypatch.setattr(env_sanitize, "_isolated_git_env", lambda *args, **kwargs: {})
    env = env_sanitize.build_agent_env(provider=provider, model=model, overrides=expected_identity("Override"))
    assert {key: env[key] for key in expected_identity(name)} == expected_identity(name)
    assert "GIT_DIR" not in env


@pytest.mark.parametrize("provider,model,name", CASES)
def test_launcher_export_git_identity(provider, model, name):
    env = (
        os.environ
        | expected_identity("Parent")
        | {
            "TEST_PROVIDER": provider,
            "TEST_MODEL": model or "",
            "TEST_ROOT": str(REPO),
            "TEST_PYTHON": sys.executable,
        }
    )
    result = subprocess.run(
        [
            "bash",
            "-euc",
            """
source "$TEST_ROOT/scripts/lib/launcher_core.sh"
LC_ROOT="$TEST_ROOT"
LC_PROVIDER="$TEST_PROVIDER"
LC_MODEL="$TEST_MODEL"
launcher_project_python() { printf '%s\\n' "$TEST_PYTHON"; }
launcher_export_git_identity
"$TEST_PYTHON" -c 'import json, os; print(json.dumps({k: v for k, v in os.environ.items() if k.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_")) and not k.endswith("DATE")}))'
""",
        ],
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout) == expected_identity(name)


def test_launcher_identity_helper_failure_refuses_export():
    result = subprocess.run(
        [
            "bash",
            "-uc",
            """
source scripts/lib/launcher_core.sh
launcher_project_python() { return 1; }
launcher_export_git_identity
""",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 3


@pytest.mark.parametrize("provider,model,name", CASES)
def test_spawned_git_commit_uses_lane_identity(tmp_path, monkeypatch, provider, model, name):
    monkeypatch.setenv("HOME", str(tmp_path))
    env = env_sanitize.build_agent_env(provider=provider, model=model)

    def git(*args):
        return subprocess.run(
            ["git", *args],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=True,
            timeout=30,
        ).stdout.strip()

    git("init", "-q")
    # A contradictory repo-local config must lose to the process identity.
    git("config", "user.name", "Parent")
    git("config", "user.email", "parent@local.invalid")
    git("-c", "core.hooksPath=/dev/null", "commit", "--allow-empty", "-qm", "Identity fixture")
    slug = "unknown" if name == "LU Unknown" else name.lower()
    assert git("show", "-s", "--format=%an|%ae|%cn|%ce") == f"{name}|{slug}@local.invalid|{name}|{slug}@local.invalid"
