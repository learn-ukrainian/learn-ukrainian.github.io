from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.env_sanitize import build_agent_env
from agent_runtime.result import ParseResult
from agent_runtime.runner import _execute_invocation_plan


def _resolve_test_python() -> str:
    checkout_venv = Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python"
    if checkout_venv.exists():
        return str(checkout_venv)

    try:
        common_dir = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=Path(__file__).resolve().parent,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if common_dir:
            main_venv = (Path(common_dir) / ".." / ".venv" / "bin" / "python").resolve()
            if main_venv.exists():
                return str(main_venv)
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    active_venv = os.environ.get("VIRTUAL_ENV")
    if active_venv:
        candidate = Path(active_venv) / "bin" / "python"
        if candidate.exists():
            return str(candidate)

    raise RuntimeError("No project virtualenv Python found")


_TEST_PYTHON = _resolve_test_python()


def test_build_agent_env_passes_only_current_provider_credentials():
    parent_env = {
        "PATH": "/usr/bin",
        "HOME": "/Users/example",
        "GEMINI_API_KEY": "gemini-key",
        "GOOGLE_API_KEY": "google-key",
        "ANTHROPIC_API_KEY": "sk-ant-fake",
        "CLAUDE_API_KEY": "sk-claude-fake",
        "OPENAI_API_KEY": "sk-openai-fake",
        "CODEX_API_KEY": "codex-key",
        "GITHUB_TOKEN": "ghp_fakegithubtoken",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        gemini_env = build_agent_env(provider="gemini", overrides={})
        claude_env = build_agent_env(provider="claude", overrides={})
        codex_env = build_agent_env(provider="codex", overrides={})
        bridge_env = build_agent_env(provider="bridge", overrides={})

    assert gemini_env["GEMINI_API_KEY"] == "gemini-key"
    assert gemini_env["GOOGLE_API_KEY"] == "google-key"
    assert "ANTHROPIC_API_KEY" not in gemini_env
    assert "OPENAI_API_KEY" not in gemini_env

    assert claude_env["ANTHROPIC_API_KEY"] == "sk-ant-fake"
    assert claude_env["CLAUDE_API_KEY"] == "sk-claude-fake"
    assert "GEMINI_API_KEY" not in claude_env
    assert "OPENAI_API_KEY" not in claude_env

    assert codex_env["OPENAI_API_KEY"] == "sk-openai-fake"
    assert codex_env["CODEX_API_KEY"] == "codex-key"
    assert "GEMINI_API_KEY" not in codex_env
    assert "ANTHROPIC_API_KEY" not in codex_env

    assert "GEMINI_API_KEY" not in bridge_env
    assert "ANTHROPIC_API_KEY" not in bridge_env
    assert "OPENAI_API_KEY" not in bridge_env
    assert "GITHUB_TOKEN" not in bridge_env


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
    assert env["GEMINI_AUTH_MODE"] == "subscription"
    assert "AB_BAD_OVERRIDE" not in env
    assert "GITHUB_TOKEN" not in env
    assert "UNRELATED" not in env


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
        "GITHUB_TOKEN",
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
        "GITHUB_TOKEN": "ghp_fakegithubtoken",
    }
    expected = {
        "gemini": {
            "GEMINI_API_KEY": "gemini-key",
            "GOOGLE_API_KEY": "google-key",
        },
        "claude": {
            "ANTHROPIC_API_KEY": "sk-ant-fake",
            "CLAUDE_API_KEY": "sk-claude-fake",
        },
        "codex": {
            "OPENAI_API_KEY": "sk-openai-fake",
            "CODEX_API_KEY": "codex-key",
        },
    }

    with patch.dict("os.environ", parent_env, clear=True), patch(
        "agent_runtime.runner._POLL_INTERVAL_S", 0.01,
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
