"""Runtime command diagnostics must not retain argv values (#10751)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from agent_runtime.adapters.deepseek import DeepSeekAdapter
from agent_runtime.adapters.glm import GlmAdapter
from scripts.agent_runtime.adapters.kimi import KimiAdapter
from tests.agent_runtime.adapters.kimi_admitted import admitted_tool_config


@pytest.mark.parametrize(
    ("adapter_type", "expected_message"),
    [
        (DeepSeekAdapter, "deepseek invocation"),
        (GlmAdapter, "glm invocation"),
        (KimiAdapter, "kimi invocation"),
    ],
)
def test_sibling_invocation_logs_constant_message(tmp_path, monkeypatch, caplog, adapter_type, expected_message):
    for variable in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    environment_value = "private-environment-value"
    monkeypatch.setenv("LOG_REDACTION_TEST_VALUE", environment_value)
    secret = "secret-looking-command-option-value"
    adapter = adapter_type()
    tool_config = {}
    if adapter_type is KimiAdapter:
        binary = tmp_path / "private-executable-value"
        binary.write_text("#!/bin/sh\n", encoding="utf-8")
        binary.chmod(0o755)
        monkeypatch.setenv("LEARN_UK_KIMI_BIN", str(binary))
        tool_config = admitted_tool_config(tmp_path, {"kimi_add_dirs": [secret]})
    effort = secret if adapter_type in (DeepSeekAdapter, GlmAdapter) else None
    with (
        patch(f"{adapter_type.__module__}.shutil.which", return_value=str(tmp_path / "runtime-cli")),
        caplog.at_level(logging.DEBUG),
    ):
        plan = adapter.build_invocation(
            prompt="private-prompt-value",
            mode="workspace-write",
            cwd=tmp_path,
            model=None,
            task_id="private-task-value",
            session_id="private-session-value",
            tool_config=tool_config,
            effort=effort,
        )
    assert secret in plan.cmd
    records = [record for record in caplog.records if record.name == adapter_type.__module__]
    assert len(records) == 1
    assert records[0].getMessage() == expected_message
    assert records[0].args == ()
    assert records[0].exc_info is None
    private_values = (
        secret,
        Path(plan.cmd[0]).name,
        adapter.default_model,
        "private-prompt-value",
        "private-task-value",
        "private-session-value",
        str(tmp_path),
        environment_value,
        *plan.env_overrides.values(),
    )
    for record in caplog.records:
        assert record.args == ()
        for value in plan.cmd:
            assert value not in record.getMessage()
            # Match whole values: the fixed agent_runtime source path contains "run".
            assert repr(value) not in repr(vars(record))
        for value in private_values:
            assert value not in record.getMessage()
            assert value not in repr(vars(record))
