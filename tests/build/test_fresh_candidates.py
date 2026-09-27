"""Store form candidates for A1 choice items (#8889 A1-P5)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.build.fresh.candidates import item_candidates, record_candidates
from scripts.build.fresh.immersion import compute_immersion_payload
from scripts.build.fresh.prompt import _render_form_candidates, check_rendered_prompt, render_lesson_prompt
from scripts.build.fresh.runner import check_4_activities
from tests.build.test_fresh_assemble import make_word_record, make_words_store

pytestmark = pytest.mark.reads_content
ROOT = Path(__file__).resolve().parents[2]


def _form(text: str, tags: str) -> dict:
    # Forms and tags below were checked with sources.inspect_words (VESUM).
    return {"form": text, "tags": tags, "stress_source": "pending", "markers": [], "learner": True}


@pytest.fixture
def words() -> dict:
    noun = make_word_record(
        101,
        "книга",
        forms=[
            _form("книга", "noun:inanim:f:v_naz"),
            _form("книгу", "noun:inanim:f:v_zna"),
            _form("книги", "noun:inanim:f:v_rod"),
            _form("книги", "noun:inanim:p:v_zna"),
        ],
    )
    verb = make_word_record(
        102,
        "читати",
        pos="verb",
        forms=[
            _form("читати", "verb:imperf:inf"),
            _form("читаю", "verb:imperf:pres:s:1"),
            _form("читаєш", "verb:imperf:pres:s:2"),
            _form("читав", "verb:imperf:past:m"),
        ],
    )
    auxiliary = make_word_record(
        103,
        "бути",
        pos="verb",
        forms=[
            _form("бути", "verb:imperf:inf"),
            _form("буду", "verb:imperf:futr:s:1"),
            _form("буде", "verb:imperf:futr:s:3"),
            _form("будеш", "verb:imperf:futr:s:2"),
            _form("будемо", "verb:imperf:futr:p:1"),
        ],
    )
    return make_words_store(words=[noun, verb, auxiliary])


def _item(record: str, answer: str, tags: str, feature: str, requires: dict[str, str], options: list[str]) -> dict:
    return {
        "mode": "form-choice",
        "kind": "form",
        "record": record,
        "answer": answer,
        "answer_tags": tags,
        "tests_feature": feature,
        "requires": requires,
        "options": options,
        "option_why": ["The form fits this slot."] * len(options),
    }


def _surfaces(candidates: list[dict]) -> list[str]:
    return [candidate["form"] for candidate in candidates]


def test_noun_case_candidates_keep_all_analyses(words: dict) -> None:
    item = _item("W-101", "книгу", "noun:inanim:f:v_zna", "Case", {"Case": "Acc", "Number": "Sing"}, ["книгу", "книга"])
    offered = item_candidates(item, words, "fill-in")
    assert offered == item_candidates(item, words, "fill-in")
    assert _surfaces(offered) == ["книга", "книгу"]
    assert {candidate["form"]: candidate["admitted"] for candidate in offered} == {"книга": False, "книгу": True}
    assert [analysis["admits_requires"] for analysis in offered[1]["analyses"]] == [True]
    assert "книги" not in _surfaces(offered)  # An accusative plural analysis shares the taught case.
    ambiguous = next(candidate for candidate in record_candidates(words["words"][0]) if candidate["form"] == "книги")
    assert len(ambiguous["analyses"]) == 2
    assert all(candidate["record"] == "W-101" for candidate in offered)


def test_verb_person_candidates_and_quiz_binding(words: dict) -> None:
    item = _item(
        "W-102", "читаю", "verb:imperf:pres:s:1", "Person", {"Person": "1", "Number": "Sing"}, ["читаю", "читаєш"]
    )
    offered = item_candidates(item, words, "fill-in")
    assert _surfaces(offered) == ["читаю", "читаєш"]
    quiz = {
        "kind": "form",
        "tests_feature": "Person",
        "requires": item["requires"],
        "correct": 1,
        "options": [{"text": "читаєш"}, {"text": "читаю"}],
        "option_records": ["W-102", "W-102"],
        "option_why": ["This form does not fit.", "This form fits."],
    }
    assert _surfaces(item_candidates(quiz, words, "quiz")) == _surfaces(offered)
    lesson = {"activities": [{"id": "a1", "type": "quiz"}]}
    draft = {"lesson": {"module": "a1/fixture", "n": 1}, "activities": [{"id": "a1", "items": [quiz]}]}
    assert check_4_activities(draft, lesson, words, {}, level="a1")[0]["status"] == "passed"
    quiz["option_records"][0] = "W-101"
    row, _ = check_4_activities(draft, lesson, words, {}, level="a1")
    assert (row["code"], row["layer"]) == ("form_candidate_not_generated", "writer")


def test_analytic_future_uses_single_auxiliary_or_infinitive_forms(words: dict) -> None:
    auxiliary = _item(
        "W-103", "буду", "verb:imperf:futr:s:1", "Person", {"Person": "1", "Number": "Sing"}, ["буду", "буде"]
    )
    aux = item_candidates(auxiliary, words, "fill-in")
    assert _surfaces(aux) == ["буде", "будеш", "буду"]
    assert "будемо" not in _surfaces(aux)  # Same taught person as the key.
    infinitive = _item("W-102", "читати", "verb:imperf:inf", "VerbForm", {"VerbForm": "Inf"}, ["читати", "читаю"])
    assert _surfaces(item_candidates(infinitive, words, "fill-in")) == ["читав", "читати", "читаю", "читаєш"]
    assert all("стressed" not in candidate for candidate in aux)
    words["words"][2]["forms"].append(_form("буду читати", "verb:imperf:futr:s:1"))
    assert "буду читати" not in _surfaces(record_candidates(words["words"][2]))
    assert _surfaces(item_candidates(auxiliary, words, "fill-in")) == _surfaces(aux)


def test_composite_and_writer_option_outside_generated_candidates_fail(words: dict) -> None:
    item = _item("W-103", "буду", "verb:imperf:futr:s:1", "Person", {"Person": "1", "Number": "Sing"}, ["буду", "буде"])
    lesson = {"activities": [{"id": "a1", "type": "fill-in"}]}
    draft = {"lesson": {"module": "a1/fixture", "n": 1}, "activities": [{"id": "a1", "items": [item]}]}
    assert check_4_activities(draft, lesson, words, {}, level="a1")[0]["status"] == "passed"
    for outsider in ("буду читати", "будемо"):
        item["options"] = ["буду", outsider]
        row, _ = check_4_activities(draft, lesson, words, {}, level="a1")
        assert row["status"] == "failed" and row["layer"] == "writer"
        assert row["reason"] == (
            "form_choice_options_invalid" if outsider == "буду читати" else "form_candidate_not_generated"
        )
        if outsider == "будемо":
            assert row["code"] == "form_candidate_not_generated"
    item["options"] = ["буду", "буде"]


def test_determinism_and_real_a1_store_candidate() -> None:
    store = yaml.safe_load((ROOT / "curriculum/l2-uk-en/evidence/a1/_words.yaml").read_text(encoding="utf-8"))
    record = next(record for record in store["words"] if record["id"] == "W-001")
    first = record_candidates(record)
    assert first == record_candidates(record)
    assert all(candidate["record"] == "W-001" for candidate in first)
    assert all("stressed" not in candidate for candidate in first)


def test_rendered_prompt_includes_store_candidate_bank(words: dict) -> None:
    store = yaml.safe_load((ROOT / "curriculum/l2-uk-en/evidence/a1/_words.yaml").read_text(encoding="utf-8"))
    record = next(record for record in store["words"] if record["id"] == "W-001")
    plan = {
        "slug": "fixture",
        "title": "Fixture",
        "kind": "teach",
        "job": "Practice",
        "rationale": "Practice",
        "word_target": 1,
        "lesson": {"module": "a1/fixture", "n": 1},
        "steps": [],
        "consolidation": [],
        "activities": [{"id": "a1", "type": "fill-in", "placement": "inline", "focus": "Form"}],
        "inventory": {
            "vocabulary": {
                "core": [{"evidence": "W-001", "lemma": record["lemma"], "forms": []}],
                "incidental": [],
                "recycled": [],
            },
            "grammar": [],
            "phonetics": {"letters": []},
        },
    }
    state = {
        "level": "a1",
        "position": 1,
        "lesson_n": 1,
        "cumulative_core_count": 0,
        "base_ids": [],
        "core_ids": {},
        "name_ids": {},
        "grammar_ids": {},
        "letters": {},
    }
    prompt = render_lesson_prompt(
        plan,
        {"W-001": record},
        state,
        compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0),
        level="a1",
        slug="fixture",
        lesson_n=1,
    )
    bank = prompt.split("## Form-choice candidate bank", 1)[1]
    assert "`W-001`: `я`" in bank
    assert "Case=Nom" in bank
    assert "стressed" not in bank
    assert check_rendered_prompt(prompt, plan, ROOT / "docs/style-cards/a1.md").passed
    pending_bank = _render_form_candidates(plan, {"W-102": words["words"][1]})
    assert "`W-102`: `читати`" in pending_bank and "stressed" not in pending_bank
