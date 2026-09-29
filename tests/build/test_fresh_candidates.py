"""Store form candidates for A1 choice items (#8889 A1-P5)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import candidates as candidate_source
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
        "sentence": "___",
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


def _assert_no_stress_leak(texts: list[str], records: list[dict]) -> None:
    pending_stressed = {
        form["stressed"]
        for record in records
        for form in record.get("forms", [])
        if form.get("stress_source") == "pending"
        and isinstance(form.get("stressed"), str)
        and any(mark in form["stressed"] for mark in ("\u0300", "\u0301"))
    }
    for text in texts:
        assert "\u0300" not in text and "\u0301" not in text
        assert all(stressed not in text for stressed in pending_stressed)


def test_noun_case_candidates_keep_all_analyses(words: dict) -> None:
    item = _item("W-101", "книгу", "noun:inanim:f:v_zna", "Case", {"Case": "Acc", "Number": "Sing"}, ["книгу", "книга"])
    offered = item_candidates(item, words, "fill-in")
    assert offered == item_candidates(item, words, "fill-in")
    assert _surfaces(offered) == ["книга", "книги", "книгу"]
    assert {candidate["form"]: candidate["admitted"] for candidate in offered} == {
        "книга": False,
        "книги": False,
        "книгу": True,
    }
    assert [analysis["admits_requires"] for analysis in offered[2]["analyses"]] == [True]
    assert [analysis["admits_requires"] for analysis in offered[1]["analyses"]] == [False, False]
    ambiguous = next(candidate for candidate in record_candidates(words["words"][0]) if candidate["form"] == "книги")
    assert len(ambiguous["analyses"]) == 2
    assert all(candidate["record"] == "W-101" for candidate in offered)
    _assert_no_stress_leak(_surfaces(offered), words["words"])


def test_verb_person_candidates_and_quiz_binding(words: dict) -> None:
    item = _item(
        "W-102", "читаю", "verb:imperf:pres:s:1", "Person", {"Person": "1", "Number": "Sing"}, ["читаю", "читаєш"]
    )
    offered = item_candidates(item, words, "fill-in")
    assert _surfaces(offered) == ["читаю", "читаєш"]
    _assert_no_stress_leak(_surfaces(offered), words["words"])
    quiz = {
        "kind": "form",
        "prompt": "___",
        "tests_feature": "Person",
        "requires": item["requires"],
        "correct": 1,
        "options": [{"text": "читаєш"}, {"text": "читаю"}],
        "option_records": ["W-102", "W-102"],
        "option_why": ["This form does not fit.", "This form fits."],
    }
    assert _surfaces(item_candidates(quiz, words, "quiz")) == _surfaces(offered)
    _assert_no_stress_leak(_surfaces(item_candidates(quiz, words, "quiz")), words["words"])
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
    assert _surfaces(aux) == ["буде", "будемо", "будеш", "буду"]
    assert "будемо" in _surfaces(aux)  # Number contradicts the slot although Person agrees.
    _assert_no_stress_leak(_surfaces(aux), words["words"])
    infinitive = _item("W-102", "читати", "verb:imperf:inf", "VerbForm", {"VerbForm": "Inf"}, ["читати", "читаю"])
    infinitive_candidates = item_candidates(infinitive, words, "fill-in")
    assert _surfaces(infinitive_candidates) == ["читав", "читати", "читаю", "читаєш"]
    _assert_no_stress_leak(_surfaces(infinitive_candidates), words["words"])
    words["words"][2]["forms"].append(_form("буду читати", "verb:imperf:futr:s:1"))
    assert "буду читати" not in _surfaces(record_candidates(words["words"][2]))
    assert _surfaces(item_candidates(auxiliary, words, "fill-in")) == _surfaces(aux)


def test_candidate_generator_uses_carried_required_group_and_rejects_undecidable() -> None:
    watch = make_word_record(
        201,
        "дивитися",
        pos="verb",
        forms=[_form("дивився", "verb:rev:imperf:past:m"), _form("дивилися", "verb:rev:imperf:past:p")],
    )
    give = make_word_record(
        202,
        "дати",
        pos="verb",
        forms=[
            _form("дай", "verb:perf:impr:s:2"),
            _form("дати", "verb:perf:inf"),
            _form("дайте", "verb:perf:impr:p:2"),
        ],
    )
    cost = make_word_record(
        203,
        "коштувати",
        pos="verb",
        forms=[_form("коштує", "verb:imperf:pres:s:3"), _form("коштувала", "verb:imperf:past:f")],
    )
    cases = [
        (
            watch,
            "дивився",
            "verb:rev:imperf:past:m",
            "Gender",
            {"Gender": "Masc", "Number": "Sing", "VerbForm": "Fin"},
            "дивилися",
            True,
        ),
        (
            give,
            "дай",
            "verb:perf:impr:s:2",
            "Number",
            {"Number": "Sing", "Person": "2", "VerbForm": "Fin"},
            "дати",
            True,
        ),
        (cost, "коштує", "verb:imperf:pres:s:3", "Person", {"Person": "3", "Number": "Sing"}, "коштувала", False),
    ]
    for record, answer, tags, group, requires, distractor, expected in cases:
        item = _item(record["id"], answer, tags, group, requires, [answer, distractor])
        offered = _surfaces(item_candidates(item, {"words": [record]}, "fill-in"))
        assert (distractor in offered) is expected
        assert answer in offered
        if expected:
            lesson = {"activities": [{"id": "a1", "type": "fill-in"}]}
            draft = {"lesson": {"module": "a1/fixture", "n": 1}, "activities": [{"id": "a1", "items": [item]}]}
            assert check_4_activities(draft, lesson, {"words": [record]}, {}, level="a1")[0]["status"] == "passed"


def test_composite_and_writer_option_outside_generated_candidates_fail(words: dict) -> None:
    item = _item("W-103", "буду", "verb:imperf:futr:s:1", "Person", {"Person": "1", "Number": "Sing"}, ["буду", "буде"])
    lesson = {"activities": [{"id": "a1", "type": "fill-in"}]}
    draft = {"lesson": {"module": "a1/fixture", "n": 1}, "activities": [{"id": "a1", "items": [item]}]}
    assert check_4_activities(draft, lesson, words, {}, level="a1")[0]["status"] == "passed"
    for outsider in ("буду читати", "бути"):
        item["options"] = ["буду", outsider]
        row, _ = check_4_activities(draft, lesson, words, {}, level="a1")
        assert row["status"] == "failed" and row["layer"] == "writer"
        assert row["reason"] == (
            "form_choice_options_invalid" if outsider == "буду читати" else "form_candidate_not_generated"
        )
        if outsider == "бути":
            assert row["code"] == "form_candidate_not_generated"
    item["options"] = ["буду", "буде"]


def test_determinism_and_real_a1_store_candidate() -> None:
    store = yaml.safe_load((ROOT / "curriculum/l2-uk-en/evidence/a1/_words.yaml").read_text(encoding="utf-8"))
    record = next(record for record in store["words"] if record["id"] == "W-001")
    first = record_candidates(record)
    assert first == record_candidates(record)
    assert all(candidate["record"] == "W-001" for candidate in first)
    _assert_no_stress_leak(_surfaces(first), [record])


def test_pending_stress_guard_catches_stressed_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    store = yaml.safe_load((ROOT / "curriculum/l2-uk-en/evidence/a1/_words.yaml").read_text(encoding="utf-8"))
    record = next(record for record in store["words"] if record["id"] == "W-001")
    form = next(form for form in record["forms"] if form.get("stressed") == "мені\u0301")
    form["stress_source"] = "pending"
    monkeypatch.setattr(candidate_source, "record_candidates", lambda _: [{"form": form["stressed"]}])
    with pytest.raises(AssertionError):
        _assert_no_stress_leak(_surfaces(candidate_source.record_candidates(record)), [record])


def test_rendered_prompt_includes_store_candidate_bank(words: dict) -> None:
    record = words["words"][1]
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
                "core": [{"evidence": "W-102", "lemma": record["lemma"], "forms": []}],
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
        {"W-102": record},
        state,
        compute_immersion_payload("a1", arc_position=1, lesson_n=1, cumulative_core_count=0),
        level="a1",
        slug="fixture",
        lesson_n=1,
    )
    bank = prompt.split("## Form-choice candidate bank", 1)[1]
    assert "`W-102`: `читати`" in bank
    assert "VerbForm=Inf" in bank
    rule = "Each distractor must be a form that the sentence rules out by a feature the form itself carries."
    assert rule in prompt
    assert (
        "`tests_feature` names one focus group; the reviewer judges whether the distractors really make the learner choose along that focus."
        in prompt
    )
    assert "A finite verb slot names `VerbForm: Fin` in `requires`; a plural slot omits `Gender`" in prompt
    _assert_no_stress_leak([bank], [record])
    assert check_rendered_prompt(prompt, plan, ROOT / "docs/style-cards/a1.md").passed
    pending_bank = _render_form_candidates(plan, {"W-102": words["words"][1]})
    assert "`W-102`: `читати`" in pending_bank
    _assert_no_stress_leak([pending_bank], [words["words"][1]])


@pytest.mark.parametrize("level", ["a2", "b1", "b2"])
def test_non_a1_candidate_bank_keeps_main_wording(words: dict, level: str) -> None:
    plan = {"activities": [{"type": "quiz"}]}
    bank = _render_form_candidates(plan, {"W-102": words["words"][1]}, level=level)
    assert (
        "Use one form from its bound record per option. State the complete slot `requires`; "
        "choose one admitted key and distractors that differ in `tests_feature`. "
        "The engine generates the item-specific subset and checks every written option."
    ) in bank
    assert "partitive genitive" not in bank
