"""Regression check: the routing guide carries no Claude-review-through-Cursor route.

Operator decision D-129 (#10464): no Claude model reviews through Cursor. The
catalog and resolver were already changed; this guards the human-facing guide
``fleet-driver-routing.md`` that ``model-assignment.md`` points to, so it cannot
keep instructing readers to use a route the resolver refuses.
"""

from __future__ import annotations

import re
from pathlib import Path

GUIDE = (
    Path(__file__).resolve().parents[1]
    / "agents_extensions"
    / "shared"
    / "rules"
    / "fleet-driver-routing.md"
)

_CURSOR_AGENT = re.compile(r"--agent\s+cursor\b")
_CLAUDE_MODEL = re.compile(r"\bclaude-[a-z0-9]")
_REVIEW_WORDS = re.compile(r"\b(review|reviews|reviewer|reviewers|cross-family|CF)\b", re.I)
_CLAUDE_POOL_ROW = re.compile(r"^\|\s*Claude (Sonnet|Opus|Fable)\b", re.I)
_NOT_REVIEW_ROUTE = "not a review route (D-129)"


def _lines() -> list[tuple[int, str]]:
    return list(enumerate(GUIDE.read_text(encoding="utf-8").splitlines(), start=1))


def test_no_cursor_agent_pairs_with_claude_model_in_review_context() -> None:
    offenders = [
        f"{number}: {line.strip()}"
        for number, line in _lines()
        if _CURSOR_AGENT.search(line)
        and _CLAUDE_MODEL.search(line)
        and _REVIEW_WORDS.search(line)
    ]
    assert not offenders, (
        "D-129: no Claude model reviews through Cursor; offending lines:\n"
        + "\n".join(offenders)
    )


def test_grok_author_review_does_not_name_an_other_models_slug() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    assert "Other Models slug" not in text


def test_other_models_pool_is_not_offered_for_review() -> None:
    offenders = [
        f"{number}: {line.strip()}"
        for number, line in _lines()
        if re.search(r"reviewer must be outside xAI", line, re.I)
        or re.search(r"cross-family review of a Grok author", line, re.I)
    ]
    assert not offenders, "Other Models pool must not be offered as a review route:\n" + "\n".join(
        offenders
    )


def test_claude_rows_of_the_other_models_pool_are_marked_not_a_review_route() -> None:
    rows = [(n, line) for n, line in _lines() if _CLAUDE_POOL_ROW.match(line)]
    assert rows, "expected Claude rows in the Other Models price table"
    unmarked = [f"{n}: {line.strip()}" for n, line in rows if _NOT_REVIEW_ROUTE not in line]
    assert not unmarked, f"Claude pool rows must say '{_NOT_REVIEW_ROUTE}':\n" + "\n".join(unmarked)


def test_guide_states_the_resolver_decides_review_of_a_grok_author() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    assert "D-129" in text
    assert re.search(r"reviewer resolver'?s? non-xAI pick", text)
