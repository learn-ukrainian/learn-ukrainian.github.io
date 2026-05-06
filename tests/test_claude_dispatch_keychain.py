from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from agent_runtime.env_sanitize import build_agent_env


@pytest.mark.skipif(sys.platform != "darwin", reason="Claude OAuth keychain access is macOS-specific")
def test_claude_oauth_keychain_works_with_sanitized_env() -> None:
    claude_bin = shutil.which("claude")
    if not claude_bin:
        pytest.skip("Claude CLI is not installed")

    result = subprocess.run(
        [claude_bin, "-p", "say PONG", "--model", "claude-haiku-4-5"],
        env=build_agent_env(provider="claude"),
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )

    combined_output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0 and (
        "Not logged in" in combined_output or "Please run /login" in combined_output
    ):
        pytest.skip("Claude CLI is not logged in with OAuth on this machine")

    assert result.returncode == 0, combined_output
    assert "PONG" in result.stdout
