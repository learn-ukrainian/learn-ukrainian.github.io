"""Tests for the mechanical plan gates M1–M8 (issue #9138).

One passing baseline and, per gate, at least one failing fixture built by a
single mutation of that baseline. The fixture world is a letter-stage module at
arc position 2 (its arc letters are derived from the plan, as in
test_plan_validate.py) with a small Cyrillic word store.

The Cyrillic strings below are placeholders assembled from the fixture's own
letters (М А Н О К); they are fixture data for the gates' letter and token
arithmetic, not claims about Ukrainian. No test here judges a Ukrainian fact —
every letter set, syllable count and CEFR level the gates use comes from the
fixture store, arc and plan.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate import codes
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.validate import validate_plan
from tests.curriculum.test_plan_validate import (
    LEVEL,
    NOT_CHECKED,
    SLUG,
    World,
    base_plan,
    write_world,
)

pytestmark = pytest.mark.reads_content

# word ids of the fixture store
MAMA, MANA, NONA, MAN, BASE_WORD, MOKA, MA, ON = (
    "W-201",
    "W-202",
    "W-203",
    "W-204",
    "W-205",
    "W-206",
    "W-207",
    "W-208",
)

MECHANICAL_CODES = {
    codes.STEP_LETTER_NOT_PRACTISED,
    codes.STEP_LETTER_NO_WORD_RECORD,
    codes.TOKEN_NOT_ALLOWED,
    codes.CORE_CEFR_ABOVE_MODULE,
    codes.CORE_WORD_NOT_REUSED,
    codes.GRAMMAR_NOT_REUSED,
    codes.COPY_MODEL_LETTER_NOT_TAUGHT,
    codes.TOKEN_UNRESOLVED,
    codes.MECHANICAL_RULE_NOT_CHECKED,
}


def _step(step_id: str, kind: str, teach: str, introduces: dict, uses: dict, practice: list[str]) -> dict:
    return {
        "id": step_id,
        "kind": kind,
        "teach": teach,
        "introduces": {"letters": [], "grammar": [], "vocabulary": [], **introduces},
        "uses": {"grammar": [], "vocabulary": [], **uses},
        "evidence": ["T-001"],
        "practice": practice,
    }


def _activity(activity_id: str, kind: str, placement: str, focus: str, **extra: object) -> dict:
    return {"id": activity_id, "type": kind, "placement": placement, "focus": focus, **extra}


def _core(word_id: str, lemma: str) -> dict:
    return {"lemma": lemma, "evidence": word_id, "forms": ["tag-a"]}


def _lesson(n: int, kind: str, letters: list[str], core: list[tuple[str, str]], recycled: list[str]) -> dict:
    inventory: dict = {
        "grammar": [],
        "vocabulary": {"core": [_core(i, lemma) for i, lemma in core], "incidental": [], "recycled": recycled},
    }
    if letters:
        inventory["phonetics"] = {"letters": letters, "sounds": []}
    return {
        "n": n,
        "slug": f"lesson-{n}",
        "title": f"Lesson {n}",
        "kind": kind,
        "job": f"Learner can do thing {n}.",
        "rationale": "Why here.",
        "word_target": 10,
        "inventory": inventory,
        "steps": [],
        "activities": [],
    }


def mechanical_plan() -> dict:
    """A letter-stage plan that passes every gate: lessons 1 (М А), 2 (Н О) and a recap."""
    plan = base_plan()
    one = _lesson(1, "teach", ["М", "А"], [(MAMA, "мама"), (MANA, "мана"), (MAN, "ман")], [])
    one["steps"] = [
        _step("s1", "teach", "The letter М.", {"letters": ["М"]}, {}, ["a1"]),
        _step("s2", "teach", "The letter А.", {"letters": ["А"], "vocabulary": [MAMA, MANA, MAN]}, {}, ["a2", "a3"]),
    ]
    one["consolidation"] = ["a4"]
    one["activities"] = [
        _activity("a1", "quiz", "inline", "Checks the letter М."),
        _activity("a2", "pick-syllables", "inline", "Complete мама and ман with А.", model="X-001"),
        _activity("a3", "letter-grid", "inline", "Copy мама into a notebook.", model="X-001"),
        _activity("a4", "count-syllables", "workbook", "Count syllables in мама and ман."),
    ]
    one["practice"] = {"vocabulary": "core", "stress": [], "patterns": ["a1"]}

    two = _lesson(2, "teach", ["Н", "О"], [(NONA, "нона")], [MAMA, MANA, MAN])
    two["inventory"]["vocabulary"]["incidental"] = [{"lemma": "мока", "evidence": MOKA}]
    two["steps"] = [
        _step("s1", "teach", "The letter Н.", {"letters": ["Н"]}, {}, ["b1"]),
        _step(
            "s2",
            "teach",
            "The letter О.",
            {"letters": ["О"], "vocabulary": [NONA]},
            {"vocabulary": [MAMA, MANA, MAN]},
            ["b2", "b3"],
        ),
    ]
    two["consolidation"] = ["b3"]
    two["activities"] = [
        _activity("b1", "quiz", "inline", "Checks the letter Н."),
        _activity("b2", "match-up", "inline", "Match мама, мана and нона to pictures; find О."),
        _activity("b3", "pick-syllables", "workbook", "Complete мама, мана and нона from syllables."),
    ]
    two["practice"] = {"vocabulary": "core", "stress": [], "patterns": ["b2"]}

    recap = _lesson(3, "recap", [], [], [MAMA, MANA, MAN, NONA])
    recap["steps"] = [_step("s1", "practice", "Review.", {}, {"vocabulary": [MAMA, MANA, MAN, NONA]}, ["c1"])]
    recap["steps"][0].pop("teach")
    recap["activities"] = [_activity("c1", "quiz", "inline", "Review quiz.")]
    plan["lessons"] = [one, two, recap]
    return plan


def mechanical_pack() -> dict:
    return {
        "evidence_schema": 1,
        "module": f"{LEVEL}/{SLUG}",
        "texts": [{"id": "T-001"}],
        "exercises": [{"id": "X-001", "quote": "мама", "items_sample": ["мама"]}],
        "examples": [],
        "errors": [],
        "videos": [],
        "standard": [],
    }


def mechanical_words() -> dict:
    def record(word_id: str, lemma: str, cefr: str | None = "A1") -> dict:
        entry: dict = {
            "id": word_id,
            "lemma": lemma,
            "pos": "noun",
            "forms": [{"form": lemma, "tags": "tag-a"}],
        }
        if cefr is not None:
            entry["cefr"] = {"level": cefr}
        return entry

    return {
        "words": [
            record(MAMA, "мама"),
            record(MANA, "мана"),
            record(NONA, "нона"),
            record(MAN, "ман"),
            record(BASE_WORD, "мам"),
            record(MOKA, "мока"),
            record(MA, "ма"),
            record(ON, "он"),
        ]
    }


Mutate = Callable[[dict, dict, dict], None]


def _lesson_of(plan: dict, n: int) -> dict:
    return plan["lessons"][n - 1]


def _activity_of(plan: dict, n: int, activity_id: str) -> dict:
    return next(a for a in _lesson_of(plan, n)["activities"] if a["id"] == activity_id)


def _step_of(plan: dict, n: int, step_id: str) -> dict:
    return next(s for s in _lesson_of(plan, n)["steps"] if s["id"] == step_id)


def _set_focus(n: int, activity_id: str, focus: str) -> Mutate:
    return lambda plan, pack, words: _activity_of(plan, n, activity_id).__setitem__("focus", focus)


def _set_cefr(word_id: str, cefr: str | None) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict) -> None:
        record = next(w for w in words["words"] if w["id"] == word_id)
        if cefr is None:
            del record["cefr"]
        else:
            record["cefr"]["level"] = cefr

    return mutate


def _m2_letter_without_word(plan: dict, pack: dict, words: dict) -> None:
    """Lesson 1 also introduces К through a pick-syllables activity; no allowed record contains К."""
    lesson = _lesson_of(plan, 1)
    lesson["inventory"]["phonetics"]["letters"].append("К")
    _step_of(plan, 1, "s1")["introduces"]["letters"].append("К")
    _activity_of(plan, 1, "a1").update({"type": "pick-syllables", "focus": "Checks the letters М and К."})


def _without_item_activities(plan: dict, pack: dict, words: dict) -> None:
    """Every match-up, workbook word activity and count-syllables becomes a quiz: no item set to check."""
    for lesson in plan["lessons"]:
        for activity in lesson["activities"]:
            if activity["type"] in ("match-up", "count-syllables") or activity["placement"] == "workbook":
                activity["type"] = "quiz"


def _m8_word_not_reused(plan: dict, pack: dict, words: dict) -> None:
    _lesson_of(plan, 2)["inventory"]["vocabulary"]["recycled"].remove(MAN)
    _lesson_of(plan, 3)["inventory"]["vocabulary"]["recycled"].remove(MAN)
    for lesson_n in (2, 3):
        uses = _lesson_of(plan, lesson_n)["steps"][-1]["uses"]["vocabulary"]
        uses.remove(MAN)


def _m8_grammar_not_reused(plan: dict, pack: dict, words: dict) -> None:
    lesson = _lesson_of(plan, 1)
    lesson["inventory"]["grammar"] = [{"id": "G-a1-001", "point": "A first point.", "evidence": ["T-001"]}]
    _step_of(plan, 1, "s2")["introduces"]["grammar"] = ["G-a1-001"]


def _drop_letters(plan: dict, pack: dict, words: dict) -> None:
    """Make the module non-literacy: no letters anywhere (the arc derived from the plan has none)."""
    for lesson in plan["lessons"]:
        lesson["inventory"].pop("phonetics", None)
        for step in lesson["steps"]:
            step["introduces"]["letters"] = []


@dataclass(frozen=True)
class Case:
    name: str
    mutate: Mutate | None = None
    failures: frozenset[str] = frozenset()
    notes: frozenset[str] = frozenset()
    not_checked: frozenset[str] = frozenset()
    #: Whether the plan keeps match-up, workbook word or count-syllables activities, whose item sets
    #: gates M6 and M7 report as not checked.
    item_sets: bool = True
    #: A fragment every failure of the expected codes must carry in its message (location or value).
    says: str = ""


CASES = [
    Case("baseline_passes_every_failing_gate"),
    # M1 -- a step introduces a letter that no practice focus names
    Case(
        "m1_letter_not_named_in_practice_focus",
        _set_focus(1, "a2", "Complete мама and ман."),
        failures=frozenset({codes.STEP_LETTER_NOT_PRACTISED}),
        says="step s2 introduces the letter А",
    ),
    # M2 -- a letter with a word-completion practice and no allowed word record containing it
    Case(
        "m2_letter_without_a_word_record",
        _m2_letter_without_word,
        failures=frozenset({codes.STEP_LETTER_NO_WORD_RECORD}),
        says="no allowed word record of lesson 1 contains К",
    ),
    # M3 -- quoted tokens against the lesson's allowed set
    Case(
        "m3_focus_token_outside_the_lesson_is_a_note",
        _set_focus(1, "a2", "Complete мама and нона with А."),
        notes=frozenset({codes.TOKEN_NOT_ALLOWED}),
        says="activity a2 focus quotes 'нона'",
    ),
    Case(
        "m3_teach_token_outside_the_lesson_is_a_note",
        lambda plan, pack, words: _step_of(plan, 1, "s1").__setitem__("teach", "The letter М in нона."),
        notes=frozenset({codes.TOKEN_NOT_ALLOWED}),
        says="step s1 teach text quotes 'нона'",
    ),
    Case(
        "m3_base_layer_token_is_allowed",
        _set_focus(1, "a2", "Complete мама and мам with А."),
    ),
    Case(
        "m3_token_without_a_record_is_not_checked",
        _set_focus(1, "a2", "Complete мама and кум with А."),
        not_checked=frozenset({codes.TOKEN_UNRESOLVED}),
    ),
    # a syllable of the taught letters that spells an out-of-allowlist word (ма, W-207) is not that word
    Case(
        "m3_syllable_colliding_with_a_word_record_is_not_a_violation",
        _set_focus(1, "a2", "Complete мама and the syllable ма with А."),
        not_checked=frozenset({codes.TOKEN_UNRESOLVED}),
        says="'ма', spelled with letters lesson 1 has taught",
    ),
    Case(
        "m3_syllable_shaped_token_with_an_untaught_letter_is_a_note",
        _set_focus(1, "a2", "Complete мама and the syllable он with А."),
        notes=frozenset({codes.TOKEN_NOT_ALLOWED}),
        says="activity a2 focus quotes 'он'",
    ),
    # M4 -- a copy task's model text uses letters not yet taught
    Case(
        "m4_copy_model_text_uses_untaught_letters_is_a_note",
        lambda plan, pack, words: pack["exercises"][0].__setitem__("quote", "мама кома"),
        notes=frozenset({codes.COPY_MODEL_LETTER_NOT_TAUGHT}),
    ),
    Case(
        "m4_untaught_letters_in_copy_focus_prose_are_not_read",
        _set_focus(1, "a3", "Copy кома into a notebook."),
        not_checked=frozenset({codes.TOKEN_UNRESOLVED}),  # кома is a placeholder no store record lists
    ),
    Case(
        "m4_copy_task_without_a_model_is_not_checked",
        lambda plan, pack, words: _activity_of(plan, 1, "a3").pop("model"),
        says="gate M4 was not checked: copy task(s) a3 (lesson 1) name no readable model exercise",
    ),
    # M5 -- a core lemma above the module's level
    Case(
        "m5_core_lemma_two_bands_above_is_a_note",
        _set_cefr(MAMA, "B1"),
        notes=frozenset({codes.CORE_CEFR_ABOVE_MODULE}),
        says="'мама' (W-201) is B1 in the word store, 2 bands above",
    ),
    Case(
        "m5_core_lemma_one_band_above_is_a_note",
        _set_cefr(MAMA, "A2"),
        notes=frozenset({codes.CORE_CEFR_ABOVE_MODULE}),
        says="1 band above",
    ),
    Case(
        "m5_core_lemma_without_cefr_is_not_checked",
        _set_cefr(MAMA, None),
        says="gate M5 was not checked: core word records carry no CEFR level: W-201",
    ),
    # M6 -- item counts: the plan binds no item set
    Case(
        "m6_match_up_and_workbook_word_activities_are_not_checked",
        says="gate M6 was not checked: the plan binds no item set for b2 (match-up, lesson 2), b3 (pick-syllables, lesson 2)",
    ),
    Case(
        "m6_words_named_in_the_focus_are_not_counted_as_items",
        _set_focus(2, "b2", "Match мама and нона to pictures; find О."),
        says="gate M6 was not checked",
    ),
    Case("m6_m7_without_item_activities_report_nothing", _without_item_activities, item_sets=False),
    # M7 -- one distinct syllable count: the plan binds no item set
    Case(
        "m7_count_syllables_is_not_checked",
        says="gate M7 was not checked: the plan binds no item set for a4 (count-syllables, lesson 1)",
    ),
    Case(
        "m7_words_named_in_the_focus_are_not_counted_as_items",
        _set_focus(1, "a4", "Count syllables in мама and мана."),
        says="gate M7 was not checked",
    ),
    # M8 -- introduced and never reused
    Case(
        "m8_core_word_never_reused_is_a_note",
        _m8_word_not_reused,
        notes=frozenset({codes.CORE_WORD_NOT_REUSED}),
        says="core word W-204 ('ман') is never used or recycled by lessons 2–3",
    ),
    Case(
        "m8_grammar_never_reused_is_a_note",
        _m8_grammar_not_reused,
        notes=frozenset({codes.GRAMMAR_NOT_REUSED}),
        says="grammar G-a1-001 is never used by lessons 2–3",
    ),
    # letter gates apply to letter-stage modules only
    Case(
        "non_letter_stage_skips_the_letter_gates",
        lambda plan, pack, words: (
            _drop_letters(plan, pack, words),
            _set_focus(1, "a3", "Copy кома into a notebook.")(plan, pack, words),
        ),
        not_checked=frozenset({codes.TOKEN_UNRESOLVED}),
    ),
]


def run(root: Path, mutate: Mutate | None) -> tuple[Report, World]:
    plan, pack, words = mechanical_plan(), mechanical_pack(), mechanical_words()
    if mutate is not None:
        mutate(plan, pack, words)
    world = write_world(root, plan, pack, words)
    request = {"request_schema": 1, "level": LEVEL, "words": [{"lemma": "мам", "pos": "noun", "want": "new"}]}
    (world.words_path.parent / "_base.request.yaml").write_text(
        yaml.safe_dump(request, allow_unicode=True), encoding="utf-8"
    )
    return validate_plan(LEVEL, SLUG, plan_path=world.plan_path), world


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_case(tmp_path: Path, case: Case) -> None:
    report, _world = run(tmp_path, case.mutate)
    text = report.render_text()
    assert {o.code for o in report.failures} == set(case.failures), text
    assert {o.code for o in report.notes} == set(case.notes), text
    item_sets = {codes.MECHANICAL_RULE_NOT_CHECKED} if case.item_sets else set()
    assert {o.code for o in report.not_checked} == NOT_CHECKED | item_sets | set(case.not_checked), text
    assert report.ok == (not case.failures)
    if case.says:
        assert any(case.says in o.message for o in report.failures + report.notes + report.not_checked), text


def test_outcomes_name_lesson_and_step(tmp_path: Path) -> None:
    report, _world = run(tmp_path, CASES[1].mutate)
    outcome = report.failures[0]
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.STEP_LETTER_NOT_PRACTISED, 1, "s2")
    report, _world = run(tmp_path / "teach", next(c for c in CASES if c.name.startswith("m3_teach")).mutate)
    outcome = report.notes[0]
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.TOKEN_NOT_ALLOWED, 1, "s1")


def test_missing_base_layer_reports_not_checked_instead_of_guessing(tmp_path: Path) -> None:
    _report, world = run(tmp_path, None)
    (world.words_path.parent / "_base.request.yaml").unlink()
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert report.ok, report.render_text()
    gates = [o for o in report.not_checked if o.code == codes.MECHANICAL_RULE_NOT_CHECKED]
    assert {gate.message.split()[1] for gate in gates} == {"M2", "M3", "M6", "M7"}
    assert all("base layer" in gate.message for gate in gates if gate.message.split()[1] in {"M2", "M3"})


def test_missing_arc_reports_not_checked_for_the_letter_gates(tmp_path: Path) -> None:
    _report, world = run(tmp_path, None)
    (world.plan_path.parent / "_arc.yaml").unlink()
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert codes.ARC_UNAVAILABLE in {o.code for o in report.failures}
    gates = [o for o in report.not_checked if o.code == codes.MECHANICAL_RULE_NOT_CHECKED]
    assert {gate.message.split()[1] for gate in gates} == {"M1/M2", "M4", "M6", "M7"}


def produced_mechanical_codes(root: Path) -> set[str]:
    produced: set[str] = set()
    for index, case in enumerate(CASES):
        produced |= run(root / f"case-{index}", case.mutate)[0].codes()
    return produced


def test_every_mechanical_code_is_produced(tmp_path: Path) -> None:
    assert produced_mechanical_codes(tmp_path) >= MECHANICAL_CODES


def test_baseline_plan_is_untouched_by_mutations() -> None:
    plan = mechanical_plan()
    before = copy.deepcopy(plan)
    _m8_word_not_reused(plan, mechanical_pack(), mechanical_words())
    assert plan != before  # the mutation helpers mutate; the builder returns a fresh plan every call
    assert mechanical_plan() == before
