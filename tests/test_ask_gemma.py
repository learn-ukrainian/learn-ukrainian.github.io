"""Retired Gemma asks fail before message creation or provider access."""

from unittest.mock import patch

import pytest

from scripts.ai_agent_bridge._opencode import (
    ask_gemma,
)

# --- constant -------------------------------------------------------------


# --- invocation: json format, no variant (not a reasoning-variant model) ---


def test_retired_gemma_is_refused_before_message_or_provider_access():
    with patch("scripts.ai_agent_bridge._opencode.send_message") as send:
        with patch("scripts.ai_agent_bridge._opencode.subprocess.run") as run:
            with pytest.raises(ValueError, match="is retired in the model catalog"):
                ask_gemma("review this", task_id="t")
            send.assert_not_called()
            run.assert_not_called()


# --- model override (churn-resistance; tags drift per model-assignment.md) --


# --- NO egress guard (load-bearing: gemma is Western-hosted, unlike glm) ----


def test_retired_gemma_remains_refused_under_ci(monkeypatch):
    monkeypatch.setenv("CI", "true")
    with patch("scripts.ai_agent_bridge._opencode.send_message") as send:
        with pytest.raises(ValueError, match="is retired in the model catalog"):
            ask_gemma("audit this", task_id="t")
        send.assert_not_called()
