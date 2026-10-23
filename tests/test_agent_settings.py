"""Claude interactive defaults must preserve the reserved named-agent seats."""

from __future__ import annotations

import json

import pytest

from scripts.agent_runtime.adapters.claude import _headless_worker_settings


@pytest.mark.parametrize("publish_guard", [False, True])
def test_headless_workers_omit_the_interactive_advisor(publish_guard: bool) -> None:
    settings = json.loads(_headless_worker_settings(publish_guard=publish_guard))
    assert "advisorModel" not in settings
    assert "model" not in settings, "worker models remain explicitly selected by the dispatch"
    assert "CLAUDE_CODE_DISABLE_ADVISOR_TOOL" not in settings.get("env", {})
