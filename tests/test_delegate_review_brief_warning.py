"""#10665: a review brief without a disposition section is dispatched with a typed warning."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def _section(relative: str, start: str, end: str) -> str:
    text = (Path(__file__).resolve().parents[1] / relative).read_text(encoding="utf-8")
    return text[text.index(start) : text.index(end)]


def _shared_review_texts() -> dict[str, str]:
    from scripts.ai_agent_bridge import _dispatch_wrappers as wrappers

    references = "agents_extensions/shared/skills/drive-epic/references"
    return {
        "review brief template": _section(
            f"{references}/review-merge-cleanup.md", "### Review brief template (#10665)", "## §7."
        ),
        "security brief": _section(
            f"{references}/routing-and-dispatch.md",
            "**Security-code briefs (#10665).**",
            "Write every brief so pytest basetemp",
        ),
        "ask verdict preamble": wrappers._REVIEW_VERDICT_OUTPUT,
        "review-deep instructions": wrappers.REVIEW_DEEP_INSTRUCTIONS,
    }


def test_shared_review_texts_state_the_rules():
    texts = _shared_review_texts()
    for disposition in ("in_scope_blocker", "follow_up", "stop_and_escalate"):
        assert disposition in texts["review brief template"]
        assert disposition in texts["review-deep instructions"]
    assert "inconclusive: give the BLOCKED token" in texts["ask verdict preamble"]
    assert "approval may carry tracked non-blocking follow-ups" in texts["ask verdict preamble"]
    assert "fail-closed" in texts["security brief"] and "a rejected review round" in texts["security brief"]
