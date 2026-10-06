"""Claude invocation tests never depend on the installed CLI version (#9903).

A fake ``claude`` that reports an old version sits first on ``PATH``. Tests
that build an invocation must still pass through the shared gate stub in
``tests/conftest.py`` on both module aliases; the gate's own tests, marked
``real_claude_cli_gate``, keep the real gate and still fail closed.
"""

import importlib
import os
import sys
from pathlib import Path

import pytest

from scripts.agent_runtime.adapters.claude import ClaudeAdapter

# The bare ``agent_runtime`` alias needs ``scripts/`` on the path (as test_agent_runtime.py does).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

OLD_VERSION = "2.1.50"
ALIASES = ("scripts.agent_runtime.adapters.claude", "agent_runtime.adapters.claude")


@pytest.fixture
def old_claude_on_path(tmp_path, monkeypatch):
    """Put a fake ``claude`` reporting an old version first on ``PATH``."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(f'#!/bin/sh\necho "{OLD_VERSION} (Claude Code)"\n', encoding="utf-8")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    return fake


def _build(adapter, cwd, fake):
    return adapter.build_invocation(
        prompt="hello",
        mode="read-only",
        cwd=cwd,
        model=None,
        task_id=None,
        session_id=None,
        tool_config={"cmd_prefix": [str(fake)]},
    )


def test_invocation_builds_with_old_cli_on_path(tmp_path, old_claude_on_path):
    plan = _build(ClaudeAdapter(), tmp_path, old_claude_on_path)
    assert plan.cmd[0] == str(old_claude_on_path)


@pytest.mark.parametrize("alias", ALIASES)
def test_gate_is_stubbed_on_every_alias(alias, old_claude_on_path):
    module = importlib.import_module(alias)
    assert module._ensure_supported_claude_cli_version((str(old_claude_on_path),)) is not None
    assert module._ensure_supported_claude_cli_version((str(old_claude_on_path),)) >= (2, 1, 116)


@pytest.mark.real_claude_cli_gate
@pytest.mark.parametrize("alias", ALIASES)
def test_real_gate_still_rejects_old_cli_on_every_alias(alias, old_claude_on_path):
    module = importlib.import_module(alias)
    with pytest.raises(RuntimeError, match=r"Claude CLI < 2\.1\.116"):
        module._ensure_supported_claude_cli_version((str(old_claude_on_path),))
