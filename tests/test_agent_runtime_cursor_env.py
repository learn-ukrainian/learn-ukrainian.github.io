"""Unit tests for CursorAdapter environment plumbing and sanitization (#7582).

Verifies that CURSOR_API_KEY is correctly passed to the child process environment
when present in either:
(a) The parent environment (os.environ), or
(b) ~/.config/cursor-agent/api.key.env

Also verifies that unrelated environment variables and other provider credentials
are not leaked to the child environment.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.adapters.cursor import (
    CursorAdapter,
    _load_cursor_api_key_from_env_file,
)
from agent_runtime.env_sanitize import build_agent_env


@pytest.fixture
def adapter() -> CursorAdapter:
    return CursorAdapter()


def test_cursor_adapter_child_env_when_api_key_in_parent_env(adapter, tmp_path):
    """When CURSOR_API_KEY is in parent env, it must be present in child env."""
    parent_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
        "CURSOR_API_KEY": "parent-env-cursor-key",
        "UNRELATED_SECRET": "should-be-dropped",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        plan = adapter.build_invocation(
            prompt="test prompt",
            mode="read-only",
            cwd=tmp_path,
            model="auto",
            task_id="test-task",
            session_id=None,
            tool_config={},
        )
        child_env = build_agent_env(provider="cursor", overrides=plan.env_overrides)

    assert "CURSOR_API_KEY" in child_env
    assert child_env["CURSOR_API_KEY"] == "parent-env-cursor-key"
    assert "UNRELATED_SECRET" not in child_env


def test_cursor_adapter_child_env_when_api_key_in_file(adapter, tmp_path, monkeypatch):
    """When CURSOR_API_KEY is in ~/.config/cursor-agent/api.key.env, it must be loaded."""
    config_dir = tmp_path / ".config" / "cursor-agent"
    config_dir.mkdir(parents=True, exist_ok=True)
    key_file = config_dir / "api.key.env"
    key_file.write_text(
        "# Cursor Agent Key Configuration\nCURSOR_API_KEY=file-backed-cursor-key\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    parent_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
        "UNRELATED_SECRET": "should-be-dropped",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        plan = adapter.build_invocation(
            prompt="test prompt",
            mode="workspace-write",
            cwd=tmp_path,
            model="auto",
            task_id="test-task",
            session_id=None,
            tool_config={},
        )
        child_env = build_agent_env(provider="cursor", overrides=plan.env_overrides)

    assert "CURSOR_API_KEY" in child_env
    assert child_env["CURSOR_API_KEY"] == "file-backed-cursor-key"
    assert "UNRELATED_SECRET" not in child_env


def test_cursor_adapter_parent_env_wins_over_file(adapter, tmp_path, monkeypatch):
    """Parent env CURSOR_API_KEY takes precedence over api.key.env file."""
    config_dir = tmp_path / ".config" / "cursor-agent"
    config_dir.mkdir(parents=True, exist_ok=True)
    key_file = config_dir / "api.key.env"
    key_file.write_text(
        "CURSOR_API_KEY=file-backed-cursor-key\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    parent_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
        "CURSOR_API_KEY": "parent-env-cursor-key",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        plan = adapter.build_invocation(
            prompt="test prompt",
            mode="danger",
            cwd=tmp_path,
            model="auto",
            task_id="test-task",
            session_id=None,
            tool_config={},
        )
        child_env = build_agent_env(provider="cursor", overrides=plan.env_overrides)

    assert child_env["CURSOR_API_KEY"] == "parent-env-cursor-key"


def test_cursor_adapter_child_env_no_key_when_both_absent(adapter, tmp_path, monkeypatch):
    """When no key is in env or file, CURSOR_API_KEY is omitted from child env."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    parent_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
    }

    with patch.dict("os.environ", parent_env, clear=True):
        plan = adapter.build_invocation(
            prompt="test prompt",
            mode="read-only",
            cwd=tmp_path,
            model="auto",
            task_id="test-task",
            session_id=None,
            tool_config={},
        )
        child_env = build_agent_env(provider="cursor", overrides=plan.env_overrides)

    assert "CURSOR_API_KEY" not in child_env
    assert "PATH" in child_env
    assert "HOME" in child_env


def test_cursor_adapter_child_env_does_not_leak_unrelated_or_foreign_credentials(adapter, tmp_path):
    """Unrelated secrets and other provider credentials must be scrubbed."""
    parent_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(tmp_path),
        "CURSOR_API_KEY": "valid-cursor-key",
        "OPENAI_API_KEY": "sk-openai-foreign",
        "ANTHROPIC_API_KEY": "sk-ant-foreign",
        "GEMINI_API_KEY": "gemini-foreign",
        "CODEX_API_KEY": "codex-foreign",
        "MOONSHOT_API_KEY": "kimi-foreign",
        "CUSTOM_AUTH_TOKEN": "custom-token-secret",
        "DATABASE_PASSWORD": "db-secret-password",
        "UNRELATED_FLAG": "drop-me",
        "LU_ENTIRE_CAPTURE_OWNER": "fleet",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        plan = adapter.build_invocation(
            prompt="test prompt",
            mode="workspace-write",
            cwd=tmp_path,
            model="auto",
            task_id="test-task",
            session_id=None,
            tool_config={},
        )
        child_env = build_agent_env(provider="cursor", overrides=plan.env_overrides)

    # Safe / provider variables kept:
    assert child_env["CURSOR_API_KEY"] == "valid-cursor-key"
    assert child_env["LU_ENTIRE_CAPTURE_OWNER"] == "fleet"
    assert "PATH" in child_env
    assert "HOME" in child_env

    # Foreign provider secrets dropped:
    assert "OPENAI_API_KEY" not in child_env
    assert "ANTHROPIC_API_KEY" not in child_env
    assert "GEMINI_API_KEY" not in child_env
    assert "CODEX_API_KEY" not in child_env
    assert "MOONSHOT_API_KEY" not in child_env

    # Unrelated secrets / variables dropped:
    assert "CUSTOM_AUTH_TOKEN" not in child_env
    assert "DATABASE_PASSWORD" not in child_env
    assert "UNRELATED_FLAG" not in child_env


def test_cursor_tools_alias_resolves_and_passes_key():
    """cursor-tools alias resolves to cursor and passes CURSOR_API_KEY."""
    parent_env = {
        "PATH": "/usr/bin:/bin",
        "HOME": "/Users/example",
        "CURSOR_API_KEY": "cursor-tools-key",
        "UNRELATED_VAR": "drop-me",
    }

    with patch.dict("os.environ", parent_env, clear=True):
        child_env = build_agent_env(provider="cursor-tools", overrides={})

    assert child_env["CURSOR_API_KEY"] == "cursor-tools-key"
    assert "UNRELATED_VAR" not in child_env


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("CURSOR_API_KEY=raw_key_123", "raw_key_123"),
        ('CURSOR_API_KEY="double_quoted_key"', "double_quoted_key"),
        ("CURSOR_API_KEY='single_quoted_key'", "single_quoted_key"),
        ("export CURSOR_API_KEY=exported_key", "exported_key"),
        ('export CURSOR_API_KEY="exported_double_quoted"', "exported_double_quoted"),
        ("  CURSOR_API_KEY  =  spaced_key  ", "spaced_key"),
        ("# Comment line\n\nCURSOR_API_KEY=commented_file_key\n", "commented_file_key"),
        ("OTHER_VAR=abc\nCURSOR_API_KEY=multi_line_key\nANOTHER=123", "multi_line_key"),
        ("CURSOR_API_KEY=", None),
        ("OTHER_KEY=only_other", None),
        ("# CURSOR_API_KEY=commented_out", None),
        ("", None),
    ],
)
def test_load_cursor_api_key_from_env_file_formats(tmp_path, content, expected):
    """Test parsing various valid and invalid .env file line formats."""
    env_file = tmp_path / "api.key.env"
    env_file.write_text(content, encoding="utf-8")
    result = _load_cursor_api_key_from_env_file(env_file)
    assert result == expected


def test_load_cursor_api_key_from_env_file_missing(tmp_path):
    """Non-existent file returns None without raising."""
    non_existent = tmp_path / "does_not_exist.env"
    assert _load_cursor_api_key_from_env_file(non_existent) is None
