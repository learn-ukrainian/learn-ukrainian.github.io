"""Claude interactive defaults must preserve the reserved named-agent seats."""

from __future__ import annotations

import json
from pathlib import Path

SETTINGS = Path(__file__).resolve().parents[1] / "agents_extensions/shared/settings.json"


def test_interactive_model_and_advisor_are_explicit() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert settings["model"] == "claude-sonnet-5-5"
    assert settings["advisorModel"] == "claude-opus-5-5"


def test_interactive_default_does_not_select_an_opus_driver_agent() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert "agent" not in settings, "a pinned driver agent overrides the Sonnet default"


def test_global_subagent_model_and_force_override_stay_unset() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    env = settings.get("env", {})
    assert "CLAUDE_CODE_SUBAGENT_MODEL" not in env
    assert "CLAUDE_CODE_SUBAGENT_MODEL_FORCE" not in env


def test_advisor_is_enabled_by_default() -> None:
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    assert "CLAUDE_CODE_DISABLE_ADVISOR_TOOL" not in settings.get("env", {})
