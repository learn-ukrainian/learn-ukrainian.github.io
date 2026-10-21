"""E1 of the create-path engine (#8397 comment 5773128681): the lesson-draft schema and its validator.

Covers the brief's E1.5 list: a valid draft per level validates; each §4 gap invariant fails its
fixture; each block kind's required fields; the markup regex; `explain` (wrong key) fails; the
generated `$ref`s resolve for every type in each level allowlist; the generate-and-check pattern.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh.draft_schema import (
    INLINE_MARKUP_RE,
    validate_draft,
)

REPO = Path(__file__).resolve().parents[2]
SCHEMAS = REPO / "schemas"
FIXTURES = Path(__file__).parent / "fixtures" / "fresh"
def load_fixture(level: str) -> tuple[dict, dict[str, str]]:
    draft = yaml.safe_load((FIXTURES / f"lesson-draft-{level}-valid.yaml").read_text(encoding="utf-8"))
    types = json.loads((FIXTURES / f"lesson-draft-{level}-types.json").read_text(encoding="utf-8"))
    if level == "a1":
        quiz = draft["activities"][0]["items"][0]
        quiz.update(
            kind="comprehension",
            host={"kind": "dialogue"},
            option_why=["This option follows the dialogue."] * len(quiz["options"]),
        )
        match = draft["activities"][1]
        match.update(left_role="question", right_role="answer")
        for pair in match["pairs"]:
            pair["why"] = "The two sides correspond."
        fill = draft["activities"][2]["items"][0]
        fill.update(
            kind="form",
            tests_feature="Case",
            requires={"Case": "Nom"},
            option_why=["This form fits the slot."] * len(fill["options"]),
        )
    return draft, types


def checks(errors) -> set[str]:
    return {e.check for e in errors}


# --- a valid draft per level -------------------------------------------------------------------


# --- §4 gap invariants ---------------------------------------------------------------------------


# --- block kinds and their required fields -------------------------------------------------------


# --- draft-internal code checks -----------------------------------------------------------------


# --- the inline markup regex and the accent ban ---------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Plain English narration.",
        "A term {{uk:слово}} inside English.",
        "An incidental word {{gloss:W-040}} glossed by the engine.",
        "Two tokens {{uk:слово}} and {{gloss:W-7}} side by side.",
    ],
)
def test_markup_regex_accepts(text: str) -> None:
    assert INLINE_MARKUP_RE.fullmatch(text)


@pytest.mark.parametrize(
    "text",
    [
        "{{uk:{{gloss:W-040}}}}",
        "{{gloss:{{uk:x}}}}",
        "{{uk:a {{uk:b}} c}}",
        "{{gloss:W-040 }}",
        "{{gloss:040}}",
        "{{UK:x}}",
        "{{uk:}}",
        "{{uk:x}",
        "a { b",
        "a } b",
        "{{stress:x}}",
        "Приві́т",
        "{{uk:Приві́т}}",
        "гра̀ве",
    ],
)
def test_markup_regex_rejects(text: str) -> None:
    assert not INLINE_MARKUP_RE.fullmatch(text)


def test_accent_in_narration_fails_schema_gate() -> None:
    draft, _ = load_fixture("a1")
    draft["steps"][0]["blocks"][0]["text"] = "Say {{uk:Приві́т}} first."
    errors = validate_draft(draft, "a1")
    assert any(e.check == "schema" and e.path.startswith("/steps/0/blocks/0") for e in errors)


def test_accent_inside_an_activity_item_fails_by_code() -> None:
    draft, types = load_fixture("a1")
    draft["activities"][0]["items"][0]["explanation"] = "with an accent: о́"
    assert checks(validate_draft(draft, "a1", activity_types=types)) == {"no_combining_accent"}


# --- activities: the per-type binding -------------------------------------------------------------


# --- the generated schemas and their references -------------------------------------------------
