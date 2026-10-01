"""Tests for the review-checkable plan gates C1–C6 (issue #9487).

Each gate has a failing (or noted) fixture and a passing one, each built by a
single mutation of the mechanical gates' passing baseline: a letter-stage
module at arc position 2 (lessons 1 М А, 2 Н О and a recap) with a small
Cyrillic word store. Check 7 of #9487 (the learner-state fix) is tested in
tests/curriculum/learner_state/test_planned.py.

The Cyrillic strings are placeholders assembled from the fixture's letters;
they are fixture data for the gates' letter arithmetic, not claims about
Ukrainian.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate import codes
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.review_gates import ReviewGates
from scripts.curriculum.validate.validate import validate_plan
from tests.curriculum.test_plan_validate import LEVEL, NOT_CHECKED, PRIOR_SLUG, SLUG, prior_plan, write_world
from tests.curriculum.test_plan_validate_mechanical import (
    MAMA,
    MANA,
    NONA,
    ON,
    _drop_letters,
    mechanical_pack,
    mechanical_plan,
    mechanical_words,
)

pytestmark = pytest.mark.reads_content

REVIEW_GATE_CODES = {
    codes.NAMED_BEFORE_INTRODUCTION,
    codes.DUPLICATE_ACTIVITY_FOCUS,
    codes.LISTENING_QUIZ_SINGLE_KEY,
    codes.INCIDENTAL_NOT_DECODABLE,
    codes.INCIDENTAL_LEMMA_NOT_DECODABLE,
    codes.HEARD_WORD_WITHOUT_VIDEO,
    codes.EARLIER_CORE_NOT_RECYCLED,
}

# extra word ids for these fixtures
PRIOR_ONE, PRIOR_TWO, MANOK = "W-209", "W-210", "W-211"

Mutate = Callable[[dict, dict, dict, dict], None]  # plan, pack, words, prior plan


def _lesson(plan: dict, n: int) -> dict:
    return plan["lessons"][n - 1]


def _activity(plan: dict, n: int, activity_id: str) -> dict:
    return next(a for a in _lesson(plan, n)["activities"] if a["id"] == activity_id)


def _step(plan: dict, n: int, step_id: str) -> dict:
    return next(s for s in _lesson(plan, n)["steps"] if s["id"] == step_id)


def _focus(n: int, activity_id: str, focus: str) -> Mutate:
    return lambda plan, pack, words, prior: _activity(plan, n, activity_id).__setitem__("focus", focus)


def _dialogue(step: str, target_grammar: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, 1)["dialogue"] = {
            "step": step,
            "situation": "Two speakers meet.",
            "setting": "A room.",
            "speakers": [
                {"name": "Speaker One", "role": "host", "gender": "f", "evidence": MAMA},
                {"name": "Speaker Two", "role": "guest", "gender": "m", "evidence": MANA},
            ],
            "register": "informal",
            "target_grammar": target_grammar,
            "evidence": ["T-001"],
        }

    return mutate


def _videos(**models: tuple[list[str], list[str]] | None) -> Mutate:
    """Pack video records: V-id -> (letters, words) models, or None for a record without models."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        for video_id, model in models.items():
            record: dict = {"id": video_id.replace("_", "-")}
            if model is not None:
                record["models"] = {"letters": model[0], "words": model[1], "segment": None}
            pack["videos"].append(record)

    return mutate


def _incidental(n: int, word_id: str, lemma: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, n)["inventory"]["vocabulary"]["incidental"].append({"lemma": lemma, "evidence": word_id})

    return mutate


def _word(word_id: str, lemma: str, *forms: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        words["words"].append(
            {
                "id": word_id,
                "lemma": lemma,
                "pos": "noun",
                "forms": [{"form": form, "tags": "tag-a"} for form in (lemma, *forms)],
                "cefr": {"level": "A1"},
            }
        )

    return mutate


def _teach(n: int, step_id: str, teach: str, evidence: list[str] | None = None) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        step = _step(plan, n, step_id)
        step["teach"] = teach
        if evidence is not None:
            step["evidence"] = evidence

    return mutate


def _prior_core(plan: dict, pack: dict, words: dict, prior: dict) -> None:
    """Position 1 introduces two core records the module may recycle."""
    _word(PRIOR_ONE, "амо")(plan, pack, words, prior)
    _word(PRIOR_TWO, "ано")(plan, pack, words, prior)
    lesson = prior["lessons"][0]
    lesson["inventory"]["vocabulary"]["core"] = [
        {"lemma": "амо", "evidence": PRIOR_ONE, "forms": ["tag-a"]},
        {"lemma": "ано", "evidence": PRIOR_TWO, "forms": ["tag-a"]},
    ]
    lesson["steps"][0]["introduces"]["vocabulary"] += [PRIOR_ONE, PRIOR_TWO]


def _recycle(*word_ids: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        two = _lesson(plan, 2)
        two["inventory"]["vocabulary"]["recycled"] += list(word_ids)
        _step(plan, 2, "s1")["uses"]["vocabulary"] += list(word_ids)

    return mutate


def _all(*mutations: Mutate) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        for mutation in mutations:
            mutation(plan, pack, words, prior)

    return mutate


@dataclass(frozen=True)
class Case:
    name: str
    mutate: Mutate | None = None
    failures: frozenset[str] = frozenset()
    notes: frozenset[str] = frozenset()
    not_checked: frozenset[str] = frozenset()
    says: str = ""


LISTENING = "Required item kind: listening; each item binds host {kind: video, ref: V-id}."

CASES = [
    Case("baseline_passes"),
    # C1 -- a word named before its step introduces it
    Case(
        "c1_dialogue_target_grammar_names_a_word_a_later_step_introduces",
        _dialogue("s1", f"Whole {MAMA} chunk only."),
        failures=frozenset({codes.NAMED_BEFORE_INTRODUCTION}),
        says=f"names {MAMA} (introduced by step s2), which a later step of this lesson introduces",
    ),
    Case("c1_dialogue_at_the_introducing_step_passes", _dialogue("s2", f"Whole {MAMA} chunk only.")),
    Case(
        "c1_practice_focus_scores_a_word_a_later_step_introduces",
        _focus(1, "a1", f"Checks the letter М and the word {MAMA}."),
        failures=frozenset({codes.NAMED_BEFORE_INTRODUCTION}),
        says="activity a1 focus (practice of step s1) names W-201 (introduced by step s2)",
    ),
    Case(
        "c1_practice_focus_scores_a_word_no_lesson_introduced_yet",
        _focus(1, "a1", f"Checks the letter М and the word {NONA}."),
        failures=frozenset({codes.NAMED_BEFORE_INTRODUCTION}),
        says=f"names {NONA}, which no step up to s1 introduces",
    ),
    Case(
        "c1_practice_focus_scoring_an_introduced_or_earlier_word_passes",
        _all(
            _focus(1, "a2", f"Complete «мама» ({MAMA}) and «ман» with А."),
            _focus(2, "b1", f"Checks the letter Н next to {MAMA}."),
        ),
    ),
    Case(
        "c1_consolidation_focus_is_not_a_step_practice",
        _focus(1, "a4", f"Count syllables in «мама» and «ман» and {NONA}."),
    ),
    # C2 -- identical focus text within one lesson
    Case(
        "c2_two_activities_with_the_same_focus_fail",
        _focus(2, "b3", "Match «мама», «мана»  and «нона» to pictures;\n find О."),  # b2's, whitespace aside
        failures=frozenset({codes.DUPLICATE_ACTIVITY_FOCUS}),
        says="activities b2, b3 carry the same focus text",
    ),
    Case(
        "c2_the_same_focus_in_two_lessons_passes",
        _focus(1, "a4", "Checks the letter Н."),  # lesson 2's b1 focus, word for word
    ),
    # C3 -- a listening activity whose videos model one target
    Case(
        "c3_listening_quiz_on_one_single_letter_video_fails",
        _all(_videos(V_001=(["М"], [])), _focus(1, "a1", f"Checks the letter М from V-001. {LISTENING}")),
        failures=frozenset({codes.LISTENING_QUIZ_SINGLE_KEY}),
        says="cites V-001, which together model only letter М",
    ),
    Case(
        "c3_listening_quiz_on_two_targets_passes",
        _all(
            _videos(V_001=(["М"], []), V_002=(["А"], [])),
            _focus(1, "a1", f"Checks the letter М against А: V-001/T-001, V-002/T-001. {LISTENING}"),
        ),
    ),
    Case(
        "c3_listening_quiz_on_a_video_without_models_is_not_decided",
        _all(_videos(V_001=None), _focus(1, "a1", f"Checks the letter М from V-001. {LISTENING}")),
    ),
    Case(
        "c3_a_quiz_not_declared_listening_is_not_read",
        _all(_videos(V_001=(["М"], [])), _focus(1, "a1", "Checks the letter М after V-001.")),
    ),
    # C4 -- incidental words readable with the taught letters
    Case(
        "c4_incidental_with_no_readable_spelling_fails",
        _incidental(1, ON, "он"),
        failures=frozenset({codes.INCIDENTAL_NOT_DECODABLE}),
        says=f"incidental {ON} ('он') needs н, о, not taught through lesson 1",
    ),
    Case("c4_incidental_readable_once_its_letters_are_taught_passes", _incidental(2, ON, "он")),
    Case(
        "c4_lemma_unreadable_but_a_form_readable_is_a_note",
        _all(_word(MANOK, "манок", "мано"), _incidental(2, MANOK, "манок")),
        notes=frozenset({codes.INCIDENTAL_LEMMA_NOT_DECODABLE}),
        says="incidental lemma 'манок' (W-211) needs к, not taught through lesson 2; readable forms: мано",
    ),
    Case(
        "c4_non_letter_stage_module_is_not_checked_for_readability",
        _all(
            lambda plan, pack, words, prior: _drop_letters(plan, pack, words),
            _focus(1, "a1", "Checks the first sounds."),
            _focus(2, "b1", "Checks the next sounds."),
            _incidental(1, ON, "он"),
        ),
    ),
    # C5 -- a heard word with no video modelling it
    Case(
        "c5_heard_word_without_a_modelling_video_is_a_note",
        _teach(1, "s2", f"The letter А. Hear {MAMA} as a whole word."),
        notes=frozenset({codes.HEARD_WORD_WITHOUT_VIDEO}),
        says=f"the teach text says {MAMA} is heard, but no video the step cites (none)",
    ),
    Case(
        "c5_heard_word_with_a_modelling_video_passes",
        _all(
            _videos(V_003=([], [MAMA])),
            _teach(1, "s2", f"The letter А. Hear {MAMA} as a whole word.", ["T-001", "V-003"]),
        ),
    ),
    Case(
        "c5_a_word_read_in_another_clause_is_not_heard",
        _teach(1, "s2", f"Hear А from the primer, then read {MAMA}; listen again before reading {MANA}."),
    ),
    # C6 -- earlier positions' core records the module never recycles
    Case(
        "c6_earlier_core_not_recycled_is_listed",
        _all(_prior_core, _recycle(PRIOR_ONE)),
        notes=frozenset({codes.EARLIER_CORE_NOT_RECYCLED}),
        says=f"1 of 2 core records of earlier positions appear in no recycled list of this module: {PRIOR_TWO} 'ано' (position 1)",
    ),
    Case("c6_all_earlier_core_recycled_passes", _all(_prior_core, _recycle(PRIOR_ONE, PRIOR_TWO))),
]


def run(root: Path, mutate: Mutate | None) -> Report:
    plan, pack, words, prior = mechanical_plan(), mechanical_pack(), mechanical_words(), prior_plan()
    if mutate is not None:
        mutate(plan, pack, words, prior)
    world = write_world(root, plan, pack, words)
    (world.plan_path.parent / f"{PRIOR_SLUG}.yaml").write_text(
        yaml.safe_dump(prior, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    request = {"request_schema": 1, "level": LEVEL, "words": [{"lemma": "мам", "pos": "noun", "want": "new"}]}
    (world.words_path.parent / "_base.request.yaml").write_text(
        yaml.safe_dump(request, allow_unicode=True), encoding="utf-8"
    )
    return validate_plan(LEVEL, SLUG, plan_path=world.plan_path)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_case(tmp_path: Path, case: Case) -> None:
    report = run(tmp_path, case.mutate)
    text = report.render_text()
    assert {o.code for o in report.failures} == set(case.failures), text
    assert {o.code for o in report.notes} == set(case.notes), text
    assert {o.code for o in report.not_checked} == NOT_CHECKED | set(case.not_checked), text
    if case.says:
        assert any(case.says in o.message for o in report.failures + report.notes + report.not_checked), text


def test_outcomes_name_lesson_and_step(tmp_path: Path) -> None:
    report = run(tmp_path, next(c for c in CASES if c.name.startswith("c1_dialogue_target")).mutate)
    outcome = report.failures[0]
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.NAMED_BEFORE_INTRODUCTION, 1, "s1")


def test_unavailable_base_layer_skips_c1_instead_of_guessing(tmp_path: Path) -> None:
    plan, pack, words, prior = mechanical_plan(), mechanical_pack(), mechanical_words(), prior_plan()
    _focus(1, "a1", f"Checks the letter М and the word {NONA}.")(plan, pack, words, prior)
    world = write_world(tmp_path, plan, pack, words)  # no _base.request.yaml: the base layer is unknown
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert codes.NAMED_BEFORE_INTRODUCTION not in {o.code for o in report.failures}, report.render_text()
    gates = {o.message.split()[1] for o in report.not_checked if o.code == codes.MECHANICAL_RULE_NOT_CHECKED}
    assert "C1" in gates, report.render_text()


def test_c4_skips_a_lesson_before_the_first_taught_letter() -> None:
    plan = mechanical_plan()
    _lesson(plan, 1)["inventory"]["vocabulary"]["incidental"].append({"lemma": "он", "evidence": ON})
    store = type("Store", (), {"records": {}})()
    gates = ReviewGates(Report(LEVEL, SLUG), plan, LEVEL, store, None, None, Path("unused"), pack=None)  # type: ignore[arg-type]
    gates.__dict__["taught_through"] = {1: set(), 2: {"м", "а", "н", "о"}, 3: {"м", "а", "н", "о"}}
    gates.check_incidental_decodable()
    assert gates.report.failures == []


def produced_review_gate_codes(root: Path) -> set[str]:
    produced: set[str] = set()
    for index, case in enumerate(CASES):
        produced |= run(root / f"case-{index}", case.mutate).codes()
    return produced


def test_every_review_gate_code_is_produced(tmp_path: Path) -> None:
    assert produced_review_gate_codes(tmp_path) >= REVIEW_GATE_CODES
