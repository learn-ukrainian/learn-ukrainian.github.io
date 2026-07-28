"""Regression coverage for Codex through the Claude-Code adapter."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from tests.test_launcher_contract import run_launcher


def _stub_claude(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    binary = bin_dir / "claude"
    binary.write_text(
        "#!/usr/bin/env bash\n"
        "printf 'base=%s\\n' \"${ANTHROPIC_BASE_URL:-unset}\"\n"
        "printf 'token=%s\\n' \"${ANTHROPIC_AUTH_TOKEN:-unset}\"\n"
        "printf 'model=%s\\n' \"${ANTHROPIC_MODEL:-unset}\"\n"
        "printf 'args=%s\\n' \"$*\"\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return bin_dir


def test_codex_claude_code_harness_dry_run_uses_local_proxy_contract() -> None:
    result = run_launcher("start-codex.sh", "--harness", "claude-code")
    assert result.returncode == 0, result.stderr
    assert "credential_source=local-proxy-placeholder" in result.stdout
    assert "would exec claude --model gpt-5.6-terra" in result.stdout


@pytest.mark.parametrize("base", ("http://127.0.0.1:8317", "http://localhost:8317"))
def test_codex_claude_code_accepts_only_approved_local_proxy_endpoints(base: str) -> None:
    result = run_launcher("start-codex.sh", "--harness", "claude-code", env={"CODEX_CC_BASE_URL": base})
    assert result.returncode == 0, result.stderr


def test_codex_claude_code_rejects_external_proxy_endpoint() -> None:
    result = run_launcher(
        "start-codex.sh",
        "--harness",
        "claude-code",
        env={"CODEX_CC_BASE_URL": "https://foreign.invalid"},
    )
    assert result.returncode == 2
    assert "approved local CLIProxyAPI endpoint" in result.stderr


def test_codex_claude_code_clears_foreign_ambient_auth_before_exec(tmp_path: Path) -> None:
    bin_dir = _stub_claude(tmp_path)
    result = run_launcher(
        "start-codex.sh",
        "--harness",
        "claude-code",
        env={
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "ANTHROPIC_AUTH_TOKEN": "foreign-secret",
        },
        dry_run=False,
    )
    assert result.returncode == 0, result.stderr
    assert "base=http://127.0.0.1:8317" in result.stdout
    assert "token=sk-dummy" in result.stdout
    assert "foreign-secret" not in result.stdout + result.stderr


def test_codex_claude_code_dry_run_redacts_explicit_proxy_token() -> None:
    secret = "codex-proxy-secret"
    result = run_launcher(
        "start-codex.sh",
        "--harness",
        "claude-code",
        env={"CODEX_CC_AUTH_TOKEN": secret},
    )
    assert result.returncode == 0, result.stderr
    assert "credential_source=CODEX_CC_AUTH_TOKEN" in result.stdout
    assert secret not in result.stdout + result.stderr
