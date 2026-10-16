"""Codex runtime command diagnostics must not retain argv values (#10751)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from agent_runtime.adapters.codex import CodexAdapter

_NO_CI_VARIABLES = ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL")
_BUDGET_MESSAGE = "non-claude adapter ignoring max_budget_usd; use hard-timeout/silence-timeout instead"


def test_non_claude_max_budget_warning_is_constant(tmp_path, monkeypatch, caplog):
    for variable in _NO_CI_VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    secret = "secret-looking-budget-value"
    with caplog.at_level(logging.DEBUG):
        CodexAdapter().build_invocation(
            prompt="private-prompt-value",
            mode="read-only",
            cwd=tmp_path,
            model=None,
            task_id=None,
            session_id=None,
            tool_config={"max_budget_usd": secret},
            effort=None,
        )
    module_name = CodexAdapter.__module__
    matching = [
        record
        for record in caplog.records
        if record.name == module_name and record.levelno == logging.WARNING and record.getMessage() == _BUDGET_MESSAGE
    ]
    assert len(matching) == 1
    assert matching[0].args == ()
    assert matching[0].exc_info is None
    for record in caplog.records:
        if record.name == module_name:
            assert secret not in record.getMessage()
            assert secret not in repr(vars(record))
