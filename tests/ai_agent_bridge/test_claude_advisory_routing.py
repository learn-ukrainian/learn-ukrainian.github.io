from __future__ import annotations

import pytest

from scripts.ai_agent_bridge._claude import (
    CLAUDE_ADVISORY_MODEL,
    CLAUDE_DEFAULT_ASK_MODEL,
    resolve_claude_ask_model,
)


def test_advisory_defaults_to_opus() -> None:
    assert resolve_claude_ask_model("advisory", None) == CLAUDE_ADVISORY_MODEL


def test_advisory_rejects_sonnet_substitution() -> None:
    with pytest.raises(ValueError, match="Do not substitute Sonnet"):
        resolve_claude_ask_model("advisory", CLAUDE_DEFAULT_ASK_MODEL)


def test_ordinary_query_keeps_practical_default() -> None:
    assert resolve_claude_ask_model("query", None) == CLAUDE_DEFAULT_ASK_MODEL
