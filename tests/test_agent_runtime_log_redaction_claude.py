"""Runtime command diagnostics must not retain argv values (#10751)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from agent_runtime.adapters.claude import ClaudeAdapter


@pytest.mark.parametrize("prefix_kind", ["native", "wrapper", "string"])
@pytest.mark.parametrize("effort", [None, "xhigh"])
def test_claude_unsupported_effort_logs_only_basename_and_ignored_effort(
    tmp_path, caplog, prefix_kind, effort,
):
    secret = "secret-looking-command-option-value"
    executable = str(tmp_path / "private-executable-location" / "claude")
    prefix = executable if prefix_kind == "string" else [executable]
    if prefix_kind == "wrapper":
        executable = str(tmp_path / "private-executable-location" / "npx")
        prefix = [executable, "--config", secret, "@anthropic-ai/claude-code"]
    with (
        patch("agent_runtime.adapters.claude._ensure_supported_claude_cli_version", return_value=(2, 1, 116)),
        patch("utils.claude_version.supports_effort", return_value=False),
        caplog.at_level(logging.DEBUG),
    ):
        plan = ClaudeAdapter().build_invocation(
            prompt="private-prompt-value",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id="private-session-value",
            tool_config={"cmd_prefix": prefix, "mcp_config_path": secret},
            effort=effort,
        )

    assert secret in plan.cmd
    assert "--effort" not in plan.cmd
    records = [record for record in caplog.records if record.name == "agent_runtime.adapters.claude"]
    assert len(records) == 1
    assert records[0].getMessage() == (
        f"Claude CLI at {Path(executable).name} does not support --effort; "
        f"ignoring effort={effort or 'high'!r} and using CLI default (#1396)"
    )
    assert records[0].args == (Path(executable).name, effort or "high")
    for record in caplog.records:
        for value in (secret, executable, "private-executable-location", "private-prompt-value", "private-session-value"):
            assert value not in record.getMessage()
            assert value not in repr(vars(record))
