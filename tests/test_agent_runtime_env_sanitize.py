from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.env_sanitize import build_agent_env
from agent_runtime.registry import AGENTS
from agent_runtime.result import ParseResult
from agent_runtime.runner import _execute_invocation_plan
from tests.helpers.python import project_python

_TEST_PYTHON = project_python()


_CREDENTIAL_PROBE_NAMES = (
    "CURSOR_API_KEY",
    "OPENAI_API_KEY",
    "CODEX_API_KEY",
    "ANTHROPIC_API_KEY",
    "CLAUDE_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "GOOGLE_GENERATIVE_AI_API_KEY",
    "XAI_API_KEY",
    "KIMICC_AUTH_TOKEN",
    "MOONSHOT_API_KEY",
    "KIMI_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "ZZ_PROBE_API_KEY",
    "ZZ_PROBE_TOKEN",
    "ZZ_PROBE_SECRET",
    "AB_PROBE_API_KEY",
    "LU_PROBE_TOKEN",
    "LC_PROBE_SECRET",
)


@pytest.mark.parametrize("provider", sorted(AGENTS))
@pytest.mark.parametrize("override", [False, True], ids=["inherited", "override"])
def test_registry_provider_credential_matrix(tmp_path, provider, override):
    credentials = {name: f"sentinel-{name.lower()}" for name in _CREDENTIAL_PROBE_NAMES}
    parent = {"PATH": "/usr/bin", "HOME": str(tmp_path)}
    if not override:
        parent.update(credentials)

    with patch.dict("os.environ", parent, clear=True):
        env = build_agent_env(
            provider=provider,
            model=AGENTS[provider]["default_model"],
            overrides=credentials if override else {},
        )

    expected = {
        "codex": {"OPENAI_API_KEY", "CODEX_API_KEY"},
        "claude": {"ANTHROPIC_API_KEY", "CLAUDE_API_KEY"},
        "gemini": {"GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"},
        "cursor": {"CURSOR_API_KEY"},
        "acpx-cursor-shadow": {"CURSOR_API_KEY"},
        "kimi": {"KIMICC_AUTH_TOKEN", "MOONSHOT_API_KEY", "KIMI_API_KEY", "ANTHROPIC_AUTH_TOKEN"},
    }.get(provider, set())
    # GitHub identity is shared intentionally; Kimi seats cannot publish.
    if provider not in {"kimi", "acpx-kimi-shadow", "acpx-kimicc-shadow"}:
        expected.add("GH_TOKEN")

    assert {name: env[name] for name in credentials if name in env} == {name: credentials[name] for name in expected}


def test_build_agent_env_drops_sensitive_names():
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "CUSTOM_TOKEN": "benign",
            "CUSTOMTOKEN": "benign",
            "DB_PASSWORD": "benign",
            "AWS_ACCESS_KEY_ID": "benign",
            "GOOGLE_APPLICATION_CREDENTIALS": "/tmp/creds.json",
            "SESSION_COOKIE": "benign",
            "AB_TRACE_ID": "safe",
        },
        clear=True,
    ):
        env = build_agent_env(provider="codex", overrides={})

    assert env["AB_TRACE_ID"] == "safe"
    assert "CUSTOM_TOKEN" not in env
    assert "CUSTOMTOKEN" not in env
    assert "DB_PASSWORD" not in env
    assert "AWS_ACCESS_KEY_ID" not in env
    assert "GOOGLE_APPLICATION_CREDENTIALS" not in env
    assert "SESSION_COOKIE" not in env


def test_build_agent_env_drops_sensitive_values():
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "AB_GITHUB_PAT": "github_pat_fakevalue",
            "AB_GITHUB_CLASSIC": "ghp_fakevalue",
            "AB_OPENAI_SHAPED": "sk-fakevalue",
            "AB_SLACK_SHAPED": "xoxb-fake-value",
            "AB_HF_SHAPED": "hf_fakevalue",
            "AB_NPM_SHAPED": "npm_fakevalue",
            "AB_AWS_SHAPED": "AKIAFAKEFAKEFAKE",
            "AB_GOOGLE_SHAPED": "AIzaFakeValue",
            "AB_SAFE_VALUE": "trace-123",
        },
        clear=True,
    ):
        env = build_agent_env(provider="codex", overrides={})

    assert env["AB_SAFE_VALUE"] == "trace-123"
    assert "AB_GITHUB_PAT" not in env
    assert "AB_GITHUB_CLASSIC" not in env
    assert "AB_OPENAI_SHAPED" not in env
    assert "AB_SLACK_SHAPED" not in env
    assert "AB_HF_SHAPED" not in env
    assert "AB_NPM_SHAPED" not in env
    assert "AB_AWS_SHAPED" not in env
    assert "AB_GOOGLE_SHAPED" not in env


def test_build_agent_env_preserves_safe_allowlist_and_applies_overrides_first():
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "TMPDIR": "/tmp",
            "LANG": "en_US.UTF-8",
            "LC_ALL": "C",
            "AB_REPO_ROOT": "/repo",
            "LU_BYPASS_RATE_LIMIT": "1",
            "LU_RUNTIME_TMP_BASE_ROOT": "/tmp",
            "LU_RUNTIME_TMP_ROOT": "/tmp/learn-ukrainian/task-4956",
            "LU_SCRATCH_ROOT": "/var/tmp/lu",
            "UNRELATED": "drop-me",
        },
        clear=True,
    ):
        env = build_agent_env(
            provider="gemini",
            overrides={
                "PATH": "/custom/bin",
                "GEMINI_AUTH_MODE": "subscription",
                "AB_BAD_OVERRIDE": "sk-override",
                "GITHUB_TOKEN": "ghp_fakeoverride",
            },
        )

    assert env["PATH"] == "/custom/bin"
    assert env["HOME"] == "/Users/example"
    assert env["TMPDIR"] == "/tmp"
    assert env["LANG"] == "en_US.UTF-8"
    assert env["LC_ALL"] == "C"
    assert env["AB_REPO_ROOT"] == "/repo"
    assert env["LU_BYPASS_RATE_LIMIT"] == "1"
    assert env["LU_RUNTIME_TMP_BASE_ROOT"] == "/tmp"
    assert env["LU_RUNTIME_TMP_ROOT"] == "/tmp/learn-ukrainian/task-4956"
    assert env["LU_SCRATCH_ROOT"] == "/var/tmp/lu"
    assert env["GEMINI_AUTH_MODE"] == "subscription"
    assert "AB_BAD_OVERRIDE" not in env
    assert "GITHUB_TOKEN" not in env
    assert "UNRELATED" not in env


def test_acpx_grok_cached_login_selector_survives_without_xai_credentials():
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "XAI_API_KEY": "xai-secret",
            "ACPX_AUTH_XAI_API_KEY": "xai-selector-secret",
        },
        clear=True,
    ):
        env = build_agent_env(
            provider="acpx-grok-shadow",
            overrides={"ACPX_AUTH_CACHED_TOKEN": "1"},
        )

    assert env["ACPX_AUTH_CACHED_TOKEN"] == "1"
    assert "XAI_API_KEY" not in env
    assert "ACPX_AUTH_XAI_API_KEY" not in env


def test_acpx_auth_method_selectors_require_literal_one():
    with patch.dict(
        "os.environ",
        {
            "PATH": "/usr/bin",
            "HOME": "/Users/example",
            "ACPX_AUTH_CHAT_GPT": "unexpected",
            "ACPX_AUTH_CACHED_TOKEN": "unexpected",
        },
        clear=True,
    ):
        codex_env = build_agent_env(provider="acpx-codex-shadow")
        grok_env = build_agent_env(provider="acpx-grok-shadow")

    assert "ACPX_AUTH_CHAT_GPT" not in codex_env
    assert "ACPX_AUTH_CACHED_TOKEN" not in grok_env


@dataclass
class _SmokePlan:
    cmd: list[str]
    cwd: Path
    stdin_payload: str = ""
    output_file: Path | None = None
    env_overrides: dict[str, str] = field(default_factory=dict)
    env_unsets: tuple[str, ...] = ()
    liveness_paths: tuple[Path, ...] = ()


class _SmokeAdapter:
    def liveness_signal_paths(self, _plan: _SmokePlan) -> tuple[Path, ...]:
        return ()

    def parse_response(self, *, stdout: str, **_kwargs: object) -> ParseResult:
        return ParseResult(ok=True, response=stdout)


def test_runner_smoke_spawns_each_provider_with_only_its_own_key(tmp_path):
    keys = [
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "ANTHROPIC_API_KEY",
        "CLAUDE_API_KEY",
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
        "CURSOR_API_KEY",
        "GITHUB_TOKEN",
        "GH_TOKEN",
    ]
    script = (
        "import json, os; "
        f"keys = {keys!r}; "
        "print(json.dumps({k: os.environ[k] for k in keys if k in os.environ}, "
        "sort_keys=True))"
    )
    parent_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp_path),
        "GEMINI_API_KEY": "gemini-key",
        "GOOGLE_API_KEY": "google-key",
        "ANTHROPIC_API_KEY": "sk-ant-fake",
        "CLAUDE_API_KEY": "sk-claude-fake",
        "OPENAI_API_KEY": "sk-openai-fake",
        "CODEX_API_KEY": "codex-key",
        "CURSOR_API_KEY": "cursor-key",
        "GITHUB_TOKEN": "ghp_fakegithubtoken",
        "GH_TOKEN": "ghp_fakeghtoken",
    }
    expected = {
        "gemini": {
            "GEMINI_API_KEY": "gemini-key",
            "GOOGLE_API_KEY": "google-key",
            "GH_TOKEN": "ghp_fakeghtoken",
        },
        "claude": {
            "ANTHROPIC_API_KEY": "sk-ant-fake",
            "CLAUDE_API_KEY": "sk-claude-fake",
            "GH_TOKEN": "ghp_fakeghtoken",
        },
        "codex": {
            "OPENAI_API_KEY": "sk-openai-fake",
            "CODEX_API_KEY": "codex-key",
            "GH_TOKEN": "ghp_fakeghtoken",
        },
        "cursor": {
            "CURSOR_API_KEY": "cursor-key",
            "GH_TOKEN": "ghp_fakeghtoken",
        },
    }

    with (
        patch.dict("os.environ", parent_env, clear=True),
        patch(
            "agent_runtime.runner._POLL_INTERVAL_S",
            0.01,
        ),
    ):
        for provider, expected_env in expected.items():
            plan = _SmokePlan(
                cmd=[_TEST_PYTHON, "-c", script],
                cwd=tmp_path,
            )
            outcome = _execute_invocation_plan(
                agent_name=provider,
                adapter=_SmokeAdapter(),
                plan=plan,
                prompt="env smoke",
                mode="read-only",
                cwd=tmp_path,
                model="smoke-model",
                task_id=f"{provider}-env-smoke",
                session_id=None,
                entrypoint="runtime-test",
                hard_timeout=10,
                stall_timeout=10,
            )

            assert outcome.parse.ok is True
            assert json.loads(outcome.stdout_text) == expected_env


def test_runner_gemini_subprocess_gets_only_resolved_agent_identity(tmp_path):
    script = (
        "import os, sys; "
        "sys.exit(0 if os.environ.get('GH_TOKEN') == 'ghp_agenttoken' and "
        "'GITHUB_TOKEN' not in os.environ else 1)"
    )
    parent_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(tmp_path),
        "GH_TOKEN": "ghp_fakeghtoken",
        "GITHUB_TOKEN": "ghp_operatorgithub",
        "LU_AGENT_GITHUB_TOKEN": "ghp_agenttoken",
    }

    with (
        patch.dict("os.environ", parent_env, clear=True),
        patch(
            "agent_runtime.runner._POLL_INTERVAL_S",
            0.01,
        ),
    ):
        outcome = _execute_invocation_plan(
            agent_name="gemini",
            adapter=_SmokeAdapter(),
            plan=_SmokePlan(cmd=[_TEST_PYTHON, "-c", script], cwd=tmp_path),
            prompt="resolved GitHub identity smoke",
            mode="read-only",
            cwd=tmp_path,
            model="smoke-model",
            task_id="gemini-no-gh-token-smoke",
            session_id=None,
            entrypoint="runtime-test",
            hard_timeout=10,
            stall_timeout=10,
        )

    assert outcome.returncode == 0
    assert outcome.parse.ok is True
