"""Tests for the review-checkable plan gates C1–C28 (issue #9487).

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

import json
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml

from scripts.curriculum.validate import codes, quote_bytes, review_gates
from scripts.curriculum.validate.report import Report
from scripts.curriculum.validate.review_gates import ReviewGates
from scripts.curriculum.validate.validate import main as validate_main
from scripts.curriculum.validate.validate import validate_plan
from tests.curriculum.test_plan_validate import LEVEL, NOT_CHECKED, PRIOR_SLUG, SLUG, prior_plan, write_world
from tests.curriculum.test_plan_validate_mechanical import (
    MAMA,
    MAN,
    MANA,
    MONA,
    NONA,
    ON,
    _drop_letters,
    mechanical_pack,
    mechanical_plan,
    mechanical_words,
)

pytestmark = pytest.mark.reads_content

REVIEW_GATE_CODES = {
    codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED,
    codes.DUPLICATE_ACTIVITY_FOCUS,
    codes.LISTENING_QUIZ_SINGLE_KEY,
    codes.INCIDENTAL_NOT_DECODABLE,
    codes.INCIDENTAL_LEMMA_NOT_DECODABLE,
    codes.HEARD_WORD_WITHOUT_VIDEO,
    codes.EARLIER_CORE_NOT_RECYCLED,
    codes.RECAP_STORY_MISSING,
    codes.RECAP_COMPREHENSION_NOT_ON_STORY,
    codes.RECAP_COMPREHENSION_AFTER_PRODUCTION,
    codes.FOCUS_EVIDENCE_NOT_IN_STEPS,
    codes.STEP_WORD_NOT_DECODABLE,
    codes.STEP_WORD_LEMMA_NOT_DECODABLE,
    codes.RECYCLED_WORD_NOT_DECODABLE_IN_PRINT,
    codes.ODD_ONE_OUT_ROW_INVALID,
    codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED,
    codes.QUOTE_HOST_PRIVATE_USE,
    codes.QUOTE_HOST_TRANSCRIPTION_SYMBOL,
    codes.QUOTE_HOST_WATERMARK,
    codes.QUOTE_HOST_TOKEN_NOT_IN_VESUM,
    codes.COMPUTED_KEY_SINGLE_VALUE,
    codes.COMPUTED_KEY_FORM_DEPENDENT,
    codes.DUPLICATE_LESSON_VIDEO,
    codes.ADJACENT_STEP_SAME_DISPLAY,
    codes.ADJACENT_STEP_DISPLAY_RECALL,
    codes.INCIDENTAL_NOT_USED,
    codes.VIDEO_USE_PIPELINE_TOKEN,
    codes.VIDEO_USE_STEP_MISMATCH,
    codes.CHOICE_OPTION_UNVERIFIED,
    codes.SENTENCE_NOT_DECODABLE_AT_HOST,
    codes.SENTENCE_DECODABLE_EARLIER,
    codes.WORD_MODEL_WITHOUT_SEGMENT,
    codes.MODELED_PRINT_NOT_DECODABLE,
    codes.CHOICE_BINARY_KEYS_REPEATED,
    codes.CHOICE_BINARY_KEYS_SHARED,
    codes.CONSTRUCTION_DISTRACTOR_FORMS_WORD,
    codes.CONSTRUCTION_DISTRACTOR_CUED,
    codes.ANAGRAM_LETTERS_FORM_OTHER_WORD,
    codes.RECYCLED_CATEGORY_NOT_IN_LIST,
    codes.PRACTICE_STEP_EMPTY,
    codes.COMPREHENSION_TARGET_NOT_IN_HOST,
    codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED,
    codes.COMPREHENSION_TARGET_UNKNOWN,
    codes.COMPREHENSION_TARGET_UNVERIFIED,
    codes.LETTER_WITHOUT_RECORDING,
    codes.LETTER_TEACHER_MODELED_ONLY,
    codes.TEACH_WORD_NOT_IN_INVENTORY,
    codes.MODELED_PRINT_TEACHER_FRAME,
    codes.VESUM_UNAVAILABLE,
}

# extra word ids for these fixtures
PRIOR_ONE, PRIOR_TWO, MANOK, NOMA = "W-209", "W-210", "W-211", "W-212"
#: The words VESUM is stubbed to list in this module (the real lookup is never used by these tests). ятір, юнак,
#: рік, яма, кран, мої and крайній are VESUM forms (sources verify_words, 2026-10-02); the C11 and C12 rows print
#: them.
VESUM_FORMS = {"мамою", "ятір", "юнак", "рік", "яма", "кран", "мої", "крайній"}


def _stub_lookup(words: list[str]) -> set[str]:
    return {word for word in words if word in VESUM_FORMS}


@pytest.fixture(autouse=True)
def _stub_vesum(monkeypatch: pytest.MonkeyPatch) -> None:
    """Quote words outside the word store are looked up in a stub, so the cases never need VESUM."""
    monkeypatch.setattr(quote_bytes, "vesum_lookup", _stub_lookup)


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
                record["models"] = {"letters": model[0], "words": model[1], "segment": "0:00–0:05"}
            pack["videos"].append(record)
            _step(plan, 1, "s1")["evidence"].append(record["id"])  # a focus names only records a step cites (C9)

    return mutate


def _incidental(n: int, word_id: str, lemma: str, named: bool = True) -> Mutate:
    """An incidental record of lesson n; named (by default) in its first step's teach text (C16)."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, n)["inventory"]["vocabulary"]["incidental"].append({"lemma": lemma, "evidence": word_id})
        if named:
            step = _lesson(plan, n)["steps"][0]
            step["teach"] = f"{step['teach']} {word_id} comes up in passing."

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
        _step(plan, 2, "s2")["uses"]["vocabulary"] += list(word_ids)  # after О is taught (C10)

    return mutate


def _all(*mutations: Mutate) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        for mutation in mutations:
            mutation(plan, pack, words, prior)

    return mutate


def _recap_activities(practice: list[str], *extra: dict) -> Mutate:
    """Add activities to the recap (lesson 3) and set its step's practice order."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, 3)["activities"] += list(extra)
        _step(plan, 3, "s1")["practice"] = practice

    return mutate


def _quote(text: str, activity: dict | None = None) -> Mutate:
    """Pack text T-002 with quote bytes, cited by lesson 2 step s2, hosting activity (in consolidation)."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        pack["texts"].append({"id": "T-002", "quote": text})
        _step(plan, 2, "s2")["evidence"].append("T-002")
        host = activity or {
            "id": "b4",
            "type": "quiz",
            "placement": "workbook",
            "focus": "Read the source line. kind: comprehension; host: {kind: quote, ref: T-002}.",
        }
        _lesson(plan, 2)["activities"].append(host)
        _lesson(plan, 2)["consolidation"].append(host["id"])

    return mutate


def _odd_one_out(focus: str) -> dict:
    return {"id": "b4", "type": "odd-one-out", "placement": "workbook", "focus": focus}


def _video_records(*records: tuple[str, str, str | None]) -> Mutate:
    """Pack video records (id, url, segment) listed as lesson 1 videos."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        for video_id, url, segment in records:
            pack["videos"].append(
                {"id": video_id, "url": url, "models": {"letters": ["М"], "words": [], "segment": segment}}
            )
            _lesson(plan, 1)["videos"].append({"evidence": video_id, "use": "Letter model."})

    return mutate


def _recycle_prior_at_lesson_two_s1(step_cites_video: bool) -> Mutate:
    """Lesson 2 step s1 (before О is taught) recycles position 1's амо/ано; lesson 2 cites V-902 modelling them."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _prior_core(plan, pack, words, prior)
        two = _lesson(plan, 2)
        two["inventory"]["vocabulary"]["recycled"] += [PRIOR_ONE, PRIOR_TWO]
        _step(plan, 2, "s1")["uses"]["vocabulary"] += [PRIOR_ONE, PRIOR_TWO]
        pack["videos"].append(
            {"id": "V-902", "models": {"letters": [], "words": [PRIOR_ONE, PRIOR_TWO], "segment": "0:00–0:05"}}
        )
        two["videos"].append({"evidence": "V-902", "use": "Whole-word model."})
        if step_cites_video:
            _step(plan, 2, "s1")["evidence"].append("V-902")

    return mutate


def _core_in_lesson_two(word_id: str, lemma: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, 2)["inventory"]["vocabulary"]["core"].append(
            {"lemma": lemma, "evidence": word_id, "forms": ["tag-a"]}
        )
        _step(plan, 2, "s2")["introduces"]["vocabulary"].append(word_id)

    return mutate


def _display_in_lesson_two(s1: str, s2: str, s1_needs_quote: bool = False, quote: str = "мама") -> Mutate:
    """Pack text T-002; lesson 2's teach texts gain s1 and s2 (C15); s1 may print T-002 as a needs: quote step."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        pack["texts"].append({"id": "T-002", "quote": quote})
        for step_id, extra in (("s1", s1), ("s2", s2)):
            step = _step(plan, 2, step_id)
            step["teach"] = f"{step['teach']} {extra}".strip()
            step["evidence"].append("T-002")
        if s1_needs_quote:
            _step(plan, 2, "s1")["needs"] = ["quote"]

    return mutate


def _video_use(use: str) -> Mutate:
    return lambda plan, pack, words, prior: _lesson(plan, 1)["videos"][0].__setitem__("use", use)


def _step_cited_video_with_pack_use(use: str) -> Mutate:
    """Pack video V-901 with a use line, cited by lesson 1 step s1 but not listed in the lesson's videos (C17)."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        pack["videos"].append({"id": "V-901", "use": use, "models": {"letters": ["М"], "words": [], "segment": None}})
        _step(plan, 1, "s1")["evidence"].append("V-901")

    return mutate


def _example(text: str, word_ids: list[str], lesson: int) -> Mutate:
    """Pack example EX-901, cited by step s2 of the given lesson (C19)."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        pack["examples"].append({"id": "EX-901", "text": text, "sentence_ref": {"words": word_ids}})
        _step(plan, lesson, "s2")["evidence"].append("EX-901")

    return mutate


def _extra_activity(n: int, activity: dict) -> Mutate:
    """Add an activity to lesson n's consolidation."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, n)["activities"].append(activity)
        _lesson(plan, n)["consolidation"].append(activity["id"])

    return mutate


def _gloss(word_id: str, gloss: str) -> Mutate:
    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        next(word for word in words["words"] if word["id"] == word_id)["gloss_en"] = gloss

    return mutate


def _rationale(n: int, text: str) -> Mutate:
    return lambda plan, pack, words, prior: _lesson(plan, n).__setitem__("rationale", text)


def _practice_step(**extra: object) -> Mutate:
    """Lesson 1 gains a third, practice step s3 with no practice."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        _lesson(plan, 1)["steps"].append(
            {
                "id": "s3",
                "kind": "practice",
                "teach": "Prepare the workbook decisions.",
                "uses": {"grammar": [], "vocabulary": []},
                "evidence": ["T-001"],
                "practice": [],
                **extra,
            }
        )

    return mutate


def _letter_video(letters: list[str]) -> Mutate:
    """Lesson 2's letter recording V-899 models these letters."""
    return lambda plan, pack, words, prior: next(v for v in pack["videos"] if v["id"] == "V-899")["models"].__setitem__(
        "letters", letters
    )


def _pick(focus: str) -> Mutate:
    return _focus(2, "b3", focus)


def _exercise_print(text: str) -> Mutate:
    """Pack exercise X-001 prints text (C21)."""

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        pack["exercises"][0].update(quote=text, items_sample=[text])

    return mutate


def _comprehension_on_quote(quote: str, focus: str) -> Mutate:
    return _quote(
        quote,
        {
            "id": "b4",
            "type": "quiz",
            "placement": "workbook",
            "focus": f"{focus} kind: comprehension; host: {{kind: quote, ref: T-002}}.",
        },
    )


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
    # C1 -- a word named before its step introduces it (a note: prose does not say the word is scored)
    Case(
        "c1_dialogue_target_grammar_names_a_word_a_later_step_introduces",
        _dialogue("s1", f"Whole {MAMA} chunk only."),
        notes=frozenset({codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED}),
        says=f"names {MAMA} (introduced by step s2) in «Whole {MAMA} chunk only.», which a later step",
    ),
    Case("c1_dialogue_at_the_introducing_step_passes", _dialogue("s2", f"Whole {MAMA} chunk only.")),
    Case(
        "c1_practice_focus_scores_a_word_a_later_step_introduces",
        _focus(1, "a1", f"Checks the letter М and the word {MAMA}."),
        notes=frozenset({codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED}),
        says="activity a1 focus (practice of step s1) names W-201 (introduced by step s2)",
    ),
    Case(
        "c1_practice_focus_scores_a_word_no_lesson_introduced_yet",
        _focus(1, "a1", f"Checks the letter М and the word {NONA}."),
        notes=frozenset({codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED}),
        says=f"names {NONA} in «Checks the letter М and the word {NONA}.», which no step up to s1 introduces",
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
        _focus(1, "a4", f"Count syllables in «мама» and {MAN} and {NONA}."),
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
        says=f"the teach text says {MAMA} is heard, but no video the step cites (V-900) lists it",
    ),
    Case(
        "c5_heard_word_with_a_modelling_video_passes",
        _all(
            _videos(V_003=([], [MAMA])),
            _teach(1, "s2", f"The letter А. Hear {MAMA} as a whole word.", ["T-001", "V-900", "V-003"]),
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
    # C7 -- a recap's first-person story and the host of its comprehension
    Case(
        "c7_recap_without_a_story_block_fails",
        lambda plan, pack, words, prior: _lesson(plan, 3).pop("dialogue"),
        failures=frozenset({codes.RECAP_STORY_MISSING}),
        says="the recap declares no first-person story: it has no dialogue block",
    ),
    Case(
        "c7_recap_with_a_two_speaker_dialogue_fails",
        lambda plan, pack, words, prior: _lesson(plan, 3)["dialogue"]["speakers"].append(
            {"name": "Second", "role": "listener", "gender": "m", "evidence": MANA}
        ),
        failures=frozenset({codes.RECAP_STORY_MISSING}),
        says="it has a dialogue with 2 speakers",
    ),
    Case(
        "c7_recap_comprehension_hosted_on_a_quote_fails",
        _focus(3, "c1", "Review quiz. kind: comprehension; host: {kind: quote, ref: T-001}."),
        failures=frozenset({codes.RECAP_COMPREHENSION_NOT_ON_STORY}),
        says="comprehension activity c1 declares host kind quote (T-001)",
    ),
    Case(
        "c7_recap_without_a_comprehension_activity_fails",
        _focus(3, "c1", "Review quiz."),
        failures=frozenset({codes.RECAP_COMPREHENSION_NOT_ON_STORY}),
        says="no activity of the recap declares kind: comprehension",
    ),
    # C8 -- the story's questions come before the production task
    Case(
        "c8_production_linked_before_the_questions_fails",
        _recap_activities(
            ["c2", "c1"],
            {"id": "c2", "type": "letter-grid", "placement": "inline", "focus": "Copy the story into a notebook."},
        ),
        failures=frozenset({codes.RECAP_COMPREHENSION_AFTER_PRODUCTION}),
        says="comprehension activity c1 (linked in s1) comes after c2 (letter-grid)",
    ),
    Case(
        "c8_story_display_before_and_production_after_the_questions_passes",
        _recap_activities(
            ["c0", "c1", "c2"],
            {"id": "c0", "type": "observe", "placement": "inline", "focus": "Read the story."},
            {"id": "c2", "type": "letter-grid", "placement": "inline", "focus": "Copy the story into a notebook."},
        ),
    ),
    # C9 -- a record a focus names reaches the writer only through the lesson's citations
    Case(
        "c9_focus_names_a_record_no_step_cites_fails",
        _focus(1, "a1", "Checks the letter М against the X-001 row."),
        failures=frozenset({codes.FOCUS_EVIDENCE_NOT_IN_STEPS}),
        says="activity a1 focus names X-001, which no step of this lesson cites",
    ),
    Case(
        "c9_focus_names_its_own_model_or_step_evidence_passes",
        _all(
            _focus(1, "a2", "Complete «мама» and «ман» with А from the X-001 rows."),
            _focus(1, "a1", "Checks the letter М in T-001."),
        ),
    ),
    # C10 -- a step's words are decodable so far, or recorded
    Case(
        "c10_step_word_with_an_untaught_letter_and_no_recording_fails",
        # The lesson's recording keeps modelling its letters (C27) but no longer models the words.
        lambda plan, pack, words, prior: pack["videos"][0]["models"].__setitem__("words", []),
        failures=frozenset({codes.STEP_WORD_NOT_DECODABLE}),
        says=f"step s2 introduces or uses {MANA} 'мана' (needs н), {MAN} 'ман' (needs н)",
    ),
    Case(
        "c10_recycled_word_recorded_elsewhere_in_the_lesson_fails_in_print",
        _recycle_prior_at_lesson_two_s1(step_cites_video=False),
        failures=frozenset({codes.RECYCLED_WORD_NOT_DECODABLE_IN_PRINT}),
        says=f"step s1 recycles {PRIOR_ONE} 'амо' (needs о), {PRIOR_TWO} 'ано' (needs о)",
    ),
    Case(
        "c10_recycled_word_whose_step_cites_its_recording_passes",
        _recycle_prior_at_lesson_two_s1(step_cites_video=True),
    ),
    Case(
        "c10_lemma_unreadable_while_a_form_is_readable_is_a_note",
        _all(_word(MANOK, "манок", "мано"), _core_in_lesson_two(MANOK, "манок")),
        notes=frozenset({codes.STEP_WORD_LEMMA_NOT_DECODABLE}),
        says=f"step s2 introduces or uses {MANOK} 'манок' (needs к; readable: мано)",
    ),
    # C11 -- odd-one-out rows drawn from a quote host
    Case(
        "c11_row_without_one_odd_member_fails",
        _quote(
            "мама мана нона\nмама мана мана",
            _odd_one_out("Pick the member whose initial letter differs. host: {kind: quote, ref: T-002}."),
        ),
        failures=frozenset({codes.ODD_ONE_OUT_ROW_INVALID}),
        says="row 'мама мана мана' of T-002 does not have exactly one member differing in initial letter",
    ),
    Case(
        "c11_rows_with_one_odd_member_pass",
        _quote(
            "мама мана нона\nман нона нона",
            _odd_one_out("Pick the member whose first letter differs. host: {kind: quote, ref: T-002}."),
        ),
    ),
    Case(
        "c11_syllable_count_feature_is_computed",
        _quote(
            "мама ман мана", _odd_one_out("Pick the member whose syllables differ. host: {kind: quote, ref: T-002}.")
        ),
    ),
    Case(
        "c11_feature_the_gate_cannot_compute_is_a_note",
        _quote("мама мана нона", _odd_one_out("Pick the odd member. host: {kind: quote, ref: T-002}.")),
        notes=frozenset({codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED}),
        says="activity b4 draws odd-one-out rows from T-002 (мама мана нона)",
    ),
    # C12 -- quote-host bytes the engine prints verbatim
    Case(
        "c12_private_use_code_point_fails",
        _quote("мама \uf0fc мана"),
        failures=frozenset({codes.QUOTE_HOST_PRIVATE_USE}),
        says="quote host T-002 (hosting lesson 2 b4) carries private use: U+F0FC",
    ),
    Case(
        "c12_symbol_inside_a_transcription_bracket_fails",
        _quote("мама [ма\u00bea]"),
        failures=frozenset({codes.QUOTE_HOST_TRANSCRIPTION_SYMBOL}),
        says="'[ма¾a]' holds",
    ),
    Case(
        "c12_publisher_watermark_fails",
        _quote("мама мана\nPidruchnyk.com.ua"),
        failures=frozenset({codes.QUOTE_HOST_WATERMARK}),
        says="carries watermark: 'Pidruchnyk.com.ua'",
    ),
    Case(
        "c12_word_neither_in_the_store_nor_in_vesum_fails",
        _quote("мама номана мамою"),
        failures=frozenset({codes.QUOTE_HOST_TOKEN_NOT_IN_VESUM}),
        says="prints 'номана', which are neither word-store spellings nor VESUM forms",
    ),
    Case(
        "c12_alphabet_table_letter_pairs_pass",
        _quote("Аа Бб Ґґ Єє Ии Іі Її Оо Юю Яя Дждж\nмама"),
    ),
    Case(
        "c12_letter_runs_that_are_not_a_capital_and_its_own_small_letter_fail",
        _quote("Єє ЄИ єє Оа"),
        failures=frozenset({codes.QUOTE_HOST_TOKEN_NOT_IN_VESUM}),
        says="prints 'ЄИ', 'єє', 'Оа', which are neither word-store spellings nor VESUM forms",
    ),
    Case(
        "c12_clean_quote_with_schemes_syllables_and_hyphenation_passes",
        _quote("Ма-ма, мана [ = • – ] [ма′на]\nма мо му нона ма-\nна мамою"),
    ),
    # C13 -- a computed key that is the same for every target
    Case(
        "c13_count_syllables_with_one_count_across_targets_fails",
        _focus(1, "a4", f"Count syllables in {MAMA} and {MANA}."),
        failures=frozenset({codes.COMPUTED_KEY_SINGLE_VALUE}),
        says=f"count-syllables activity a4 targets {MAMA}, {MANA}, whose syllable count is 2 for every target",
    ),
    Case(
        "c13_count_syllables_with_two_counts_passes",
        _focus(1, "a4", f"Count syllables in {MAMA} and {MAN}."),
    ),
    Case(
        "c13_another_count_only_through_an_unbound_form_is_a_note",
        _all(_word(MANOK, "манок", "мано", "манками"), _focus(1, "a4", f"Count syllables in {MAMA} and {MANOK}.")),
        notes=frozenset({codes.COMPUTED_KEY_FORM_DEPENDENT}),
        says=f"another key needs a form the plan does not bind ({MANOK})",
    ),
    # C14 -- one recording embedded twice in a lesson
    Case(
        "c14_two_entries_for_one_youtube_video_fail",
        _video_records(
            ("V-910", "https://www.youtube.com/watch?v=ksXIXj7CXwc", None),
            ("V-911", "https://youtu.be/ksXIXj7CXwc", None),
        ),
        failures=frozenset({codes.DUPLICATE_LESSON_VIDEO}),
        says="video entries V-910, V-911 resolve to one recording (youtube:ksXIXj7CXwc, whole video)",
    ),
    Case(
        "c14_two_segments_of_one_video_pass",
        _video_records(
            ("V-910", "https://www.youtube.com/watch?v=ksXIXj7CXwc", "0:00–0:10"),
            ("V-911", "https://www.youtube.com/watch?v=ksXIXj7CXwc", "0:10–0:20"),
        ),
    ),
    # C15 -- one record displayed by two adjacent steps
    Case(
        "c15_adjacent_steps_displaying_one_quote_fail",
        _display_in_lesson_two("", "Display the attributed T-002 before b2.", s1_needs_quote=True),
        failures=frozenset({codes.ADJACENT_STEP_SAME_DISPLAY}),
        says="steps s1 and s2 both display T-002; steps and their evidence are binding (plan schema §7 decision 1)",
    ),
    Case(
        "c15_second_display_called_a_recall_is_a_note",
        _display_in_lesson_two("Display T-002 before b1.", "Recall the already displayed T-002 before b2."),
        notes=frozenset({codes.ADJACENT_STEP_DISPLAY_RECALL}),
        says="steps s1 and s2 both display T-002, and s2 calls it a recall",
    ),
    Case(
        "c15_record_as_subject_or_negated_display_passes",
        _display_in_lesson_two("Display T-002 before b1.", "T-002 shows О; do not display T-002 here."),
    ),
    # C16 -- an incidental record the lesson never names
    Case(
        "c16_incidental_named_nowhere_is_a_note",
        _incidental(2, ON, "он", named=False),
        notes=frozenset({codes.INCIDENTAL_NOT_USED}),
        says=f"1 incidental record named by no step, activity or dialogue of the lesson, nor in a record it displays or a recording it cites: {ON} 'он'",
    ),
    Case(
        "c16_incidental_printed_by_a_displayed_quote_passes",
        _all(
            _incidental(2, ON, "он", named=False), _display_in_lesson_two("", "", s1_needs_quote=True, quote="о-н мама")
        ),
    ),
    Case(
        "c16_a_quote_cited_only_as_grounding_does_not_name_it",
        _all(_incidental(2, ON, "он", named=False), _display_in_lesson_two("", "", quote="он мама")),
        notes=frozenset({codes.INCIDENTAL_NOT_USED}),
        says=f"{ON} 'он'",
    ),
    # C17 -- the description Ресурси prints for a lesson video
    Case(
        "c17_pipeline_wording_in_a_video_use_fails",
        _video_use("Step s2 whole-word model (segment: null); acoustic proof remains driver-owned."),
        failures=frozenset({codes.VIDEO_USE_PIPELINE_TOKEN}),
        says="carries pipeline wording: 'segment:' (the YAML syntax of the pack field models.segment), 'null'",
    ),
    Case(
        "c17_record_id_in_a_video_use_fails",
        _video_use("Step s2 whole-word model; T-001 supplies the rows."),
        failures=frozenset({codes.VIDEO_USE_PIPELINE_TOKEN}),
        says="'T-001' (a record id)",
    ),
    Case(
        "c17_pack_use_printed_for_a_step_cited_video_fails",
        _step_cited_video_with_pack_use("Letter model; exact playback/timecode confirmation remains driver-owned."),
        failures=frozenset({codes.VIDEO_USE_PIPELINE_TOKEN}),
        says="the Ресурси description of V-901 (the pack record's use:",
    ),
    Case(
        "c17_video_use_naming_a_step_that_does_not_cite_it_fails",
        _video_use("Step s1 whole-word model."),
        failures=frozenset({codes.VIDEO_USE_STEP_MISMATCH}),
        says="the Ресурси description of V-900 (videos[].use) names step s1, which does not cite V-900",
    ),
    Case("c17_plain_where_and_why_use_passes", _video_use("Step s2: hear the whole words before reading them.")),
    # C18 -- a choice focus word with a letter the lesson has not taught (a note: the plan has no option field)
    Case(
        "c18_quiz_option_with_an_untaught_letter_is_a_note",
        _focus(1, "a1", "Checks the letter М; the options are мама and нона."),
        notes=frozenset({codes.CHOICE_OPTION_UNVERIFIED}),
        says="quiz activity a1 focus names 'нона' (needs н, о) in «the options are мама and нона.»",
    ),
    Case(
        "c18_option_a_cited_recording_models_passes",
        _focus(1, "a1", "Checks the letter М; the options are мама and ман."),
    ),
    # C19 -- an example sentence and the lesson that can read it
    Case(
        "c19_sentence_cited_before_its_letters_are_taught_fails",
        _example("Мама, нона.", [MAMA, NONA], 1),
        failures=frozenset({codes.SENTENCE_NOT_DECODABLE_AT_HOST}),
        says="example EX-901 ('Мама, нона.') is cited in lesson 1 and needs н, о",
    ),
    Case(
        "c19_sentence_decodable_in_an_earlier_lesson_is_a_note",
        _example("Мама.", [MAMA], 2),
        notes=frozenset({codes.SENTENCE_DECODABLE_EARLIER}),
        says="example EX-901 ('Мама.') is cited first in lesson 2 but is decodable from lesson 1",
    ),
    Case("c19_sentence_cited_where_it_becomes_decodable_passes", _example("Мама.", [MAMA], 1)),
    # C20 -- a word model without its timed segment
    Case(
        "c20_word_model_without_a_segment_fails",
        lambda plan, pack, words, prior: pack["videos"][0]["models"].__setitem__("segment", None),
        failures=frozenset({codes.WORD_MODEL_WITHOUT_SEGMENT}),
        says=f"V-900 models {MANA}, {MAN} (words or phrases, not a whole-resource letter) but binds no models.segment",
    ),
    # C21 -- a step that sends the learner to the exact print of a record it cannot read
    Case(
        "c21_exact_print_before_its_letters_are_taught_fails",
        _teach(1, "s1", "The letter М. Modeling source: the teacher demonstrates the exact print in X-001."),
        failures=frozenset({codes.MODELED_PRINT_NOT_DECODABLE}),
        says="step s1 teach text directs modelling or reading the exact print of X-001 (мама; needs а)",
    ),
    Case(
        "c21_activity_focus_modelling_the_exact_print_fails_at_its_step",
        _all(
            _focus(
                1,
                "a1",
                "Checks the letter М. Before this print reading, the teacher models the exact cited X-001 forms.",
            ),
            lambda plan, pack, words, prior: _step(plan, 1, "s1")["evidence"].append("X-001"),  # cited (C9)
        ),
        failures=frozenset({codes.MODELED_PRINT_NOT_DECODABLE}),
        says="activity a1 focus directs modelling or reading the exact print of X-001",
    ),
    Case(
        "c21_exact_print_at_the_step_that_teaches_its_letters_passes",
        _teach(1, "s2", "The letter А. Modeling source: the teacher demonstrates the exact print in X-001."),
    ),
    Case(
        "c21_reading_named_words_of_a_record_is_not_its_print",
        _teach(1, "s1", "The letter М. Also read the exact X-001 ма syllable after teacher demonstration."),
    ),
    # C22 -- one binary key set scored by several choice activities
    Case(
        "c22_three_choice_activities_on_one_binary_key_set_fail",
        _all(
            _focus(1, "a1", "Checks the letter М; keys мама and ман vary."),
            _focus(1, "a2", "Complete «мама» and «ман» with А. Both keys Мама and ман occur."),
            _extra_activity(
                1, {"id": "a5", "type": "quiz", "placement": "workbook", "focus": "Transfer: keys мама/ман."}
            ),
        ),
        failures=frozenset({codes.CHOICE_BINARY_KEYS_REPEATED}),
        says="choice activities a1, a2, a5 all declare the two keys мама / ман",
    ),
    Case(
        "c22_two_choice_activities_on_one_binary_key_set_are_a_note",
        _all(
            _focus(1, "a1", "Checks the letter М; keys мама and ман vary."),
            _focus(1, "a2", "Complete «мама» and «ман» with А. Both keys мама and ман occur."),
        ),
        notes=frozenset({codes.CHOICE_BINARY_KEYS_SHARED}),
        says="choice activities a1, a2 both declare the two keys мама / ман",
    ),
    Case(
        "c22_different_key_sets_pass",
        _all(
            _focus(1, "a1", "Checks the letter М; keys мама and ман vary."),
            _focus(1, "a2", "Complete «мама» and «ман» with А. Keys 1, 2 and 3 occur."),
        ),
    ),
    # C23 -- a construction item whose other completion is a real word
    Case(
        "c23_syllable_swap_forming_a_store_word_fails",
        _pick("Complete the source segmentations ма-ма and мо-на; select the missing final syllables."),
        failures=frozenset({codes.CONSTRUCTION_DISTRACTOR_FORMS_WORD}),
        says="pick-syllables activity b3: another syllable of the activity in a blanked slot forms a word-store "
        "spelling or VESUM form (ма-на → мана)",
    ),
    Case(
        "c23_blanked_row_with_its_key_fails",
        _pick("The final blank in ма- __ has key на; the other row is но-на."),
        failures=frozenset({codes.CONSTRUCTION_DISTRACTOR_FORMS_WORD}),
        says="ма-ма → мама",
    ),
    Case(
        "c23_swap_forming_a_vesum_form_fails",
        _pick("Complete ма-мою from its syllables; select the missing final syllable among мою and ма."),
        failures=frozenset({codes.CONSTRUCTION_DISTRACTOR_FORMS_WORD}),
        says="ма-ма → мама",
    ),
    Case(
        "c23_stems_carrying_a_cue_are_a_note",
        _pick("Complete ма-ма and мо-на; select the missing final syllables. Each stem carries its English gloss."),
        notes=frozenset({codes.CONSTRUCTION_DISTRACTOR_CUED}),
        says="the focus says the stems carry a cue",
    ),
    # ма-на (a store word) would come only from the final slot, which the focus does not blank.
    Case("c23_only_the_named_slot_is_swapped", _pick("Complete ма-ма; select the missing first syllable among на.")),
    Case(
        "c23_swaps_forming_no_word_pass", _pick("Complete но-на from its syllables; select the missing first syllable.")
    ),
    Case(
        "c23_anagram_spelling_another_store_word_is_a_note",
        _all(
            _word(NOMA, "нома"),
            _extra_activity(2, {"id": "b4", "type": "anagram", "placement": "workbook", "focus": f"Assemble {MONA}."}),
        ),
        notes=frozenset({codes.ANAGRAM_LETTERS_FORM_OTHER_WORD}),
        says=f"the letters also spell {MONA} мона → нома",
    ),
    Case(
        "c23_anagram_with_one_arrangement_passes",
        _extra_activity(2, {"id": "b4", "type": "anagram", "placement": "workbook", "focus": f"Assemble {MONA}."}),
    ),
    # C24 -- a recycle claim the recycled list does not back
    Case(
        "c24_recycled_category_with_no_record_in_the_lesson_fails",
        _all(_gloss(NONA, "nun (a woman)"), _rationale(1, "This lesson recycles word records including nuns.")),
        failures=frozenset({codes.RECYCLED_CATEGORY_NOT_IN_LIST}),
        says=f"the lesson rationale says it recycles 'nun' ({NONA} нона)",
    ),
    Case(
        "c24_quoted_word_not_recycled_fails",
        _rationale(1, "This lesson recycles word records such as «нона»."),
        failures=frozenset({codes.RECYCLED_CATEGORY_NOT_IN_LIST}),
        says=f"«нона» ({NONA} нона)",
    ),
    Case(
        "c24_category_held_by_the_lesson_and_function_words_pass",
        _all(
            _gloss(NONA, "nun (a woman)"),
            _gloss(ON, "and"),
            _rationale(2, "This lesson recycles word records including nuns and earlier forms."),
        ),
    ),
    # C25 -- a practice step with nothing in it
    Case(
        "c25_practice_step_with_no_content_fails",
        _practice_step(),
        failures=frozenset({codes.PRACTICE_STEP_EMPTY}),
        says="practice step s3 links no activity, needs no block",
    ),
    Case(
        "c25_practice_step_that_shows_a_video_passes",
        _practice_step(needs=["video"], evidence=["V-900"]),
    ),
    # C26 -- a comprehension item about a word its host does not hold
    Case(
        "c26_comprehension_target_absent_from_the_quote_fails",
        _comprehension_on_quote("он мама", f"Answer about {NONA}."),
        failures=frozenset({codes.COMPREHENSION_TARGET_NOT_IN_HOST}),
        says=f"comprehension activity b4 names {NONA} 'нона', which no host (T-002) prints or models",
    ),
    Case(
        "c26_target_only_in_a_transcription_is_a_note",
        _comprehension_on_quote("мама [нон′а]", f"Answer about {NONA}."),
        notes=frozenset({codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED}),
        says=f"{NONA} 'нона', which no host (T-002) prints in spelling",
    ),
    Case(
        "c26_targets_the_host_prints_pass_also_in_a_sentence_about_another_activity",
        _comprehension_on_quote("он м а м а", f"Answer about {MAMA}. Inline b2 uses {MAMA}."),
    ),
    # A sentence naming another activity does not say whose items it is about, so an unhosted id there notes.
    Case(
        "c26_unhosted_id_in_a_sentence_about_another_activity_is_a_note",
        _comprehension_on_quote("он м а м а", f"Answer about {MAMA}. Inline b2 uses {MANA}."),
        notes=frozenset({codes.COMPREHENSION_TARGET_UNVERIFIED}),
        says=f"names {MANA} 'мана' in «Inline b2 uses {MANA}» (the sentence names activity b2), whose presence in the host",
    ),
    # Exclusion wording in prose does not say which id it excludes, so an unhosted id there notes, never vanishes.
    Case(
        "c26_unhosted_target_in_an_excluding_sentence_is_a_note",
        _comprehension_on_quote("он мама", f"Asks about {NONA} and do not give hints."),
        notes=frozenset({codes.COMPREHENSION_TARGET_UNVERIFIED}),
        says=(
            f"names {NONA} 'нона' in «Asks about {NONA} and do not give hints» (the sentence says something is "
            "excluded), whose presence in the host (T-002) is unverified"
        ),
    ),
    # round 10 of the cross-family review (#9487): the reviewer's fixtures, which passed silently.
    Case(
        "c26_excluding_sentence_naming_another_activity_is_a_note",
        _comprehension_on_quote("он мама", f"This b4 asks about {NONA} and do not give hints as in b2."),
        notes=frozenset({codes.COMPREHENSION_TARGET_UNVERIFIED}),
        says=(
            f"in «This b4 asks about {NONA} and do not give hints as in b2» (the sentence says something is "
            "excluded and names activity b2)"
        ),
    ),
    Case(
        "c26_plain_sentence_naming_another_activity_is_a_note",
        _comprehension_on_quote("он мама", f"This b4 asks about {NONA} as in b2."),
        notes=frozenset({codes.COMPREHENSION_TARGET_UNVERIFIED}),
        says=f"names {NONA} 'нона' in «This b4 asks about {NONA} as in b2» (the sentence names activity b2)",
    ),
    Case(
        "c26_target_also_in_a_plain_sentence_fails_over_a_sentence_about_another_activity",
        _comprehension_on_quote("он мама", f"This b4 asks about {NONA} as in b2. Answer about {NONA}."),
        failures=frozenset({codes.COMPREHENSION_TARGET_NOT_IN_HOST}),
    ),
    Case(
        "c26_same_target_in_a_plain_sentence_fails",
        _comprehension_on_quote("он мама", f"Asks about {NONA}. Give no hints."),
        failures=frozenset({codes.COMPREHENSION_TARGET_NOT_IN_HOST}),
        says=f"comprehension activity b4 names {NONA} 'нона', which no host (T-002) prints or models",
    ),
    Case(
        "c26_target_also_in_a_plain_sentence_fails_without_a_note",
        _comprehension_on_quote("он мама", f"Answer about {NONA}. Do not reuse {NONA} later."),
        failures=frozenset({codes.COMPREHENSION_TARGET_NOT_IN_HOST}),
    ),
    Case(
        "c26_hosted_target_in_an_excluding_sentence_passes",
        _comprehension_on_quote("он м а м а", f"Asks about {MAMA} and do not give hints."),
    ),
    # round 11 of the cross-family review (#9487): the reviewer's fixtures, which passed silently.
    Case(
        "c26_focus_id_the_store_lacks_fails",
        _comprehension_on_quote("он мама", "Answer about W-999."),
        failures=frozenset({codes.COMPREHENSION_TARGET_UNKNOWN}),
        says="comprehension activity b4 names W-999 in «Answer about W-999», which the level word store does not hold",
    ),
    Case(
        "c26_sibling_dialogue_host_does_not_skip_the_check",
        _comprehension_on_quote("он мама", f"This b4 asks about {NONA} as in b2 (host: {{kind: dialogue}})."),
        notes=frozenset({codes.COMPREHENSION_TARGET_UNVERIFIED}),
        says=f"names {NONA} 'нона' in «This b4 asks about {NONA} as in b2 (host: {{kind: dialogue}})» (the sentence",
    ),
    Case(
        "c26_own_dialogue_host_notes_a_word_no_resolvable_host_holds",
        _quote(
            "он мама",
            {
                "id": "b4",
                "type": "quiz",
                "placement": "workbook",
                "focus": f"Answer about {NONA}. kind: comprehension; host: {{kind: dialogue}}.",
            },
        ),
        notes=frozenset({codes.COMPREHENSION_TARGET_UNVERIFIED}),
        says=(
            f"names {NONA} 'нона' in «Answer about {NONA}», whose presence in the host (dialogue) is unverified; host dialogue "
            "is not a pack quote or a recording with models"
        ),
    ),
    # C27 -- a new letter with no recording that models it
    Case(
        "c27_letters_no_recording_models_fail",
        _letter_video([]),
        failures=frozenset({codes.LETTER_WITHOUT_RECORDING}),
        says="step s1 introduces Н, but no recording the lesson cites declares it in models.letters (V-899)",
    ),
    Case(
        "c27_teacher_model_recorded_for_the_letter_is_a_note",
        _all(_letter_video(["О"]), _teach(2, "s1", "The letter Н; the teacher models Н aloud before reading.")),
        notes=frozenset({codes.LETTER_TEACHER_MODELED_ONLY}),
        says="step s1 introduces Н, which no recording the lesson cites models (V-899)",
    ),
    Case("c27_letters_compared_case_folded_pass", _letter_video(["н", "о"])),
    # C28 -- a teach text naming a word the lesson's packet lacks
    Case(
        "c28_teach_text_naming_a_later_word_fails",
        _teach(1, "s1", f"The letter М; {NONA} comes later."),
        failures=frozenset({codes.TEACH_WORD_NOT_IN_INVENTORY}),
        says=f"step s1 teach text names {NONA} нона, outside the lesson's inventory",
    ),
    Case("c28_teach_text_naming_a_recycled_word_passes", _teach(2, "s1", f"The letter Н; recall {MAMA}.")),
    # round 8 of the cross-family review (#9487): the reviewer's fixtures
    Case(
        "c1_a_word_the_focus_keeps_out_is_still_a_note_not_read_from_prose",
        _focus(1, "a1", f"Checks the letter М. Do not score {MAMA} here; it is introduced in s2."),
        notes=frozenset({codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED}),
        says=f"in «Do not score {MAMA} here;»",
    ),
    Case(
        "c11_initial_sound_of_word_initial_ya_yu_is_y",
        _quote(
            "ятір юнак рік",
            _odd_one_out("Pick the member whose initial sound differs. host: {kind: quote, ref: T-002}."),
        ),
    ),
    Case(
        "c11_initial_sound_shared_by_every_member_fails",
        _quote(
            "ятір юнак яма",
            _odd_one_out("Pick the member whose initial sound differs. host: {kind: quote, ref: T-002}."),
        ),
        failures=frozenset({codes.ODD_ONE_OUT_ROW_INVALID}),
        says="differing in initial sound: ятір (й), юнак (й), яма (й)",
    ),
    Case(
        "c11_initial_letters_of_the_same_row_still_differ",
        _quote(
            "ятір юнак рік",
            _odd_one_out("Pick the member whose initial letter differs. host: {kind: quote, ref: T-002}."),
        ),
        failures=frozenset({codes.ODD_ONE_OUT_ROW_INVALID}),
        says="differing in initial letter: ятір (я), юнак (ю), рік (р)",
    ),
    Case(
        "c11_initial_sound_the_gate_does_not_compute_is_a_note",
        _quote(
            "кран ятір юнак\nятір юнак рік",
            _odd_one_out("Pick the member whose first sound differs. host: {kind: quote, ref: T-002}."),
        ),
        notes=frozenset({codes.ODD_ONE_OUT_FEATURE_NOT_COMPUTED}),
        says="row 'кран ятір юнак' of T-002: the gate does not compute the initial sound of кран",
    ),
    Case("c12_decomposed_quote_is_read_as_its_composed_words", _quote(unicodedata.normalize("NFD", "мої крайній"))),
    Case(
        "c18_ukrainian_word_in_focus_prose_is_a_note_not_an_option",
        _focus(
            1,
            "a1",
            "Checks the letter М; the options are М and А. The teacher translates прочитай aloud and never displays it.",
        ),
        notes=frozenset({codes.CHOICE_OPTION_UNVERIFIED}),
        says="quiz activity a1 focus names 'прочитай' (needs и, й, о, п, р, т, ч) in «The teacher translates",
    ),
    Case(
        "c21_teacher_read_instruction_with_a_bounded_learner_reading_passes",
        _all(
            _exercise_print("Прочитай: мама."),
            _teach(
                1,
                "s2",
                "The letter А. The teacher demonstrates the exact print in X-001. The teacher reads the "
                "instruction while the learner reads only мама.",
            ),
        ),
    ),
    Case(
        "c21_teacher_read_word_named_in_the_plan_is_not_learner_print",
        _all(
            _exercise_print("Прочитай: мама."),
            _teach(
                1, "s2", "The letter А. The teacher demonstrates the exact print in X-001; the teacher reads Прочитай."
            ),
        ),
    ),
    Case(
        "c21_teacher_read_instruction_without_its_words_is_a_note",
        _all(
            _exercise_print("Прочитай: мама."),
            _teach(
                1,
                "s2",
                "The letter А. The teacher demonstrates the exact print in X-001; the teacher reads the instruction.",
            ),
        ),
        notes=frozenset({codes.MODELED_PRINT_TEACHER_FRAME}),
        says="X-001 (Прочитай; needs",
    ),
    Case(
        "c21_a_word_both_teacher_and_learner_read_is_learner_print",
        _all(
            _exercise_print("мало"),
            _teach(
                1,
                "s2",
                "The letter А. The teacher demonstrates the exact print in X-001. The teacher reads мало. The "
                "learner reads only мало.",
            ),
        ),
        failures=frozenset({codes.MODELED_PRINT_NOT_DECODABLE}),
        says="X-001 (мало; needs л, о)",
    ),
    Case(
        "c21_unbounded_exact_print_with_an_untaught_frame_word_fails",
        _all(
            _exercise_print("Прочитай: мама."),
            _teach(1, "s2", "The letter А. The teacher demonstrates the exact print in X-001."),
        ),
        failures=frozenset({codes.MODELED_PRINT_NOT_DECODABLE}),
        says="X-001 (Прочитай; needs",
    ),
]


def run(root: Path, mutate: Mutate | None, strict: bool = False) -> Report:
    return validate_plan(LEVEL, SLUG, plan_path=_world(root, mutate), strict=strict)


def _world(root: Path, mutate: Mutate | None) -> Path:
    """The plan path of a written world: the mechanical plan, its prior plan and its base request."""
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
    return world.plan_path


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_case(tmp_path: Path, case: Case) -> None:
    report = run(tmp_path, case.mutate)
    text = report.render_text()
    assert {o.code for o in report.failures} == set(case.failures), text
    assert {o.code for o in report.notes} == set(case.notes) | {codes.OPTIONS_MISSING}, text
    assert {o.code for o in report.not_checked} == NOT_CHECKED | set(case.not_checked), text
    if case.says:
        assert any(case.says in o.message for o in report.failures + report.notes + report.not_checked), text


def test_outcomes_name_lesson_and_step(tmp_path: Path) -> None:
    report = run(tmp_path, next(c for c in CASES if c.name.startswith("c1_dialogue_target")).mutate)
    outcome = next(o for o in report.notes if o.code != codes.OPTIONS_MISSING)
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED, 1, "s1")


def test_unavailable_base_layer_skips_c1_instead_of_guessing(tmp_path: Path) -> None:
    plan, pack, words, prior = mechanical_plan(), mechanical_pack(), mechanical_words(), prior_plan()
    _focus(1, "a1", f"Checks the letter М and the word {NONA}.")(plan, pack, words, prior)
    world = write_world(tmp_path, plan, pack, words)  # no _base.request.yaml: the base layer is unknown
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED not in report.codes(), report.render_text()
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
    """Every code the cases produce, with this module's VESUM stub: test_plan_validate's registry test calls this
    outside the autouse fixture, and the set must not depend on whether the host has VESUM."""
    produced: set[str] = set()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(quote_bytes, "vesum_lookup", _stub_lookup)
        for index, case in enumerate(CASES):
            produced |= run(root / f"case-{index}", case.mutate).codes()

    def unavailable(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("no database")

    with pytest.MonkeyPatch.context() as patch:  # VESUM unreadable: the C12 lookup is undecided
        patch.setattr(quote_bytes, "vesum_lookup", unavailable)
        produced |= run(root / "vesum-unavailable", _quote("мама мамою")).codes()
    return produced


def test_every_review_gate_code_is_produced(tmp_path: Path) -> None:
    assert produced_review_gate_codes(tmp_path) >= REVIEW_GATE_CODES


def test_c12_unavailable_vesum_is_not_checked_not_passed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("no database")

    monkeypatch.setattr(quote_bytes, "vesum_lookup", unavailable)
    report = run(tmp_path, _quote("мама номана мана \uf0fc"))
    assert {o.code for o in report.failures} == {codes.QUOTE_HOST_PRIVATE_USE}, report.render_text()
    undecided = [o.message for o in report.not_checked if o.code == codes.VESUM_UNAVAILABLE]
    assert undecided and undecided[0].startswith("gate C12 is undecided"), report.render_text()
    assert report.status == "fail"


def test_c12_unavailable_vesum_never_passes_strict(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The reviewer's case: a clean quote host whose words need a lookup no longer passes strict with no failures."""

    def unavailable(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("no database")

    monkeypatch.setattr(quote_bytes, "vesum_lookup", unavailable)
    report = run(tmp_path, _quote("мама мамою"), strict=True)
    assert codes.VESUM_UNAVAILABLE in {o.code for o in report.failures}, report.render_text()
    assert report.status == "fail"


def _vesum_unreadable(monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("no database")

    monkeypatch.setattr(quote_bytes, "vesum_lookup", unavailable)


DECLARE_NO_VESUM = ["--not-checked-when-unavailable", "vesum"]


def test_strict_cli_fails_an_undecided_vesum_gate_unless_declared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """CI's runner has no VESUM: only the declared option keeps the undecided gate not_checked under --strict."""
    _vesum_unreadable(monkeypatch)
    plan_path = _world(tmp_path, _quote("мама мамою"))
    command = [LEVEL, SLUG, "--plan", str(plan_path), "--strict"]

    assert validate_main(command) == 1
    assert "FAIL vesum_unavailable: gate C12 is undecided because VESUM is unavailable" in capsys.readouterr().out

    assert validate_main([*command, *DECLARE_NO_VESUM]) == 0
    out = capsys.readouterr().out
    assert "status: pass" in out
    assert "FAIL " not in out
    undecided = [line for line in out.splitlines() if line.startswith("NOT_CHECKED vesum_unavailable: ")]
    assert len(undecided) == 1, out
    assert undecided[0].startswith("NOT_CHECKED vesum_unavailable: gate C12 is undecided because VESUM is unavailable")
    assert undecided[0].endswith("no database (declared by --not-checked-when-unavailable vesum)"), undecided


def test_declared_vesum_unavailable_lists_each_undecided_gate_in_the_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _vesum_unreadable(monkeypatch)
    plan_path = _world(tmp_path, _pick("Complete но-на from its syllables; select the missing first syllable."))
    assert validate_main([LEVEL, SLUG, "--plan", str(plan_path), "--strict", "--json", *DECLARE_NO_VESUM]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "pass"
    undecided = [entry["message"] for entry in payload["not_checked"] if entry["code"] == codes.VESUM_UNAVAILABLE]
    assert len(undecided) == 1 and undecided[0].startswith("gate C23 is undecided"), undecided


def test_declared_vesum_unavailable_never_hides_another_strict_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    _vesum_unreadable(monkeypatch)
    plan_path = _world(tmp_path, _quote("мама мамою \uf0fc"))
    assert validate_main([LEVEL, SLUG, "--plan", str(plan_path), "--strict", *DECLARE_NO_VESUM]) == 1
    out = capsys.readouterr().out
    assert f"FAIL {codes.QUOTE_HOST_PRIVATE_USE}" in out
    assert "NOT_CHECKED vesum_unavailable: gate C12" in out


def test_all_mode_prints_declared_undecided_gates_of_a_passing_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """--all prints only failing plans' reports, so a passing plan's undecided gates get their own lines. The
    level's prior plan is a schema stub that fails on its own, so this reads the plan's lines, not the exit code
    (the single-plan test above holds the exit codes)."""
    _vesum_unreadable(monkeypatch)
    plan_path = _world(tmp_path, _quote("мама мамою"))
    command = [LEVEL, "--all", "--level-dir", str(plan_path.parent), "--strict"]

    validate_main(command)
    out = capsys.readouterr().out
    assert f"{LEVEL}/{SLUG}: fail (1 failures)" in out
    assert "FAIL vesum_unavailable: gate C12 is undecided" in out

    validate_main([*command, *DECLARE_NO_VESUM])
    out = capsys.readouterr().out
    assert f"{LEVEL}/{SLUG}: pass" in out.splitlines()
    assert f"{LEVEL}/{SLUG}: NOT_CHECKED vesum_unavailable: gate C12 is undecided" in out
    assert "FAIL vesum_unavailable" not in out


def test_c8_outcome_names_the_comprehension_step(tmp_path: Path) -> None:
    case = next(c for c in CASES if c.name == "c8_production_linked_before_the_questions_fails")
    outcome = run(tmp_path, case.mutate).failures[0]
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.RECAP_COMPREHENSION_AFTER_PRODUCTION, 3, "s1")


def test_c18_skips_a_lesson_before_the_first_taught_letter() -> None:
    plan = mechanical_plan()
    _activity(plan, 1, "a1")["focus"] = "Checks the options нона and он."
    store = type("Store", (), {"records": {}})()
    pack = type("Pack", (), {"video_models": {}})()
    gates = ReviewGates(Report(LEVEL, SLUG), plan, LEVEL, store, None, None, Path("unused"), pack=pack)  # type: ignore[arg-type]
    gates.__dict__["taught_through"] = {1: set(), 2: {"м", "а", "н", "о"}, 3: {"м", "а", "н", "о"}}
    gates.check_choice_options_taught()
    assert gates.report.failures == gates.report.notes == []


def test_c17_and_c15_outcomes_name_lesson_and_step(tmp_path: Path) -> None:
    case = next(c for c in CASES if c.name == "c15_adjacent_steps_displaying_one_quote_fail")
    outcome = run(tmp_path / "c15", case.mutate).failures[0]
    assert (outcome.code, outcome.lesson, outcome.step) == (codes.ADJACENT_STEP_SAME_DISPLAY, 2, "s2")
    case = next(c for c in CASES if c.name == "c17_video_use_naming_a_step_that_does_not_cite_it_fails")
    outcome = run(tmp_path / "c17", case.mutate).failures[0]
    assert (outcome.code, outcome.lesson) == (codes.VIDEO_USE_STEP_MISMATCH, 1)


def test_c18_unavailable_arc_is_not_checked_not_passed(tmp_path: Path) -> None:
    plan, pack, words, prior = mechanical_plan(), mechanical_pack(), mechanical_words(), prior_plan()
    _focus(1, "a1", "Checks the letter М; the options are мама and нона.")(plan, pack, words, prior)
    world = write_world(tmp_path, plan, pack, words)
    (world.plan_path.parent / "_arc.yaml").unlink()
    report = validate_plan(LEVEL, SLUG, plan_path=world.plan_path)
    assert codes.CHOICE_OPTION_UNVERIFIED not in report.codes(), report.render_text()
    gates = {o.message.split()[1] for o in report.not_checked if o.code == codes.MECHANICAL_RULE_NOT_CHECKED}
    assert "C18" in gates, report.render_text()


def test_c23_unavailable_vesum_is_not_checked_not_passed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def unavailable(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("no database")

    monkeypatch.setattr(quote_bytes, "vesum_lookup", unavailable)
    report = run(tmp_path, _pick("Complete но-на from its syllables; select the missing first syllable."))
    assert codes.CONSTRUCTION_DISTRACTOR_FORMS_WORD not in report.codes(), report.render_text()
    undecided = [o.message for o in report.not_checked if o.code == codes.VESUM_UNAVAILABLE]
    assert undecided and undecided[0].startswith("gate C23 is undecided"), report.render_text()


@pytest.mark.parametrize("strict", [False, True])
def test_c23_word_store_completions_survive_unavailable_vesum(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, strict: bool
) -> None:
    """The reviewer's case: a completion the word store attests (ма-на → мана) is proven without VESUM."""

    def unavailable(words: list[str]) -> set[str]:
        raise quote_bytes.VesumUnavailable("no database")

    monkeypatch.setattr(quote_bytes, "vesum_lookup", unavailable)
    case = next(c for c in CASES if c.name == "c23_syllable_swap_forming_a_store_word_fails")
    report = run(tmp_path, case.mutate, strict=strict)
    assert codes.CONSTRUCTION_DISTRACTOR_FORMS_WORD in {o.code for o in report.failures}, report.render_text()
    undecided = report.failures if strict else report.not_checked
    assert codes.VESUM_UNAVAILABLE in {o.code for o in undecided}, report.render_text()
    assert report.status == "fail"


@pytest.mark.parametrize(
    ("word", "sound"),
    [
        ("ятір", "й"),
        ("Юнак", "й"),
        ("єнот", "й"),
        ("їжак", "й"),
        ("йод", "й"),
        ("рік", "р′"),
        ("ліс", "л′"),
        ("люк", "л′"),
        ("лак", "л"),
        ("мама", "м"),
        ("м’ясо", "м"),
        ("щука", "ш"),
        ("джерело", "дж"),
        ("дзиґа", "дз"),
        ("ім’я", "і"),
        ("око", "о"),
        ("бюро", None),
        ("кран", None),
        ("вчитель", None),
        ("дзвін", None),
        ("пісня", None),
    ],
)
def test_c11_initial_sound(word: str, sound: str | None) -> None:
    assert review_gates._initial_sound(word) == sound
    assert review_gates._initial_sound(unicodedata.normalize("NFD", word)) == sound


# The reviewer's fixtures (#9487 round 8): each phrasing a prose parser misread. Targets and options are read from
# focus prose, so every one is a note quoting its sentence, never a failure and never a silent pass.
@pytest.mark.parametrize(
    ("focus", "code", "span"),
    [
        (f"Checks {MAMA}.", codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED, f"«Checks {MAMA}.»"),
        (
            f"Checks {MAMA} and do not give hints.",
            codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED,
            f"«Checks {MAMA} and do not give hints.»",
        ),
        ("The printed options are мама and мало.", codes.CHOICE_OPTION_UNVERIFIED, "«The printed options are"),
        ("The printed options: мама, мало.", codes.CHOICE_OPTION_UNVERIFIED, "«The printed options: мама, мало.»"),
        (
            "The teacher never prints the options мама and мало.",
            codes.CHOICE_OPTION_UNVERIFIED,
            "«The teacher never prints the options мама and мало.»",
        ),
    ],
)
@pytest.mark.parametrize("strict", [False, True])
def test_prose_targets_and_options_are_notes_with_their_span(
    tmp_path: Path, focus: str, code: str, span: str, strict: bool
) -> None:
    report = run(tmp_path, _focus(1, "a1", focus), strict=strict)
    assert report.failures == [], report.render_text()
    noted = [o.message for o in report.notes if o.code == code]
    assert len(noted) == 1 and span in noted[0], report.render_text()
    if code == codes.CHOICE_OPTION_UNVERIFIED:
        assert "'мало' (needs л, о)" in noted[0] and "'мама'" not in noted[0], report.render_text()
    assert report.status != "fail"


def test_evidence_span_is_the_sentence_holding_the_token() -> None:
    text = f"Score {MAMA}.  Do not   score {NONA} here; it is introduced in s2."
    assert review_gates._span(text, NONA, review_gates._WORD_ID) == f"«Do not score {NONA} here;»"
    assert review_gates._span(text, MAMA, review_gates._WORD_ID) == f"«Score {MAMA}.»"


# round 10 of the cross-family review (#9487): a span is the sentence where the id or word occurs whole.
@pytest.mark.parametrize(
    ("token", "span"),
    [("W-20", "«Then W-20.»"), ("W-201", "«Checks W-201.»"), ("W-2010", "«Do not score W-2010 here.»")],
)
def test_evidence_span_matches_whole_ids(token: str, span: str) -> None:
    text = "Do not score W-2010 here. Checks W-201. Then W-20."
    assert review_gates._span(text, token, review_gates._WORD_ID) == span


def test_evidence_span_matches_whole_words() -> None:
    text = "The options are мама and мана. Then ма."
    assert review_gates._span(text, "ма", review_gates._ROW_TOKEN) == "«Then ма.»"


def test_c1_note_quotes_the_sentence_of_its_own_id(tmp_path: Path) -> None:
    longer = "W-2010"
    report = run(tmp_path, _all(_word(longer, "нон"), _focus(1, "a1", f"Do not score {longer} here. Checks {MAMA}.")))
    later = [o.message for o in report.notes if o.code == codes.NAMED_BEFORE_INTRODUCTION_UNVERIFIED]
    assert any(f"{MAMA} (introduced by step s2) in «Checks {MAMA}.»" in message for message in later), (
        report.render_text()
    )
    assert not any(f"{MAMA} (introduced by step s2) in «Do not" in message for message in later), report.render_text()


def test_c15_display_directive_reads_each_id_whole() -> None:
    step = {"teach": "Recall T-0010, then show T-001."}
    shown, _recalled = review_gates._displays(step, {"T-001", "T-0010"}, {})
    assert shown == {"T-001"}


# Every W-id of a comprehension focus ends in exactly one C26 outcome (#9487 C26, round 12): an id the store lacks ->
# comprehension_target_unknown; held by a resolvable host of the activity -> nothing; unheld, named in a plain sentence,
# with every host of the activity resolvable and none declared in a sentence naming another activity ->
# comprehension_target_not_in_host (comprehension_target_only_transcribed when a host holds a transcription); any
# other unheld id -> comprehension_target_unverified.
C26_SENTENCES = {
    "plain": "Answer about {id}.",
    "excluding": "Asks about {id} and do not give hints.",
    "sibling": "This b4 asks about {id} as in b2.",
    "both": "This b4 asks about {id} and do not give hints as in b2.",
}
C26_UNKNOWN = "W-999"


@dataclass(frozen=True)
class C26Hosts:
    """A host configuration of activity b4: its host sentences, the T-002 quote, the ids it holds, whether it decides."""

    sentences: str
    held: frozenset[str]
    decides: bool
    quote: str = "он м а м а"
    transcribed: bool = False


C26_HOSTS = {
    "quote": C26Hosts("kind: comprehension; host: {kind: quote, ref: T-002}.", frozenset({MAMA}), True),
    "transcribed_quote": C26Hosts(
        "kind: comprehension; host: {kind: quote, ref: T-002}.",
        frozenset({MAMA}),
        True,
        quote="он м а м а [нон′а]",
        transcribed=True,
    ),
    "quote+video": C26Hosts(
        "kind: comprehension; host {kind: quote, ref: T-002} or {kind: video, ref: V-900}.",
        frozenset({MAMA, MANA}),
        True,
    ),
    "quote+sibling_dialogue": C26Hosts(
        "kind: comprehension; host: {kind: quote, ref: T-002}. Drafted as in b2 (host: {kind: dialogue}).",
        frozenset({MAMA}),
        False,
    ),
    # T-003 prints нона, but the sentence declaring it names b2, so it never holds b4's words.
    "quote+sibling_quote": C26Hosts(
        "kind: comprehension; host: {kind: quote, ref: T-002}. As in b2, host: {kind: quote, ref: T-003}.",
        frozenset({MAMA}),
        False,
    ),
    "quote+sibling_video": C26Hosts(
        "kind: comprehension; host: {kind: quote, ref: T-002}. As in b2, host: {kind: video, ref: V-900}.",
        frozenset({MAMA}),
        False,
    ),
    "quote+own_dialogue": C26Hosts(
        "kind: comprehension; host {kind: quote, ref: T-002} or {kind: dialogue}.", frozenset({MAMA}), False
    ),
    "quote+own_unresolved": C26Hosts(
        "kind: comprehension; host {kind: quote, ref: T-002} or {kind: quote, ref: T-998}.", frozenset({MAMA}), False
    ),
    "dialogue": C26Hosts("kind: comprehension; host: {kind: dialogue}.", frozenset(), False),
    "sibling_only": C26Hosts("kind: comprehension. As in b2, host: {kind: quote, ref: T-002}.", frozenset(), False),
}
C26_LABELS = {
    codes.COMPREHENSION_TARGET_UNKNOWN: "unknown",
    codes.COMPREHENSION_TARGET_NOT_IN_HOST: "failure",
    codes.COMPREHENSION_TARGET_ONLY_TRANSCRIBED: "transcribed",
    codes.COMPREHENSION_TARGET_UNVERIFIED: "note",
}


def _c26_expected(item: str, kinds: list[str], hosts: C26Hosts) -> str:
    if item == C26_UNKNOWN:
        return "unknown"
    if item in hosts.held:
        return "nothing"
    if "plain" in kinds and hosts.decides:
        return "transcribed" if hosts.transcribed else "failure"
    return "note"


@pytest.mark.parametrize("hosts", C26_HOSTS, ids=str)
@pytest.mark.parametrize(
    "kinds", [*([kind] for kind in C26_SENTENCES), ["plain", "sibling"], ["excluding", "sibling"]], ids="+".join
)
def test_c26_every_focus_id_ends_in_exactly_one_outcome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hosts: str, kinds: list[str]
) -> None:
    config = C26_HOSTS[hosts]
    items = [MAMA, MANA, NONA, C26_UNKNOWN]
    focus = " ".join(C26_SENTENCES[kind].format(id=item) for item in items for kind in kinds)
    focus = f"{focus} {config.sentences}"

    def mutate(plan: dict, pack: dict, words: dict, prior: dict) -> None:
        pack["texts"].append({"id": "T-003", "quote": "нона"})
        _quote(config.quote, {"id": "b4", "type": "quiz", "placement": "workbook", "focus": focus})(
            plan, pack, words, prior
        )

    # The invariant itself: the outcome mapping is total over the focus's W- ids, each with a C26 code or None.
    mappings: list[tuple[str, dict]] = []
    outcomes = ReviewGates._comprehension_target_outcomes

    def spy(self: ReviewGates, context: review_gates._C26Context) -> dict:
        mapping = outcomes(self, context)
        mappings.append((context.focus, mapping))
        return mapping

    monkeypatch.setattr(ReviewGates, "_comprehension_target_outcomes", spy)
    report = run(tmp_path, mutate)
    assert [list(mapping) for text, mapping in mappings if text == focus] == [items], "C26 skipped b4's ids"
    for text, mapping in mappings:
        assert list(mapping) == review_gates._ids(review_gates._WORD_ID, text)
        assert all(code is None or code in C26_LABELS for code, _entry in mapping.values())
    # Each id ends in exactly the outcome the rule gives it, reported once.
    for item in items:
        found = [
            C26_LABELS[o.code]
            for o in report.failures + report.notes
            if o.code in C26_LABELS and item in review_gates._WORD_ID.findall(o.message)
        ]
        outcome = found[0] if len(found) == 1 else "nothing" if not found else f"several {found}"
        assert outcome == _c26_expected(item, kinds, config), (item, report.render_text())


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("c21_exact_print_before_its_letters_are_taught_fails", (codes.MODELED_PRINT_NOT_DECODABLE, 1, "s1")),
        ("c25_practice_step_with_no_content_fails", (codes.PRACTICE_STEP_EMPTY, 1, "s3")),
        ("c27_letters_no_recording_models_fail", (codes.LETTER_WITHOUT_RECORDING, 2, "s1")),
        ("c28_teach_text_naming_a_later_word_fails", (codes.TEACH_WORD_NOT_IN_INVENTORY, 1, "s1")),
        ("c22_three_choice_activities_on_one_binary_key_set_fail", (codes.CHOICE_BINARY_KEYS_REPEATED, 1, None)),
    ],
)
def test_fourth_round_outcomes_name_lesson_and_step(
    tmp_path: Path, name: str, expected: tuple[str, int, str | None]
) -> None:
    outcome = run(tmp_path, next(c for c in CASES if c.name == name).mutate).failures[0]
    assert (outcome.code, outcome.lesson, outcome.step) == expected


# The wording below is copied from the A1 position 1 plan the fourth review returned (#9487); the syllables are
# the plan's own rows, and the tests check how the gate reads them, not which completions VESUM lists.
def test_c22_reads_the_key_sets_the_plans_declare() -> None:
    def keys(focus: str) -> list[frozenset[str]]:
        return [
            frozenset(" ".join(item.split()).casefold() for item in review_gates._KEY_SPLIT.split(match.group(1)))
            for match in review_gates._KEY_SET.finditer(focus)
        ]

    assert keys("Both greeting keys Привіт and Добрий день occur; vary substantive keys and option positions.") == [
        frozenset({"привіт", "добрий день"})
    ]
    assert keys("Exactly one member differs in letter identity; keys О, У, И, А vary.") == [
        frozenset({"о", "у", "и", "а"})
    ]
    assert keys("The correction keys 1 and 2 both occur.") == [frozenset({"1", "2"})]
    assert keys("Both class keys occur, progressing from lesson 4 repair.") == []


def test_c23_reads_blanked_rows_named_slots_and_the_activity_syllables() -> None:
    blanked = review_gates._syllable_swaps(
        "From the complete X-004 missing-syllable rows, use only core W-082 and W-083: the middle blank in "
        "ма- __ -на has key ли, and the initial blank in __ -ва has key сли."
    )
    assert ("ма-сли-на", "маслина", "малина") in blanked
    assert ("ва-ва", "вава", "слива") in blanked
    assert all(made[:2] == "ма" and made[-2:] == "на" for _shown, made, key in blanked if key == "малина")

    final = review_gates._syllable_swaps(
        "On the exact T-036 source segmentations ма-ма (W-081) and Ко-ло (incidental W-154), select the missing "
        "final syllables ма and ло. The teacher first models these exact T-036 print forms."
    )
    assert {("ма-ло", "мало", "мама"), ("Ко-ма", "кома", "коло")} <= set(final)
    assert all(made[:2] == key[:2] for _shown, made, key in final)  # only the named final slot is swapped


def test_c21_reading_bounds() -> None:
    learner, teacher, frame = review_gates._reading_bounds(
        "The teacher demonstrates the exact print in X-001. The teacher reads the instruction while the learner reads "
        "only мама."
    )
    assert (learner, teacher, frame) == ({"мама"}, set(), True)
    assert review_gates._reading_bounds("The teacher reads Прочитай; learners read мама and ман.") == (
        {"мама", "ман"},
        {"прочитай"},
        False,
    )
    assert review_gates._reading_bounds("The teacher demonstrates the exact print in X-001.") == (None, set(), False)
    assert review_gates._reading_bounds("The teacher reads мало. The learner reads only мало.") == (
        {"мало"},
        set(),
        False,
    )
