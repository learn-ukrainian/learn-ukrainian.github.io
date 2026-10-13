"""Regression check for operator decision D-129 (#10464).

No Claude model reviews through Cursor. The catalog keeps Opus on the native
Claude CLI; these guides must not offer that review on a Cursor route. A unit
is one markdown table row, or one paragraph of consecutive non-blank lines
joined. The Claude model has to be the model of that ``--agent cursor``
invocation: a Grok ``--model grok-4.7-high`` review line stays valid when the
same paragraph also names Opus or another ``claude-`` id.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "agents_extensions" / "shared" / "rules" / "fleet-driver-routing.md"

_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
_CURSOR_AGENT = re.compile(r"--agent[=\s]+cursor\b", re.IGNORECASE)
_MODEL_AFTER_CURSOR = re.compile(
    r"--agent[=\s]+cursor\b"
    r"(?:(?:\s+--(?!model\b)[\w.-]+(?:[=\s]+\S+)?)*"
    r"\s+--model[=\s]+`?(?P<model>[^\s`]+))?",
    re.IGNORECASE,
)
_CLAUDE_MODEL = re.compile(r"\bclaude-[a-z0-9]", re.IGNORECASE)
_CLAUDE_MODEL_TOKEN = re.compile(r"^claude-[a-z0-9]", re.IGNORECASE)
_OPUS_OR_SONNET_TOKEN = re.compile(r"(?:opus|sonnet)", re.IGNORECASE)
_OPUS_OR_SONNET_WORD = re.compile(r"\b(?:Opus|Sonnet)\b")
_REVIEW_OR_ADVISOR = re.compile(r"\b(?:reviews?|reviewers?|advisors?|advisory)\b", re.IGNORECASE)
_NATIVE_CLAUDE_OR_CURSOR_SLUG = re.compile(
    r"native\s+Claude\s+or\s+verified\s+Cursor\s+slug",
    re.IGNORECASE,
)
_CURSOR_SLUG = re.compile(r"\bCursor\s+slug\b", re.IGNORECASE)
_CLAUDE_NAME = re.compile(r"\b(?:Claude|Opus|Sonnet)\b|\bclaude-[a-z0-9]", re.IGNORECASE)
_CLAUDE_POOL_ROW = re.compile(r"^\|\s*Claude (Sonnet|Opus|Fable)\b", re.IGNORECASE)
_NOT_REVIEW_ROUTE = "not a review route (D-129)"

_WRAPPED_REVIEW = "For a formal review, use\n`--agent cursor --model claude-sonnet-5-5-high`"
_EQUALS_FORM = "For a formal review, pass `--agent=cursor --model claude-opus-5-5`."
_EQUALS_NAMED_MODEL = "For a formal review, pass `--agent=cursor` with `claude-sonnet-5-5-high`."
_TABLE_SLUG = (
    "| **Claude Opus 5.5** | deep code review and hard advisory judgment "
    "| Anthropic / native Claude or verified Cursor slug |"
)
_GROK_REVIEW = "For code review, use `--agent cursor --model grok-4.7-high`."
_RESOLVER_PICK = "For cross-family review of a Grok author, use the resolver non-xAI pick."
_PROHIBITION = "No Claude model reviews through Cursor (D-129, #10464)."
_GROK_BESIDE_OPUS = (
    "Review admission: `claude-fable-5-1` holds no review role. "
    "Grok 4.7 reviews through Cursor `--agent cursor --model grok-4.7-high`. "
    "Route execution-dependent reviews to Opus 5.5."
)

POSITIVE_EXAMPLES = (_WRAPPED_REVIEW, _EQUALS_FORM, _EQUALS_NAMED_MODEL, _TABLE_SLUG)
NEGATIVE_EXAMPLES = (_GROK_REVIEW, _RESOLVER_PICK, _PROHIBITION, _GROK_BESIDE_OPUS)


def split_units(text: str) -> list[tuple[int, str]]:
    """Return ``(start_line, text)`` for each table row and joined paragraph."""
    units: list[tuple[int, str]] = []
    paragraph: list[str] = []
    start: int | None = None

    def flush() -> None:
        nonlocal start
        if start is not None and paragraph:
            units.append((start, " ".join(paragraph)))
        paragraph.clear()
        start = None

    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            flush()
            continue
        if _TABLE_ROW.match(line):
            flush()
            units.append((number, line.strip()))
            continue
        if start is None:
            start = number
        paragraph.append(line.strip())
    flush()
    return units


def _cursor_model_is_claude(model: str) -> bool:
    token = model.rstrip(".,;:")
    return bool(_CLAUDE_MODEL_TOKEN.search(token) or _OPUS_OR_SONNET_TOKEN.search(token))


def _command_offers_claude_review(unit: str) -> bool:
    if not _REVIEW_OR_ADVISOR.search(unit):
        return False
    for sentence in re.split(r"(?<=[.!?])\s+", unit):
        if not _CURSOR_AGENT.search(sentence):
            continue
        models = [item.group("model") for item in _MODEL_AFTER_CURSOR.finditer(sentence) if item.group("model")]
        if any(_cursor_model_is_claude(model) for model in models):
            return True
        # A named non-Claude model is the Grok pin, not an offer of Opus or Sonnet.
        if models:
            continue
        if _OPUS_OR_SONNET_WORD.search(sentence) or _CLAUDE_MODEL.search(sentence):
            return True
    return False


def _slug_offers_claude_review(unit: str) -> bool:
    if _NATIVE_CLAUDE_OR_CURSOR_SLUG.search(unit):
        return True
    return bool(_CURSOR_SLUG.search(unit) and _CLAUDE_NAME.search(unit) and _REVIEW_OR_ADVISOR.search(unit))


def offers_claude_review_through_cursor(unit: str) -> bool:
    return _command_offers_claude_review(unit) or _slug_offers_claude_review(unit)


def _guarded_files() -> list[Path]:
    rules = sorted((ROOT / "agents_extensions" / "shared" / "rules").glob("*.md"))
    references = sorted((ROOT / "agents_extensions" / "shared" / "skills" / "drive-epic" / "references").glob("*.md"))
    return [
        *rules,
        ROOT / "docs" / "best-practices" / "fleet-role-scorecard.md",
        ROOT / "docs" / "best-practices" / "agent-activity-matrix.md",
        *references,
    ]


def _offenders(text: str) -> list[tuple[int, str]]:
    return [(number, unit) for number, unit in split_units(text) if offers_claude_review_through_cursor(unit)]


@pytest.mark.parametrize("sample", POSITIVE_EXAMPLES)
def test_positive_examples_are_flagged(sample: str) -> None:
    assert _offenders(sample), sample


def test_wrapped_command_is_caught_only_as_one_paragraph() -> None:
    lines = _WRAPPED_REVIEW.splitlines()
    assert len(lines) == 2
    assert not any(offers_claude_review_through_cursor(line) for line in lines)
    units = split_units(_WRAPPED_REVIEW)
    assert len(units) == 1
    assert offers_claude_review_through_cursor(units[0][1])


def test_table_row_stays_separate_from_neighboring_paragraphs() -> None:
    text = f"{_RESOLVER_PICK}\n{_TABLE_SLUG}\n{_PROHIBITION}\n"
    units = [unit for _, unit in split_units(text)]
    assert units == [_RESOLVER_PICK, _TABLE_SLUG, _PROHIBITION]
    assert [offers_claude_review_through_cursor(unit) for unit in units] == [False, True, False]


@pytest.mark.parametrize("sample", NEGATIVE_EXAMPLES)
def test_negative_examples_pass(sample: str) -> None:
    assert not _offenders(sample), sample


def test_guarded_set_includes_the_named_documents() -> None:
    rels = {path.relative_to(ROOT).as_posix() for path in _guarded_files()}
    assert {
        "agents_extensions/shared/rules/fleet-driver-routing.md",
        "agents_extensions/shared/rules/model-assignment.md",
        "docs/best-practices/fleet-role-scorecard.md",
        "docs/best-practices/agent-activity-matrix.md",
        "agents_extensions/shared/skills/drive-epic/references/routing-and-dispatch.md",
    } <= rels
    assert all(path.is_file() for path in _guarded_files())


def test_guarded_docs_do_not_offer_claude_review_through_cursor() -> None:
    offenders = [
        f"{path.relative_to(ROOT)}:{number}: {unit[:240]}"
        for path in _guarded_files()
        for number, unit in _offenders(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, "D-129: no Claude model reviews through Cursor; offending units:\n" + "\n".join(offenders)


def test_grok_author_review_does_not_name_an_other_models_slug() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    assert "Other Models slug" not in text


def test_claude_rows_of_the_other_models_pool_are_marked_not_a_review_route() -> None:
    rows = [
        (number, line)
        for number, line in enumerate(GUIDE.read_text(encoding="utf-8").splitlines(), start=1)
        if _CLAUDE_POOL_ROW.match(line)
    ]
    assert rows, "expected Claude rows in the Other Models price table"
    unmarked = [f"{number}: {line.strip()}" for number, line in rows if _NOT_REVIEW_ROUTE not in line]
    assert not unmarked, f"Claude pool rows must say '{_NOT_REVIEW_ROUTE}':\n" + "\n".join(unmarked)


def test_guide_states_the_resolver_decides_review_of_a_grok_author() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    assert "D-129" in text
    assert re.search(r"reviewer resolver'?s? non-xAI pick", text)
